"""① 적재: normalized_v2.json의 RAG 서브그래프 -> Neo4j (멱등).
build_graph_view가 읽는 필드 전부 저장: 개념(def_status), 논문(domain, home_concept).
"""
import json, os, sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import config

load_dotenv(Path(__file__).resolve().parent / ".env")
URI = os.environ["NEO4J_URI"]
AUTH = (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])

SEED_PAPER = "paper:2005.11401"
N_FOLLOWERS = 2


def pick_subgraph(nodes, edges):
    keep = {SEED_PAPER}
    for e in edges:
        if e["from"] == SEED_PAPER:
            keep.add(e["to"])
    followers = [e["from"] for e in edges
                 if e["to"] == "concept:rag" and e["type"] == "builds_on"]
    for f in followers[:N_FOLLOWERS]:
        keep.add(f)
        for e in edges:
            if e["from"] == f:
                keep.add(e["to"])
    return keep


def _id(nid):
    return nid.split(":", 1)[1]


def ensure_constraints(tx):
    tx.run("CREATE CONSTRAINT paper_id IF NOT EXISTS "
           "FOR (p:Paper) REQUIRE p.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT concept_id IF NOT EXISTS "
           "FOR (c:Concept) REQUIRE c.id IS UNIQUE")


def load(tx, nodes, edges, keep):
    home = {}
    for e in edges:
        if e["from"] in keep and e["type"] == "defines":
            home.setdefault(e["from"], _id(e["to"]))

    for nid in keep:
        n = nodes[nid]
        if n["type"] == "concept":
            tx.run("MERGE (c:Concept {id:$id}) "
                   "SET c.name=$name, c.definition=$defn, "
                   "    c.def_status=$ds, c.status=$st",
                   id=_id(nid), name=n.get("canonical", nid),
                   defn=n.get("definition", ""),
                   ds=n.get("def_status", "ok"), st=n.get("status", ""))
        else:
            tx.run("MERGE (p:Paper {id:$id}) "
                   "SET p.title=$title, p.problem=$prob, p.paper_type=$pt, "
                   "    p.domain=$dom, p.home_concept=$home",
                   id=_id(nid), title=n.get("title", ""),
                   prob=n.get("problem", ""), pt=n.get("paper_type", "other"),
                   dom=n.get("domain", "general"), home=home.get(nid))

    for e in edges:
        if e["from"] in keep and e["to"] in keep:
            rel = "DEFINES" if e["type"] == "defines" else "BUILDS_ON"
            tx.run(f"MATCH (p:Paper {{id:$f}}), (c:Concept {{id:$t}}) "
                   f"MERGE (p)-[:{rel}]->(c)",
                   f=_id(e["from"]), t=_id(e["to"]))


def main():
    data = json.loads((config.OUT_DIR / "normalized_v2.json").read_text())
    nodes, edges = data["nodes"], data["edges"]
    keep = pick_subgraph(nodes, edges)
    with GraphDatabase.driver(URI, auth=AUTH) as drv:
        with drv.session() as s:
            s.execute_write(ensure_constraints)
            s.execute_write(load, nodes, edges, keep)
    print("적재 완료 (def_status, domain, home_concept 포함).")


if __name__ == "__main__":
    main()
