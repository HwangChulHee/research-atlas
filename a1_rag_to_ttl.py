"""A-1: normalized_v2.json의 RAG 서브그래프 -> Turtle(.ttl)."""
import json, sys
from pathlib import Path
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, SKOS

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import config

ATLAS = Namespace("https://github.com/HwangChulHee/agent-project/atlas#")

SEED_PAPER = "paper:2005.11401"   # RAG 논문
N_FOLLOWERS = 2                    # concept:rag 를 딛고 선 후속 논문 N편


def slug(node_id: str):
    """'concept:rag' -> atlas:rag,  'paper:2005.11401' -> atlas:p2005.11401"""
    kind, name = node_id.split(":", 1)
    local = name if kind == "concept" else "p" + name
    return ATLAS[local.replace(" ", "_")]


def pick_subgraph(nodes, edges):
    keep = {SEED_PAPER}
    for e in edges:                          # RAG 논문이 양손으로 잡은 개념
        if e["from"] == SEED_PAPER:
            keep.add(e["to"])
    followers = [e["from"] for e in edges
                 if e["to"] == "concept:rag" and e["type"] == "builds_on"]
    for f in followers[:N_FOLLOWERS]:        # 후속 N편 + 그 개념들
        keep.add(f)
        for e in edges:
            if e["from"] == f:
                keep.add(e["to"])
    return keep


def main():
    data = json.loads((config.OUT_DIR / "normalized_v2.json").read_text())
    nodes, edges = data["nodes"], data["edges"]
    keep = pick_subgraph(nodes, edges)

    g = Graph()
    g.bind("atlas", ATLAS)
    g.bind("skos", SKOS)

    for nid in keep:                         # 노드
        n = nodes[nid]
        node = slug(nid)
        if n["type"] == "concept":
            g.add((node, RDF.type, SKOS.Concept))
            g.add((node, SKOS.prefLabel, Literal(n.get("canonical", nid), lang="en")))
            if n.get("definition"):
                g.add((node, SKOS.definition, Literal(n["definition"], lang="en")))
        else:
            g.add((node, RDF.type, ATLAS.Paper))
            if n.get("problem"):
                g.add((node, ATLAS.problem, Literal(n["problem"], lang="en")))
            g.add((node, ATLAS.paperType, Literal(n.get("paper_type", "other"))))

    for e in edges:                          # 엣지: 논문 -> 개념
        if e["from"] in keep and e["to"] in keep:
            pred = ATLAS.defines if e["type"] == "defines" else ATLAS.buildsOn
            g.add((slug(e["from"]), pred, slug(e["to"])))

    g.serialize(destination="atlas_rag.ttl", format="turtle")
    papers = sum(1 for k in keep if nodes[k]["type"] == "paper")
    concepts = sum(1 for k in keep if nodes[k]["type"] == "concept")
    print(f"서브그래프: 논문 {papers}, 개념 {concepts}, 트리플 {len(g)}개 -> atlas_rag.ttl\n")
    print(g.serialize(format="turtle"))


if __name__ == "__main__":
    main()
