# PHASE A5 — 멀티에이전트 배치 경계 패턴 보고 (STOP·사용자 검수 대기)

> multiagent_b3 60편(keep) builds_on 초안을 D1~D4로 잡았다. **강제로 루브릭에 맞추지 않고**,
> 판정이 갈리는 경계 패턴을 아래로 모은다. gold는 **draft:true·미freeze** — 사용자 검수 후 별도 확정.
> 작성 2026-07-07. keep 60 / drop 4 / builds_on 채워진 것 14편(빈 것 46편=**77%**).

## 0. 가장 큰 신호 — builds_on이 대부분 빈 리스트 (46/60)

멀티에이전트 논문은 선행 프레임워크(AutoGen·MetaGPT·CAMEL·AgentVerse·ChatDev)를 **거의 항상
"비교 baseline"으로 인용**한다("우리가 이들보다 낫다"). lineage-only 루브릭 D3는 단순 비교를 제외하므로
결과적으로 계보가 비게 된다. 즉 이 배치는 **구조적으로 empty-gold가 많다**(RAG batch의 48%보다 높은 77%).
→ **채점 시 precision 붕괴가 예고됨**(pipeline이 이 논문들에 RAG/프레임워크명을 뱉으면 전부 FP). PHASE C4에서
정량 확인 예정. 이 자체가 "멀티에이전트 위상의 계보 구조는 프레임워크-비교로 표현되지, 방법적 후예로는
잘 안 드러난다"는 발견.

## 1. 핵심 판단 게이트 — 프레임워크 인용: baseline인가 계보인가 (사용자 결정 필요)

같은 프레임워크(MetaGPT/ChatDev/AutoGen/CAMEL/AgentVerse)가 논문마다 **비교 baseline**로도, **한계→개선의
계보(D2)**로도 등장한다. 서브에이전트는 "그 위에 세웠다"는 명시 서술이 있을 때만 포함했다:

- **계보로 포함한 것(D2, 초안 반영)**: AgentCoder(2312.13010)→MetaGPT·ChatDev·AgentVerse(+CodeCoT·Self-Edit),
  MetaAgents(2310.06500)→ChatDev·MetaGPT("고정 팀구성 한계→자율 팀조립"), CMD(2402.18272)→Debate·MAD·ReConcile,
  CORAL(2604.01658)→AlphaEvolve·FunSearch("고정 진화탐색 한계→자율 위임"), SPP(2307.05300)→CAMEL·ExpertPrompting.
- **baseline로 보고 제외한 것**: AutoAgents(2309.17288), Achilles Heel, 대부분의 debate/orchestration 논문에서
  AutoGen·CrewAI·Reflexion·ChatDev가 **성능 비교표에만** 등장.

⚠ **결정 요청**: AgentCoder처럼 "MetaGPT보다 pass@1 높다"가 **동시에** "MetaGPT의 고정 워크플로를 개선"인
중첩 케이스를 계보로 볼지. 초안은 명시적 "한계→개선" 서술이 있으면 포함, 순수 성능표면 비교면 제외로 통일.

## 2. keep/drop 경계 (초안은 keep, 재검토 여지)

| 논문 | 경계 | 초안 |
|---|---|---|
| Chain-of-Agents/AFM (2508.13167) | MAS를 증류한 **단일 모델**이 최종 산물 → 단일에이전트 drop 기준과 충돌 | keep |
| O-Researcher (2601.03743) | 멀티에이전트가 **데이터합성 워크플로에만**, 배포는 단일 모델 | keep |
| Agent Forest / More Agents (2402.05120) | 통신 없는 독립 샘플링+다수결(self-consistency 스케일업), 협업 약함 | keep |
| AgentLite (2402.15538) | **라이브러리/프레임워크** 논문 — "방법 논문"인지 | keep |
| D-Bot (2308.05481 / 2312.01454) | 멀티에이전트가 시스템의 **부분 구성요소**(본질은 DB 진단) | keep |
| Self-collab / LTC (2310.01444) | single+multi 혼재 학습, MA가 유일 본질 아님 | keep |

→ 초안은 "논문 프레이밍이 멀티에이전트면 keep"로 관대하게. drop 후보로 볼지는 사용자 판단.

## 3. RAG를 계보로 볼지 (D4 범주어 경계)

RAG-KG-IL(2503.13514)·MAO-ARAG(2508.01005)은 초안에 `RAG` 포함, MDocAgent(2503.13964)·HM-RAG(2504.12330)·
지식캐시반복검색(2503.13275)은 D4(느슨한 ○○RAG 범주어)로 **제외**. → RAG를 named 패러다임으로 일관 포함할지,
범주어로 일관 제외할지 canon 단계(C1)에서 통일 필요. **불일치 존재**.

## 4. D1(옵티마이저) 경계 — 아키텍처 착안 vs 옵티마이저

- LLaMAC(2311.13884): **actor-critic** — 이름·구조의 착안원이나 RL 알고리즘 계열이라 D1 제외. 단 학습
  옵티마이저가 아닌 아키텍처 착안이라 애매.
- MANTRA(2503.14340): **Verbal Reinforcement Learning**(=Reflexion) — 그래디언트 옵티마이저 아닌 언어적
  자기반성이라 **포함**으로 판단(D1 경계).
- DyLAN(2310.02170): back-propagation/neuron-importance 착안 — 계보 애매, 제외.

→ D1은 "그래디언트 옵티마이저"로 좁게 적용, Reflexion류 언어기법은 포함으로 통일 제안(사용자 확인).

## 5. 명명 안 된 착안(제외 통일) · 데이터 교정

- **제외(통일)**: Society of Mind(Minsky)·cognitive architectures·debate theory·ABM 등은 **이론/개념 영감**이지
  named 시스템/기법이 아니라 전부 제외(SPP·GPTSwarm·MAD·Concordia 등에서).
- **데이터 교정**: `2503.10265` 후보 제목이 "SLA Management in Reconfigurable Multi-Agent RAG"로 오매핑돼
  있었으나 arXiv 원문은 **"SurgRAW: Multi-Agent Workflow ... Robotic Surgical Video Analysis"** — 원문 기준으로
  교정(멀티에이전트 맞아 keep 유지).

## drop 4편 (매니페스트 보존, 번복 가능)

- ChemCrow(2304.05376): 단일 LLM+툴(ReAct 루프), 멀티에이전트 아님.
- OpenAgents(2310.10634): 독립 스탠드얼론 3에이전트 호스팅, 상호 협업 없음.
- More LLM Calls(2403.02419): Vote/Filter-Vote 스케일링 **분석·이론**.
- Achilles Heel(2504.07461): 분산 MAS 신뢰성 **red-team 분석·평가**.

## 권고

초안은 위 통일 규칙(프레임워크는 명시적 한계→개선 서술 시만 계보 / RAG는 canon서 결정 / D1 좁게 /
착안 제외)으로 잡혀 있다. **freeze 전 사용자 검수 항목**: (1) §1 프레임워크-계보 중첩, (2) §2 단일모델 산물
keep 여부, (3) §3 RAG 포함/제외 통일. 나머지(§4·§5)는 제안대로 두길 권함.
