"""읽기 단일 진입점. 라이브=Neo4j / 오프라인(ATLAS_OFFLINE=1)=normalized_v2.json.

graphdb/write.py 의 대칭 — '현재 그래프 상태'를 어디서 읽을지 한 곳에서 결정한다.

모드:
  ATLAS_OFFLINE=1  → 오프라인(eval 전용): 보조 읽기는 normalized_v2.json 직독.
                     수집은 write_paper 스킵 → eval 세계 전체가 JSON → Neo4j 완전 격리.
  (미설정)         → 라이브(기본): 보조 읽기는 Neo4j 직독 → 실시간.

라이브에서 Neo4j 다운 시 **조용한 JSON 폴백을 넣지 않는다** — staleness가 다시 새어들기 때문.
읽기는 명시적으로 실패하게 둬 사용자가 Neo4j 다운을 알게 한다(의도).
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORMALIZED = ROOT / "data" / "outputs" / "normalized_v2.json"


def is_offline() -> bool:
    return os.environ.get("ATLAS_OFFLINE") == "1"


def _json_nodes() -> dict:
    return json.loads(NORMALIZED.read_text())["nodes"]


def owned_paper_ids() -> set:
    """보유 arXiv ID 집합 (dedup용). 접두사 없는 id."""
    if is_offline():
        nodes = _json_nodes()
        return {k.split("paper:", 1)[1] for k in nodes if k.startswith("paper:")}
    from graphdb.conn import get_driver
    with get_driver() as drv, drv.session() as s:
        return {r["id"] for r in s.run("MATCH (p:Paper) RETURN p.id AS id")}


def concept_names() -> list:
    """필터 에이전트 어휘용 — 개념 canonical 이름 정렬 리스트."""
    if is_offline():
        nodes = _json_nodes()
        return sorted(v["canonical"] for v in nodes.values()
                      if v.get("type") == "concept")
    from graphdb.conn import get_driver
    with get_driver() as drv, drv.session() as s:
        return sorted(r["n"] for r in s.run("MATCH (c:Concept) RETURN c.name AS n"))


def node_meta() -> dict:
    """수집 상태보고 표시용 노드 메타. 키 = 'concept:rk'/'paper:id'(load_embeddings norm 호환).

    값 필드는 _concept_line(canonical/definition/def_status)·_paper_line(title/problem)이
    .get 으로 읽는 것을 모두 채운다 — 라이브도 v2 노드 스키마와 같은 키 형태로 직접 질의.
    (graph_view_neo4j 로 짓지 않음 — 그건 개념주도 변환이라 키 형태가 다름.)
    """
    if is_offline():
        return _json_nodes()
    from graphdb.conn import get_driver
    meta = {}
    with get_driver() as drv, drv.session() as s:
        for r in s.run("MATCH (c:Concept) RETURN c.id AS id, c.name AS canonical, "
                       "c.definition AS definition, "
                       "coalesce(c.def_status,'ok') AS def_status"):
            meta[f"concept:{r['id']}"] = {
                "type": "concept", "canonical": r["canonical"],
                "definition": r["definition"], "def_status": r["def_status"],
            }
        for r in s.run("MATCH (p:Paper) RETURN p.id AS id, coalesce(p.title,'') AS title, "
                       "coalesce(p.problem,'') AS problem"):
            meta[f"paper:{r['id']}"] = {
                "type": "paper", "title": r["title"], "problem": r["problem"],
            }
    return meta
