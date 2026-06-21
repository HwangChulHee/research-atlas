# builds_on 채점 결과 — 항목별 분석 (v1)

이 문서는 `eval/score_buildson.py`가 낸 채점 결과를 **항목 단위로 펼쳐** 읽기 쉽게 푼 분석이다. 정답지(`eval/goldset/labels.json`, 50편, frozen) 대비 파이프라인이 뽑은 builds_on(논문→방법적 조상 계보) 항목을, 논문 50편 각각에 대해 맞힘/틀리게추가/놓침으로 나누고, 틀린 것들을 종류별로 분류한다. **측정은 이미 끝났고, 여기서 데이터·점수를 바꾸지 않는다.**

## 용어

- **TP (맞힘)** — 정답에도 있고 파이프라인도 맞게 댄 항목.
- **FP (틀리게 더 붙임)** — 파이프라인이 댔는데 정답엔 없는 항목.
- **FN (놓침)** — 정답엔 있는데 파이프라인이 못 댄 항목.
- **lexicon 필터** — 파이프라인 날것(relate 출력) 중 사전(lexicon)에서 `approved`/`unreviewed`인 개념만 그래프에 노드로 남고, `pending`/`rejected`는 빠진다. 채점도 그래프에 실제로 남는 것(=필터 통과분)만 본다. 그래서 파이프라인이 옳게 뱉어도 그 개념이 아직 `pending`이면 채점에선 놓침(FN)으로 잡힌다.
- **P(정밀도)** = TP/(TP+FP), **R(재현율)** = TP/(TP+FN).

## 1. 점수 요약

| 그룹 | n | micro P | micro R | macro P | macro R | FN: lexicon탈락 | FN: 추출X |
|---|--:|--:|--:|--:|--:|--:|--:|
| 전체(50) | 50 | 0.562 | 0.683 | 0.708 | 0.785 | 3 | 16 |
| new_collected | 21 | 0.708 | 0.515 | 0.792 | 0.654 | 3 | 13 |
| from_corpus | 29 | 0.490 | 0.889 | 0.651 | 0.886 | 0 | 3 |

- **전체** micro P=0.562 / R=0.683 — 댄 것의 56%가 맞고, 정답의 68%를 잡았다.
- **new_collected** P=0.708 / R=0.515 — *정밀도는 높지만 재현율이 낮다*. 댄 건 대체로 맞는데 최근 논문의 형제 계보를 절반 가까이 놓친다.
- **from_corpus** P=0.490 / R=0.889 — *정반대*. 뻔한 조상은 거의 다 잡지만(R↑) intro의 비교·부품까지 과추출해 정밀도가 절반(P↓).
- macro는 논문별 P·R 평균(P는 pred≠∅ 논문만, R은 gold≠∅ 논문만 분모) — 큰 정답을 가진 소수 논문에 덜 휘둘린 값이라 micro보다 높다.

## 2. 논문별 상세 (50편)

> FN 태그: `[탈락]`=lexicon에서 pending/rejected라 잘림(검수하면 복구), `[추출X]`=애초에 안 뽑힘(abstract-only 한계). FP 태그: `[부품/도구]`=계보 아님(reject 후보), `[substrate]`=백본(문맥의존), `[방법오인]`=진짜 방법인데 이 논문에선 baseline/비교.

