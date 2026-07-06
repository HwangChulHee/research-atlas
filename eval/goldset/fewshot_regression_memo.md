# few-shot 회귀 분석 메모 — 롤백 근거

> relate 프롬프트 few-shot(커밋 `1457a62`, "ColBERT/OTC/benchmark 경계 3개")이 frozen 50에 낸
> 순 퇴행(퇴행 4 : 개선 1 : 중립 4)의 원인 진단. gold 고정, ATLAS_OFFLINE 측정. 작성 2026-07-07.

## few-shot이 추가한 예시 3개 (1457a62)

- **ColBERT** "late interaction over BERT" → `["BERT"]` (베이스모델 적응 → **포함**)
- **OTC** "experiments with Qwen-2.5" 백본 → `[]` (백본 위에서 돌릴 뿐 → **제외**)
- **새 검색 벤치마크** → `[]` (새 원형, 선행 없음 → **제외**)

의도는 method_misjudged FP 억제였으나, 이 3개가 모델을 두 방향으로 밀었다.

## 퇴행 4편 — few-shot이 바꾼 것

| 논문 | old→new relations | gold | 효과(old→new TP/FP/FN) | few-shot이 유도한 패턴 |
|---|---|---|:--:|---|
| **HippoRAG 2** (2502.14802) | `[RAG,HippoRAG]`→`[HippoRAG,Personalized PageRank,RAG]` | HippoRAG, RAG | 2/0/0 → **2/1/0** | **부품 과잉포함** — 알고리즘 부품 PPR을 계보로 승격. **D1(lineage-only, 부품 제외) 직접 위반** |
| **R1-Searcher++** (2505.17005) | `[RAG]`→`[Retrieval-Augmented Generation,R1-Searcher]` | RAG | 1/0/0 → **1/1/0** | **자기계열 과잉포함** — 동일저자 선행판 R1-Searcher(self-lineage)를 FP로 추가 |
| **s3** (2505.14146) | `[RAG,Self-RAG,DeepRetrieval,Search-R1]`→`[RAG,Active RAG,Self-RAG]` | RAG, Search-R1, DeepRetrieval | 2/1/1 → **1/1/2** | **진짜 조상 탈락** — 정본 조상 Search-R1 드롭(TP→FN), 대신 gold 밖 Active RAG 추가 |
| **Rewrite-Retrieve-Read** (2305.14283) | `[RAG,retrieve-then-read]`→`[retrieve-then-read,retrieval-augmented LLMs]` | RAG | 1/0/0 → **0/0/1** | **진짜 조상 탈락** — 정본 조상 RAG 드롭(TP→FN), 대신 일반구 retrieval-augmented LLMs 추가 |

## 패턴 = 두 방향의 동시 악화

few-shot 예시가 상반된 두 힘을 유발했다:

1. **과잉포함**(ColBERT "베이스모델 적응→포함" 예시의 과일반화): 방법의 *하부 substrate*를 계보로
   끌어올림 → HippoRAG의 PPR(부품), R1-Searcher++의 self-lineage, s3의 Active RAG.
   특히 **HippoRAG의 PPR은 D1(부품 제외) 위반** — 이 태스크가 위상 신뢰도를 위해 명시적으로 배제하는
   노이즈를 few-shot이 정확히 재유입.
2. **정본 조상 탈락**(OTC "백본→제외" + "벤치마크→빈 리스트" 예시의 과일반화): 캐노니컬 RAG-계열
   조상을 "비교/백본/원형"으로 오분류해 드롭 → Rewrite의 RAG, s3의 Search-R1.

즉 HippoRAG의 부품(PPR) FP 패턴은 **고립된 사고가 아니라** 같은 few-shot이 낳은 과잉포함 계열의
대표 사례이고(R1-Searcher++·s3-ActiveRAG와 동형), 여기에 정본 조상 탈락이 겹쳐 순 퇴행이 됐다.
개선 1편(REPLUG 2301.12652, baseline이 이미 FP였던 GPT-3/Codex 제거)은 규칙 명료화의 부수효과일 뿐,
퇴행 4편의 손실을 상쇄하지 못한다.

## 결론

**few-shot은 부품/과잉 관계를 유도(하고 정본 조상을 탈락시켜) → 이 태스크에 순해(net harmful) → 기각.**
baseline(full 모델 + v2 프롬프트, few-shot 없음, P0.82/R0.83) 프롬프트로 롤백한다.
