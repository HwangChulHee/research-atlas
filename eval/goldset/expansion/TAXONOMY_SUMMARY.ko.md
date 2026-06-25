# RAG-추론 survey 분류 체계 요약 (4편)

goldset 확장 후보 큐레이션용. 각 survey가 **분야를 어떤 하위 범주로 쪼개는지**만 한국어로
정리한다(본문 번역 아님). 맨 아래에 네 survey를 가로지르는 통합 `section_tag` 어휘를 둔다 —
`candidates.csv`의 `section_tag`는 이 어휘만 쓴다.

> **수집 경로 메모.** s1·s2·s3 모두 동반 GitHub awesome-list가 있어 PDF 참고문헌 대신
> 그 목록(분류·arXiv 링크 정리됨)을 썼다 — 절 태그가 깨끗하고 비용도 낮다.
> s4는 공개 repo URL을 PDF에서 못 찾아, 본문 Figure 3 taxonomy(명명된 시스템)를 직접 썼다.
> - s1 = `DavidZWZ/Awesome-RAG-Reasoning`
> - s2 = `mangopy/Deep-Research-Survey`
> - s3 = `ventr1c/Awesome-RL-based-Agentic-Search-Papers`

---

## s1 — Towards Agentic RAG with Deep Reasoning (2507.09477)

**최상위 축**: 추론과 검색을 "어느 쪽이 어느 쪽을 돕는가"로 3분.
- **§3 Reasoning-Enhanced RAG (Reasoning→RAG)** — 추론으로 RAG 각 단계를 개선.
  - *Retrieval Optimization*: 질의 재작성·적응 검색 (DeepRetrieval, Adaptive-RAG, MaFeRw)
  - *Integration Enhancement*: 증거 충돌 해소·노이즈 강건 (SEER, ret-robust, BeamAggR)
  - *Generation Enhancement*: 근거 있는 생성 (EviOmni, Disco-RAG)
- **§4 RAG-Enhanced Reasoning (RAG→Reasoning)** — 검색한 지식이 추론의 빠진 전제를 보충.
  - *External Knowledge*: Knowledge Base/KG, Web Retrieval, Tool Using (GNN-RAG, Search-o1)
  - *In-context Retrieval*: 이전 경험(메모리)·예시/학습데이터 (Dr.ICL)
- **§5 Synergized RAG-Reasoning (RAG⇔Reasoning)** — (에이전트) LLM이 검색·추론을 반복 교차.
  - *Reasoning Workflow*: Chain / Tree / Graph 기반
  - *Agentic Orchestration*: Single-Agent / Multi-Agent(분산·중앙형)

**관점**: "한쪽 방향 강화(RTR, retrieve-then-reason)"의 한계를 짚고, 양방향이 맞물리는
synergized·agentic 프레임을 정점으로 둔다. 분류 골격이 가장 정연해 통합 축의 뼈대로 삼았다.

---

## s2 — Deep Research: A Systematic Survey (2512.02038)

**최상위 축**: deep-research 에이전트의 **동작 파이프라인 단계** + **학습 패러다임**.
- **Query Planning** — 분해·재작성·계획 (Least-to-Most, Tree-of-Thoughts, Search-R1)
- **Information Acquisition**
  - *Knowledge Boundary*: 모델이 "모름"을 아는가 — 캘리브레이션·불확실성 (R-Tuning, SelfCheckGPT)
  - *Retrieval Timing*: 언제 검색할까 — 적응/능동 검색 (FLARE, Self-RAG, DRAGIN, Search-o1)
  - *Information Filtering*: 재랭킹·압축·노이즈 제거 (RECOMP, RankRAG, Chain-of-Note)
- **Memory Management** — 장기/세션 메모리 (Reflective Memory Management 등)
- **Answer Generation** — 최종 합성·인용 충실성
- **Training Paradigm**
  - *Supervised Fine-tuning* / *Agentic End-to-End RL* (Search-R1, R1-Searcher, ZeroSearch …)
  - *Datasets & Benchmarks*: 평가 자원

**관점**: 단일 기법이 아니라 "deep research 시스템"을 단계별 부품 + 학습법으로 해부한다.
RL 학습층(Agentic E2E RL)이 가장 두껍다. → s3가 깊게 파는 층의 상위 지도.

---

## s3 — RL-based Agentic Search (2510.16724)

**최상위 축**: RL을 세 질문으로 가른다(같은 논문이 세 축에 동시 등장).
- **What RL is for — 기능적 역할(Functional Roles)** ← 본 작업에서 절 태그로 사용
  - *Retrieval Control*: 검색 여부/시점 결정
  - *Query Optimization*: 질의 생성·재작성
  - *Reasoning–Retrieval Integration*: 추론·검색 교차의 RL 학습 (agentic search 핵심)
  - *Multi-Agent Collaboration*: 다중 에이전트 협업
  - *Tool & Knowledge Integration*: 도구·외부지식 결합
