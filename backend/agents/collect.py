"""수집 에이전트 (전환 4/4) — 의도 파싱 → 현황(개념+논문 두 각도) → 현황 보고 + 충분성 추천.

v2 이중 노드 임베딩(node_embeddings_v2.json) 위에서 동작.
- 개념 매칭(definition): "이 주제 관련 기법이 뭐 있나".
- 논문 매칭(problem): "같은 문제를 다룬 논문이 뭐 있나" (세렌디피티 씨앗).
arXiv 실제 수집/승인/분기는 다음 조각. 이번은 현황 보고까지만.

이 모듈은 라이브러리 — backend/api/main.py·eval/test_collect.py 가 함수를 import 해 쓴다.
스모크 검증은 eval/smoke_collect.py (uv run python eval/smoke_collect.py [--*-smoke]).
"""
import datetime
import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from typing import TypedDict

import feedparser
import numpy as np
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
# 기존 추출 파이프라인 재사용 (pipeline/) — 호출만, 로직 수정 안 함
from pipeline import config  # noqa: E402
from pipeline import extract  # noqa: E402
from pipeline import fetch  # noqa: E402
from pipeline import parse  # noqa: E402
from pipeline import relate  # noqa: E402

from graphdb.write import write_paper  # noqa: E402  (증분 쓰기 — 추출 직후 Neo4j 반영)
from graphdb.read import is_offline, node_meta, owned_paper_ids  # noqa: E402  (읽기 단일 진입점)

# 프롬프트는 prompts/ 패키지 단일 출처에서(인라인 제거) — 한 프롬프트당 한 파일.
from prompts.collect.gate import GATE_PROMPT_VER, GATE_SYSTEM, GATE_USER  # noqa: E402
from prompts.collect.intent import INTENT_SYSTEM  # noqa: E402
from prompts.collect.report import REPORT_SYSTEM, build_report_user  # noqa: E402
from prompts.collect.expand import EXPAND_SYSTEM, build_expand_user  # noqa: E402

# .env 는 위 `import config`(load_dotenv(ROOT/.env))에서 이미 로딩됨 — 별도 호출 불필요.
client = config.make_openai_client()
MODEL = config.MODEL_COLLECT
EMBED_MODEL = config.EMBED_MODEL


# ---------- LLM 비용·시간 계기판 (레벨2: 호출당 기록 + 단계별 집계) ----------
# 동작 불변 — 결과를 바꾸지 않고 토큰·시간만 옆에서 잰다. 흐름의 LLM 호출은 전부
# logged_chat / logged_embed 를 경유시켜 _LLM_LOG 한 곳에 모은다. 회차 시작 시 reset.
_LLM_LOG = []   # 호출별 기록 (모듈 레벨 누적; 회차 시작 시 _log_reset)


def _log_reset():
    """회차 시작 시 호출 — 누적 로그 비우기."""
    _LLM_LOG.clear()


def logged_chat(*, stage, **kwargs):
    """client.chat.completions.create 래퍼 — 토큰·시간 기록(인자는 그대로 전달)."""
    t0 = time.time()
    resp = client.chat.completions.create(**kwargs)
    u = getattr(resp, "usage", None)
    _LLM_LOG.append({
        "stage": stage, "kind": "chat", "model": kwargs.get("model"),
        "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(u, "completion_tokens", 0) or 0,
        "seconds": round(time.time() - t0, 3),
    })
    return resp


def logged_embed(*, stage, **kwargs):
    """client.embeddings.create 래퍼 — 토큰·시간 기록(임베딩은 completion_tokens 없음)."""
    t0 = time.time()
    resp = client.embeddings.create(**kwargs)
    u = getattr(resp, "usage", None)
    _LLM_LOG.append({
        "stage": stage, "kind": "embed", "model": kwargs.get("model"),
        "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0, "completion_tokens": 0,
        "seconds": round(time.time() - t0, 3),
    })
    return resp


