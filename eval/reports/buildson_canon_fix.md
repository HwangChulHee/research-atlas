# builds_on — 작명 정규화(resolve 괄호 fallback) 재채점

`src/normalize_core.resolve()`에 **괄호 약어 fallback**(additive)을 추가하고 v1/v2/v3를 같은 규칙으로 재채점한 결과. `Long Form (ACRONYM)` 표기가 직접 매칭에 실패하면 (a)괄호 안 약어, (b)괄호 뗀 본체로 재시도해 **이미 알려진 대표개념에만** 연결한다(새 개념 생성 안 함). lexicon/relations.json/모델 무수정, 그래프 재빌드 없음 — 점수 재측정만.

> ⚠️ 이 변경으로 이전 §7 baseline은 무효(설계상 baseline이 바뀜). **new 값이 새 기준**, old는 비교용. fallback은 additive라 재현율은 패치 전보다 내려갈 수 없다(검증 게이트 통과).

## 1. 점수표 (old → new, run별)

### v1

| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| **전체(50)** old | 0.562 | 0.683 | 0.708 | 0.785 | 41 | 32 | 19 |
| **전체(50)** new | 0.562 | 0.683 | 0.708 | 0.785 | 41 | 32 | 19 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |
| **new_collected** old | 0.708 | 0.515 | 0.792 | 0.654 | 17 | 7 | 16 |
| **new_collected** new | 0.708 | 0.515 | 0.792 | 0.654 | 17 | 7 | 16 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |
| **from_corpus** old | 0.490 | 0.889 | 0.651 | 0.886 | 24 | 25 | 3 |
| **from_corpus** new | 0.490 | 0.889 | 0.651 | 0.886 | 24 | 25 | 3 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |

### v2

| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| **전체(50)** old | 0.597 | 0.667 | 0.709 | 0.764 | 40 | 27 | 20 |
| **전체(50)** new | 0.597 | 0.667 | 0.709 | 0.764 | 40 | 27 | 20 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |
| **new_collected** old | 0.654 | 0.515 | 0.714 | 0.664 | 17 | 9 | 16 |
| **new_collected** new | 0.654 | 0.515 | 0.714 | 0.664 | 17 | 9 | 16 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |
| **from_corpus** old | 0.561 | 0.852 | 0.707 | 0.841 | 23 | 18 | 4 |
| **from_corpus** new | 0.561 | 0.852 | 0.707 | 0.841 | 23 | 18 | 4 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |

### v3

| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| **전체(50)** old | 0.660 | 0.517 | 0.712 | 0.567 | 31 | 16 | 29 |
| **전체(50)** new | 0.672 | 0.650 | 0.717 | 0.734 | 39 | 19 | 21 |
| Δ | +0.013 | +0.133 | +0.005 | +0.167 | +8 | +3 | -8 |
| **new_collected** old | 0.778 | 0.424 | 0.769 | 0.477 | 14 | 4 | 19 |
| **new_collected** new | 0.739 | 0.515 | 0.735 | 0.625 | 17 | 6 | 16 |
| Δ | −0.039 | +0.091 | −0.034 | +0.147 | +3 | +2 | -3 |
| **from_corpus** old | 0.586 | 0.630 | 0.675 | 0.636 | 17 | 12 | 10 |
| **from_corpus** new | 0.629 | 0.815 | 0.703 | 0.818 | 22 | 13 | 5 |
| Δ | +0.042 | +0.185 | +0.028 | +0.182 | +5 | +1 | -5 |

## 2. 회복된 항목 (패치로 TP가 된 것 — 표기 변종이 대표개념에 연결됨)

### v1 — 0건

- (없음)

### v2 — 0건

- (없음)

### v3 — 8건

