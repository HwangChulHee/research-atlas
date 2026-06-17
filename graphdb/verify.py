"""② 검증: 프로덕션 graph_view_neo4j() 가 build_graph_view(JSON)을 전체 재현하나.

expected_from_json(include_papers) = build_graph_view 로직의 충실한 포트(JSON 직독).
actual = api.graph_neo4j.graph_view_neo4j(include_papers) — 실제 프로덕션 함수.
papers=false / papers=true 둘 다 비교. 순서가 무의미한 것(papers 리스트, 엣지)은 정렬/집합화 후 비교.

주의: 단독 실행 전 normalize_v2.py 를 먼저 돌려 오라클(normalized_v2.json)을 최신화할 것.
      API lexicon 편집(patch/merge)은 오라클을 갱신하지 않으므로, 편집 직후 verify 를 바로
      부르면 stale 오라클과 비교해 FAIL 할 수 있다(드리프트 아님). /api/rebuild 는
      normalize→load→verify 순서라 무관.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import config  # noqa: F401  (.env 로딩 + 경로 상수)
# 드라이버는 만들지 않는다 — graph_view_neo4j(프로덕션)가 자체 드라이버로 읽는다.
# .env 는 config / api.graph_neo4j import 시 이미 로딩됨.
from api.graph_neo4j import graph_view_neo4j


def _strip(nid):
    return nid.split(":", 1)[1] if ":" in nid else nid


def expected_from_json(include_papers: bool) -> dict:
    """build_graph_view 의 충실한 포트 — normalized_v2.json 직독."""
    raw = json.loads((config.OUT_DIR / "normalized_v2.json").read_text())
    v2_nodes, edges = raw["nodes"], raw["edges"]
    papers_meta = {pid: n for pid, n in v2_nodes.items() if n["type"] == "paper"}

    out_nodes = {}
    for cid, n in v2_nodes.items():
        if n["type"] != "concept":
            continue
        out_nodes[_strip(cid)] = {
            "canonical": n["canonical"],
            "definition": n.get("definition", ""),
            "def_status": n.get("def_status", "ok"),
            "status": n.get("status"),
            "papers": [], "ptype": "technique", "domain": "general",
        }

    concept_papers, concept_home_paper = {}, {}
    defines_first, builds_by_paper = {}, {}
    for e in edges:
        pid_full, cid_full = e["from"], e["to"]
        pid, rk = _strip(pid_full), _strip(cid_full)
        lst = concept_papers.setdefault(rk, [])
        if pid not in lst:
            lst.append(pid)
        if e["type"] == "defines":
            concept_home_paper.setdefault(rk, pid_full)
            defines_first.setdefault(pid_full, rk)
        elif e["type"] == "builds_on":
            builds_by_paper.setdefault(pid_full, []).append(rk)

    for rk, node in out_nodes.items():
        node["papers"] = concept_papers.get(rk, [])
        home = concept_home_paper.get(rk)
        if home and home in papers_meta:
            node["ptype"] = papers_meta[home].get("paper_type") or "technique"
            node["domain"] = papers_meta[home].get("domain") or "general"

    seen, builds_on = set(), []
    for pid_full, targets in builds_by_paper.items():
        src = defines_first.get(pid_full)
        if src is None:
            continue
        for tgt in targets:
            if tgt == src or tgt not in out_nodes:
                continue
            if (src, tgt) not in seen:
                seen.add((src, tgt))
                builds_on.append({"from": src, "to": tgt})

    view = {"nodes": out_nodes, "builds_on": builds_on}

    if include_papers:
        for pid, n in papers_meta.items():
            view["nodes"][pid] = {
                "type": "paper", "title": n.get("title", ""),
                "paper_type": n.get("paper_type", "other"),
                "domain": n.get("domain", "general"),
                "problem": n.get("problem", ""),
            }
        view["defines"] = [{"from": e["from"], "to": _strip(e["to"])}
                           for e in edges
                           if e["type"] == "defines" and _strip(e["to"]) in out_nodes]
        papers_with_defines = {e["from"] for e in edges if e["type"] == "defines"}
        view["paper_builds_on"] = [
            {"from": e["from"], "to": _strip(e["to"])}
            for e in edges
            if (e["type"] == "builds_on" and e["from"] not in papers_with_defines
                and _strip(e["to"]) in out_nodes)]
    return view


def _norm(view: dict) -> dict:
    """순서 무의미한 부분을 정규화: papers 리스트 정렬, 엣지 리스트→정렬 튜플."""
    nodes = {}
    for k, n in view["nodes"].items():
        n = dict(n)
        if "papers" in n:
            n["papers"] = sorted(n["papers"])
        nodes[k] = n
    norm = {"nodes": nodes}
    for key in ("builds_on", "defines", "paper_builds_on"):
        if key in view:
            norm[key] = sorted((e["from"], e["to"]) for e in view[key])
    return norm


def _diff(label, exp, act):
    e, a = _norm(exp), _norm(act)
    ok = True
    if e["nodes"] != a["nodes"]:
        ok = False
        keys = set(e["nodes"]) | set(a["nodes"])
        print(f"❌ [{label}] 노드 불일치:")
        for k in sorted(keys):
            if e["nodes"].get(k) != a["nodes"].get(k):
                print(f"  [{k}]\n    JSON : {e['nodes'].get(k)}\n    Neo4j: {a['nodes'].get(k)}")
    for key in ("builds_on", "defines", "paper_builds_on"):
        if e.get(key) != a.get(key):
            ok = False
            es, as_ = set(e.get(key, [])), set(a.get(key, []))
            print(f"❌ [{label}] {key} 불일치: JSON에만 {sorted(es-as_)} / Neo4j에만 {sorted(as_-es)}")
    if ok:
        nc = sum(1 for v in a["nodes"].values() if v.get("type") != "paper")
        extra = "".join(f", {k} {len(a[k])}" for k in ("defines", "paper_builds_on") if k in a)
        print(f"✅ [{label}] 일치 — 개념노드 {nc}, builds_on {len(a['builds_on'])}{extra}")
    return ok


def main():
    ok = True
    for include_papers in (False, True):
        label = "papers=true" if include_papers else "papers=false"
        ok &= _diff(label, expected_from_json(include_papers),
                    graph_view_neo4j(include_papers))
    sys.exit(0 if ok else 1)


# --- 감사(--audit): lexicon.json vs Neo4j 직독 드리프트 리포트(고치지 않음, 리포트만) ---
def audit() -> int:
    """라이브 Neo4j와 정본(lexicon.json + 재빌드 오라클 normalized_v2.json) 사이의 드리프트 점검.

    탐지(모두 깨끗한 상태 0건):
      A rejected인데 노드 존재   (lexicon status=rejected ∩ Neo4j Concept)
      B 별칭인데 독립 노드        (lexicon alias canon이 그 대표와 다른데 Neo4j에 단독 노드)
      C 정의 불일치              (lexicon 비어있지않은 definition ≠ Neo4j c.definition)
      D 닻 깨짐                  (Paper.home_concept이 가리키는 Concept 부재)
      E 노드 드리프트            (재빌드 오라클 개념집합 ↔ Neo4j 개념집합 불일치; row2 '있어야/없어야' 포함)
    자동수정 금지 — 위상 정확도가 정체성. 사람이 보고 판단. 발견 시 exit 1.
    """
    import normalize_core as nc
    from graphdb.conn import get_driver

    lex = json.loads((config.DATA_DIR / "lexicon.json").read_text())["techniques"]
    status_by_rk, def_by_rk, alias2rep = {}, {}, {}
    for rep, meta in lex.items():
        rk = nc.canon(rep)
        status_by_rk[rk] = meta.get("status")
        d = (meta.get("definition") or "").strip()
        if d:
            def_by_rk[rk] = d
        for a in meta.get("aliases", []):
            alias2rep[nc.canon(a)] = rk

    with get_driver() as drv, drv.session() as s:
        node_def = {r["id"]: (r["definition"] or "")
                    for r in s.run("MATCH (c:Concept) RETURN c.id AS id, "
                                   "c.definition AS definition")}
        homes = [(r["pid"], r["h"]) for r in
                 s.run("MATCH (p:Paper) WHERE p.home_concept IS NOT NULL "
                       "RETURN p.id AS pid, p.home_concept AS h")]
    node_ids = set(node_def)
    oracle = json.loads((config.OUT_DIR / "normalized_v2.json").read_text())["nodes"]
    oracle_ids = {k.split(":", 1)[1] for k, n in oracle.items() if n["type"] == "concept"}

    A = sorted(rk for rk, st in status_by_rk.items() if st == "rejected" and rk in node_ids)
    B = sorted(ac for ac, rep in alias2rep.items() if ac in node_ids and ac != rep)
    C = sorted(rk for rk, d in def_by_rk.items()
               if rk in node_def and node_def[rk].strip() != d)
    D = sorted(pid for pid, h in homes if h not in node_ids)
    E_missing = sorted(oracle_ids - node_ids)   # 오라클상 노드여야 하는데 라이브에 없음(row2)
    E_extra = sorted(node_ids - oracle_ids)      # 라이브에 있는데 오라클엔 없음(거부/병합 잔재 등)

    rows = [
        ("A rejected인데 노드 존재", A),
        ("B 별칭인데 독립 노드", B),
        ("C 정의 불일치(lexicon≠Neo4j)", C),
        ("D 닻 깨짐(home_concept 부재)", D),
        ("E 노드 누락(오라클엔 있음=재빌드 필요)", E_missing),
        ("E 노드 잔재(라이브에만 있음)", E_extra),
    ]
    total = 0
    for label, ids in rows:
        if ids:
            total += len(ids)
            print(f"⚠️  [{label}] {len(ids)}건: {ids[:20]}{' …' if len(ids) > 20 else ''}")
        else:
            print(f"✅ [{label}] 0건")
    if total == 0:
        print("=== 감사 통과 — 드리프트 없음 ===")
    else:
        print(f"=== 감사 {total}건 드리프트 — 사람 확인 필요(자동수정 안 함) ===")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    if "--audit" in sys.argv:
        sys.exit(audit())
    main()
