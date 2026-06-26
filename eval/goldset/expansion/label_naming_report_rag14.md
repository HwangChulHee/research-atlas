# 네이밍 정합 리포트 — RAG강화추론 14편 builds_on

작성일: 2026-06-26
대상: batch2 keep 85편 중 RAG강화추론 클러스터 14편 (`eval/goldset/labels.json` append 완료)
누적: 학습형RL 13 + 검색시점 19 + RAG강화추론 14 = **확장 46/85** (frozen 50 별도)
canon 기준: `data/lexicon.json`(techniques) + 기존 labels(50 + 13 + 19)의 builds_on 표면형
판정: D1(GRPO/PPO/DPO/GSPO/MCTS 등 옵티마이저 제외) + D2~D4

> 목적: 사람이 "정본 통일/추가 필요"·"표면형 불일치"를 한눈에. lexicon 미수정(보고만).

---

## 1. 참조 방법명별 canon 정합 표

| 방법명 | lexicon 존재? | 기존 labels 표면형? | 기입 표면형 | 비고 |
|---|---|---|---|---|
| RAG | ✅ `RAG`(approved) | ✅ 다수 | `RAG` | 교차 일치 ✓ |
| Search-R1 | ⚠️ `SEARCH-R1`(대문자) | ✅ `Search-R1`(학습형RL·검색시점·50편) | `Search-R1` | 앞 클러스터와 **교차 일치 ✓**. lexicon 대소문자 통일은 기존 미결 |
| ReAct | ✅ `ReAct`(approved) | ✅ 다수 | `ReAct` | 교차 일치 ✓ |
| DeepSeek-R1 | ✅ `DeepSeek-R1`(unreviewed) | ✅ 2501.12948 title·2503.19470 builds_on | `DeepSeek-R1` | 일치. **DeepSeek-R1-Zero와 별개 노드** — §2(a) 강조 |
| ReTool | ❌ 없음 | ❌ 없음 | `ReTool` | **canon 미존재**. 잠정 기입. 정본 추가 후보 |
| MMSearch-R1 | ❌ 없음 | ❌ 없음 | `MMSearch-R1` | **canon 미존재**. 잠정 기입. 정본 추가 후보 |

---

## 2. 사람 후속 결정이 필요한 항목

### (a) `DeepSeek-R1` ↔ `DeepSeek-R1-Zero` — 별개 vs 통합 (강조)
- 둘 다 lexicon·labels에 **별개 노드로 존재**:
  - `DeepSeek-R1` — 2501.12948(title)·2503.19470(builds_on)·이번 2504.03947(builds_on).
  - `DeepSeek-R1-Zero` — 2503.09516(builds_on)·학습형RL 2505.03335(builds_on).
- R1과 R1-Zero는 엄밀히 다른 모델(R1-Zero=순수 RL, R1=cold-start+RL)이라 **현재 분리 유지가 타당**.
- 단 사람이 정본에서 둘을 한 계열로 묶을지(부모-자식/별칭)는 판단 대상. **이번엔 표 그대로 `DeepSeek-R1`로 분리 기입.**

### (b) canon 미존재 신규 — 정본 추가 후보
- `ReTool`(2505.14246), `MMSearch-R1`(2512.24330). 둘 다 잠정 표기. lexicon 노드 추가 여부 사람 판단.
  (특히 MMSearch-R1은 멀티모달 검색-RL의 참조점이라 후속 클러스터에서 재등장 가능 → 정본화 우선순위 ↑)

---

## 3. ⚠ 사람 미확정 / 클러스터 경계 (표값 그대로 기입)

| id | title | 기입값 | 사유 |
|---|---|---|---|
| 2504.03947 | Distilled Reasoning Re-ranking | `["DeepSeek-R1"]` | 영감/확장 경계 — 번복 가능 |
| 2511.01854 | Tool-to-Agent Retrieval | `[]` | 멀티에이전트 라우팅이 본질 → RAG-추론 클러스터 경계, keep/drop 재고 후보 |
| 2512.04220 | GRPO Collapse | `[]` | RL 학습 안정화 논문 → 방법 계보 아님, 클러스터 경계, keep/drop 재고 후보 |

---

## 4. 기입 결과 요약 (14편)

| id | title | builds_on |
|---|---|---|
| 2404.12065 | RAGAR | `["RAG"]` |
| 2502.05867 | Self-Training Tool-Use | `[]` |
| 2504.03947 | Distilled Reasoning Re-ranking | `["DeepSeek-R1"]` ⚠ |
| 2505.14246 | Visual-ARFT | `["Search-R1", "ReTool"]` |
| 2508.05748 | WebWatcher | `[]` (GRPO 부품 D1) |
| 2511.01854 | Tool-to-Agent Retrieval | `[]` ⚠ |
| 2512.04220 | GRPO Collapse | `[]` ⚠ |
| 2512.24330 | SenseNova-MARS | `["MMSearch-R1"]` (GSPO 제외 D1) |
| 2601.04767 | AT2PO | `[]` |
| 2601.20439 | PEARL | `[]` (GRPO 부품 D1) |
| 2602.00994 | Reasoning–Tool Interference | `[]` (LoRA 부품) |
| 2603.01050 | MM-DeepResearch | `[]` |
| 2603.07853 | SynPlanResearch-R1 | `["ReAct"]` (RAG=precursor 제외 D4) |
| 2605.07177 | HyperEyes | `[]` |

빈 라벨 **9편**(멀티모달 신생 + GSPO/GRPO 옵티마이저 확장 D1 제외 → 계보 빈 경우. "근거 못 찾음" 아님).

---

## 5. 검증/무수정 확인
- `labels.json`: 14편 append만 (git diff = 67 insertions / 0 deletions). 기존 50 + 13 + 19 **무변경**.
- 빈 라벨 9편 명시 기입(`[]`).
- `data/lexicon.json` · `data/outputs/` **무변경**.
- `_meta`: append-only 검증 위해 **미수정**. `_meta.labeled`가 63(실제 96=50+13+19+14)로 **stale** →
  사람이 96으로 갱신 권장(누적 46/85 반영).
