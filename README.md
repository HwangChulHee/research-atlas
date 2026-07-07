# research-atlas

**LLM·RAG·에이전트 논문의 지형도(topology map).** 논문 한 편이 아니라 분야 전체의 구조를 봅니다.

<!-- 스크린샷 자리 — 로컬 지형도 화면 캡처 후 교체 -->
![지형도 화면](docs/screenshot.png)

## LLM이 주지 못하는 것

ChatGPT나 Claude는 논문 한 편을 잘 설명합니다. 하지만 분야 전체의 위상은 답하지 못합니다. 무엇이 무엇에서 파생됐는지(계보), 어디가 밀집하고 어디가 비어 있는지, 내 관심사가 그 지형의 어디쯤에 놓이는지 같은 것입니다. research-atlas는 그 지도를 그립니다.

세 가지를 할 수 있습니다.

1. **질문 → 위치**: 자유 문장으로 질의하면 지도 위 해당 노드로 안내합니다.
2. **주변 탐색**: 그 노드의 계보(조상·자손)와 이웃을 펼쳐 봅니다.
3. **세렌디피티**: "같은 문제를 다룬 다른 논문"을 의미적으로 띄워 몰랐던 연결을 드러냅니다.

## 구축 과정

arXiv PDF에서 초록과 서론만 파싱한 뒤, LLM으로 각 논문의 **개념**과 **계보 관계(`builds_on`)** 를 추출합니다. 이어서 표기를 정규화하고 동일 개념 여부를 사람이 판정하며(HITL), 그 결과를 그래프에 적재합니다.

```
fetch(arXiv) → parse(초록+서론) → extract(gpt-5.4-mini) → relate(gpt-5.4) → normalize → embed → Neo4j
```

정본은 논문별 JSON(추출)이 최상위이고, 그 아래에 lexicon.json(개념 자격·동일성 판정, 사람 개입), 맨 아래가 Neo4j(라이브 그래프)입니다.

스택: Python 3.12 · FastAPI · Vite/React/D3 · Neo4j 5 · OpenAI API(추출 gpt-5.4-mini / 관계 gpt-5.4 / 임베딩 text-embedding-3-small).

## 신뢰성 (측정 결과)

지형도의 가치는 계보 관계의 정확도에 달려 있습니다. 그래서 사람이 라벨링한 골든셋 211편으로 `builds_on` 추출을 채점했습니다. 좋은 숫자만 제시하는 대신, 튜닝에 사용한 분포 안(in-sample)과 밖(out-of-sample)을 분리해 측정한 점이 핵심입니다.

- 골든셋 211편은 네 분포로 구성됩니다. 초기 RAG 코퍼스 / RAG-추론 / 멀티에이전트 / 평가·신뢰성.
- in-sample(초기 50편)은 정밀도 0.83, 재현율 0.82입니다.
- out-of-sample(나머지 161편, held-out)에서는 일반화의 한계가 드러납니다. 재현율은 사전(lexicon) 커버리지만 확보되면 유지되지만, 정밀도는 튜닝 분포를 벗어나면 하락합니다. 낯선 논문에 익숙한 개념을 과도하게 부여하는 "과잉 emission"이 병목입니다.
- 개선 여부도 직관이 아니라 재측정으로 판단합니다. few-shot 프롬프트는 오히려 성능을 떨어뜨려 기각했습니다.

이 프로젝트의 초점은 "동작하는 데모"가 아니라 held-out 평가로 자기 편향을 측정하는 규율입니다. 상세는 [`eval/README.md`](eval/README.md), 한계는 [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md)에 정리했습니다.

## 실행 (로컬)

전제:

- **Neo4j 5** 가동 (`bolt://localhost:7687`)
- 루트 `.env`에 `OPENAI_API_KEY`와 `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`

```bash
git clone https://github.com/HwangChulHee/research-atlas.git
cd research-atlas
./dev.sh
```

백엔드(:8000)와 프론트(:5173)를 한 번에 띄웁니다. 브라우저에서 **http://localhost:5173** 으로 접속하며, 기본 화면은 `/usage`입니다. `dev.sh`는 `uv run`을 거치므로 의존성과 프로젝트 설치가 자동으로 동기화됩니다.

## 화면

- **사용법 (`/usage`, 기본)**: 처음 접하는 사용자를 위한 화면입니다. "하고 싶은 것"별 예시 칩을 누르면 지형도로 이동해 해당 질문이 자동으로 실행됩니다.
- **지형도 (`/graph`)**: 개념 노드와 `builds_on` 계보를 그린 메인 화면입니다. 이름검색·조건필터·계보·의미검색 명령창과 arXiv 증분 수집을 제공합니다.
- **사전 (`/lexicon`)**: 개념의 상태 장부(approve/reject)와 정의·병합을 편집합니다(HITL).

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

동작 원리는 **[`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md)** 에 자세히 정리했습니다. 프롬프트 지도는 [`prompts/README.md`](prompts/README.md), 평가 상세는 [`eval/README.md`](eval/README.md)를 참고하세요.

## 개발 · 테스트

```bash
uv sync                 # 의존성 + 프로젝트(editable) 설치
uv run pytest           # 순수함수 단위테스트 (네트워크·Neo4j 불필요)
```

CI는 `git push` 직전 로컬 pre-push 훅으로 실행됩니다(GitHub Actions는 쓰지 않습니다). 새로 클론한 경우 한 번만 활성화하면 됩니다.

```bash
git config core.hooksPath .githooks
```

`scripts/ci_local.sh`가 backend(`ruff` + `pytest`)와 frontend(`lint` + `build`)를 검사하며, 하나라도 실패하면 push가 차단됩니다.
