"""자연어 명령 → tool call 번역(필터 에이전트). 실행은 프론트가 한다."""
import json

from dotenv import load_dotenv
from fastapi import APIRouter, Body, HTTPException
from openai import OpenAI

from agents.collect import embed_query, load_embeddings, match
from agents.filter import TOOLS, build_system_prompt
from api.deps import ROOT
from api.graph_neo4j import graph_view_neo4j

router = APIRouter()

load_dotenv(ROOT / ".env")
_oai = OpenAI()
COMMAND_MODEL = "gpt-5.4-mini"

# 의미검색용 임베딩 행렬 캐시(1회 로드). collect의 검증된 부품 재사용 — 코사인/임베딩 재구현 없음.
_EMB = None


def _emb():
    global _EMB
    if _EMB is None:
        _EMB = load_embeddings()  # (model, norm, (ckeys,cmat), (pkeys,pmat))
    return _EMB


def _to_front_id(hit_key: str) -> str:
    """매칭 키(concept:<rk> / paper:<id>) → 프론트 graph_view 노드 id."""
    if hit_key.startswith("concept:"):
        return hit_key.split("concept:", 1)[1]  # 개념은 접두사 제거(프론트는 rk로 키)
    return hit_key                               # 논문은 paper:<id> 그대로


@router.post("/api/command")
def command(payload: dict = Body(...)):
    """자연어 명령 -> tool call 번역. 실행은 프론트가 한다.

    반환: {"tool": "filter|focus_lineage|reset", "args": {...}}
          tool call이 안 나오면 {"tool": null, "message": "..."}
    """
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text가 비어 있음")

    view = graph_view_neo4j(include_papers=False)
    names = sorted(v["canonical"] for v in view["nodes"].values())

    resp = _oai.chat.completions.create(
        model=COMMAND_MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt(names)},
            {"role": "user", "content": text},
        ],
        tools=TOOLS,
    )
    msg = resp.choices[0].message
    if not msg.tool_calls:
        return {"tool": None, "message": (msg.content or "")[:200]}

    tc = msg.tool_calls[0]
    try:
        args = json.loads(tc.function.arguments or "{}")
    except json.JSONDecodeError:
        raise HTTPException(502, f"tool 인자 파싱 실패: {tc.function.arguments}")

    # semantic_search: 백엔드에서 임베딩 매칭까지 끝내고 하이라이트할 id 목록을 돌려준다.
    # (프론트엔 임베딩이 없음.) 키 매핑 후 라이브 그래프에 실재하는 id만 — 유령 노드 방지.
    if tc.function.name == "semantic_search":
        query = (args.get("query") or text).strip()
        model, _norm, (ckeys, cmat), (pkeys, pmat) = _emb()
        q = embed_query(query, model)
        chits = match(q, ckeys, cmat, top=8, floor=0.30)   # 개념
        phits = match(q, pkeys, pmat, top=8, floor=0.30)   # 논문
        # 검증용 노드셋은 논문 포함(papers=True). 기본 view는 papers=False라 논문 id가 없음.
        live_nodes = graph_view_neo4j(include_papers=True)["nodes"]

        def pack(hits):
            out = []
            for k, s in hits:
                fid = _to_front_id(k)
                if fid in live_nodes:
                    out.append({"id": fid, "score": round(s, 3)})
            return out

        return {"tool": "semantic_search",
                "args": {"query": query, "concepts": pack(chits), "papers": pack(phits)}}

    # focus_lineage의 node가 실재하는지 백엔드에서 한 번 더 검증
    if tc.function.name == "focus_lineage":
        canon_set = {n.lower() for n in names}
        if (args.get("node") or "").lower() not in canon_set:
            return {"tool": None, "message": f"'{args.get('node')}' 노드를 찾지 못함"}

    return {"tool": tc.function.name, "args": args}
