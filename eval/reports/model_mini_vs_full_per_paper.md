# 모델 비교 — mini@0 vs full@0, 논문 단위 diff (분석 전용)

집계(정밀도 +0.20)는 `model_mini_vs_full.md`에 있다. 이 문서는 **논문 한 편씩** builds_on을 어떻게 다르게 뽑았는지 펼친다. 새 추출·LLM 호출 없음 — 기존 결과와 `exp_model_compare.py`의 채점 함수 재사용(숫자 정합성 게이트 통과). 항목은 resolve 후 rep_key 라벨, status로 그래프에서 빠진 pred는 채점과 동일하게 표시 안 함.

## ① 요약

| 그룹 | mini@0 P | mini@0 R | full@0 P | full@0 R |
|---|--:|--:|--:|--:|
| 전체(50) | 0.603 | 0.783 | 0.803 | 0.817 |
| new_collected | 0.667 | 0.667 | 0.893 | 0.758 |
| from_corpus | 0.556 | 0.926 | 0.727 | 0.889 |

- **diff 논문 17편 / 동일 33편** (builds_on 채점 결과 집합 기준, 합 50).
- 합산 게이트: mini ΣTP/FP/FN = (47, 31, 13), full = (49, 12, 11) — 집계 리포트와 일치 ✅.

## ② 차이 있는 논문 (FP 차 큰 순)

**Reflexion** (2303.11366, from_corpus)  ·  mini P0.167/R1.000 → full P1.000/R1.000
```
gold:  ReAct
mini:  ReAct[TP]  Generative Agents[FP·method_misjudged]  HuggingGPT[FP·method_misjudged]  SayCan[FP·method_misjudged]  Toolformer[FP·method_misjudged]  WebGPT[FP·method_misjudged]
full:  ReAct[TP]
```
→ full이 method_misjudged 5 제거

**MARAG-R1** (2510.27569, new_collected)  ·  mini P0.200/R1.000 → full P1.000/R1.000
```
gold:  RAG
mini:  RAG[TP]  GraphRAG[FP·method_misjudged]  HyperGraphRAG[FP·method_misjudged]  ReSearch[FP·method_misjudged]  SEARCH-R1[FP·method_misjudged]
full:  RAG[TP]
```
→ full이 method_misjudged 4 제거

**RAGBench** (2407.11005, from_corpus)  ·  mini P0.000/R— → full P0.000/R—
```
gold:  —(gold 없음)
mini:  ARES[FP·component_tool]  RAG[FP·method_misjudged]  RAGAS[FP·component_tool]  TruLens[FP·component_tool]
full:  RAG[FP·method_misjudged]
```
→ full이 component_tool 3 제거

**REALM** (2002.08909, from_corpus)  ·  mini P0.250/R1.000 → full P0.000/R0.000
```
gold:  kNN-LM
mini:  kNN-LM[TP]  BERT[FP·substrate]  RoBERTa[FP·substrate]  T5[FP·substrate]
full:  BERT[FP·substrate]
```
→ full이 substrate 2 제거; full이 kNN-LM 잃음

**SEARCH-R1** (2503.09516, new_collected)  ·  mini P0.500/R0.500 → full P1.000/R1.000
```
gold:  DeepSeek-R1-Zero  RAG
mini:  DeepSeek-R1-Zero[TP]  PPO[FP·component_tool]
full:  DeepSeek-R1-Zero[TP]  RAG[TP]
```
→ full이 component_tool 1 제거; full이 RAG 회복

**OTC** (2504.14870, new_collected)  ·  mini P—/R0.000 → full P0.500/R1.000
```
gold:  SEARCH-R1
mini:  —
full:  SEARCH-R1[TP]  PPO[FP·component_tool]
```
→ full이 component_tool 1 추가; full이 SEARCH-R1 회복

**s3** (2505.14146, new_collected)  ·  mini P0.500/R0.667 → full P0.500/R0.333
```
gold:  DeepRetrieval(미추출)  RAG  SEARCH-R1
mini:  RAG[TP]  SEARCH-R1[TP]  DeepSeek-R1-Zero[FP·method_misjudged]  Self-RAG[FP·method_misjudged]
full:  RAG[TP]  Self-RAG[FP·method_misjudged]
```
→ full이 method_misjudged 1 제거; full이 SEARCH-R1 잃음

**REPLUG** (2301.12652, from_corpus)  ·  mini P—/R— → full P0.000/R—
```
gold:  —(gold 없음)
mini:  —
full:  GPT-3[FP·substrate]
```
→ full이 substrate 1 추가

**Toolformer** (2302.04761, from_corpus)  ·  mini P0.000/R— → full P—/R—
```
gold:  —(gold 없음)
mini:  GPT-3[FP·substrate]
full:  —
```
→ full이 substrate 1 제거

**Agentic RAG Survey** (2501.09136, new_collected)  ·  mini P0.000/R— → full P—/R—
```
gold:  —(gold 없음)
mini:  RAG[FP·method_misjudged]
full:  —
```
→ full이 method_misjudged 1 제거

**From RAG to Memory (HippoRAG 2)** (2502.14802, from_corpus)  ·  mini P0.667/R1.000 → full P1.000/R1.000
```
gold:  HippoRAG  RAG
mini:  HippoRAG[TP]  RAG[TP]  Personalized PageRank[FP·method_misjudged]
full:  HippoRAG[TP]  RAG[TP]
```
→ full이 method_misjudged 1 제거

