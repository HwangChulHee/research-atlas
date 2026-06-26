# Canon 통일 결정 시트 — batch2 builds_on 표면형

작성일: 2026-06-26
대상: batch2 85편(survey_sourced_b2) builds_on 방법명 전수 + frozen 50 라벨·lexicon·corpus 대조
출처: 5개 정합 리포트(rl13·search19·rag14·plan19·rest20) + `labels.json` + `data/lexicon.json` + `data/outputs/normalized_v2.json`
성격: **결정 시트(권장만)**. lexicon·labels 미수정 — 실제 반영은 사람.

---

## 0. 집계 정합 (빠짐없음 확인)

- batch2 85편 = **비-빈 라벨 44편 + 빈 라벨 41편** (클러스터별 빈: rl13 5 · search19 11 · rag14 9 · plan19 8 · rest20 8 = 41 ✓).
- builds_on 참조 **54건**(= 비-빈 44편의 builds_on 리스트 길이 합; 일부 2~3개) → **distinct 방법명 23개**.
- 아래 A~D + "안전" 구역이 23개를 모두 포함(합 23).

## 0-1. 채점 매칭 원리 (왜 이 시트가 필요한가)

`score_buildson.py`는 gold·pred 둘 다 `nc.resolve()`로 **rep_key(canon + lexicon alias)** 공간에 둔 뒤 비교한다. 두 가지가 매칭을 좌우한다:

1. **canon**: `lower → 하이픈→공백 → 공백압축`. 그래서 `Search-R1`↔`SEARCH-R1`은 둘 다 `search r1`로 **자동 흡수**(casing/하이픈 차이는 채점에 무해). 단 `CoT`↔`Chain of Thought`처럼 canon이 다른 변형은 **lexicon alias**가 있어야 묶인다.
2. **status 필터(pred 한정)**: 예측 방법명은 `status_of(rep) ∈ {approved, unreviewed}`일 때만 채점에 남는다. **lexicon에 없는(=status None) 노드로 해소되면 예측이 통째로 탈락** → 맞아도 FN(`추출O·lexicon탈락`). ⇒ **B 구역(노드 미존재)이 진짜 위험**이다.

> 적재 시 자동 등록: extract_pipeline가 batch2를 적재하면 `normalize_core.register`가
> `defines` 타깃은 `unreviewed`(NODE_OK), `builds_on`만의 타깃은 `pending`(NODE_OK 아님)으로 넣는다.
> → **자기 논문이 defines하는 노드는 자동 통과, 외부 인용만 있는 노드는 자동 탈락.**

---

## 원칙 2 결과 (상단 고정) — DeepSeek-R1 vs DeepSeek-R1-Zero: **분리 유지**

| 노드 | lexicon | corpus | frozen50 | 참조 batch2 |
|---|---|---|---|---|
| `DeepSeek-R1` | ✅ unreviewed | ✅ | ✅ | 2503.06034(Rank-R1), 2504.03947(Distilled Re-ranking) |
| `DeepSeek-R1-Zero` | ✅ unreviewed | ✅ | ✅ | 2505.03335(Absolute Zero) |

둘 다 모든 출처에 별개로 존재. 엄밀히 다른 모델(R1=추론 RL 일반, R1-Zero=cold-start 없는 변종)이라 **통합 시 위상 뭉개짐**. → 현행 분리 유지(조치 불요).

---

## ✅ 안전 구역 — 조치 불요 (lexicon approved/unreviewed + canon 매칭 OK)

| 방법명 | n | lexicon status | corpus | 비고 |
|---|---:|---|---|---|
| RAG | 19 | approved | ✅ | 최다 허브, 완전 일치 |
| ReAct | 3 | approved | ✅ | |
| FLARE | 2 | approved | ✅ | |
| Self-RAG | 1 | approved | ✅ | |
| RankGPT | 1 | approved | ✅ | |
| IRCoT | 1 | approved | ❌(corpus엔 없으나 lexicon approved라 채점 안전) | |
| DeepResearcher | 1 | unreviewed | ✅ | |
| DeepSeek-R1 / -Zero | 2 / 1 | unreviewed | ✅ | 위 원칙 2 |

