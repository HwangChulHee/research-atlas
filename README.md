# research-atlas

**LLM·RAG·에이전트 논문의 지형도(topology map).** 논문 한 편이 아니라 분야 전체가 어떻게 생겼는지 보는 지도.

<!-- 스크린샷 자리 — 로컬 지형도 화면 캡처 후 교체 -->
![지형도 화면](docs/screenshot.png)

## LLM한테 물어봐도 안 나오는 것

ChatGPT·Claude는 논문 한 편은 잘 설명함. 그런데 분야 전체가 어떻게 얽혔는지는 못 줌. 뭐가 뭐에서 갈라져 나왔는지(계보), 어디가 빽빽하고 어디가 비었는지, 내 관심사가 그 지형 어디쯤인지. research-atlas가 그리는 게 그 지도.

할 수 있는 건 세 가지.

1. **질문 → 위치**: 문장으로 물으면 지도 위 해당 노드로 안내.
2. **주변 탐색**: 그 노드의 계보(조상·자손)와 이웃을 펼침.
3. **세렌디피티**: "같은 문제를 다룬 다른 논문"을 의미로 띄워 몰랐던 연결을 노출.

## 만드는 과정

arXiv PDF에서 초록·서론만 파싱, LLM으로 각 논문의 **개념**과 **계보 관계(`builds_on`)** 를 추출. 이어서 표기 정규화와 동일성 판정(사람 개입, HITL)을 거쳐 그래프에 적재.

```
fetch(arXiv) → parse(초록+서론) → extract(gpt-5.4-mini) → relate(gpt-5.4) → normalize → embed → Neo4j
```

정본 순위는 논문별 JSON(추출)이 최상위, 그 아래 lexicon.json(개념 자격·동일성 판정, 사람 개입), 맨 아래 Neo4j(라이브 그래프).

스택: Python 3.12 · FastAPI · Vite/React/D3 · Neo4j 5 · OpenAI API(추출 gpt-5.4-mini / 관계 gpt-5.4 / 임베딩 text-embedding-3-small).

## 지도를 얼마나 믿을 수 있나 (측정 결과)

지형도의 값어치는 계보 관계의 정확도에 달림. 그래서 사람이 라벨링한 골든셋 211편으로 `builds_on` 추출을 채점. 잘 나온 숫자만 보여주는 대신, 튜닝에 쓴 분포 안(in-sample)과 밖(out-of-sample)을 나눠 잰 게 핵심.

- 골든셋 211편, 네 분포 — 초기 RAG 코퍼스 / RAG-추론 / 멀티에이전트 / 평가·신뢰성.
- in-sample(초기 50편): 정밀도 0.83, 재현율 0.82.
- out-of-sample(나머지 161편, held-out): 일반화 한계가 그대로 노출. 재현율은 사전(lexicon) 커버리지만 갖추면 유지, 정밀도는 튜닝 분포 밖에서 하락. 낯선 논문에 익숙한 개념을 자꾸 갖다 붙이는 "과잉 emission"이 병목.
- 개선도 감이 아니라 재측정으로 판단. few-shot 프롬프트는 오히려 점수를 깎아서 기각.

이 프로젝트의 초점은 "잘 도는 데모"가 아니라 held-out으로 자기 편향을 재는 습관. 자세한 내용은 [`eval/README.md`](eval/README.md), 한계는 [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md).

## 실행 (로컬)

필요한 것:

- **Neo4j 5** 가동 (`bolt://localhost:7687`)
- 루트 `.env`에 `OPENAI_API_KEY`와 `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`

```bash
git clone https://github.com/HwangChulHee/research-atlas.git
cd research-atlas
./dev.sh
```

백엔드(:8000)와 프론트(:5173)를 한 번에 기동. 브라우저에서 **http://localhost:5173**, 기본 화면은 `/usage`. `dev.sh`가 `uv run`으로 도니까 의존성·프로젝트 설치는 자동 동기화.

## 화면

- **사용법 (`/usage`, 기본)**: 처음 온 사람용. "하고 싶은 것"별 예시 칩을 누르면 지형도로 이동, 그 질문이 자동 실행.
- **지형도 (`/graph`)**: 개념 노드와 `builds_on` 계보를 그린 메인 화면. 이름검색·조건필터·계보·의미검색 명령창에 arXiv 증분 수집까지.
- **사전 (`/lexicon`)**: 개념의 상태 장부(approve/reject)와 정의·병합을 손보는 곳(HITL).

## 구조

| 디렉토리 | 역할 |
|---|---|
| `pipeline/` | 빌드 파이프라인 (fetch → parse → extract → relate → normalize → embed) |
| `backend/` | FastAPI 서비스(`api/`) + 에이전트 계층(`agents/`: 수집 LangGraph·필터 tool) |
| `frontend/` | Vite + React UI (사용법 / 지형도 / 사전) |
| `graphdb/` | Neo4j 적재·검증·접속 — 파이프라인·백엔드 공유 |
| `prompts/` | 모든 LLM 프롬프트(한 파일당 하나) |
| `eval/` | 골든셋 평가 (정밀도/재현율 측정, 채점 하네스) |
| `tests/` | 순수함수 단위테스트 (pytest) |
| `data/` | 사전(`lexicon.json`) · 맵 결과(`outputs/`) |
| `docs/` | 문서 |

동작 원리 상세는 **[`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md)**. 프롬프트 지도는 [`prompts/README.md`](prompts/README.md), 평가 상세는 [`eval/README.md`](eval/README.md).

## 개발 · 테스트

```bash
uv sync                 # 의존성 + 프로젝트(editable) 설치
uv run pytest           # 순수함수 단위테스트 (네트워크·Neo4j 불필요)
```

CI는 `git push` 직전 로컬 pre-push 훅으로 구동(GitHub Actions 없음). 새 클론에서 한 번만 활성화:

```bash
git config core.hooksPath .githooks
```

`scripts/ci_local.sh`가 backend(`ruff` + `pytest`)와 frontend(`lint` + `build`)를 검사, 하나라도 실패하면 push 차단.
