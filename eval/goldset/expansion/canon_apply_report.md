# canon 반영 + freeze + 적재 보고 (STEP 0~4 완료, 채점 직전)

작성일: 2026-06-26
상태: **STEP 0 드리프트 → 결정(B) → STEP 1~3(canon/freeze) + STEP 4(적재, B안) 완료. 채점은 별도 게이트.**

---

## STEP 0 — config 게이트 결과 + 결정

| 항목 | 상태 |
|---|---|
| MODEL_EXTRACT=gpt-5.4-mini · MODEL_RELATE=gpt-5.4 · relate temp=0 | ✅ 일치 |
| batch2 parsed 85/85 (`expansion/parsed/`) | ✅ |
| **relate few-shot 드리프트** | ⚠️ 확인됨 → 아래 |

**드리프트**: frozen 50 baseline 예측은 06-22(`d498246`, few-shot 이전) 산출인데 `relate.py`엔
06-25(`1457a62`) few-shot 3개(ColBERT/OTC/benchmark 경계)가 있음. 그대로 batch2를 돌리면
"새 논문 + Change B" 혼재.

**사람 결정 = B (baseline 재측정 후 batch2)**: frozen 50 relations를 현 config(few-shot 포함)로
재생성해 새 baseline을 잡고, batch2도 동일 config로. 양쪽에 현 실제 파이프라인을 일관 적용.
→ STEP 4에서 frozen 50 relate 재실행 + batch2 85편 relate 둘 다 필요(아래).

---

## STEP 1 — lexicon 반영 (완료, append-only)

`data/lexicon.json`에 6개 노드 **append**(기존 엔트리 무수정, 42 insertions / 0 deletions).
전부 `status: approved` → `resolve()`/`status_of()` NODE_OK 통과 스모크 확인:

| 노드 | 구역 | first_seen | NODE_OK |
|---|---|---|---|
| MMSearch-R1 | B2 | 2512.24330 | ✅ |
| ReTool | B2 | 2505.14246 | ✅ |
| Semantic Entropy | B2 | 2307.01379 | ✅ |
| OpenSeeker | B2 | 2605.04036 | ✅ |
| evolving-rubric-eval-shao2025 | C(토큰) | 2605.10899 | ✅ |
| Visual RAG | D(분리 유지) | 2604.09508 | ✅ |

### ⚠ 미처리 1건 — agentic RAG (사람 결정 필요)
- `agentic RAG`는 lexicon에 **이미 `pending`으로 존재**. STEP 1의 "기존 엔트리 수정 금지, append만"
  (단조성) 원칙 + "없을 때만 추가" 지침에 따라 **건드리지 않았다**.
- 그러나 `pending`은 NODE_OK가 아니라 **2511.05385(TeaRAG)의 builds_on `agentic RAG`가 채점에서
  탈락**한다(D=분리 유지인데 유효 노드가 아님).
- 분리 유지 + 채점 반영하려면 사람이 `agentic RAG` status를 `pending → approved`로 승격해야 함
  (기존 엔트리 수정이라 이번 additive-only 범위 밖). 미승격 시 그 1건은 FN.

### Shao2025 arXiv id
- 확신 가능한 id 확인 못 함 → 핸드오프 지침대로 **임시 토큰 `evolving-rubric-eval-shao2025`**로 추가.
  나중 id 확인 시 lexicon 노드명 + 2605.10899 라벨 표면형 동시 교체(둘 다 canon 일치 유지).

---

## STEP 2 — labels 표면형 정리 (완료)

- 2605.10899(RubricEM) builds_on: `진화 루브릭 평가 (Shao 2025)` → `evolving-rubric-eval-shao2025`
  (STEP 1 노드와 일치). 표면형 표준화만 — **의미 불변**(같은 Shao 노드 지시).
- **A 표면형 통일(Search-R1/CoT)은 미적용**: canon이 흡수해 채점 무해하고, frozen 50 라벨까지
  건드리게 되므로 보류(핸드오프상 선택). 채점 영향 없음.
- git diff: Shao 1줄 교체 + _meta(freeze) 외 builds_on 값 변경 없음 확인.

---

## STEP 3 — freeze (완료)

`labels.json` `_meta`: `status: in_progress → labels_frozen`, `batch2_frozen_at: 2026-06-26` 추가.
labeled=total=135 고정. frozen 50 메타(papers.json frozen_at 2026-06-17)·baseline 불변.

---

## STEP 4 — 적재 (완료, B안)

`.env` 키 제공됨 → 실행. 드라이버 `scripts/gen_predictions.py`(graphdb 미호출, JSON만 생성).

| 대상 | 동작 | 결과 |
|---|---|---|
| batch2 85 | extract(mini) + relate(full, temp0), parsed `expansion/parsed/` 재사용 | concepts 85/85 · relations 85/85, **실패 0** |
| frozen 50 | relate(full, few-shot 포함) `--force` 재실행(extract 재사용) | relations 50/50 재생성, **실패 0** |

- **frozen 재측정 효과**: temp0 결정적이라 few-shot에 민감한 **9편만 relations 변경**, 41편 동일.
  → 새 baseline은 frozen 50 중 9편이 이전과 다름(few-shot 경계 보정분). headline 0.82/0.83은 채점
  게이트에서 재산출 대상.
- **호출량**: extract 85(mini) + relate 135(full=50+85). per-item try/except·timeout·retry(P0-3) 적용.
  토큰/$ 정밀 집계는 미계측(extract/relate에 토큰 로깅 없음) — 호출 수로 보고.
- **격리 확인**: extract/relate는 Neo4j 미접촉(graphdb/load·collect 미실행). 라이브 그래프 무변경.
- **산출물**: `data/outputs/{id}.{concepts,relations}.json`(score_buildson가 읽는 경로). batch2 parsed
  85편도 `data/outputs/`로 복사(기존 corpus 관례=tracked).

---

## 무변경/검증
- `data/lexicon.json` append-only(0 deletions), 추가 6노드 NODE_OK 통과.
- `labels.json` builds_on 의미 불변(Shao 표면형만), freeze 표시됨.
- **라이브 Neo4j 무변경**(extract/relate는 JSON만 생성). `data/outputs/`는 예측 생성으로 변경됨(의도).

## 다음 단계 (사람 — 별도 채점 게이트)
1. (선택) agentic RAG `pending→approved` 승격 결정(미승격 시 2511.05385 1건 FN).
2. (선택) Shao2025 arXiv id 확인 → 토큰 교체.
3. out-of-sample 채점: ① batch2 85편 전체 ② 경계 5편(Absolute Zero·Tool-to-Agent·GRPO Collapse·
   Pangu DeepDiver·PTAH) 제외 부분집합 ③ 새 baseline(frozen 50, 9편 갱신) vs batch2 P/R 격차
   = in-sample 편향 정량화. (frozen baseline은 few-shot 포함으로 재산출됐으므로 in/out 동일 파이프라인.)
