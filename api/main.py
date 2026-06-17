"""research-atlas 웹 UI 백엔드.

그래프(읽기 전용)와 사전(편집)을 서빙한다.
파이프라인(src/)은 건드리지 않고, /api/rebuild만 src/normalize_v2.py를 subprocess로 호출한다.

실행:  uv run uvicorn api.main:app --reload --port 8000
"""
import json
import subprocess
import sys
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LEX_PATH = DATA_DIR / "lexicon.json"
NORMALIZED_V2_PATH = DATA_DIR / "outputs" / "normalized_v2.json"  # v2 이중 노드 — 현재 소스

app = FastAPI(title="research-atlas")

# Vite dev 서버(들)에서의 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- lexicon 입출력 헬퍼 ---
def load_lexicon() -> dict:
    """lexicon.json 전체(dict). techniques 키 하위에 개념들."""
    if not LEX_PATH.exists():
        raise HTTPException(500, f"lexicon.json 없음: {LEX_PATH}")
    return json.loads(LEX_PATH.read_text())


def save_lexicon(lex: dict) -> None:
    LEX_PATH.write_text(json.dumps(lex, ensure_ascii=False, indent=2))


# --- 그래프 ---
def _strip(nid: str) -> str:
    """'concept:rk' / 'paper:id' -> 접두사 제거. 접두사 없으면 그대로."""
    return nid.split(":", 1)[1] if ":" in nid else nid


def build_graph_view(include_papers: bool) -> dict:
    """normalized_v2.json(이중 노드) -> 개념 주도 형태로 변환.

    Neo4j 읽기 경로(graph_view_neo4j)가 정상화한 현역 변환의 롤백용 원본(/api/rebuild이 사용).
    기본(include_papers=False): 개념 노드만 + 개념간 builds_on(유도).
    include_papers=True: 위에 더해 논문 노드(paper: 접두사 유지)와 defines 엣지 추가.
    """
    if not NORMALIZED_V2_PATH.exists():
        raise HTTPException(500, f"normalized_v2.json 없음: {NORMALIZED_V2_PATH} (먼저 재빌드 필요)")
    raw = json.loads(NORMALIZED_V2_PATH.read_text())
    v2_nodes, edges = raw["nodes"], raw["edges"]
    papers_meta = {pid: n for pid, n in v2_nodes.items() if n["type"] == "paper"}

    # 개념 노드 → 개념 주도 키(접두사 제거)
    out_nodes = {}
    for cid, n in v2_nodes.items():
        if n["type"] != "concept":
            continue
        out_nodes[_strip(cid)] = {
            "canonical": n["canonical"],
            "definition": n.get("definition", ""),
            "def_status": n.get("def_status", "ok"),
            "status": n.get("status"),
            "papers": [],          # 아래에서 채움
            "ptype": "technique",  # defines 논문 paper_type로 유도(없으면 기본)
            "domain": "general",
        }

    # 엣지 순회: 개념별 papers/유도용 그룹 수집
    concept_papers = {}        # rk -> [paper id(접두사 제거), 순서/중복제거]
    concept_home_paper = {}    # rk -> 처음 defines한 paper:id (ptype/domain 유도용)
    defines_first = {}         # paper:id -> 그 논문이 처음 defines한 개념 rk (builds_on source)
    builds_by_paper = {}       # paper:id -> [builds_on 대상 개념 rk]

    for e in edges:
        pid_full, cid_full = e["from"], e["to"]
        pid, rk = _strip(pid_full), _strip(cid_full)
        lst = concept_papers.setdefault(rk, [])
        if pid not in lst:
            lst.append(pid)
        if e["type"] == "defines":
            concept_home_paper.setdefault(rk, pid_full)
            defines_first.setdefault(pid_full, rk)
        elif e["type"] == "builds_on":
            builds_by_paper.setdefault(pid_full, []).append(rk)

    # 개념 노드에 papers/ptype/domain 채우기
    for rk, node in out_nodes.items():
        node["papers"] = concept_papers.get(rk, [])
        home = concept_home_paper.get(rk)
        if home and home in papers_meta:
            node["ptype"] = papers_meta[home].get("paper_type") or "technique"
            node["domain"] = papers_meta[home].get("domain") or "general"

    # 개념간 builds_on 유도: 각 논문의 '첫 정의 개념' → builds_on 대상들.
    # (normalize_v2 규칙과 동일: home concept = defs[0]. 자기 루프 제외, 중복 제거)
    seen, builds_on = set(), []
    for pid_full, targets in builds_by_paper.items():
        src = defines_first.get(pid_full)
        if src is None:          # defines 없는 논문 → 개념간 계보 없음
            continue
        for tgt in targets:
            if tgt == src or tgt not in out_nodes:
                continue
            key = (src, tgt)
            if key not in seen:
                seen.add(key)
                builds_on.append({"from": src, "to": tgt})

    view = {"nodes": out_nodes, "builds_on": builds_on}

    if include_papers:
        for pid, n in papers_meta.items():  # pid 예: "paper:1706.03762"
            view["nodes"][pid] = {
                "type": "paper",
                "title": n.get("title", ""),
                "paper_type": n.get("paper_type", "other"),
                "domain": n.get("domain", "general"),
                "problem": n.get("problem", ""),
            }
        defines = []
        for e in edges:
            if e["type"] == "defines" and _strip(e["to"]) in out_nodes:
                defines.append({"from": e["from"], "to": _strip(e["to"])})
        view["defines"] = defines

        # 정의 없는 논문(survey/analysis 등)은 defines 엣지가 없어 고립됨.
        # 그런 논문만 builds_on(논문→개념)으로 닻을 내려준다(이미 연결된 논문은 화면 유지).
        papers_with_defines = {e["from"] for e in edges if e["type"] == "defines"}
        paper_builds_on = []
        for e in edges:
            if (e["type"] == "builds_on"
                    and e["from"] not in papers_with_defines
                    and _strip(e["to"]) in out_nodes):
                paper_builds_on.append({"from": e["from"], "to": _strip(e["to"])})
        view["paper_builds_on"] = paper_builds_on

    return view


