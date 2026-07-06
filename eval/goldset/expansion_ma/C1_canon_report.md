# PHASE C1 — 네이밍 canon 통일 리포트 (두 신규 배치)

> multiagent_b3 60 + eval_b4 16 의 builds_on 초안 타깃 이름을 기존 lexicon/canon과 대조.
> 외부 인용만 있는(코퍼스가 정의 안 한) 노드의 lexicon 추가 필요 여부를 **플래그**(사용자 결정).
> gold 초안·relations·lexicon 무변경(읽기 전용 분석). 작성 2026-07-07.

## 요약
- 신규 배치 builds_on 타깃 **고유명 26개(총 29건)**.
- **7개는 기존 lexicon에서 NODE_OK로 해소 → 채점 반영됨.**
- **19개는 lexicon에 없음(status None) → 채점 시 pred에서 탈락**(gold면 FN:lexicon탈락으로 잡힘).
- **canon 표면형 충돌 없음** — 대소문자/하이픈/괄호는 nc.canon이 흡수(예: `LLM-as-a-judge`=`LLM-as-a-Judge`→`llm as a judge`, `Retrieval-Augmented Generation (RAG)`→`rag`).

## NODE_OK로 해소되는 7개 (채점 반영)
| 표면형 | rep_key | status |
|---|---|---|
| Retrieval-Augmented Generation (RAG) | rag | approved |
| ChatDev | chatdev | approved |
| MetaGPT | metagpt | approved |
| AgentVerse | agentverse | approved |
| ReAct | react | approved |
| Chain-of-Thought (CoT) | cot | approved |
| Search-R1 | search r1 | unreviewed |

## lexicon에 없는 19개 (채점서 pred 탈락 — 추가 필요 여부 사용자 결정)

전부 **외부 인용 전용**(이 코퍼스의 어떤 논문도 정의하지 않음). 성격별:

- **멀티에이전트 협업 기법**: CAMEL, Debate, MAD(Multi-Agent Debate), ReConcile, ExpertPrompting, CoT-SC, MAPE-K
- **코드/자기수정 기법**: CodeCoT, Self-Edit, Verbal Reinforcement Learning(=Reflexion), tree of thought
- **평가/방법**: LLM-as-a-judge, DSPy, Agent-as-a-Judge 계열
- **과학탐색/메모리**: AlphaEvolve, FunSearch, Zettelkasten
- **부품성**: graph neural networks (GNN), self-reflection(범주어)

## 영향 · 결정

이 19개가 lexicon에 없으므로 **provisional 채점에서 신규 배치의 "채워진 gold" 상당수가 FN(lexicon탈락)**으로
잡힌다. 즉 신규 배치 recall이 파이프라인 성능이 아니라 **lexicon 커버리지 부족**으로 낮아 보일 수 있다.
채점 코드는 FN을 `lexicon탈락`(추출은 됐으나 status 미달) vs `추출X`(아예 못 뽑음)로 분리하므로, 리포트에서
이 둘을 나눠 **lexicon 갭 vs 파이프라인 미스**를 구분해 보고한다(oos_scoring_200.md).

**권고(사용자 결정 대기)**:
- **provisional 단계**: lexicon **무변경** 유지 — 현재 커버리지 기준 수치 + FN 분리로 갭을 정량화(이번 채점).
- **freeze 전**: 위 19개 중 실제 방법 노드(CAMEL·Debate·DSPy·FunSearch·AlphaEvolve·Zettelkasten 등)를
  unreviewed로 추가할지 사용자가 결정(부품성 GNN·범주어 self-reflection은 제외 권장). 추가하면 신규 배치
  recall이 올라가나, 이는 gold 확정(freeze)과 함께 가야 한다.
- **canon 통일 자체는 불필요** — 표면형 충돌이 없어 별도 alias/병합 작업 없음.