**R1-Searcher++** (2505.17005, new_collected)  ·  mini P0.500/R1.000 → full P1.000/R1.000
```
gold:  RAG
mini:  RAG[TP]  Monte Carlo Tree Search[FP·component_tool]
full:  RAG[TP]
```
→ full이 component_tool 1 제거

**HiPRAG** (2510.07794, new_collected)  ·  mini P0.500/R1.000 → full P1.000/R1.000
```
gold:  RAG
mini:  RAG[TP]  PPO[FP·component_tool]
full:  RAG[TP]
```
→ full이 component_tool 1 제거

**DPR** (2004.04906, from_corpus)  ·  mini P1.000/R0.500 → full P1.000/R1.000
```
gold:  BERT  ORQA
mini:  BERT[TP]
full:  BERT[TP]  ORQA[TP]
```
→ full이 ORQA 회복

**Rewrite-Retrieve-Read** (2305.14283, from_corpus)  ·  mini P1.000/R1.000 → full P—/R0.000
```
gold:  RAG
mini:  RAG[TP]
full:  —
```
→ full이 RAG 잃음

**DeepResearcher** (2504.03160, new_collected)  ·  mini P1.000/R0.750 → full P1.000/R1.000
```
gold:  R1-Searcher  RAG  ReSearch  SEARCH-R1
mini:  R1-Searcher[TP]  ReSearch[TP]  SEARCH-R1[TP]
full:  R1-Searcher[TP]  RAG[TP]  ReSearch[TP]  SEARCH-R1[TP]
```
→ full이 RAG 회복

**GlobalRAG** (2510.20548, new_collected)  ·  mini P1.000/R0.333 → full P1.000/R0.667
```
gold:  RAG  SEARCH-R1(미추출)  TIRESRAG-R1
mini:  TIRESRAG-R1[TP]
full:  RAG[TP]  TIRESRAG-R1[TP]
```
→ full이 RAG 회복

## ③ 동일한 논문 (채점 결과 같음)

<details><summary>33편 — 펼치기</summary>

| id | 제목 | 그룹 | P | R |
|---|---|---|--:|--:|
| 2501.12948 | DeepSeek-R1 | new_collected | 1.000 | 0.500 |
| 2501.05366 | Search-o1 | new_collected | 1.000 | 0.500 |
| 2503.19470 | ReSearch | new_collected | 1.000 | 1.000 |
| 2502.01142 | DeepRAG | new_collected | 1.000 | 1.000 |
| 2503.23513 | RARE | new_collected | 1.000 | 1.000 |
| 2504.21776 | WebThinker | new_collected | 0.500 | 1.000 |
| 2502.13957 | RAG-Gym | new_collected | 1.000 | 1.000 |
| 2503.00223 | DeepRetrieval | new_collected | — | — |
| 2504.20073 | RAGEN | new_collected | — | — |
| 2509.25140 | ReasoningBank | new_collected | — | — |
| 2509.26383 | KG-R1 | new_collected | 1.000 | 0.400 |
| 2511.09109 | Bi-RAR | new_collected | 1.000 | 1.000 |
| 2004.12832 | ColBERT | from_corpus | 1.000 | 1.000 |
| 2201.11903 | Chain-of-Thought | from_corpus | — | — |
| 2203.11171 | Self-Consistency | from_corpus | 1.000 | 1.000 |
| 2205.10625 | Least-to-Most | from_corpus | 1.000 | 1.000 |
| 2210.03629 | ReAct | from_corpus | 1.000 | 1.000 |
| 2305.04091 | Plan-and-Solve | from_corpus | 1.000 | 1.000 |
| 2305.16291 | Voyager | from_corpus | 0.000 | — |
| 2308.00352 | MetaGPT | from_corpus | — | — |
| 2310.04406 | LATS | from_corpus | 0.500 | 1.000 |
| 2310.11511 | Self-RAG | from_corpus | 1.000 | 1.000 |
| 2401.14887 | Power of Noise | from_corpus | 0.000 | — |
| 2401.15884 | CRAG | from_corpus | 0.500 | 1.000 |
| 2401.18059 | RAPTOR | from_corpus | — | 0.000 |
| 2403.10131 | RAFT | from_corpus | 1.000 | 1.000 |
| 2404.16130 | GraphRAG | from_corpus | 1.000 | 1.000 |
| 2405.14831 | HippoRAG | from_corpus | 1.000 | 1.000 |
| 2408.04187 | MedGraphRAG | from_corpus | 1.000 | 1.000 |
| 2406.17526 | LumberChunker | from_corpus | 1.000 | 1.000 |
| 2410.05779 | LightRAG | from_corpus | 1.000 | 1.000 |
| 2502.04413 | MedRAG | from_corpus | 1.000 | 1.000 |
| 2503.21322 | HyperGraphRAG | from_corpus | 1.000 | 1.000 |

</details>

## ④ 마무리

diff 17편에서 full이 없앤 FP는 method_misjudged 12, component_tool 6, substrate 3 (새로 낸 FP component_tool 1, substrate 1). TP는 full이 5 회복 / 3 잃음. 즉 full의 강점은 압도적으로 **method_misjudged(비교 baseline을 계보로 오인) 제거**와 **component_tool/substrate(부품·백본 혼입) 제거**에 몰려 있다 — 같은 v2 규칙을 더 정확히 적용한 결과지 새 정보를 본 게 아니다(입력 동일). 재현율 변화가 작은 것도 이와 일치(남은 FN은 입력에 없는 not_extracted). 채택 판단은 사람.