@app.get("/api/graph")
def get_graph(papers: bool = False):
    """개념 주도 그래프. papers=false/true 모두 Neo4j 읽기 경로.

    build_graph_view(JSON)는 롤백용으로 보존 — 라우팅만 Neo4j로 전환.
    """
    from .graph_neo4j import graph_view_neo4j
    return graph_view_neo4j(include_papers=papers)


# --- 사전 ---
@app.get("/api/lexicon")
def get_lexicon():
    """techniques를 배열로 변환해 반환(프론트 편의)."""
    lex = load_lexicon()
    techniques = lex.get("techniques", {})
    return [
        {
            "name": name,
            "aliases": meta.get("aliases", []),
            "status": meta.get("status", "unreviewed"),
            "definition": meta.get("definition", ""),
            "source": meta.get("source", ""),
            "first_seen": meta.get("first_seen", ""),
        }
        for name, meta in techniques.items()
    ]


@app.patch("/api/lexicon/{name}")
def patch_lexicon(name: str, patch: dict = Body(...)):
    """한 개념의 부분 업데이트. 전달된 필드만 수정 + Neo4j 증분 동기화(T0 표 6·9).

    - status → 'rejected': 노드·엣지 삭제(reject_concept).
    - definition 전달: Neo4j 정의 갱신 + 재임베딩(update_definition). **임시 라이브 오버레이** —
      재빌드 시 추출 정의로 복귀(정의 정본은 논문 추출). 정의 교정의 올바른 해법은 정본 교정.
    - status 를 approved/unreviewed 로 *상향*: 즉시 노드화는 범위 밖(표#7) — 감사가 리포트.
    """
    from graphdb.write import reject_concept, update_definition
    from normalize_core import canon

    lex = load_lexicon()
    techniques = lex.get("techniques", {})
    if name not in techniques:
        raise HTTPException(404, f"개념 없음: {name}")
    editable = {"status", "aliases", "definition", "source", "first_seen"}
    for key, value in patch.items():
        if key in editable:
            techniques[name][key] = value
    save_lexicon(lex)

    rk = canon(name)
    note = None
    try:
        if patch.get("status") == "rejected":
            reject_concept(rk)
        if "definition" in patch:
            update_definition(rk, patch["definition"])
            note = ("정의는 임시 라이브 오버레이입니다 — 재빌드 시 추출 정의로 복귀합니다"
                    "(정의 정본은 논문 추출). 영구 교정은 정본(concepts.json) 수정/재추출로.")
    except Exception as e:  # noqa: BLE001  (lexicon은 이미 저장됨 — rebuild로 복구 가능)
        return {"ok": True, "name": name, "neo4j_sync": f"실패({type(e).__name__})",
                **techniques[name]}
    resp = {"ok": True, "name": name, **techniques[name]}
    if note:
        resp["note"] = note
    return resp


