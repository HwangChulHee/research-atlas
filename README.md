# research-atlas

**LLM·RAG·에이전트 연구 논문의 지형도(topology map).** 개별 논문이 아니라 *분야 전체의 구조*를 본다.

## 왜 중요한가

ChatGPT·Claude에게 논문 하나를 물으면 잘 설명해 준다. 하지만 LLM은 **분야 전체의 위상(topology)** 은 못 준다 — 무엇이 무엇에서 갈라져 나왔나(계보), 어디가 빽빽하고 어디가 비었나, *내 관심사가 그 지형의 어디쯤인가*. research-atlas는 그 지도를 만든다.

세 가지 효용:
1. **질문 → 위치** — 자유 문장으로 물으면 지도 위의 해당 노드로 데려간다.
2. **주변 위상 탐색** — 그 노드의 계보(조상·자손)와 이웃을 펼쳐 본다.
3. **세렌디피티** — "같은 문제를 다룬 다른 논문"을 의미적으로 띄워, 몰랐던 연결을 보여준다.

## 핵심 결과

- 라이브 그래프는 **gpt-5.4(full)** 품질로 빌드.
- 사람이 라벨링한 **골든셋 50편** 평가에서 `builds_on` 계보 **정밀도 0.82 / 재현율 0.83**.
- 핵심 서사는 **"직관이 아니라 측정으로 결정했다"** — 모델 비교로 full 승격(정밀도 +0.20), evidence·related-work 실험은 측정 후 *미채택*(개선 없음을 데이터로 확인).
- 규모: 논문 91 · 개념 127 · `builds_on` 엣지 209.

## 데모

`(데모 GIF — TODO)`

## 실행

전제:
- **Neo4j 5** 가동 (`bolt://localhost:7687`)
- 루트 `.env`에 `OPENAI_API_KEY` + `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`

```bash
./dev.sh
```

백엔드(:8000) + 프론트(:5173)를 한 번에 띄운다. 브라우저에서 **http://localhost:5173** (기본 진입 = `/usage`).
(`dev.sh`는 `uv run`을 거치므로 의존성·프로젝트 설치를 자동 동기화한다.)

## 개발 · 테스트

파이썬 코드는 editable 패키지로 설치된다(`pyproject` `[build-system]`). 직접 동기화하려면:

```bash
uv sync                 # 의존성 + 프로젝트(editable) 설치 → cwd 무관 절대 import
uv run pytest           # 순수함수 단위테스트(네트워크·Neo4j 불필요)
```

`pipeline`·`backend`·`graphdb`·`prompts`는 설치된 패키지라 `from pipeline import config`처럼 절대 import한다(`sys.path` 조작 없음). push/PR마다 GitHub Actions가 `uv sync + pytest`를 돌린다(`.github/workflows/ci.yml`). 로컬에서 ROS 등으로 `PYTHONPATH`가 주입된 환경이면 `PYTHONPATH= uv run pytest`로 실행.

## 화면

- **사용법 (`/usage`, 기본)** — 처음 보는 사람용. "하고 싶은 것"별 예시 칩을 누르면 지형도로 이동해 그 질문이 자동 실행되어 맵이 반응한다.
- **지형도 (`/graph`)** — 개념 노드 + `builds_on` 계보를 그린 메인 화면. 오른쪽 채팅 **[명령]/[수집]** 탭 + 하단 수동 필터/계보 컨트롤. 명령창 = 이름검색·조건필터·계보·의미검색·리셋. 수집 = arXiv에서 새 논문 증분 추가.
- **사전 (`/lexicon`)** — 개념의 상태 장부(approve/reject)·정의·병합을 편집(HITL).

## 구조

| 디렉토리 | 역할 |
|---|---|
| `pipeline/` | 빌드 파이프라인 (fetch → parse → extract → relate → normalize_v2 → embed) |
| `backend/` | FastAPI 서비스(`api/`) + 에이전트 계층(`agents/`: 수집 LangGraph·필터 tool) |
| `frontend/` | Vite + React UI (사용법 / 지형도 / 사전) |
| `graphdb/` | Neo4j 적재(`load.py`)·검증(`verify.py`)·접속(`conn.py`) — 파이프라인·백엔드 공유 |
| `prompts/` | 모든 LLM 프롬프트(한 파일당 하나) |
| `eval/` | 골든셋 평가 (정밀도/재현율 측정) |
| `tests/` | 순수함수 단위테스트 (pytest) |
| `data/` | 사전(`lexicon.json`) · 맵 결과(`outputs/`) |
| `docs/` | 문서 |

자세한 동작 원리는 **[`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md)** — 각 기능이 무엇을 어떻게 하는지 전체 메커니즘. 프롬프트 지도는 [`prompts/README.md`](prompts/README.md), 평가 상세는 [`eval/README.md`](eval/README.md).
