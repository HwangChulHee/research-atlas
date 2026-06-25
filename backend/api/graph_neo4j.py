"""그래프 뷰를 Neo4j에서 빌드 (papers=false / papers=true 둘 다).

verify_neo4j.py 로 build_graph_view(JSON)와 전체 일치 검증된 로직.
드라이버는 모듈 로드 시 1회 생성(지연 연결이라 Neo4j 미기동이어도 import는 안전).

주의: Neo4j 의 Paper.id 는 접두사 없이 저장된다("1706.03762"). build_graph_view 는
논문 노드 키/엣지에 "paper:" 접두사를 유지하므로, papers=true 출력에선 다시 붙인다.
개념 id 는 양쪽 모두 접두사 없음.
"""
from graphdb.conn import get_driver

_driver = get_driver()  # 모듈 로드 시 1회 생성(지연 연결이라 import는 안전)

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

# papers=true 추가분.
_PAPER_NODES_CYPHER = """
MATCH (p:Paper)
RETURN p.id AS id, coalesce(p.title,'') AS title,
       coalesce(p.paper_type,'other') AS paper_type,
       coalesce(p.domain,'general') AS domain, coalesce(p.problem,'') AS problem
"""

_DEFINES_CYPHER = """
MATCH (p:Paper)-[:DEFINES]->(c:Concept)
RETURN p.id AS pid, c.id AS cid
"""

# 정의(defines) 없는 논문만 — 그 논문의 builds_on(논문→개념)으로 닻을 내려준다.
_PAPER_BUILDS_CYPHER = """
MATCH (p:Paper)-[:BUILDS_ON]->(c:Concept)
WHERE NOT (p)-[:DEFINES]->(:Concept)
RETURN p.id AS pid, c.id AS cid
"""


def graph_view_neo4j(include_papers: bool = False) -> dict:
    """build_graph_view 재현. papers=false/true 둘 다 Neo4j 에서 빌드."""
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
        view = {"nodes": nodes, "builds_on": builds_on}

        if include_papers:
            for r in s.run(_PAPER_NODES_CYPHER):
                view["nodes"][f"paper:{r['id']}"] = {
                    "type": "paper", "title": r["title"],
                    "paper_type": r["paper_type"], "domain": r["domain"],
                    "problem": r["problem"],
                }
            view["defines"] = [{"from": f"paper:{r['pid']}", "to": r["cid"]}
                               for r in s.run(_DEFINES_CYPHER)]
            view["paper_builds_on"] = [{"from": f"paper:{r['pid']}", "to": r["cid"]}
                                       for r in s.run(_PAPER_BUILDS_CYPHER)]
    return view
