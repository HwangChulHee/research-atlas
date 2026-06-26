# 네이밍 정합 리포트 — 학습형RL 13편 builds_on

작성일: 2026-06-26
대상: batch2 keep 85편 중 학습형RL 클러스터 13편 (`eval/goldset/labels.json`에 append 완료)
canon 기준: `data/lexicon.json` (techniques, 263개) + 기존 `eval/goldset/labels.json` 50편 builds_on 표면형
판정 규칙: D1(GRPO/PPO/DPO/MCTS/DAPO 등 RL 옵티마이저·탐색 기법은 부품 → builds_on 제외)

> 목적: 사람이 "정본(lexicon) 추가/통일이 필요한 항목"을 한눈에 보도록 정리. 이 리포트는
> 보고일 뿐 lexicon은 수정하지 않았다(정본 변경은 사람 판단).

---

## 1. 참조된 방법명별 canon 정합 표

| 방법명 | lexicon 존재? | 기존 labels 표면형? | 기입 표면형 | 비고 |
|---|---|---|---|---|
| DeepSeek-R1-Zero | ✅ `DeepSeek-R1-Zero` (status: unreviewed) | ✅ 2503.09516 builds_on에 `DeepSeek-R1-Zero` | `DeepSeek-R1-Zero` | 일치. 별도 확인 불요 |
| ReAct | ✅ `ReAct` (approved) | ✅ 다수(2303.11366, 2310.04406 등) | `ReAct` | 일치 |
| Search-R1 | ⚠️ `SEARCH-R1` (대문자, unreviewed) | ✅ `Search-R1` (5회 사용) | `Search-R1` | **표면형 불일치**: lexicon=`SEARCH-R1`, labels=`Search-R1`. labels 관례 따라 `Search-R1`로 기입. 정본 통일 필요(대소문자) |
| DeepResearcher | ✅ `DeepResearcher` (unreviewed) | ✅ 2504.03160 title (node로 존재) | `DeepResearcher` | 일치 |
| RAG | ✅ `RAG` (approved) | ✅ 다수 | `RAG` | 일치 |
| agentic RAG | ✅ `agentic RAG` (status: pending) | ❌ (builds_on 미사용) | `agentic RAG` | lexicon에만 존재. `RAG`와 합칠지 별개 노드로 둘지 **사람 판단 대상**(아래 §2 참조) |
| Atom-Searcher | ❌ 없음 | ❌ 없음 | `Atom-Searcher` | **canon 미존재**. 단 goldset 논문 2508.12800 자체가 Atom-Searcher → lexicon 노드 추가 후보. SE-Search(2603.03293)가 이를 계승 참조 |
| 진화 루브릭 평가 (Shao 2025) | ❌ 없음 | ❌ 없음 | `진화 루브릭 평가 (Shao 2025)` | **canon 미존재 + 고유명 없음**. 잠정 기입. **사람이 표면형 확정 필요**(아래 §2 참조) |

---

## 2. 사람 후속 결정이 필요한 항목 (우선순위순)

### (a) `진화 루브릭 평가 (Shao 2025)` — 2605.10899 (RubricEM) ⚠️ 최우선
- 고유명(proper name) 없는 **인용 기반 방법**. canon 노드명으로 마땅치 않다.
- 잠정 표기로 기입했으나, 한글 서술형 + author-year가 섞여 다른 라벨 관례(영문 고유명)와 이질적.
- **결정 필요**: ① 적절한 영문 고유명/약칭으로 통일, ② arXiv id로 대체(예: Shao 2025의 실제
  arXiv id가 확인되면 그 id를 노드로), 또는 ③ 표면형 자체를 사람이 직접 부여.

### (b) `agentic RAG` vs `RAG` — 노드 통합 여부
- 2510.05691(DecEx-RAG)는 `RAG`, 2511.05385(TeaRAG)는 `agentic RAG`로 기입(원문 표기 보존, 임의
  병합 안 함).
- lexicon에 `agentic RAG`(pending)와 `RAG`(approved)가 별개로 존재. 참고로 2501.09136 title은
  "Agentic RAG Survey"(대문자 A)로 또 다른 표기.
- **결정 필요**: `agentic RAG`를 `RAG`로 흡수할지, 독립 노드로 승격할지(+대소문자 통일).

### (c) `Search-R1` 대소문자 통일
- lexicon `SEARCH-R1` vs labels `Search-R1`. 기능상 동일 노드. 정본을 어느 쪽으로 통일할지 결정.
  (이번 기입은 기존 labels 관례인 `Search-R1` 유지.)

### (d) `Atom-Searcher` lexicon 노드 추가
- 현재 lexicon 미등재. goldset 논문 2508.12800이 곧 Atom-Searcher이고, 2603.03293(SE-Search)이
  이를 builds_on으로 참조 → lexicon 정본 노드 추가가 자연스러움. 표면형 `Atom-Searcher` 권장.

---

## 3. 기입 결과 요약 (13편)

| id | title | builds_on | 비고 |
|---|---|---|---|
| 2505.03335 | Absolute Zero | `["DeepSeek-R1-Zero"]` | ⚠ 클러스터 경계 — §4 참조 |
| 2505.22648 | WebDancer | `["ReAct"]` | DAPO 제외(D1) |
| 2507.15061 | WebShaper | `[]` | 계승 named 없음 |
| 2508.12800 | Atom-Searcher | `["Search-R1", "DeepResearcher"]` | |
| 2509.13313 | ReSum | `["ReAct"]` | GRPO 제외(D1) |
| 2510.05691 | DecEx-RAG | `["Search-R1", "RAG"]` | |
| 2511.05385 | TeaRAG | `["Search-R1", "agentic RAG"]` | DPO 제외(D1) |
| 2601.06021 | Chaining the Evidence | `[]` | C-GRPO만 → 제외(D1) |
| 2601.08282 | D2Plan | `[]` | author-year 단순인용뿐 |
| 2601.21912 | ProRAG | `[]` | MCTS/PRM 부품, RAG 우산 |
| 2603.03293 | SE-Search | `["Search-R1", "Atom-Searcher"]` | |
| 2603.09203 | Evaluate-as-Action | `[]` | PCAR(GRPO) 제외(D1) |
| 2605.10899 | RubricEM | `["진화 루브릭 평가 (Shao 2025)"]` | ⚠ 표면형 미확정 §2(a) |

빈 라벨 5편(2507.15061·2601.06021·2601.08282·2601.21912·2603.09203)은 **D1(부품 제외) 적용
결과**이지 "근거 못 찾음"이 아니다. 기존 빈 라벨 관례(`[]` 명시)대로 기입 — "검토했고 비어있음"과
"아직 안 함"을 구분.

---

## 4. 보고할 특이점 (사람 keep/drop 재고용)

- **2505.03335 (Absolute Zero)**: 검색을 쓰지 않는 **코드 self-play** 논문 → 클러스터(검색 에이전트
  RL) 경계에 걸친다. 라벨은 기입했으나 사람이 keep/drop 재고 가능. (builds_on은 `DeepSeek-R1-Zero`
  하나로, zero-RLVR 패러다임 계승.)

---

## 5. canon 미수정 확인
- `data/lexicon.json` 무변경 (이 리포트는 보고만).
- 기존 50편 라벨 무변경 (`labels.json` git diff = 13편 append만, 72 insertions / 0 deletions).
- `data/outputs/` 무변경, 채점·적재 미수행.
