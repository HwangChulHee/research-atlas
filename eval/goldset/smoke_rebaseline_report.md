# SMOKE 핀 재기준선 리포트 — 채점 게이트 진입 전

> 목적: `score_buildson.py`의 SMOKE 기대값이 stale해진 원인을 규명하고, **개선/중립만** 갱신,
> **퇴행은 미갱신 + 보고**. 무비판 박제로 퇴행을 정답으로 굳히는 것을 막는다.
> 작업일 2026-07-07 · 채점 로직·labels·lexicon·예측·parsed 무변경 · API/Neo4j 불필요(`ATLAS_OFFLINE=1`).

---

## 요약 (먼저)

- **핀 5개 중 4개가 stale.** DeepSeek-R1만 그대로 PASS.
- **원인 귀인이 핸드오프와 다르다(중요).** 핸드오프는 "9편 재측정 + lexicon 6노드"를 원인으로 봤으나,
  **핀 관점에선** 다음이 실측이다:
  - **SEARCH-R1 · Toolformer · KG-R1** → 최근 few-shot 재측정(53f1ca5)이 아니라 **06-22 full 모델
    승격(d498246)** 때 이미 stale. 핀은 그날 **아침(0c3d915, 02:24) mini 출력**으로 박혔고, 같은 날
    **저녁(17:13) full 승격**이 relations를 바꿔 15시간 만에 stale해졌다. 셋 다 gold 기준 **개선**.
  - **HippoRAG 2** → **최근 few-shot 재측정(53f1ca5)이 PASS→FAIL로 만든 유일한 핀. 퇴행.**
  - **lexicon 6노드 추가**({MMSearch-R1, ReTool, Semantic Entropy, OpenSeeker,
    evolving-rubric-eval-shao2025, Visual RAG})는 **어느 핀에도 영향 없음** — 이 6개 중 5핀의
    pred/gold에 걸리는 항목이 없다.
- **갱신**: 개선 3편(SEARCH-R1·Toolformer·KG-R1) 핀을 현재값으로 교체.
- **미갱신(강조)**: HippoRAG 2 퇴행 → 핀 유지 → **스모크는 이 핀에서 의도적으로 FAIL**. 사람이
  few-shot 드리프트를 조사·결정할 때까지 덮지 않는다.
- **더 큰 신호(게이트 전 필독)**: 재측정된 frozen 50 중 **9편이 바뀌었고, 그 자체로 퇴행 4 : 개선 1 :
  중립 4**. 핀에 안 걸리는 퇴행 3편(Rewrite-Retrieve-Read, s3, R1-Searcher++)이 **실제 채점 게이트의
  P/R를 깎는다**. few-shot(B안) 재측정이 frozen 50에 **순(net) 퇴행**을 냈다 — STEP0의 "relate
  few-shot 드리프트" 우려가 데이터로 확인됨. §2-B 참조.

---

## STEP 1 — 스모크 핀 현황 (하드코딩 기대값 vs 현재 실측)

핀 설정 커밋: `0c3d915` (2026-06-22 **02:24**, mini 모델 출력 기준).
그 뒤 시점표: `d498246`(06-22 **17:13**, relate full 승격·전체 재추출) → `53f1ca5`(06-26, few-shot 재측정).

| 핀 | 하드코딩 기대 | 현재 실측 | 불일치 | stale 시점 | 원인 |
|---|---|---|---|:--:|---|
| SEARCH-R1 (2503.09516) | TP1 FP1 FN1 · P.5 R.5 | **TP2 FP0 FN0 · P1 R1** | O | d498246 | relations `DeepSeek-R1`→`DeepSeek-R1 Zero` (full 모델) |
| DeepSeek-R1 (2501.12948) | TP1 FP0 FN1 · P1 R.5 | TP1 FP0 FN1 · P1 R.5 | — | — | (일치) |
| Toolformer (2302.04761) | TP0 FP1 FN0 · P0 R∅ | **TP0 FP0 FN0 · P0 R∅** | O | d498246 | relations `[GPT-3,GPT-J]`→`[]` (full 모델이 baseline/부품 제거) |
| HippoRAG 2 (2502.14802) | TP2 FP0 FN0 · P1 R1 | **TP2 FP1 FN0 · P.667 R1** | O | **53f1ca5** | few-shot 재측정이 부품 `Personalized PageRank`를 FP로 추가 |
| KG-R1 (2509.26383) | TP1 FP0 FN4 · P1 R.2 | **TP2 FP0 FN3 · P1 R.4** | O | d498246 | relations `Retrieval-Augmented Generation`→`RAG`(gold의 `RAG` 명중) |

