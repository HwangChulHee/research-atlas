"""② 검증: Neo4j 가 build_graph_view(papers=false) 전체를 재현하나.
view_from_neo4j() = 다음 단계에서 api/main.py로 들어갈 본체.
"""
import json, os, sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import config
from load_neo4j import pick_subgraph, _id

load_dotenv(Path(__file__).resolve().parent / ".env")
URI = os.environ["NEO4J_URI"]
AUTH = (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])

NODES_CYPHER = """
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

BUILDS_CYPHER = """
MATCH (p:Paper)-[:BUILDS_ON]->(b:Concept)
MATCH (a:Concept {id:p.home_concept})
WHERE a.id <> b.id
RETURN DISTINCT a.id AS src, b.id AS dst
"""


def view_from_neo4j():
    """build_graph_view(papers=false) 재현. (다음 단계 api 본체)"""
    with GraphDatabase.driver(URI, auth=AUTH) as drv:
        with drv.session() as s:
            nodes = {}
            for r in s.run(NODES_CYPHER):
                nodes[r["id"]] = {
                    "canonical": r["canonical"], "definition": r["definition"],
                    "def_status": r["def_status"], "status": r["status"],
                    "papers": sorted(r["papers"]),
                    "ptype": r["ptype"], "domain": r["domain"],
                }
            builds = {(r["src"], r["dst"]) for r in s.run(BUILDS_CYPHER)}
    return nodes, builds


def expected_from_json():
    data = json.loads((config.OUT_DIR / "normalized_v2.json").read_text())
    nodes, edges = data["nodes"], data["edges"]
    keep = pick_subgraph(nodes, edges)
    pm = {k: v for k, v in nodes.items() if v["type"] == "paper" and k in keep}
    out = {}
    for cid, nd in nodes.items():
        if nd["type"] == "concept" and cid in keep:
            out[_id(cid)] = {"canonical": nd["canonical"],
                "definition": nd.get("definition", ""),
                "def_status": nd.get("def_status", "ok"), "status": nd.get("status"),
                "papers": [], "ptype": "technique", "domain": "general"}
    cp, chp = {}, {}
    for e in edges:
        if e["from"] not in keep:
            continue
        pid, rk = _id(e["from"]), _id(e["to"])
        cp.setdefault(rk, [])
        if pid not in cp[rk]:
            cp[rk].append(pid)
        if e["type"] == "defines":
            chp.setdefault(rk, e["from"])
    for rk, node in out.items():
        node["papers"] = sorted(cp.get(rk, []))
        h = chp.get(rk)
        if h and h in pm:
            node["ptype"] = pm[h].get("paper_type") or "technique"
            node["domain"] = pm[h].get("domain") or "general"
    builds = set()
    home = {}
    for e in edges:
        if e["from"] in keep and e["type"] == "defines":
            home.setdefault(e["from"], _id(e["to"]))
    for e in edges:
        if e["from"] in keep and e["type"] == "builds_on":
            src = home.get(e["from"]); tgt = _id(e["to"])
            if src and tgt != src and tgt in out:
                builds.add((src, tgt))
    return out, builds


def main():
    en, eb = expected_from_json()
    an, ab = view_from_neo4j()
    ok = True
    if en != an:
        ok = False
        print("❌ 개념 노드 불일치:")
        for k in sorted(set(en) | set(an)):
            if en.get(k) != an.get(k):
                print(f"  [{k}]\n    JSON : {en.get(k)}\n    Neo4j: {an.get(k)}")
    if eb != ab:
        ok = False
        print("❌ builds_on 불일치:", "JSON에만", sorted(eb-ab), "/ Neo4j에만", sorted(ab-eb))
    if ok:
        print(f"✅ 전체 일치 — 개념노드 {len(en)}개, builds_on {len(eb)}개.")
        print("   view_from_neo4j() 가 build_graph_view(papers=false)를 재현함.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
