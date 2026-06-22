# WORKLOG

세션 인계용 개선 로그. 최신이 위.

## 2026-06-19 — builds_on을 lineage-only로 전환 + relate 입력 필드 축소

`builds_on`이 "계보(extends/improves) + 점수비교 baseline"을 한 통에 섞어 추출하던 것을 **lineage-only**(방법적 후예만)로 전환. 동시에 relate 입력에서 `problem`/`domain`을 빼고 `defines`+본문만 남김. **채점(scoring) 0회인 "평가 쌓기 전" 창에서 lockstep으로** 진행 — relate 프롬프트·골든셋 정답지·코퍼스를 같은 정의로 맞춤.

- **동기**: (1) baseline 포함은 미검토 디폴트였고 제품(위상 지도)에서 GPT-4 류 거대 허브 노이즈를 만듦. (2) `problem`/`domain`은 extract 파생물이라 단계 오류 전파 + `problem` 텍스트가 본문 근거 없이 builds_on을 끌어내는 간섭(single-prompt 안티패턴). `defines`는 self-reference 배제 기능이 명확해 유지. domain/problem은 extract가 계속 뽑아 노드 속성으로 쓰임(데이터 손실 없음) — relate가 *소비*만 멈춤.
- **변경**: `prompts/pipeline/relate.py` RELATE_SYSTEM=lineage-only(점수비교 baseline·부품(PPO/GRPO/MCTS)·데이터셋·툴·self-defined 제외, "Comparison alone is NOT builds_on"), RELATE_USER=defines-only. `src/relate.py: relate_one()` 호출부에서 domain/problem 인자 제거(`agent_collect.py`도 이 단일 경로 경유 — 추가 수정 불필요).
- **⚠️ 두 변경 동시 반영 → 결과 변화 귀인 분리 불가**(의식적 선택). baseline 제외와 필드 축소가 한 재추출에 묶임.
- **⚠️ 발견(핸드오프 가정과 불일치)**: `src/relate.py --run --force`는 `config.PAPER_IDS`(=FULL_IDS 54편)만 순회 → 에이전트 수집 37편(라벨된 골든셋 7편 + RARE 포함)이 **재추출 안 됨**. 일회용 드라이버로 나머지 37편을 `relate.relate_one`(프롬프트 단일 출처) 경유 재추출해 91편 전부 새 프롬프트로 정합화.
- **코퍼스 before/after**(git HEAD↔작업트리): relations.json 변경 68편. raw builds_on 항목 190→196(↑6 — 새 프롬프트가 generic phrase "large language models"·"question answering" 등을 더 뱉음, 단 lexicon NODE_OK가 걸러냄). 정규화 그래프(normalize_v2): 개념 157→134, builds_on 엣지 153→133(**−20**), placeholder 56→33, defines 101 불변. GPT-4·BM25·PaLM·BLOOM·OPT 등 baseline이 의도대로 빠짐.
- **골든셋 재판정(§4)**: 4-A 자율 적용 — 2505.17005 [RAG,MCTS]→[RAG], 2504.03160에서 CoT·Search-o1 drop, 2503.19470에서 Iter-RetGen·IRCoT drop. labels.json `_meta.rubric`을 lineage-only로 재작성, `labeled`=7 유지. **4-B 경계 4건(CoT/o1/QwQ/DeepSeek-R1)은 사용자 확정 대기** — 라벨 본문은 미변경 보존.
- **워크시트(eval/goldset/translations 50편)**: 상단 "라벨링 규칙" 헤더 블록을 lineage-only로 byte-안전 교체(250/250 blockquote 라인만, 본문 0변경, Voyager CRLF 보존). 라벨 7편 본문 동기화는 4-B 확정 후.
- **렉시콘 감사(§8, 삭제 0)**: 재추출로 무참조가 된 항목 38건 리포트 — approved 29(GPT-4·BM25·PaLM·RAPTOR·REPLUG 등), pending 9(R1-Searcher·RoG·ToG·DRAGIN 등). approved/rejected HITL 결정 무변경 확인, normalize_v2가 새 pending 48건 추가(머신 장부, 노드 아님). R1-Searcher/RAPTOR/RoG/ToG 등은 골든셋이 기대하는데 파이프라인이 놓친 recall 손실 → eval이 잡을 항목.
- **소비 코드 점검(§3⑥)**: normalize_core·graphdb·api·web·command 전부 `builds_on`을 구조적 엣지명으로만 소비(baseline-vs-lineage 의미 하드코딩 없음). `focus_lineage`/`lineageSets`·온톨로지 `a3_infer_lineage`는 오히려 의미가 더 정확해짐 — **코드 수정 불필요**.
- **⚠️ 미완(환경 블로커)**: Neo4j 미기동(WSL에 docker 없음) → `graphdb/load.py` 적재 + `graphdb/verify.py` 오라클(불변식 1) **미실행**. 새 `normalized_v2.json`(재빌드 오라클)은 생성됨 — Neo4j 기동 후 `/api/rebuild`(normalize→load→verify) 또는 load+verify 수동 실행 필요.
- **문서**: README·prompts/README·prompts/__init__·docs/ontology/README에 lineage-only 반영.

## 2026-06-17 — 라이브/오프라인 모드 스위치 (증분 쓰기 호환성 마감)

증분 쓰기 전환(e9f3059) 후 뒤처진 **보조 읽기 3곳 + eval 격리 1곳**을 단일 모드 스위치로 정리. 공통 뿌리: 이들이 아직 `normalized_v2.json`(이제 재빌드 전용 중간산물, 증분 때 갱신 안 됨)을 읽음.

**모드** `ATLAS_OFFLINE` 환경변수: `=1`(오프라인·eval 전용 — 수집이 write_paper 스킵 + 보조읽기 JSON 직독 → Neo4j 완전 격리) / 미설정(라이브·기본 — 보조읽기 Neo4j 직독 실시간). 충돌 안 나는 이유: eval diff는 이미 JSON 기반(`load_view`)이라 eval 세계 전체가 JSON.

