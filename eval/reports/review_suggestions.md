# 검토 도우미 — 제안 리포트 (결정 아님 · lexicon 무변경)

검토 대기 **97개** · 제안 분포: approve 38 · reject 50 · merge 9
· **확신 낮음 20개**(사람 우선 검토)

> 이 문서는 *제안*이다. approve/reject/merge는 사람이 최종 클릭한다.

## ⚠️ 확신 낮음·중간 — 한 장씩 검토

### Active RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: Evidence is insufficient beyond the surface form and similar_existing_concept='RAG'; 'Active RAG' could be a named paradigm related to RAG rather than a mere generic umbrella term, so this should not be auto-approved or confidently rejected without textual evidence.
- 유사 기존 개념: `RAG`

### trajectory memory  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제공된 evidence에 정의문, 명명된 방법으로의 사용례, 또는 다른 논문이 이를 extends/improves 대상으로 삼았다는 계보 신호가 없어 현재로서는 일반적 표현(trajectory에 대한 memory)로 보입니다.

### workflow memory  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제공된 evidence에 정의문·인용·조상 관계가 전혀 없고, 이름 자체도 특정 논문이 제안한 고유 방법명이라기보다 일반적 기능 설명(‘workflow memory’)처럼 보여 현재로서는 generic으로 보는 것이 보수적입니다.

### ToG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에 정의문, 정의 논문(defined_in), 또는 후속 논문에서의 조상 인용(cited_as_ancestor_in)이 전혀 없어, 'ToG'가 고유한 명명된 방법인지보다 약어/우산표현일 가능성이 커 현재로서는 계보(lineage) 근거가 부족합니다.

### ReKnoS  `pending`
- 제안: **approve** · lineage · 확신 low
- 근거: 이름상 고유한 방법명처럼 보이지만, 제공된 evidence에 정의문·등장 문맥·조상 인용 정보가 전혀 없어 component/generic/substrate와 구분할 근거가 부족하므로 임시로 명명된 방법 후보(lineage)로 두고 사람 검토가 필요합니다.

### RoG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 주어진 evidence에 정의문, 정의 논문, 또는 다른 논문에서의 조상 인용 정보가 전혀 없어, 'RoG'가 고유한 명명된 방법인지 일반적/모호한 약칭인지 판별할 근거가 부족합니다.

### Compressive Transformer  `pending`
- 제안: **merge_into:Transformer** · duplicate · 확신 low
- 근거: 제공된 evidence에 정의문·사용 문맥·조상 인용이 전혀 없어 독립적인 명명된 방법인지 판단할 근거가 부족하고, 현재 evidence만으로는 existing concept인 "Transformer"의 변형 표기로 보이므로 사람 검토 전 임시로 merge 제안이 적절합니다.
- 유사 기존 개념: `Transformer`

### Sparse Transformer  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제공된 evidence에 정의문·사용 문맥·조상 인용이 없고, 현재로서는 'Sparse Transformer'가 특정 고유 방법명이라기보다 Transformer 계열의 일반적 설명어로 보이며(similar_existing_concept도 'Transformer'), 명명된 lineage로 승인할 근거가 부족합니다.
- 유사 기존 개념: `Transformer`

### Gopher  `pending`
- 제안: **approve** · lineage · 확신 low
- 근거: ‘Gopher’ is a named model/method rather than a generic training component or author-year citation, so it is best treated as a lineage candidate, though no supporting definition or ancestor citation is provided in the evidence.

### GPT-J  `pending`
- 제안: **approve** · lineage · 확신 low
- 근거: ‘GPT-J’는 일반어가 아니라 EleutherAI의 명명된 모델/방법명으로 널리 고유명사처럼 쓰이며, 이런 명명된 모델은 후속 작업에서 기반·비교·확장 대상으로 인용될 수 있어 계보 후보로 보는 것이 타당하다.

### Program-of-Thought Prompting  `pending`
- 제안: **merge_into:Zero-shot-Program-of-Thought Prompting** · duplicate · 확신 low
- 근거: The only evidence provided is a similar existing concept, and without definition or citation evidence distinguishing it as a separate named method, this looks like a likely naming variant that should be reviewed against the existing 'Zero-shot-Program-of-Thought Prompting' entry.
- 유사 기존 개념: `Zero-shot-Program-of-Thought Prompting`

