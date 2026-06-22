# 검토 도우미 — 제안 리포트 (결정 아님 · lexicon 무변경)

검토 대기 **97개** · 제안 분포: approve 39 · reject 50 · merge 8
· **확신 낮음 21개**(사람 우선 검토)

> 이 문서는 *제안*이다. approve/reject/merge는 사람이 최종 클릭한다.

## ⚠️ 확신 낮음·중간 — 한 장씩 검토

### Active RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에 정의문·도입 논문·조상 인용이 전혀 없어 명명된 방법인지 일반적/우산적 표현인지 판별할 근거가 부족하며, 가드라인상 'Active RAG'류는 자동 reject보다 사람 검토가 필요한 애매 사례입니다.
- 유사 기존 개념: `RAG`

### trajectory memory  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제공된 evidence에서 특정 논문이 제안한 고유한 방법명이나 계보 부모로 인용된 사례가 없고, 'trajectory memory'는 일반적으로 에이전트의 궤적/경험을 저장하는 기능을 가리키는 일반 표현으로 보입니다.

### workflow memory  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제시된 evidence에 정의문·인용·조상 관계가 전혀 없어 고유한 명명된 방법으로 확인되지 않고, 'workflow memory'는 일반적 기능/개념 표현으로 읽히므로 현재로서는 generic으로 보는 것이 타당합니다.

### ToG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에 정의문·등장 문맥·조상 인용 정보가 전혀 없어 'ToG'가 명명된 방법인지, 일반 약어/우산 범주인지 판단할 근거가 부족하므로 보수적으로 우산/모호 약어로 분류해 사람 검토가 필요합니다.

### ReKnoS  `pending`
- 제안: **approve** · lineage · 확신 low
- 근거: 후보명 'ReKnoS'는 일반 학습 부품이나 저자-연도 인용 형식이 아니라 고유한 방법명으로 보이지만, 현재 evidence에 정의문·등장 논문·조상 인용 정보가 전혀 없어 본문에서 실제로 명명된 방법인지 확인할 수 없으므로 계보 후보로만 낮은 확신으로 제안합니다.

### RoG  `pending`
- 제안: **approve** · lineage · 확신 low
- 근거: ‘RoG’는 일반어·학습부품·저자연도 표기가 아니라 통상 논문에서 고유한 방법명 약칭으로 쓰이는 형태이며, 현재 증거가 비어 있어 단정은 어렵지만 명명된 기법일 가능성이 높아 사람 검토 전제로 계보 후보로 두는 것이 보수적입니다.

### Sparse Transformer  `pending`
- 제안: **merge_into:Transformer** · duplicate · 확신 low
- 근거: 제시된 evidence에 정의문·계보 인용이 없고 이름만 보면 기존 개념인 "Transformer"의 변형 표기로 해석되는 반면, 별도의 고유 명명 방법으로 확인할 근거가 부족합니다.
- 유사 기존 개념: `Transformer`

### Gopher  `pending`
- 제안: **approve** · lineage · 확신 low
- 근거: ‘Gopher’는 일반 학습 부품이나 저자-연도 표기가 아니라 논문에서 고유명사로 제시된 명명된 모델/방법명으로 해석되므로, 추가 근거가 비어 있어도 현 단계에서는 계보 후보로 보는 것이 타당합니다.

### GPT-J  `pending`
- 제안: **reject** · substrate · 확신 low
- 근거: 제공된 evidence에 정의문이나 다른 논문이 이를 기반으로 방법을 확장·개선했다는 계보 신호가 없고, 'GPT-J'는 일반적으로 실험에 사용하는 베이스 모델명으로 해석되는 경우가 많아 현재 정보만으로는 명명된 방법 lineage로 보기 어렵습니다.

### active retrieval augmented generation  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에 정의문·명명 논문·조상 인용이 전혀 없어 현재로서는 'active retrieval augmented generation'이 고유한 방법명인지, 아니면 'agentic/active RAG'류의 넓은 우산 표현인지 판별 근거가 부족하므로 보수적으로 우산 범주로 본다.

### passive retrieval augmented LMs  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에 정의문·사용 문맥·조상 인용이 전혀 없어 명명된 고유 방법인지 확인할 수 없고, 표현상으로는 특정 기법명보다 검색증강 언어모델의 한 유형을 가리키는 모호한 우산 범주로 보입니다.

### GTR  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제공된 evidence에 정의문·등장 문맥·조상 인용 정보가 전혀 없어 GTR이 명명된 방법 계보(lineage)인지 일반 약어인지 판단할 근거가 부족하므로 보수적으로 generic으로 분류합니다.

