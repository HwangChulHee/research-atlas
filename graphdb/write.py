"""증분 쓰기: 쓰기가 일어난 그 자리에서 lexicon·Neo4j에 반영.

배치 재빌드(normalize_v2→load)와 **같은 normalize_core.normalize_paper**를 쓴다.
불변식: write_paper 누적 결과 == 같은 원자료로 배치 재빌드한 결과.

핵심 SET 의미(HANDOFF 0.4 + T0 표):
- 개념 MERGE: ON CREATE는 def/def_status/embedding 그대로. ON MATCH는 '최초정의승'—
  기존 definition이 비어있을 때만 채운다(채우면 def_status·embedding도 함께 ok로 승급).
  기존 definition이 있으면 유지(ok↛placeholder 금지). 그래서 CASE가 모두 *옛* c.definition을
  읽도록 definition 갱신을 SET의 맨 뒤에 둔다.
- 임베딩은 OpenAI 호출 → Neo4j tx 밖에서 먼저 계산.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from src import config  # noqa: F401  (.env + 경로)
from src import normalize_core as nc

from graphdb.conn import get_driver
from graphdb.load import ensure_constraints  # 멱등, 재사용

EMB_MODEL = "text-embedding-3-small"
EMB_PATH = config.OUT_DIR / "node_embeddings_v2.json"

# --- 개념 MERGE: 최초정의승 + ok↛placeholder. CASE는 옛 c.definition을 읽는다(아래 주석). ---
_CONCEPT_MERGE = """
MERGE (c:Concept {id:$id})
ON CREATE SET c.name=$name, c.status=$st, c.definition=$def,
              c.def_status=$ds, c.embedding=$vec
ON MATCH SET c.name=$name, c.status=$st,
    c.embedding   = CASE WHEN coalesce(c.definition,'')='' AND $vec IS NOT NULL
                         THEN $vec ELSE c.embedding END,
    c.def_status  = CASE WHEN coalesce(c.definition,'')='' THEN $ds ELSE c.def_status END,
    c.definition  = CASE WHEN coalesce(c.definition,'')='' THEN $def ELSE c.definition END
"""

_PAPER_MERGE = """
MERGE (p:Paper {id:$id})
SET p.title=$title, p.problem=$prob, p.paper_type=$pt, p.domain=$dom,
    p.home_concept=$home, p.embedding=$pvec
"""


def _load_cache():
    if EMB_PATH.exists():
        store = json.loads(EMB_PATH.read_text())
        store.setdefault("vectors", {})
        store.setdefault("model", EMB_MODEL)
        return store
    return {"model": EMB_MODEL, "dim": None, "vectors": {}}


def _embed_batch(texts):
    """OpenAI 임베딩 배치. 빈 입력이면 []."""
    if not texts:
        return []
    from openai import OpenAI
    resp = OpenAI().embeddings.create(model=EMB_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def _prepare_embeddings(res, pid, *, embed):
    """이 논문이 새로 임베딩해야 할 것만 OpenAI 호출 → 캐시(append-only)에 반영·저장.

    최초정의승과 정합: concept:rk 가 이미 캐시에 있으면(=이미 정의·임베딩 확정) 건너뜀.
    반환: (paper_vec, {rk: concept_vec}) — Neo4j SET에 쓸 '정본' 벡터(없으면 None).
    embed=False면 OpenAI 미호출·캐시 미변경, 전부 None.
    """
    cache = _load_cache()
    vecs = cache["vectors"]
    pkey = f"paper:{pid}"
    if not embed:
        return vecs.get(pkey), {rk: vecs.get(f"concept:{rk}") for rk in res["concept_nodes"]}

    todo_keys, todo_txt = [], []
    prob = (res["paper_node"].get("problem") or "").strip()
    if prob and pkey not in vecs:
        todo_keys.append(pkey)
        todo_txt.append(prob)
    for rk, cn in res["concept_nodes"].items():
        ckey = f"concept:{rk}"
        d = (cn.get("definition") or "").strip()
        if d and ckey not in vecs:        # 이미 있으면 최초정의승 — 건너뜀
            todo_keys.append(ckey)
            todo_txt.append(d)

    for key, vec in zip(todo_keys, _embed_batch(todo_txt)):
        vecs[key] = vec
        cache["dim"] = len(vec)
    if todo_keys:
        EMB_PATH.write_text(json.dumps(cache, ensure_ascii=False))

    return vecs.get(pkey), {rk: vecs.get(f"concept:{rk}") for rk in res["concept_nodes"]}


def _write_tx(tx, res, pid, pvec, cvecs):
    pn = res["paper_node"]
    tx.run(_PAPER_MERGE, id=pid, title=pn["title"], prob=pn["problem"],
           pt=pn["paper_type"], dom=pn["domain"], home=pn["home_concept"], pvec=pvec)
    for rk, cn in res["concept_nodes"].items():
        tx.run(_CONCEPT_MERGE, id=rk, name=cn["canonical"], st=cn["status"],
               **{"def": cn["definition"]}, ds=cn["def_status"], vec=cvecs.get(rk))
    for e in res["edges"]:
        rel = "DEFINES" if e["type"] == "defines" else "BUILDS_ON"
        tx.run(f"MATCH (p:Paper {{id:$f}}), (c:Concept {{id:$t}}) "
               f"MERGE (p)-[:{rel}]->(c)", f=pid, t=e["to"])


def write_paper(con, rel, pid, *, embed=True, driver=None):
    """추출 결과 1편(con=concepts, rel=relations) → lexicon·Neo4j 증분 반영.

    1) normalize_core.normalize_paper 로 노드/엣지/신규개념 산출(register가 lexicon 갱신)
    2) lexicon.json 저장
    3) 정의/problem 임베딩 계산(embed=True; OpenAI) → 캐시 append (tx 밖)
    4) Neo4j MERGE: paper/concept(+embedding) + DEFINES/BUILDS_ON (0.4 SET 규칙)
    반환: normalize_paper 결과(dict).
    """
    st = nc.load_lex_state()
    res = nc.normalize_paper(con, rel, pid, st)
    nc.save_lexicon(st)

    pvec, cvecs = _prepare_embeddings(res, pid, embed=embed)

    drv = driver or get_driver()
    try:
        with drv.session() as s:
            s.execute_write(ensure_constraints)
            s.execute_write(_write_tx, res, pid, pvec, cvecs)
    finally:
        if driver is None:
            drv.close()
    return res


# --- lexicon 편집 증분 쓰기 (T0 표 6·8·9 + 0.6) ---------------------------------

def _run(fn, *, driver=None):
    drv = driver or get_driver()
    try:
        with drv.session() as s:
            return s.execute_write(fn)
    finally:
        if driver is None:
            drv.close()


def reject_concept(rk, *, driver=None):
    """T0#6: 개념을 거부 → 노드·엣지 통째 삭제. 닻 깨짐은 감사가 리포트(0.6)."""
    def tx(t):
        return t.run("MATCH (c:Concept {id:$rk}) DETACH DELETE c", rk=rk).consume()
    _run(tx, driver=driver)