- **RAG** ← `retrieval-augmented generation (RAG)` — Search-o1 (2501.05366, new_collected)
- **RAG** ← `Retrieval-Augmented Generation (RAG)` — R1-Searcher++ (2505.17005, new_collected)
- **RAG** ← `retrieval-augmented generation (RAG)` — WebThinker (2504.21776, new_collected)
- **CoT** ← `few-shot chain-of-thought (CoT) prompting` — Plan-and-Solve (2305.04091, from_corpus)
- **RAG** ← `Retrieval-Augmented Generation (RAG)` — Self-RAG (2310.11511, from_corpus)
- **RAG** ← `Retrieval-Augmented Generation (RAG)` — MedGraphRAG (2408.04187, from_corpus)
- **RAG** ← `Retrieval Augmented Generation (RAG)` — LumberChunker (2406.17526, from_corpus)
- **RAG** ← `Retrieval-augmented generation (RAG)` — MedRAG (2502.04413, from_corpus)

## 3. ★ 남은 lexicon탈락 변종 (사람 검토용 — alias 추가 후보, 자동등록 아님)

패치 후에도 emit됐지만 lexicon에서 노드가 안 되는(status∉approved/unreviewed) 표기. 대부분 괄호 아닌 변종(예: "retrieval augmentation", "agentic RAG")이라 판단이 필요 — **목록만 제공**, 다음 라운드에 사람이 alias로 승격할지 정한다. 빈도순.

