# out-of-sample 채점 리포트 — in-sample 편향 정량화

> 롤백된 파이프라인(full relate / temp0 / **few-shot 없음** / mini extract)으로 frozen 50과 batch2 85를
> **완전히 같은 config·같은 세션**으로 측정. gold 고정, `ATLAS_OFFLINE=1`, Neo4j 미접촉. 작성 2026-07-07.
> 채점 정본 = `score_buildson.py`(측정 전용). FP 분류 = `report_buildson.py` taxonomy 재사용.
> agentic RAG는 **pending 유지**(STEP6 결정 — 승격 시 +1 TP/+4 FP로 순해, 아래 §6).

---

## 1. 핵심 — in-sample vs out-of-sample 격차

| 세트 | n | micro P | micro R | macro P | macro R | ΔP(vs in) | ΔR(vs in) |
|---|--:|--:|--:|--:|--:|--:|--:|
| **frozen 50 (in-sample)** | 50 | **0.831** | **0.817** | 0.850 | 0.852 | — | — |
| **batch2 85 (out-of-sample)** | 85 | **0.465** | **0.741** | 0.470 | 0.750 | **−0.365** | −0.076 |
| batch2 80 (경계 5편 제외) | 80 | 0.481 | 0.750 | 0.493 | 0.762 | −0.349 | −0.067 |

**한 줄 결론: recall은 대체로 일반화되지만(−0.08, 노이즈의 ~2배), precision은 붕괴한다(−0.37, 노이즈의 ~9배).**
in-sample 0.83/0.82는 **precision이 크게 낙관 편향**된 수치였다. 처음 보는 논문에서 파이프라인은 진짜
조상을 놓치기보다는(**recall 유지**) **없거나 틀린 조상을 과잉 emission**한다(**precision 붕괴**).

> 노이즈 바닥: 과거 실험(`eval/reports/buildson_evidence_v3.md`)에서 run-to-run ±0.04. ΔP −0.37은 그
> 9배로 명백한 신호, ΔR −0.08은 ~2배로 실재하나 완만.

---

## 2. batch2 클러스터별 분해

| 클러스터 | n | gold∅ | micro P | micro R | TP | FP | FN | FP:방법오인 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 학습형RL | 13 | 5 | 0.412 | 0.583 | 7 | 10 | 5 | 9 |
| 검색시점 | 19 | 11 | 0.400 | 0.545 | 6 | 9 | 5 | 9 |
| RAG강화추론 | 14 | 9 | 0.455 | 0.833 | 5 | 6 | 1 | 6 |
| 질의계획 | 19 | 8 | 0.423 | 0.846 | 11 | 15 | 2 | 15 |
| 나머지 | 20 | 8 | 0.647 | 0.917 | 11 | 6 | 1 | 5 |

- **precision이 전 클러스터에서 낮다(0.40~0.65)** — 한 클러스터의 문제가 아니라 **체계적**.
- '나머지'(0.647)가 그나마 높음 — frozen 코퍼스와 가장 유사한 성격(초기 RAG·에이전트 계열)이라 추정.
- '학습형RL'·'검색시점'은 recall도 낮음(0.55~0.58) — RL·검색 논문은 조상이 본문에 명시 안 돼 추출 자체가 어려움.

---

## 3. 왜 precision이 붕괴하나 — FP taxonomy

| 세트 | FP 계 | 부품/도구 | substrate | **방법오인(method_misjudged)** |
|---|--:|--:|--:|--:|
| frozen 50 | 10 | 1 | 1 | 8 |
| batch2 85 | **46** | 2 | 0 | **44** |

FP의 **96%(44/46)가 method_misjudged** — relate가 gold에 없는 관계를 그럴듯하게 지어냄. 두 모드:

**모드 A — gold∅ 과잉 emission (구조적).** batch2 85편 중 **41편(48%)이 gold∅**(조상 없는 foundational·
RL·벤치마크 논문), frozen은 11/50(22%)뿐. 이 중 **22편이 비어있지 않은 pred를 뱉어 전부 FP**가 됐다.
예: R-Tuning→`instruction tuning`, Pangu DeepDiver→`RAG`, RAISE/EviOmni/OPERA→`RAG`. "특정 선행 기법에서
안 내려오면 빈 리스트"라는 규칙을 처음 보는 논문에선 못 지킴 — intro에 언급된 넓은 패러다임(RAG)을 조상으로 오인.

**모드 B — 오답 조상 (판단 오류).** 진짜 조상이 있는데 넓은 것을 집고 특정한 것을 놓침:

