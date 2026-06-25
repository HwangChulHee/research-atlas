"""normalize_v2: concepts/relations.json -> 이중 노드(paper+concept) + edges.
   LLM 없음(재조립). lexicon status로 개념 거름. 빈 링 개념 유지.
   로직은 normalize_core.normalize_paper 공유(증분 쓰기와 같은 함수 — 두 경로 무분기).
   출력: normalized_v2.json (배치 재빌드의 중간 오라클).
   실행: uv run python pipeline/normalize_v2.py
"""
import glob
import json
import sys
from pathlib import Path

from pipeline import config
from pipeline import normalize_core as nc

OUT = config.OUT_DIR / "normalized_v2.json"


def main():
    st = nc.load_lex_state()
    nodes, edges = {}, []

    pids = [Path(f).name.split(".concepts")[0]
            for f in sorted(glob.glob(str(config.OUT_DIR / "*.concepts.json")))]

    for pid in pids:
        con = json.loads((config.OUT_DIR / f"{pid}.concepts.json").read_text())
        rel_path = config.OUT_DIR / f"{pid}.relations.json"
        rel = json.loads(rel_path.read_text()) if rel_path.exists() else {}
        res = nc.normalize_paper(con, rel, pid, st)

        # 논문 노드: normalized_v2.json 스키마(접두사 + 6키, home_concept 제외)
        pn = res["paper_node"]
        nodes[f"paper:{pid}"] = {
            "type": "paper",
            "title": pn["title"],
            "problem": pn["problem"],
            "task": pn["task"],
            "domain": pn["domain"],
            "paper_type": pn["paper_type"],
        }
        # 개념 노드: 전역 누적(최초정의승·ok↛placeholder를 paper 경계 넘어 적용)
        for rk, cn in res["concept_nodes"].items():
            cid = f"concept:{rk}"
            if cid not in nodes:
                nodes[cid] = {"type": "concept", "canonical": cn["canonical"],
                              "definition": cn["definition"],
                              "def_status": cn["def_status"], "status": cn["status"]}
            elif cn["definition"] and not nodes[cid]["definition"]:
                nodes[cid]["definition"] = cn["definition"]
                nodes[cid]["def_status"] = cn["def_status"]
        # 엣지: 접두사 부여(순서/중복 보존)
        for e in res["edges"]:
            edges.append({"type": e["type"], "from": f"paper:{pid}",
                          "to": f"concept:{e['to']}"})

    nc.save_lexicon(st)
    OUT.write_text(json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2))

    papers = sum(1 for n in nodes.values() if n["type"] == "paper")
    concepts = sum(1 for n in nodes.values() if n["type"] == "concept")
    defines = sum(1 for e in edges if e["type"] == "defines")
    builds = sum(1 for e in edges if e["type"] == "builds_on")
    placeholders = sum(1 for n in nodes.values()
                       if n["type"] == "concept" and n["def_status"] == "placeholder")
    print(f"=== 논문 {papers} + 개념 {concepts} = 노드 {len(nodes)} / "
          f"엣지 {len(edges)} (defines {defines} · builds_on {builds}) ===")
    print(f"=== 빈 링 개념 {placeholders}개 / 사전 신규 {st['new']} ===")


if __name__ == "__main__":
    main()
