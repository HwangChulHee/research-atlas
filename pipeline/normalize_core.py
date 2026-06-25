"""normalize_core: 논문 1편 → 그 논문이 그래프에 기여하는 노드/엣지(중립 형태).

배치 재빌드(normalize_v2.py)와 증분 쓰기(graphdb/write.py)가 **이 한 함수**를 공유한다.
두 경로가 영영 갈라지지 않게 하는 게 목적(불변식: 라이브 Neo4j == 배치 재빌드).

규칙은 HANDOFF 0.4를 글자대로 따른다(순서 의존 동작 포함, 고치지 않음):
- canon(s) = lower → '-'→공백 → 공백 1칸 정규화. 개념 키는 canon값.
- NODE_OK = {"approved","unreviewed"} 만 노드/엣지가 됨.
- 신규 개념: defines로 처음 보면 unreviewed, builds_on로 처음 보면 pending.
- pending/rejected는 노드 아님 → 엣지도 없음.
- 정의: 최초 비어있지 않은 정의가 이김(나중 defines가 안 덮음). def_status는
  정의 있으면 'ok', builds_on만으로 생긴 빈 개념은 'placeholder'. ok→placeholder 금지.
- home_concept = 그 논문이 처음 defines한 개념(첫 defines '엣지' 기준).
- 알려진 순서 의존(0.4): 어떤 개념이 builds_on으로 먼저 pending 등록되면, 이후
  defines가 와도 register가 no-op이라 계속 pending → 노드 안 됨. 이 동작 그대로 복제.
"""
import json
import re
from pathlib import Path

from pipeline import config

NODE_OK = {"approved", "unreviewed"}
_PAREN = re.compile(r"\s*\(([^()]*)\)\s*")
LEX_PATH = config.DATA_DIR / "lexicon.json"


def canon(s):
    return " ".join(s.lower().replace("-", " ").split())


def load_lex_state():
    """lexicon.json → 가변 사전상태(lex_state).

    lex      : 원본 techniques dict(label→meta). 저장 대상.
    alias2rep: 별칭canon → 대표canon.
    rep_meta : 대표canon → {label, status, ...}.
    new      : 이번 세션에 register된 신규 개념 카운트(요약용).
    """
    lex = json.load(open(LEX_PATH))["techniques"]
    alias2rep, rep_meta = {}, {}
    for rep, meta in lex.items():
        rk = canon(rep)
        rep_meta[rk] = {"label": rep, **meta}
        alias2rep[rk] = rk
        for v in meta.get("aliases", []):
            alias2rep[canon(v)] = rk
    return {"lex": lex, "alias2rep": alias2rep, "rep_meta": rep_meta,
            "new": {"unreviewed": 0, "pending": 0}}


def save_lexicon(st):
    json.dump({"techniques": st["lex"]}, open(LEX_PATH, "w"),
              ensure_ascii=False, indent=2)


def status_of(st, rk):
    return st["rep_meta"].get(rk, {}).get("status", None)


def resolve(st, name):
    k = canon(name)
    if k in st["alias2rep"]:
        rk = st["alias2rep"][k]
        return rk, st["rep_meta"][rk]["label"]
    # fallback: "Long Form (ACRONYM)" 표기 변종 — 직접 매칭 실패 시에만,
    # 이미 알려진 대표개념에만 연결(새 개념 생성 안 함).
    m = _PAREN.search(name)
    if m:
        inner = canon(m.group(1))                  # 괄호 안 약어, 예: "RAG"
        if inner in st["alias2rep"]:
            rk = st["alias2rep"][inner]
            return rk, st["rep_meta"][rk]["label"]
        outer = canon(_PAREN.sub(" ", name))       # 괄호 뗀 본체
        if outer in st["alias2rep"]:
            rk = st["alias2rep"][outer]
            return rk, st["rep_meta"][rk]["label"]
    return k, name


def register(st, rk, label, status, source, pid):
    """신규 개념이면 lex_state에 추가하고 True. 이미 있으면 no-op + False."""
    if rk in st["rep_meta"]:
        return False
    st["lex"][label] = {"aliases": [], "status": status, "definition": "",
                        "source": source, "first_seen": pid}
    st["rep_meta"][rk] = {"label": label, "status": status}
    st["alias2rep"][rk] = rk
    st["new"][status] += 1
    return True


def normalize_paper(con, rel, pid, st):
    """논문 1편의 concepts(con)/relations(rel) + 현재 사전상태(st) →
    그 논문이 기여하는 {paper_node, concept_nodes, edges, new_lexicon_entries}.

    st는 가변(register가 신규 개념을 여기에 추가). normalized_v2.json은 안 만듦.
    반환은 중립(접두사 없는 id) — 호출측이 JSON 직렬화 또는 Neo4j MERGE로 소비.

    paper_node : {id, title, problem, task, domain, paper_type, home_concept}
                 (home_concept은 Neo4j용 — normalized_v2.json은 이 필드 미사용)
    concept_nodes: {rk: {id, canonical, definition, def_status, status}}
                 (한 논문 안에서 ensure로 최초정의승·ok↛placeholder 적용)
    edges      : [{type:'defines'|'builds_on', from:pid, to:rk}] (접두사 없음, 순서/중복 보존)
    """
    paper_node = {
        "id": pid,
        "title": con.get("title", pid),
        "problem": con.get("problem", ""),
        "task": con.get("task", []),
        "domain": con.get("domain", "general"),
        "paper_type": con.get("paper_type", "other"),
        "home_concept": None,
    }
    concept_nodes = {}
    edges = []
    new_entries = []

    def ensure(rk, label, definition, def_status):
        if rk not in concept_nodes:
            concept_nodes[rk] = {
                "id": rk, "canonical": label,
                "definition": definition, "def_status": def_status,
                "status": status_of(st, rk),
            }
        elif definition and not concept_nodes[rk]["definition"]:
            concept_nodes[rk]["definition"] = definition
            concept_nodes[rk]["def_status"] = def_status

    for d in con.get("defines", []):
        rk, label = resolve(st, d["name"])
        if register(st, rk, label, "unreviewed", "defines", pid):
            new_entries.append(rk)
        if status_of(st, rk) in NODE_OK:
            ensure(rk, label, d.get("definition", ""), "ok")
            edges.append({"type": "defines", "from": pid, "to": rk})

    for name in (rel or {}).get("builds_on", []):
        rk, label = resolve(st, name)
        if register(st, rk, label, "pending", "builds_on", pid):
            new_entries.append(rk)
        if status_of(st, rk) in NODE_OK:
            ensure(rk, label, "", "placeholder")
            edges.append({"type": "builds_on", "from": pid, "to": rk})

    for e in edges:                       # home = 첫 defines 엣지의 대상
        if e["type"] == "defines":
            paper_node["home_concept"] = e["to"]
            break

    return {"paper_node": paper_node, "concept_nodes": concept_nodes,
            "edges": edges, "new_lexicon_entries": new_entries}