### active retrieval augmented generation  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: Evidence is absent here (no definition, source paper, or ancestor citation), and the phrase “active retrieval augmented generation” reads like a broad descriptive paradigm akin to “agentic/active RAG” rather than a clearly named method; per the guard, this should be treated as ambiguous and sent for human review rather than confidently approved.

### passive retrieval augmented LMs  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: Evidence is insufficient to show this is a named method lineage; the phrase "passive retrieval augmented LMs" reads as a broad descriptive category/paradigm rather than a specific proper-named technique, so it is better treated as an umbrella term pending stronger citation evidence.

### GTR  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제공된 evidence에 정의문, 정의 논문, 또는 다른 방법이 'based on/extends GTR'라고 인용한 계보 근거가 전혀 없어 현재로서는 명명된 방법인지 일반 약어인지 판별할 수 없습니다.

### Advanced RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: Evidence only provides the label "Advanced RAG" with no defining paper, definition, or ancestor citation, so it reads as a vague umbrella variant of the existing broad concept "RAG" rather than a clearly named method lineage.
- 유사 기존 개념: `RAG`

### Modular RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: Evidence only provides the name and a similar existing concept ('RAG'); without a defining citation or ancestor-use showing 'Modular RAG' as a specific named method, it reads as a broad variant label over RAG rather than a distinct lineage node.
- 유사 기존 개념: `RAG`

### Graph-based RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에 정의문·사용 문맥·조상 인용이 없고, 이름만 보면 'RAG에 그래프를 활용하는 계열'을 넓게 가리키는 우산 표현으로 해석되며 기존 개념 'RAG'의 명명된 단일 방법이라고 입증되지 않습니다.
- 유사 기존 개념: `RAG`

### successful routines  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제공된 evidence에 정의문, 명명된 방법으로의 사용례, 또는 조상으로 인용된 근거가 없고, 'successful routines'는 현재로서는 특정 고유 기법명보다 일반 표현으로 보입니다.

### agentic RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: The evidence only shows it is cited in the title 'MARAG-R1: Multi-tool Agentic Retrieval-Augmented Generation via Reinforcement Learning,' which suggests a broad paradigm label rather than a clearly defined named method; per the guard on terms like 'agentic RAG,' this is ambiguous and should not be auto-approved as lineage.
- 유사 기존 개념: `RAG`
- 조상으로 인용: 2510.27569

### GraphRAG-R1  `pending`
- 제안: **merge_into:GraphRAG** · duplicate · 확신 low
- 근거: 증거상 정의문·계보 인용은 없고 existing concept가 'GraphRAG'로 제시되어 있어, 현재로서는 'GraphRAG-R1'을 독립 방법이라기보다 기존 개념의 표기 변종/파생 표기로 보는 것이 가장 보수적입니다.
- 유사 기존 개념: `GraphRAG`

### Group Relative Policy Optimization  `pending`
- 제안: **reject** · component · 확신 med
- 근거: ‘Group Relative Policy Optimization’ names an RL optimization/training objective (GRPO), which fits the rubric’s learning-component category rather than a distinct named method lineage, and no evidence here shows it being defined as an ancestor method that later work extends.

### Search-o1  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: The evidence defines Search-o1 as a named framework—"Search-o1: Agentic Retrieval-Augmented Generation for Large Reasoning Models" and "A framework that augments large reasoning models..."—which fits a distinct method/technique rather than a generic component.
- 정의: A framework that augments large reasoning models with agentic search-driven retrieval and document reasoning to supply external knowledge during stepwise reasoning.
- 정의한 논문: 2501.05366

### RARE  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: The evidence defines RARE as a named method/paradigm in its own paper—“Retrieval-Augmented Reasoning Modeling (RARE)” is introduced as “a retrieval-augmented training paradigm...” rather than a generic component or base model.
- 정의: A retrieval-augmented training paradigm that externalizes domain knowledge to retrievable sources while internalizing domain-specific reasoning patterns during training.
- 정의한 논문: 2503.23513

### StarPO  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: The evidence defines StarPO as a named framework—“a general trajectory-level reinforcement learning framework for training LLM agents with multi-turn rollouts, state-thinking-action-reward representations, and policy optimization”—so it is presented as a specific method rather than a generic RL component.
- 정의: A general trajectory-level reinforcement learning framework for training LLM agents with multi-turn rollouts, state-thinking-action-reward representations, and policy optimization.
- 정의한 논문: 2504.20073

