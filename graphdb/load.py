"""① 적재: normalized_v2.json 전체(이분 그래프) -> Neo4j (멱등, MERGE).
build_graph_view가 읽는 필드 전부 저장: 개념(def_status), 논문(domain, home_concept).
node_embeddings_v2.json 이 있으면 id로 조인해 c.embedding/p.embedding 도 SET(있는 것만).
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from src import config

from graphdb.conn import get_driver

EMB_PATH = config.OUT_DIR / "node_embeddings_v2.json"


def _id(nid):
    return nid.split(":", 1)[1]


def load_embeddings():
    """node_embeddings_v2.json → {prefixed_id: vector}. 없으면 {}.

    store 키는 normalized_v2.json 노드 키와 동일한 접두사 형태("concept:rk"/"paper:id")라
    load()의 nid로 바로 조인된다.
    """
    if not EMB_PATH.exists():
        return {}
    return json.loads(EMB_PATH.read_text()).get("vectors", {})


def wipe(tx):
    """전체 적재 전 기존 그래프 삭제 — '전체 덮어쓰기'로 증분 드리프트(고아 엣지/노드)를 청소.
    (증분 경로 graphdb.write는 이 함수를 쓰지 않음 — load.py는 정본 재빌드 전용.)"""
    tx.run("MATCH (n) DETACH DELETE n")


def ensure_constraints(tx):
    tx.run("CREATE CONSTRAINT paper_id IF NOT EXISTS "
           "FOR (p:Paper) REQUIRE p.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT concept_id IF NOT EXISTS "
           "FOR (c:Concept) REQUIRE c.id IS UNIQUE")


def load(tx, nodes, edges, vectors):
    # 논문별 home concept = 그 논문이 처음 defines한 개념(defs[0]).
    home = {}
    for e in edges:
        if e["type"] == "defines":
            home.setdefault(e["from"], _id(e["to"]))

    for nid, n in nodes.items():
        vec = vectors.get(nid)              # 정의/문제 없는 노드는 벡터 없음 → SET 생략
        if n["type"] == "concept":
            tx.run("MERGE (c:Concept {id:$id}) "
                   "SET c.name=$name, c.definition=$defn, "
                   "    c.def_status=$ds, c.status=$st "
                   + ("SET c.embedding=$vec " if vec is not None else ""),
                   id=_id(nid), name=n.get("canonical", nid),
                   defn=n.get("definition", ""),
                   ds=n.get("def_status", "ok"), st=n.get("status", ""),
                   vec=vec)
        else:
            tx.run("MERGE (p:Paper {id:$id}) "
                   "SET p.title=$title, p.problem=$prob, p.paper_type=$pt, "
                   "    p.domain=$dom, p.home_concept=$home "
                   + ("SET p.embedding=$vec " if vec is not None else ""),
                   id=_id(nid), title=n.get("title", ""),
                   prob=n.get("problem", ""), pt=n.get("paper_type", "other"),
                   dom=n.get("domain", "general"), home=home.get(nid),
                   vec=vec)

    for e in edges:
        rel = "DEFINES" if e["type"] == "defines" else "BUILDS_ON"
        tx.run(f"MATCH (p:Paper {{id:$f}}), (c:Concept {{id:$t}}) "
               f"MERGE (p)-[:{rel}]->(c)",
               f=_id(e["from"]), t=_id(e["to"]))


def main():
    data = json.loads((config.OUT_DIR / "normalized_v2.json").read_text())
    nodes, edges = data["nodes"], data["edges"]
    vectors = load_embeddings()
    with get_driver() as drv:
        with drv.session() as s:
            s.execute_write(ensure_constraints)
            s.execute_write(wipe)                       # 드리프트 청소(전체 덮어쓰기)
            s.execute_write(load, nodes, edges, vectors)
            p = s.run("MATCH (p:Paper) RETURN count(p) AS n").single()["n"]
            c = s.run("MATCH (c:Concept) RETURN count(c) AS n").single()["n"]
            r = s.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
            ce = s.run("MATCH (c:Concept) WHERE c.embedding IS NOT NULL "
                       "RETURN count(c) AS n").single()["n"]
            pe = s.run("MATCH (p:Paper) WHERE p.embedding IS NOT NULL "
                       "RETURN count(p) AS n").single()["n"]
    print(f"적재 완료 — Paper {p}, Concept {c}, 관계 {r} "
          "(def_status, domain, home_concept 포함).")
    print(f"임베딩 — 개념 {ce}, 논문 {pe} (없으면 0).")


if __name__ == "__main__":
    main()