### Naive RAG  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제공된 evidence에서 고유한 방법명으로 정의되거나 특정 논문이 이를 조상 방법으로 확장했다는 근거가 없고, 기존 개념인 'RAG'의 단순한 설명적 변형처럼 보여 일반적 분류어에 가깝습니다.
- 유사 기존 개념: `RAG`

### Advanced RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에 정의문·사용 문맥·조상 인용이 전혀 없고 이름상으로도 기존 'RAG'를 수식하는 모호한 우산 표현에 가까워 현재로서는 변별력 있는 명명된 방법이라고 보기 어렵습니다.
- 유사 기존 개념: `RAG`

### Modular RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제시된 evidence에 정의문·등장 논문·조상 인용 정보가 전혀 없어 고유한 명명된 방법인지 판단할 근거가 부족하고, 현재로서는 기존의 RAG를 수식하는 모호한 우산 표현으로 보입니다.
- 유사 기존 개념: `RAG`

### Graph-based RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에서 정의문·대표 제안 논문·후속 논문의 조상 인용이 전혀 없어, 'Graph-based RAG'는 현재로서는 특정 명명된 방법이라기보다 RAG에 그래프를 활용하는 접근 전반을 가리키는 모호한 우산 표현으로 보입니다.
- 유사 기존 개념: `RAG`

### LLM agents  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 제공된 evidence에 정의문·대표 제안 논문·조상 인용이 전혀 없고, ‘LLM agents’는 특정 명명된 방법이라기보다 여러 에이전트형 LLM 접근을 넓게 가리키는 우산 표현으로 보입니다.

### successful routines  `pending`
- 제안: **reject** · generic · 확신 low
- 근거: 제시된 evidence에 정의문·인용·조상 관계가 전혀 없고, 'successful routines'는 본문에서 다른 논문이 확장하는 고유한 방법명이라기보다 일반 표현으로 보이므로 일반어로 검토하는 것이 타당합니다.

### agentic RAG  `pending`
- 제안: **reject** · umbrella · 확신 low
- 근거: 근거상 이 용어는 「MARAG-R1: Multi-tool Agentic Retrieval-Augmented Generation via Reinforcement Learning」에서 조상으로만 인용되지만, 개발자 가드에 따르면 'agentic RAG'는 일반어처럼 보여도 명명된 패러다임일 수 있어 자동 기각하기 어려우므로 우산 범주로 보되 사람 검토가 필요합니다.
- 유사 기존 개념: `RAG`
- 조상으로 인용: 2510.27569

### GraphRAG-R1  `pending`
- 제안: **merge_into:GraphRAG** · duplicate · 확신 low
- 근거: 제공된 근거에는 별도의 정의·정의 논문·조상으로 인용된 사례가 없고 기존 개념이 'GraphRAG'로 제시되어 있어, 현재로서는 'GraphRAG-R1'을 독립 계보라기보다 'GraphRAG'의 표기 변형 또는 파생 명명으로 보는 것이 타당합니다.
- 유사 기존 개념: `GraphRAG`

### CPT  `pending`
- 제안: **approve** · lineage · 확신 low
- 근거: 근거상 ‘CPT’는 최소한 논문 2503.23513(RARE)에서 조상 방법으로 인용되었으므로 단순 일반어·부품·실험용 베이스모델로 단정하기보다 계보(lineage) 후보로 보는 것이 타당합니다.
- 조상으로 인용: 2503.23513

### Search-o1  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거 문헌이 이를 “Search-o1: Agentic Retrieval-Augmented Generation for Large Reasoning Models”라는 고유한 프레임워크로 정의하며, “agentic search-driven retrieval and document reasoning”을 결합한 명명된 방법으로 제시하므로 일반어·부품보다 계보(lineage) 후보에 가깝습니다.
- 정의: A framework that augments large reasoning models with agentic search-driven retrieval and document reasoning to supply external knowledge during stepwise reasoning.
- 정의한 논문: 2501.05366

### RARE  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: evidence에서 RARE를 논문 제목과 정의문("Retrieval-Augmented Reasoning Modeling (RARE)", "A retrieval-augmented training paradigm...")으로 직접 명명된 방법/패러다임으로 제시하므로 일반 부품이나 단순 백본이 아니라 계보 후보로 보는 근거가 있습니다.
- 정의: A retrieval-augmented training paradigm that externalizes domain knowledge to retrievable sources while internalizing domain-specific reasoning patterns during training.
- 정의한 논문: 2503.23513