def llm_summary():
    """_LLM_LOG → stage별 {calls, prompt_tokens, completion_tokens, seconds} + total."""
    from collections import defaultdict
    agg = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0,
                               "completion_tokens": 0, "seconds": 0.0})
    for e in _LLM_LOG:
        a = agg[e["stage"]]
        a["calls"] += 1
        a["prompt_tokens"] += e["prompt_tokens"]
        a["completion_tokens"] += e["completion_tokens"]
        a["seconds"] = round(a["seconds"] + e["seconds"], 3)
    total = {"calls": sum(a["calls"] for a in agg.values()),
             "prompt_tokens": sum(a["prompt_tokens"] for a in agg.values()),
             "completion_tokens": sum(a["completion_tokens"] for a in agg.values()),
             "seconds": round(sum(a["seconds"] for a in agg.values()), 3)}
    return {"by_stage": dict(agg), "total": total}

ARXIV_API = "https://export.arxiv.org/api/query"
PAPERS_LEDGER = config.OUT_DIR / "papers.json"
COLLECT_DB = config.DATA_DIR / "collect_sessions.db"  # 수집 세션 체크포인트(서버 재시작에도 생존)
REJECT_VERDICTS = {"reject", "rejected", "drop"}  # 관문 탈락으로 보는 verdict

DEFAULT_EXTRACT = 2           # 사용자가 편수 미언급 시 기본 추출 편수
HARD_CAP = 10                 # 안전 상한(실수로 수백 편 PDF 받는 사고 방지) — count 가 커도 여기까지만


def extract_target(intent):
    """사용자가 명시한 편수(intent['count']) → 목표 추출 편수.

    미언급/모호(count=None)면 DEFAULT_EXTRACT, 명시했어도 HARD_CAP 을 넘지 않는다.
    """
    return min(intent.get("count") or DEFAULT_EXTRACT, HARD_CAP)

INTENT_TOOL = {
    "type": "function",
    "function": {
        "name": "report_intent",
        "description": "수집 명령의 의도를 구조화해 보고한다.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "수집 주제, 영어 연구용어로 (예: RAG robustness to retrieval noise)"},
                "topic_kr": {"type": "string", "description": "주제를 해석한 한국어 한 줄. 입력 문장을 복사하지 말고, 어떤 연구 주제로 이해했는지 풀어쓴다 (예: '검색된 문서에 노이즈가 섞여도 답변 품질을 유지하는 RAG 기법')"},
                "interpretation": {"type": "string", "description": "이 주제의 가능한 갈래들과 그중 어느 갈래로 좁혔는지 2~3문장. 모호한 부분이 있으면 명시 (예: '강건성은 검색 노이즈/적대적 공격/분포 변화로 갈리는데, RAG 맥락에선 보통 검색 노이즈를 뜻하므로 그쪽으로 해석')"},
                "period_from": {"type": "string", "description": "YYYY-MM. 명시 없으면 빈 문자열"},
                "period_to": {"type": "string", "description": "YYYY-MM. 명시 없으면 빈 문자열"},
                "count": {"type": ["integer", "null"],
                          "description": "사용자가 명시한 수집 논문 편수. 명시 없으면 null. '5편'->5, '여러 개'처럼 모호하면 null"},
            },
            "required": ["topic", "topic_kr", "interpretation"],
        },
    },
}


# --- 임베딩 로더 (v2, 타입 분리) ---
def load_embeddings():
    """node_embeddings_v2.json -> 타입별(개념/논문) 정규화 행렬로 분리.

    반환: model, norm(v2 nodes dict), (concept_keys, concept_mat), (paper_keys, paper_mat)
    """
    store = json.loads((config.OUT_DIR / "node_embeddings_v2.json").read_text())
    norm = node_meta()  # 라이브=Neo4j / 오프라인=normalized_v2.json (벡터는 캐시 그대로)
    model = store["model"]

    def build(prefix):
        keys = [k for k in store["vectors"] if k.startswith(prefix)]
        if not keys:
            return [], None
        mat = np.array([store["vectors"][k] for k in keys], dtype=np.float32)
        mat /= np.linalg.norm(mat, axis=1, keepdims=True)
        return keys, mat

    return model, norm, build("concept:"), build("paper:")


