# builds_on — evidence(v3) vs v2 (한 변수: 본문 근거 요구)

라이브 프롬프트는 v2 유지. 그 위에 builds_on 각 항목에 **본문 근거(evidence)**를 같이 뽑게 한 v3과 비교. 같은 모델(`gpt-5.4-mini`)·lexicon(frozen)·goldset(50편)·채점 규칙. v3은 `name`만 채점, `evidence`는 리포트용. 라이브 relate.py·normalize·lexicon 무수정.

> ⚠️ **노이즈 바닥 미측정** — 직전 실험에서 프롬프트 효과가 run-to-run 노이즈(±0.04) 수준이었다. 작은 Δ는 해석 보류. **FP 종류 변화·회귀 목록·evidence 인용**만 신뢰하라. 이 실험의 주 목적은 점수가 아니라 (1) legibility (2) grounding의 method_misjudged 억제 여부.

- v2(baseline) pred = `eval/experiments/relate_v2/{id}.relations.json` (보존)
- v3 pred = `eval/experiments/relate_v3_evidence/{id}.relations.json`
- v2 재계산이 §7 직전 v2 숫자를 재현함을 확인하고 작성됨(검증 게이트 통과).

## 1. 점수 비교 (v2 / v3 / Δ)

| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| **전체(50)** v2 | 0.597 | 0.667 | 0.709 | 0.764 | 40 | 27 | 20 |
| **전체(50)** v3 | 0.660 | 0.517 | 0.712 | 0.567 | 31 | 16 | 29 |
| Δ | +0.063 | −0.150 | +0.003 | −0.197 | -9 | -11 | +9 |
| **new_collected** v2 | 0.654 | 0.515 | 0.714 | 0.664 | 17 | 9 | 16 |
| **new_collected** v3 | 0.778 | 0.424 | 0.769 | 0.477 | 14 | 4 | 19 |
| Δ | +0.124 | −0.091 | +0.056 | −0.186 | -3 | -5 | +3 |
| **from_corpus** v2 | 0.561 | 0.852 | 0.707 | 0.841 | 23 | 18 | 4 |
| **from_corpus** v3 | 0.586 | 0.630 | 0.675 | 0.636 | 17 | 12 | 10 |
| Δ | +0.025 | −0.222 | −0.032 | −0.205 | -6 | -6 | +6 |

> Δ = v3 − v2. 노이즈 바닥 미측정이므로 작은 micro Δ는 단정 금지.

## 2. FP 변화 (grounding이 헛것을 줄였나)

v2 FP 27건 → v3 FP 16건. 사라진 FP **15**, 새 FP **4**.

| 종류 | 사라진(v2→없음) | 새(v3) | 순변화 |
|---|--:|--:|--:|
| component_tool | −2 | +1 | -1 |
| substrate | −1 | +0 | -1 |
| method_misjudged | −12 | +3 | -9 |

**method_misjudged FP: v2 19 → v3 10 (-9).** (grounding이 비교-baseline 오인을 줄였는지의 핵심 지표.)

**사라진 FP:**

- [method_misjudged] AutoGPT — Voyager (2305.16291, from_corpus)
- [method_misjudged] GPT-4 — Voyager (2305.16291, from_corpus)
- [method_misjudged] ReAct — Voyager (2305.16291, from_corpus)
- [method_misjudged] Reflexion — Voyager (2305.16291, from_corpus)
- [method_misjudged] AgentVerse — MetaGPT (2308.00352, from_corpus)
- [method_misjudged] AutoGPT — MetaGPT (2308.00352, from_corpus)
- [method_misjudged] ChatDev — MetaGPT (2308.00352, from_corpus)
- [method_misjudged] LangChain — MetaGPT (2308.00352, from_corpus)
- [method_misjudged] RAG — Agentic RAG Survey (2501.09136, new_collected)
- [method_misjudged] Direct Preference Optimization — WebThinker (2504.21776, new_collected)
- [method_misjudged] HyperGraphRAG — MARAG-R1 (2510.27569, new_collected)
- [method_misjudged] SEARCH-R1 — MARAG-R1 (2510.27569, new_collected)
- [component_tool] PPO — SEARCH-R1 (2503.09516, new_collected)
- [component_tool] PPO — HiPRAG (2510.07794, new_collected)
- [substrate] GPT-3 — Toolformer (2302.04761, from_corpus)

