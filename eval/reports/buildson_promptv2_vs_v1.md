# builds_on — relate 프롬프트 v2 vs v1 (한 변수 비교)

같은 모델(`config.MODEL=gpt-5.4-mini`)·같은 lexicon(frozen)·같은 goldset(50편, frozen)·같은 채점 규칙으로, **relate 프롬프트만** v1→v2로 바꿨을 때의 변화. 측정 전용 — 채택 여부는 사람이 숫자를 보고 정한다.

- v1(baseline) pred = `data/outputs/{id}.relations.json` (보존)
- v2 pred = `eval/experiments/relate_v2/{id}.relations.json`
- v1 재계산이 HANDOFF §7 기존 채점 숫자를 재현함을 확인하고 작성됨(검증 게이트 통과).

## 1. 점수 비교 (v1 / v2 / Δ)

| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| **전체(50)** v1 | 0.562 | 0.683 | 0.708 | 0.785 | 41 | 32 | 19 |
| **전체(50)** v2 | 0.597 | 0.667 | 0.709 | 0.764 | 40 | 27 | 20 |
| Δ | +0.035 | −0.017 | +0.001 | −0.021 | -1 | -5 | +1 |
| **new_collected** v1 | 0.708 | 0.515 | 0.792 | 0.654 | 17 | 7 | 16 |
| **new_collected** v2 | 0.654 | 0.515 | 0.714 | 0.664 | 17 | 9 | 16 |
| Δ | −0.054 | +0.000 | −0.078 | +0.010 | +0 | +2 | +0 |
| **from_corpus** v1 | 0.490 | 0.889 | 0.651 | 0.886 | 24 | 25 | 3 |
| **from_corpus** v2 | 0.561 | 0.852 | 0.707 | 0.841 | 23 | 18 | 4 |
| Δ | +0.071 | −0.037 | +0.056 | −0.045 | -1 | -7 | +1 |

> Δ = v2 − v1. (micro P↑ AND R not↓ 가 채택 신호.)

## 2. FP 변화 (정밀도)

v1 FP 32건 → v2 FP 27건. 사라진 FP **11**, 새로 생긴 FP **6**.

| 종류 | 사라진 FP(v1→없음) | 새 FP(v2에서 생김) | 순변화 |
|---|--:|--:|--:|
| component_tool | −1 | +2 | +1 |
| substrate | −2 | +0 | -2 |
| method_misjudged | −8 | +4 | -4 |

**method_misjudged FP 순변화: -4** (v1 23 → v2 19).

**사라진 FP (정밀도 개선):**

- [method_misjudged] RAG — REPLUG (2301.12652, from_corpus)
- [method_misjudged] Generative Agents — Reflexion (2303.11366, from_corpus)
- [method_misjudged] HuggingGPT — Reflexion (2303.11366, from_corpus)
- [method_misjudged] SayCan — Reflexion (2303.11366, from_corpus)
- [method_misjudged] Toolformer — Reflexion (2303.11366, from_corpus)
- [method_misjudged] WebGPT — Reflexion (2303.11366, from_corpus)
- [method_misjudged] IRCoT — HippoRAG (2405.14831, from_corpus)
- [method_misjudged] DeepSeek-R1 — SEARCH-R1 (2503.09516, new_collected)
- [component_tool] PPO — OTC (2504.14870, new_collected)
- [substrate] RoBERTa — REALM (2002.08909, from_corpus)
- [substrate] T5 — REALM (2002.08909, from_corpus)

**새로 생긴 FP (정밀도 악화):**

- [method_misjudged] GPT-4 — Voyager (2305.16291, from_corpus)
- [method_misjudged] Personalized PageRank — From RAG to Memory (HippoRAG 2) (2502.14802, from_corpus)
- [method_misjudged] StarPO — RAGEN (2504.20073, new_collected)
- [method_misjudged] Direct Preference Optimization — WebThinker (2504.21776, new_collected)
- [component_tool] PPO — SEARCH-R1 (2503.09516, new_collected)
- [component_tool] PPO — HiPRAG (2510.07794, new_collected)

## 3. FN 변화 + 회귀 체크 (재현율)

v1 FN 19건 → v2 FN 20건. 회복된 FN **3**, 새로 놓친 FN **4**.
TP: v1 41 → v2 40 (새로 맞힘 3, 잃음 4).

### 회복된 FN (v1 놓침 → v2 맞힘 또는 더이상 FN아님)

- DeepSeek-R1-Zero — SEARCH-R1 (2503.09516, new_collected) [v1: not_extracted → v2 TP]
- DeepSeek-R1 — ReSearch (2503.19470, new_collected) [v1: not_extracted → v2 TP]
- SEARCH-R1 — DeepResearcher (2504.03160, new_collected) [v1: not_extracted → v2 TP]

### 새로 놓친 FN (v1엔 없던 놓침이 v2에서 생김)

- kNN-LM — REALM (2002.08909, from_corpus) [v2: not_extracted]
- CoT — DeepSeek-R1 (2501.12948, new_collected) [v2: not_extracted]
- RAG — DeepResearcher (2504.03160, new_collected) [v2: not_extracted]
- RAG — GlobalRAG (2510.20548, new_collected) [v2: not_extracted]

### ⚠️ 회귀 — v1에서 TP였는데 v2에서 잃은 항목 (가장 중요)

v1에서 맞혔던 것을 v2가 놓친 것. gold 항목이므로 v2에선 FN(아래 진단).

- kNN-LM — REALM (2002.08909, from_corpus) [v2 진단: not_extracted]
- CoT — DeepSeek-R1 (2501.12948, new_collected) [v2 진단: not_extracted]
- RAG — DeepResearcher (2504.03160, new_collected) [v2 진단: not_extracted]
- RAG — GlobalRAG (2510.20548, new_collected) [v2 진단: not_extracted]

## 4. 핵심 점검

### (a) 패러다임 보호 작동? — RAPTOR / Rewrite-Retrieve-Read 가 RAG를 잡았나

| 논문 | id | v1 RAG | v2 RAG |
|---|---|---|---|
| RAPTOR | 2401.18059 | FN(not_extracted) | FN(not_extracted) |
| Rewrite-Retrieve-Read | 2305.14283 | FN(not_extracted) | FN(not_extracted) |

### (b) 회귀 없나? — v1에서 TP=RAG였던 논문 중 v2에서 RAG가 빠진 것

v1에서 RAG가 TP였던 논문 26편. 그 중 v2에서 RAG를 잃은 것:

- DeepResearcher (2504.03160, new_collected) [v2: FN(not_extracted)]
- GlobalRAG (2510.20548, new_collected) [v2: FN(not_extracted)]

## 5. 해석

전체 micro P 0.562→0.597 (+0.035), micro R 0.683→0.667 (−0.017). 정밀도↑이나 재현율↓ — ONLY-as-comparison 규칙이 일부 과하게 먹었을 수 있음(위 회귀 목록 확인). method_misjudged FP는 23→19건으로 변했고, v1에서 맞혔다 v2에서 잃은 회귀는 4건이다. 이름을 프롬프트에 박지 않았으므로(고유명사 예시 v1과 동일) 50편에서의 점수 변화는 규칙 일반화의 효과이지 우연한 적합이 아니다. 채택 여부는 위 표와 회귀 목록을 보고 사람이 정한다.