---

## A. 표면형 충돌 — canon/alias로 **이미 안전**, 표시 일관성만 결정

| 방법명(라벨) | 다른 표면형 | canon | 현재 매칭? | 권장 | 영향 batch2 |
|---|---|---|---|---|---|
| `Search-R1` (라벨·frozen 50편) | lexicon·corpus = `SEARCH-R1` | `search r1` (동일) | ✅ 자동 흡수 | **표시 표면형을 `Search-R1`로 통일 권장**(라벨 50+85편 다수파, corpus/lexicon 1곳만 대문자). 채점엔 무해하니 우선순위 낮음 | n=10 (ZeroSearch, Visual-ARFT, Atom-Searcher, AI-SearchPlanner, DecEx-RAG, Agentic Self-Learning, TeaRAG, CriticSearch, SE-Search, CoSearch) |
| `Chain-of-Thought` (라벨·frozen) | lexicon rep = `CoT`, alias `Chain of Thought` | `chain of thought` ≠ `cot` | ✅ **alias 경유** 해소 | alias 유지(이미 있음). 정본 대표를 `CoT`로 둘지 `Chain-of-Thought`로 둘지는 표시 취향 — 채점 무해 | 2210.03350(Self-Ask) |

> A는 "맞는데 보기 안 통일"인 경우다. 승인만 하면 됨(또는 그대로 둬도 채점 영향 없음).

---

## B. 허브 노드 미존재 — **채점 위험, lexicon 등록 판단 필요**

builds_on 타깃인데 lexicon에 없음(status None). pred로 나오면 **탈락**한다. 두 갈래:

### B1. 자기 논문이 defines(goldset 논문 자신) → 적재 시 `unreviewed` 자동 등록
적재만 하면 NODE_OK가 되어 채점에 잡힐 **가능성**이 큼. 단 **적재 후 그 논문의 defines 표면형이 gold builds_on 표면형과 canon 일치하는지 확인** 필요(불일치 시 alias 추가).

| 방법명 | = goldset 논문 | gold canon | 권장 |
|---|---|---|---|
| `Absolute Zero` | 2505.03335 (자신) | `absolute zero` | 적재 후 defines 표면형 확인. alias 후보 `Absolute-Zero` |
| `Adaptive-RAG` | 2403.14403 (자신) | `adaptive rag` | 적재 후 확인. alias 후보 `Adaptive RAG` |
| `Atom-Searcher` | 2508.12800 (자신) | `atom searcher` | 적재 후 확인 |
| `ZeroSearch` | 2505.04588 (자신) | `zerosearch` | 적재 후 확인. ⚠ 검색시점 SSRL(2508.10874)이 **교차 참조** — 표면형 어긋나면 그 계보도 끊김 |
| `SelfCheckGPT` | 2303.08896 (자신) | `selfcheckgpt` | 적재 후 확인. SAC3(2311.01740)가 참조 |

### B2. 외부 인용만 존재(goldset 논문 아님) → 적재해도 `pending` = **채점 탈락**
계보를 채점에 넣으려면 **사람이 lexicon에 노드 추가(approved/unreviewed) 필요**. 추가 안 하면 이 builds_on은 영구 FN(`lexicon탈락`).

| 방법명 | 참조 batch2 | corpus | 권장 |
|---|---|---|---|
| `MMSearch-R1` | 2512.24330(SenseNova-MARS) | ❌ | lexicon 추가 권장(멀티모달 검색-RL 허브, 후속 재등장 가능). 미추가 시 FN |
| `ReTool` | 2505.14246(Visual-ARFT) | ❌ | lexicon 추가 여부 결정. 미추가 시 FN |
| `Semantic Entropy` | 2307.01379(Shifting Attention to Relevance) | ❌ | 불확실성 정량화 허브. 추가 권장 |
| `OpenSeeker` | 2605.04036(OpenSeeker-v2) | ❌ | 전 버전(Du et al. 2026). corpus·goldset에 없음 → 노드 추가할지 or 계보 생략할지 결정 |