검증(53f1ca5^ 워크트리 재구성): **최근 재측정 직전** 상태에서 이미 SEARCH-R1·Toolformer·KG-R1 =
FAIL, HippoRAG 2 = **PASS**. → 3핀은 재측정 이전(d498246)에 stale, HippoRAG만 재측정이 깨뜨림.

---

## STEP 2 — 개선 / 퇴행 판정

판정 기준(gold 객관): **개선** = TP↑ ∨ FP↓ ∨ FN↓ (역방향 없음) · **퇴행** = TP↓ ∨ FP↑ ∨ FN↑ (순방향
없음) · **중립** = TP/FP/FN 3튜플 무변. 예측/정답 모두 `nc.resolve()`로 rep_key화, 예측만 status 필터.

### 2-A. SMOKE 핀 5편 판정

| 핀 | old TP/FP/FN | new TP/FP/FN | 판정 | 근거 |
|---|:--:|:--:|:--:|---|
| SEARCH-R1 | 1/1/1 | **2/0/0** | **개선** | pred가 gold(`rag`,`deepseek r1 zero`)와 정확 일치. FP·FN 소거 |
| DeepSeek-R1 | 1/0/1 | 1/0/1 | 중립 | 새로 뽑힌 `GRPO`는 부품→status 필터로 탈락, 점수 무변 |
| Toolformer | 0/1/0 | **0/0/0** | **개선** | gold=∅인데 있던 헛것 FP(`gpt 3`) 제거 |
| HippoRAG 2 | 2/0/0 | **2/1/0** | **퇴행** | gold(`hipporag`,`rag`)는 그대로 맞히나 부품 `personalized pagerank`를 FP로 추가 |
| KG-R1 | 1/0/4 | **2/0/3** | **개선** | gold에 실재하는 `rag`를 이제 명중(표면형 `RAG`로 교정). 헛것 아님 |

> KG-R1 확인(핸드오프 요구): TP 1→2는 **"gold에 실제로 있는 `RAG`를 이제 맞혀서 2"**(개선)이지,
> gold에 없는 걸 잘못 뽑은 게 아니다. gold = [kg rag, rag, reknos, rog, tog].

### 2-B. 재측정된 frozen 50 전체 9편 판정 (핀 밖 포함 — 게이트 영향)

`53f1ca5`에서 relations가 수정된(Modified) frozen 50 논문은 정확히 9편. old(53f1ca5^) vs new 채점:

| 논문 | old→new relations (요지) | gold | old→new TP/FP/FN | 판정 |
|---|---|---|:--:|:--:|
| 2004.04906 DPR | `[BERT,dual-encoder]`→`[BERT]` | BERT, ORQA | 1/0/1 → 1/0/1 | 중립 |
| 2205.10625 Least-to-Most | 대소문자만 (`CoT`,`Few-Shot`) | CoT | 1/0/0 → 1/0/0 | 중립 |
| 2301.12652 REPLUG | `[GPT-3,Codex]`→`[]` | (∅) | 0/1/0 → **0/0/0** | **개선** |
| 2305.14283 Rewrite-Retrieve-Read | `[RAG,retrieve-then-read]`→`[retrieve-then-read,retrieval-augmented LLMs]` | RAG | 1/0/0 → **0/0/1** | **퇴행** |
| 2407.11005 RAGBench | `RAG` 표면형 정규화 | (∅) | 0/3/0 → 0/3/0 | 중립 |
| 2501.12948 DeepSeek-R1 | `+GRPO`(부품) | CoT, DeepSeek-V3-Base | 1/0/1 → 1/0/1 | 중립 |
| 2502.14802 HippoRAG 2 | `+Personalized PageRank`(부품) | HippoRAG, RAG | 2/0/0 → **2/1/0** | **퇴행** |
| 2505.14146 s3 | `-Search-R1 -DeepRetrieval +Active RAG` | RAG, Search-R1, DeepRetrieval | 2/1/1 → **1/1/2** | **퇴행** |
| 2505.17005 R1-Searcher++ | `+R1-Searcher`(자기 계열) | RAG | 1/0/0 → **1/1/0** | **퇴행** |