### StarPO  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: evidence에서 StarPO를 "A general trajectory-level reinforcement learning framework"라고 직접 명명하며 다중 턴 rollout·state-thinking-action-reward 표현·policy optimization을 갖춘 구체적 프레임워크로 정의하므로, 일반 부품(RL/PPO)이나 단순 일반어가 아니라 명명된 방법 계보 후보로 보는 것이 타당합니다.
- 정의: A general trajectory-level reinforcement learning framework for training LLM agents with multi-turn rollouts, state-thinking-action-reward representations, and policy optimization.
- 정의한 논문: 2504.20073

### RAGEN  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: evidence에서 RAGEN을 "A modular system for training and evaluating LLM agents under multi-turn and stochastic reinforcement learning settings"라고 고유하게 명명된 시스템으로 정의하고 있어 일반 부품이나 일반어보다 명명된 방법/프레임워크 계보 후보로 보는 것이 타당합니다.
- 정의: A modular system for training and evaluating LLM agents under multi-turn and stochastic reinforcement learning settings.
- 정의한 논문: 2504.20073

### SFT  `pending`
- 제안: **reject** · component · 확신 med
- 근거: 증거상 SFT는 논문 제목·방법명으로 계보를 이루는 고유 기법이라기보다 지도 미세조정(supervised fine-tuning)을 뜻하는 학습 부품/절차이며, RARE에서 조상처럼 언급되더라도 루브릭상 PPO·RL과 같은 component에 해당합니다.
- 조상으로 인용: 2503.23513

### OTC-GRPO  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거 문구가 "An instantiation of OTC-PO using Group Relative Preference Optimization"라고 명시해 OTC-PO의 구체적 명명 변형인 방법명이며, GRPO 자체는 구성요소이지만 후보인 OTC-GRPO는 그 구성요소를 사용한 별도 기법명으로 보입니다.
- 정의: An instantiation of OTC-PO using Group Relative Preference Optimization.
- 정의한 논문: 2504.14870

### GRPO  `pending`
- 제안: **reject** · component · 확신 med
- 근거: 근거상 GRPO는 「Optimal Tool Call-controlled Policy Optimization for Tool-Integrated Reasoning」에서 조상으로 인용되지만, 이름 자체가 policy optimization 계열의 학습 알고리즘/최적화 부품을 가리켜 고유한 방법 노드라기보다 학습 컴포넌트로 해석되는 것이 타당합니다.
- 조상으로 인용: 2504.14870

### MaTTS  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: evidence에서 MaTTS를 "Memory-aware test-time scaling"이라고 직접 명명·정의하고 있어 일반 학습 부품이나 베이스모델이 아니라 논문이 제안한 명명된 방법/기법으로 보는 근거가 있습니다.
- 정의: Memory-aware test-time scaling that increases an agent’s interaction experience to accelerate and diversify memory formation.
- 정의한 논문: 2509.25140

### HiPRAG  `unreviewed`
- 제안: **approve** · lineage · 확신 med
- 근거: evidence에서 HiPRAG를 "A hierarchical process-reward training framework for agentic RAG"라고 직접 명명·정의하고 있어 일반 부품이 아니라 고유한 방법명으로 보입니다.
- 정의: A hierarchical process-reward training framework for agentic RAG that gives step-level feedback on search decisions to improve both answer quality and retrieval efficiency.
- 정의한 논문: 2510.07794

### gated recurrent neural networks  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 제시된 evidence에 정의문·명명된 방법으로서의 사용례·조상 인용이 없고, ‘gated recurrent neural networks’는 특정 고유 기법명이라기보다 GRU/LSTM류를 포괄하는 일반적 모델 계열 표현으로 읽혀 generic으로 보는 것이 타당합니다.

### span extraction  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 제시된 evidence가 없고 'span extraction'은 특정 논문이 명명한 고유 방법명이 아니라 일반적인 정보추출 작업/기법을 가리키는 보통명사로 보입니다.

### dual-encoder  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 근거에는 이 용어가 특정 고유명사 방법명이 아니라 「Dense Passage Retrieval for Open-Domain Question Answering」에서 조상으로만 언급된 일반적 아키텍처 표현(dual-encoder)로 보이므로, 명명된 방법/기법 계보보다는 일반어에 가깝습니다.
- 조상으로 인용: 2004.04906

### maximum inner product search  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 제시된 evidence에 정의문·명명된 방법으로서의 사용례·조상 인용이 없고, 'maximum inner product search'는 특정 고유 기법명이라기보다 널리 쓰이는 일반 검색 문제/과업명을 가리키는 표현으로 보입니다.

