"""그래프(읽기) + 검토 도우미 + 논문 상세 + 개인화(reviewed) 라우트."""
import json

from fastapi import APIRouter, Body, HTTPException

from backend.api.deps import DATA_DIR, NORMALIZED_V2_PATH, REVIEWED_PATH, ROOT, run_step
from backend.api.graph_neo4j import graph_view_neo4j

router = APIRouter()


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

    build_graph_view(JSON)는 롤백용으로 보존 — 라우팅만 Neo4j로 전환.
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
