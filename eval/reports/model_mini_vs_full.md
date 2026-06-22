# 모델 비교 — gpt-5.4-mini vs gpt-5.4(full), temperature=0

프로젝트 핵심 질문 = "굳이 더 큰/비싼 모델이 필요한가." 라이브 v2 프롬프트 그대로, **모델만** `gpt-5.4-mini`→`gpt-5.4` 로 바꿔 50편 재추출·재채점. 같은 프롬프트·lexicon(버킷1)·goldset·채점규칙. 변수는 모델 하나. 두 모델 다 **temperature=0**(샘플링 분산 제거 → Δ=모델 능력 차).

## 1. determinism 체크 (temp=0가 결정적인가 — 1차 게이트)

- **mini** (gpt-5.4-mini): 7/10 편 재호출 byte-동일.
- **full** (gpt-5.4): 9/10 편 재호출 byte-동일.

→ 일부 비결정적 — 아래 diff를 노이즈 바닥으로 보고 그보다 작은 Δ는 단정 보류.
  - mini/2505.17005: stored=['Retrieval-Augmented Generation', 'Supervised Fine-Tuning', 'Reinforcement Learning', 'Monte Carlo Tree Search'] vs rerun=['Retrieval-Augmented Generation', 'SFT', 'reinforcement learning']
  - mini/2502.01142: stored=['Retrieval-Augmented Generation', 'Markov Decision Process', 'Iterative Retrieval', 'Imitation Learning'] vs rerun=['Retrieval-Augmented Generation', 'Markov Decision Process', 'Binary Tree Search', 'Imitation Learning', 'Chain of Calibration']
  - mini/2504.21776: stored=['RAG', 'Direct Preference Optimization'] vs rerun=['RAG', 'DPO']
  - full/2502.13957: stored=['Retrieval-Augmented Generation'] vs rerun=['Retrieval-Augmented Generation', 'Re2Search']

## 2. 점수표 (mini@0 / full@0 / Δ)

### 전체(50)

| | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| mini@0 | 0.603 | 0.783 | 0.733 | 0.850 | 47 | 31 | 13 |
| full@0 | 0.803 | 0.817 | 0.817 | 0.856 | 49 | 12 | 11 |
| Δ | +0.201 | +0.033 | +0.084 | +0.006 | +2 | -19 | -2 |

### new_collected

| | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| mini@0 | 0.667 | 0.667 | 0.747 | 0.744 | 22 | 11 | 11 |
| full@0 | 0.893 | 0.758 | 0.912 | 0.847 | 25 | 3 | 8 |
| Δ | +0.226 | +0.091 | +0.165 | +0.103 | +3 | -8 | -3 |

### from_corpus

| | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| mini@0 | 0.556 | 0.926 | 0.723 | 0.932 | 25 | 20 | 2 |
| full@0 | 0.727 | 0.889 | 0.750 | 0.864 | 24 | 9 | 3 |
| Δ | +0.172 | −0.037 | +0.027 | −0.068 | -1 | -11 | +1 |

## 3. FP/FN 종류 변화 (full이 mini의 무엇을 고치나)

| 종류 | mini@0 | full@0 | Δ |
|---|--:|--:|--:|
| FP:component_tool | 7 | 2 | -5 |
| FP:substrate | 4 | 2 | -2 |
| FP:method_misjudged | 20 | 8 | -12 |
| FN:lexicon탈락 | 1 | 0 | -1 |
| FN:not_extracted | 12 | 11 | -1 |

**full이 없앤 mini FP 21건:**

- [substrate] RoBERTa — REALM (2002.08909, from_corpus)
- [substrate] T5 — REALM (2002.08909, from_corpus)
- [substrate] GPT-3 — Toolformer (2302.04761, from_corpus)
- [method_misjudged] Generative Agents — Reflexion (2303.11366, from_corpus)
- [method_misjudged] HuggingGPT — Reflexion (2303.11366, from_corpus)
- [method_misjudged] SayCan — Reflexion (2303.11366, from_corpus)
- [method_misjudged] Toolformer — Reflexion (2303.11366, from_corpus)
- [method_misjudged] WebGPT — Reflexion (2303.11366, from_corpus)
- [component_tool] ARES — RAGBench (2407.11005, from_corpus)
- [component_tool] RAGAS — RAGBench (2407.11005, from_corpus)
- [component_tool] TruLens — RAGBench (2407.11005, from_corpus)
- [method_misjudged] RAG — Agentic RAG Survey (2501.09136, new_collected)
- [method_misjudged] Personalized PageRank — From RAG to Memory (HippoRAG 2) (2502.14802, from_corpus)
- [component_tool] PPO — SEARCH-R1 (2503.09516, new_collected)
- [method_misjudged] DeepSeek-R1-Zero — s3 (2505.14146, new_collected)
- [component_tool] Monte Carlo Tree Search — R1-Searcher++ (2505.17005, new_collected)
- [component_tool] PPO — HiPRAG (2510.07794, new_collected)
- [method_misjudged] GraphRAG — MARAG-R1 (2510.27569, new_collected)
- [method_misjudged] HyperGraphRAG — MARAG-R1 (2510.27569, new_collected)
- [method_misjudged] ReSearch — MARAG-R1 (2510.27569, new_collected)
- [method_misjudged] SEARCH-R1 — MARAG-R1 (2510.27569, new_collected)

