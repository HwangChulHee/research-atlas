# PHASE C1 STEP3 — lexicon 노드 판정 (신규 배치 미등록 타깃)

> C1 미등록 노드를 **"실재 명명 시스템/기법" vs "범주어/이론착안/부품"**으로 분류.
> **결정 기준 = 노드 유효성**(점수 아님 — 교훈: agentic RAG는 +1TP/+4FP였으나 유효성으로 미승격).
> 추가는 `status=unreviewed`(NODE_OK) append-only. 각 노드 점수영향(TP+/FP+)은 투명 표기용.
> 작성 2026-07-07. lexicon 269→284(+15). frozen/RAG relations·labels 무변경, 스모크 5/5.

## 추가 15개 (실재 명명 기법/시스템 → unreviewed)

| 노드 | rep_key | first_seen | TP+ | FP+ | 근거 |
|---|---|---|--:|--:|---|
| CAMEL | camel | 2307.05300 | 0 | 0 | 명명 MA 프레임워크(SPP가 딛음). 파이프라인 미emission이라 점수영향 0이나 유효 노드 |
| MAD | mad | 2402.18272 | 1 | 0 | Multi-Agent Debate(Du et al.), 명명 |
| Debate | debate | 2402.18272 | 1 | 0 | 명명 토론 기법(CMD가 확장, 사용자 예시에 명시) |
| ReConcile | reconcile | 2402.18272 | 1 | 0 | 명명 합의 기법 |
| FunSearch | funsearch | 2604.01658 | 1 | 0 | 명명(DeepMind), CORAL이 D2로 딛음 |
| AlphaEvolve | alphaevolve | 2604.01658 | 1 | 0 | 명명(DeepMind), CORAL이 D2로 딛음 |
| DSPy | dspy | 2407.01502 | 1 | 0 | 명명 프레임워크 |
| ExpertPrompting | expertprompting | 2307.05300 | 0 | 0 | 명명 기법(SPP가 딛음) |
| CodeCoT | codecot | 2312.13010 | 1 | 0 | 명명 코드생성 기법 |
| Self-Edit | self edit | 2312.13010 | 1 | 0 | 명명 기법 |
| CoT-SC | cot sc | 2402.05120 | 1 | 0 | CoT-Self-Consistency, 명명 |
| Verbal Reinforcement Learning | verbal reinforcement learning | 2503.14340 | 1 | 0 | =Reflexion(§4 결정: Reflexion류 포함) |
| tree of thought | tree of thought | 2308.05481 | 1 | 1 | Tree of Thoughts(Yao et al.), 명명. D-Bot이 딛음. (FP+1은 파이프라인 과잉emission — 노드 유효성과 무관) |
| Zettelkasten | zettelkasten | 2502.12110 | 1 | 0 | 명명 지식관리 방법론(A-MEM이 명시적으로 딛음). 비-AI지만 실재 명명 기법 |
| MAPE-K | mape k | 2307.06187 | 1 | 0 | 명명 자율컴퓨팅 참조아키텍처(Self-Adaptive MAS가 루프를 딛음). 타분야지만 실재 명명 |

**추가 합계 점수영향: TP +13, FP +1** (CAMEL·ExpertPrompting은 0). recall이 진실을 반영하게 됨.

## 미추가 2개 (범주어/부품 → 제외)

| 노드 | 사유 | (TP+/FP+ 참고) |
|---|---|---|
| self-reflection (self-correction) | **범주어**(D4) — 특정 명명 시스템 아닌 패러다임. | 0/0 |
| graph neural networks (GNN) | **부품/일반 ML 아키텍처** — G-Safeguard의 탐지 부품이지 방법 계보 아님. | 0/0 |

## 🛑 플래그 1개 (STOP — 사용자 판단)

| 노드 | 애매성 | 미추가 시 | 추가 시 |
|---|---|---|---|
| **LLM-as-a-judge** | "LLM을 심판으로" **범주어**인가, 아니면 **명명된 평가 패러다임**(Agent-as-a-Judge가 명시적으로 확장)인가 — 50/50. RAG·ReAct처럼 노드화된 패러다임과 유사하나, "as-a-judge" 표현이 범주 성격도 강함. | 현행(미등록, 2건 FN:lexicon탈락) | **TP +2, FP +0** |

권고: 유효성 경계가 진짜 50/50이라 강제하지 않음. 사용자가 "노드로 인정"하면 추가(TP+2). 이 리포트의
STEP4 채점은 **LLM-as-a-judge 미추가 기준**(보수적)으로 계산 — 승인 시 multiagent/eval recall이 소폭 더 오름.

## 범위 명시 (건드리지 않은 것)

C1은 **신규 배치(multiagent·eval)** 타깃만 대상. 전체 스캔에서 frozen/RAG 배치의 미등록 gold 타깃도
11개(adaptive rag·deepretrieval·rog·tog·reknos·zerosearch·absolute zero·atom searcher·selfcheckgpt·o1·
agentic rag) 발견됐으나 **baseline 보존 원칙상 미변경**(기존 FN:lexicon탈락 그대로). agentic RAG는 앞서
+1TP/+4FP로 미승격 결정 유지.