# --- 두 각도 매칭 ---
def embed_query(topic, model):
    qv = logged_embed(stage="parse_embed", model=model, input=[topic]).data[0].embedding
    q = np.array(qv, dtype=np.float32)
    return q / np.linalg.norm(q)


def match(q, keys, mat, top=8, floor=0.30):
    """topic 벡터와 코사인 유사. floor 미만은 컷, 상위 top개만."""
    if mat is None:
        return []
    sims = mat @ q  # 코사인 (둘 다 정규화됨)
    order = np.argsort(-sims)[:top]
    return [(keys[i], float(sims[i])) for i in order if sims[i] >= floor]


def parse_intent(text):
    resp = logged_chat(
        stage="parse_intent",
        model=MODEL,
        messages=[{"role": "system", "content": INTENT_SYSTEM}, {"role": "user", "content": text}],
        tools=[INTENT_TOOL],
        tool_choice={"type": "function", "function": {"name": "report_intent"}},
    )
    return json.loads(resp.choices[0].message.tool_calls[0].function.arguments)


# --- 현황 보고 + 충분성 추천 (LLM 1회) ---  REPORT_SYSTEM은 prompts.collect.report
def _concept_line(key, score, norm):
    n = norm.get(key, {})
    name = n.get("canonical", key.split(":", 1)[-1])
    definition = (n.get("definition") or "").strip()
    if n.get("def_status") == "placeholder" or not definition:
        return f"- {name} (정의 미보유) [{score:.2f}]"
    return f"- {name}: {definition} [{score:.2f}]"


def _paper_line(key, score, norm):
    n = norm.get(key, {})
    title = n.get("title", key.split(":", 1)[-1])
    problem = (n.get("problem") or "").strip() or "(문제 설명 없음)"
    return f"- {title} — {problem} [{score:.2f}]"


def build_status_report(intent, cm_hits, pm_hits, norm):
    concepts = "\n".join(_concept_line(k, s, norm) for k, s in cm_hits) or "(매칭된 개념 없음)"
    papers = "\n".join(_paper_line(k, s, norm) for k, s in pm_hits) or "(매칭된 논문 없음)"
    user = build_report_user(intent, concepts, papers)
    resp = logged_chat(
        stage="status_report",
        model=MODEL,
        messages=[
            {"role": "system", "content": REPORT_SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content


# --- [3] 검색어 확장 ---
EXPAND_TOOL = {
    "type": "function",
    "function": {
        "name": "expand_queries",
        "description": "수집 주제를 arXiv 전문 검색에 쓸 검색어 묶음으로 확장한다.",
        "parameters": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "5~8개의 영어 검색어. 각 검색어는 2~4단어의 짧은 핵심구(여러 개념을 한 검색어에 합치지 말고 개념마다 분리). 동의어·인접 표현·상위/하위 개념을 포함하되 주제에서 벗어나지 않게. 단순 topic 반복 금지.",
                },
            },
            "required": ["queries"],
        },
    },
}


def expand_query(topic, related_terms=None):
    """topic을 arXiv 검색어 5~8개로 확장. related_terms(보유 개념/논문)는 맵 밀착 재료."""
    user = build_expand_user(topic, related_terms)
    resp = logged_chat(
        stage="expand",
        model=MODEL,
        messages=[{"role": "system", "content": EXPAND_SYSTEM}, {"role": "user", "content": user}],
        tools=[EXPAND_TOOL],
        tool_choice={"type": "function", "function": {"name": "expand_queries"}},
    )
    args = json.loads(resp.choices[0].message.tool_calls[0].function.arguments)
    # 결정론적 안전망: 프롬프트가 확률적이라 또 긴 구문을 뱉을 수 있음.
    # all:"<구문>" 정확매칭은 길수록 0건 → MAX_WORDS 초과는 (자르지 말고) 버림.
    # 자르면 의미가 깨져 엉뚱한 매칭이 되므로 버리는 쪽이 안전.
    MAX_WORDS = 6
    MIN_QUERIES = 3
    out, seen = [], set()
    for q in args.get("queries", []):
        q = (q or "").strip()
        if not q or q.lower() in seen:
            continue
        if len(q.split()) > MAX_WORDS:
            print(f"  [확장] 너무 긴 검색어 버림({len(q.split())}단어): {q!r}", file=sys.stderr)
            continue
        seen.add(q.lower())
        out.append(q)
    if len(out) < MIN_QUERIES:
        print(f"  [확장] 경고: 유효 검색어 {len(out)}개뿐(길이 가드 통과 부족) — 검색 재현율 낮을 수 있음",
              file=sys.stderr)
    return out


