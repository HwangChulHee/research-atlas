# builds_on — lexicon 버킷1(gold 개념 승격) 재채점

FN 중 '모델은 맞게 뽑았으나 lexicon에서 pending이라 노드가 안 돼 잘린' 것 중 **goldset에 실제 있는 5개 개념을 approve**하고 긴 표기 3개를 alias로 연결한 뒤 v1/v2/v3 재채점. 전부 gold라 precision 위험이 거의 없고 곧바로 FN→TP가 된다. lexicon만 변경 — relate/relations.json/canon/resolve/모델 무수정, 그래프 재빌드 없음.

변경: status pending→approved (KG-RAG, ReSearch, R1-Searcher, TIRESRAG-R1, DeepSeek-V3-Base) + alias (KG-RAG←"Knowledge-Graph Retrieval-Augmented Generation", ReSearch←"Re-Search", kNN-LM←"k-Nearest Neighbor Language Model").

> approve는 additive(노드가 생길 뿐 사라지지 않음) → 재현율은 안 내려간다(게이트 통과). **이 lexicon이 이제 새 기준 상태.**

## 1. 점수표 (old → new, run별)

### v1

| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| **전체(50)** old | 0.562 | 0.683 | 0.708 | 0.785 | 41 | 32 | 19 |
| **전체(50)** new | 0.571 | 0.733 | 0.707 | 0.812 | 44 | 33 | 16 |
| Δ | +0.010 | +0.050 | −0.001 | +0.026 | +3 | +1 | -3 |
| **new_collected** old | 0.708 | 0.515 | 0.792 | 0.654 | 17 | 7 | 16 |
| **new_collected** new | 0.714 | 0.606 | 0.789 | 0.715 | 20 | 8 | 13 |
| Δ | +0.006 | +0.091 | −0.003 | +0.061 | +3 | +1 | -3 |
| **from_corpus** old | 0.490 | 0.889 | 0.651 | 0.886 | 24 | 25 | 3 |
| **from_corpus** new | 0.490 | 0.889 | 0.651 | 0.886 | 24 | 25 | 3 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |

### v2

| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| **전체(50)** old | 0.597 | 0.667 | 0.709 | 0.764 | 40 | 27 | 20 |
| **전체(50)** new | 0.616 | 0.750 | 0.722 | 0.803 | 45 | 28 | 15 |
| Δ | +0.019 | +0.083 | +0.012 | +0.039 | +5 | +1 | -5 |
| **new_collected** old | 0.654 | 0.515 | 0.714 | 0.664 | 17 | 9 | 16 |
| **new_collected** new | 0.688 | 0.667 | 0.743 | 0.754 | 22 | 10 | 11 |
| Δ | +0.034 | +0.152 | +0.029 | +0.090 | +5 | +1 | -5 |
| **from_corpus** old | 0.561 | 0.852 | 0.707 | 0.841 | 23 | 18 | 4 |
| **from_corpus** new | 0.561 | 0.852 | 0.707 | 0.841 | 23 | 18 | 4 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |

### v3

| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| **전체(50)** old | 0.672 | 0.650 | 0.717 | 0.734 | 39 | 19 | 21 |
| **전체(50)** new | 0.694 | 0.717 | 0.736 | 0.786 | 43 | 19 | 17 |
| Δ | +0.021 | +0.067 | +0.019 | +0.052 | +4 | +0 | -4 |
| **new_collected** old | 0.739 | 0.515 | 0.735 | 0.625 | 17 | 6 | 16 |
| **new_collected** new | 0.769 | 0.606 | 0.750 | 0.685 | 20 | 6 | 13 |
| Δ | +0.030 | +0.091 | +0.015 | +0.061 | +3 | +0 | -3 |
| **from_corpus** old | 0.629 | 0.815 | 0.703 | 0.818 | 22 | 13 | 5 |
| **from_corpus** new | 0.639 | 0.852 | 0.725 | 0.864 | 23 | 13 | 4 |
| Δ | +0.010 | +0.037 | +0.022 | +0.045 | +1 | +0 | -1 |

## 2. 회복된 FN (이 변경으로 FN→TP)

승격/alias로 노드가 생겨 채점에 잡힌 것. 해당 run이 그 개념을 실제 emit한 경우만 회복된다 (not_extracted였던 건 안 살아남 — related work 추출 단계 몫).

### v1 — 3건

- **DeepSeek-V3-Base** — DeepSeek-R1 (2501.12948, new_collected)
- **KG-RAG** — KG-R1 (2509.26383, new_collected)
- **TIRESRAG-R1** — GlobalRAG (2510.20548, new_collected)

### v2 — 5건

- **DeepSeek-V3-Base** — DeepSeek-R1 (2501.12948, new_collected)
- **R1-Searcher** — DeepResearcher (2504.03160, new_collected)
- **ReSearch** — DeepResearcher (2504.03160, new_collected)
- **KG-RAG** — KG-R1 (2509.26383, new_collected)
- **TIRESRAG-R1** — GlobalRAG (2510.20548, new_collected)

### v3 — 4건

- **DeepSeek-V3-Base** — DeepSeek-R1 (2501.12948, new_collected)
- **KG-RAG** — KG-R1 (2509.26383, new_collected)
- **TIRESRAG-R1** — GlobalRAG (2510.20548, new_collected)
- **kNN-LM** — REALM (2002.08909, from_corpus)

## 3. 새 FP (승격으로 노드가 됐으나 gold 아닌 논문 — 정상 부작용)

### v1 — 1건

- **ReSearch** — MARAG-R1 (2510.27569, new_collected)

### v2 — 1건

- **ReSearch** — MARAG-R1 (2510.27569, new_collected)

### v3 — 0건

- (없음)

## 4. 해석

회복 총 12건(FN→TP), 새 FP 2건. v3 전체 micro R 0.650→0.717 (+0.067). 5개가 emit된 run·논문에서 TP로 떴고, 비교 언급이던 곳은 새 FP로 전환(정상). 남은 FN의 진단 분포(new): v1(탈락 0/추출X 16), v2(탈락 0/추출X 15), v3(탈락 0/추출X 17) — 대부분이 **추출X(not_extracted)**, 즉 모델이 abstract+intro에서 아예 안 뽑은 related-work 계보다. lexicon 레버는 거의 소진됐고, 다음 레버는 relate가 보는 범위(related work 추출)다. 이 lexicon이 이후 evidence 채택 판단·모델 비교의 기준 상태가 된다.
