# prompts/ — 프롬프트 → 에이전트 → 적용 위치

모든 LLM 프롬프트를 **목적(에이전트)별 하위 디렉토리 + 한 프롬프트당 한 파일**로 모은 패키지.
각 파일 상단에 5줄 메타(`[단계]/[언제]/[입력]/[출력]/[의도]`) + `[한글 번역]` 주석이 있다.

```
prompts/
  paper_type_criteria.py   # 공유 조각 (extract·gate가 함께 참조 → 최상위에 둠)
  pipeline/  extract.py  relate.py            # ① 추출 파이프라인
  collect/   gate.py  intent.py  report.py  expand.py   # ② 수집 에이전트
  filter/    command.py                        # ③ 필터 에이전트
```

프롬프트를 쓰는 주체는 셋이다 — **① 추출 파이프라인**, **② 수집 에이전트**, **③ 필터 에이전트**.
아래 표가 "어떤 프롬프트가 어떤 에이전트를 만들고, 그게 어디에 적용되는지"의 한눈 지도다.

## 한눈 매핑

| 프롬프트 파일 | 주요 심볼 | 쓰는 코드(함수) | 에이전트 | 적용 표면 (API / 화면) |
|---|---|---|---|---|
| `paper_type_criteria.py` | `PAPER_TYPE_CRITERIA` | (조각) `pipeline/extract`·`collect/gate`가 import | 공유 | — (단일 출처 조각) |
| `pipeline/extract.py` | `EXTRACT_SYSTEM/USER/SCHEMA` | `src/extract.py: extract_one()` | ① 추출 파이프라인 | `uv run python src/extract.py` · ②의 추출 단계가 재사용 |
| `pipeline/relate.py` | `RELATE_SYSTEM/USER/SCHEMA` | `src/relate.py: relate_one()` | ① 추출 파이프라인 | `uv run python src/relate.py` · ②의 추출 단계가 재사용 |
| `collect/intent.py` | `INTENT_SYSTEM` | `agents/collect.py: parse_intent()` | ② 수집 에이전트 | `POST /api/collect/start` ← `/graph` 채팅(수집 명령) |
| `collect/report.py` | `REPORT_SYSTEM`, `build_report_user()` | `agents/collect.py: build_status_report()` | ② 수집 에이전트 | 같은 흐름의 **interpret** interrupt 카드(한국어 보고) |
| `collect/expand.py` | `EXPAND_SYSTEM`, `build_expand_user()` | `agents/collect.py: expand_query()` | ② 수집 에이전트 | `proceed` 후 arXiv 검색 직전 |
| `collect/gate.py` | `GATE_SYSTEM/USER`, `GATE_PROMPT_VER` | `agents/collect.py: gate_classify()/gate_one()` | ② 수집 에이전트 | **approve** 승인 후 관문 판정 |
| `filter/command.py` | `build_system_prompt(names)` | `agents/filter.py` → `api/main.py` | ③ 필터 에이전트 | `POST /api/command` ← `/graph` 채팅(화면 조작 명령) |

> 언어: `extract`/`relate`는 영문 프롬프트. `extract`는 동작 불변(byte-동일 유지),
> `relate`는 lineage-only로 전환됨(점수비교 baseline 제외, 입력에서 problem/domain 제거). `gate`/`intent`/`report`/
> `expand`/`command`는 지시문 영문. 단 **`report`는 출력이 한국어**(프론트가 그 보고를 그대로 표시),
> **`command`는 사용자 한국어 트리거 단어(보여줘/가져와…)를 유지**한다.

---

## ① 추출 파이프라인 (배치)

`fetch → parse → extract → relate → normalize_v2 → embed_nodes_v2`. 논문 PDF에서 노드/계보를 뽑는다.

- `pipeline/extract.py` 프롬프트 → `src/extract.py`: 논문 본문에서 `defines/uses/problem/domain/paper_type` 추출.
- `pipeline/relate.py` 프롬프트 → `src/relate.py`: `builds_on`(방법적으로 딛고 선 선행 기법 — lineage-only, 점수비교 baseline 제외) 식별.
- **적용**: 배치 실행(`uv run python src/extract.py [--run]`). 결과는 `*.concepts.json`/`*.relations.json`.
  이 두 프롬프트는 ②의 추출 단계에서도 그대로 재사용된다(같은 함수 호출).

## ② 수집 에이전트 (`agents.collect`, LangGraph)

"말로 부리는 수집". 사용자가 채팅으로 주제를 던지면 arXiv에서 찾아 관문을 통과한 것만 지도에 추가한다.
사람 개입(interrupt) 3곳에서 멈춘다.

```
parse ─▶ confirm_interpret ⏸interpret ─▶ expand_search ─▶ approve ⏸approve ─▶ gate
                                                                                  │
                  report ◀─ extract ◀─ confirm_extract ⏸extract_confirm ◀────────┘
```

| 그래프 노드 | 쓰는 프롬프트 |
|---|---|
| `parse` | `intent`(의도 파싱) + `report`(현황 보고) |
| `expand_search` | `expand`(arXiv 검색어 확장) |
| `gate` | `gate`(초록만 보고 1차 판정 — technique만 통과) |
| `extract` | `extract` + `relate`(① 파이프라인 함수 재사용) |
| `report` | (LLM 없음 — 최종 요약 텍스트 조립) |

- **적용 API**: `POST /api/collect/start`(첫 interrupt까지) · `POST /api/collect/resume`(결정 주입).
- **화면**: `/graph` 채팅 패널. 필터 에이전트가 `collect` tool로 라우팅하면 이 흐름으로 진입하고,
  interrupt 3곳(`interpret`/`approve`/`extract_confirm`)이 버튼 카드(`CollectCard`)로 뜬다.
- `GATE_PROMPT_VER`: 관문 프롬프트가 바뀌면 올린다(현재 `gate-v2`). `papers.json`의 옛 버전 판정은
  자동 재판정된다.

## ③ 필터 에이전트 (`agents.filter`)

자연어 화면 조작 명령을 tool call로 번역한다(실행은 프론트가 함).

- `filter/command.py`의 `build_system_prompt(names)` → `api/main.py`의 `/api/command`가 매 호출 시
  현재 개념 이름 목록(`names`, Neo4j에서 조회)을 끼워 시스템 프롬프트를 만든다.
- 라우팅: 보여줘/강조/필터/계보 → `filter`·`focus_lineage`·`reset`, 가져와/수집/찾아와 → `collect`
  (→ ② 수집 에이전트로 넘어감).
- **적용 API**: `POST /api/command`. **화면**: `/graph` 채팅 패널(`runCommand`).
