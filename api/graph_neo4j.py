"""papers=false 그래프 뷰를 Neo4j에서 빌드.

verify_neo4j.py 로 build_graph_view(papers=false)와 전체 일치 검증된 로직.
드라이버는 모듈 로드 시 1회 생성(지연 연결이라 Neo4j 미기동이어도 import는 안전).
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
_URI = os.environ["NEO4J_URI"]
_AUTH = (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
_driver = GraphDatabase.driver(_URI, auth=_AUTH)

_NODES_CYPHER = """
MATCH (c:Concept)
OPTIONAL MATCH (c)<-[:DEFINES|BUILDS_ON]-(p:Paper)
WITH c, collect(DISTINCT p.id) AS papers
OPTIONAL MATCH (c)<-[:DEFINES]-(dp:Paper)
WITH c, papers, head(collect(dp)) AS home
RETURN c.id AS id, c.name AS canonical, c.definition AS definition,
       coalesce(c.def_status,'ok') AS def_status, c.status AS status, papers,
       coalesce(home.paper_type,'technique') AS ptype,
       coalesce(home.domain,'general') AS domain
"""

_BUILDS_CYPHER = """
MATCH (p:Paper)-[:BUILDS_ON]->(b:Concept)
MATCH (a:Concept {id:p.home_concept})
WHERE a.id <> b.id
RETURN DISTINCT a.id AS src, b.id AS dst
"""


def graph_view_neo4j(include_papers: bool = False) -> dict:
    """build_graph_view(papers=false) 재현. papers=true는 아직 미지원(상위에서 라우팅)."""
    if include_papers:
        raise NotImplementedError("papers=true는 아직 Neo4j 미이전 — main.py가 JSON으로 라우팅")
    with _driver.session() as s:
        nodes = {}
        for r in s.run(_NODES_CYPHER):
            nodes[r["id"]] = {
                "canonical": r["canonical"], "definition": r["definition"],
                "def_status": r["def_status"], "status": r["status"],
                "papers": sorted(r["papers"]),
                "ptype": r["ptype"], "domain": r["domain"],
            }
        builds_on = [{"from": r["src"], "to": r["dst"]} for r in s.run(_BUILDS_CYPHER)]
    return {"nodes": nodes, "builds_on": builds_on}
