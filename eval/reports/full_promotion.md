# full 라이브 승격 — relate만 gpt-5.4(full)로, 그래프 재빌드

2026-06-22. 모델 비교 결론(full이 builds_on 정밀도 +0.20, 비용 <$1)에 따라 **라이브 relate를 full로 승격**하고 그래프를 다시 빌드했다. **승격 범위는 relate만** — extract는 검증된 구성대로 mini 유지(개념/노드 집합 불변), evidence(v3)·RW(v4)는 미채택이라 미사용.

## 구성 변경 (모델 분리)

`src/config.py` — `MODEL` 한 줄을 둘로 분리:

```python
MODEL_EXTRACT = "gpt-5.4-mini"   # extract는 mini 유지 (개념 집합 불변)
MODEL_RELATE  = "gpt-5.4"        # relate만 full 승격
```

- `src/extract.py`: `model=config.MODEL_EXTRACT`
- `src/relate.py`: `model=config.MODEL_RELATE` + **`temperature=0`** 추가(검증을 temp=0에서 했고 그래프 재현성 확보).
- 가드 통과: `grep config.MODEL\b src/` 참조는 extract.py·relate.py **둘뿐**(eval 스크립트는 별개). API에 `gpt-5.4`·`gpt-5.4-mini` 둘 다 존재 확인.

## 세팅 (새 머신)

- `uv sync` 완료(Python 3.12, 변경 없음 — 이미 동기화 상태).
- `.env` 존재(시크릿 채워짐). `.env`는 `.gitignore` 처리 확인 → 커밋 안 됨.
- Neo4j(docker `atlas-neo4j`, neo4j:5) 기동 → `get_driver().verify_connectivity()` **OK**.
- `data/outputs`: parsed 91 / concepts 91 / relations 91 전부 존재. PDF 94편. → **세팅 게이트 통과**.

## relate 재실행 (91편, full, temp=0)

- 입력: 기존 `{id}.concepts.json`·`{id}.parsed.json` 그대로(extract 재실행 없음).
- 대상: `data/outputs/*.relations.json` 존재 **91편 전부**(디렉토리 기준).
- 실행: `eval/run_relate_full.py` — ThreadPoolExecutor(8워커)로 91편 병렬 relate, 결과를 `{id}.relations.json`에 **덮어쓰기**(라이브 승격). 기존 mini relations는 `/tmp/relations_mini_backup/`에 백업(diff용).
  - *주: 핸드오프는 "서브에이전트 병렬"을 제안했으나, 91편 독립 OpenAI 호출은 스레드풀이 동일 결과를 더 안정·결정적(temp=0)으로 낸다고 판단해 스레드풀로 실행.*
- 결과: **ok=91, fail=0** (JSON 파싱 실패 0건).

## 그래프 재빌드

라이브 lexicon(버킷1) 그대로:

1. `src/normalize_v2.py` → 논문 91 + 개념 127 = 노드 218 / 엣지 209 (defines 102 · builds_on 107).
2. `src/embed_nodes_v2.py` → node_embeddings_v2.json (논문 91 + 개념 103 = 194, dim 1536, 신규 임베딩 1).
3. `graphdb/load.py` → Neo4j 적재: Paper 91, Concept 127, 관계 208. 임베딩 개념 102 · 논문 91.

## 단계 E — 승격 검증 게이트 (핵심)

goldset 50편을 **새 라이브 relations.json** 기준으로 재채점(`eval/score_buildson.py`의 `run_full` — `normalize_core`, 버킷1 lexicon, status∈NODE_OK 그대로 재사용).

> 주: `score_buildson.py`의 SMOKE 5편 기대값은 **승격 전 mini 출력**에 하드코딩돼 있어, full 승격 후엔 (개선 방향으로) 불일치하여 `--run`을 막는다. 이는 예상된 동작 — 게이트의 판단 기준은 SMOKE가 아니라 **집계 수치**이므로 동일 채점 로직(`run_full`)을 직접 호출했다. (예: SEARCH-R1 mini 기대 TP=1/FP=1/FN=1 → full 실제 TP=2/FP=0/FN=0; KG-R1 mini TP=1 → full TP=2.)

| 그룹 | n | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 전체(50) | 50 | **0.820** | **0.833** | 0.846 | 0.878 | 50 | 11 | 10 |
| new_collected | 21 | 0.897 | 0.788 | 0.922 | 0.867 | 26 | 3 | 7 |
| from_corpus | 29 | 0.750 | 0.889 | 0.792 | 0.886 | 24 | 8 | 3 |

**대조 — 검증 실험 `model_full_t0`: 전체 micro P 0.803 / R 0.817.**

→ 라이브 P 0.820 / R 0.833 으로 검증값과 **거의 동일**(미세하게 상회, temp=0 9/10 결정성 범위 내). P가 0.7 floor을 훨씬 상회. **검증한 full@0 구성을 그대로 승격했음이 확인됨 — 게이트 통과.** 저장: `eval/runs/score_buildson_20260622-171113.{json,md}`.

## mini → full 엣지 변화 (91편)

| 항목 | 값 |
|---|--:|
| builds_on 집합 변경 논문 | **69 / 91** |
| 변경 없음 | 22 / 91 |
| builds_on 엣지 총합 | mini 196 → **full 137** |

full은 더 보수적·정밀하다 — 엣지 수가 196→137로 줄고, 그 감소분이 정밀도 +0.20의 출처다. 대표 예: Attention(1706.03762) mini=[LSTM, RNN, …] → full=[](선조 나열 FP 제거), Self-Refine(2303.17651)·Toolformer(2302.04761) 등도 약한 계보 주장 정리. RAG 표기 변형(`Retrieval-Augmented Generation`→`RAG`)을 canonical로 수렴시키는 변화도 다수.

## 산출물

- `src/config.py`(모델 분리), `src/extract.py`·`src/relate.py`(호출부+temp=0)
- `data/outputs/*.relations.json` 91편 full로 교체
- `data/outputs/normalized_v2.json`, `node_embeddings_v2.json`, Neo4j 적재 완료
- `eval/run_relate_full.py`(재실행 드라이버), `eval/runs/score_buildson_20260622-171113.*`(재채점)
- 본 리포트

## 범위 밖 (안 함)

extract→full / evidence(v3) / 5.5 비교 / RW 입력 / lexicon·goldset 변경 / PDF 재fetch·재parse.