### RAGEN  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: The evidence defines RAGEN as a named system—“a modular system for training and evaluating LLM agents under multi-turn and stochastic reinforcement learning settings”—which indicates a specific method/framework rather than a generic component or substrate.
- 정의: A modular system for training and evaluating LLM agents under multi-turn and stochastic reinforcement learning settings.
- 정의한 논문: 2504.20073

### SFT  `pending`
- 제안: **reject** · component · 확신 med
- 근거: Evidence only supports SFT as a training component: it is the standard abbreviation for supervised fine-tuning, and being cited as an ancestor in RARE does not by itself make it a named method node under the rubric’s component/generic exclusion.
- 조상으로 인용: 2503.23513

### OTC-PPO  `unreviewed`
- 제안: **reject** · component · 확신 med
- 근거: The evidence defines OTC-PPO as "an instantiation of OTC-PO using Proximal Policy Optimization," which indicates it is a PPO-based training variant/component rather than a distinct named method lineage target.
- 유사 기존 개념: `PPO`
- 정의: An instantiation of OTC-PO using Proximal Policy Optimization.
- 정의한 논문: 2504.14870

### OTC-GRPO  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: The evidence defines OTC-GRPO as a named method variant—“an instantiation of OTC-PO using Group Relative Preference Optimization”—so despite GRPO itself being a training component, OTC-GRPO is presented as a specific method name in the paper.
- 정의: An instantiation of OTC-PO using Group Relative Preference Optimization.
- 정의한 논문: 2504.14870

### GRPO  `pending`
- 제안: **reject** · component · 확신 med
- 근거: Evidence only supports GRPO as a training optimization component—its name expands to a policy optimization method, and being cited as an ancestor in 'Optimal Tool Call-controlled Policy Optimization for Tool-Integrated Reasoning' is consistent with a learning algorithm rather than a distinct named end-to-end method node.
- 조상으로 인용: 2504.14870

### MaTTS  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: The evidence presents MaTTS as a named method—“Memory-aware test-time scaling”—with a specific mechanism (“increases an agent’s interaction experience to accelerate and diversify memory formation”), which fits a distinct technique rather than a generic component or substrate.
- 정의: Memory-aware test-time scaling that increases an agent’s interaction experience to accelerate and diversify memory formation.
- 정의한 논문: 2509.25140

### dual-encoder  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: Evidence only shows that "dual-encoder" is cited as an ancestor in Dense Passage Retrieval, but the term itself denotes a broad architectural pattern rather than a uniquely named method, so it fits a generic concept rather than a lineage node.
- 조상으로 인용: 2004.04906

### GPT  `pending`
- 제안: **merge_into:GPT-3** · duplicate · 확신 med
- 근거: 후보명은 단독으로는 매우 일반적이지만, 제공된 근거에서 유사 기존 개념이 'GPT-3'로 지정되어 있어 이 항목은 독립 방법명이라기보다 기존 개념의 표기 축약/변종으로 보는 것이 타당합니다.
- 유사 기존 개념: `GPT-3`

### few-shot prompting  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: The candidate is a broad prompting setup rather than a uniquely named method node; the evidence only shows it as a general ancestor context in 'Least-to-Most Prompting Enables Complex Reasoning in Large Language Models,' while the existing concept 'Few-shot chain-of-thought prompting' is a more specific named variant, not a mere spelling duplicate.
- 유사 기존 개념: `Few-shot chain-of-thought prompting`
- 조상으로 인용: 2205.10625

### RLAIF  `pending`
- 제안: **reject** · component · 확신 med
- 근거: RLAIF usually denotes 'Reinforcement Learning from AI Feedback,' which is a training paradigm/component analogous to RLHF rather than a uniquely named method lineage, and no evidence here shows it being defined as a specific method extended by later work.

### ChatGPT  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: Although "ChatGPT" can look like a product/model name, the evidence shows it is explicitly cited as an ancestor in multiple papers (e.g., HuggingGPT, Generative Agents, RankGPT), which is a strong lineage signal under the rubric.
- 조상으로 인용: 2303.17580, 2304.03442, 2304.09542

### Hugging Face  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: Evidence is insufficient to treat 'Hugging Face' as a named method lineage: it is commonly an organization/platform name, and there is no definition, ancestor citation, or statement here that a paper builds a method on/extends 'Hugging Face'.