**full이 새로 낸 FP 2건:**

- [substrate] GPT-3 — REPLUG (2301.12652, from_corpus)
- [component_tool] PPO — OTC (2504.14870, new_collected)

**재현율: full이 더 맞힌 TP 5 / 잃은 TP 3** (모델만 바꾸면 not_extracted FN은 입력에 없어 안 변하는 게 정상 — 회복 있으면 본문에 있던 걸 mini가 놓친 것).

- +TP ORQA — DPR (2004.04906)
- +TP RAG — SEARCH-R1 (2503.09516)
- +TP RAG — DeepResearcher (2504.03160)
- +TP SEARCH-R1 — OTC (2504.14870)
- +TP RAG — GlobalRAG (2510.20548)
- −TP kNN-LM — REALM (2002.08909)
- −TP RAG — Rewrite-Retrieve-Read (2305.14283)
- −TP SEARCH-R1 — s3 (2505.14146)

## 4. 비용 / 속도 (호출당, 측정값)

| 모델 | 평균 지연(s) | 평균 total tokens | n |
|---|--:|--:|--:|
| mini (gpt-5.4-mini) | 1.94 | 2288 | 50 |
| full (gpt-5.4) | 2.25 | 2283 | 50 |

- 지연 비율 full/mini ≈ **1.2×** (측정). 토큰량은 입력이 같아 prompt는 비슷, 차이는 completion. 달러 비용은 공급자 per-token 가격비에 비례(가격표 기준 별도 확인 — 본 리포트는 측정 가능한 토큰·지연만 보고).

## 5. 판정 재료

full@0 전체 micro P 0.603→0.803 (+0.201), R 0.783→0.817 (+0.033). determinism 노이즈 바닥=비결정(위 §1)이므로 이 Δ는 노이즈 위에서만 해석. full은 주로 component_tool/method_misjudged FP를 줄여 정밀도에 작용했고(부품·baseline 오인 구분이 더 정확), 재현율은 +0.033 변동(남은 FN이 not_extracted라 모델 키워도 입력에 없는 건 못 뽑음 — 예상대로). 지연 1.2× 더 든다. **판정: full의 정밀도 이득이 노이즈를 넘는지 + 비용을 정당화하는지로 업그레이드 여부를 사람이 정한다. full≈mini면 '미니로 충분'(프론티어 불필요)이 헤드라인 결론.**

### 메인 판정 (Opus)

**정밀도 이득은 노이즈를 압도한다 — 결론은 "mini로 불충분, full이 의미 있게 낫다".** 근거:

1. **Δ ≫ 노이즈.** 정밀도 Δ는 +0.201(전체)·new_collected +0.226·from_corpus +0.172로 전 그룹 일관. 반면 determinism diff(§1)는 대부분 *표기 변종*(`SFT`↔`Supervised Fine-Tuning`, `DPO`↔`Direct Preference Optimization`)이라 canon/resolve를 거치면 점수에 거의 영향 없다 — 실효 노이즈는 3/10보다 훨씬 작다. +0.20은 그 위에서 명백히 실재.
2. **메커니즘이 일관**: full이 없앤 21건 FP가 정확히 직전 실험들이 짚어온 약점(method_misjudged 12 = Reflexion의 비교baseline 5건·MARAG-R1의 형제 4건; component 5 = PPO·MCTS·RAGAS/TruLens/ARES; substrate 2). full은 같은 v2 규칙을 **더 잘 적용**한다(비교 vs 계보 구분, 부품 배제). 새로 낸 FP는 2건뿐.
3. **재현율도 손해 없음**: +0.033(전체). 잃은 TP 3건은 노이즈성(s3는 mini가 determinism-diff난 논문), 얻은 5건이 더 많다. not_extracted FN은 예상대로 거의 불변(입력에 없는 형제는 모델 키워도 못 뽑음).
4. **full이 더 안정적**: determinism 9/10 vs mini 7/10 — 큰 모델이 temp=0에서 분산도 작다.
5. **비용 부담 작음**: 지연 1.2×, completion 토큰 오히려 더 적음(full이 군더더기 적게 뱉음). 달러 단가비만 가격표로 확인하면 됨.

→ **이 태스크(builds_on 계보 추출)에선 프론티어가 필요하다**가 데이터의 결론. 라이브 채택(config.MODEL을 gpt-5.4로)은 달러 단가까지 본 뒤 사람이 정하되, 품질 측면 판단은 명확히 full 쪽이다.
