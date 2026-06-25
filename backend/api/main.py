"""research-atlas 웹 UI 백엔드.

그래프(읽기 전용)와 사전(편집)을 서빙한다.
파이프라인(pipeline/)은 건드리지 않고, /api/rebuild만 pipeline/normalize_v2.py를 subprocess로 호출한다.
라우트는 도메인별 라우터로 분리(backend/api/routers/): graph · lexicon · rebuild · command · collect.

실행:  uv run uvicorn backend.api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers import collect, command, graph, lexicon, rebuild

app = FastAPI(title="research-atlas")

# Vite dev 서버(들)에서의 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph.router)
app.include_router(lexicon.router)
app.include_router(rebuild.router)
app.include_router(command.router)
app.include_router(collect.router)