### retrieval-augmented LLMs  `pending`
- 제안: **reject** · umbrella · 확신 med
- 근거: ‘retrieval-augmented LLMs’는 특정 고유명사 방법명이 아니라 검색 결합형 LLM 전반을 가리키는 넓은 범주의 표현이며, 정의문·조상 인용 등에서 개별 명명 기법으로 쓰였다는 근거가 제시되지 않았습니다.

### LLM-based multi-agent systems  `pending`
- 제안: **reject** · umbrella · 확신 med
- 근거: ‘LLM-based multi-agent systems’는 특정 논문이 제안한 고유한 방법명이 아니라 여러 접근을 포괄하는 서술적 범주명이며, 제공된 evidence에도 정의문·제안 논문·후속 works의 조상 인용이 없어 변별력 낮은 우산 범주로 보입니다.

### Transformers  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: Evidence is insufficient to treat this as a specific named method lineage; “Transformers” is most commonly a broad architecture family/general term rather than a distinct method node, and no defining paper or ancestor citation is provided here.

### Naive RAG  `pending`
- 제안: **merge_into:RAG** · duplicate · 확신 med
- 근거: 주어진 evidence에는 별도 정의문이나 독립적인 명명 기법으로서의 근거가 없고, 후보명 자체가 기존 개념 'RAG'의 변형 표기/하위 호칭으로 보이므로 우선 중복 병합 검토가 적절합니다.
- 유사 기존 개념: `RAG`

### retrieval augmentation  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: The evidence only shows the broad phrase "retrieval augmentation" being cited in RAPTOR, which reads as a general technique family rather than a specifically named method that later work explicitly extends.
- 조상으로 인용: 2401.18059

### query augmentation  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 제공된 evidence에 정의문·명명된 방법 인용·조상으로의 사용 사례가 없고, 'query augmentation'은 특정 고유 기법명이라기보다 질의 확장/보강을 뜻하는 일반적 표현으로 보입니다.

### GPT-2  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: Evidence shows GPT-2 functions as an ancestor method rather than merely a substrate: it is explicitly cited as prior lineage in the GPT-3 paper (“cited_as_ancestor_in”: GPT-3: Language Models are Few-Shot Learners), and the rubric notes that being cited as a builds_on/ancestor signal is itself evidence for lineage.
- 조상으로 인용: 2005.14165

### Reinforcement Learning from Human Feedback  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: ‘Reinforcement Learning from Human Feedback’ is a general training paradigm/component rather than a uniquely named method node, even though it is cited as an ancestor in ‘Constitutional AI: Harmlessness from AI Feedback’.
- 조상으로 인용: 2212.08073

### RL from AI Feedback  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: The evidence only shows it as a descriptive training phrase cited in “Constitutional AI: Harmlessness from AI Feedback,” and “RL from AI Feedback” names a reinforcement-learning setup rather than a distinct named method/technique node.
- 조상으로 인용: 2212.08073

### SUPER-NATURALINSTRUCTIONS  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: `SUPER-NATURALINSTRUCTIONS` is cited as an ancestor in SELF-INSTRUCT ('Aligning Language Models with Self-Generated Instructions'), which is a strong lineage signal that it functions as a named prior method/dataset benchmark rather than a generic component or mere substrate.
- 조상으로 인용: 2212.10560

### PromptSource  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: ‘PromptSource’ is cited as an ancestor by Self-Instruct, which is a direct lineage signal under the rubric (‘builds_on/ancestor’ citations indicate a parent method rather than a mere substrate or generic term).
- 조상으로 인용: 2212.10560

### Codex  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: Evidence of lineage is explicit because this candidate is "cited_as_ancestor_in" REPLUG (2301.12652), and the rubric states that being cited as a builds_on/ancestor signal indicates a named method/model should be treated as lineage rather than merely a substrate.
- 조상으로 인용: 2301.12652

### Bradley-Terry model  `pending`
- 제안: **reject** · component · 확신 med
- 근거: Evidence points to a learning objective/component rather than a named paper method node: in Direct Preference Optimization it is invoked as the classical Bradley-Terry preference model underlying pairwise comparisons, not as a distinct method that the paper extends as a lineage ancestor.
- 조상으로 인용: 2305.18290