# --- [4] arXiv 검색 ---
def _norm_arxiv_id(raw):
    """'http://arxiv.org/abs/2401.12345v2' / '2401.12345v2' -> '2401.12345' (버전 접미사 제거)."""
    tail = (raw or "").rstrip("/").split("/")[-1]
    return re.sub(r"v\d+$", "", tail)


def search_arxiv(queries, period_from="", period_to="", max_per_query=50):
    """검색어 묶음으로 arXiv 메타 검색 → {arxivID: meta}. 검색어 간 ID로 dedup.

    rate limit: 요청 사이 3초 sleep(arXiv 규정), 순차. period(YYYY-MM)는 클라이언트단 필터.
    """
    found = {}
    for i, q in enumerate(queries):
        if i:
            time.sleep(3)  # arXiv rate limit
        params = urllib.parse.urlencode({
            # 구문(phrase) 검색: 따옴표로 묶어야 다단어가 AND/구문으로 잡힘.
            # 따옴표 없으면 all:이 토큰 OR로 풀려 무관 논문이 뜸.
            "search_query": f'all:"{q}"',
            "start": 0,
            "max_results": max_per_query,
            # relevance 정렬: 상위가 주제 적합 → 후보가 관련도순 → gate 상위부터 = 주제 가까운 것부터.
            # (옛 submittedDate 정렬은 최신순이라 상위에 주제 무관 신상이 섞였음.)
            "sortBy": "relevance",
            "sortOrder": "descending",
        })
        req = urllib.request.Request(
            f"{ARXIV_API}?{params}",
            headers={"User-Agent": "research-atlas/0.1 (collect agent)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
        except Exception as e:  # 네트워크/타임아웃 — 한 검색어 건너뛰고 계속
            print(f"  검색 실패 [{q}]: {e}", file=sys.stderr)
            continue
        feed = feedparser.parse(raw)
        for e in feed.entries:
            aid = _norm_arxiv_id(e.get("id", ""))
            if not aid:
                continue
            published = (e.get("published", "") or "")[:10]  # YYYY-MM-DD
            ym = published[:7]
            if period_from and ym and ym < period_from:
                continue
            if period_to and ym and ym > period_to:
                continue
            if aid in found:
                continue  # 다른 검색어에 이미 잡힘
            found[aid] = {
                "title": " ".join((e.get("title", "") or "").split()),
                "abstract": " ".join((e.get("summary", "") or "").split()),
                "published": published,
                "categories": [t.get("term") for t in e.get("tags", [])],
                "first_seen_query": q,
            }
    return found


# --- papers.json 장부 (논문 장부, lexicon의 논문판) ---
def load_ledger():
    if PAPERS_LEDGER.exists():
        return json.loads(PAPERS_LEDGER.read_text())
    return {}


def upsert_ledger(found):
    """검색 결과를 papers.json에 upsert. gate/extracted/first_seen_query는 기존값 보존."""
    ledger = load_ledger()
    for aid, meta in found.items():
        if aid in ledger:  # 메타만 갱신, 판정 이력 보존
            ledger[aid].update({
                "title": meta["title"], "abstract": meta["abstract"],
                "published": meta["published"], "categories": meta["categories"],
            })
        else:
            ledger[aid] = {
                "title": meta["title"], "abstract": meta["abstract"],
                "published": meta["published"], "categories": meta["categories"],
                "gate": None, "extracted": False,
                "first_seen_query": meta["first_seen_query"],
            }
    PAPERS_LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2))
    return ledger


