"""① 적재: normalized_v2.json 전체(이분 그래프) -> Neo4j (멱등, MERGE).
build_graph_view가 읽는 필드 전부 저장: 개념(def_status), 논문(domain, home_concept).
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # graphdb.conn import용 (스크립트 실행 시 루트 미포함)
sys.path.insert(0, str(ROOT / "src"))
import config

from graphdb.conn import get_driver


def _id(nid):
    return nid.split(":", 1)[1]


def ensure_constraints(tx):
    tx.run("CREATE CONSTRAINT paper_id IF NOT EXISTS "
           "FOR (p:Paper) REQUIRE p.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT concept_id IF NOT EXISTS "
           "FOR (c:Concept) REQUIRE c.id IS UNIQUE")


def load(tx, nodes, edges):
    # 논문별 home concept = 그 논문이 처음 defines한 개념(defs[0]).
    home = {}
    for e in edges:
        if e["type"] == "defines":
            home.setdefault(e["from"], _id(e["to"]))

    for nid, n in nodes.items():
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
        rel = "DEFINES" if e["type"] == "defines" else "BUILDS_ON"
        tx.run(f"MATCH (p:Paper {{id:$f}}), (c:Concept {{id:$t}}) "
               f"MERGE (p)-[:{rel}]->(c)",
               f=_id(e["from"]), t=_id(e["to"]))


def main():
    data = json.loads((config.OUT_DIR / "normalized_v2.json").read_text())
    nodes, edges = data["nodes"], data["edges"]
    with get_driver() as drv:
        with drv.session() as s:
            s.execute_write(ensure_constraints)
            s.execute_write(load, nodes, edges)
            p = s.run("MATCH (p:Paper) RETURN count(p) AS n").single()["n"]
            c = s.run("MATCH (c:Concept) RETURN count(c) AS n").single()["n"]
            r = s.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
    print(f"적재 완료 — Paper {p}, Concept {c}, 관계 {r} "
          "(def_status, domain, home_concept 포함).")


if __name__ == "__main__":
    main()