| id | 제목 | 그룹 | 정답(gold) | 맞힘(TP) | 틀리게추가(FP) | 놓침(FN) | P | R |
|---|---|---|---|---|---|---|--:|--:|
| 2503.09516 | SEARCH-R1 | new_collected | DeepSeek-R1-Zero, RAG | RAG | DeepSeek-R1[방법오인] | DeepSeek-R1-Zero[추출X] | 0.500 | 0.500 |
| 2501.12948 | DeepSeek-R1 | new_collected | CoT, DeepSeek-V3-Base | CoT | — | DeepSeek-V3-Base[탈락] | 1.000 | 0.500 |
| 2501.05366 | Search-o1 | new_collected | o1, RAG | RAG | — | o1[추출X] | 1.000 | 0.500 |
| 2505.17005 | R1-Searcher++ | new_collected | RAG | RAG | — | — | 1.000 | 1.000 |
| 2504.03160 | DeepResearcher | new_collected | R1-Searcher, RAG, ReSearch, SEARCH-R1 | RAG | — | R1-Searcher[추출X], ReSearch[추출X], SEARCH-R1[추출X] | 1.000 | 0.250 |
| 2503.19470 | ReSearch | new_collected | DeepSeek-R1, RAG | RAG | — | DeepSeek-R1[추출X] | 1.000 | 0.500 |
| 2502.01142 | DeepRAG | new_collected | RAG | RAG | — | — | 1.000 | 1.000 |
| 2503.23513 | RARE | new_collected | RAG | RAG | — | — | 1.000 | 1.000 |
| 2504.21776 | WebThinker | new_collected | RAG | RAG | — | — | 1.000 | 1.000 |
| 2502.13957 | RAG-Gym | new_collected | RAG | RAG | — | — | 1.000 | 1.000 |
| 2505.14146 | s3 | new_collected | DeepRetrieval, RAG, SEARCH-R1 | RAG | Self-RAG[방법오인] | DeepRetrieval[추출X], SEARCH-R1[추출X] | 0.500 | 0.333 |
| 2503.00223 | DeepRetrieval | new_collected | —(없음) | — | — | — | — | —(gold∅) |
| 2501.09136 | Agentic RAG Survey | new_collected | —(없음) | — | RAG[방법오인] | — | 0.000 | —(gold∅) |
| 2504.20073 | RAGEN | new_collected | —(없음) | — | — | — | — | —(gold∅) |
| 2504.14870 | OTC | new_collected | SEARCH-R1 | — | PPO[부품/도구] | SEARCH-R1[추출X] | 0.000 | 0.000 |
| 2509.25140 | ReasoningBank | new_collected | —(없음) | — | — | — | — | —(gold∅) |
| 2509.26383 | KG-R1 | new_collected | KG-RAG, RAG, ReKnoS, RoG, ToG | RAG | — | KG-RAG[탈락], ReKnoS[추출X], RoG[추출X], ToG[추출X] | 1.000 | 0.200 |
| 2510.07794 | HiPRAG | new_collected | RAG | RAG | — | — | 1.000 | 1.000 |
| 2510.20548 | GlobalRAG | new_collected | RAG, SEARCH-R1, TIRESRAG-R1 | RAG | — | SEARCH-R1[추출X], TIRESRAG-R1[탈락] | 1.000 | 0.333 |
| 2510.27569 | MARAG-R1 | new_collected | RAG | RAG | GraphRAG[방법오인], HyperGraphRAG[방법오인], SEARCH-R1[방법오인] | — | 0.250 | 1.000 |
| 2511.09109 | Bi-RAR | new_collected | RAG, SEARCH-R1 | RAG, SEARCH-R1 | — | — | 1.000 | 1.000 |
| 2002.08909 | REALM | from_corpus | kNN-LM | kNN-LM | BERT[substrate], RoBERTa[substrate], T5[substrate] | — | 0.250 | 1.000 |
| 2004.04906 | DPR | from_corpus | BERT, ORQA | BERT | — | ORQA[추출X] | 1.000 | 0.500 |
| 2004.12832 | ColBERT | from_corpus | BERT | BERT | — | — | 1.000 | 1.000 |
| 2201.11903 | Chain-of-Thought | from_corpus | —(없음) | — | — | — | — | —(gold∅) |
| 2203.11171 | Self-Consistency | from_corpus | CoT | CoT | — | — | 1.000 | 1.000 |
| 2205.10625 | Least-to-Most | from_corpus | CoT | CoT | — | — | 1.000 | 1.000 |
| 2210.03629 | ReAct | from_corpus | CoT | CoT | — | — | 1.000 | 1.000 |
| 2301.12652 | REPLUG | from_corpus | —(없음) | — | RAG[방법오인] | — | 0.000 | —(gold∅) |
| 2302.04761 | Toolformer | from_corpus | —(없음) | — | GPT-3[substrate] | — | 0.000 | —(gold∅) |
| 2303.11366 | Reflexion | from_corpus | ReAct | ReAct | Generative Agents[방법오인], HuggingGPT[방법오인], SayCan[방법오인], Toolformer[방법오인], WebGPT[방법오인] | — | 0.167 | 1.000 |
| 2305.04091 | Plan-and-Solve | from_corpus | CoT, Zero-shot-CoT | CoT, Zero-shot-CoT | — | — | 1.000 | 1.000 |
| 2305.14283 | Rewrite-Retrieve-Read | from_corpus | RAG | — | — | RAG[추출X] | — | 0.000 |
| 2305.16291 | Voyager | from_corpus | —(없음) | — | AutoGPT[방법오인], ReAct[방법오인], Reflexion[방법오인] | — | 0.000 | —(gold∅) |
| 2308.00352 | MetaGPT | from_corpus | —(없음) | — | AgentVerse[방법오인], AutoGPT[방법오인], ChatDev[방법오인], LangChain[방법오인] | — | 0.000 | —(gold∅) |
| 2310.04406 | LATS | from_corpus | ReAct | ReAct | Monte Carlo Tree Search[부품/도구] | — | 0.500 | 1.000 |
| 2310.11511 | Self-RAG | from_corpus | RAG | RAG | — | — | 1.000 | 1.000 |
| 2401.14887 | Power of Noise | from_corpus | —(없음) | — | RAG[방법오인] | — | 0.000 | —(gold∅) |
| 2401.15884 | CRAG | from_corpus | RAG | RAG | Self-RAG[방법오인] | — | 0.500 | 1.000 |
| 2401.18059 | RAPTOR | from_corpus | RAG | — | — | RAG[추출X] | — | 0.000 |
| 2403.10131 | RAFT | from_corpus | RAG | RAG | — | — | 1.000 | 1.000 |
| 2404.16130 | GraphRAG | from_corpus | RAG | RAG | — | — | 1.000 | 1.000 |
| 2405.14831 | HippoRAG | from_corpus | RAG | RAG | IRCoT[방법오인] | — | 0.500 | 1.000 |
| 2407.11005 | RAGBench | from_corpus | —(없음) | — | ARES[부품/도구], RAG[방법오인], RAGAS[부품/도구], TruLens[부품/도구] | — | 0.000 | —(gold∅) |
| 2408.04187 | MedGraphRAG | from_corpus | GraphRAG, RAG | GraphRAG, RAG | — | — | 1.000 | 1.000 |
| 2406.17526 | LumberChunker | from_corpus | RAG | RAG | — | — | 1.000 | 1.000 |
| 2410.05779 | LightRAG | from_corpus | RAG | RAG | — | — | 1.000 | 1.000 |
| 2502.04413 | MedRAG | from_corpus | RAG | RAG | — | — | 1.000 | 1.000 |
| 2502.14802 | From RAG to Memory (HippoRAG 2) | from_corpus | HippoRAG, RAG | HippoRAG, RAG | — | — | 1.000 | 1.000 |
| 2503.21322 | HyperGraphRAG | from_corpus | GraphRAG, RAG | GraphRAG, RAG | — | — | 1.000 | 1.000 |