# --- [5] 신규 후보 산출 (보유분/관문탈락 제외) ---
def load_owned_ids():
    """보유 arXiv ID 집합 — 읽기 단일 진입점(라이브=Neo4j / 오프라인=normalized_v2.json)."""
    return owned_paper_ids()


def dedup_new_candidates(found, ledger):
    """found 중 (1)이미 지도 보유, (2)과거 관문 탈락 을 제외한 신규 후보 id + 카운트."""
    owned = load_owned_ids()
    new, owned_excl, gate_excl = [], 0, 0
    for aid in found:
        if aid in owned:
            owned_excl += 1
            continue
        gate = (ledger.get(aid) or {}).get("gate") or {}
        if str(gate.get("verdict", "")).lower() in REJECT_VERDICTS:
            gate_excl += 1
            continue
        new.append(aid)
    counts = {"found": len(found), "owned_excluded": owned_excl,
              "gate_excluded": gate_excl, "new": len(new)}
    return new, counts


def save_ledger(ledger):
    PAPERS_LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2))


# --- [7] 관문 (gate) — 초록만 보고 paper_type 분류, technique만 통과 ---
GATE_TOOL = {
    "type": "function",
    "function": {
        "name": "classify_paper",
        "description": "제목/초록만 보고(PDF 없이) paper_type 하나로 분류한다.",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {"type": "string",
                         "enum": ["technique", "benchmark", "analysis", "survey", "other"]},
                "reason": {"type": "string", "description": "분류 근거 한 줄"},
            },
            "required": ["type", "reason"],
        },
    },
}


def gate_classify(title, abstract):
    """LLM 1회. PAPER_TYPE_CRITERIA(추출과 동일 기준)로 초록만 보고 분류."""
    user = GATE_USER.format(title=title, abstract=abstract)
    resp = logged_chat(
        stage="gate",
        model=MODEL,
        messages=[{"role": "system", "content": GATE_SYSTEM},
                  {"role": "user", "content": user}],
        tools=[GATE_TOOL],
        tool_choice={"type": "function", "function": {"name": "classify_paper"}},
    )
    return json.loads(resp.choices[0].message.tool_calls[0].function.arguments)


def gate_one(aid, ledger):
    """ledger[aid]의 title/abstract로 관문. 같은 prompt_ver 캐시 있으면 재호출 안 함.

    반환: (verdict, passed(bool), cached(bool)). technique만 통과(이진).
    """
    entry = ledger[aid]
    g = entry.get("gate")
    if g and g.get("prompt_ver") == GATE_PROMPT_VER:
        return g["verdict"], g["verdict"] == "technique", True
    res = gate_classify(entry.get("title", ""), entry.get("abstract", ""))
    verdict = res["type"]
    entry["gate"] = {
        "verdict": verdict,
        "reason": res.get("reason", ""),
        "model": MODEL,
        "prompt_ver": GATE_PROMPT_VER,
        "date": datetime.date.today().isoformat(),
    }
    return verdict, verdict == "technique", False