@app.post("/api/lexicon/merge")
def merge_lexicon(body: dict = Body(...)):
    """`from` 개념을 `into`의 alias로 병합하고 `from`은 삭제."""
    src = body.get("from")
    dst = body.get("into")
    if not src or not dst:
        raise HTTPException(400, "from/into 필요")
    if src == dst:
        raise HTTPException(400, "from과 into가 같음")
    lex = load_lexicon()
    techniques = lex.get("techniques", {})
    if src not in techniques:
        raise HTTPException(404, f"from 개념 없음: {src}")
    if dst not in techniques:
        raise HTTPException(404, f"into 개념 없음: {dst}")

    dst_aliases = techniques[dst].get("aliases", [])
    # from 이름 + from의 aliases를 into의 aliases로 흡수(중복 제거, 순서 보존)
    incoming = [src] + techniques[src].get("aliases", [])
    for alias in incoming:
        if alias not in dst_aliases and alias != dst:
            dst_aliases.append(alias)
    techniques[dst]["aliases"] = dst_aliases
    del techniques[src]
    save_lexicon(lex)

    # Neo4j 증분 동기화(T0#8 + 0.6): src 엣지를 dst 로 재연결, 닻 이동, src 삭제.
    from graphdb.write import merge_concept
    from normalize_core import canon
    try:
        merge_concept(canon(src), canon(dst))
    except Exception as e:  # noqa: BLE001  (lexicon은 이미 저장됨 — rebuild로 복구 가능)
        return {"ok": True, "into": dst, "aliases": dst_aliases,
                "neo4j_sync": f"실패({type(e).__name__})"}
    return {"ok": True, "into": dst, "aliases": dst_aliases}


# --- 재빌드 ---
def _run_step(name: str, *args: str) -> str:
    """파이프라인 스텝을 subprocess로 실행. 실패 시 stdout/stderr 묶어 HTTP 500."""
    proc = subprocess.run([sys.executable, *args], cwd=str(ROOT),
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise HTTPException(500, f"{name} 실패:\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout


@app.post("/api/rebuild")
def rebuild():
    """정본(원자료+사전)에서 Neo4j를 처음부터 다시 만들고 검증까지 — 증분 드리프트 복구 버튼.

    1) src/normalize_v2.py  : 원자료→normalized_v2.json(오라클 중간산물) + lexicon 반영
    2) graphdb/load.py      : Neo4j 전체 덮어쓰기(wipe+load) — 증분 드리프트 청소
    3) graphdb/verify.py    : 라이브 Neo4j == 재빌드 JSON 검증(실패 시 500 + diff)
    4) graph_view_neo4j     : Neo4j(라이브) 기준 카운트 반환
       (build_graph_view(JSON) 카운트 금지 — '성공인데 화면 옛것' 함정.)
    """
    _run_step("normalize_v2.py", str(ROOT / "src" / "normalize_v2.py"))
    _run_step("load.py", str(ROOT / "graphdb" / "load.py"))
    _run_step("verify.py", str(ROOT / "graphdb" / "verify.py"))

    from .graph_neo4j import graph_view_neo4j
    view = graph_view_neo4j(include_papers=False)
    return {
        "ok": True,
        "nodes": len(view["nodes"]),
        "builds_on": len(view["builds_on"]),
    }


# --- 자연어 명령 (필터 에이전트) ---
sys.path.insert(0, str(ROOT))  # agent_filter import용 (uvicorn 실행 위치 무관하게)
from dotenv import load_dotenv
from openai import OpenAI

from agent_filter import TOOLS, build_system_prompt

load_dotenv(ROOT / ".env")
_oai = OpenAI()
COMMAND_MODEL = "gpt-5.4-mini"


@app.post("/api/command")
def command(payload: dict = Body(...)):
    """자연어 명령 -> tool call 번역. 실행은 프론트가 한다.

    반환: {"tool": "filter|focus_lineage|reset", "args": {...}}
          tool call이 안 나오면 {"tool": null, "message": "..."}
    """
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text가 비어 있음")

    from .graph_neo4j import graph_view_neo4j
    view = graph_view_neo4j(include_papers=False)
    names = sorted(v["canonical"] for v in view["nodes"].values())

    resp = _oai.chat.completions.create(
        model=COMMAND_MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt(names)},
            {"role": "user", "content": text},
        ],
        tools=TOOLS,
    )
    msg = resp.choices[0].message
    if not msg.tool_calls:
        return {"tool": None, "message": (msg.content or "")[:200]}

    tc = msg.tool_calls[0]
    try:
        args = json.loads(tc.function.arguments or "{}")
    except json.JSONDecodeError:
        raise HTTPException(502, f"tool 인자 파싱 실패: {tc.function.arguments}")

    # focus_lineage의 node가 실재하는지 백엔드에서 한 번 더 검증
    if tc.function.name == "focus_lineage":
        canon_set = {n.lower() for n in names}
        if (args.get("node") or "").lower() not in canon_set:
            return {"tool": None, "message": f"'{args.get('node')}' 노드를 찾지 못함"}

    return {"tool": tc.function.name, "args": args}


