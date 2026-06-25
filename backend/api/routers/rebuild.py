"""재빌드 라우트 — 정본(원자료+사전)에서 Neo4j를 처음부터 다시 만들고 검증."""
from fastapi import APIRouter

from backend.api.deps import ROOT, run_step
from backend.api.graph_neo4j import graph_view_neo4j

router = APIRouter()


@router.post("/api/rebuild")
def rebuild():
    """정본(원자료+사전)에서 Neo4j를 처음부터 다시 만들고 검증까지 — 증분 드리프트 복구 버튼.

    1) pipeline/normalize_v2.py  : 원자료→normalized_v2.json(오라클 중간산물) + lexicon 반영
    2) graphdb/load.py      : Neo4j 전체 덮어쓰기(wipe+load) — 증분 드리프트 청소
    3) graphdb/verify.py    : 라이브 Neo4j == 재빌드 JSON 검증(실패 시 500 + diff)
    4) graph_view_neo4j     : Neo4j(라이브) 기준 카운트 반환
       (build_graph_view(JSON) 카운트 금지 — '성공인데 화면 옛것' 함정.)
    """
    run_step("normalize_v2.py", str(ROOT / "pipeline" / "normalize_v2.py"))
    run_step("load.py", str(ROOT / "graphdb" / "load.py"))
    run_step("verify.py", str(ROOT / "graphdb" / "verify.py"))

    view = graph_view_neo4j(include_papers=False)
    return {
        "ok": True,
        "nodes": len(view["nodes"]),
        "builds_on": len(view["builds_on"]),
    }