### Compressive Transformer  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: ‘Compressive Transformer’는 ‘Transformer’의 단순 표기 변형이 아니라 압축 메모리를 도입한 별도의 명명된 방법명으로 해석되므로, 기존 개념 ‘Transformer’에 병합하기보다 계보(lineage) 후보로 검토하는 것이 타당합니다.
- 유사 기존 개념: `Transformer`

### GPT  `pending`
- 제안: **merge_into:GPT-3** · duplicate · 확신 med
- 근거: 후보명은 단독으로는 일반 계열명처럼 보이지만 제공된 근거에는 별도 방법으로 정의되거나 조상으로 인용된 사례가 없고, 기존 유사 개념이 명시적으로 "GPT-3"로 주어져 표기 변종으로 병합 검토하는 것이 타당합니다.
- 유사 기존 개념: `GPT-3`

### adapters  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 제시된 evidence에 정의문·인용·계보 맥락이 전혀 없고, 'adapters'는 일반적으로 파라미터 효율 미세조정의 일반 부품/기법군을 가리키는 보통명사이므로 고유한 명명된 방법으로 보기 어렵습니다.

### few-shot prompting  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 근거에는 이 용어가 「Least-to-Most Prompting Enables Complex Reasoning in Large Language Models」에서 조상으로 인용되었다는 사실만 있을 뿐, ‘few-shot prompting’ 자체가 고유하게 명명된 방법이라기보다 예시 몇 개를 주는 일반적 프롬프팅 방식이라는 점에서 일반어에 가깝습니다.
- 유사 기존 개념: `Few-shot chain-of-thought prompting`
- 조상으로 인용: 2205.10625

### RLAIF  `pending`
- 제안: **reject** · component · 확신 med
- 근거: RLAIF는 보통 ‘AI 피드백을 활용한 강화학습(Reinforcement Learning from AI Feedback)’을 뜻하는 학습 절차명으로, 본문에 고유한 명명 기법이라기보다 RLHF와 같은 학습 부품/패러다임 범주에 해당합니다.

### Hugging Face  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 제공된 evidence에서 ‘Hugging Face’는 논문 내에서 extends/improves의 대상이 되는 명명된 방법·기법이 아니라 일반적으로 플랫폼/조직명을 가리키는 표현일 뿐 계보적 방법명이라는 근거가 없습니다.

### Program-of-Thought Prompting  `pending`
- 제안: **merge_into:Zero-shot-Program-of-Thought Prompting** · duplicate · 확신 med
- 근거: 제공된 evidence에는 별도 정의·계보 인용이 없고 similar_existing_concept가 'Zero-shot-Program-of-Thought Prompting'로 지정되어 있어 현재로서는 동일 계열의 표기 변종으로 보는 것이 타당합니다.
- 유사 기존 개념: `Zero-shot-Program-of-Thought Prompting`

### retrieve-and-generate  `pending`
- 제안: **merge_into:RAG** · duplicate · 확신 med
- 근거: 후보명 'retrieve-and-generate'는 통상 'retrieval-augmented generation(RAG)'의 풀어쓴 표현에 가까우며, 제시된 evidence에 별도 정의·원전·계보 인용이 없어 독립된 명명된 방법이라기보다 기존 개념 'RAG'의 표기 변종으로 보는 것이 타당합니다.
- 유사 기존 개념: `RAG`

### retrieval-augmented LLMs  `pending`
- 제안: **reject** · umbrella · 확신 med
- 근거: 제시된 evidence에 정의문·명명 논문·조상 인용이 없고, ‘retrieval-augmented LLMs’는 특정 고유 방법명이라기보다 검색 증강 LLM 전반을 가리키는 우산적 표현으로 보입니다.

### Transformers  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 제공된 evidence에서 특정 논문이 제안한 고유한 방법명이 아니라 널리 쓰이는 일반 아키텍처 용어인 'Transformers'만 확인되므로, 명명된 방법 계보 노드보다는 일반어로 보는 것이 타당합니다.

### retrieval augmentation  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 근거에는 이 용어가 RAPTOR에서 조상으로 한 번 인용되었을 뿐이며, 'retrieval augmentation' 자체는 특정 논문이 명명한 고유 방법명이라기보다 검색을 통해 생성을 보강하는 일반적 접근을 가리키는 일반어로 보입니다.
- 조상으로 인용: 2401.18059

### query augmentation  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 제공된 evidence에 정의문·명명된 방법 인용·조상으로의 사용 사례가 전혀 없고, ‘query augmentation’은 일반적으로 질의 확장/변형을 뜻하는 폭넓은 일반어로 읽혀 고유한 방법명으로 보기 어렵습니다.

