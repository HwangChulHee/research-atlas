# 200편 골든셋 — provisional 통합 채점 (in-sample 편향 배치별 분해)

> 골든셋 211편(frozen 50 + RAG 85 + multiagent 60 + eval 16)을 **동일 롤백 파이프라인**(mini extract /
> full relate temp0 / **few-shot 없음**)으로 채점. **provisional** — multiagent·eval gold는 draft(미freeze),
> lexicon 무변경. `ATLAS_OFFLINE=1`, Neo4j 미접촉. 작성 2026-07-07. 채점 정본 `score_buildson.py`.

## 1. 배치별 P/R (핵심)

| 그룹 | n | gold∅ | micro P | micro R | TP | FP | FN | FP:방법오인 | FN:lex탈락 | FN:추출X |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **frozen 50 (in-sample)** | 50 | 11 | **0.831** | **0.817** | 49 | 10 | 11 | 8 | 1 | 10 |
| RAG 85 (out) | 85 | 41 | 0.465 | 0.741 | 40 | 46 | 14 | 44 | 5 | 9 |
| **multiagent 60 (out)** | 60 | 46 | **0.143** | **0.304** | 7 | 42 | 16 | 40 | 12 | 4 |
| eval 16 (out) | 16 | 10 | 0.200 | 0.167 | 1 | 4 | 5 | 4 | 3 | 2 |
| **전체 211** | 211 | 108 | 0.487 | 0.678 | 97 | 102 | 46 | 96 | 21 | 25 |

## 2. in-sample vs out-of-sample 격차 — 거리가 멀수록 악화

| out 배치 | ΔP(vs frozen) | ΔR(vs frozen) |
|---|--:|--:|
| RAG 85 | −0.365 | −0.076 |
| **multiagent 60** | **−0.688** | **−0.512** |
| eval 16 | −0.631 | −0.650 |

**핵심: precision 붕괴가 튜닝 분포에서 멀어질수록 단계적으로 심해진다.** frozen 0.831 → RAG 0.465 →
multiagent **0.143** → eval 0.200. RAG 배치(파이프라인 튜닝 도메인)는 P −0.37이었는데, 멀티에이전트는
**P −0.69**(0.143)로 훨씬 더 붕괴. in-sample 0.83은 극도로 낙관 편향임이 두 번째 out 배치로 재확인.

## 3. 왜 붕괴하나 — 기본값 과잉 emission (C4 배치 비교)

| batch | FP/논문 | gold∅인데 emission | empty-gold 비율 | top FP |
|---|--:|--:|--:|---|
| frozen | 0.20 | 3 | 22% | RAG·BERT·AutoGPT·ReAct |
| RAG | 0.54 | 22 | 48% | **RAG×22**·ReAct·IRCoT·MCTS |
| multiagent | **0.70** | **24** | **77%** | **RAG×12·CoT×7·GPT-4×4**·ReAct |
| eval | 0.25 | 3 | 62% | RAG×3·CoT |

**메커니즘: 파이프라인이 out-of-distribution 논문에 튜닝 분포의 지배 개념("RAG", 다음으로 CoT·GPT-4·ReAct)을
기본값으로 뱉는다.** 멀티에이전트 논문 60편 중 46편이 gold∅(계보 없음 — 프레임워크를 비교 baseline로만 인용,
A5 참조)인데 파이프라인은 그 중 24편에 RAG/CoT를 emission → 전부 FP. "파이프라인이 어디서나 RAG를 본다."
FP의 95%(multiagent 40/42, 전체 96/102)가 method_misjudged(부품/substrate 아닌 순수 오판)로 동일 성격.

## 4. recall 해석 — 멀티에이전트는 lexicon 갭이 주범 (precision 붕괴와 분리)

- multiagent FN 16 중 **12가 lexicon탈락**(gold 타깃 CAMEL·Debate·MAD·FunSearch 등이 lexicon에 없어 pred가
  status 필터로 탈락 — C1 리포트의 19개 미등록 노드). 즉 **multiagent recall 0.304는 파이프라인 미스가 아니라
  주로 lexicon 커버리지 부족**. C1의 방법노드를 unreviewed로 추가하면 recall은 오를 것(freeze와 함께 결정).
- 반면 **precision 붕괴(0.143)는 lexicon 아티팩트가 아님** — FP 42는 전부 lexicon에 있는(status 통과) RAG/CoT
  과잉 emission. lexicon을 고쳐도 precision은 안 오른다. **precision이 진짜 병목.**
- frozen/RAG는 FN이 주로 추출X(abstract-only 구조적 한계)로 lexicon 갭 작음.

## 5. 한계 · 정직한 읽기

1. **provisional**: multiagent·eval gold는 **draft(미freeze)** — 사용자 검수 전. A5(멀티에이전트 경계)·
   C1(lexicon 추가) 결정에 따라 수치가 바뀐다. 특히 multiagent recall은 lexicon 추가 시 상승 여지.
2. **eval16은 표본 작음**(n=16, TP=1) — P/R 해석 신중. 방향(precision 낮음)만 신뢰.
3. **precision 결론은 robust**: 세 out 배치 모두 method_misjudged 과잉 emission으로 P 급락, lexicon과 무관.
   in-sample 0.83을 "일반화 성능"으로 읽으면 안 됨 — out-of-sample precision은 0.14~0.47.
4. **비결정성**: full relate temp0도 run-to-run ±0.04. 작은 Δ 해석 보류, 큰 격차(ΔP −0.37~−0.69)만 신뢰.

## 6. 시사점

- **precision(과잉 emission)이 최대 병목**이고, **튜닝 분포 밖일수록 심하다** — 파이프라인이 "RAG/CoT를 기본
  계보로 투사". few-shot은 이를 악화(이미 기각). 다음 레버는 relate가 **gold∅ 논문에 빈 리스트를 내도록**
  하는 것(모드 A 억제) — 특히 멀티에이전트처럼 계보가 프레임워크-비교로만 표현되는 도메인.
- 골든셋은 이제 **네 분포(초기RAG코퍼스 / RAG-추론서베이 / 멀티에이전트 / 평가신뢰성)**를 커버 →
  in-sample 편향을 다각도로 정량화. 이 다분포 측정 자체가 확장의 성과.
- **freeze 전 사용자 결정**: (A5) 멀티에이전트 경계 3종, (C1) lexicon 19개 중 방법노드 추가 여부. 결정 후
  multiagent·eval을 freeze하고 재채점하면 확정 out-of-sample 수치가 나온다.
