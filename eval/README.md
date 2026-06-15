# eval/ — 수집 에이전트 diff 테스트 (rough)

같은 질문으로 수집 에이전트를 돌렸을 때 **기존 지도(데이터)에 무엇이 추가됐는지(diff)** 를 보는
반자동 스크립트. 한 번 실행 = 한 회차. 데이터는 매번 **원상복구**되어 다음 실행도 같은 출발점.

> **성격**: 2026-07 정식 평가의 *rough 선행 버전*. 격리 반복 자동 N회 루프·일관성 메트릭·정답지
> 대조는 범위 밖(7월). 지금은 "한 회차가 알아서 도는 반자동"까지.

```
eval/
├─ test_collect.py   # 스크립트(1회차 = 백업→자동수집→normalize→diff→복원)
├─ runs/             # 회차 산출물 {timestamp}.json  (gitignore)
└─ README.md         # 이 문서
```

---

## 한 회차가 하는 일

```
1. 백업    data/outputs/ 통째 + data/lexicon.json → data/_snapshot_test/ (원자적)
2. 기준선  normalized_v2.json 의 개념/논문/계보 + lexicon status 를 메모리에 로드
3. 수집    build_collect_graph(MemorySaver()) + _run_scenario(…, ["proceed"×3])
           → interrupt 3개(해석·물량·추출 승인) 자동통과, 추출까지(MAX_EXTRACT 상한)
4. 반영    subprocess: uv run python src/normalize_v2.py  (추출분 → 노드/lexicon)
5. diff    normalized_v2.json 재로드 → 기준선과 비교: +개념 / +논문 / +계보 / +lexicon
           → 콘솔 출력 + eval/runs/{timestamp}.json 기록
6. 복원    finally: data/_snapshot_test/ → 되돌리고 스냅샷 정리,
           이번 회차가 새로 받은 PDF만 삭제 → data/ 원상복구
```

수집 로직·프롬프트·그래프 정의는 **건드리지 않고** `agent_collect.py` 의 기존 함수를 호출만 한다.

---

## 사전 준비

- `uv` 설치(이 레포의 표준 실행기).
- 레포 루트 `.env` 에 `OPENAI_API_KEY` (수집이 LLM·임베딩을 부름).
- 네트워크: arXiv 메타 검색 + PDF 다운로드. arXiv rate limit 때문에 검색어 사이 3초 간격 → 한 회차에
  대략 1~2분.
- **비용 주의**: 실제 OpenAI 토큰을 쓰고 PDF를 최대 `MAX_EXTRACT`(현재 2)편 받는다. 공짜 아님.

---

## 실행 (레포 루트에서)

```bash
# 1회차
uv run python eval/test_collect.py "llm 에이전트 메모리 관련 조사해줘"

# 여러 질문 — 줄단위, 각각 독립 회차(매번 복원). '#' 주석/빈 줄 무시
uv run python eval/test_collect.py --query-file eval/queries.txt
```

`queries.txt` 예시:

```
# 한 줄에 질문 하나
llm 에이전트 메모리 관련 조사해줘
검색 노이즈에 강건한 RAG 기법 찾아줘
```

> 같은 질문을 자동으로 N번 반복하는 루프는 **범위 밖**(7월). 지금은 질문당 1회차.

---

## 출력

### 콘솔 (수집 진행 로그 뒤)

```
질문: "llm 에이전트 메모리 관련 조사해줘"   (2026-06-16 02:29:32)
+ 개념 1:  gaze heads
+ 논문 2:  2606.14703, 2606.14704
+ lexicon: unreviewed 신규 1  (검수 대기)
복원 완료 — data/ 원상복구.
```

추가가 없으면 `+ 추가 없음 (전부 기존/dedup)`.

### 파일 `eval/runs/{timestamp}.json`

콘솔과 동일 내용을 구조화 저장(나중 회차 비교용 — 7월 토대). 실제 예시:

```json
{
  "query": "llm 에이전트 메모리 관련 조사해줘",
  "time": "2026-06-16T02:29:32",
  "added_concepts": ["gaze heads"],
  "added_papers": ["2606.14703", "2606.14704"],
  "added_edges": [],
  "lexicon_added": ["Image Heads", "Localization Heads", "gaze heads"],
  "lexicon_new_unreviewed": ["gaze heads"]
}
```

| 필드 | 뜻 |
|---|---|
| `added_concepts` | 이번 수집으로 새로 생긴 개념(canonical 이름) |
| `added_papers` | 새로 들어온 논문 arXiv ID |
| `added_edges` | 새 개념간 계보 `"A → B"` (paper→concept 엣지에서 유도) |
| `lexicon_added` | lexicon 에 새로 등록된 개념 이름 전체 |
| `lexicon_new_unreviewed` | 그중 `unreviewed`(검수 대기) — 보통 새 추출 개념 |

> 참고: `added_concepts` ⊆ `lexicon_added`. lexicon 에는 올랐지만 노드 자격(status) 못 갖춰
> 지도에 안 뜬 개념이 있을 수 있어 둘이 다를 수 있다(위 예시: lexicon 3 vs 개념 1).

---

## 데이터 안전 (최우선 보장)

- **try/finally**: 수집~diff 를 try, 복원을 finally → 에러·`Ctrl-C` 무엇에도 복원 실행.
- **원자적 스냅샷**: `data/_snapshot_test.tmp/` 에 쓰고 완료 후 `rename` → `_snapshot_test/` 이름이
  보이면 항상 *완전한* 백업(부분 스냅샷 방지).
- **preflight**:
  - 남은 `.tmp`(백업 도중 죽은 흔적) 청소.
  - 완료 스냅샷이 남아있으면(직전 실행이 복원 못 하고 종료) → 그게 pristine 본이므로 **먼저 복구** 후 진행.
  - `git status --porcelain data/` 에 커밋 안 된 변경이 있으면 경고(스냅샷/복원이 덮을 수 있어서).
- **PDF**: 백업 범위 밖(`data/pdfs/`, gitignore·재다운로드 가능)이지만, 회차가 *새로 받은 것만*
  finally 에서 삭제(기존 캐시는 보존).

복원 검증(직접):

```bash
# 실행 전후로 data/ 가 동일해야 정상
git status --porcelain data/      # 비어 있으면 OK
```

### 만약 복원 전에 강제 종료돼서 데이터가 꼬였다면

`data/_snapshot_test/` 가 남아 있으면 그게 직전 pristine 본이다. 다시 한 번 스크립트를 실행하면
preflight 가 **자동 복구**한다. 수동으로 되돌리려면:

```bash
rm -rf data/outputs && cp -r data/_snapshot_test/outputs data/outputs
cp data/_snapshot_test/lexicon.json data/lexicon.json
rm -rf data/_snapshot_test
```

---

## 동작 원리 메모

- 수집 그래프는 세션 DB(`data/collect_sessions.db`, SqliteSaver) 오염을 막으려 **MemorySaver**(휘발성)로
  돌린다. 그래서 이 테스트는 채팅 UI의 세션 영속/복원과 **독립** — 수집 그래프를 호출만 하므로 프론트
  핸드오프 적용 여부와 무관하게 동작한다.
- 개념간 계보(`added_edges`)는 `normalized_v2.json` 에 직접 저장돼 있지 않고 paper→concept 엣지에서
  유도된다. `test_collect.py: load_view()` 가 `api/main.py: build_graph_view` 의 파생 규칙(home
  concept = 그 논문이 처음 defines 한 개념 → builds_on 대상들)을 **읽기 전용으로 미러**한다.
