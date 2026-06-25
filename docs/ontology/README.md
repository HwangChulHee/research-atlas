> ⚠️ legacy 실험 — 현재 빌드 경로 아님. (현행 동작은 [`../HOW_IT_WORKS.md`](../HOW_IT_WORKS.md) 참조)

# 온톨로지 설계·추론 검증 → Neo4j 구현 (학습 산출물)

research-atlas의 데이터는 **이분 그래프**다: 노드는 `paper`/`concept` 두 종류,
엣지는 전부 논문→개념(`defines`/`builds_on`) 두 종류뿐이고, **개념→개념 직접 엣지는 없다.**
개념 계보(어떤 개념이 어떤 개념을 딛고 섰나)는 저장하지 않고 **논문을 경유해 유도**한다.

이 유도 규칙이 임의의 코드 트릭이 아니라 **온톨로지적으로 타당한 추론**임을 먼저 RDF/OWL로
검증한 뒤, 그 규칙을 Neo4j 읽기 경로(`backend/api/graph_neo4j.py`)에 옮겼다. 그 작업 기록이 이 폴더다.

- **`a1_rag_to_ttl.py`** — `normalized_v2.json`의 RAG 서브그래프를 Turtle(`atlas_rag.ttl`)로 직렬화.
  개념은 `skos:Concept`(prefLabel/definition), 논문은 `atlas:Paper`, 엣지는 `atlas:defines`/`atlas:buildsOn`.
- **`atlas_rag.ttl`** — 위 산출물(RDF 그래프).
- **`a3_infer_lineage.py`** — OWL 추론으로 숨은 개념 계보를 끌어낸다.
  스키마는 단 두 줄: `definedBy ≡ inverseOf(defines)`, 그리고 속성 사슬
  `buildsUpon ⊑ definedBy ∘ buildsOn`. 즉 **"논문이 A를 정의하고 B를 딛고 서면, A는 B 위에 선다."**
  `owlrl`로 폐포를 전개하면 저장하지 않았던 `concept→concept` 계보가 도출된다(self-loop = 추출 오류로 표면화).
  `buildsOn`이 lineage-only로 전환된 뒤(점수비교 baseline 제외)로는 이 사슬이 진짜 방법적 계보만
  전개하므로 `buildsUpon` 추론의 의미 정확도가 올라간다(GPT-4 류 baseline 허브가 만들던 가짜 계보 소거).

**서사**: RDF/OWL로 "논문 경유 개념 계보"가 표준 추론(property chain)으로 환원됨을 확인하고,
그 추론을 운영 그래프 DB(Neo4j)의 Cypher(`home_concept → builds_on 대상`)로 구현했다.
프로덕션 읽기 경로가 이 규칙과 일치함은 `graphdb/verify.py`가 `build_graph_view`(JSON 정본)와
전체 대조해 보증한다.

## 실행

```bash
uv run python docs/ontology/a1_rag_to_ttl.py   # normalized_v2.json → atlas_rag.ttl
uv run python docs/ontology/a3_infer_lineage.py # OWL 추론으로 개념 계보 도출
```
