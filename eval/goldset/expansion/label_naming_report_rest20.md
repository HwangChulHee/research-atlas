# 네이밍 정합 리포트 — 마지막 20편 builds_on (batch2 라벨 완료)

작성일: 2026-06-26
대상: batch2 keep 85편 중 마지막 20편(지식경계 7·정보필터링 7·추론워크플로우 4·생성 1·오케스트레이션 1)
누적: 13 + 19 + 14 + 19 + 20 = **확장 85/85 완료** (frozen 50 별도 → 전체 라벨 135)
canon 기준: `data/lexicon.json`(techniques) + 기존 labels(50 + 65)의 builds_on 표면형
판정: D1(GRPO/PPO/MCTS 등 옵티마이저 제외) + RAG 뿌리 포함

> 목적: 사람이 "정본 통일/추가 필요"·"표면형 불일치"를 한눈에. lexicon 미수정(보고만).

---

## 1. 참조 방법명별 canon 정합 표

| 방법명 | lexicon 존재? | 기존 labels 표면형? | 기입 표면형 | 비고 |
|---|---|---|---|---|
| RAG | ✅ `RAG`(approved) | ✅ 다수 | `RAG` | 교차 일치 ✓ (이 묶음 최다) |
| DeepSeek-R1 | ✅ `DeepSeek-R1`(unreviewed) | ✅ 2501.12948·2503.19470·RAG강화추론 2504.03947 | `DeepSeek-R1` | **2504.03947과 동일 노드 ✓**. R1-Zero와는 분리 유지(일관) — §2(b) |
| RankGPT | ✅ `RankGPT`(approved) | ❌ (이번 첫 사용) | `RankGPT` | 일치 |
| SelfCheckGPT | ❌ lexicon 없음 | ✅ **이번에 노드 생성**(2303.08896 title) | `SelfCheckGPT` | 내부 계보 — §2(a). 정본 추가 후보 |
| Semantic Entropy | ❌ lexicon 없음 | ❌ 없음 | `Semantic Entropy` | **canon 미존재**. 잠정 기입. 정본 추가 후보(불확실성 정량화 허브) |

---

## 2. 내부/교차 계보 — 표면형 일치 확인 (채점 연결)

### (a) `SelfCheckGPT` ↔ 2303.08896 (논문 자신) ✓
- 2303.08896이 SelfCheckGPT 논문 → **title을 `SelfCheckGPT`로 기입**.
- 2311.01740(SAC3)의 builds_on `["SelfCheckGPT"]`가 이 노드를 가리킴.
- canon 일치 검증 완료(`selfcheckgpt`) → 채점 시 연결됨.

### (b) `DeepSeek-R1` 계열 — 일관성 확인 ✓
- 2503.06034(Rank-R1)의 builds_on `["DeepSeek-R1"]`은 RAG강화추론 2504.03947과 **동일 노드**
  (canon 일치 검증 완료).
- `DeepSeek-R1-Zero`(학습형RL 2505.03335·2503.09516)와는 **분리 유지** — 5클러스터 내내 일관.
  최종 R1↔R1-Zero 통합/분리는 사람 canon 통일 단계 결정 대상(아래 §4).

---

## 3. 기입 결과 요약 (20편)

| id | title | builds_on |
|---|---|---|
| 2205.14334 | Verbalized Uncertainty | `[]` |
| 2303.08896 | SelfCheckGPT | `[]` (논문 자신) |
| 2304.13734 | Internal-State Lie Detection | `[]` |
| 2307.01379 | Shifting Attention to Relevance | `["Semantic Entropy"]` |
| 2311.01740 | SAC3 | `["SelfCheckGPT"]` (내부계보→2303.08896) |
| 2311.09677 | R-Tuning | `[]` (instruction tuning 미포함, 광범위) |
| 2502.11677 | Internal-State Knowledge Boundary | `[]` (building-on 있으나 노드명 불명) |
| 2306.17563 | Pairwise Ranking Prompting | `[]` |
| 2402.12174 | BIDER | `["RAG"]` (PPO 제외) |
| 2406.11678 | TourRank | `["RankGPT"]` |
| 2406.13629 | InstructRAG | `["RAG"]` |
| 2407.02485 | RankRAG | `["RAG"]` (ChatQA-1.5 제외) |
| 2410.04739 | TableRAG | `["RAG"]` |
| 2503.06034 | Rank-R1 | `["DeepSeek-R1"]` |
| 2310.05388 | Grove | `["RAG"]` |
| 2501.02727 | Tree-RAG-Agent Recommender | `[]` |
| 2501.10053 | AirRAG | `["RAG"]` (MCTS 제외 D1) |
| 2501.14342 | Chain-of-Retrieval RAG | `["RAG"]` |
| 2507.15586 | EviOmni | `[]` (GRPO 제외 D1) |
| 2605.29861 | Verifiable Multimodal DR | `["RAG"]` ⚠ 클러스터 경계(멀티에이전트+평가) |

빈 라벨 **8편**(지식경계의 독립 수립 토대 연구 다수 — 의도된 것, "근거 못 찾음" 아님).

---

## 4. 사람 후속 (batch2 라벨 완료 → canon 통일 단계로)

5개 클러스터 리포트를 모아 일괄 정리할 항목:

- **DeepSeek-R1 vs DeepSeek-R1-Zero**: 별개 노드 유지(현재) vs 한 계열 통합 — 최종 결정.
- **정본 미존재 노드(고빈도 허브 우선)**: `SelfCheckGPT`·`Semantic Entropy`·`Adaptive-RAG`·
  `ZeroSearch`·`ReTool`·`MMSearch-R1`·`Visual RAG`·`OpenSeeker`·`Shao 2025`(author-year).
- **표면형 통일**: `Search-R1` vs lexicon `SEARCH-R1`, `Chain-of-Thought` vs lexicon `CoT`,
  `agentic RAG` vs `RAG`.
- **클러스터 경계 drop 재고**: Absolute Zero·Tool-to-Agent·GRPO Collapse·Pangu DeepDiver·
  2605.29861 등.

---

## 5. 검증/무수정 확인
- `labels.json`: 20편 append만 (git diff = 104 insertions / 0 deletions). 기존 50 + 65 **무변경**.
- 빈 라벨 8편 명시 기입(`[]`). 내부 계보 2건(SelfCheckGPT·DeepSeek-R1) canon 일치 검증 완료.
- **합계 라벨 135 = frozen 50 + batch2 85** (구조 확인 — batch2 라벨 전부 완료).
- `data/lexicon.json` · `data/outputs/` **무변경**.
- `_meta.labeled` 115→135 동반 갱신(전 핸드오프 패턴, 요청 반영). total 135 도달 = labeling 완료.