### GPT-2  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거에 따르면 GPT-2는 「GPT-3: Language Models are Few-Shot Learners」(2005.14165)에서 조상 방법으로 인용되므로, 단순 실험 백본이 아니라 후속 명명된 방법이 builds_on하는 계보(lineage) 신호로 보는 것이 타당합니다.
- 조상으로 인용: 2005.14165

### Reinforcement Learning from Human Feedback  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 증거상 이 용어는 고유한 단일 방법명이라기보다 일반 학습 패러다임으로 쓰이며, 인용 논문도 이를 특정 명명 기법이 아니라 보편적 정렬 절차인 'Reinforcement Learning from Human Feedback'의 선행으로 언급하므로 generic으로 보는 것이 타당합니다.
- 조상으로 인용: 2212.08073

### RL from AI Feedback  `pending`
- 제안: **reject** · generic · 확신 med
- 근거: 근거상 이 용어는 고유한 명명 기법이라기보다 논문 「Constitutional AI: Harmlessness from AI Feedback」에서 쓰인 일반적 학습 패러다임 표현으로 보이며, cited_as_ancestor_in 정보만으로는 다른 논문이 확장하는 독립된 방법명이라고 보기 어렵습니다.
- 조상으로 인용: 2212.08073

### SUPER-NATURALINSTRUCTIONS  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거에서 ‘SELF-INSTRUCT: Aligning Language Models with Self-Generated Instructions’가 이 개념을 조상으로 인용하고 있으므로, 단순 일반어가 아니라 후속 방법이 builds_on하는 명명된 방법 계보로 보는 것이 타당합니다.
- 조상으로 인용: 2212.10560

### PromptSource  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거에 따르면 PromptSource는 직접 정의문은 없지만 Self-Instruct(2212.10560)에서 조상으로 인용된 명명된 자원/방법명이므로, 단순 실험 백본이나 일반어가 아니라 계보(lineage) 후보로 보는 것이 타당합니다.
- 조상으로 인용: 2212.10560

### Codex  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거에 따르면 Codex는 「REPLUG: Retrieval-Augmented Black-Box Language Models」(2301.12652)에서 조상 방법으로 인용되므로, 단순 실험 백본이라기보다 다른 방법이 기반으로 삼는 명명된 계보 대상이라는 신호가 있습니다.
- 조상으로 인용: 2301.12652

### Bradley-Terry model  `pending`
- 제안: **reject** · component · 확신 med
- 근거: 근거로 제시된 것은 DPO 논문(2305.18290)에서 선호쌍 비교의 확률모형으로 Bradley-Terry model을 사용·인용했다는 사실뿐이며, 이는 다른 논문이 직접 확장하는 고유한 방법명이라기보다 보상모형/선호학습의 구성 요소로 쓰인 통계적 모델에 가깝다.
- 조상으로 인용: 2305.18290

### S5  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거에 따르면 S5는 「Mamba: Linear-Time Sequence Modeling with Selective State Spaces」(2312.00752)에서 조상 방법으로 인용되므로, 단순 백본이나 일반어가 아니라 후속 방법이 기반으로 삼는 명명된 기법 계보로 보는 것이 타당합니다.
- 조상으로 인용: 2312.00752

### OpenAI-o1  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거에 따르면 ‘OpenAI-o1’은 「Search-o1: Agentic Retrieval-Augmented Generation for Large Reasoning Models」에서 조상 방법으로 직접 인용되므로, 단순 실험 백본이라기보다 후속 방법이 builds_on하는 명명된 계보 노드로 보는 것이 타당합니다.
- 조상으로 인용: 2501.05366

### Re2Search  `pending`
- 제안: **approve** · lineage · 확신 med
- 근거: 근거에 따르면 ‘RAG-Gym: A Framework for Process Supervision in Autonomous Search Agents’가 Re2Search를 조상 방법으로 인용하고 있으므로, 단순 백본이나 일반어가 아니라 후속 연구가 builds_on하는 명명된 방법일 가능성이 높습니다.
- 조상으로 인용: 2502.13957

### Tool-Integrated Reasoning  `pending`
- 제안: **reject** · umbrella · 확신 med
- 근거: 근거상 이 용어는 「Optimal Tool Call-controlled Policy Optimization for Tool-Integrated Reasoning」의 제목에서만 조상 개념처럼 언급될 뿐 구체적으로 명명된 단일 방법이라기보다 도구 사용 추론 전반을 가리키는 우산 범주로 읽혀 변별력이 낮습니다.
- 조상으로 인용: 2504.14870