### S5  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 후보 'S5'는 정의문은 비어 있지만, 적어도 한 논문에서 조상으로 직접 인용되며(cited_as_ancestor_in: Mamba, 'Selective State Spaces'), 가드에 따라 '다른 논문의 builds_on 대상'이라는 사실 자체가 계보(lineage) 신호다.
- 조상으로 인용: 2312.00752

### OpenAI-o1  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거상 이 후보는 단순 실험 백본이 아니라 다른 논문에서 계보 부모로 쓰였습니다: cited_as_ancestor_in에 따르면 Search-o1이 이를 조상으로 인용하므로, 가드라인의 'builds_on(조상)으로 인용됐다는 사실 자체가 계보 신호'에 해당합니다.
- 조상으로 인용: 2501.05366

### Re2Search  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: `Re2Search` is cited as an ancestor in “RAG-Gym: A Framework for Process Supervision in Autonomous Search Agents,” and being used as a builds-on parent is itself a lineage signal under the rubric, even without an explicit definition here.
- 조상으로 인용: 2502.13957

### CPT  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거상 CPT는 최소한 한 논문에서 조상 방법으로 직접 인용됩니다(“cited_as_ancestor_in: Retrieval-Augmented Reasoning Modeling (RARE)”), 그리고 루브릭상 다른 논문의 builds_on/ancestor로 쓰인 이름은 베이스모델처럼 보여도 계보(lineage) 신호로 봐야 합니다.
- 조상으로 인용: 2503.23513

### Tool-Integrated Reasoning  `pending`
- 제안: **reject** · umbrella · 확신 med
- 근거: Evidence only shows the phrase as the task/paradigm named in the title “Optimal Tool Call-controlled Policy Optimization for Tool-Integrated Reasoning,” not a distinct method being extended or improved, so it is better treated as a broad umbrella term rather than a named lineage node.
- 조상으로 인용: 2504.14870

## ✅ 확신 높음 — category별 일괄 검토

### author_year — 2개
- **Kaplan et al. (2020)** (reject) — The candidate is an author-year citation form ('Kaplan et al. (2020)') rather than a named method/technique, even though it is cited as an ancestor in 'Training Compute-Optimal Large Language Models'.
- **Nickerson et al. (2013)** (reject) — The candidate is formatted as an author-year citation ('Nickerson et al. (2013)') rather than a named method or technique, so it fits the author_year reject category despite being cited in a taxonomy paper.

### component — 1개
- **Gain Beyond RAG (GBR)** (reject → RAG) — The evidence defines Gain Beyond RAG (GBR) as "a reward signal" measuring improvement over naïve RAG, which makes it a training/evaluation component rather than a named method lineage.

### duplicate — 4개
- **recurrent neural networks** (merge_into:RNN → RNN) — The candidate appears to be a spelling-out variant of the existing concept “RNN” (“recurrent neural networks” = RNN), so this is best treated as a duplicate label rather than a distinct named method.
- **retrieve-and-generate** (merge_into:RAG → RAG) — The candidate name “retrieve-and-generate” appears to be a spelling-out/variant of the existing concept “RAG” (Retrieval-Augmented Generation), and no separate definition or distinct ancestor evidence is provided here.
- **instruction fine-tuning** (merge_into:instruction tuning → instruction tuning) — The candidate appears to be a wording variant of the existing concept “instruction tuning,” and the evidence only shows it as a general training paradigm cited in RAFT rather than a distinct named method.
- **Dense Passage Retriever** (merge_into:DPR → DPR) — The candidate name 'Dense Passage Retriever' is the expanded form of the established method acronym 'DPR', and the evidence places it as the named neural retriever used in RAG ('accessed with a pre-trained neural retriever'), so this is best treated as a naming variant of the existing concept.

