# WORKLOG

세션 인계용 개선 로그. 최신이 위.

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