**새로 생긴 FP:**

- [method_misjudged] REPLUG LSR — REPLUG (2301.12652, from_corpus)
- [method_misjudged] WebGPT — Reflexion (2303.11366, from_corpus)
- [method_misjudged] Personalized PageRank — HippoRAG (2405.14831, from_corpus)
- [component_tool] PPO — OTC (2504.14870, new_collected)

## 3. 회귀 체크 — v2에서 TP였는데 v3에서 잃은 항목

TP: v2 40 → v3 31 (새로 맞힘 2, 잃음 11). 잃은 항목은 gold이므로 v3에선 FN.

- CoT — Plan-and-Solve (2305.04091, from_corpus) [v3 진단: not_extracted]
- RAG — Self-RAG (2310.11511, from_corpus) [v3 진단: not_extracted]
- RAG — LumberChunker (2406.17526, from_corpus) [v3 진단: not_extracted]
- RAG — MedGraphRAG (2408.04187, from_corpus) [v3 진단: not_extracted]
- RAG — Search-o1 (2501.05366, new_collected) [v3 진단: not_extracted]
- RAG — MedRAG (2502.04413, from_corpus) [v3 진단: not_extracted]
- RAG — From RAG to Memory (HippoRAG 2) (2502.14802, from_corpus) [v3 진단: not_extracted]
- SEARCH-R1 — DeepResearcher (2504.03160, new_collected) [v3 진단: not_extracted]
- RAG — WebThinker (2504.21776, new_collected) [v3 진단: not_extracted]
- RAG — R1-Searcher++ (2505.17005, new_collected) [v3 진단: not_extracted]
- RAG — HiPRAG (2510.07794, new_collected) [v3 진단: not_extracted]

**참고 — v3에서 새로 맞힌 TP:**

- RAG — DeepResearcher (2504.03160, new_collected)
- RAG — GlobalRAG (2510.20548, new_collected)

## 4. ★ evidence 항목 표 (주 산출물 — 모델이 왜 골랐나)

v3가 emit한 builds_on 항목 전부(채점 후). 판정=TP/FP(채점은 rep_key 공간, lexicon status 필터 후). **FP를 위로** 정렬. evidence가 비교 문장이면(예 "we compare against X") → 모델이 비교를 build-on으로 오독한 grounding 실패가 인용으로 드러난다.

> 주의: status 필터로 그래프에서 빠진 항목(pending/rejected)은 채점 pred에 없어 여기 verdict가 `dropped`로 뜬다(헛것도 정답도 아님 — lexicon 미등록 신개념).