### generic — 15개
- **supervised fine-tuning** (reject) — ‘supervised fine-tuning’는 특정 논문이 제안한 고유한 방법명이 아니라 여러 작업에 널리 쓰이는 일반 학습 절차(SFT)의 풀어쓴 표현이므로 명명된 방법/기법 계보 노드로 보기 어렵습니다.
- **RL** (reject → REPLUG LSR) — ‘RL’는 reinforcement learning의 약어로 특정 논문이 제안한 고유한 방법명이 아니라 일반 학습 패러다임을 가리키는 일반어입니다.
- **encoder-decoder architectures** (reject) — ‘encoder-decoder architectures’는 특정 논문이 제안한 고유한 명명 방법이 아니라 모델 계열을 가리키는 일반적 아키텍처 용어이며, 제공된 evidence에도 이를 특정 lineage로 볼 정의문이나 조상 인용이 없습니다.
- **gated recurrent neural networks** (reject) — ‘gated recurrent neural networks’는 특정 논문이 제안한 고유한 방법명이라기보다 GRU/LSTM류를 포괄하는 일반 모델 계열 표현이며, 제공된 evidence에도 이를 명명된 계보 방법으로 볼 정의문이나 후속 논문의 extends/improves 대상 인용이 없습니다.
- **question answering** (reject) — ‘question answering’는 특정 논문이 제안한 고유한 방법명이 아니라 널리 쓰이는 일반 과업/문제 설정 용어이며, 정의문이나 조상 인용 같은 계보 근거도 제시되지 않았습니다.
- **language modeling** (reject) — ‘language modeling’ is a broad task/training objective rather than a named method lineage, and there is no evidence here that it is introduced or cited as a specific method ancestor.
- **span extraction** (reject) — 'span extraction'는 특정 논문이 제안한 고유한 방법명이 아니라 텍스트에서 구간(span)을 뽑는 일반 작업/기법명으로 보이며, 정의문·조상 인용 같은 lineage 근거도 제시되지 않았습니다.
- **maximum inner product search** (reject) — "maximum inner product search" is a general problem/task name in retrieval and nearest-neighbor search, not evidence of a specific named method or technique lineage in the provided fields.
- **autoregressive language models** (reject) — "autoregressive language models" is a broad class of models rather than a uniquely named method/technique, and there is no evidence here that it is introduced or cited as a specific ancestor method.
- **adapters** (reject) — ‘adapters’는 특정 논문이 제안한 고유명사 방법명이 아니라 일반적인 파라미터 효율 미세조정 기법을 가리키는 보통명사이며, provided evidence에도 이를 명명된 계보 방법으로 볼 정의문이나 조상 인용이 없습니다.
- **retrieval-augmented language models** (reject) — ‘retrieval-augmented language models’ is a broad descriptive class of models rather than a uniquely named method, and there is no evidence here that it is introduced or cited as a specific ancestor technique.
- **large language models** (reject → emergent abilities of large language models) — "large language models" is a broad class of models rather than a named method/technique, and the provided evidence does not show it being defined or cited as a specific ancestor method.
- **query rewriting** (reject) — ‘query rewriting’는 특정 고유명사 방법명이 아니라 검색/질의 처리 전반에서 널리 쓰이는 일반적 기법명이며, 정의문·조상 인용 등 이를 명명된 방법(lineage)으로 볼 근거가 제시되지 않았습니다.
- **reinforcement learning** (reject) — ‘reinforcement learning’는 특정 논문이 제안한 고유한 명명 방법이 아니라 여러 방법에 공통으로 쓰이는 일반 학습 패러다임/용어이므로 lineage 노드보다 generic에 가깝습니다.
- **raw trajectories** (reject) — "raw trajectories" has no evidence of being a named method or technique in the provided fields and reads as a generic phrase for unprocessed trajectory data rather than a citable lineage node.