| 빈도 | emit 표기 | 예시(run, 논문) |
|--:|---|---|
| 9 | reinforcement learning | v1, DeepRetrieval (2503.00223) |
| 7 | GRPO | v1, OTC (2504.14870) |
| 4 | Group Relative Policy Optimization | v1, DeepSeek-R1 (2501.12948) |
| 4 | agentic RAG | v1, HiPRAG (2510.07794) |
| 4 | retrieval-augmented language models | v1, REPLUG (2301.12652) |
| 3 | DeepSeek-V3-Base | v1, DeepSeek-R1 (2501.12948) |
| 3 | Active RAG | v1, s3 (2505.14146) |
| 3 | TIRESRAG-R1 | v1, GlobalRAG (2510.20548) |
| 3 | few-shot prompting | v1, Chain-of-Thought (2201.11903) |
| 3 | GPT-J | v1, Toolformer (2302.04761) |
| 3 | retrieve-then-read | v1, Rewrite-Retrieve-Read (2305.14283) |
| 3 | retrieval-augmented LLMs | v1, Rewrite-Retrieve-Read (2305.14283) |
| 3 | retrieval augmentation | v1, RAPTOR (2401.18059) |
| 3 | instruction fine-tuning | v1, RAFT (2403.10131) |
| 3 | supervised fine-tuning | v2, DeepSeek-R1 (2501.12948) |
| 3 | Markov Decision Process | v2, DeepRAG (2502.01142) |
| 3 | prompting | v2, Chain-of-Thought (2201.11903) |
| 3 | in-context learning | v2, Toolformer (2302.04761) |
| 2 | query augmentation | v1, DeepRetrieval (2503.00223) |
| 2 | Graph-based RAG | v1, Agentic RAG Survey (2501.09136) |
| 2 | ReSearch | v1, MARAG-R1 (2510.27569) |
| 2 | LLM-based multi-agent systems | v1, MetaGPT (2308.00352) |
| 2 | rejection sampling | v2, DeepSeek-R1 (2501.12948) |
| 2 | Large Language Models | v2, DeepRetrieval (2503.00223) |
| 2 | dual-encoder architecture | v2, DPR (2004.04906) |
| 2 | few-shot learning | v2, Chain-of-Thought (2201.11903) |
| 2 | graph-based RAG | v3, Agentic RAG Survey (2501.09136) |
| 1 | RL | v1, RAGEN (2504.20073) |
| 1 | LLM agents | v1, RAGEN (2504.20073) |
| 1 | raw trajectories | v1, ReasoningBank (2509.25140) |
| 1 | successful routines | v1, ReasoningBank (2509.25140) |
| 1 | KG-RAG | v1, KG-R1 (2509.26383) |
| 1 | GraphRAG-R1 | v1, GlobalRAG (2510.20548) |
| 1 | dual-encoder | v1, DPR (2004.04906) |
| 1 | maximum inner product search | v1, DPR (2004.04906) |
| 1 | Few-Shot Prompting | v1, Least-to-Most (2205.10625) |
| 1 | Program-of-Thought Prompting | v1, Plan-and-Solve (2305.04091) |
| 1 | query rewriting | v1, Rewrite-Retrieve-Read (2305.14283) |
| 1 | outcome-based reinforcement learning | v2, R1-Searcher++ (2505.17005) |
| 1 | R1-Searcher | v2, DeepResearcher (2504.03160) |
| 1 | Iterative Retrieval | v2, DeepRAG (2502.01142) |
| 1 | Imitation Learning | v2, DeepRAG (2502.01142) |
| 1 | Reinforcement Learning with Verifiable Rewards | v2, s3 (2505.14146) |
| 1 | Proximal Policy Optimization | v2, OTC (2504.14870) |
| 1 | Group Relative Preference Optimization | v2, OTC (2504.14870) |
| 1 | Knowledge-Graph Retrieval-Augmented Generation | v2, KG-R1 (2509.26383) |
| 1 | Re-Search | v2, MARAG-R1 (2510.27569) |
| 1 | supervised fine-tuning (SFT) | v3, R1-Searcher++ (2505.17005) |
| 1 | reinforcement learning (RL) | v3, R1-Searcher++ (2505.17005) |
| 1 | Iterative retrieval | v3, DeepRAG (2502.01142) |
| 1 | large reasoning models (LRMs) | v3, WebThinker (2504.21776) |
| 1 | RLVR | v3, s3 (2505.14146) |
| 1 | State-Thinking-Actions-Reward Policy Optimization | v3, RAGEN (2504.20073) |
| 1 | knowledge-graph retrieval-augmented generation | v3, KG-R1 (2509.26383) |
| 1 | k-Nearest Neighbor Language Model | v3, REALM (2002.08909) |
| 1 | late interaction | v3, ColBERT (2004.12832) |
| 1 | natural language rationales | v3, Chain-of-Thought (2201.11903) |
| 1 | greedy decoding | v3, Self-Consistency (2203.11171) |
| 1 | pre-trained language models for planning and acting in interactive environments | v3, ReAct (2210.03629) |
| 1 | black-box language models | v3, REPLUG (2301.12652) |
| 1 | retrieval model | v3, REPLUG (2301.12652) |
| 1 | novelty search | v3, Voyager (2305.16291) |
| 1 | meta-programming | v3, MetaGPT (2308.00352) |
| 1 | LLM-based multi-agent collaborations | v3, MetaGPT (2308.00352) |
| 1 | control tokens | v3, Self-RAG (2310.11511) |
| 1 | Information Retrieval | v3, Power of Noise (2401.14887) |
| 1 | open domain question answering systems | v3, RAPTOR (2401.18059) |
| 1 | vector RAG | v3, GraphRAG (2404.16130) |
| 1 | LLM-as-a-judge | v3, GraphRAG (2404.16130) |
| 1 | dense retrieval | v3, LumberChunker (2406.17526) |
| 1 | knowledge graph (KG)-elicited reasoning | v3, MedRAG (2502.04413) |

총 고유 표기 71종 / emit 누계 129건.

## 4. 해석

v3 전체 micro R 0.517→0.650 (+0.133), P 0.660→0.672 (+0.013). 예상대로 v3(verbose 표기 多)가 가장 크게 회복됐다 — `Retrieval-Augmented Generation (RAG)` 류가 RAG로 연결되며 dropped→TP. v1은 micro R 0.683→0.683로 거의 불변(이미 짧은 표기라 fallback이 거의 안 먹음 — 패치가 과하지 않다는 신호). 정밀도는 양방향 가능: fallback이 pred의 미해결 표기도 대표개념에 연결시키므로 그 항목이 gold면 TP(P↑), gold 아니면 FP(P↓)가 된다 — 위 표의 ΣFP 변화로 확인. 남은 변종 71종(§3)은 괄호 아닌 표기라 자동 연결 대상이 아니며, 사람이 alias 승격 여부를 다음 라운드에 정한다. 이로써 작명이 강건해져 evidence·모델비교의 선결 조건이 갖춰졌다.
