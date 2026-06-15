"""② 검증: 프로덕션 graph_view_neo4j() 가 build_graph_view(JSON)을 전체 재현하나.

expected_from_json(include_papers) = build_graph_view 로직의 충실한 포트(JSON 직독).
actual = api.graph_neo4j.graph_view_neo4j(include_papers) — 실제 프로덕션 함수.
papers=false / papers=true 둘 다 비교. 순서가 무의미한 것(papers 리스트, 엣지)은 정렬/집합화 후 비교.
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


if __name__ == "__main__":
    main()