| 논문 | id | name(emit) | 판정 | FP종류 | evidence 인용 |
|---|---|---|---|---|---|
| REALM | 2002.08909 | BERT | FP | substrate | “we augment language model pre-training with a latent knowledge retriever” |
| REPLUG | 2301.12652 | REPLUG LSR | FP | method_misjudged | “We also introduce REPLUG LSR (REPLUG with LM-Supervised Retrieval)” |
| Reflexion | 2303.11366 | WebGPT | FP | method_misjudged | “Recent works such as ReAct [30], SayCan [1], Toolformer [22], HuggingGPT [23], generative agents [19], and WebGPT [17] have demonstrated the feasibility of autonomous decision-making agents” |
| LATS | 2310.04406 | Monte Carlo Tree Search | FP | component_tool | adapting Monte Carlo Tree Search (MCTS) |
| Power of Noise | 2401.14887 | Retrieval-Augmented Generation | FP | method_misjudged | RAG has recently emerged as a method to extend beyond the pre-trained knowledge of Large Language Models |
| CRAG | 2401.15884 | Self-RAG | FP | method_misjudged | “CRAG is plug-and-play and experimentally implemented into RAG (Lewis et al., 2020) and Self-RAG (Asai et al., 2024)” |
| HippoRAG | 2405.14831 | Personalized PageRank | FP | method_misjudged | “runs the Personalized PageRank (PPR) algorithm [30] on the KG” |
| RAGBench | 2407.11005 | Retrieval-Augmented Generation | FP | method_misjudged | Retrieval-Augmented Generation (RAG) has become a standard architectural pattern |
| RAGBench | 2407.11005 | RAGAS | FP | component_tool | we adopt existing metric definitions for context relevance, answer faithfulness [9, 32] |
| RAGBench | 2407.11005 | TruLens | FP | component_tool | automated RAG evaluation systems like RAGAS [9] and TruLens [36] have emerged |
| RAGBench | 2407.11005 | ARES | FP | component_tool | ARES [32] and RAGAS [9] define a context relevance metric |
| From RAG to Memory (HippoRAG 2) | 2502.14802 | Personalized PageRank | FP | method_misjudged | “HippoRAG 2 builds upon the Personalized PageRank algorithm used in HippoRAG” |
| OTC | 2504.14870 | PPO | FP | component_tool | We implement OTC-PPO ... based on PPO [19] |
| RAGEN | 2504.20073 | StarPO | FP | method_misjudged | Built on top of StarPO, we develop RAGEN |
| s3 | 2505.14146 | Self-RAG | FP | method_misjudged | “Self-RAG ... distilled such behaviors from larger models into smaller ones via supervised fine-tuning” |
| MARAG-R1 | 2510.27569 | GraphRAG | FP | method_misjudged | “Instead of relying on a single retriever or static graph abstraction” |
| REALM | 2002.08909 | k-Nearest Neighbor Language Model | dropped | — | “In the language modeling literature, the k-Nearest Neighbor Language Model (Khandelwal et al., 2019) (kNN-LM) retrieves similar LM examples to improve memorization.” |
| DPR | 2004.04906 | dual-encoder architecture | dropped | — | “a dual-encoder architecture (Bromley et al., 1994)” |
| ColBERT | 2004.12832 | late interaction | dropped | — | “ColBERT, a ranking model based on contextualized late interaction over BERT” |
| Chain-of-Thought | 2201.11903 | prompting | dropped | — | “we explore the ability of language models to perform few-shot prompting for reasoning tasks” |
| Chain-of-Thought | 2201.11903 | few-shot learning | dropped | — | “in-context few-shot learning via prompting” |
| Chain-of-Thought | 2201.11903 | natural language rationales | dropped | — | “techniques for arithmetic reasoning can beneﬁt from generating natural language rationales that lead to the ﬁnal answer”}]}]}} Please note: |
| Chain-of-Thought | 2201.11903 | prompting | dropped | — | “we refer to this approach as chain-of-thought prompting” |
| Self-Consistency | 2203.11171 | greedy decoding | dropped | — | "to replace the greedy decoding strategy used in chain-of-thought prompting" |
| Least-to-Most | 2205.10625 | few-shot prompting | dropped | — | “It combines the idea of natural language rationales ... with few-shot prompting ... Both stages are implemented by few-shot prompting”}]}}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}]}] …[clipped] |
| ReAct | 2210.03629 | pre-trained language models for planning and acting in interactive environments | dropped | — | “recent work has explored the use of pre-trained language models for planning and acting in interactive environments” |
| REPLUG | 2301.12652 | retrieval-augmented language models | dropped | — | “We introduce REPLUG, a retrieval-augmented language modeling framework” |
| REPLUG | 2301.12652 | black-box language models | dropped | — | “REPLUG treats the language model as a black box” |
| REPLUG | 2301.12652 | retrieval model | dropped | — | “augments it with a tuneable retrieval model” |
| Toolformer | 2302.04761 | GPT-J | dropped | — | “Toolformer, which is based on a pretrained GPT-J model” |
| Toolformer | 2302.04761 | in-context learning | dropped | — | “based on the recent idea of using large LMs with in-context learning” |
| Plan-and-Solve | 2305.04091 | few-shot chain-of-thought (CoT) prompting | dropped | — | few-shot chain-of-thought (CoT) prompting includes a few manually crafted step-by-step reasoning demonstrations |
| Plan-and-Solve | 2305.04091 | Zero-shot-Program-of-Thought (PoT) Prompting | dropped | — | is comparable to or exceeds Zero-shot-Program-of-Thought (PoT) Prompting |
| Rewrite-Retrieve-Read | 2305.14283 | retrieve-then-read | dropped | — | "instead of the previous retrieve-then-read" |
| Rewrite-Retrieve-Read | 2305.14283 | retrieval-augmented LLMs | dropped | — | "a new framework for retrieval-augmented LLMs from the perspective of the query rewriting" |
| Voyager | 2305.16291 | in-context learning | dropped | — | “VOYAGER interacts with GPT-4 via blackbox queries … through prompting and in-context learning” |
| Voyager | 2305.16291 | novelty search | dropped | — | “This approach can be perceived as an in-context form of novelty search” |
| MetaGPT | 2308.00352 | meta-programming | dropped | — | “we design a promising GPT-based Meta-Programming framework called MetaGPT” |
| MetaGPT | 2308.00352 | LLM-based multi-agent collaborations | dropped | — | “an innovative meta-programming framework incorporating efficient human workflows into LLM-based multi-agent collaborations” |
| Self-RAG | 2310.11511 | Retrieval-Augmented Generation (RAG) | dropped | — | “Self-Reflective Retrieval-Augmented Generation (SELF-RAG)” |
| Self-RAG | 2310.11511 | control tokens | dropped | — | “our trained LM uses critique tokens to assess its own predictions after each generated segment as an integral part of the generation output” |
| Power of Noise | 2401.14887 | Information Retrieval | dropped | — | the retrieval component of RAG systems, be it dense or sparse, deserves increased attention from the research community |
| RAPTOR | 2401.18059 | retrieval augmentation | dropped | — | “retrieval augmentation”, Lewis et al., 2020; Izacard et al., 2022; Min et al., 2023; Ram et al., 2023 |
| RAPTOR | 2401.18059 | open domain question answering systems | dropped | — | An alternative approach, pioneered in open domain question answering systems (Chen et al., 2017; Yu et al., 2018), is to index large quantities of text |
| RAFT | 2403.10131 | instruction fine-tuning | dropped | — | “In this paper, we study how to combine instruction fine-tuning (IFT) with retrieval augmented generation (RAG).” |
| GraphRAG | 2404.16130 | vector RAG | dropped | — | To combine the strengths of these contrasting methods, we propose GraphRAG |
| GraphRAG | 2404.16130 | LLM-as-a-judge | dropped | — | we developed a novel application of the LLM-as-a-judge technique |
| LumberChunker | 2406.17526 | Retrieval Augmented Generation (RAG) | dropped | — | "Retrieval Augmented Generation (RAG) systems present a viable solution to hallucinations" |
| LumberChunker | 2406.17526 | dense retrieval | dropped | — | "Modern NLP tasks increasingly rely on dense retrieval methods" |
| MedGraphRAG | 2408.04187 | Retrieval-Augmented Generation (RAG) | dropped | — | “we introduce a novel graph-based RAG method for medical domain” |
| LightRAG | 2410.05779 | Retrieval-Augmented Generation (RAG) | dropped | — | “we propose LightRAG, which incorporates graph structures into text indexing and retrieval processes” |
| Search-o1 | 2501.05366 | retrieval-augmented generation (RAG) | dropped | — | “Search-o1, which integrates the reasoning process of LRMs with two core components: an agentic retrieval-augmented generation (RAG) mechanism” |
| Search-o1 | 2501.05366 | agentic RAG | dropped | — | “Unlike them, Search-o1 employs an agentic RAG technique that guides the model to actively decode search queries when facing knowledge shortages” |
| Agentic RAG Survey | 2501.09136 | Retrieval-Augmented Generation (RAG) | dropped | — | “Agentic Retrieval-Augmented Generation (Agentic RAG) transcends these limitations by embedding autonomous AI agents into the RAG pipeline.” |
| Agentic RAG Survey | 2501.09136 | graph-based RAG | dropped | — | “including naïve, modular, and graph-based RAG [17], and their transition toward agentic systems.” |
| DeepSeek-R1 | 2501.12948 | DeepSeek-V3-Base | dropped | — | we build upon DeepSeek-V3-Base (DeepSeek-AI, 2024b) |
| DeepSeek-R1 | 2501.12948 | Group Relative Policy Optimization | dropped | — | employ Group Relative Policy Optimization (GRPO) (Shao et al., 2024) as our RL framework |
| DeepSeek-R1 | 2501.12948 | supervised fine-tuning | dropped | — | we bypass the conventional supervised fine-tuning (SFT) phase before RL training |
| DeepSeek-R1 | 2501.12948 | rejection sampling | dropped | — | a multi-stage learning framework that integrates rejection sampling, reinforcement learning, and supervised fine-tuning |
| DeepRAG | 2502.01142 | Markov Decision Process | dropped | — | "modeling retrieval-augmented reasoning as a Markov Decision Process (MDP)" |
| DeepRAG | 2502.01142 | Iterative retrieval | dropped | — | "Iterative retrieval has been proposed as a solution to continuously update retrieval results" |
| MedRAG | 2502.04413 | Retrieval-augmented generation (RAG) | dropped | — | “We proposed a novel RAG approach enhanced by KG-elicited reasoning” |
| MedRAG | 2502.04413 | knowledge graph (KG)-elicited reasoning | dropped | — | “MedRAG, a RAG model enhanced by knowledge graph (KG)-elicited reasoning” |
| RAG-Gym | 2502.13957 | Markov Decision Process | dropped | — | We formulate agentic search as a Markov Decision Process (MDP) in which search queries act as macro-actions. |
| RAG-Gym | 2502.13957 | reinforcement learning | dropped | — | Building on the success of reinforcement learning in enhancing LLMs for mathematical reasoning |
| DeepRetrieval | 2503.00223 | reinforcement learning | dropped | — | "we introduce DeepRetrieval, a reinforcement learning (RL) approach that trains LLMs for query generation" |
| DeepRetrieval | 2503.00223 | Large Language Models | dropped | — | "we introduce DeepRetrieval, a reinforcement learning (RL) approach that trains LLMs for query generation" |
| HyperGraphRAG | 2503.21322 | graph-based RAG | dropped | — | “HyperGraphRAG, a novel graph-based RAG method built upon hypergraph-structured knowledge representation” |
| DeepResearcher | 2504.03160 | reinforcement learning | dropped | — | we directly scale RL training for deep research with only outcome rewards |
| OTC | 2504.14870 | GRPO | dropped | — | We implement OTC-GRPO ... based on GRPO [20] |
| RAGEN | 2504.20073 | State-Thinking-Actions-Reward Policy Optimization | dropped | — | We propose StarPO (State-Thinking-Actions-Reward Policy Optimization), a general framework for trajectory-level agent RL |
| WebThinker | 2504.21776 | retrieval-augmented generation (RAG) | dropped | — | existing open-source deep search agents typically employ retrieval-augmented generation (RAG) techniques with predefined workflows |
| WebThinker | 2504.21776 | online Direct Preference Optimization (DPO) | dropped | — | we construct preference pairs for online DPO training |
| WebThinker | 2504.21776 | large reasoning models (LRMs) | dropped | — | we propose WebThinker, an autonomous deep research agent entirely powered by large reasoning models |
| s3 | 2505.14146 | Active RAG | dropped | — | “Active RAG techniques ... interleaved query generation, retrieval, and reasoning in a multi-turn loop.” |
| s3 | 2505.14146 | RLVR | dropped | — | “the recent emergence of reinforcement learning with verifiable rewards (RLVR)” |
| R1-Searcher++ | 2505.17005 | Retrieval-Augmented Generation (RAG) | dropped | — | “Retrieval-Augmented Generation (RAG) helps by injecting external information” |
| R1-Searcher++ | 2505.17005 | supervised fine-tuning (SFT) | dropped | — | “an initial SFT Cold-start phase for preliminary format learning” |
| R1-Searcher++ | 2505.17005 | reinforcement learning (RL) | dropped | — | “followed by RL for Dynamic Knowledge Acquisition” |
| KG-R1 | 2509.26383 | knowledge-graph retrieval-augmented generation | dropped | — | “To address this, we introduce KG-R1, an agentic framework that optimizes KG-RAG through reinforcement learning (RL).” |
| HiPRAG | 2510.07794 | agentic RAG | dropped | — | “HiPRAG, a Hierarchical Process reward framework for agentic RAG” |
| HiPRAG | 2510.07794 | reinforcement learning | dropped | — | “we introduce Hierarchical Process Rewards for Efficient agentic RAG (HiPRAG), a novel training methodology that incorporates a fine-grained, knowledge-grounded process reward into the RL training” |
| GlobalRAG | 2510.20548 | GRPO | dropped | — | These objectives are jointly optimized using GRPO (Shao et al., 2024) |
| GlobalRAG | 2510.20548 | TIRESRAG-R1 | dropped | — | inspired by TIRESRAG-R1 (He et al., 2025), we adopt a progressive weight annealing strategy |
| DPR | 2004.04906 | BERT | TP | — | “we leverage the now standard BERT pretrained model (Devlin et al., 2019)” |
| ColBERT | 2004.12832 | BERT | TP | — | “a novel ranking model that adapts deep LMs (in particular, BERT) for efficient retrieval” |
| Self-Consistency | 2203.11171 | chain-of-thought prompting | TP | — | "we introduce a novel decoding strategy called self-consistency to replace the greedy decoding strategy used in chain-of-thought prompting" |
| Least-to-Most | 2205.10625 | chain-of-thought prompting | TP | — | “The recently proposed chain-of-thought prompting approach ... has taken a signiﬁcant step ... We propose least-to-most prompting.” |
| ReAct | 2210.03629 | chain-of-thought prompting | TP | — | “reasoning (e.g. chain-of-thought prompting) and acting” |
| Reflexion | 2303.11366 | ReAct | TP | — | “Recent works such as ReAct [30] ... have demonstrated the feasibility of autonomous decision-making agents that are built on top of a large language model (LLM) core.” |
| Plan-and-Solve | 2305.04091 | Zero-shot-CoT | TP | — | we propose Plan-and-Solve (PS) Prompting. It consists of two components |
| LATS | 2310.04406 | ReAct | TP | — | expanding ReAct (Yao et al., 2023b) into a search over a combinatorial space of possible reasoning and acting steps |
| CRAG | 2401.15884 | RAG | TP | — | “we propose the Corrective Retrieval Augmented Generation (CRAG)” |
| RAFT | 2403.10131 | Retrieval Augmented Generation | TP | — | “We propose a novel adaptation strategy – Retrieval-Augmented Fine Tuning (RAFT). RAFT specifically addresses the challenge of fine-tuning LLMs to both incorporate domain knowledge while also improvin …[clipped] |
| GraphRAG | 2404.16130 | Retrieval-Augmented Generation | TP | — | we propose GraphRAG, a graph-based approach to question answering over private text corpora |
| HippoRAG | 2405.14831 | RAG | TP | — | “we introduce HippoRAG, a novel retrieval framework” |
| MedGraphRAG | 2408.04187 | GraphRAG | TP | — | “Our method builds on GraphRAG” |
| LightRAG | 2410.05779 | RAG | TP | — | “we propose LightRAG, a model that seamlessly integrates a graph-based text indexing paradigm with a dual-level retrieval framework” |
| DeepRAG | 2502.01142 | Retrieval-Augmented Generation | TP | — | "enhancing retrieval-augmented generation (RAG) with reasoning" |
| RAG-Gym | 2502.13957 | Retrieval-Augmented Generation | TP | — | This transition is largely powered by Retrieval-Augmented Generation (RAG), which grounds model outputs in external documents to ensure factuality |
| From RAG to Memory (HippoRAG 2) | 2502.14802 | HippoRAG | TP | — | “HippoRAG 2 builds upon the Personalized PageRank algorithm used in HippoRAG” |
| SEARCH-R1 | 2503.09516 | DeepSeek-R1 Zero | TP | — | “SEARCH-R1 can be viewed as an extension of DeepSeek-R1 Zero (Guo et al., 2025)” |
| SEARCH-R1 | 2503.09516 | RAG | TP | — | “improve performance by 24% (Qwen2.5-7B) and 20% (Qwen2.5-3B) over various RAG baselines under the same setting” |
| ReSearch | 2503.19470 | Retrieval-Augmented Generation | TP | — | This capability, often referred to as Retrieval-Augmented Generation (RAG) |
| ReSearch | 2503.19470 | DeepSeek-R1 | TP | — | the reasoning chain in this framework is not only composed of text-based thinking (i.e., enclosed by <think> </think>) as DeepSeek-R1 |
| HyperGraphRAG | 2503.21322 | RAG | TP | — | “we propose HyperGraphRAG, a novel graph-based RAG method” |
| HyperGraphRAG | 2503.21322 | GraphRAG | TP | — | “existing graph-based RAG approaches” |
| RARE | 2503.23513 | Retrieval-Augmented Generation | TP | — | “P1. Naked Open-book Exam: Retrieval-augmented generation (RAG) methods” |
| RARE | 2503.23513 | RAG | TP | — | “We propose Retrieval-Augmented Reasoning Modeling (RARE)” |
| DeepResearcher | 2504.03160 | Retrieval-Augmented Generation | TP | — | current open-source efforts to integrate RL with information retrieval, such as Search-R1, R1-Searcher, and ReSearch, have primarily focused on Retrieval-Augmented Generation (RAG) using static, local …[clipped] |
| s3 | 2505.14146 | RAG | TP | — | “Retrieval-Augmented Generation (RAG) enables large language models (LLMs) to access and reason over external knowledge” |
| KG-R1 | 2509.26383 | Retrieval-augmented generation | TP | — | “Knowledge-graph retrieval-augmented generation (KG-RAG) couples large language models (LLMs) with structured, verifiable knowledge graphs (KGs)” |
| GlobalRAG | 2510.20548 | RAG | TP | — | reinforcement learning has recently shown promise in improving retrieval-augmented generation (RAG) |
| MARAG-R1 | 2510.27569 | RAG | TP | — | “we propose MARAG-R1, a reinforcement-learned multi-tool RAG framework” |
| Bi-RAR | 2511.09109 | RAG | TP | — | “We propose Bi-RAR, a novel retrieval-augmented reasoning framework” |
| Bi-RAR | 2511.09109 | Search-R1 | TP | — | “A representative paradigm is Search-R1 (Jin et al. 2025)”},{ |

합계 emit 116건 = TP 32 + FP 16 + dropped 68. (evidence가 200자 초과라 클립된 항목 3건 — 일부는 모델이 구조토큰 `}]}`을 문자열에 흘린 runaway 출력으로, evidence 자체의 신뢰성 한계를 보여줌.)

## 5. 해석

전체 micro P 0.597→0.660 (+0.063), R 0.667→0.517 (−0.150). 노이즈 바닥(±0.04) 미측정이라 이 micro Δ 자체는 단정하지 않는다. 메커니즘 지표인 **method_misjudged FP는 19→10건**으로 움직였고, v2에서 맞혔다 v3에서 잃은 회귀는 11건이다. evidence 표(§4)는 emit 116건 각각에 본문 인용을 붙여, 특히 FP 16건이 '정말 build-on 근거가 있어 골랐는지' vs '비교 문장을 오독했는지'를 인용 한 줄로 판별 가능하게 한다 — 이게 이 실험의 주 산출물(legibility)이다. evidence가 (a) FP를 줄였는지는 위 method_misjudged 순변화로, (b) 인용이 FP 원인 진단에 쓸 만한지는 §4 표의 인용 품질로 사람이 판단한다. 채택은 숫자/인용을 본 뒤 별도 작업.
