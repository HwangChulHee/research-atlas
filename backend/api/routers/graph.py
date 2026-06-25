"""그래프(읽기) + 검토 도우미 + 논문 상세 + 개인화(reviewed) 라우트."""
import json

from fastapi import APIRouter, Body, HTTPException

from backend.api.deps import DATA_DIR, REVIEWED_PATH, ROOT, run_step
from backend.api.graph_neo4j import graph_view_neo4j

router = APIRouter()


def _load_reviewed() -> set:
    """data/reviewed.json → 검토한 개념 rk 집합(없으면 빈 set)."""
    if not REVIEWED_PATH.exists():
        return set()
    try:
        return set(json.loads(REVIEWED_PATH.read_text()).get("reviewed", []))
    except (json.JSONDecodeError, OSError):
        return set()


@router.get("/api/graph")
def get_graph(papers: bool = False):
    """개념 주도 그래프. papers=false/true 모두 Neo4j 읽기 경로.
    개념 노드엔 개인화 reviewed 플래그를 머지(reviewed.json 기준).

    JSON 직독 뷰 로직은 graphdb/verify.py 의 expected_from_json(검증 오라클)에만 남아
    graph_view_neo4j 와의 일치를 보증한다.
    """
    view = graph_view_neo4j(include_papers=papers)
    reviewed = _load_reviewed()
    for nid, node in view["nodes"].items():
        if node.get("type") != "paper":  # 개념만
            node["reviewed"] = nid in reviewed
    return view


@router.get("/api/review_suggestions")
def review_suggestions():
    """검토 도우미 제안(정적 스냅샷). scripts/review_helper.py가 생성. 적용은 기존
    PATCH/merge 엔드포인트로 — 여기선 서빙만(read-only)."""
    p = ROOT / "eval" / "reports" / "review_suggestions.json"
    if not p.exists():
        return {"cards": []}
    return {"cards": json.loads(p.read_text())}  # .json은 카드 리스트


@router.get("/api/paper/{pid}")
def paper_detail(pid: str):
    """노드 클릭 시 보여줄 논문 정보 — 제목·문제·초록(발췌). parsed/concepts.json에서 읽음."""
    out = DATA_DIR / "outputs"
    cp = out / f"{pid}.concepts.json"
    pp = out / f"{pid}.parsed.json"
    if not cp.exists() and not pp.exists():
        raise HTTPException(404, f"논문 없음: {pid}")
    title, problem, abstract = pid, "", ""
    if cp.exists():
        c = json.loads(cp.read_text())
        title = c.get("title", pid)
        problem = c.get("problem", "")
    if pp.exists():
        txt = json.loads(pp.read_text()).get("text", "")
        abstract = txt[:1800].strip()  # 초록+도입 발췌
    return {"id": pid, "title": title, "problem": problem, "abstract": abstract}


@router.post("/api/review_suggestions/regenerate")
def regenerate_review_suggestions():
    """검토 도우미를 증분 실행 — 카드 없는 신규 검토대기 개념만 제안 생성(LLM).
    기존 카드는 유지, 더는 대기 아닌 개념 카드는 정리. 갱신된 카드 리스트 반환."""
    run_step("review_helper.py",
             str(ROOT / "scripts" / "review_helper.py"), "--incremental")
    return review_suggestions()


@router.post("/api/concept/reviewed")
def set_reviewed(body: dict = Body(...)):
    """개념의 검토함 토글. {id, reviewed: bool} → reviewed.json에 기록."""
    cid = body.get("id")
    if not cid:
        raise HTTPException(400, "id 필요")
    flag = bool(body.get("reviewed"))
    s = _load_reviewed()
    if flag:
        s.add(cid)
    else:
        s.discard(cid)
    REVIEWED_PATH.write_text(
        json.dumps({"reviewed": sorted(s)}, ensure_ascii=False, indent=2)
    )
    return {"id": cid, "reviewed": flag}