# --- [8] 추출 (기존 파이프라인 재사용) ---
def extract_pipeline(aid, ledger):
    """관문 통과 논문 1편: PDF→parse→extract→relate→파일 생성, ledger.extracted=true.

    반환: (ok, msg, concepts|None). 실패 시 스킵용 (ok=False).
    """
    config.PDF_DIR.mkdir(parents=True, exist_ok=True)
    ok, msg = fetch.download_one(aid)
    if not ok:
        return False, f"download 실패({msg})", None
    parsed = parse.parse_one(aid)
    if not parsed.get("ok"):
        return False, f"parse 실패({parsed.get('reason')})", None
    (config.OUT_DIR / f"{aid}.parsed.json").write_text(
        json.dumps(parsed, ensure_ascii=False, indent=2))
    text = parsed["text"]
    concepts = extract.extract_one(text)
    (config.OUT_DIR / f"{aid}.concepts.json").write_text(
        json.dumps(concepts, ensure_ascii=False, indent=2))
    rel = relate.relate_one(concepts, text)
    (config.OUT_DIR / f"{aid}.relations.json").write_text(
        json.dumps(rel, ensure_ascii=False, indent=2))
    # 증분 쓰기: 원자료가 디스크에 남은 직후 lexicon·Neo4j에 반영(불변식: 재빌드와 동일).
    # 오프라인(eval)은 Neo4j 미반영 — eval 세계 전체가 JSON이라 격리 유지.
    # 실패해도 원자료는 디스크에 있으니 추출 자체는 성공으로 본다(rebuild/감사가 복구).
    if is_offline():
        wmsg = "오프라인(eval) — Neo4j 미반영"
    else:
        try:
            write_paper(concepts, rel, aid)
            wmsg = "Neo4j 반영"
        except Exception as e:  # noqa: BLE001
            wmsg = f"Neo4j 반영 실패({type(e).__name__}) — rebuild로 복구 필요"
    ledger[aid]["extracted"] = True
    return True, f"추출 완료({msg}, {wmsg})", concepts


# ============ LangGraph 흐름 엔진 ============
# 위 단위 함수들을 그래프로 묶고, 사람 개입 2곳(interrupt)을 넣는다.
# 노드는 기존 함수를 부르는 얇은 래퍼 — 로직 변경 없음. 채팅 연결은 다음 조각.


class CollectState(TypedDict, total=False):
    query: str            # 최초 사용자 명령
    intent: dict          # parse_intent 결과
    related: list          # 현황 매칭에서 뽑은 관련 용어(검색어 확장 재료)
    status_report: str    # build_status_report (interrupt 1에서 보여줄 것)
    queries: list          # expand_query 결과
    found: dict           # search_arxiv 결과
    candidates: list       # dedup 후 신규 후보 id
    counts: dict          # dedup 카운트 (interrupt 2에서 보여줄 것)
    gate_results: list     # 관문 판정 [(aid, verdict, ok)]
    extracted: list        # 추출된 aid
    decision: str         # 사람 입력 주입용 (resume value)
    report_text: str      # 최종 요약


def gnode_parse(state):
    """[1]의도파싱 + [2]현황매칭 → status_report·related."""
    model, norm, (ck, cm), (pk, pm) = load_embeddings()
    intent = parse_intent(state["query"])
    qv = embed_query(intent["topic"], model)
    cm_hits, pm_hits = match(qv, ck, cm), match(qv, pk, pm)
    related = [norm[k]["canonical"] for k, _ in cm_hits if k in norm]
    related += [norm[k].get("title", "") for k, _ in pm_hits if k in norm]
    related = [r for r in related if r][:10]
    report = build_status_report(intent, cm_hits, pm_hits, norm)
    return {"intent": intent, "related": related, "status_report": report}


def gnode_confirm_interpret(state):
    """[2.5] 해석 확인 — interrupt. resume: 'proceed' | 'revise:<텍스트>'."""
    decision = interrupt({"stage": "interpret",
                          "status_report": state["status_report"],
                          "topic": state["intent"]["topic"]})
    upd = {"decision": decision}
    if isinstance(decision, str) and decision.startswith("revise:"):
        upd["query"] = decision.split("revise:", 1)[1].strip()  # 재해석용 새 명령
    return upd


def route_after_interpret(state):
    d = state.get("decision", "")
    return "parse" if isinstance(d, str) and d.startswith("revise:") else "expand_search"


def gnode_expand_search(state):
    """[3]검색어확장 [4]arXiv [5]장부·dedup."""
    intent = state["intent"]
    queries = expand_query(intent["topic"], state.get("related"))
    found = search_arxiv(queries, intent.get("period_from", ""), intent.get("period_to", ""))
    ledger = upsert_ledger(found)
    candidates, counts = dedup_new_candidates(found, ledger)
    return {"queries": queries, "found": found, "candidates": candidates, "counts": counts}