## 3. FP 분석 — 정밀도를 깎는 것

틀리게 더 붙인 항목 총 **32건**. 종류별로 갈라야 "정밀도를 싸게 고칠 수 있나"의 답이 나온다.

### [부품/도구] component_tool — 5건

**부품/도구 (reject 후보, 싸게 제거 가능)** — PPO·MCTS·RAGAS 같은 학습 부품·평가도구. 영영 계보가 아니므로 lexicon에서 reject하면 그래프에서 전역 제거된다. 가장 싸게 정밀도를 올릴 수 있는 부분.

- PPO — OTC (2504.14870, new_collected)
- Monte Carlo Tree Search — LATS (2310.04406, from_corpus)
- ARES — RAGBench (2407.11005, from_corpus)
- RAGAS — RAGBench (2407.11005, from_corpus)
- TruLens — RAGBench (2407.11005, from_corpus)

### [substrate] substrate — 4건

**substrate / 백본 (문맥의존, 전역 reject 불가)** — BERT·GPT-3·T5 등. 이건 DPR·ColBERT 같은 논문에선 *정답 계보*이기도 해서 전역 reject가 불가능하다. 논문별로 baseline인지 계보인지 판단이 필요 → 사전 하나로 못 고침.

- BERT — REALM (2002.08909, from_corpus)
- RoBERTa — REALM (2002.08909, from_corpus)
- T5 — REALM (2002.08909, from_corpus)
- GPT-3 — Toolformer (2302.04761, from_corpus)

### [방법오인] method_misjudged — 23건

**방법 오인 (relate 판단 문제, 사전으로 못 고침)** — Self-RAG·ReAct·RAG·GraphRAG처럼 진짜 방법 노드인데 *이 논문에선* baseline/비교로 등장한 걸 계보로 오인한 것. 개념 자체는 유효(approved/unreviewed)라 lexicon으로 못 거른다. relate.py가 본문 맥락에서 "딛고 선 것"과 "비교 대상"을 구분해야 풀린다.

