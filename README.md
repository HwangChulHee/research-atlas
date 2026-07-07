# research-atlas

**LLM·RAG·에이전트 논문의 지형도(topology map).** 논문 한 편이 아니라 분야 전체가 어떻게 생겼는지를 봐요.

<!-- 스크린샷 자리 — 로컬 지형도 화면 캡처 후 교체 -->
![지형도 화면](docs/screenshot.png)

## LLM한테 물어봐도 안 나오는 것

ChatGPT나 Claude한테 논문 하나 물어보면 잘 설명해 줘요. 그런데 분야 전체가 어떻게 얽혀 있는지는 못 줘요. 뭐가 뭐에서 갈라져 나왔는지(계보), 어디가 빽빽하고 어디가 비었는지, 내 관심사가 그 지형의 어디쯤인지 같은 거요. research-atlas가 그리는 게 바로 그 지도예요.

할 수 있는 건 세 가지예요.

1. **질문 → 위치**: 문장으로 물어보면 지도 위 해당 노드로 데려가요.
2. **주변 탐색**: 그 노드의 계보(조상·자손)와 이웃을 펼쳐 봐요.
3. **세렌디피티**: "같은 문제를 다룬 다른 논문"을 의미로 띄워서, 몰랐던 연결을 보여줘요.

## 만드는 과정

arXiv PDF에서 초록과 서론만 파싱하고, LLM으로 각 논문의 **개념**과 **계보 관계(`builds_on`)** 를 뽑아요. 그다음 표기를 정규화하고 같은 개념인지 사람이 판정한 뒤(HITL) 그래프에 올려요.

```
fetch(arXiv) → parse(초록+서론) → extract(gpt-5.4-mini) → relate(gpt-5.4) → normalize → embed → Neo4j
```

정본은 논문별 JSON(추출)이 먼저고, 그 위에 lexicon.json(개념 자격·동일성 판정, 사람 개입), 맨 아래가 Neo4j(라이브 그래프)예요.

스택: Python 3.12 · FastAPI · Vite/React/D3 · Neo4j 5 · OpenAI API(추출 gpt-5.4-mini / 관계 gpt-5.4 / 임베딩 text-embedding-3-small).

## 지도를 얼마나 믿을 수 있나 (측정 결과)

지형도의 값어치는 계보 관계가 얼마나 맞느냐에 달려 있어요. 그래서 사람이 라벨링한 골든셋 211편으로 `builds_on` 추출을 채점했어요. 그냥 잘 나온 숫자를 보여주는 게 아니라, 튜닝에 쓴 분포 안(in-sample)과 밖(out-of-sample)을 나눠서 잰 게 핵심이에요.

- 골든셋 211편이 네 분포로 나뉘어요. 초기 RAG 코퍼스 / RAG-추론 / 멀티에이전트 / 평가·신뢰성.
- in-sample(초기 50편)은 정밀도 0.83, 재현율 0.82예요.
- out-of-sample(나머지 161편, held-out)에서는 일반화 한계가 그대로 드러나요. 재현율은 사전(lexicon) 커버리지만 갖추면 유지되는데, 정밀도는 튜닝 분포 밖에서 떨어져요. 낯선 논문에 익숙한 개념을 자꾸 갖다 붙이는 "과잉 emission"이 병목이었어요.
- 개선도 감으로 정하지 않고 다시 재봤어요. few-shot 프롬프트는 오히려 점수를 깎아서 채점 결과를 보고 기각했고요.

이 프로젝트가 신경 쓴 건 "데모가 잘 도네"가 아니라 held-out으로 자기 편향을 재는 습관이에요. 자세한 내용은 [`eval/README.md`](eval/README.md), 한계는 [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md)에 적어 뒀어요.

## 실행 (로컬)

필요한 것:

- **Neo4j 5** 가동 (`bolt://localhost:7687`)
- 루트 `.env`에 `OPENAI_API_KEY`와 `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`

```bash
git clone https://github.com/HwangChulHee/research-atlas.git
cd research-atlas
./dev.sh
```

백엔드(:8000)와 프론트(:5173)를 한 번에 띄워요. 브라우저에서 **http://localhost:5173** 을 열면 되고, 기본 화면은 `/usage`예요. `dev.sh`가 `uv run`으로 도니까 의존성과 프로젝트 설치는 알아서 맞춰 줘요.

## 화면

- **사용법 (`/usage`, 기본)**: 처음 온 사람용이에요. "하고 싶은 것"별 예시 칩을 누르면 지형도로 넘어가서 그 질문이 자동으로 실행돼요.
- **지형도 (`/graph`)**: 개념 노드와 `builds_on` 계보를 그린 메인 화면이에요. 이름검색·조건필터·계보·의미검색 명령창에 arXiv 증분 수집까지 있어요.
- **사전 (`/lexicon`)**: 개념의 상태 장부(approve/reject)와 정의·병합을 손보는 곳이에요(HITL).

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

동작 원리를 더 파고들려면 **[`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md)** 를 보면 돼요. 프롬프트 지도는 [`prompts/README.md`](prompts/README.md), 평가 상세는 [`eval/README.md`](eval/README.md)에 있어요.

## 개발 · 테스트

```bash
uv sync                 # 의존성 + 프로젝트(editable) 설치
uv run pytest           # 순수함수 단위테스트 (네트워크·Neo4j 불필요)
```

CI는 `git push` 직전에 로컬 pre-push 훅으로 돌아요(GitHub Actions 안 써요). 새로 클론했으면 한 번만 켜 주면 돼요.

```bash
git config core.hooksPath .githooks
```

`scripts/ci_local.sh`가 backend(`ruff` + `pytest`)와 frontend(`lint` + `build`)를 검사하고, 하나라도 실패하면 push가 막혀요.