# --- 수집 에이전트 (LangGraph 흐름, start/resume) ---
# 그래프는 모듈 로드 시 1회 컴파일해 전역 보관 — 매 요청 compile하면 MemorySaver 상태가
# 초기화돼 resume이 깨진다(핵심 함정). thread_id별로 세션 격리됨.
import uuid

from langgraph.types import Command

from agent_collect import build_collect_graph

_collect_graph = build_collect_graph()


def _interrupt_response(thread_id: str, payload: dict) -> dict:
    """interrupt payload(agent_collect의 interrupt({...})) → stage별 프론트 응답."""
    stage = payload.get("stage")
    out = {"thread_id": thread_id, "done": False, "stage": stage}
    if stage == "interpret":
        out["topic"] = payload.get("topic", "")
        out["report"] = payload.get("status_report", "")
        out["actions"] = ["proceed", "revise", "cancel"]
    elif stage == "approve":
        out["counts"] = payload.get("counts", {})
        out["actions"] = ["proceed", "cancel"]
    elif stage == "extract_confirm":
        out["passed_count"] = payload.get("passed_count")
        out["to_extract"] = payload.get("to_extract")
        out["gate_summary"] = payload.get("gate_summary")
        out["actions"] = ["proceed", "cancel"]
    return out


def _done_response(thread_id: str, values: dict) -> dict:
    """완료 상태(values dict) → done 응답."""
    return {"thread_id": thread_id, "done": True,
            "extracted": values.get("extracted", []),
            "summary": values.get("report_text", "")}


def _to_response(thread_id: str, result: dict) -> dict:
    """그래프 invoke 결과 → 프론트용. interrupt 멈춤이면 stage별 payload, 완료면 최종 요약."""
    if "__interrupt__" in result:
        return _interrupt_response(thread_id, result["__interrupt__"][0].value)
    return _done_response(thread_id, result)


@app.post("/api/collect/start")
def collect_start(payload: dict = Body(...)):
    """수집 명령 → 첫 interrupt(해석 확인)까지 실행."""
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text 비어 있음")
    thread_id = uuid.uuid4().hex
    cfg = {"configurable": {"thread_id": thread_id}}
    result = _collect_graph.invoke({"query": text}, cfg)
    return _to_response(thread_id, result)


@app.post("/api/collect/resume")
def collect_resume(payload: dict = Body(...)):
    """결정(proceed|cancel|revise:<텍스트>) → 다음 interrupt 또는 완료까지 재개."""
    thread_id = payload.get("thread_id")
    decision = payload.get("decision")
    if not thread_id or not decision:
        raise HTTPException(400, "thread_id/decision 필요")
    cfg = {"configurable": {"thread_id": thread_id}}
    # 존재하지 않는 thread_id면 상태가 없어 조용히 새 실행처럼 돌 수 있음 → 명시적으로 거른다.
    if _collect_graph.get_state(cfg).created_at is None:
        raise HTTPException(404, "세션 없음(서버 재시작/만료) — 다시 시작하세요")
    try:
        result = _collect_graph.invoke(Command(resume=decision), cfg)
    except Exception as e:
        raise HTTPException(500, f"재개 실패(세션 만료 가능): {e}")
    return _to_response(thread_id, result)


@app.get("/api/collect/state")
def collect_state(thread_id: str):
    """thread_id 의 현재 체크포인트 상태 → start/resume 과 동일 스키마.

    프론트가 새로고침/재접속 시 카드를 복원하는 데 쓴다. get_state 반환은 invoke 의
    {"__interrupt__": [...]} 와 형식이 달라 어댑터로 맞춘다:
    - 멈춘 interrupt 는 snap.interrupts[*].value 에 있음 → _interrupt_response 로 감쌈.
    - interrupt 없고 next 없음 → 완료(snap.values 로 done 응답).
    - 세션 없음(created_at None) → 404.
    """
    cfg = {"configurable": {"thread_id": thread_id}}
    snap = _collect_graph.get_state(cfg)
    if snap.created_at is None:
        raise HTTPException(404, "세션 없음(서버 재시작/만료)")
    if snap.interrupts:
        return _interrupt_response(thread_id, snap.interrupts[0].value)
    if snap.next:
        # interrupt 없이 다음 노드 대기 = 실행 중간(예: 추출 도중 서버 재시작).
        # 카드로 복원할 안정 지점이 아님 → 만료로 취급(프론트가 thread 참조 정리). ⑤ 범위.
        raise HTTPException(404, "복원 가능한 멈춤 지점 아님(실행 중간)")
    return _done_response(thread_id, snap.values)
