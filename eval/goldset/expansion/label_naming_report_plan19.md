# 네이밍 정합 리포트 — 질의계획 19편 builds_on

작성일: 2026-06-26
대상: batch2 keep 85편 중 질의계획 클러스터 19편 (`eval/goldset/labels.json` append 완료)
누적: 학습형RL 13 + 검색시점 19 + RAG강화추론 14 + 질의계획 19 = **확장 65/85** (frozen 50 별도)
canon 기준: `data/lexicon.json`(techniques) + 기존 labels(50 + 46)의 builds_on 표면형
판정: D1(GRPO/PPO/MAPPO/IPO 등 옵티마이저 제외) + RAG 뿌리 포함

> 목적: 사람이 "정본 통일/추가 필요"·"표면형 불일치"를 한눈에. lexicon 미수정(보고만).

---

## 1. 참조 방법명별 canon 정합 표

| 방법명 | lexicon 존재? | 기존 labels 표면형? | 기입 표면형 | 비고 |
|---|---|---|---|---|
| RAG | ✅ `RAG`(approved) | ✅ 다수 | `RAG` | 교차 일치 ✓ (이 클러스터 최다 사용) |
| Search-R1 | ⚠️ `SEARCH-R1`(대문자) | ✅ `Search-R1`(앞 3클러스터·50편) | `Search-R1` | **교차 일치 ✓**. lexicon 대소문자 통일은 기존 미결 |
| IRCoT | ✅ `IRCoT`(approved) | ❌ (이번이 첫 사용) | `IRCoT` | 일치 |
| Adaptive-RAG | ❌ lexicon 없음 | ✅ **이번에 노드 생성**(2403.14403 title) | `Adaptive-RAG` | 내부 계보 — §2(a). lexicon 정본 추가 후보 |
| ZeroSearch | ❌ lexicon 없음 | ✅ `ZeroSearch`(검색시점 SSRL builds_on, 이번에 2505.04588 title로 노드화) | `ZeroSearch` | 내부 계보 — §2(b). lexicon 정본 추가 후보 |

---

## 2. 내부/교차 계보 — 표면형 일치 확인 (채점 연결)

### (a) `Adaptive-RAG` ↔ 2403.14403 (논문 자신) ✓
- 2403.14403이 Adaptive-RAG 논문 → **title을 `Adaptive-RAG`로 기입**.
- 2502.14614(ICA-RAG)의 builds_on `["Adaptive-RAG"]`가 이 노드를 가리킴.
- canon 일치 검증 완료: `adaptive rag` == `adaptive rag` ✓ (채점 시 연결됨).

### (b) `ZeroSearch` ↔ 2505.04588 (논문 자신) ↔ SSRL(검색시점 2508.10874) ✓
- 2505.04588이 ZeroSearch 논문 → **title을 `ZeroSearch`로 기입**.
- 검색시점 클러스터의 SSRL(2508.10874) builds_on `["ZeroSearch"]`가 이 노드를 가리킴(교차 클러스터).
- canon 일치 검증 완료: `zerosearch` == `zerosearch` ✓.

### (c) `Adaptive-RAG` vs `LLM-Independent Adaptive RAG`(2505.04253) — 별개 주의
- 2505.04253 title은 `LLM-Independent Adaptive RAG`(빈 라벨). "Adaptive"가 겹치나 **별개 논문/노드**.
  canon: `llm independent adaptive rag` ≠ `adaptive rag` → 자동 분리됨(혼동 없음). 참고용 표기.

---

## 3. canon 미존재 — 정본 추가 후보
- `Adaptive-RAG`, `ZeroSearch` 모두 lexicon 정본에는 없고 goldset 노드(논문 title)로만 존재.
  둘 다 다른 논문이 builds_on으로 참조하는 **참조 허브**라 lexicon 정본화 우선순위 높음.
- 나머지(IRCoT·RAG·Search-R1)는 기존 canon/labels에 있음.

---

## 4. 기입 결과 요약 (19편)

| id | title | builds_on |
|---|---|---|
| 2309.11495 | Chain-of-Verification | `[]` (line 인용, Self-Refine 미포함) |
| 2403.14403 | Adaptive-RAG | `["IRCoT"]` |
| 2405.20139 | GNN-RAG | `["RAG"]` |
| 2410.22353 | RuleRAG | `["RAG"]` (CoK=적용대상 제외) |
| 2501.15228 | Multi-Agent RL RAG | `["RAG"]` (MAPPO 제외 D1) |
| 2502.14614 | ICA-RAG | `["Adaptive-RAG"]` (내부계보→2403.14403) |
| 2504.04915 | Collab-RAG | `["RAG"]` (IPO 제외 D1계열) |
| 2504.16787 | Credible Plan-RAG | `[]` |
| 2505.04253 | LLM-Independent Adaptive RAG | `[]` |
| 2505.04588 | ZeroSearch | `["Search-R1"]` |
| 2505.15776 | ConvSearch-R1 | `[]` (GRPO 제외 D1) |
| 2506.08625 | RAISE | `[]` |
| 2508.16438 | OPERA | `[]` (GRPO 제외 D1) |
| 2508.20368 | AI-SearchPlanner | `["Search-R1", "RAG"]` |
| 2510.10095 | CardRewriter | `[]` |
| 2510.24652 | R3 | `["RAG"]` |
| 2511.12159 | CriticSearch | `["Search-R1"]` (TIR 우산 제외) |
| 2604.17555 | CoSearch | `["Search-R1", "RAG"]` (GRPO 제외 D1) |
| 2605.29307 | GrepSeek | `[]` |

빈 라벨 **8편**(독자 신설·반대 방향 신설·익명 인용군 — D1 제외 결과이지 "근거 못 찾음" 아님).

> 비고: title 충돌 방지 — 2501.15228은 명시 system명이 없어 서술형 `Multi-Agent RL RAG`로 기입
> (기존 `MARAG-R1`(2510.27569)과 다른 논문). 사람이 더 적절한 표면형 부여 가능.

---

## 5. 검증/무수정 확인
- `labels.json`: 19편 append만 (git diff = 100 insertions / 0 deletions). 기존 50 + 46 **무변경**.
- 빈 라벨 8편 명시 기입(`[]`).
- 내부/교차 계보 2건(Adaptive-RAG, ZeroSearch) canon 일치 검증 완료.
- `data/lexicon.json` · `data/outputs/` **무변경**.
- `_meta.labeled`: 직전 96 → 이번 append로 실제 **115**(50+46+19). _meta는 본 작업에서 미수정
  (앞 핸드오프 패턴). 사람이 115로 갱신 권장(누적 65/85).
