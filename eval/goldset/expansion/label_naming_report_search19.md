# 네이밍 정합 리포트 — 검색시점 19편 builds_on

작성일: 2026-06-26
대상: batch2 keep 85편 중 검색시점 클러스터 19편 (`eval/goldset/labels.json` append 완료)
누적: 학습형RL 13 + 검색시점 19 = **확장 32/85** (frozen 50 별도)
canon 기준: `data/lexicon.json`(techniques) + 기존 labels(50 + 학습형RL 13)의 builds_on 표면형
판정: D1(GRPO/PPO/DPO/MCTS 등 옵티마이저 제외) + D4(느슨한 "○○ RAG" 우산 제외, 구체 패러다임·named 포함)

> 목적: 사람이 "정본(lexicon) 통일/추가 필요 항목"과 "표면형 불일치"를 한눈에. lexicon은 미수정(보고만).

---

## 1. 참조 방법명별 canon 정합 표

| 방법명 | lexicon 존재? | 기존 labels 표면형? | 기입 표면형 | 비고 |
|---|---|---|---|---|
| Chain-of-Thought | ⚠️ `CoT`(approved, alias "Chain of Thought") | ✅ `Chain-of-Thought` 다수 | `Chain-of-Thought` | labels 관례 따름. lexicon 대표는 `CoT` — canon(하이픈→공백)으로는 동일군이나 **정본 표면형 통일 필요**(`CoT` vs `Chain-of-Thought`) |
| FLARE | ✅ `FLARE`(approved) | ❌ (이번이 첫 사용) | `FLARE` | 일치 |
| Self-RAG | ✅ `Self-RAG`(approved, alias SelfRAG) | ✅ 2310.11511 등 | `Self-RAG` | 일치 |
| RAG | ✅ `RAG`(approved) | ✅ 다수 | `RAG` | 일치. 학습형RL과 교차 일치 ✓ |
| Search-R1 | ⚠️ `SEARCH-R1`(대문자) | ✅ `Search-R1`(학습형RL·50편) | `Search-R1` | 학습형RL과 **교차 일치 ✓**. lexicon 대소문자(`SEARCH-R1`) 통일은 기존 리포트와 동일 미결 |
| Absolute Zero | ❌ 없음 | ✅ `Absolute Zero`(2505.03335 title, 학습형RL) | `Absolute Zero` | **핸드오프 표는 `Absolute-Zero`였으나 기존 노드 표면형 `Absolute Zero`에 맞춰 기입**(내부 계보 연결). canon(하이픈→공백)으로 동일 → 채점 끊김 없음. §2(a) 참조 |
| ZeroSearch | ❌ 없음 | ❌ 없음 | `ZeroSearch` | **canon 미존재**. 잠정 기입. 정본 추가 후보 |
| Visual RAG | ❌ 없음 | ❌ 없음 | `Visual RAG` | **canon 미존재**. D4상 구체 패러다임이라 포함. `RAG`로 합치지 않음(별개 노드 후보) |
| OpenSeeker | ❌ 없음 | ❌ 없음 | `OpenSeeker` | **canon 미존재 + corpus 미존재**. 2605.04036(OpenSeeker-v2)의 전 버전(Du et al. 2026). §2(b) 참조 |

---

## 2. 사람 후속 결정이 필요한 항목

### (a) `Absolute Zero` ↔ 2505.03335 (내부 계보 연결) — 처리됨, 확인만
- 2510.14253이 2505.03335(배치2 논문) 자신을 builds_on으로 참조.
- 핸드오프 표는 `Absolute-Zero`(하이픈)였으나, 2505.03335의 기존 노드 표면형은 `Absolute Zero`(공백, 학습형RL에서 기입).
- **기존 노드에 맞춰 `Absolute Zero`로 통일** → 표기 불일치로 인한 채점 단절 없음(canon이 하이픈↔공백 흡수).
- 사람이 정본 표면형을 하이픈형으로 정한다면 2505.03335 title과 함께 일괄 변경 필요.

