# canon 반영 + 적재 — STEP 0 게이트 보고 (적재 중단)

작성일: 2026-06-26
결과: **STEP 0 컨파운드 게이트 FAIL + API 키 부재 → 적재(STEP 4) 중단, 사람 결정 대기.**
이 핸드오프의 "드리프트가 있으면 적재를 멈추고 보고" 지침대로, lexicon·labels·freeze는
**아직 손대지 않았다**(STEP 1~3 미실행). 무엇을 바꾸기 전에 결정이 필요하다.

---

## STEP 0 — config 확인 결과

| 항목 | 상태 | 판정 |
|---|---|---|
| `MODEL_EXTRACT` = gpt-5.4-mini | ✅ 일치 | OK |
| `MODEL_RELATE` = gpt-5.4 | ✅ 일치 | OK |
| relate `temperature` = 0 | ✅ (`pipeline/relate.py:15`) | OK |
| batch2 parsed 85편 | ✅ 전부 `expansion/parsed/`에 존재(85/85) | OK |
| **relate few-shot (Change B)** | ⚠️ **드리프트 확인** | **STOP** |

---

## ⚠ 드리프트 — relate few-shot이 baseline 측정 이후 들어왔다

타임라인(git):

```
2026-06-17  labels frozen (papers.json frozen_at)
2026-06-22  d498246  relate를 full(gpt-5.4)로 승격 + 그래프 재빌드
            → frozen 50 relations.json 이때 생성 (= baseline P0.82/R0.83의 예측 출처)
2026-06-25  1457a62  relate 프롬프트 few-shot 3개 추가  ← Change B
            → 프롬프트 파일 1개만 수정(+25줄). data/outputs/ 재생성 안 함.
```

근거:
- `git log -1 -- data/outputs/2503.09516.relations.json` → **d498246 (06-22)**. 즉 커밋된
  frozen-50 예측은 few-shot **이전** 산출물.
- `git show --stat 1457a62` → `prompts/pipeline/relate.py` **1개 파일만** 변경. 예측 재생성 없음.
- 06-25 이후 baseline 재측정 기록 없음(`eval/runs`·`eval/reports`에 post-06-25 baseline run 부재).

추가된 few-shot 3개(`1457a62`):
- ColBERT("late interaction over BERT") → `["BERT"]` (포함 경계)
- OTC("experiments with Qwen-2.5" 백본) → `[]` (제외 경계)
- 새 벤치마크 제시 → `[]` (빈 리스트)
→ `method_misjudged` FP를 겨냥한 **정밀도 지향 변경**.

### 왜 STOP인가
baseline(frozen 50)은 **few-shot 없이** 측정됐는데 지금 `relate.py`엔 few-shot이 있다. 이대로
batch2 85편을 돌리면 out-of-sample 결과가 **"새 논문(일반화) + Change B(프롬프트 개선)" 두 변수
혼재**가 된다. in-sample vs out-of-sample 격차를 깨끗이 못 읽는다 — 이 핸드오프 STEP 0이 막으려는
바로 그 컨파운드.

---

## ⚠ 두 번째 블로커 — OpenAI API 키 부재

- 작업 환경에 `.env` 없음, `OPENAI_API_KEY` 미설정.
- STEP 4는 85편 × (extract+relate) OpenAI 호출이 필수 → **이 환경에서 실행 불가**.
- 키가 있어도 위 드리프트가 먼저 해결돼야 결과가 유효.

---

## 결정 필요 (사람) — 드리프트 해소 방법

| 옵션 | 내용 | 비용 | 트레이드오프 |
|---|---|---|---|
| **A. few-shot 되돌리고 batch2 실행** | relate.py를 06-22 상태로(few-shot 제거) → batch2 85편 생성 → 기존 baseline과 비교 | batch2 ×(extract+relate)만 | baseline 불변·격차가 순수 "일반화"만 측정. 단 현 라이브 개선(few-shot)은 평가에서 빠짐 |
| **B. baseline 재측정(few-shot 포함) 후 batch2** | frozen 50 relations 재생성(few-shot) → 새 baseline → batch2도 few-shot으로 | (50 + 85) relate 재호출 | **현 실제 파이프라인**을 양쪽에 일관 적용(가장 대표적). 단 headline 0.82/0.83 재산출됨 |
| **C. 그대로 진행(컨파운드 수용)** | 현 config로 batch2, 기존 baseline과 비교하되 혼재 명시 | batch2만 | 가장 빠르나 격차 해석에 두 변수 섞임(권장 안 함) |

**권장**: 목표가 "현 시스템의 일반화 측정"이면 **B**(양쪽 동일 파이프라인, few-shot은 유지할 개선),
"baseline 보존 + 순수 일반화 격차"면 **A**. **C는 비권장**.

그리고 어느 쪽이든 **API 키**를 제공하거나(또는 사람이 직접 실행) 해야 STEP 4가 돈다.

---

## 아직 안 한 것 (결정 후 진행)
- STEP 1 lexicon 반영(B2 4 + Shao + agentic/Visual RAG) — **미실행**
- STEP 2 labels Shao 표면형 교체 / A 표면형 통일 — **미실행**
- STEP 3 freeze 표시 — **미실행**
- STEP 4 적재(예측 생성) — **미실행(블록)**

> STEP 1~3은 드리프트 해소와 독립이라 지금 해도 안전하지만, STEP 0이 "멈추고 보고 우선"이고
> STEP 4가 어차피 블록(키 부재)이라, 방향 확정 전 상태 변경을 보류했다. "1~3 먼저 진행" 지시 시
> 즉시 처리 가능.

## 무변경 확인
- `lexicon.json` · `labels.json` · `data/outputs/` · 라이브 Neo4j 전부 **무변경**. 본 보고서 1장만 생성.