### lineage — 20개
- **DeepSeek-R1-Zero** (approve) — The evidence defines DeepSeek-R1-Zero as a specific named method—“an LLM trained with pure reinforcement learning on verifiable rewards”—and it is also cited as an ancestor in SEARCH-R1, which is a strong lineage signal rather than a mere substrate mention.
- **DeepSeek-R1** (approve) — The evidence presents DeepSeek-R1 as a named method/model introduced in its own paper ('DeepSeek-R1: Incentivizing Reasoning Capability in Large Language Models via Reinforcement Learning') and it is also cited as an ancestor by a later work ('ReSearch'), which is a strong lineage signal rather than a generic component or mere substrate.
- **SEARCH-R1** (approve) — The evidence defines SEARCH-R1 as a named method—“a reinforcement learning framework that trains large language models to interleave multi-turn search queries with step-by-step reasoning”—and it is also cited as an ancestor by later papers, which is a strong lineage signal rather than a generic RL component.
- **R1-Searcher++** (approve) — The evidence defines “R1-Searcher++” as a specific named method—“a two-stage training framework” introduced in the paper titled “R1-Searcher++”—which fits a named technique/method rather than a generic component or substrate.
- **DeepResearcher** (approve) — The evidence defines DeepResearcher as a specific named method—“a reinforcement-learning framework for training LLM-based research agents to interact with live web search engines and perform iterative reasoning and evidence gathering”—which fits a named technique rather than a generic component.
- **DeepRAG** (approve) — The evidence defines DeepRAG as a specific named framework—“A retrieval-augmented reasoning framework that models the retrieval process as a Markov Decision Process”—which indicates a distinct method rather than a generic component or umbrella term.
- **WebThinker** (approve) — The evidence defines WebThinker as a specific named method—“an autonomous deep research agent” introduced in the paper title itself (“WebThinker: Deep Research Agent via Autonomous Think-Search-and-Draft”)—rather than a generic component or substrate.
- **RAG-Gym** (approve → RAG) — The evidence defines RAG-Gym as a named method/framework—“RAG-Gym: A Framework for Process Supervision in Autonomous Search Agents” that “formulates agentic search as an MDP and shifts supervision from final answers to intermediate search processes”—so it is a specific technique rather than generic RAG or a training component.
- **Re2Search++** (approve) — The evidence defines Re2Search++ as a named method — “a process-supervised search agent built on RAG-Gym and Re2Search” — indicating it is a specific technique rather than a generic component or substrate.
- **s3** (approve) — The evidence defines “s3” as a specific named method—“a modular RL-based search framework” introduced in its own paper—so it is a named technique rather than a generic RL component.
- **DeepRetrieval** (approve) — The evidence defines DeepRetrieval as a named method—“A reinforcement learning framework that trains LLMs to generate or rewrite queries by directly optimizing retrieval performance”—and it is also cited as an ancestor by a later paper (s3), which is a strong lineage signal.
- **StarPO-S** (approve) — The evidence defines StarPO-S as "a stabilized variant of StarPO," i.e., a named method variant built by extending an existing method rather than a generic component or mere base model.
- **OTC-PO** (approve) — The evidence defines OTC-PO as a named method—“Optimal Tool Call-controlled Policy Optimization,” a “reinforcement-learning framework” introduced in its own paper—so it is a specific proposed technique rather than a generic RL component.
- **ReasoningBank** (approve) — The evidence defines ReasoningBank as a named method/framework—“a memory framework that distills generalizable reasoning strategies … and retrieves them to guide future interactions”—rather than a generic component or substrate.
- **KG-R1** (approve) — The evidence defines KG-R1 as a specific named framework—“An agentic KG-RAG framework that uses end-to-end multi-turn reinforcement learning to learn a single unified policy”—which indicates a distinct method rather than a generic component or substrate.
- **HiPRAG** (approve) — The evidence defines HiPRAG as a specific named method—“a hierarchical process-reward training framework for agentic RAG”—rather than a generic component or base model, so it fits a named technique/method node.
- **GlobalRAG** (approve) — The evidence defines GlobalRAG as a named method—“GlobalRAG: A Reinforcement Learning Framework for Global Reasoning in Multi-hop QA” that “decompos[es] questions into subgoals and coordinat[es] retrieval with reasoning”—so it is a specific technique rather than a generic RL component.
- **MARAG-R1** (approve) — The evidence defines MARAG-R1 as a specific named method—“a unified multi-tool agentic RAG framework that learns to coordinate multiple retrieval mechanisms with reinforcement learning”—which fits a named technique rather than a generic component or substrate.
- **Bi-RAR** (approve) — The evidence defines Bi-RAR as a specific named framework—“Bi-RAR: Bidirectional Retrieval-Augmented Reasoning with Information Distance” that “evaluates each intermediate reasoning step ... and optimizes it with multi-objective reinforcement learning”—which indicates a distinct method rather than a generic component or substrate.
- **S4** (approve) — Evidence of lineage is explicit because this candidate is cited as an ancestor in “Mamba: Linear-Time Sequence Modeling with Selective State Spaces” (2312.00752), indicating S4 is a named prior method/model family that Mamba builds on rather than merely a generic component or substrate.

### umbrella — 1개
- **LLM agents** (reject) — "LLM agents" is a broad umbrella label for a class of systems rather than a specific named method/technique, and no evidence here shows it being defined as a distinct method lineage.
