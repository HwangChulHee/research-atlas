"""A-3: 추론으로 '숨은 개념 계보'를 끌어낸다.
규칙: 논문이 A를 defines + B를 buildsOn  =>  A buildsUpon B
"""
from rdflib import Graph, Namespace, BNode
from rdflib.namespace import OWL
from rdflib.collection import Collection
import owlrl

ATLAS = Namespace("https://github.com/HwangChulHee/agent-project/atlas#")


def main():
    g = Graph()
    g.parse("atlas_rag.ttl", format="turtle")
    before = len(g)

    # 스키마: 역속성 + 속성 사슬
    g.add((ATLAS.definedBy, OWL.inverseOf, ATLAS.defines))
    chain = BNode()
    Collection(g, chain, [ATLAS.definedBy, ATLAS.buildsOn])
    g.add((ATLAS.buildsUpon, OWL.propertyChainAxiom, chain))

    # 추론
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    print(f"트리플 {before} -> {len(g)} (추론으로 늘어남)\n")
    print("=== 도출된 개념->개념 계보 (저장 안 했던 것) ===")
    for s, o in sorted(g.subject_objects(ATLAS.buildsUpon)):
        sl, ol = str(s).split("#")[-1], str(o).split("#")[-1]
        flag = "   ⚠ self-loop (추출오류)" if sl == ol else ""
        print(f"  {sl}  buildsUpon  {ol}{flag}")


if __name__ == "__main__":
    main()
