"""사전(lexicon) 편집 라우트 — 조회 · 부분수정(+Neo4j 동기) · 병합."""
from fastapi import APIRouter, Body, HTTPException

from backend.api.deps import load_lexicon, save_lexicon

router = APIRouter()


@router.get("/api/lexicon")
def get_lexicon():
    """techniques를 배열로 변환해 반환(프론트 편의)."""
    lex = load_lexicon()
    techniques = lex.get("techniques", {})
    return [
        {
            "name": name,
            "aliases": meta.get("aliases", []),
            "status": meta.get("status", "unreviewed"),
            "definition": meta.get("definition", ""),
            "source": meta.get("source", ""),
            "first_seen": meta.get("first_seen", ""),
        }
        for name, meta in techniques.items()
    ]


@router.patch("/api/lexicon/{name}")
def patch_lexicon(name: str, patch: dict = Body(...)):
    """한 개념의 부분 업데이트. 전달된 필드만 수정 + Neo4j 증분 동기화(T0 표 6·9).

    - status → 'rejected': 노드·엣지 삭제(reject_concept).
    - definition 전달: Neo4j 정의 갱신 + 재임베딩(update_definition). **임시 라이브 오버레이** —
      재빌드 시 추출 정의로 복귀(정의 정본은 논문 추출). 정의 교정의 올바른 해법은 정본 교정.
    - status 를 approved/unreviewed 로 *상향*: 즉시 노드화는 범위 밖(표#7) — 감사가 리포트.
    """
    from graphdb.write import reject_concept, update_definition
    from pipeline.normalize_core import canon

    lex = load_lexicon()
    techniques = lex.get("techniques", {})
    if name not in techniques:
        raise HTTPException(404, f"개념 없음: {name}")
    editable = {"status", "aliases", "definition", "source", "first_seen"}
    for key, value in patch.items():
        if key in editable:
            techniques[name][key] = value
    save_lexicon(lex)

    rk = canon(name)
    note = None
    try:
        if patch.get("status") == "rejected":
            reject_concept(rk)
        if "definition" in patch:
            update_definition(rk, patch["definition"])
            note = ("정의는 임시 라이브 오버레이입니다 — 재빌드 시 추출 정의로 복귀합니다"
                    "(정의 정본은 논문 추출). 영구 교정은 정본(concepts.json) 수정/재추출로.")
    except Exception as e:  # noqa: BLE001  (lexicon은 이미 저장됨 — rebuild로 복구 가능)
        return {"ok": True, "name": name, "neo4j_sync": f"실패({type(e).__name__})",
                **techniques[name]}
    resp = {"ok": True, "name": name, **techniques[name]}
    if note:
        resp["note"] = note
    return resp


@router.post("/api/lexicon/merge")
def merge_lexicon(body: dict = Body(...)):
    """`from` 개념을 `into`의 alias로 병합하고 `from`은 삭제."""
    src = body.get("from")
    dst = body.get("into")
    if not src or not dst:
        raise HTTPException(400, "from/into 필요")
    if src == dst:
        raise HTTPException(400, "from과 into가 같음")
    lex = load_lexicon()
    techniques = lex.get("techniques", {})
    if src not in techniques:
        raise HTTPException(404, f"from 개념 없음: {src}")
    if dst not in techniques:
        raise HTTPException(404, f"into 개념 없음: {dst}")

    dst_aliases = techniques[dst].get("aliases", [])
    # from 이름 + from의 aliases를 into의 aliases로 흡수(중복 제거, 순서 보존)
    incoming = [src] + techniques[src].get("aliases", [])
    for alias in incoming:
        if alias not in dst_aliases and alias != dst:
            dst_aliases.append(alias)
    techniques[dst]["aliases"] = dst_aliases
    del techniques[src]
    save_lexicon(lex)

    # Neo4j 증분 동기화(T0#8 + 0.6): src 엣지를 dst 로 재연결, 닻 이동, src 삭제.
    from graphdb.write import merge_concept
    from pipeline.normalize_core import canon
    try:
        merge_concept(canon(src), canon(dst))
    except Exception as e:  # noqa: BLE001  (lexicon은 이미 저장됨 — rebuild로 복구 가능)
        return {"ok": True, "into": dst, "aliases": dst_aliases,
                "neo4j_sync": f"실패({type(e).__name__})"}
    return {"ok": True, "into": dst, "aliases": dst_aliases}