## ✅ 확신 높음 — category별 일괄 검토

### author_year — 2개
- **Kaplan et al. (2020)** (reject) — 후보가 방법명이 아니라 저자-연도 형식의 인용표현인 "Kaplan et al. (2020)" 자체이며, 근거에도 2203.15556에서 조상으로 인용된 참고문헌으로만 나타나므로 개념 노드로 승인하기 어렵습니다.
- **Nickerson et al. (2013)** (reject) — 후보가 방법명 자체가 아니라 저자-연도 형식의 인용명인 "Nickerson et al. (2013)"로 제시되어 있어, cited_as_ancestor_in 정보와 무관하게 개념 노드보다는 문헌 인용에 해당합니다.

### component — 3개
- **Group Relative Policy Optimization** (reject) — ‘Group Relative Policy Optimization’는 방법 전체의 고유명사 계보라기보다 RL 학습 알고리즘/최적화 부품(PPO류의 policy optimization) 명칭이므로, 루브릭상 명명된 방법 노드가 아닌 component로 보는 것이 타당합니다.
- **Gain Beyond RAG (GBR)** (reject → RAG) — evidence에서 GBR를 "retrieved documents over naïve RAG"에 대한 "reward signal"로 직접 정의하고 있어, 이는 명명된 독립 방법 계보라기보다 학습/평가용 보상 구성요소에 해당합니다.
- **OTC-PPO** (reject → PPO) — 근거 문구가 "An instantiation of OTC-PO using Proximal Policy Optimization"로, OTC-PPO는 명명된 독립 방법이라기보다 OTC-PO에 PPO라는 학습 부품을 적용한 변형으로 설명되므로 component로 보는 것이 타당합니다.

### duplicate — 3개
- **recurrent neural networks** (merge_into:RNN → RNN) — 후보명 'recurrent neural networks'는 기존 개념 'RNN'의 풀어쓴 표기 변종으로 보이며, 제시된 evidence에서도 별도의 고유 명명 기법이 아니라 동일 약어의 확장형으로 해석됩니다.
- **instruction fine-tuning** (merge_into:instruction tuning → instruction tuning) — ‘instruction fine-tuning’은 고유한 명명 기법이라기보다 기존 개념 ‘instruction tuning’의 표기 변형으로 보이며, 제시된 근거도 RAFT에서 조상으로 인용되었다는 사실뿐이라 별도 노드로 분리할 근거가 약합니다.
- **Dense Passage Retriever** (merge_into:DPR → DPR) — 근거 문헌(2005.11401)의 RAG 설명에서 비매개 메모리를 'a dense vector index of Wikipedia, accessed with a pre-trained neural retriever'로 두며 이는 통상 Dense Passage Retriever(DPR)를 가리키고, 기존 유사 개념이 이미 'DPR'로 제시되어 표기 확장형 중복으로 보는 것이 타당합니다.

### generic — 11개
- **supervised fine-tuning** (reject) — ‘supervised fine-tuning’은 특정 논문이 제안한 고유한 명명 방법이 아니라 여러 문맥에서 널리 쓰이는 일반 학습 절차(SFT)를 가리키는 일반어이므로 계보 노드로 보기 어렵습니다.
- **RL** (reject → REPLUG LSR) — ‘RL’은 특정 논문이 제안한 고유한 방법명이 아니라 강화학습 전반을 가리키는 일반 용어이므로, 본문에서 extends/improves의 대상이 되는 명명된 방법 계보 노드로 보기 어렵습니다.
- **encoder-decoder architectures** (reject) — ‘encoder-decoder architectures’는 특정하게 명명된 방법명이 아니라 모델 구조를 가리키는 일반 용어이며, 제시된 evidence에도 이를 계보상 조상으로 쓰인 고유 기법이라는 근거가 없습니다.
- **question answering** (reject) — ‘question answering’는 특정 논문이 제안한 고유한 방법명이 아니라 여러 작업 전반을 가리키는 일반 과업명이며, 정의문·조상 인용 등 계보 신호도 제시되지 않았으므로 일반어로 보는 것이 타당합니다.
- **language modeling** (reject) — ‘language modeling’은 특정 논문이 제안한 고유한 방법명이 아니라 언어 모델의 학습 과업 전반을 가리키는 일반 용어이므로 계보 노드로 보기 어렵습니다.
- **autoregressive language models** (reject) — ‘autoregressive language models’는 특정 논문이 제안한 고유한 방법명이 아니라 언어모델의 일반적 계열을 가리키는 보통명사이므로 개별 방법 노드로 승인하기 어렵습니다.
- **retrieval-augmented language models** (reject) — ‘retrieval-augmented language models’는 특정 고유명사 방법명이 아니라 검색 증강 언어모델 전반을 가리키는 일반적 기술 범주로 보이며, 정의문이나 조상 인용 같은 계보 근거도 제시되지 않았습니다.
- **large language models** (reject → emergent abilities of large language models) — ‘large language models’는 특정하게 명명된 방법명이 아니라 여러 모델군을 가리키는 일반 범주 표현이며, 제시된 evidence에도 이를 고유한 기법 계보로 볼 정의나 조상 인용이 없습니다.
- **query rewriting** (reject) — 제시된 evidence에 정의문·인용·조상 관계가 전혀 없고, 'query rewriting'은 특정 논문이 명명한 고유 방법명이라기보다 질의 재작성이라는 일반적 작업/기법 표현으로 읽히므로 generic으로 보는 것이 타당합니다.
- **reinforcement learning** (reject) — ‘reinforcement learning’은 특정 논문이 제안한 고유한 명명 방법이 아니라 여러 방법에 공통으로 쓰이는 일반 학습 패러다임이므로 계보 노드보다 일반어에 해당합니다.
- **raw trajectories** (reject) — 제시된 evidence에서 특정 논문이 제안한 고유한 방법명이 아니라 단순히 데이터·경로를 뜻하는 일반 표현인 "raw trajectories"만 확인되므로 일반어로 보는 것이 타당합니다.