- **How RL is used — 최적화 전략**: GRPO/PPO, ORM/PRM, rule-based vs LLM judge 보상 …
- **Where RL is applied — 범위**: Agent-/Step-/Module-/System-level
- **Evaluation**: 메트릭 · deep-research/agentic-search 벤치마크 · 데이터셋

**관점**: Search-R1 계열(RL로 학습된 검색 에이전트)의 정중앙. "어떤 보상으로 무엇을
학습시키나"가 핵심. 매우 최신(2025~2026) 논문 비중이 높다.

---

## s4 — Reasoning RAG via System 1 or System 2 (2506.10408)

**최상위 축**: 인지과학 이분법으로 2분.
- **Predefined Reasoning (System 1 — 빠름·고정 파이프라인)**
  - *Route-based*: 조건부 검색 트리거 (RAGate, Self-Route)
  - *Loop-based*: 자기성찰 반복 (Self-RAG, CRAG)
  - *Tree-based*: 계층 탐색 (RAPTOR, MCTS-RAG)
  - *Hybrid-modular*: 모듈 조립 (Adaptive-RAG, Modular-RAG)
- **Agentic Reasoning (System 2 — 느림·자율 결정)**
  - *Prompt-based*: 학습 없이 in-context (ReAct, Self-Ask, Search-o1)
  - *Training-based(RL)*: 보상으로 도구 사용 학습 (DeepRetrieval, Search-R1, R1-Searcher, DeepResearcher)

**관점**: "사전정의(고정 모듈) vs 학습형(자율 에이전트)"의 가장 단순·명료한 이분.
산업 적용·강건성 각도를 강조. 명명된 대표 시스템 16개만 추렸다.

---

## 메타 — 네 survey가 같은 지형을 어떻게 다르게 자르나

- **s4**가 가장 거칠게(사전정의 vs 학습형), **s1**이 가장 정연하게(추론↔검색 양방향 + synergized),
  **s2**가 시스템 파이프라인 단계로, **s3**가 RL 한 축을 가장 깊게 — 같은 분야를 추상도만 달리해 본다.
- **겹침**: Self-RAG·Search-o1·Search-R1·R1-Searcher·DeepResearcher 등 핵심 시스템은 네 곳에
  반복 등장한다(그래서 `candidates.csv`에서 한 행으로 합치고 `survey_source`에 `s1;s2;s3;s4`처럼 누적).
- **층위**: s3(RL-검색) ⊂ s2(deep-research 시스템) — s3가 파는 학습층을 s2가 상위 파이프라인에 얹는다.
  s4·s1은 그 위에서 "고정 vs 자율 / 추론↔검색 방향"의 큰 골격을 제공.

---

## 통합 section_tag 어휘 (candidates.csv 통제 어휘)

각 survey 원분류 → 아래 통합 태그로 사상. 한 논문이 여러 절에 걸치면 `;`로 누적.

| 통합 태그 | 뜻 | 주로 어디서 |
|---|---|---|
| `질의계획` | 질의 분해·재작성·계획 | s1 Retrieval Opt · s2 Query Planning · s3 Query Optimization |
| `검색시점` | 언제/검색할지(적응·능동·route/loop) | s2 Retrieval Timing · s3 Retrieval Control · s4 route/loop/prompt |
| `정보필터링` | 재랭킹·압축·노이즈 제거 | s1 Integration Enh · s2 Information Filtering |
| `지식경계` | 캘리브레이션·불확실성·"모름" 인지 | s2 Knowledge Boundary |
| `메모리` | 장기/세션 메모리·이전 경험 | s1 Prior Experience · s2 Memory Management |
| `생성` | 최종 합성·인용 충실성 | s1 Generation Enh · s2 Answer Generation |
| `추론워크플로우` | Chain/Tree 기반 구조적 추론 | s1 Chain/Tree · s4 Tree-based |
| `그래프RAG` | Graph/KG 기반 검색·추론 | s1 Graph-based·Knowledge Base |
| `에이전트오케스트레이션` | Single/Multi-Agent 협업·조율 | s1 Agentic Orchestration · s3 Multi-Agent |
| `학습형RL` | RL로 학습된 검색·추론 에이전트 | s2 Agentic E2E RL/SFT · s3 R–S Integration · s4 Training-based |
| `RAG강화추론` | 검색지식(웹·도구·예시)으로 추론 보강 | s1 §4 Web/Tool/Example · s3 Tool & Knowledge |
| `사전정의` | 고정 모듈 파이프라인(hybrid-modular) | s4 Hybrid-modular |
| `평가` | 데이터셋·벤치마크 | s1·s2·s3 Benchmarks/Datasets |
| `기타` | 위에 안 맞는 것(현재 후보엔 미사용) | — |