def gnode_approve(state):
    """[6] 물량 승인 — interrupt. resume: 'proceed' | 'cancel'."""
    decision = interrupt({"stage": "approve",
                          "counts": state["counts"],
                          "queries": state.get("queries", [])})
    return {"decision": decision}


def route_after_approve(state):
    return "gate" if state.get("decision") == "proceed" else "report"


GATE_BATCH = 10          # 한 배치당 gate 판정 편수
GATE_MAX_BATCHES = 5     # 최대 5배치(=상위 50편)까지 보고 포기


def gnode_gate(state):
    """[7] 관문 — 관련도순 상위부터 GATE_BATCH씩 배치 판정, 목표 편수 통과하면 조기 종료.

    candidates 가 관련도순(search relevance)이라 상위부터 = 주제 가까운 것부터 본다.
    목표(target)만큼 통과하면 나머지는 LLM 판정 안 함 → 호출 대폭 절감.
    """
    ledger = load_ledger()
    target = extract_target(state["intent"])
    candidates = state["candidates"]
    results, passed, gate_calls, batches = [], [], 0, 0
    for b in range(GATE_MAX_BATCHES):
        chunk = candidates[b * GATE_BATCH:(b + 1) * GATE_BATCH]
        if not chunk:
            break
        batches += 1
        for aid in chunk:
            verdict, ok, cached = gate_one(aid, ledger)
            gate_calls += 0 if cached else 1
            results.append((aid, verdict, ok))
            if ok:
                passed.append(aid)
        if len(passed) >= target:   # 목표 채우면 조기 종료(나머지 배치 LLM 판정 안 함)
            break
    save_ledger(ledger)
    print(f"\n[7] 관문 {batches}배치({len(results)}편) 판정 — 통과 {len(passed)} / 목표 {target} "
          f"(LLM {gate_calls}회, 캐시 {len(results) - gate_calls}회, 미판정 {len(candidates) - len(results)}편)")
    return {"gate_results": results}


def gnode_confirm_extract(state):
    """[7.5] 추출 승인 — interrupt. 관문 결과 보여주고 멈춤. resume: 'proceed' | 'cancel'.

    관문(빠름)과 추출(느림·stall 위험)을 분리 — 추출은 여기서 승인한 뒤에만 돈다.
    """
    target = extract_target(state["intent"])
    passed = [aid for aid, _v, ok in state["gate_results"] if ok]
    requested = state["intent"].get("count")
    decision = interrupt({
        "stage": "extract_confirm",
        "passed_count": len(passed),
        "to_extract": passed[:target],        # 목표 편수만큼 실제 추출 예정 목록
        "target": target,
        "judged_count": len(state["gate_results"]),
        # 사용자가 HARD_CAP 초과 요청 시 상한 안내(카드용)
        "cap_notice": (f"{requested}편 요청 → 상한 {HARD_CAP}편까지만 추출"
                       if requested and requested > HARD_CAP else ""),
        "gate_summary": [{"id": aid, "verdict": v, "passed": ok}
                         for aid, v, ok in state["gate_results"]],
    })
    return {"decision": decision}


def route_after_confirm_extract(state):
    return "extract" if state.get("decision") == "proceed" else "report"


def gnode_extract(state):
    """[8] 추출 — 통과분 상위 target편(사용자 명시 편수, 미언급 기본 DEFAULT_EXTRACT·상한 HARD_CAP)."""
    ledger = load_ledger()
    target = extract_target(state["intent"])
    passed = [aid for aid, _v, ok in state["gate_results"] if ok]
    extracted = []
    for aid in passed[:target]:
        ok, _msg, _c = extract_pipeline(aid, ledger)
        if ok:
            extracted.append(aid)
    save_ledger(ledger)
    return {"extracted": extracted}