| 논문 | gold | pred(FP 굵게) | 문제 |
|---|---|---|---|
| Adaptive-RAG (2403.14403) | IRCoT | **RAG, Self-RAG** (+IRCoT 놓침) | 특정 조상(IRCoT) 대신 넓은 RAG류 |
| DRAGIN (2403.10081) | FLARE | **IRCoT, RAG** (+FLARE 놓침) | 진짜 조상 FLARE 미포착 |
| ZeroSearch (2505.04588) | SEARCH-R1 | **R1-Searcher, RAG, ReSearch** | 형제 다수 나열 |
| R3 (2510.24652) | RAG | **Contriever, DPR** (+RAG는 맞힘) | 부품/구성요소 추가 |

batch2 in frozen(FP 8 method_misjudged)에서도 같은 성향이 있었으나, out-of-sample에서 **5.5배(8→44)로 증폭**.

---

## 4. recall은 왜 버티나 — FN taxonomy

| 세트 | FN 계 | lexicon탈락 | 추출X(abstract-only 한계) |
|---|--:|--:|--:|
| frozen 50 | 11 | 1 | 10 |
| batch2 85 | 14 | 5 | 9 |

FN은 frozen(11)과 batch2(14)가 비슷 → **놓침은 out-of-sample에서 거의 안 늘었다**. 진짜 조상이 본문에
명시되면 파이프라인이 대체로 잡는다(recall 0.74 유지). recall 손실의 대부분은 **추출X**(abstract-only라 본문
related-work에 있는 조상 미도달) — 이는 few-shot·모델과 무관한 **구조적 트레이드오프**(README §2-A 문서화됨).

---

## 5. 경계 5편 (제외 부분집합의 근거)

| 논문 | gold | pred | TP/FP/FN | 성격 |
|---|---|---|--:|---|
| Absolute Zero (2505.03335) | DeepSeek-R1-Zero | ReAct | 0/1/1 | 조상 오인 + 놓침 |
| Pangu DeepDiver (2505.24332) | (∅) | RAG | 0/1/0 | gold∅ 과잉emission |
| Tool-to-Agent (2511.01854) | (∅) | RAG | 0/1/0 | gold∅ 과잉emission |
| GRPO Collapse (2512.04220) | (∅) | SEARCH-R1 | 0/1/0 | gold∅ 과잉emission |
| PTAH / Verifiable Multimodal DR (2605.29861) | RAG | RAG | 1/0/0 | clean |

경계 5편 제외 시 P 0.465→0.481, R 0.741→0.750 — **격차의 원인이 경계 케이스가 아님을 확인**(제외해도
ΔP −0.35로 거의 불변). in-sample 편향은 **소수 이상치가 아니라 체계적 precision 붕괴**다.

---

## 6. 한계 · 정직한 읽기

1. **precision 편향이 핵심 교훈**: 데모/문서의 0.83/0.82를 "일반화 성능"으로 읽으면 안 된다.
   out-of-sample precision은 **0.47**(경계 제외 0.48)이다. 지도의 계보 엣지 **절반 이상이 out-of-sample에선
   헛것일 수 있다** — 위상 신뢰도 주장 시 이 수치를 병기해야 한다.
2. **같은 라벨러·같은 루브릭**: batch2도 프로젝트 본인이 라벨링(자기 라벨). 단 batch2는 프롬프트·lexicon
   **튜닝에 한 번도 안 쓴 held-out**이라, in-sample 대비 이 격차가 곧 **튜닝 과적합의 하한 추정**이다.
   (라벨러 편향까지 없애려면 제3자 라벨이 필요 — 로드맵.)
3. **비결정성**: full relate는 temp0이라도 run-to-run ±0.04. frozen 재측정도 baseline과 ±1엣지 드리프트가
   있었다(STEP3). 클러스터별 작은 Δ는 해석 보류, 격차의 방향·크기(ΔP≈−0.36)만 신뢰.
4. **agentic RAG(STEP6) pending 유지**: 승격 시 frozen P −0.027(순손), batch2 P −0.004/R +0.019. 일반
   범주어라 4 FP를 만들어 미승격. 이 리포트 수치는 pending 기준.

---

## 7. 시사점 (다음 후보)

- **precision이 진짜 병목** — 재현율 실험(evidence·related-work)은 이미 미채택. 다음은 relate가 **gold∅ 논문에
  빈 리스트를 내도록** 하는 것(모드 A 억제)이 최대 레버. 단 few-shot은 역효과(STEP1~2 기각) 확인됨 → 다른 수단 필요.
- 모드 B(넓은 RAG류로 특정 조상 대체)는 lexicon으로 못 고침 — relate 판단/입력범위 문제.
- 측정 원칙은 지켜짐: **out-of-sample 수치를 확보했고, in-sample과의 격차를 정량화**했다. 이게 STEP7의 목표.