- DeepSeek-R1 — SEARCH-R1 (2503.09516, new_collected)
- Self-RAG — s3 (2505.14146, new_collected)
- RAG — Agentic RAG Survey (2501.09136, new_collected)
- GraphRAG — MARAG-R1 (2510.27569, new_collected)
- HyperGraphRAG — MARAG-R1 (2510.27569, new_collected)
- SEARCH-R1 — MARAG-R1 (2510.27569, new_collected)
- RAG — REPLUG (2301.12652, from_corpus)
- Generative Agents — Reflexion (2303.11366, from_corpus)
- HuggingGPT — Reflexion (2303.11366, from_corpus)
- SayCan — Reflexion (2303.11366, from_corpus)
- Toolformer — Reflexion (2303.11366, from_corpus)
- WebGPT — Reflexion (2303.11366, from_corpus)
- AutoGPT — Voyager (2305.16291, from_corpus)
- ReAct — Voyager (2305.16291, from_corpus)
- Reflexion — Voyager (2305.16291, from_corpus)
- AgentVerse — MetaGPT (2308.00352, from_corpus)
- AutoGPT — MetaGPT (2308.00352, from_corpus)
- ChatDev — MetaGPT (2308.00352, from_corpus)
- LangChain — MetaGPT (2308.00352, from_corpus)
- RAG — Power of Noise (2401.14887, from_corpus)
- Self-RAG — CRAG (2401.15884, from_corpus)
- IRCoT — HippoRAG (2405.14831, from_corpus)
- RAG — RAGBench (2407.11005, from_corpus)

## 4. FN 분석 — 재현율을 깎는 것

놓친 항목 총 **19건** = lexicon탈락 3 + 추출X 16.

### [탈락] lexicon_dropped — 검수하면 복구되는 놓침

파이프라인은 **맞게 뱉었는데** 그 개념이 사전에서 `pending`이라 그래프에서 잘렸다. lexicon 검수로 approve하면 즉시 TP로 살아난다 — *추출 품질 문제가 아니다*.

- DeepSeek-V3-Base — DeepSeek-R1 (2501.12948, new_collected, status=pending)
- KG-RAG — KG-R1 (2509.26383, new_collected, status=pending)
- TIRESRAG-R1 — GlobalRAG (2510.20548, new_collected, status=pending)

### [추출X] not_extracted — abstract-only의 본질적 한계

애초에 파이프라인이 뽑지도 못한 것. 대부분 related work에 나열되는 *형제 계보*(같은 시기 경쟁 방법)로, abstract+intro만 보는 현재 입력에선 "딛고 선 조상"으로 드러나지 않는다.

**new_collected (13건):**

- DeepSeek-R1-Zero — SEARCH-R1 (2503.09516)
- o1 — Search-o1 (2501.05366)
- R1-Searcher — DeepResearcher (2504.03160)
- ReSearch — DeepResearcher (2504.03160)
- SEARCH-R1 — DeepResearcher (2504.03160)
- DeepSeek-R1 — ReSearch (2503.19470)
- DeepRetrieval — s3 (2505.14146)
- SEARCH-R1 — s3 (2505.14146)
- SEARCH-R1 — OTC (2504.14870)
- ReKnoS — KG-R1 (2509.26383)
- RoG — KG-R1 (2509.26383)
- ToG — KG-R1 (2509.26383)
- SEARCH-R1 — GlobalRAG (2510.20548)

**from_corpus (3건):**

- ORQA — DPR (2004.04906)
- RAG — Rewrite-Retrieve-Read (2305.14283)
- RAG — RAPTOR (2401.18059)

## 5. 관찰 / 해석

**두 그룹이 정반대다.** from_corpus(오래된·확립된 논문)는 재현율↑·정밀도↓ — 뻔한 조상(거의 RAG)은 잘 잡지만 intro에 같이 언급되는 형제·baseline·부품까지 과추출한다. new_collected(최근 수집 논문)는 정밀도↑·재현율↓ — 댄 건 대체로 맞지만 최근 형제 계보를 놓치고, 일부는 사전 미검수(pending)로 탈락한다.

**둘 다 한 뿌리다.** abstract+intro는 "무엇이 계보고 무엇이 비교/부품인지"를 명시하지 않는다. 단순한 논문에선 언급된 방법을 죄다 계보로 과발화(정밀도↓), 복잡한 논문에선 본문 깊숙이 있는 형제 계보를 놓친다(재현율↓). 같은 입력 한계의 양면.

**고칠 수 있는 것 vs 구조적 한계.**

- *싸게 개선 가능(lexicon 작업)*: lexicon_dropped FN 3건(검수로 approve) + component_tool FP 5건(reject). 둘 다 사전 차원에서 끝난다.
- *구조적 한계(abstract-only)*: not_extracted FN 16건 + method_misjudged FP 23건. 이건 사전이 아니라 입력 범위·relate 판단의 문제라 lexicon으로 안 풀린다. substrate FP 4건은 문맥의존이라 전역 처리 불가(논문별 판단 필요).

> 요약: 사전 작업으로 손볼 수 있는 건 소수고, 점수를 크게 좌우하는 다수(method_misjudged FP, not_extracted FN)는 abstract+intro만 보는 입력의 본질적 한계다. 다음 레버는 lexicon이 아니라 relate가 보는 범위/맥락이다.
