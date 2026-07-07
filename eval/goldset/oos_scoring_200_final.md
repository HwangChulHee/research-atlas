# 200편 골든셋 — 확정 통합 채점 (A5·C1 반영 후)

> 골든셋 **211편 freeze 완료**(frozen 50 + RAG 85 + multiagent 60 + eval 16). A5 결정(§3 RAG 통일)과
> C1 lexicon(실재 명명 15노드 추가)을 반영해 재채점. **예측 재생성 없음**(동일 롤백 파이프라인: mini
> extract / full relate temp0 / few-shot 없음). `ATLAS_OFFLINE=1`, Neo4j 미접촉. 작성 2026-07-07.
> 이 문서가 확정본 — provisional은 `oos_scoring_200.md`.

> ✅ **최종 확정 (no pending decisions, 2026-07-07)**: 모든 사용자 결정 종료 — A5(§1~§5 반영·확정),
> C1 lexicon(15 추가 / 2 제외 / **LLM-as-a-judge 1 제외 확정**). **골든셋 211편 최종 확정.**
> 아래 수치가 **최종 out-of-sample 수치**다: frozen **0.831/0.817** · RAG **0.465/0.741** ·
> multiagent **0.262/0.762** · eval **0.429/0.500**. (LLM-as-a-judge 제외로 이 수치 그대로 확정.)

## 1. 배치별 P/R (확정)

| 그룹 | n | gold∅ | micro P | micro R | TP | FP | FN | FP:방법오인 | FN:lex | FN:추출X |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **frozen 50 (in-sample)** | 50 | 11 | **0.831** | **0.817** | 49 | 10 | 11 | 8 | 1 | 10 |
| RAG 85 (out) | 85 | 41 | 0.465 | 0.741 | 40 | 46 | 14 | 44 | 5 | 9 |
| **multiagent 60 (out)** | 60 | 48 | **0.262** | **0.762** | 16 | 45 | 5 | 43 | 1 | 4 |
| eval 16 (out) | 16 | 10 | 0.429 | 0.500 | 3 | 4 | 3 | 4 | 1 | 2 |
| **전체 211** | 211 | 110 | 0.507 | 0.766 | 108 | 105 | 33 | 99 | 8 | 25 |

## 2. provisional → 확정 변화 (A5·C1 효과)

| 그룹 | provisional P/R | 확정 P/R | ΔP | ΔR | 원인 |
|---|---|---|--:|--:|---|
| frozen 50 | 0.831 / 0.817 | 0.831 / 0.817 | 0 | 0 | **완전 무변** — baseline 보존 확인 |
| RAG 85 | 0.465 / 0.741 | 0.465 / 0.741 | 0 | 0 | **완전 무변** — C1은 신규배치 노드만 |
| **multiagent 60** | 0.143 / 0.304 | **0.262 / 0.762** | +0.119 | **+0.458** | C1 노드로 FN:lex 12→1(recall 폭등) |
| eval 16 | 0.200 / 0.167 | 0.429 / 0.500 | +0.229 | +0.333 | C1 노드로 FN:lex 3→1 |

**frozen·RAG 무변 = 제약(baseline 불변) 준수의 증거.** 신규 배치만 C1 lexicon으로 recall 회복.

## 3. 검증된 두 예측 (provisional 리포트 §4가 예측 → 여기서 확인)

**예측 A: "multiagent recall은 파이프라인 미스가 아니라 lexicon 갭이 주범 → C1 추가 시 오른다."** ✅ **확인.**
- multiagent recall 0.304 → **0.762** (frozen 0.817에 근접, ΔR −0.512 → **−0.055**). FN:lex 12→1.
- 즉 **recall은 도메인 lexicon만 갖춰지면 잘 일반화한다.** 진짜 조상이 본문에 있으면 파이프라인이 잡는다.

**예측 B: "precision 붕괴는 lexicon 아티팩트가 아니다 → lexicon 고쳐도 precision 안 오른다."** ✅ **대체로 확인.**
- multiagent P는 0.143→0.262로 **소폭 상승**했으나, 이는 파이프라인이 옳게 뽑은 유효노드가 FN→TP로
  전환된 **recall-해제의 부수효과**(분자 TP↑)이지 과잉 emission이 줄어서가 아니다.
- **FP(과잉 emission) 개수는 42→45로 오히려 늘었다**(§3로 empty-gold 2편 증가). 최종 top-FP도 여전히
  **RAG×14·CoT×7·GPT-4×4·ReAct×3·PPO×2** — C1 전과 동일한 과잉 emission.
- 결론: **precision 천장은 과잉 emission이 결정하고, lexicon으로 안 내려간다. precision이 진짜 병목.**

## 4. in-sample 편향 (확정)

| out 배치 | ΔP(vs frozen) | ΔR(vs frozen) |
|---|--:|--:|
| RAG 85 | −0.365 | −0.076 |
| **multiagent 60** | **−0.568** | **−0.055** |
| eval 16 | −0.402 | −0.317 |

**핵심 그림(확정)**: **recall은 out-of-sample에서도 유지되나(lexicon 갖추면 ΔR −0.05~−0.32), precision은
붕괴한다(ΔP −0.37~−0.57).** in-sample 0.83/0.82를 "일반화 성능"으로 읽으면 안 됨 — 확정 out-of-sample은
**P 0.26~0.47 / R 0.50~0.76**. 편향의 정체는 **precision(과잉 emission)**이고, recall이 아니다.

## 5. precision 병목의 메커니즘 (C4 확정)

파이프라인이 out-of-distribution 논문에 **튜닝 분포의 지배 개념(RAG·CoT·GPT-4·ReAct)을 기본 계보로 투사**한다.
멀티에이전트 논문 60편 중 48편이 gold∅(계보가 프레임워크-비교로만 표현 — A5)인데, 파이프라인은 그 상당수에
RAG/CoT를 emission → FP. FP의 94%(multiagent 43/45, 전체 99/105)가 method_misjudged. **few-shot은 이를
악화(기각됨), lexicon은 recall만 회복.** precision을 고치려면 relate가 **gold∅ 논문에 빈 리스트를 내도록**
하는 별도 개입이 필요.

## 6. 한계

1. **out-of-sample gold도 자기 라벨**(프로젝트 본인, D1~D4). held-out(제3자 라벨)은 로드맵. 단 튜닝에 안 쓴
   세트라 in-sample 대비 격차는 과적합 하한 추정으로 유효.
2. **eval16 표본 작음**(n=16). 방향만 신뢰.
3. **LLM-as-a-judge 제외 확정**(사용자 결정 2026-07-07): 명명 명확성 50/50이라 "명확한 named 방법" 기준
   미달 → 제외(TIR·self-reflection·GNN 제외와 일관, metric gaming 회피). 이 수치가 최종(더 이상 pending 없음).
4. **비결정성**: full relate temp0도 run-to-run ±0.04. 큰 격차(ΔP −0.37~−0.57)만 신뢰.

## 7. 확정 결론

- 골든셋이 **네 분포(초기RAG코퍼스 / RAG-추론 / 멀티에이전트 / 평가신뢰성) 211편**으로 확장·freeze됨.
- **recall은 일반화된다(lexicon 커버리지 조건부). precision은 튜닝 분포 밖에서 붕괴하고 lexicon으로 안 고쳐진다.**
- 다음 레버는 명확: **relate의 과잉 emission 억제(gold∅→빈 리스트)** — few-shot 아닌 다른 수단.