> B2를 추가하지 않기로 하면, 해당 builds_on은 "정답이지만 채점에서 빠지는 노드"임을 명시적으로
> 받아들이는 것(recall 상한에 영향). 결정 사항.

---

## C. author-year 노드 — 표현 결정

라벨에 **실제 들어간 것은 1건**:

| 방법명(현재 표기) | 참조 | 문제 | 옵션 |
|---|---|---|---|
| `진화 루브릭 평가 (Shao 2025)` | 2605.10899(RubricEM) | 고유명 없음, 한글 서술+author-year(다른 라벨과 이질) | ① 영문 약칭 부여 ② 원논문 arXiv id로 대체 ③ 그대로 두되 lexicon에 동일 표면형 노드 추가(채점 매칭용) |

> 참고(라벨 미포함): Mallen2023(적응검색)·Su2024/Chen2024(내부상태) 등은 검토 후 **빈 라벨**로
> 처리됨(노드명 불명/광범위). 현재 채점 대상 아님 — C 결정 범위 밖.

---

## D. 흡수 경계 — 상위 노드로 합칠지 위상 판단

| 하위 | 상위 | 참조 | 흡수 시 | 분리 시 | 권장 |
|---|---|---|---|---|---|
| `agentic RAG` | `RAG` | 2511.05385(TeaRAG) | RAG 허브에 1건 추가, "에이전트형" 구분 소멸 | agentic RAG 별 노드(현 lexicon `pending`) | **분리 유지**(위상 정보 보존). 단 단독 1건이라 흡수해도 손실 작음 — 사람 판단 |
| `Visual RAG` | `RAG` | 2604.09508(VISOR) | 멀티모달 분기 소멸 | 별 노드(canon `visual rag`, lexicon 없음) | **분리 유지** 권장. 분리 유지 시 B2처럼 lexicon 추가 필요(아니면 탈락) |

> 흡수하면 그 라벨의 builds_on을 `RAG`로 바꿔야 함(labels 수정 — 사람). 분리 유지면 D 항목은
> 사실상 B2(노드 추가 필요)와 동일 처리.

---

## 요약 — 사람 액션 체크리스트

- [ ] **A**: `Search-R1` 표시 표면형 통일 승인(또는 무시). `Chain-of-Thought` alias 유지 확인. *(채점 무해)*
- [ ] **B1**(5건): 적재 후 각 논문 defines 표면형 ↔ gold canon 일치 확인. 불일치만 alias 추가. *(특히 ZeroSearch 교차계보)*
- [ ] **B2**(4건: MMSearch-R1·ReTool·Semantic Entropy·OpenSeeker): lexicon 노드 추가 여부 결정. 미추가=해당 계보 채점 제외(recall 영향).
- [ ] **C**(1건: Shao2025): 노드 표면형 방식 결정 + lexicon 동일 표면형 등록.
- [ ] **D**(2건: agentic RAG·Visual RAG): 흡수 vs 분리. 분리 시 B2처럼 lexicon 추가.
- [ ] **원칙 2**: DeepSeek-R1/-Zero 분리 유지(조치 불요).

→ 결정 반영(별도 작업) → 클러스터 경계 drop 재고 → freeze → 적재 → out-of-sample 채점.

---

## 검증 (무수정 확인)
- 본 작업: 시트 1장만 생성. `lexicon.json` · `labels.json` · `data/outputs/` **무변경**.
- 빈도 합 54(refs) = 비-빈 44편 builds_on 합, distinct 23개 전수 분류(A2·B9·C1·D2·안전9 = 23).