def gnode_report(state):
    # cancel은 두 지점에서 옴: approve(관문 전) vs extract_confirm(관문 후·추출만 취소)
    if state.get("decision") == "cancel":
        gr = state.get("gate_results")
        if gr:
            passed = sum(1 for _a, _v, ok in gr if ok)
            return {"report_text": f"추출 취소 — 관문 {len(gr)}편 완료(통과 {passed}편), 추출 안 함."}
        return {"report_text": "수집 취소 — 관문/추출 안 함."}
    ex = state.get("extracted", [])
    tail = "오프라인(eval) — Neo4j 미반영, rebuild 시 정본에서 합류" if is_offline() \
        else "Neo4j 반영 완료"
    return {"report_text": f"추출 완료 {len(ex)}편({tail}): {ex}"}


def build_collect_graph(checkpointer=None):
    """수집 흐름 컴파일. checkpointer 미지정 시 SqliteSaver(파일 영속) 사용.

    서버는 모듈 로드 시 1회만 compile(매 요청 compile 금지 — thread resume 깨짐).
    SqliteSaver 라 uvicorn 재시작에도 멈춘 세션이 살아있다. 스모크/테스트는
    MemorySaver 를 주입해 휘발성으로(파일 오염·재실행 충돌 방지).
    """
    if checkpointer is None:
        COLLECT_DB.parent.mkdir(parents=True, exist_ok=True)
        # FastAPI 는 여러 스레드에서 요청을 처리하므로 check_same_thread=False.
        conn = sqlite3.connect(str(COLLECT_DB), check_same_thread=False)
        checkpointer = SqliteSaver(conn)
    g = StateGraph(CollectState)
    g.add_node("parse", gnode_parse)
    g.add_node("confirm_interpret", gnode_confirm_interpret)
    g.add_node("expand_search", gnode_expand_search)
    g.add_node("approve", gnode_approve)
    g.add_node("gate", gnode_gate)
    g.add_node("confirm_extract", gnode_confirm_extract)
    g.add_node("extract", gnode_extract)
    g.add_node("report", gnode_report)
    g.add_edge(START, "parse")
    g.add_edge("parse", "confirm_interpret")
    g.add_conditional_edges("confirm_interpret", route_after_interpret,
                            {"parse": "parse", "expand_search": "expand_search"})
    g.add_edge("expand_search", "approve")
    g.add_conditional_edges("approve", route_after_approve,
                            {"gate": "gate", "report": "report"})
    g.add_edge("gate", "confirm_extract")
    g.add_conditional_edges("confirm_extract", route_after_confirm_extract,
                            {"extract": "extract", "report": "report"})
    g.add_edge("extract", "report")
    g.add_edge("report", END)
    return g.compile(checkpointer=checkpointer)


def _run_scenario(graph, thread_id, query, responses):
    """interrupt마다 멈춤 payload 출력 + responses[i]로 재개. (최종 state, 멈춤 스냅샷들) 반환."""
    cfg = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"query": query}, cfg)
    snapshots, i = [], 0
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        snapshots.append((payload, graph.get_state(cfg).values))
        if payload.get("stage") == "interpret":
            head = payload["status_report"].splitlines()[0] if payload["status_report"] else ""
            print(f"\n  [멈춤·해석확인] topic={payload['topic']} | 보고 첫줄: {head[:60]}")
        elif payload.get("stage") == "approve":
            c = payload["counts"]
            print(f"\n  [멈춤·물량승인] 신규 {c['new']}편 (발견 {c['found']}/보유제외 {c['owned_excluded']})")
        elif payload.get("stage") == "extract_confirm":
            print(f"\n  [멈춤·추출승인] 통과 {payload['passed_count']}편 → 추출 예정 {payload['to_extract']}")
        resume = responses[i] if i < len(responses) else "proceed"
        print(f"   ← 입력: {resume!r}")
        result = graph.invoke(Command(resume=resume), cfg)
        i += 1
    print(f"  [결과] {result.get('report_text', '')}")
    return result, snapshots