# src 의 정의/임베딩을 dst(비어있을 때만) 승계 — 최초정의승. 옛 d.definition을 읽도록 정의는 맨 뒤.
_MERGE_INHERIT = """
MATCH (s:Concept {id:$src}), (d:Concept {id:$dst})
SET d.embedding  = CASE WHEN coalesce(d.definition,'')='' AND s.embedding IS NOT NULL
                        THEN s.embedding ELSE d.embedding END,
    d.def_status = CASE WHEN coalesce(d.definition,'')='' THEN s.def_status ELSE d.def_status END,
    d.definition = CASE WHEN coalesce(d.definition,'')='' THEN s.definition ELSE d.definition END
"""


def merge_concept(src_rk, dst_rk, *, driver=None):
    """T0#8 + 0.6: src 를 dst 로 병합.
    - src 의 DEFINES/BUILDS_ON 엣지를 dst 로 재연결(MERGE 중복제거)
    - home_concept==src 인 논문의 닻을 dst 로 이동(재빌드의 alias 해소와 정합)
    - dst 가 빈 정의면 src 정의/임베딩 승계(최초정의승)
    - src DETACH DELETE
    src/dst 둘 중 노드가 없을 수도 있다(placeholder가 노드 아닌 경우 등) → 있으면만 동작.
    """
    if src_rk == dst_rk:
        return

    def tx(t):
        # dst 노드가 없으면 재연결 대상이 없으므로, 우선 src만이라도 정리 가능해야 한다.
        # 단 엣지 재연결은 dst 노드 존재를 전제로 MERGE.
        t.run("MATCH (p:Paper)-[r:DEFINES]->(:Concept {id:$src}) "
              "MATCH (d:Concept {id:$dst}) MERGE (p)-[:DEFINES]->(d) DELETE r",
              src=src_rk, dst=dst_rk)
        t.run("MATCH (p:Paper)-[r:BUILDS_ON]->(:Concept {id:$src}) "
              "MATCH (d:Concept {id:$dst}) MERGE (p)-[:BUILDS_ON]->(d) DELETE r",
              src=src_rk, dst=dst_rk)
        t.run(_MERGE_INHERIT, src=src_rk, dst=dst_rk)
        t.run("MATCH (p:Paper {home_concept:$src}) SET p.home_concept=$dst",
              src=src_rk, dst=dst_rk)
        t.run("MATCH (s:Concept {id:$src}) DETACH DELETE s", src=src_rk)
    _run(tx, driver=driver)


def update_definition(rk, definition, *, driver=None, embed=True):
    """T0#9: 사람이 개념 정의 수정 → Neo4j SET 정의 + 재임베딩 + 캐시 갱신.

    이건 **임시 라이브 오버레이**다 — 전체 재빌드(/api/rebuild) 시 추출 정의로 복귀한다.
    설계상 의도다(버그 아님): 개념 정의의 정본은 '논문 추출'(concepts.json→normalize_core)이고,
    사람이 lexicon에서 하는 일은 정의 작성이 아니라 자격 판정(approve/reject)·동일성 판정
    (merge/alias)이다. 정의 자체는 추출 산물로 둔다. 감사(--audit C)가 lexicon↔Neo4j 정의
    드리프트를 리포트한다.

    정의가 틀렸을 때의 올바른 해법은 정본 교정이다 — 그 개념을 정의한 논문의 concepts.json을
    고치거나(추출 오류 교정) 재추출 후 재빌드. "정의를 바꾸려면 정본을 바꿔라."
    """
    definition = (definition or "").strip()
    vec = None
    if embed and definition:
        vec = _embed_batch([definition])[0]
        cache = _load_cache()
        cache["vectors"][f"concept:{rk}"] = vec
        cache["dim"] = len(vec)
        EMB_PATH.write_text(json.dumps(cache, ensure_ascii=False))

    def tx(t):
        t.run("MATCH (c:Concept {id:$rk}) "
              "SET c.definition=$def, c.def_status='ok' "
              + ("SET c.embedding=$vec " if vec is not None else ""),
              rk=rk, **{"def": definition}, vec=vec)
    _run(tx, driver=driver)