**T1 `graphdb/read.py`(신규)**: write.py 대칭. `is_offline()`·`owned_paper_ids()`·`concept_names()`·`node_meta()`. 라이브는 Neo4j 직독, 오프라인은 normalized_v2.json. `node_meta` 라이브는 v2 노드 스키마와 같은 키('concept:rk'/'paper:id')로 직접 질의(개념주도 graph_view 아님), `_concept_line`(canonical/definition/**def_status**)·`_paper_line`(title/problem) 필드 충족. **라이브 Neo4j 다운 시 조용한 JSON 폴백 없음** — 명시적 실패(staleness 재유입 방지).

**T2 배선**: agent_collect `load_owned_ids`→`owned_paper_ids()`, `load_embeddings`의 norm→`node_meta()`(벡터는 캐시 그대로), `extract_pipeline`의 write_paper를 `is_offline()` 가드(오프라인=미반영 메시지). agent_filter `load_node_names`→`concept_names()`. eval/test_collect 최상단 `os.environ.setdefault("ATLAS_OFFLINE","1")`(agent_collect import 전). 죽은 상수 `NORMALIZED_V2` 제거.

**검증(스모크)**:
- **S1(격리, 핵심)**: 오프라인서 extract_pipeline → write_paper 0회 호출·Neo4j 70→70 불변; 라이브선 1회·71. (full eval 대신 write 게이트를 결정적으로 증명 — 비용/비결정성 회피.)
- **S2(라이브 실시간)**: Neo4j에 임시노드 직삽입 → owned/names/node_meta 즉시 반영, 삭제 후 사라짐(진짜 라이브).
- **S3(다운 시 의도된 실패)**: 라이브+Neo4j down → `ServiceUnavailable`(폴백 없음); 오프라인은 같은 bad URI여도 JSON 70편 정상.
- verify+audit exit0, lexicon/normalized 골든 byte-동일, 데이터 잔여변경 0.

**미적용(범위 밖 명시)**: eval B층 Neo4j 읽기 전환(격리 위해 JSON diff 유지가 오히려 맞음), 0.4 순서의존, 벡터 ANN. normalize_core·write.py·load.py·graph_neo4j 미수정.
## 2026-06-17 — Neo4j 증분 쓰기 전환 (라이브 경로 + 재빌드 오라클)

핸드오프 T0~T6 전부 구현·검증. 목표: 쓰기(수집/사전편집)가 일어나면 그 자리에서 Neo4j에 증분 반영. **불변식: 라이브 Neo4j == 같은 원자료·사전으로 배치 재빌드한 Neo4j** — 모든 작업의 합격선. 증분 경로와 배치 경로가 **같은 함수**(`normalize_core.normalize_paper`)를 쓰게 해 영영 갈라지지 않게 함.

**T1 공유 함수** `src/normalize_core.py`(신규): per-paper normalize 로직을 중립 형태(`{paper_node, concept_nodes, edges, new_lexicon_entries}`)로 추출. `normalize_v2.py`는 이걸 glob 순회 호출하게 리팩터 → `normalized_v2.json`·lexicon **byte-동일**(골든 diff 통과, 삽입순서까지). 0.4 규칙(canon, NODE_OK, 최초정의승, ok↛placeholder, home=첫 defines, 순서의존 pending) 글자대로 복제. CE1/CE2/CE3 카운터예제 직접 확인.

**T2 임베딩 적재** `graphdb/load.py`: `node_embeddings_v2.json`(접두사 키)을 노드 id로 조인해 `c.embedding`/`p.embedding` SET. 확인: 개념 76·논문 70 임베딩, transformer dim 1536, verify 무회귀.

**T3 수집 증분쓰기** `graphdb/write.py`(신규) `write_paper`: normalize_core→lexicon 저장→임베딩(tx 밖 OpenAI)→Neo4j MERGE. 최초정의승은 `_CONCEPT_MERGE`의 ON CREATE/ON MATCH CASE로 구현(정의 갱신을 SET 맨 뒤에 둬 CASE가 *옛* 값 읽게). `agent_collect.extract_pipeline`에 배선(추출 직후 반영, 실패해도 추출은 성공·rebuild 복구). gnode_report·CLI 안내문구에서 "수동 normalize_v2 실행" 제거. **검증: 전체 70편 도착순 replay → verify 통과(증분==재빌드)**, 단일 embed=True 스모크로 임베딩 SET 확인.

**T4 사전편집 증분쓰기** `write.py`에 `reject_concept`(DETACH DELETE)·`merge_concept`(엣지 재연결+닻 이동+최초정의승 승계+src 삭제)·`update_definition`(SET 정의+재임베딩+캐시). `api/main.py` patch/merge 핸들러 배선. 각 조작 후 rebuild+verify 통과(reject 124, merge 123).

**T5 rebuild=재빌드+적재+검증** `api/main.py` `/api/rebuild`: normalize_v2→load→verify→graph_view_neo4j 카운트. **`load.py`에 `wipe()` 추가** — 핸드오프는 "load.py가 덮어쓴다"고 가정했으나 실제론 MERGE만이라 드리프트(고아 엣지)를 안 지웠음. 이제 wipe+load로 진짜 전체 덮어쓰기. 스모크: 가짜 노드 심기→rebuild→사라짐, 카운트 Neo4j 기준.

**T6 감사** `verify.py --audit`: lexicon.json↔Neo4j 드리프트 6종(A 거부인데노드 / B 별칭인데노드 / C 정의불일치 / D 닻깨짐 / E 노드누락 / E 노드잔재). 깨끗하면 전부 0·exit0, 드리프트 시 리포트·exit1(자동수정 안 함). row2 'NODE_OK인데 노드없음'은 lexicon-status 직접 비교가 미참조 시드 6건 오탐 → **재빌드 오라클(normalized_v2.json) 집합 비교**로 구현(clean=0).

**정의 정본 — 결정 확정(override 미적용)**: 개념 정의의 정본은 '논문 추출'(concepts.json→normalize_core)로 **둔다**. `update_definition`은 **임시 라이브 오버레이**로 유지 — 전체 재빌드 시 추출 정의로 복귀(버그 아님, 올바른 모델 표현). 이유: (1) lexicon.definition override를 켜면 "추출 정의가 더 정확해도 lexicon 옛 정의가 영구 승"으로 0.4 최초정의승이 조용히 lexicon승으로 갈림 — 오늘 byte-동일은 우연이고 비용은 미래 논문에서 발생. (2) 지도 신뢰성은 "기계가 논문에서 뽑았고 사람이 임의로 안 고침"에서 나옴 — 사람이 lexicon에서 하는 일은 자격 판정(approve/reject)·동일성 판정(merge/alias)이지 정의 작성이 아님. **명시 처리**: `update_definition` docstring + patch API 응답 `note`에 "임시 오버레이, 재빌드 시 복귀, 영구 교정은 정본(concepts.json) 수정/재추출" 박음. 감사 C가 lexicon↔Neo4j 정의 드리프트 리포트.

**wipe 격리 확인**: `wipe()`는 재빌드 경로(load.py main)에만 1곳. write.py는 `wipe` import 안 함(ensure_constraints만), 증분 삭제는 전부 id 지정 단일노드(reject/merge)뿐 — 전역 wipe 없음. 증분 경로에 wipe 끼면 그래프 날아가므로 명시 검증함.

**미적용(핸드오프 범위 밖 명시)**: eval test_collect B층 Neo4j 읽기 전환, 벡터 ANN 인덱스, lexicon SQLite화, 0.4 순서의존 버그 수정.

## 2026-06-17 — 수집 비용·성능 로깅 (레벨2: 단계별 집계 계기판)

수집 흐름이 단계별로 LLM 호출수·토큰·시간을 얼마나 쓰는지 보이게. 개선 아님 — 계기판만. 동작 불변(래퍼는 인자 그대로 전달, 결과 안 바꿈). 수집 에이전트만 먼저(파이프라인·필터·command 는 후속).

- **TASK 1·2 래퍼+집계**(agent_collect.py): `logged_chat`/`logged_embed`(stage 라벨 + resp.usage 토큰·wall-time 을 모듈 누적 `_LLM_LOG` 에 기록), `_log_reset()`(회차 시작), `llm_summary()`(stage별 calls/prompt/completion/seconds + total). 수집의 LLM 호출 **5곳 전부** 래퍼 경유: embed_query→`parse_embed`, parse_intent→`parse_intent`, build_status_report→`status_report`(핸드오프 목록엔 빠졌지만 실제 호출이라 포함), expand_query→`expand`, gate_classify→`gate`(배치 루프라 여러 번, stage 같게 합산). 프롬프트·인자·흐름 불변.
- **TASK 3 eval 통합**(eval/test_collect.py): run_one 이 수집 전 `_log_reset()`, 후 `llm_summary()` → .json `"llm"`(by_stage+total) + .md `## LLM 비용·시간` 표(코드블록 정렬) + 콘솔 `print_cost`. 토큰은 `_tok`(>=1000→k약식). stage 표시순 고정(parse_embed→parse_intent→status_report→expand→gate).
- **TASK 4**(웹 reset): 범위 밖(eval 중심). 후속.
- **검증**: graph_smoke 통과(동작 불변). 실 수집 "llm 에이전트 메모리…" → 콘솔·.md·.json 에 비용 표, **gate 10회**(1배치)로 재설계 절감이 숫자로 드러남(루프 없었으면 379회). total 14회/in 7.7k·out 1.6k/19.5s. llm_summary·render/print 단위검증, data/ 복원 clean.

## 2026-06-17 — 수집 선정 재설계: 동적 편수 + 관련도순 검색 + gate 배치 루프

검색어 짧게 고친 뒤 드러난 뒷단 문제(gate 가 신규 전부 348편 LLM 판정 → 비쌈 / 최신순 검색이라 "앞 2편"이 주제 무관 신상 — "agent memory" 검색에 FragFuse 추출) 수정. 핵심은 "많이 찾는다"가 아니라 "많은데 아무거나 집는다" → **선정**을 고침. 그래프 골격·interrupt 3종·따옴표 전략·검색어 짧게 로직·_run_scenario 불변.

- **TASK 0 검증**: (0-A) arXiv `sortBy=relevance` 상위 10편이 짧은 검색어 기준 주제 적합("agent memory"→전부 agent memory 논문) → 임베딩 정렬 생략 가능. (0-B) intent count 파싱 정확("5편"→5, "다섯 편"→5, "10개 정도"→10, "여러 개"/"좀"/미언급→null, "100편"→100).
- **TASK 1 동적 편수**(agent_collect.py + prompts/collect/intent.py): INTENT_TOOL 에 `count`(["integer","null"], 선택) + 프롬프트 한 줄(영/한 일치). `MAX_EXTRACT=2` 폐기 → `DEFAULT_EXTRACT=2`/`HARD_CAP=10` + `extract_target(intent)=min(count or DEFAULT, HARD_CAP)`. confirm_extract·extract·smoke 전부 target 사용. HARD_CAP 초과 요청 시 카드에 `cap_notice`.
- **TASK 2 관련도순 검색**(search_arxiv): `sortBy submittedDate→relevance`(descending 유지). found→candidates 관련도순 보존(dict 삽입순). 따옴표·rate limit·meta 불변, 임베딩 정렬 미추가(0-A 통과).
- **TASK 3 gate 배치 루프**(gnode_gate): candidates 상위부터 `GATE_BATCH=10`씩 판정, 통과 누적 ≥ target 이면 조기 종료(`GATE_MAX_BATCHES=5`=상위 50편 한도). gate_one 캐시 그대로. 판정/통과/목표/미판정 콘솔 로그.
- **기록 보강**(eval/test_collect.py): extract_confirm stage 에 target·judged_count·cap_notice 기록, .md 에 "통과 N편 (목표 T편, gate 판정 J편) → 추출 M편" + cap_notice 표기.
- **검증**: graph_smoke 통과(cancel 추출0·정상 추출≤target·revise 재해석). 실 수집 "llm 에이전트 메모리…" → gate **10편만 판정**(옛 379편 전부 대비)·추출 2편이 주제 적합(Agent Memory Below the Prompt / MRMMIA — FragFuse 무관 추출 사라짐). "에이전트 메모리 5편 수집해줘" → target 5·**추출 5편**(FadeMem/GEM/MRMMIA/MemAdapter/MemState, 전부 on-topic). 두 회차 모두 data/ 복원 clean. extract_target/count 파싱 단위검증, .md 렌더 단위검증 통과.

## 2026-06-17 — 검색어 확장 수정: 긴 구문 0건 → 짧게 + 길이 가드

직전 진단(긴 검색어로 `all:"{q}"` 정확구문 0건)의 근본 수정. 따옴표 전략·재시도·search_arxiv·gnode_search 전부 불가침, 검색어 길이 하나만 손봄.

- **TASK 0 검증**: arXiv 에 직접 쏴봄 — 2~3단어 자연구("agent memory" 등)는 5건씩, 4단어 다개념 합성("episodic memory language model")은 0건. `all:"…"` 가 **정확 연속구문 매칭**이라 길수록·여러 개념 합칠수록 0건임 확인 → 방향(짧게·개념당 하나) 타당.
- **TASK 1**(prompts/collect/expand.py + EXPAND_TOOL desc): EXPAND_SYSTEM 에 "각 검색어 2~4단어 짧은 핵심구, 여러 개념 한 검색어에 합치지 말고 개념마다 분리, 논문에 그대로 나오는 자연 용어" 결정적 규칙 + 좋음/나쁨 예시 추가. 5줄 메타 + [한글 번역]도 새 영문과 일치하게 갱신(영문이 실제 동작·번역은 주석). EXPAND_TOOL queries description 도 동일 취지로.
- **TASK 2**(agent_collect.py expand_query): 결정론적 안전망 — dedup 루프에 `MAX_WORDS=6` 초과 검색어는 (자르지 말고)**버림**+stderr 경고, 유효 검색어 `MIN_QUERIES=3` 미만이면 재현율 경고. 자르면 의미 깨져 엉뚱 매칭이라 버리는 쪽. search_arxiv·따옴표 불변.
- **TASK 3**(0건 재시도): 범위 밖 — 이번 수정으로 충분.
- **검증**: 0건이던 "llm 에이전트 메모리…" 재수집 → 검색어 8개 전부 2단어("agent memory","episodic memory" 등) **발견 348편**. 둘째 주제 "검색 노이즈에 강건한 RAG" → 7개 짧은 검색어 **발견 152편**. 둘 다 data/ 복원 clean. 길이 가드 단위검증: 9단어 구문 버림+dedup+부족경고 동작.


## 2026-06-17 — 수집 기록에 arXiv 검색어(queries) 남기기

"발견 N편"의 N을 만든 검색어가 기록에 안 남아 "발견 0편"의 원인(검색어가 빡빡한가/호출 실패인가)을 사후 추적 못 하던 문제. 검색어는 이미 state(`queries`)에 있었고 approve interrupt payload 에만 빠져 있었음 → payload 에 실어 snapshots→기록까지 자동 전파.

- **TASK 1**(agent_collect.py): `gnode_approve` interrupt payload 에 `"queries": state.get("queries", [])` 추가(안전 접근). gnode_search·search_arxiv·expand_query·따옴표 전략(`all:"{q}"`) 전부 불가침 — 이미 있는 queries 노출만.
- **TASK 2**(eval/test_collect.py): `.md` approve 블록에 "검색어 N개:" + 줄단위 목록(비면 "검색어 없음(확장 실패 의심)"), `.json` approve stage dict 에 `queries` 배열. 둘 다 `.get("queries", [])`.
- **TASK 3**(검색 실패 목록): 권장대로 보류 — 검색어만 보여도 대개 갈림.
- **검증/성과**: 1회차 실행이 마침 **발견 0편** → 기록된 검색어 7개가 전부 매우 긴 구문("LLM agent memory retrieval augmented memory for autonomous agents" 등). 즉 `all:"{q}"` 정확구문 매칭에 너무 길어 0건임이 한눈에 드러남(호출 실패 아님 — 검색어는 멀쩡). `.md`/`.json` 양쪽에 queries 확인, data/ 복원 clean, `_run_scenario`·수집 로직 불변.

## 2026-06-17 — 수집 diff 회차에 "대화 기록"(.md) + stages(.json) 추가

회차마다 채팅 흐름(해석확인→물량승인→추출승인→결과→diff)을 **글로 재현**하는 사람용 `.md` 와, 기존 diff에 단계 payload(`stages`)·`report_text`를 더한 비교용 `.json`을 같은 timestamp로 짝지어 남기게 함. 수집 로직·프롬프트·그래프·`_run_scenario` 시그니처 전부 불가침 — `eval/test_collect.py`에서 반환값만 소비.

- **재료**: `_run_scenario`가 이미 `(result, snapshots)` 반환(snapshots=각 interrupt의 `(payload, state)`). 기존 `run_one`은 반환값을 버렸음 → 이제 받아서 소비. payload 키: interpret(`status_report`·`topic`), approve(`counts`), extract_confirm(`passed_count`·`to_extract`).
- **신규 함수**(test_collect.py): `stages_from_snapshots(snapshots, responses)`(snapshot i의 자동입력 = `responses[i]`, `_run_scenario`와 동일 규칙; payload `.get()` 안전접근으로 단계 미도달·키 누락 방어), `render_diff_md`/`render_md`(채팅 흐름 .md 생성), `write_records`(같은 ts로 .md+.json 짝). 기존 `write_record`(json 단독) 대체.
- **전문 보존**: 콘솔의 `[:60]` 절단과 달리 .md는 `status_report`(개념 목록·설명·유사도 점수)·`report_text`를 **자르지 않고 전문**. 단계 일부 미도달이면 도달한 단계까지만.
- **build_record**에 `thread`(tid) 추가. 콘솔 출력은 그대로 + 끝에 "기록: …md / …json" 안내.
- **검증**: 실 1회차("llm 에이전트 메모리…") → `eval/runs/{ts}.md`/`.json` 쌍 생성, .md가 해석확인 전문(개념 8 + 논문 8 + 점수)까지 채팅처럼 읽힘, .json `stages` 3단계(status_report 1946자·counts·to_extract·report_text) 포함, `git status data/` clean(복원 정상). README도 .md/.json 짝·stages 스키마로 갱신.

## 2026-06-16 — 수집 diff 테스트를 eval/ 디렉토리로 + 재현 문서

`test_collect.py`(루트)를 `eval/`로 모음: `eval/test_collect.py`(코드) + `eval/runs/`(회차 산출물 JSON, gitignore) + `eval/README.md`(재현 문서). 한 단계 깊어진 만큼 `ROOT = Path(__file__).parent.parent`로 수정(`HERE=eval/`, `RUNS=HERE/runs`), 백업 스냅샷은 data/ 백업이라 `data/_snapshot_test/`에 그대로. 실행은 레포 루트에서 `uv run python eval/test_collect.py "질문"`. .gitignore `data/test_runs/`→`eval/runs/`. README에 흐름·사전준비(.env/네트워크/비용)·출력 스키마·데이터 안전 보장·수동 복구법·동작원리(MemorySaver 휘발성·계보 유도 미러) 정리. 경로 재해석 후 load_view(실데이터 125/70/115)·write_record(eval/runs/) 동작 재검증.

## 2026-06-16 — 수집 diff 테스트 스크립트 (test_collect.py, rough)

같은 질문으로 수집을 돌려 "기존 데이터에서 무엇이 추가됐나(diff)"를 보는 반자동 1회차 스크립트. 7월 정식 평가(격리 반복 N회·일관성 메트릭·정답지)의 rough 선행. 신규 파일 루트 `test_collect.py` 1개 + 산출물 디렉토리만, 수집 로직/프롬프트/그래프는 호출만.

- **한 회차 흐름**: 백업(`data/outputs/`+`lexicon.json` 통째 → `data/_snapshot_test/`) → 기준선 로드 → 수집(`build_collect_graph(MemorySaver())` + `_run_scenario(…, ["proceed"×3])` 로 interrupt 자동통과, MAX_EXTRACT 상한) → `src/normalize_v2.py` subprocess 반영 → diff → **finally 복원**.
- **데이터 안전(#1 원칙)**: 3~5단계를 try, 복원을 finally — 에러·Ctrl-C에도 원상복구. 백업은 `_snapshot_test.tmp`에 쓰고 원자적 `rename`(부분 스냅샷 방지). preflight: 부분 스냅샷 청소 + 직전 미복원 스냅샷 자동 복구(스냅샷이 pristine 본) + `git status --porcelain data/` dirty 경고.
- **diff 산출**: `load_view()`가 normalized_v2.json에서 개념(canonical)·논문(id)·**개념간 계보**를 뽑음. 계보는 normalized에 직접 없고 paper→concept 엣지에서 유도 → build_graph_view 파생 규칙(home concept=첫 defines, →builds_on 대상)을 읽기 전용 미러. (검증: 실데이터 115엣지 = Neo4j 검증의 builds_on115와 일치.) lexicon status diff로 unreviewed 신규 N. 콘솔 + `data/test_runs/{ts}.json` 동일 내용.
- **인자**: `test_collect.py "질문"` 1회차, `--query-file <파일>`(줄단위 #주석/빈줄 스킵, 각각 독립 회차·매번 복원). 자동 N회 반복은 7월 범위 밖.
- **부산물 정리**: 추출이 받는 PDF(`data/pdfs/`, 백업 범위 밖·gitignore)는 회차 시작 시 파일명 집합을 찍어두고 finally에서 **이번에 새로 받은 것만** 삭제(기존 캐시 보존). → "추출 부산물 안 남음" 완전 충족.
- **gitignore**: `data/_snapshot_test/`, `data/_snapshot_test.tmp/`, `data/test_runs/`.
- **검증**: 임포트·인자/usage·preflight·load_view·build_record(형식·추가없음 케이스)·pdf cleanup(새것만 제거·기존 보존) OK. **데이터 안전 라운드트립**(backup→고의 오염→restore) 바이트 동일·git clean. **실 end-to-end 1회 성공**: "llm 에이전트 메모리 관련 조사해줘" → 발견 50·통과 34·추출 2(MAX_EXTRACT 상한 작동) → diff `+개념1(gaze heads)·+논문2·+lexicon unreviewed1`, `data/test_runs/`에 JSON 기록, 복원 후 outputs/lexicon 바이트 동일·git clean 확인.

## 2026-06-16 — 수집 UX 버그 + 세션 영속(Sqlite)·복원·클리어

수집 흐름을 서버 재시작/새로고침에도 잇고, CollectCard 갇힘·맥락유실 버그를 잡고, 대화 이력 유지 + 클리어를 더함. (`agent_collect.py`, `api/main.py`, `web/src/routes/Graph.jsx`, `web/src/api.js`, `web/src/styles.css`)

- **PART 2 — 체크포인터 Sqlite 영속**: `build_collect_graph(checkpointer=None)` — 미지정 시 `SqliteSaver(sqlite3.connect("data/collect_sessions.db", check_same_thread=False))`(FastAPI 멀티스레드 대비). 서버는 기존대로 모듈 로드 시 1회 compile(매 요청 compile 금지 함정 유지). `graph_smoke`는 `MemorySaver()` 주입해 휘발성(db 오염·재실행 충돌 방지). `uv add langgraph-checkpoint-sqlite`. db는 .gitignore. dev.sh 주석 갱신(이제 재시작에 세션 생존, 그래도 --reload는 진행 중 요청 끊김 때문에 off).
- **PART 3 — 세션 복원**: 신규 `GET /api/collect/state?thread_id=`. `_to_response`를 `_interrupt_response`(payload→stage별)·`_done_response`(values→done)로 분리 → get_state 어댑터가 재사용. 멈춤은 `snap.interrupts[0].value`(langgraph 1.2: StateSnapshot.interrupts 직접 노출), 완료는 `snap.next` 빔→`snap.values`, `created_at None`→404, interrupt 없는데 next 있음(실행 중간)→404(⑤ 범위). 반환 스키마는 start/resume과 동일 → 프론트가 그대로 카드 렌더. 프론트: startCollect 성공/응답마다 `localStorage.collectThread` 저장, done/취소/재개실패 시 제거, 마운트 useEffect가 thread 있으면 `collectGetState`→복원, 404면 제거.
- **PART 1 — CollectCard 버그**:
  - ①② revise 폼에 **[뒤로]**(ghost) 추가 → `setReviseOpen(false)+setReviseText("")`(빈 입력 갇힘 해소). `resumeCollect` 진입 시에도 `setReviseText("")`.
  - ③ 자동 스크롤 effect deps에 `collect` 추가 → 단계 전환(approve→extract_confirm)·busy 때도 맨 아래로.
  - ④ busy 카드에 직전 맥락 한 줄 유지(`stageLabel` + "통과 N편 → M편 추출 중…").
- **PART 4 — 대화 유지 + 클리어**: `messages`를 `loadMessages()`로 초기 복원 + 변경 시 `localStorage.chatMessages` 저장(chips는 그래프 하이라이트와 연동돼 **미복원** — 라벨만 뜨는 불일치 방지). chat-head에 **[비우기]** 버튼(`clearChat`: 전 상태+그래프 highlight(null)+localStorage(chatMessages·collectThread) 초기화). 수집 흐름 중(collect!=null)엔 disabled(고아 thread 방지).
- **검증**: vite build·app import·라우트 등록 OK. 인프로세스 통합테스트(무거운 노드 더미화 + 임시 db)로 **재시작 시뮬레이션** 전 단계 통과 — interpret/approve/extract_confirm 복원·done(extracted)·없는 thread 404. SqliteSaver get_state.interrupts 동작도 별도 미니그래프로 확인. (실 LLM/arXiv 경유 브라우저 시각확인은 사용자 dev.sh 권장.)

## 2026-06-16 — 그래프/채팅 레이아웃·수집 카드·입력 UI 개선 (web)

그래프가 주 화면, 채팅이 조종석. 카드는 자연 확장, 분할은 드래그 조절, 입력은 편안한 크기로. 외부 라이브러리 없이 바닐라 React 드래그. (`web/src/routes/Graph.jsx`, `web/src/styles.css`)

- **TASK A — 수집 카드 내부 스크롤 제거**: `.collect-report`(max-height 220px)·`.collect-gate`(max-height 140px)의 max-height+overflow 삭제 → 카드가 내용만큼 세로로 늘고, 길어지면 바깥 `.chat-msgs`가 스크롤(클로드식 자연 확장).
- **TASK B — 그래프↔채팅 분할 드래그**: `.chat-panel` 고정폭(420px)을 `--chat-width` CSS 변수로. `.graph-area`와 패널 사이 `.pane-divider`(6px, col-resize) 추가. `onDividerDown`→window mousemove로 `chatWidth = window.innerWidth − ev.clientX` 갱신, mouseup에 해제. clamp는 모듈 레벨 `clampChat`: min 300px ~ max `min(창폭*0.55, 720)`. 폭 변경 시 `.graph-area`(flex:1) 줄어듦 → 기존 ResizeObserver가 d3 자동 재적합(그래프 로직 무수정). 드래그 중 `body.resizing-pane`으로 전역 col-resize+선택방지. collapsed면 divider/패널 통째 숨김(기존 토글 보존), 펴면 폭 복원. `chatWidth`는 localStorage(`chatWidth`)에 저장→새로고침 유지.
- **TASK C — 입력·버튼 확대**: `.chat-input` 입력창 padding 11/12px·14px, 전송 버튼 padding 10/18px·--accent 배경. `.collect-actions button` padding 9/12px(진행=accent 주액션, 취소=ghost 위계 유지).
- **검증**: `vite build` 통과. 색·간격은 기존 토큰 재사용.

## 2026-06-15 — Neo4j 읽기 경로 전환 마무리 (전체 적재 + papers=true + 디렉토리 정리)

읽기 경로를 JSON 변환에서 Neo4j로 완전 전환. 쓰기 경로(수집/normalize/lexicon)는 손대지 않음 — JSON이 여전히 정본, Neo4j는 읽기 사본.

- **TASK A — 전체 적재**: `load_neo4j.py`에서 `pick_subgraph`(RAG 서브그래프) 제거 → `normalized_v2.json` 전체 적재. 결과 Paper 70 / Concept 125 / 관계 195(엣지 196 중 중복 1건 `2307.09288→llama:builds_on`을 MERGE가 멱등 dedup). home_concept는 전체 논문 대상 첫 defines로 계산.
- **TASK B — papers=true 전환**: `api/graph_neo4j.py`의 `graph_view_neo4j(include_papers=True)` 구현 — 논문 노드(`paper:` 접두사 복원)·`defines`·정의 없는 논문만의 `paper_builds_on`(3편)을 Cypher로 추가. `get_graph` 라우팅을 papers=false/true **둘 다 Neo4j**로. (Neo4j는 Paper.id를 접두사 없이 저장 → 출력 시 `paper:` 재부착, 개념 id는 양쪽 무접두.)
- **검증**: `verify_neo4j.py`를 재작성 — 이제 **프로덕션 함수** `graph_view_neo4j`를 직접 호출해 `build_graph_view`의 충실한 JSON 포트와 papers=false/true 둘 다 대조(papers 리스트 정렬·엣지 집합화로 순서 무시). 전체 일치: 개념125·builds_on115·defines76·paper_builds_on3. 백엔드 띄워 `/api/graph` 양쪽 모드 curl로 동일 확인.
- **TASK C**: `/api/lexicon`은 JSON 유지(lexicon.json은 rejected/pending 포함 전체 사전이라 Neo4j가 대체 불가 — 쓰기/검수 도메인). `/api/command`의 개념명 목록 조회만 `graph_view_neo4j`로 전환. `/api/rebuild`는 의도적으로 `build_graph_view`(JSON) 유지 — 방금 재생성한 JSON 카운트 보고 + 롤백 함수 보존.
- **TASK D — 디렉토리 정리**:
  - `load_neo4j.py`→`graphdb/load.py`, `verify_neo4j.py`→`graphdb/verify.py` (신규 `graphdb/` 패키지). a1/a3/ttl→`docs/ontology/`(+서사 README). 경로 한 단계 깊어진 만큼 `parent.parent`로 수정, 전 스크립트 새 위치에서 실행 검증.
  - **함정 회피**: 핸드오프는 `neo4j/` 디렉토리를 지시했으나 그 이름은 루트가 sys.path에 오를 때(uvicorn cwd, main.py의 `sys.path.insert(ROOT)`) 설치된 `neo4j` 드라이버를 **shadow**해 `from neo4j import GraphDatabase`를 깨뜨림(empirical 확인). → 충돌 없는 `graphdb/`로 명명.
- **롤백 보존**: `build_graph_view`(JSON) 원본은 main.py에 그대로(line 54), `/api/rebuild`가 계속 사용 → 죽은 코드 아님.

## 2026-06-11 — 프론트 채팅: 수집 에이전트 연결 (라우팅 + interrupt 카드)

같은 채팅 패널에서 필터 명령과 수집 명령을 둘 다 받음. 수집이면 LangGraph 흐름(start/resume)을 타고 interrupt 3개를 버튼 카드로. "말로 부리는 수집" 데모의 마지막 표면.

- **라우팅(agent_filter.py)**: TOOLS에 `collect{topic_text}` 추가 + 시스템 프롬프트 한 줄("가져와/수집/찾아와→collect"). 새 라우터 안 만들고 기존 분류기로 흡수. /api/command 변경 없음(collect도 generic 반환).
- **api.js**: `collectStart(text)`, `collectResume(thread_id, decision, signal)`.
- **Graph.jsx**: runCommand가 tool==="collect"면 collectStart로 흐름 진입. `collect` state{thread_id, stage, data, busy, timedOut}. interrupt 카드(`CollectCard`) stage별:
  - interpret: status_report + [진행][수정][취소]. 수정은 입력→`revise:<텍스트>`.
  - approve: counts(발견/신규/보유제외) + [진행][취소].
  - extract_confirm: gate_summary(통과 강조·탈락 흐림) + N편 추출예정 + [추출][그만].
  - 수집 흐름 중 입력창 잠금. done이면 summary 버블 + 잠금 해제, 추출분 있으면 재빌드 안내.
  - 추출 단계만 AbortController 120초 타임아웃 → 초과 시 [재시도][취소]+안내(흐름 안 죽임).
- styles.css: collect-card/스피너 등.

**검증**: `/api/command` 라우팅 — 필터 회귀 없음(벤치마크→filter, RAG계보→focus_lineage, 다보여줘→reset), 수집 3종 모두 collect{topic_text}. `npm run build` 성공. 카드 상호작용(버튼/잠금/스피너/타임아웃)은 빌드+로직 검증, 브라우저 클릭 검증은 미수행(원하면 /run으로 실연 가능).

## 2026-06-11 — 추출 승인 interrupt 추가 (gate ↔ extract 분리)

proceed→proceed가 관문(빠름)+추출(느림·11분 stall 실증)을 한 번에 돌려 HTTP가 오래 hang하던 문제. gate와 extract 사이에 interrupt를 하나 더 넣어 관문 결과를 먼저 보여주고 멈춘 뒤 추출을 따로 승인.

- **`gnode_confirm_extract`(agent_collect.py)**: gate→[extract_confirm]→extract. interrupt payload `{stage:"extract_confirm", passed_count, to_extract(상한적용), gate_summary}`. resume proceed→extract, cancel→report. 흐름 interrupt 3개: interpret/approve/extract_confirm.
- **`gnode_report` cancel 구분**: approve cancel→"수집 취소(관문 안 함)", extract_confirm cancel→"추출 취소 — 관문 N편 완료(통과 M편)". gate_results 유무로 판단.
- **`_to_response`(api/main.py)**: extract_confirm stage 추가(passed_count/to_extract/gate_summary/actions). start/resume 로직 불변.
- graph_smoke 갱신: 정상경로 interrupt 3회·순서 검증 + extract_confirm 멈춤 시점에 extracted 비어있음(분리 증거) assert.
- 기존 함수(gate_one/extract_pipeline) 로직 무수정 — 노드 배선만.

**curl 스모크**: start→interpret / proceed→approve(new 23) / proceed→**extract_confirm(done=false, passed 9, to_extract 2편, concepts 70 그대로=추출 안 됨)** / cancel→done·extracted []·"추출 취소 관문 23편(통과 9)". 하드 게이트 1~3 통과. 핵심: **두 번째 proceed가 추출 없이 멈춤** = 관문/추출 분리.

**효과**: hang 구간이 "마지막 [추출] 승인 이후"로 좁아짐. 추출 자체의 stall은 그대로 — 6-2 프론트에서 그 구간 진행표시/타임아웃 또는 비동기 잡 필요.

## 2026-06-11 — 수집 에이전트 채팅 백엔드 (start/resume API)

LangGraph 수집 흐름을 HTTP로 노출. 그래프는 interrupt까지만 실행 → 멈춤을 응답으로 → 결정으로 재개. 프론트 버튼은 다음 조각.

- **그래프 모듈 로드 시 1회 컴파일·전역 보관**(`_collect_graph = build_collect_graph()`). 매 요청 compile하면 MemorySaver 상태가 날아가 resume이 깨짐(핵심 함정). thread_id별 세션 격리.
- `POST /api/collect/start {text}` → uuid4 thread_id 발급, 첫 interrupt(해석확인)까지. `_to_response`로 `{thread_id, done, stage, report/counts, actions}`.
- `POST /api/collect/resume {thread_id, decision}` → `Command(resume=decision)`로 재개. decision: proceed|cancel|revise:<텍스트>.
- **세션 가드**: 없는 thread_id는 `get_state(cfg).created_at is None` → **404**(조용히 새 실행 방지).
- checkpointer는 인메모리 MemorySaver 유지(데모 충분, 영속은 과투자).

**curl 스모크(하드 게이트 4종 통과)**:
1. invalid thread_id resume → 404 ✓
2. start → done=false·stage=interpret·actions[proceed,revise,cancel] ✓
3. resume proceed → done=false·stage=approve·counts(new 32) ✓
4. resume cancel → done=true·extracted [] ✓
- 정상경로(proceed/proceed): done=true·extracted ['2602.03689','2602.01965'](≤MAX_EXTRACT) ✓.

**⚠️ 관찰(다음 조각 과제)**: proceed→proceed는 동기 응답 안에서 관문(후보 20편)+PDF추출2편이 다 돌아 수십초~분 지연. 이번엔 `relate` LLM 호출 하나가 ~11분 stall(API 일시 지연/재시도)해 HTTP가 그만큼 hang. **동기 추출은 장시간 hang 위험** → 프론트 연결 시 비동기/백그라운드 잡 + 폴링, 또는 타임아웃·진행표시 필요.

**커밋 범위**: API 코드만(api/main.py). 정상경로 스모크 byproduct(추출 2편·papers.json 변경)는 되돌림(직전 조각과 동일 원칙).

## 2026-06-11 — 수집 에이전트 LangGraph 묶기 (흐름 엔진)

[1]~[8] 단위 함수를 LangGraph 그래프로 묶고 사람 개입 2곳(interrupt)을 넣음. **기존 함수 로직 변경 없음 — 노드는 호출 래퍼.** 채팅 UI 연결은 다음 조각.

- 의존성 `langgraph` 1.2.4. checkpointer = MemorySaver(인메모리), interrupt/resume에 thread_id 필요.
- **State**: `CollectState`(TypedDict) — query/intent/related/status_report/queries/found/candidates/counts/gate_results/extracted/decision/report_text.
- **그래프**: parse → [interrupt 해석확인] → expand_search → [interrupt 물량승인] → gate → extract → report. 조건분기: 해석확인 `revise:` → parse 루프, 물량승인 `cancel` → report 직행(추출 0).
- interrupt는 `langgraph.types.interrupt()` 노드 안 호출 → 일시정지, `Command(resume=값)`으로 재개. resume: 해석확인 `proceed`|`revise:<텍스트>`, 물량승인 `proceed`|`cancel`.
- `--graph-smoke`. 기존 `collect_extract_smoke()`도 회귀 비교용으로 유지.

**스모크(3 시나리오, 스크립트 resume)**:
- A 취소: proceed→cancel → extracted []. 두 지점 멈춤 확인. (dedup 보유제외 2 = 직전 반영분이 이제 보유라 정상 제외)
- B 수정: `revise: RAG robustness to noisy retrieval` → 재parse(topic 재해석)→해석확인 재멈춤 → proceed → cancel. (재해석된 구체 topic은 `all:"긴 구문"` 정확매칭이라 발견 0 — phrase 검색이 과구체 주제에 취약함 관찰)
- C 정상: proceed→proceed → 관문→추출 1편(≤MAX_EXTRACT). 파일 생성 확인.
- 하드 게이트 4종 통과(compile·interrupt 멈춤2회·cancel 추출0·정상 추출≤상한·revise 재해석).

**커밋 범위**: 흐름 엔진 코드만(agent_collect.py + langgraph 의존성). 정상경로 스모크가 byproduct로 추출한 2602.12709(ReFilter)와 papers.json 장부 변경은 되돌림 — 이 chunk는 엔진 검증이고 수집 반영은 범위 밖(사용자 결정).

다음 조각: API/프론트에 그래프 흐름 연결 + 채팅 [진행]/[취소] 버튼. 영속 checkpointer 고려.

## 2026-06-11 — 수집 에이전트 [6][7][8]: 물량승인(임시) + 관문 + 추출

[5] 신규 후보 → [6] CLI 승인 → [7] 관문(초록만 보고 분류) → [8] 통과분 PDF 추출. LangGraph 묶기·채팅 버튼은 다음 조각.

- **기준표 분리(`src/prompts.py`)**: EXTRACT_SYSTEM 안의 paper_type 정의를 `PAPER_TYPE_CRITERIA` 상수로 추출, extract와 관문이 공유(단일 출처). **EXTRACT_SYSTEM 재조립 결과 byte-identical 확인**(sha256 동일) → extract 동작 불변.
- **[7] 관문(`gate_one`/`gate_classify`)**: LLM 1회, 제목+초록만 보고 paper_type 분류. **이진 판정**(technique=통과). papers.json gate에 `{verdict, reason, model, prompt_ver:"gate-v1", date}` 기록. **캐시**: 같은 prompt_ver 있으면 LLM 재호출 안 함(프롬프트 바뀌면 재판정).
- **[8] 추출(`extract_pipeline`)**: 통과분만 `fetch.download_one`(PDF 첫 다운로드)→`parse.parse_one`→`extract.extract_one`→`relate.relate_one`, `{pid}.parsed/concepts/relations.json` 생성, ledger.extracted=true. 다운로드 실패 시 스킵(중단 안 함). 기존 파이프라인 호출만, 로직 수정 없음.
- **[6] 물량승인**: CLI y/N 임시 게이트. 스모크 추출 상한 `MAX_EXTRACT=2`(수백 편 PDF 사고 방지).
- `--collect-extract-smoke` 플래그.

**스모크 결과**(`echo y |`): 신규 22편 → 관문 22편 분류(통과 10/22). 분류 갈림 정상: technique(GARAG·RoseRAG·RPO·CORD·ATM 등), benchmark(EmoRAG·T²-RAGBench·QE-RAG), analysis(When Retrieval Hurts·Evaluating Robustness), survey(AI Search Paradigm). 추출 2편(상한): **2404.13948 GARAG**[technique, builds_on RAG], **2605.01302 CoRM-RAG**[technique, builds_on RAG] — 산출 파일 6개 생성. 게이트 4종 통과. 캐시 동작 확인(재호출 cached=True, LLM 0회). PDF는 `data/pdfs/`(gitignore)라 미커밋.

다음 조각: LangGraph로 [2.5]/[6] 대기 묶기 + 채팅 [진행]/[취소] 버튼. 추출분 노드 반영은 `uv run python src/normalize_v2.py` 별도 1회.

## 2026-06-11 — 수집 에이전트 [3][4][5]: 검색어 확장 + arXiv 검색 + 장부/중복제거

의도 파싱(topic) → arXiv 신규 후보 목록까지. PDF·관문·추출은 다음 조각.

- **[3] `expand_query(topic, related_terms)`**: LLM 1회로 topic을 arXiv 검색어 5~8개로 확장. [2] 현황확인의 보유 개념/논문 canonical을 재료로 넘겨 맵 밀착.
- **[4] `search_arxiv(queries, period_from, period_to, max_per_query=50)`**: export.arxiv.org Atom API(feedparser 파싱). 요청 사이 3초 sleep(rate limit), 순차. arXiv ID 버전접미사(`v\d+`) 제거 정규화, 검색어 간 ID dedup, period는 클라이언트단 필터.
  - **함정 발견·수정**: 핸드오프 스펙 `all:<검색어>`(따옴표 없음)는 다단어를 토큰 OR로 풀어, submittedDate 정렬 시 **무관한 최신 논문 firehose**가 떴음(첫 스모크 184편 전부 노이즈: Low-Light Video, Lattice QCD…). → **구문 검색 `all:"<검색어>"`**(따옴표)로 수정. 재스모크 22편 전부 RAG robustness 관련. 변형 A/B/C 직접 대조로 확인.
- **papers.json 장부**(신규): "한 번이라도 검색에 걸린 논문" 장부(lexicon의 논문판). upsert로 메타 갱신, gate/extracted/first_seen_query 보존.
- **[5] `dedup_new_candidates`**: found에서 (1)지도 보유(normalized_v2 paper 노드), (2)관문 탈락(gate.verdict∈reject) 제외 → 신규 후보 + 카운트.
- `--collect-smoke` 플래그로 [1][2] 스모크(`intent_smoke`)와 분리.

**스모크 결과**: 검색어 8개(robust RAG·failure modes·self-correcting·benchmarking reliability 등 다양). arXiv 발견 22편, 샘플 3편 모두 RAG robustness 주제, 메타 정상. dedup: 발견 22/보유제외 0/신규 22. 게이트 4종 통과. 보유 dedup은 이번 검색에 보유 논문이 안 걸려 자연 관찰 불가 → **주입 테스트로 로직 검증**(보유 1706.03762 제외·관문탈락 제외·신규 산출 OK).

다음 조각: [6]물량승인 + [7]관문 + [8]추출(PDF 받기 시작). papers.json의 gate/extracted를 거기서 채움.

## 2026-06-11 — 논문 보기: 정의없는 논문 닻 내리기

"논문 보기 ON인데 일부 논문이 안 보인다" 지적. 원인: 논문은 `defines`(논문→개념)로만 그래프에 붙는데, survey/analysis처럼 새 기법을 정의하지 않는 논문 4편은 엣지가 없어 고립(라벨 없는 r6 회색 점이라 사실상 안 보임).

- 기준 명확화: 논문 연결 = `defines`. 64편은 정의로 연결, 4편(2001.08361·2312.10997·2401.14887·2408.08921)은 정의 없음.
- 수정(`api/main.py`): `?papers=true`에 **정의없는 논문만** `builds_on`(논문→개념)으로 닻 내리는 `paper_builds_on` 추가. 이미 연결된 64편은 그대로(화면 회귀 0). 결과: 3편 닻 내림, 2001.08361만 데이터상 정의·참조 둘 다 없어 고립 잔존.
- 프론트(`Graph.jsx`): 링크 스타일을 `kind==='builds_on'`(개념↔개념=색 실선+화살표) vs 그 외(`defines`·`paper_builds_on`=옅은 점선)로 정리.

**검증**: build 성공. `?papers=true` → defines 73 · paper_builds_on 3 · 고립 1(2001.08361). 기본뷰엔 paper_builds_on 키 없음.

## 2026-06-11 — 수집 에이전트 v2 재배치 (전환 4/4)

`agent_collect.py`를 v2 이중 노드 임베딩 위로 옮기고, 현황 확인을 **두 각도**로 확장 + **현황 보고 + 충분성 추천** 생성. arXiv 실제 수집은 다음 조각.

- 임베딩 로더 v1→v2: `node_embeddings_v2.json`을 개념(`concept:`)·논문(`paper:`)으로 **타입 분리**해 각각 정규화 행렬. v1 파일(node_embeddings.json·normalized.json) 더는 안 읽음.
- 두 각도 매칭: topic 임베딩 1회 → **개념(definition) 매칭** "관련 기법이 뭐 있나" + **논문(problem) 매칭** "같은 문제 다룬 논문이 뭐 있나"(세렌디피티). floor=0.30 컷, top=8.
- `build_status_report()`(LLM 1회): 매칭 상위의 definition/problem을 묶어 주제 관점 풀이 + 종합 판정 + 충분성 추천(충분/부분적/비어있음). placeholder 개념은 "정의 미보유"로 짧게. `confirm_message()` 대체.
- 스모크를 **하드 게이트**로: model·개념73·논문68 assert 실패 시 exit 1.

**스모크 결과**(쿼리당 LLM 2회 + 임베딩 1):
- 게이트 통과: 개념 73 + 논문 68.
- "knowledge graph 만들기" → 개념 상위에 **GraphRAG(0.54)·HippoRAG(0.51)·LightRAG(0.43)·HyperGraphRAG** 등장(v2 definition 매칭의 핵심 증거).
- 논문(problem) 매칭이 개념과 **다른 항목**도 포착: RAG강건성에서 "The Power of Noise"·RAGBench, 멀티에이전트에서 Switch Transformers·Constitutional AI 등 — problem 각도가 definition과 다른 정보 제공.
- 보고가 나열이 아닌 풀이+종합+추천 형태, floor 아래(<0.30) 노드 미혼입(최저 0.34).

다음 조각: 실제 arXiv 검색/수집/승인 + LangGraph 분기(설명/수집/수정). 충분성은 이번엔 **추천만**, 자동 결정 아님.

## 2026-06-11 — API·프론트 v1→v2 전환 (전환 3/4)

API가 `normalized_v2.json`(이중 노드)을 읽어 **개념 주도 v1 호환 형태로 변환**해 서빙. 프론트는 최소 수정 + "논문 보기" 토글. 회귀 최소화 우선.

**API (`api/main.py`)**
- `build_graph_view(include_papers)` 신설: v2 → 개념 노드(접두사 제거) + 개념간 builds_on 유도.
  - **builds_on 유도 결정**: 핸드오프는 D×B 교차곱을 명시했으나, v1 normalize.py는 실제로 **'첫 정의 개념'(defs[0])만 source**로 씀을 확인. 교차곱은 v1과 +17 엣지(다중정의 논문 9개에서) 차이 → 시각 회귀. 사용자 확인 후 **첫 정의(defs[0]×B)** 채택. 결과 113 엣지 = v1과 113/113 정확 일치(파생-only 0). v1-only 4는 paper 의사노드 소스 3 + `replug→replug` 자기루프 1(v2가 올바르게 제거).
  - ptype/domain: 그 개념을 defines한 첫 home 논문의 paper_type/domain(없으면 technique/general). papers: defines·builds_on로 언급한 논문 id.
- `GET /api/graph?papers=true`: 논문 노드(`paper:` 접두사 유지) + defines 엣지 추가. 기본 응답엔 defines 키 없음.
- `/api/rebuild`: normalize.py + normalize_v2.py **둘 다** 실행(v1 normalized.json도 생성 → 롤백 가능). `/api/command`: 노드명 소스를 v1 normalized.json → v2 변환본으로 교체. **코드가 더는 v1 파일을 읽지 않음**(NORMALIZED_PATH는 정의만 남음).

**프론트 (`web/src/`)**
- `api.js`: `getGraph(withPapers)` → `?papers=`.
- `Graph.jsx`: "논문 보기" 토글(범례 내, 기본 OFF). ON이면 재로드 → 논문=작은 회색 점(r6), defines=옅은 점선. 논문 클릭 시 디테일 패널에 title/paper_type/problem/arXiv. 검색·필터·계보는 **개념만**(applyFilter가 `type==='paper'` 스킵, names 개념만). 토글 시 강조/선택 초기화.

**검증**: `npm run build` 성공. 라이브 서버: 기본 `/api/graph` = 개념 122·builds_on 113·defines 키 없음·paper 키 없음. `?papers=true` = 논문 68·defines 73. `/api/command` 다보여줘→reset, RAG 계보→focus_lineage(RAG), asdf→tool:null. 보호 파일(normalize*.py·normalized.json·lexicon.json·v1 임베딩) 무변경.
- **기본뷰 122 vs v1 126 = 의사노드 4 차이**: v1이 개념처럼 그리던 define-없는 논문 4개(2001.08361·2312.10997·2401.14887·2408.08921)가 이제 "논문 보기" 토글의 진짜 논문 노드로 이동. 개념 지형도는 동일 — 전환의 의도된 결과.

다음: 수집 에이전트 재배치(4/4) — agent_collect.py를 v2 위에, 현황 확인을 개념+논문 이중 매칭으로.

## 2026-06-10 — embed_nodes_v2: 이중 노드 타입별 임베딩 (전환 2/4)

`normalized_v2.json`(190노드)를 타입별로 임베딩. 개념→definition, 논문→problem.

- `src/embed_nodes_v2.py` 신규. 개념 노드는 **순수 definition 텍스트만** 임베딩(canonical 이름 미부착 — "RAG" 류 철자 오염 방지), 논문 노드는 problem 임베딩.
- placeholder 개념(정의 없음, 49개)은 제외. 수집으로 정의 채워지면 자동 합류(증분).
- 모델명을 파일에 기록 → 같은 모델이면 영구 재사용, 바뀌면 전체 재생성(Neo4j 이관 시 재계산 불필요). 증분 캐시: 이미 임베딩된 id 건너뜀, `--force`로 전체.
- 출력: `data/outputs/node_embeddings_v2.json` = `{model, dim, vectors}`. v1 `node_embeddings.json`은 무변경(3/4에서 전환).

**검증**: `uv run python src/embed_nodes_v2.py` → 논문 68 + 개념 73 = 141 / dim 1536. 수용 기준 6종 통과: 임베딩 개념수=정의있는개념수(73=122−49), 임베딩 논문수=전체논문(68), dim 1536, model 기록됨, 재실행 시 "신규 0개", `--force`로 141개 재생성. normalize.py·normalized.json·lexicon.json 무변경.

다음: API/프론트 v1→v2 전환(3/4) → 수집 재배치(4/4).

## 2026-06-10 — normalize_v2: 이중 노드(논문+개념) 데이터 토대 (전환 1/4)

개념 단일 노드 → **이중 노드(paper + concept)** 전환의 데이터 재조립 단계. LLM 호출 없음, 기존 파일 무변경.

- `src/normalize_v2.py` 신규. `*.concepts.json`(논문 속성)·`*.relations.json`(builds_on)을 재조립해 `data/outputs/normalized_v2.json` 생성.
- problem→논문 노드, definition→개념 노드로 귀속 분리. id에 `paper:`/`concept:` 접두사, 엣지는 `{type, from, to}` 단일 배열(defines·builds_on). 모든 엣지 `paper:* → concept:*` 방향.
- 거름망은 개념에만(lexicon status approved/unreviewed). 논문은 전부 노드. 빈 링 개념은 `def_status=placeholder`로 계보 보존.
- `normalize.py`에서 canon/load_lexicon/save_lexicon/NODE_OK import 재사용(규칙 단일 출처). normalize.py 무수정.

**검증**: `uv run python src/normalize_v2.py` → 논문 68 + 개념 122 = 노드 190 / 엣지 191(defines 73·builds_on 118) / 빈 링 49 / **사전 신규 {unreviewed:0, pending:0}**. 수용 기준 6종 통과: 논문수=concepts파일수(68), 엣지 방향 위반 0, paper 노드 problem/title·concept 노드 canonical/definition 보유, `lexicon.json`·`normalized.json` git diff 무변경(롤백 가능).

다음: 임베딩 분리(2/4) → API/프론트(3/4) → 수집 재배치(4/4).

## 2026-06-10 — UI 개선 4종: 그래프 자동맞춤·노드 디테일·채팅 예시칩·사전 zebra

`web/src/routes/Graph.jsx` · `styles.css`. 사용자가 4개 모두 선택.

**1) 그래프 자동 맞춤** — `render()`에 `fitView(animate)` 추가(노드 x/y bbox→줌 transform, 라벨 여백 위해 padX 160·padY 90, k 상한 1.6). 로드 시 sim `alphaDecay(0.05)`로 ~2초 빨리 안정 후 `on("end")` 1회 자동 맞춤(드래그 재안정 땐 `didFit` 가드로 재맞춤 안 함). 좌상단 svg 위 "⤢ 전체 보기" 버튼이 `apiRef.fitView()` 호출.
  - 시행착오: 동기 `sim.tick()` 루프 사전안정은 forceCenter만으론 비연결 노드가 멀리 튀어(blow-out→speck) 폐기. forceX/Y(0.05) 복원력은 charge를 눌러 클럼프 붕괴→폐기. 원래 force(-900) 유지 + alphaDecay만 올려 timer-driven end 맞춤이 정답(스샷 확인 양호).
**2) 노드 디테일** — 미선택 시 카드 숨김(기존 "지형도/클릭하세요" 제거). type 색 배지(`.type-badge`), papers를 arXiv 링크(`https://arxiv.org/abs/{id}`), 닫기 ✕(`detail-close`).
**3) 채팅 예시 칩** — 빈 상태에 클릭 가능한 예시 4종(벤치마크/RAG 계보/2024 이후/다 보여줘). `sendCommand`를 `runCommand(text)`+`onSubmit`으로 분리해 칩이 직접 실행.
**4) 사전 가독성** — tbody 짝수행 zebra(`#f1f1ec`), sticky th 그림자.

**검증**: build 성공 + Playwright 스샷 — 자동맞춤(전체 노드 프레이밍), 디테일(InstructGPT 배지+arXiv 링크+닫기), 예시칩 클릭→필터 적용(칩+버블+노드 강조), 사전 zebra 확인.

## 2026-06-10 — UI 미세조정: 뷰포트 꽉채움 + 채팅 확대 + 브랜드 확대

`styles.css`만. 스크롤바/잘림 원인은 `.graph-page`의 `width:100vw`(스크롤바 폭 포함→가로바)와 하드코딩 `calc(100vh-41px)`(14px 폰트로 nav 실제 높이>41px→세로 오버플로).
- 앱 셸을 세로 플렉스로: `html,body,#root{height:100%}`, `body{overflow:hidden}`, `#root{display:flex;flex-direction:column}`. nav `flex:0 0 auto`. 라우트 컨테이너(`.graph-page`/`.lex-wrap`/`.center-msg`)는 `flex:1; min-height:0`로 잔여 공간 정확히 채우고 내부 스크롤. `.graph-page`의 100vw·calc 제거 → `width:100%`.
- Playwright로 /graph·/lexicon 모두 scrollWidth==clientWidth·scrollHeight==clientHeight(오버플로 없음) 확인.
- 채팅 패널 320→420px. 브랜드 `.nav .brand` 19px bold.

## 2026-06-10 — UI 개선: 라이트 테마 + 스케일업 + 레이아웃 정리

스타일·표시만. 채팅/필터/계보 동작 로직 미변경. `web/src/styles.css` · `routes/Graph.jsx`.

**라이트 테마(전역)** `styles.css`
- `:root` 교체(웜 오프화이트 `#f7f7f5`/패널 `#fff`/accent `#2563eb`). `--accent-fg`(accent 위 글씨)·`--hover`·`--shadow`·`--mono` 추가. 다크 하드코딩(#16161a/#1f1f26/#2a2a33/#14141a/#08121a 등) 전수 변수화. body 폰트 mono→system-ui 산세리프, 13→14px. badge/toast/matched 행은 라이트 톤(blue-100, green/red-100 등). /lexicon source·first_seen 열만 `--mono` 유지(arXiv ID).
- 노드색 라이트용 교체(Graph.jsx TYPE_COLOR): technique #2563eb / benchmark #d97706 / analysis #7c3aed / survey #059669.
- placeholder 노드: fill #fff + 점선 테두리(`stroke-dasharray "3 2"`, stroke=type색). 범례 dot도 흰 바탕+점선.

**스케일업** `Graph.jsx`
- 노드 r 10→12(focus 18, ~1.5× 유지), 라벨 11→13px·fill `--text`·x오프셋 13→16, `forceCollide` 28→30.

**필터 시 엣지 표시** `Graph.jsx highlight()`
- 비매칭 엣지를 opacity 0.06 → **`display:none`**(화살촉만 또렷이 남던 문제 해결). 매칭(양끝) 엣지만 표시, 비매칭 노드는 흐림 0.18(숨김 아님). reset 시 `display:null` 복원.

**레이아웃** `styles.css`
- 검색창 top-center→**좌상단**, 범례→**좌하단**, 노드 디테일 패널 우측 풀하이트→**좌측 카드**(검색창 아래, max-height로 범례와 비충돌), 활성 칩→상단 중앙. 오버레이 전부 border+`--shadow`로 분리. 오른쪽은 채팅 단독.

**검증**: `npm run build` 성공 + Playwright 스크린샷 3종 육안 확인 — (1) /graph·/lexicon 라이트, 다크 잔재 없음 (2) placeholder kNN-LM 흰 점선 원 (3) "벤치마크만" 필터 시 비매칭 노드 흐림·**화살표 전부 사라짐**·칩 표시·버블 "benchmark · 3개 강조".

## 2026-06-10 — `/graph` 채팅 패널(필터 에이전트 프론트)

핸드오프대로 프론트만. 백엔드 `POST /api/command`(이미 구현·검증)는 미수정.

**레이아웃** `web/src/routes/Graph.jsx` · `styles.css`
- `.graph-page`를 flex 가로 분할: `.graph-area`(flex 1, 기존 svg·검색·범례·디테일 패널을 그 안의 absolute 오버레이로 이동) + `.chat-panel`(320px 고정).
- 패널 접기 토글(`>`/`<`). 접으면 그래프 전체 폭. svg 크기는 `window.innerWidth` 대신 `.graph-area` 측정으로 변경하고 `ResizeObserver`로 접기/리사이즈 시 svg·forceCenter 갱신(`sim.alpha(0.2).restart()`).

**채팅→그래프** (LLM 추가 호출 없이 프론트 템플릿)
- `api.js`에 `postCommand(text)` 추가. 입력→사용자 버블→`/api/command`→대기「…」→tool 실행→에이전트 버블.
- `render()`가 `{sim, focus, names, highlight, resize}` 반환(기존 3개에 highlight·resize 추가). 강조=opacity만 입힘(매칭 1·비매칭 0.12, 엣지는 양끝 매칭 시만 0.65 아니면 0.06). 시뮬레이션 재시작 없음.
- `filter`: 노드 속성 AND 매칭. `date_after`는 papers의 arXiv ID 앞4자리→연월 중 **최소값** 기준, papers 빈 placeholder는 비매칭. 0개면 강조 변경 없이 「조건에 맞는 노드가 없음」.
- `focus_lineage`: `builds_on{from,to}`(to=조상) JS 순회, ancestors/descendants/both, visited로 사이클 방지. node 소문자화해 키 매칭, 없으면 메시지.
- `reset`: 강조 해제. 활성 조건은 좌상단 칩(✕=reset)으로 표시.
- `tool:null`/네트워크 실패는 에이전트 버블로 표시.

**검증**: `npm run build` 성공. `/api/command` 실제 응답 4종(filter ptype/date_after, focus_lineage, ) 프론트 기대 형태와 일치 확인. 데이터 정합: `rag` 키 존재, benchmark 3·date≥2024-01 20개 매칭. 브라우저 수용기준은 미실행(서버 기동 확인까지).

## 2026-06-09 — 웹 UI (FastAPI + React) 1차 구현

핸드오프 문서대로 결과물(그래프+사전) 웹 조회/편집 UI 구축. `src/` 파이프라인 미수정(normalize.py는 호출만).

**백엔드 `api/main.py` (FastAPI)**
- `GET /api/graph` — `data/outputs/normalized.json` 그대로 반환
- `GET /api/lexicon` — `lexicon.json`의 techniques를 배열로 변환
- `PATCH /api/lexicon/{name}` — 부분 업데이트(status/aliases/definition/source/first_seen)
- `POST /api/lexicon/merge` — `{from,into}`: from(+aliases)을 into의 alias로 흡수 후 from 삭제
- `POST /api/rebuild` — `src/normalize.py`를 subprocess 실행(cwd=루트, MAP 미설정), 노드/계보 수 반환
- CORS: localhost:5173 허용
- deps: `uv add fastapi "uvicorn[standard]"`

**프론트 `web/` (Vite + React + react-router + d3)**
- `/lexicon` (기본) — 표 + 필터(pending 기본)/검색/status 드롭다운(PATCH)/alias 칩 편집/definition textarea/병합(prompt로 대상 지정)/재빌드 버튼+토스트. AI 도우미 버튼은 disabled(준비 중).
- `/graph` — `build_graph.py`의 d3-force 이식. ptype 색, placeholder=빈 원, 엣지=from ptype 색+화살표, zoom/pan/drag, charge -900/link 160·0.3/collide 28. (problem 유사도 슬라이더는 범위 밖 → 제외)
- `/search` — coming soon placeholder
- Vite proxy로 `/api`→8000. `web/{node_modules,dist,.vite}` gitignore 추가.

**검증**: 백엔드 4개 엔드포인트 curl 통과(PATCH 왕복 후 lexicon git-clean 확인), `npm run build` 성공, 두 서버 띄워 5173→8000 프록시로 lexicon(144)/graph(66) 로드 확인.

**실행**: `uv run uvicorn api.main:app --reload --port 8000` + `cd web && npm install && npm run dev`

**남은 일(범위 밖, 미래)**: problem 유사도 슬라이더, /search 동작, AI 도우미 동작.

## 2026-06-09 — 웹 UI 2차: 노드/사전 검색·이동·정렬

핸드오프 v2 3건. 백엔드(`api/`)·파이프라인(`src/`) 미수정, 프론트만.

**`/graph` 노드 검색→이동(핵심)** `web/src/routes/Graph.jsx`
- svg 상단 중앙 검색창(`form`). `canonical` 부분일치(대소문자 무시).
- `render()`가 `{sim, focus, names}` 반환하도록 변경(기존엔 sim만). `zoom` 핸들러를 변수로 잡아 `focus(id)`에서 `zoom.transform`을 500ms transition으로 호출 → 해당 노드를 화면 중앙(scale 1.5)으로 이동. 강조: 해당 circle만 stroke-width 5·r 15.
- 매칭 0=「없음」, 1=바로 이동, 여러개=검색창 아래 매칭 목록(클릭 이동) + 같은 검색어로 Enter 반복 시 다음 매칭 순회. 이동 시 사이드 패널(`setSelected`)도 갱신.
- 노드 키는 canon 소문자(`n.id`)로 focus, 검색·표시는 `n.canonical`.

**`/lexicon` 정렬** `web/src/routes/Lexicon.jsx`
- 헤더 클릭 정렬(name/status/source/first_seen) 오름/내림 토글 + ▲/▼ 표시. aliases·definition·액션은 비정렬.
- 정렬은 현재 status 필터 적용 후의 목록에 대해 동작.

**`/lexicon` 검색 강화**
- 검색을 **숨김 필터 → 강조 방식**으로 변경: 비매칭을 숨기지 않고 매칭 행에 `.matched`(배경 강조) + 첫 매칭으로 `scrollIntoView`(smooth, center). 툴바에 「N건 매칭/매칭 없음」 표시.
- 검색+정렬+상태필터 동시 동작(필터→정렬된 목록 안에서 강조).

**검증**: `npm run build` 성공. `normalized.json` 노드 키=canon소문자·`canonical`=표시명 확인(focus 로직 전제 일치).

## 2026-06-17 — 검증 후 사소 정리 2건 (verify 전제 명시 + 오프라인 보고 정직화)

핸드오프(선행 1858cf7) 무해 관찰 2건. 동작 회귀 없음, 문서·문구 수준.

**C1 `graphdb/verify.py` docstring** — verify 는 *대조기*지 *빌더*가 아님을 명문화. 단독 실행 전 `normalize_v2.py` 로 오라클(`normalized_v2.json`) 최신화 필요. API lexicon 편집(patch/merge)은 오라클을 갱신하지 않으므로 편집 직후 verify 단독 호출 시 stale 오라클과 비교해 FAIL 가능(드리프트 아님). `/api/rebuild` 는 normalize→load→verify 순서라 무관. 코드 무수정.

**C2 `agent_collect.py` `gnode_report`** — 추출 성공 보고 문구를 `is_offline()` 로 분기. 오프라인(eval)은 실제 쓰기가 스킵되는데도 "반영 완료"로 찍혀 eval 로그가 거짓을 말하던 문제. 오프라인 분기만 「오프라인(eval) — Neo4j 미반영, rebuild 시 정본에서 합류」로 정직화. 라이브 분기는 「Neo4j 반영 완료」로 종전과 byte-동일(`is_offline` 은 이미 import 됨).

**검증**: `verify.py` exit 0 / `--audit` exit 0. `normalize_v2.py` 재실행 후 `normalized_v2.json` git-clean(골든 byte-동일). 오프라인 eval 1회(`ATLAS_OFFLINE` 기본) → 보고에 "Neo4j 미반영" 정직 표기 + 개념노드 N 전후 불변(125→125, 격리 유지) + `git status` 클린(eval restore). 라이브 문구 무회귀(f-string 결과 byte-동일).

## 2026-06-17 — 잔여 HITL 확정: lexicon status 일괄 + 첫 그래프 변경

사용자 HITL 결정을 배치 경로(직접 lexicon 편집 + 전체 재빌드)로 적용. 증분 reject 미사용 — 전체 재빌드가 wipe+reload로 모든 status를 반영해 더 단순·검증가능.

**규칙**: `data/lexicon.json` techniques 중 status가 `unreviewed`/`pending`인 항목 전부 `approved`, 단 "RAG taxonomy" 하나만 `rejected`. status만 변경, 그 외 필드 불변(43줄 status-only diff).
- 변이 3건(block-sparse FlashAttention/PS+ Prompting/Llama 2-Chat)은 병합 안 함 — 같은 논문 내 구별되는 기여라 별개 노드 유지 → approved.
- "emergent abilities…"는 실재 명명 개념 → approved. "RAG taxonomy"는 서베이 내부 분류틀(재사용 개념 아님) → rejected.
- pending 7(RAGAS/TruLens/ARES/AttributionBench/RAGTruth/FL-RAG/DRAGIN)은 실재 RAG 생태계 → approved. builds_on로만 언급돼 정의 논문이 코퍼스에 없어 placeholder("빈 링") 노드가 됨 = "아직 안 모은 것을 딛고 섰다"는 위상 표시로 유용.

**status 분포**: approved 95→137, unreviewed 36→0, pending 7→0, rejected 23→24 (합 161 불변).
**그래프(재빌드)**: Concept 125→131(-RAG taxonomy, +7 placeholder), DEFINES 76→75, BUILDS_ON 120→127(raw)/121(view), 빈 링 49→56. "RAG taxonomy" 거부 부수효과: 정의 논문 2408.02854는 defines 0인 서베이 노드로 정상 잔존, home_concept 미설정 → stale 닻 없음(audit D 0건).

**경로 주의**: 재빌드 스크립트는 `src/normalize_v2.py`·`src/embed_nodes_v2.py`·`graphdb/load.py` (graphdb/normalize_v2.py 는 없음).

**검증**: verify exit 0(papers=false/true 모두 일치, 개념노드 131), `--audit` exit 0(드리프트 0). 골든 byte-동일은 의도적으로 깨짐(첫 그래프 변경) — 대신 기대 델타가 골든 역할로 정확히 일치. embeddings는 신규 0개라 불변.

## 2026-06-17 — 정답지 신규 21편 수집 (첫 실전 증분쓰기)

builds_on 추출 정확도 정답지(50편) 중 신규 21편을 arXiv ID로 직접 적재. 토픽검색·관문 없이 `extract_pipeline(aid, ledger)` 직접 호출(큐레이션은 ID 검증으로 종료 → 관문 불필요). 합성이 아닌 진짜 신규 논문으로 라이브 Neo4j `write_paper` 증분 경로를 처음 본격 가동.

**T1 ID 검증**(arXiv API): 21/21 통과. 19건 제목 키워드 일치, 2건은 제목이 약어 대신 서술형이라 초록으로 확정 — 2502.13957(초록에 "RAG-Gym"), 2504.14870(초록에 "OTC"/"Optimal Tool Call"). 불일치 0.

**T2 적재**(`scripts/ingest_goldset.py` 신규): 성공 21/21, 전부 Neo4j 반영. paper_type=technique 20 + survey 1(2501.09136 Agentic RAG Survey, defines 0 정상). 중복 0(사전 확인).

**T3 재빌드·검증**: `src/normalize_v2.py`→`embed_nodes_v2.py`(신규 임베딩 0 — 증분쓰기가 이미 채움)→`graphdb/load.py`. verify exit 0(papers=false/true 모두 일치), `--audit` exit 0(드리프트 0). **불변식 입증: 21회 증분쓰기로 만든 라이브 Neo4j == 배치 재빌드.**
- Paper 70→91(+21), Concept 131→157(+26), DEFINES 75→101(+26), BUILDS_ON 127→153(raw)/141(view).
- lexicon: unreviewed +26, pending +14(신규 개념 — 정상). approved/rejected 불변(137/24, 기존 결정 보존). 정답지(builds_on)는 per-paper JSON 기준이라 lexicon status와 무관 → 검수는 별도 단계.

**T4 로스터**(`eval/goldset/papers.json` 신규): 50편 못박음(new_collected 21 + from_corpus 29, 겹침 0, from_corpus 29/29 Neo4j 존재 확인). 라벨링 단계가 읽음.

**범위 밖**(다음): builds_on 라벨링, paper_type 채점, 모델 비교.

## 2026-06-17 — 정답지 50편 한글 번역 워크시트 (라벨링 준비)

goldset 50편의 abstract+intro를 한글 전문 번역한 라벨링 워크시트 생성. 입력은 이미 있는 `data/outputs/{id}.parsed.json`의 text(파이프라인이 본 그 텍스트, PDF 재수집 없음).

**무결성 원칙**: 워크시트에 파이프라인 추출 결과(builds_on/defines)를 절대 넣지 않음(독립 라벨링 보장). "진짜 builds_on" 칸은 빈 채로 두고 라벨링 세션에서 채움.

**번역 주체 변경**: 처음엔 `make_goldset_worksheets.py`가 gpt-5.4-mini로 배치 번역하게 했으나(45/50까지 진행됨), 사용자 요청으로 **중단하고 Claude Code가 직접 번역**하는 방식으로 전환(품질↑·별도 API비용 0). 스크립트는 번역 API 호출을 제거하고 placeholder(`<!-- TODO: 한글 번역 -->`)만 박는 스켈레톤 생성기로 축소.

**작업 방식**: 50편 중 2편은 직접, 나머지 48편은 **서브에이전트 6개(각 8편) 병렬**로 번역(사용자 제안). 각 에이전트에 동일 스타일 지침(전문번역·영문병기·고유명 보존·단락유지)과 무결성 규칙(placeholder 한 줄만 교체, builds_on 빈칸 유지) 전달.

**검증**: 50/50 생성, 잔여 placeholder 0, 로스터 ID 50/50 매칭, builds_on 칸 전부 빈칸(채워짐 0), 한글 번역 전부 존재(최소 1600자). 일부 원문(Toolformer/RAPTOR/ReasoningBank 등)은 parsed text 자체가 중간에 끊겨 그 지점까지만 번역됨 — 파이프라인 입력과 동일하므로 정답지 공정성엔 무관.

**범위 밖(다음)**: builds_on 빈칸 채우기(라벨링 세션, RUBRIC을 relate 프롬프트와 대조해 확정), 채점, 정답지 freeze.

## 2026-06-22 — builds_on 채점 스코어러 (eval/score_buildson.py)

frozen 정답지 50편 vs 파이프라인 출력(`data/outputs/{id}.relations.json`, relate 날것)을 정밀도/재현율로 측정하는 스크립트 신규. **측정 전용 — lexicon/labels/relate/normalize 무수정(읽기 전용).**

**핵심 변환**: 비교 전에 예측·정답을 `normalize_core.resolve()`로 rep_key 공간에 둠(alias 흡수+canon). 예측에만 status 필터(`status_of ∈ NODE_OK={approved,unreviewed}`) — pending/rejected/None은 그래프에 안 보이므로 채점에서도 탈락. gold는 표기만 정규화, status 필터 X. `normalize_paper`(Neo4j 쓰기) 안 씀 — frozen lexicon이 각 개념 최종 status를 이미 담음.

**FN 진단 분류**: FN이 raw 예측에 있으면 "추출O·lexicon탈락"(lexicon 리뷰 백로그 후보), 없으면 "추출X"(abstract-only 한계). 재현율 손실이 추출실패인지 미검수인지 가름.

**집계**: micro(TP/FP/FN 합산) + macro(논문별 평균; macro P 분모=pred≠∅, macro R 분모=gold≠∅로 empty gold 11편 제외). 전체/new_collected/from_corpus 3세트 분리.

**스모크(필수)**: `--run` 없으면 5편(SEARCH-R1/DeepSeek-R1/Toolformer/HippoRAG2/KG-R1) 손계산 예상값과 대조 PASS/FAIL. FAIL이면 `--run` 거부. → **5/5 PASS**.

**전체 결과(50편, 누락 0)**:
- 전체: micro P=0.562 R=0.683 / macro P=0.708 R=0.785. FN 19(lexicon탈락 3 + 추출X 16).
- new_collected(21): micro P=0.708 R=0.515 / macro P=0.792 R=0.654. FN 16(lexicon탈락 3 + 추출X 13).
- from_corpus(29): micro P=0.490 R=0.889 / macro P=0.651 R=0.886. FN 3(전부 추출X, lexicon탈락 0).
- 해석: from_corpus는 recall 천장 100%(정답 개념 전부 NODE_OK 생존) → 낮은 recall은 순수 추출실패. new_collected는 lexicon 미검수(pending)로 천장이 눌림 + 형제(related work) 추출X가 다수. FP는 from_corpus 멀티에이전트 논문(Reflexion/MetaGPT/Voyager)에서 baseline·형제 과추출이 집중.

**출력**: 콘솔(3세트 표 + FP 전체 + FN 전체 진단) + `eval/runs/score_buildson_{ts}.json/.md`(rep_key→라벨 변환 저장).

실행: `uv run python eval/score_buildson.py` (스모크) / `--run` (전체).

## 2026-06-22 — builds_on 채점 결과 항목별 분석 리포트 (eval/report_buildson.py)

채점기(score_buildson.py) 결과를 **사람이 읽는 분석 문서**로 렌더링. 측정은 끝났고 이건 결과를 항목 단위로 푸는 작업 — 데이터·점수 무수정. 계산은 normalize_core 그대로 재사용(재발명 X), §8 기대 숫자 6항목 재현 검증 후에만 산출(불일치 시 중단).

**산출물(eval/reports/, gitignore 아님 — 추적 확인):**
- `buildson_analysis_v1.md` — 용어풀이→점수요약→논문별 상세표 50편→FP 3분류→FN 2분류→해석.
- `buildson_items_v1.csv` — 항목 1줄(92행=ΣTP41+FP32+FN19). paper_id,title,group,concept,verdict,fn_reason,fp_category,concept_status.

**FP 3분류(32건)** — "정밀도를 싸게 고칠 수 있나"의 답:
- component_tool 5(PPO/MCTS/RAGAS/ARES/TruLens) — 계보 아님 → lexicon reject로 싸게 제거.
- substrate 4(GPT-3/BERT류) — 백본, DPR·ColBERT엔 정답이라 전역 reject 불가(문맥의존).
- method_misjudged 23(Self-RAG/ReAct/AutoGPT 등) — 진짜 방법인데 이 논문선 baseline. lexicon으로 못 고침 = relate 판단 문제. **다수.**

**FN 2분류(19건)**: lexicon_dropped 3(DeepSeek-V3-Base/KG-RAG/TIRESRAG-R1, 전부 pending → 검수하면 복구) + not_extracted 16(abstract-only 형제계보 누락).

**결론(문서 §5)**: 싸게 고칠 수 있는 건 소수(lexicon_dropped FN 3 + component_tool FP 5 = 사전작업). 점수를 좌우하는 다수(method_misjudged FP 23 + not_extracted FN 16)는 abstract+intro 입력의 본질적 한계 → 다음 레버는 lexicon이 아니라 relate가 보는 범위/맥락.

실행: `uv run python eval/report_buildson.py`.

## 2026-06-22 — full 라이브 승격 (relate만) + 그래프 재빌드

모델 비교 결론(full이 builds_on 정밀도 +0.20, 비용 <$1)에 따라 **라이브 relate를 gpt-5.4(full)로 승격**. 범위는 relate만 — extract는 검증 구성대로 mini 유지(개념/노드 불변), evidence·RW 미사용.

**config 분리**: `MODEL` → `MODEL_EXTRACT="gpt-5.4-mini"` + `MODEL_RELATE="gpt-5.4"`. extract.py/relate.py 호출부 분기, relate에 `temperature=0` 추가. 가드: src/의 config.MODEL 참조는 extract·relate 둘뿐.

**세팅(새 머신)**: uv sync, .env(시크릿, gitignore 확인), Neo4j docker 기동 + verify_connectivity OK, outputs parsed/concepts/relations 91편 확인 → 게이트 통과.

**relate 재실행**: `eval/run_relate_full.py`(ThreadPool 8워커)로 91편 full,temp=0 재호출 → relations.json 덮어쓰기. ok=91 fail=0(파싱실패 0). mini 백업은 /tmp.

**재빌드**: normalize_v2(노드218/엣지209) → embed_nodes_v2(194,dim1536) → load.py(Neo4j: Paper91/Concept127/관계208).

**승격 게이트(핵심)**: goldset 50편 새 relations 기준 재채점 → 전체 micro **P 0.820 / R 0.833**. 검증값 model_full_t0(P 0.803/R 0.817)과 거의 동일(미세 상회, temp=0 9/10 결정성 범위). → 검증한 full@0 구성을 그대로 승격 확인. (주: score_buildson.py SMOKE는 mini 기대값 하드코딩이라 개선방향으로 불일치 → run_full 직접 호출로 집계. 게이트 기준은 집계지 SMOKE가 아님.)

**mini→full 변화**: builds_on 집합 변경 69/91편, 엣지 총합 196→137. full이 더 보수적·정밀(선조 나열 FP 제거 = 정밀도 +0.20 출처). 예: Attention paper builds_on []로.

산출물: src/config·extract·relate, data/outputs/*.relations.json(91 교체), normalized_v2.json, node_embeddings_v2.json, Neo4j 적재, eval/reports/full_promotion.md, eval/run_relate_full.py, eval/runs/score_buildson_20260622-171113.*.

## 2026-06-22 — 의미검색을 명령창 오케스트레이터에 배선

지형도 명령창에 사용자가 주제를 자유 문장으로 묘사하면, 필터 에이전트가 임베딩 유사도로 지도에 *이미 있는* 개념·논문을 찾아 하이라이트. 새 탭 없음, collect(arXiv 신규 수집)와 구분. **읽기 전용 + 배선** — 코사인/임베딩 로직 재구현 없이 agent_collect의 검증 부품(load_embeddings/embed_query/match) 재사용.

**변경 4파일**:
- `agent_filter.py`: TOOLS에 `semantic_search` 추가. 스모크를 Type B 6케이스 PASS/FAIL로 교체(1·6은 collect로 새면 안 되는 하드 기준).
- `prompts/filter/command.py`: 라우팅 경계 명시 — filter는 구조속성(type/domain/year)만이며 인자 못 채우면 금지(자유 주제 묘사 → semantic_search), 명시적 fetch 동사(모아줘/수집/긁어와/추가)는 collect로 decisive, 그 외 애매하면 semantic_search 기본.
- `api/main.py`: 임베딩 행렬 1회 캐시(`_emb`) + 키매핑(`_to_front_id`: concept:rk→rk, paper:는 그대로). `/api/command`에 semantic_search 분기 — 매칭(top8/floor0.30) 후 **라이브 그래프(papers=True 노드셋)에 실재하는 id만** 반환(유령노드 방지). 논문 검증은 papers=False 기본뷰엔 논문이 없어 papers=True로 별도 조회.
- `web/src/routes/Graph.jsx`: handleResult에 semantic_search 분기 — 기존 `highlight(ids)` 재사용, 칩 `검색="..."`, 무매칭 시 "유사한 노드 없음", 논문 hit 있는데 '논문 보기' 꺼져있으면 안내(자동 토글 안 함).

**핵심 함정(키 공간 2개)**: 매칭은 `concept:rk`/`paper:id`, 프론트 graph_view는 개념을 접두사 없이(rk), 논문은 `paper:id`. 접두사 제거 매핑 + 실재 노드 검증.

**열린 판단**: semantic_search vs collect 애매 시 기본=semantic_search 유지(수집은 비용·파괴적). 단 명시적 fetch 동사는 collect 우선(스모크 #4 보장).

**검증**: 라우팅 스모크 6/6 PASS. 라이브 "검색하면서 추론하는 방법 있어?" → semantic_search, 개념6+논문6 실제 id 하이라이트. off-topic "양자컴퓨터…" → 빈 결과(→유사 노드 없음). web build 통과.

실행: `uv run python agent_filter.py`(라우팅 스모크). 라이브: dev.sh.

## 2026-06-22 — 수집 에이전트를 채팅 [수집] 서브탭으로 분리

채팅 패널을 [명령]/[수집] 두 탭으로 분리. [명령]=filter/lineage/reset/semantic_search(기존). [수집]=수집 에이전트를 자체 입력창으로 시작·진행. 명령창에서 collect 라우팅을 제거해 semantic↔collect 애매함을 라우팅(LLM)이 아니라 탭(물리적)으로 제거. 수집 흐름 로직(agent_collect)은 무수정 — 트리거 위치 이전 + 채팅 UI 재구성.

**변경 4파일**:
- `agent_filter.py`: TOOLS에서 collect 도구 삭제(4개만 남음: filter/focus_lineage/reset/semantic_search). 스모크 #4 '모아줘' 기대값 collect→None(도구 없이 안내). 1·6 semantic_search 유지.
- `prompts/filter/command.py`: collect 라우팅 삭제. fetch 의도(모아줘/수집/긁어와/추가)는 도구 안 부르고 평문 안내 — "새 논문 수집은 [수집] 탭에서 진행하세요."
- `web/src/routes/Graph.jsx`: (1) activeTab 상태 command|collect. (2) 메시지 분리 — messages=명령 탭(localStorage chatMessages), collectMessages=수집 탭(신규 키 collectMessages, 별도 저장 useEffect). loadMessages(key) 일반화. addCollectMsg 신설 후 collect 핸들러 addAgent→addCollectMsg. (3) runCommand에서 collect 가드/분기 제거(명령 탭은 수집과 독립). (4) 복원 함정: 마운트 복원 성공+미완료면 setActiveTab("collect"), startCollect도 수집 탭 전환, collect 활성+다른 탭이면 수집 탭 라벨에 ● 점. (5) 입력창 2개: 명령(sendCommand, disabled=pending) / 수집(sendCollect, !collect일 때만 활성, 흐름 중엔 카드 버튼). (6) chat-msgs/입력 form을 activeTab으로 스위치. (7) clearActiveChat — 탭별 비우기(수집 흐름 중엔 수집 탭 비우기 disabled).
- `web/src/styles.css`: .chat-tabs/.chat-tab/.active/.tab-dot (기존 .nav 톤 재사용).

**검증**: 라우팅 스모크 6/6 PASS(#4 None, 1·6 semantic_search). 라이브: "모아줘"→tool:null + "[수집] 탭에서 진행하세요" 안내. "검색하면서 추론"→semantic_search(개념8·논문8). collect/start→interpret interrupt 정상(thread_id+actions). web build 통과. 복원 자동 전환/탭 이력 분리는 코드 경로 확인(수동 UI 확인 권장).

## 2026-06-22 — 질의 탭 → 클릭형 [사용법] 페이지로 교체

어긋난 placeholder `질의` 탭(/search, "준비 중")을 [사용법] 페이지로 교체. 처음 보는 사람이 "뭘 물어볼 수 있나"를 평범한 말 표로 보고, 예시 칩을 누르면 지형도로 이동해 그 질문이 자동 실행(맵 반응). 도구 이름 노출 없음. 프론트 전용 — 백엔드/파이프라인 무수정.

**변경(프론트 5파일)**:
- `web/src/routes/Usage.jsx`(신규, Search.jsx 대체): 안내 한 줄 + 6행 표. "이렇게 물어보세요" 칸 문구가 클릭 칩. run 칩→`navigate("/graph",{state:{run}})`, collect 칩→`{state:{collectTopic}}`. useNavigate.
- `web/src/App.jsx`: import/라우트/NavLink Search→Usage, `/search`→`/usage`, 라벨 질의→사용법. Search.jsx 삭제.
- `web/src/routes/Graph.jsx`: useLocation/useNavigate. ready 상태(데이터 로드 effect에서 apiRef 세팅 직후 setReady(true)) + consumedRef로 들어온 state 1회 소비. run→runCommand 즉시 실행, collectTopic→수집 탭 전환+setCollectInput prefill(자동 시작 X, destructive라 사람이 [시작]). 실행 후 navigate replace state:null로 재실행 방지.
- `web/src/styles.css`: .usage-page/intro/table/chips/chip(+collect). 기존 example-chip/nav 톤 재사용.

**라이브 검증(API+그래프로 클라 하이라이트 로직 재현, 11칩 전부 >0 확인)**:
- 깨진 칩 2개 교체: "지식그래프로 답 보강하는 연구"(semantic 0)→"그래프 기반 검색 증강 생성"(c8+p8). "Self-RAG"→"GraphRAG"(focus_lineage 6) — Self-RAG는 rk='self rag'(하이픈→공백)인데 chat은 canonical 'Self-RAG'로 라우팅→클라 nodes[rk] 미스(기존 하이픈 키 불일치, 범위 밖). clean rk 이름으로 교체.
- 결과: 검색16 / 그래프검색16 / RAG계보36 / ReAct계보2 / CoT계보8 / 2024+ 54 / 의료 3 / GraphRAG 6 / Toolformer 1 / 다보여줘 reset / 모아줘 collect칩(수집탭 prefill). web build 통과.

**남은 사전 이슈(기록만)**: focus_lineage가 backend는 canonical로 검증하나 client lineageSets는 rk(노드 id)로 조회 → 하이픈/공백 들어간 이름(Self-RAG 등)은 chat 계보 명령이 클라에서 미스. 별도 수정 대상.

## 2026-06-22 — [사용법] UI 다듬기 + 기본 페이지화 + 로고 클릭

직전 사용법 페이지가 "대충한 느낌"(밋밋한 표)이라 폴리시. 기능/칩 검증값은 동일, 표현만 개선.
- `App.jsx`: 기본 라우트 `/`→`/usage`(온보딩), 로고를 `<Link to="/usage">`로(클릭 시 사용법). nav 순서 사용법/지형도/사전.
- `routes/Usage.jsx`: 표→카드 그리드. 히어로(h1 "이렇게 물어보세요" + 설명), 카드마다 제목+힌트+보기/수집 배지+칩+효과(→ 화살표). collect 카드는 점선·그라데이션으로 구분.
- `styles.css`: usage-hero/grid/card/badge/hint/chip/effect 신규. 칩은 pill+hover fill, 카드 hover lift+shadow, color-mix로 accent 톤. 로고 hover opacity.
- 검증: web build 통과. (브라우저 스크린샷 툴 없어 클래스 매칭+빌드로 확인 — 실물은 dev.sh 권장.)

## 2026-06-22 — 로고 개선

밋밋·전부소문자 로고 교체. SVG 지식그래프 마크(3노드 별자리, 하단 노드 accent 채움) + 워드마크 "Research Atlas"(Research=텍스트색 600, Atlas=accent 700). hover 시 마크 살짝 회전·확대. App.jsx 마크업 + styles.css(.brand-mark/.brand-word). web build 통과.

## 2026-06-22 — lineageSets 하이픈 이름 버그 수정 (전 기록한 사전 이슈 해소)

focus_lineage가 canonical("Self-RAG")로 들어오는데 lineageSets가 toLowerCase로만 조회해 rk(노드 id, "self rag")와 불일치 → 하이픈/특수문자 든 노드(Self-RAG/KG-RAG/R1-Searcher 등)는 계보 명령이 클라에서 조용히 실패하던 문제.
수정(프론트 1함수): lineageSets 첫머리에서 node→id 해소 — 직접 키 → 소문자 키 → canonical 소문자 매칭 순, 못 찾으면 null. traversal은 그대로. 백엔드 무수정.
검증(API+그래프로 재현): Self-RAG→id 'self rag' 조상2·자손2(전엔 MISSING), KG-RAG/R1-Searcher 해소 OK, RAG 36(하이픈없는 기존 동작 회귀 없음), 없는노드→null. web build 통과.

## 2026-06-22 — [사용법] 배경 장식(지식그래프 별자리 SVG)

밋밋한 배경에 앱 정체성(논문 지형도)에 맞는 SVG 별자리 backdrop 추가. 결정적 의사난수로 노드 30개 흩뿌리고 거리<175 쌍을 연결(가까울수록 진하게), accent(#2563eb) 저투명도. top-right/bottom-left 부드러운 radial glow 2개.
- 레이아웃: usage-bg는 position:fixed(스크롤해도 제자리), z-index:0. usage-inner z-index:1(콘텐츠 위). nav position:relative z-index:5(배경이 nav 위로 안 올라오게). pointer-events:none.
- 카드: frosted glass — rgba(255,255,255,.82)+backdrop-filter blur로 별자리가 카드 뒤로 은은히 비침. collect 카드 점선/그라데이션 구분 유지.
- Usage.jsx에 useConstellation(useMemo) 생성기. web build 통과. (스크린샷 툴 없어 빌드/코드로만 확인 — 실물 dev.sh 권장.)

## 2026-06-22 — [사전] UI 개선 + AI도우미/재빌드 버튼 제거

- 액션 칼럼의 비활성 "AI 도우미"(준비중 placeholder) 삭제. 병합 버튼만 남기고 컴팩트화.
- 그래프 재빌드 버튼 + "재빌드해야 반영" 안내 제거(사용자 판단: UI에서 불필요). rebuild import/state/함수 제거. /api/rebuild 엔드포인트·api.js 래퍼는 유지(백엔드 무수정).
- 페이지 헤더 추가(h1 "사전" + 한 줄 설명) — Usage/지형도와 톤 통일.
- 상태 필터를 세그먼티드 컨트롤로(--hover 배경 그룹 + 활성칩 패널+그림자). 검색창 폭, 우측에 "총 N개 · 표시 M" 카운트(재빌드 자리 대체).
- web build 통과. (스크린샷 툴 없어 빌드/코드 확인 — 실물 dev.sh 권장.)
- 참고: 재빌드 버튼 제거로, pending→approved 승인이 그래프에 반영되려면 CLI 재빌드(normalize_v2→load) 필요. reject/정의수정/병합은 기존대로 증분 동기화됨.

## 2026-06-22 — 지형도 수동 컨트롤(filter 드롭다운 + 노드클릭 계보 + 초기화)

채팅으로만 되던 조작을 수동 UI로도. 새 기능 아님 — 기존 applyFilter/lineageSets/highlight에 수동 진입점만 추가. 프론트 전용(Graph.jsx+styles.css).
- 상태모델: filterState({ptype?,domain?,date_after?})를 filter 차원 단일 진실원. setFilter(next)가 정리→빈값이면 전체복원, 아니면 applyFilter→highlight+chips. 드롭다운·채팅 filter·초기화 모두 setFilter 경유(effect 경쟁 없음). lineage/semantic은 자기 highlight 직접 세팅+setFilterState({})(표시만 동기, effect 안 터짐).
- handleResult: filter→setFilter(args), reset→setFilter({}) 로 교체(중복 제거, filterSummary 삭제). focus_lineage/semantic_search 끝에 setFilterState({}).
- 컨트롤 바(하단중앙 플로팅): 유형/분야/시점 드롭다운(옵션은 로드된 개념노드에서 동적 생성 — 하드코딩 없음) + 초기화. filterState로 controlled → 채팅↔드롭다운 양방향 동기.
- 노드클릭 계보: 개념 디테일 패널에 [조상][자손][양쪽] → runLineageFromNode(selected.id, dir). selected.id는 rk라 하이픈 무관. 논문 패널엔 없음.
- 칩 ✕/명령탭 비우기도 filterState 리셋 동기.
- 검증(API+그래프 재현): 옵션 동적(ptype 3·domain 6·year 2017~2026), medical=3, 2024이후=54, technique+2024 AND=52. web build 통과.

## 2026-06-22 — [사전] 상태 설명 + 페이징 + 검색 동작 개선

- 상태 설명 추가: 헤더에 "상태 설명 ▾" 토글(기본 펼침) + 범례 — approved/unreviewed/pending/rejected 각 의미와 그래프 표시여부(NODE_OK=approved/unreviewed) 명시. 코드 근거: normalize_core(정의→unreviewed, 참조→pending, NODE_OK만 노드).
- 페이징: PAGE_SIZE=50. filtered→정렬→슬라이스. 필터/검색/정렬 바뀌면 1페이지로. pager 행("a–b / N", ‹이전 X/Y 다음›). safePage로 항목 감소 시 클램프.
- 검색 동작 변경: 기존 "강조+스크롤"(matchSet/firstMatchRef) → 목록 좁히기(filter). 페이징과 자연 결합. firstMatch 스크롤 머신/ useRef 제거. matched 행 강조 제거.
- 카운트: 검색 시 "N건", 우측 "총 N개 · 조건 M".
- web build 통과.

## 2026-06-22 — 전체 가독성 개선 + 문서화 패스(HOW_IT_WORKS/README)

UI 가독성: 전반적으로 글자가 작다는 피드백 → base 14→15px + line-height 1.5, 컨트롤(button/input/select/textarea) 13→14px·패딩↑, badge 11→12px, 테이블 셀 패딩 6/8→9/11, 노드 라벨 13→14px, 채팅 버블 여백↑. styles.css만.

문서화(코드 무수정):
- docs/HOW_IT_WORKS.md 신규 — 기능별 동작 메커니즘 전체(화면/백엔드/평가). 기준 5cd3e46.
- README.md 재작성 — 처음 보는 사람·리뷰어용. 왜 중요/핵심 결과(P0.82 R0.83·측정으로 결정)/실행(./dev.sh)/화면/구조+링크. stale 4곳 제거(/search 질의→/usage, 재빌드 버튼 문구 삭제, nav 순서 사용법/지형도/사전, --reload 단독→dev.sh).
- docs/ontology/README.md 상단에 "⚠️ legacy" 배너.
- FEATURES.md 안 만듦(HOW_IT_WORKS가 대체). 상호 링크 깨짐 0, web build 통과.

## 2026-06-22 — UI 개선 일괄(다크모드 제외) + 사용법 행 정리

리스트업했던 개선점을 다크모드(#4)·데모GIF(#17, 녹화 필요) 빼고 전부 구현. 3페이즈로 커밋.
- 전역/nav: :focus-visible 포커스 표시, 컨트롤 트랜지션, nav 활성/hover 강조, 반응형 @media(820/520; 지형도 세로적층·사전 테이블 가로스크롤·사용법 1열·모바일 nav), prefers-reduced-motion.
- 지형도: 디테일 패널 좌상→우(검색박스 충돌 해소), 줌아웃 시 라벨 자동숨김(k<0.6), 계보 방향색(조상 파랑/자손 주황/시작 강조 — highlightLineage, lineageSets가 ancSet/descSet 반환), 컨트롤바 '필터' 라벨 + 논문보기 토글을 범례→컨트롤로 이동, 로딩 오버레이.
- 사전: 병합을 window.prompt→검색형 모달, 행에 빠른 승인/거부 버튼, 정의 dirty 시각화(테두리+안내), 페이지크기 선택(25/50/100)+하단 페이저, 로딩 스피너.
- 사용법: 사소한 3행 삭제(조건으로 좁혀보기/이름 정확히 알때/전체 되돌리기) → 의미검색·계보·수집만 남김.
- 가독성(직전): base 15px 등.
- web build 통과. (스크린샷 툴 없어 빌드/코드로만 확인 — 실물 dev.sh 권장.)