### lineage — 20개
- **DeepSeek-R1-Zero** (approve) — 근거 정의문에서 DeepSeek-R1-Zero를 'supervised fine-tuning 없이 순수 강화학습으로 추론 능력을 유도한' 고유한 방법명으로 제시하고, 또한 SEARCH-R1에서 조상(ancestor)으로 인용되어 다른 방법이 builds_on하는 계보 신호가 분명하므로 lineage로 보는 것이 타당합니다.
- **DeepSeek-R1** (approve) — 정의문에서 ‘DeepSeek-R1’이 강화학습·거절 샘플링·지도 미세조정을 결합한 고유한 다단계 추론 모델로 명명되어 있고, 또한 후속 논문 「ReSearch: Reasoning with Search via Reinforcement Learning」에서 조상 방법으로 인용되어 계보 신호가 분명하므로 lineage로 보는 것이 타당합니다.
- **SEARCH-R1** (approve) — 정의문에서 SEARCH-R1을 "A reinforcement learning framework"라는 고유한 방법명으로 직접 제시하고 있으며, 추가로 여러 후속 논문이 이를 ancestor로 인용하고 있어 단순 학습 부품이나 일반어가 아니라 계보상 명명된 방법으로 보는 근거가 충분합니다.
- **R1-Searcher++** (approve) — evidence에서 ‘R1-Searcher++’를 “A two-stage training framework”라고 직접 정의하며 내부 지식과 외부 검색을 적응적으로 활용하도록 가르치는 고유한 명명 방법으로 제시하므로 lineage로 보는 것이 타당합니다.
- **DeepResearcher** (approve) — evidence에서 DeepResearcher를 논문 제목과 정의문에서 직접 ‘A reinforcement-learning framework for training LLM-based research agents…’라고 고유하게 명명된 방법으로 소개하므로, 일반 학습 부품이 아니라 명명된 방법 계보 후보로 보는 것이 타당합니다.
- **DeepRAG** (approve) — evidence에서 DeepRAG를 "A retrieval-augmented reasoning framework"로 직접 명명하고 있으며 검색 과정을 MDP로 모델링하는 고유한 방법명으로 정의하므로 일반 부품이나 베이스모델이 아니라 명명된 기법 계보로 보는 근거가 충분합니다.
- **WebThinker** (approve) — evidence에서 WebThinker를 논문 제목과 정의문에서 직접 'An autonomous deep research agent'로 명명된 방법으로 소개하고 있어 일반 부품이나 베이스모델이 아니라 고유한 방법명으로 보는 근거가 있습니다.
- **RAG-Gym** (approve → RAG) — evidence에서 RAG-Gym을 "A Framework for Process Supervision in Autonomous Search Agents"로 명명하고 "agentic search를 MDP로 정식화하고 supervision을 intermediate search processes로 옮긴다"고 정의하므로, 일반 부품이나 단순 베이스모델이 아니라 고유하게 명명된 방법/프레임워크로 보입니다.
- **Re2Search++** (approve) — 정의문에 따르면 Re2Search++는 "RAG-Gym and Re2Search" 위에 구축된 고유한 검색 에이전트 방법으로서 다중 홉 정보 탐색 성능을 개선한 명명된 기법이므로 계보(lineage)로 보는 근거가 충분합니다.
- **s3** (approve) — evidence에서 s3를 논문 제목과 정의로 직접 제시하며("s3: Searcher for Search-Only Reinforcement Learning in Retrieval-Augmented Generation", "A modular RL-based search framework...") 검색기만 학습하는 고유한 명명된 방법으로 소개하므로 일반 부품이나 일반어보다 방법 계보(lineage)로 보는 근거가 충분합니다.
- **DeepRetrieval** (approve) — 후보는 정의문에서 스스로를 'A reinforcement learning framework'라는 고유한 방법명으로 제시하고 있으며, 또한 후속 논문(s3)에서 조상으로 인용되므로 단순 학습 부품이나 일반어가 아니라 계보상 명명된 방법으로 보는 근거가 있습니다.
- **StarPO-S** (approve) — evidence에서 StarPO-S를 "A stabilized variant of StarPO"라고 직접 정의하며 trajectory filtering, critic baselining, gradient stabilization으로 개선한 명명된 방법의 변형이므로 계보(lineage) 후보로 보는 근거가 충분합니다.
- **OTC-PO** (approve) — 근거 문헌이 OTC-PO를 "Optimal Tool Call-controlled Policy Optimization"이라는 고유한 강화학습 프레임워크로 직접 정의하고 있어 일반 부품이나 우산어가 아니라 명명된 방법으로 보입니다.
- **ReasoningBank** (approve) — evidence에서 ReasoningBank를 "A memory framework that distills generalizable reasoning strategies ... and retrieves them to guide future interactions"라고 고유하게 정의한 명명된 방법으로 제시하므로 일반 부품이나 일반어보다 방법 계보 후보로 보는 것이 타당합니다.
- **KG-R1** (approve) — evidence에서 KG-R1을 "An agentic KG-RAG framework"이자 "end-to-end multi-turn reinforcement learning"으로 학습되는 단일 정책을 가진 고유한 프레임워크로 직접 정의하고 있어, 일반 부품이나 우산어가 아니라 명명된 방법/기법으로 보는 근거가 충분합니다.
- **GlobalRAG** (approve) — evidence에서 "GlobalRAG: A Reinforcement Learning Framework for Global Reasoning in Multi-hop QA"로 고유명사화된 방법명을 제시하고, 질문을 하위 목표로 분해해 검색과 추론을 조정하는 구체적 프레임워크로 정의하므로 일반 부품이나 일반어보다 명명된 방법 계보로 보는 근거가 충분합니다.
- **MARAG-R1** (approve) — evidence에서 MARAG-R1을 논문 제목과 정의로 직접 제시하며("MARAG-R1: Multi-tool Agentic Retrieval-Augmented Generation via Reinforcement Learning", "A unified multi-tool agentic RAG framework...") 강화학습이라는 부품을 사용하더라도 후보 자체는 명명된 방법/프레임워크이므로 lineage로 보는 근거가 충분합니다.
- **Bi-RAR** (approve) — evidence에서 Bi-RAR를 논문 제목과 정의문으로 직접 명명된 프레임워크("Bi-RAR: Bidirectional Retrieval-Augmented Reasoning...", "A retrieval-augmented reasoning framework...")로 소개하므로 일반 부품이나 일반어가 아니라 승인 가능한 방법 계보 후보로 보입니다.
- **ChatGPT** (approve) — 근거에 따르면 이 후보는 단순 실험 백본이 아니라 「HuggingGPT」, 「Generative Agents」, 「RankGPT」에서 조상 방법으로 직접 인용되므로, 다른 논문이 기반으로 삼는 명명된 방법이라는 계보(lineage) 신호가 분명합니다.
- **S4** (approve) — 근거에 따르면 S4는 「Mamba: Linear-Time Sequence Modeling with Selective State Spaces」(2312.00752)에서 조상 개념으로 직접 인용되므로, 단순 일반어·부품이 아니라 후속 방법이 builds_on하는 명명된 방법 계보다.

### umbrella — 1개
- **LLM-based multi-agent systems** (reject) — ‘LLM-based multi-agent systems’는 특정 논문이 제안한 고유한 방법명이 아니라 여러 접근을 포괄하는 일반적 우산 표현이며, 정의문·조상 인용 같은 계보 근거도 제시되지 않아 변별력 낮은 범주로 보는 것이 타당합니다.