**합계: 개선 1 · 중립 4 · 퇴행 4.** 퇴행 4편의 공통 패턴 = few-shot이 (a) 부품을 계보로
끌어올리거나(PPR, R1-Searcher), (b) 진짜 조상을 떨어뜨림(s3의 Search-R1, Rewrite의 RAG). 이는
lineage-only 규칙이 명시적으로 배제하려는 노이즈이며, STEP0 게이트의 "relate few-shot 드리프트"와 일치.

핀에 안 걸리는 퇴행 3편(**2305.14283, 2505.14146, 2505.17005**)은 스모크는 통과시켜도 **실채점
P/R를 직접 깎는다** — 채점 게이트에서 반드시 반영/조사 대상.

---

## STEP 3 — 스모크 갱신 내역 (조건부)

**갱신(개선분, 3핀)** — `score_buildson.py` SMOKE dict:

| 핀 | 변경 |
|---|---|
| SEARCH-R1 (2503.09516) | `TP1 FP1 FN1 P0.5 R0.5` → `TP2 FP0 FN0 P1.0 R1.0` |
| Toolformer (2302.04761) | `TP0 FP1 FN0 P0.0 R None` → `TP0 FP0 FN0 P0.0 R None` |
| KG-R1 (2509.26383) | `TP1 FP0 FN4 P1.0 R0.2` → `TP2 FP0 FN3 P1.0 R0.4` |

**미갱신(퇴행, 강조)**:

- **HippoRAG 2 (2502.14802)** — `TP2 FP0 FN0 P1.0 R1.0` **유지**(현재 실측 `TP2 FP1 FN0`과 불일치).
  few-shot이 부품 Personalized PageRank를 계보로 뽑은 **퇴행**이라 박제하지 않음. 코드에 사유 주석 명시.

**갱신 후 스모크 재실행 결과**: **4/5 PASS**, HippoRAG 2만 **의도적 FAIL**(전체 결과는 FAIL로 표시됨).
개선 3핀은 통과, DeepSeek-R1은 원래 통과. → 퇴행 미박제 원칙을 지키면 스모크는 HippoRAG 핀에서
빨간불을 유지하는 게 정상. 사람이 few-shot 드리프트를 결정하기 전까지 초록불로 덮지 않는다.

```
[PASS] SEARCH-R1  TP=2 FP=0 FN=0  P=1.000 R=1.000
[PASS] DeepSeek-R1 TP=1 FP=0 FN=1  P=1.000 R=0.500
[PASS] Toolformer  TP=0 FP=0 FN=0  P=0.000 R=—(gold∅)
[FAIL] HippoRAG 2  TP=2 FP=1 FN=0  P=0.667 R=1.000   ← 퇴행, 의도적 미갱신
[PASS] KG-R1      TP=2 FP=0 FN=3  P=1.000 R=0.400
스모크 결과: FAIL ❌ (HippoRAG 1핀)
```

---

## 사람 결정 대기 (채점 게이트 전)

1. **few-shot 드리프트 판단**: frozen 50 재측정이 순 퇴행(4:1:4)을 냈다. HippoRAG 2 외에도
   2305.14283 / 2505.14146 / 2505.17005이 gold에서 멀어졌다. B안(few-shot 재측정)을 그대로 채점에
   쓸지, few-shot을 빼고 재측정할지, 개별 논문을 손볼지 결정 필요.
2. **HippoRAG 핀**: (a) few-shot 롤백/수정으로 FP를 없애 원래 핀 복원 / (b) 퇴행을 수용하고 핀을
   `TP2 FP1 FN0`으로 갱신(비권장 — 부품 오염 박제). 현재는 (a)를 열어둔 채 미갱신.
3. 위 결정 후에야 out-of-sample 채점(batch2 85 · 경계 5편 제외 · new baseline 50 vs batch2 P/R
   격차)로 진행.

---

## 검증 체크리스트

- [x] 9편 판정표 — 퇴행 4건 명시, 전부 미갱신(그중 핀=HippoRAG만 스모크에 노출)
- [x] `score_buildson.py` diff = SMOKE 기대값(+주석)만 변경, 채점 로직 무변경(@@ 130 부근 8줄)
- [x] 스모크 재실행 = 개선 3핀 PASS, 퇴행 1핀 의도적 FAIL
- [x] labels.json · lexicon.json · 예측 relations · parsed 무변경 (git status로 확인)