### (b) `OpenSeeker` — corpus/노드 부재
- 2605.04036(OpenSeeker-v2)이 자기 전 버전 `OpenSeeker`를 참조하나 lexicon·labels·goldset 어디에도 없음.
- 계보 타깃이 노드로 존재하지 않으면 채점 시 FN(lexicon탈락 아님, 아예 부재)로 빠질 수 있음.
- 결정 필요: OpenSeeker를 노드로 추가할지, 아니면 v2만 두고 계보를 생략할지.

### (c) canon 미존재 신규 — 정본 추가 후보
- `ZeroSearch`(2508.10874), `Visual RAG`(2604.09508). 모두 잠정 표기. lexicon 노드 추가 여부 사람 판단.
- `Visual RAG`는 D4상 `RAG`와 **별개 노드**로 두었다(임의 통합 금지). 합칠지 사람 결정.

### (d) `Chain-of-Thought` vs `CoT` 정본 통일
- lexicon 대표는 `CoT`, labels 표면형은 `Chain-of-Thought`. canon으론 동일군이나 정본 표면형이 갈림. (기존 50편부터의 미결 사항 — 이번에 재확인.)

---

## 3. ⚠ 사람 미확정 2건 (표값 그대로 기입, 번복 가능)

| id | title | 기입값 | 미확정 내용 |
|---|---|---|---|
| 2505.24332 | Pangu DeepDiver | `[]` | Iterative RAG를 넣을지 여부 — 우산(D4)이라 일단 제외, 사람 번복 가능 |
| 2604.19766 | OThink-SRR1 | `["RAG"]` | search-RL 3종 추가 여부 — 일단 RAG만, 사람 번복 가능 |

---

## 4. 기입 결과 요약 (19편)

| id | title | builds_on |
|---|---|---|
| 2210.03350 | Self-Ask | `["Chain-of-Thought"]` |
| 2403.10081 | DRAGIN | `["FLARE"]` (Dynamic RAG 제외 D4) |
| 2406.12534 | Unified Active Retrieval (UAR) | `["Self-RAG", "FLARE"]` |
| 2504.04736 | Synthetic Data & Multi-Step RL | `[]` |
| 2505.24332 | Pangu DeepDiver | `[]` ⚠ |
| 2508.10874 | SSRL | `["ZeroSearch"]` (Search-R1=baseline 제외) |
| 2510.14253 | Agentic Self-Learning | `["Search-R1", "Absolute Zero"]` |
| 2601.11037 | BAPO | `[]` |
| 2601.11888 | Agentic-R | `[]` |
| 2601.13115 | Agentic Conversational Search | `[]` (GRPO 부품 D1) |
| 2601.23188 | Meta-Cognitive Deep Search | `[]` |
| 2602.03304 | To Search or Not to Search | `[]` |
| 2602.03468 | IntentRL | `[]` |
| 2603.28376 | Marco DeepResearch | `[]` |
| 2604.04651 | Search, Don't Guess | `[]` |
| 2604.09508 | VISOR | `["Visual RAG", "RAG"]` |
| 2604.17931 | LiteResearcher | `[]` |
| 2604.19766 | OThink-SRR1 | `["RAG"]` ⚠ |
| 2605.04036 | OpenSeeker-v2 | `["OpenSeeker"]` |

빈 라벨 **11편**(독자 메커니즘 제안 다수 — D1/D4 적용 결과이지 "근거 못 찾음"이 아님).
> 참고: 핸드오프 본문은 "빈 라벨 12편"이라 했으나 표를 글자대로 세면 **11편**이다(비-빈 8 + 빈 11 = 19).
> 표값을 그대로 기입했으므로 실제 11편. 사람 확인 요망.

---

## 5. 검증/무수정 확인
- `labels.json`: 19편 append만 (git diff = 95 insertions / 0 deletions). 기존 50 + 학습형RL 13 **무변경**.
- 빈 라벨 11편 명시 기입(`[]`) — "검토했고 비어있음" ≠ "아직 안 함".
- `data/lexicon.json` · `data/outputs/` **무변경**.
- `labels.json` `_meta`: append-only 검증(`git diff = 19편 append만`)을 지키려 **미수정**.
  단 `_meta.labeled`가 63(실제 82=50+13+19)로 **stale** → 사람이 82로 갱신 권장(누적 32/85 반영).
