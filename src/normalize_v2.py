"""normalize_v2: concepts/relations.json -> 이중 노드(paper+concept) + edges.
   LLM 없음(재조립). lexicon status로 개념 거름. 빈 링 개념 유지.
   출력: normalized_v2.json.
   실행: uv run python src/normalize_v2.py
"""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

OUT = config.OUT_DIR / "normalized_v2.json"
LEX_PATH = config.DATA_DIR / "lexicon.json"

# 노드 자격: 이 status만 맵에 노드로
NODE_OK = {"approved", "unreviewed"}


def canon(s):
    return " ".join(s.lower().replace("-", " ").split())


def load_lexicon():
    """반환: lex_raw(원본 dict), alias2rep(별칭canon→대표canon), rep_meta(대표canon→메타)"""
    lex = json.load(open(LEX_PATH))["techniques"]
    alias2rep, rep_meta = {}, {}
    for rep, meta in lex.items():
        rk = canon(rep)
        rep_meta[rk] = {"label": rep, **meta}
        alias2rep[rk] = rk
        for v in meta.get("aliases", []):
            alias2rep[canon(v)] = rk
    return lex, alias2rep, rep_meta


def save_lexicon(lex):
    json.dump({"techniques": lex}, open(LEX_PATH, "w"), ensure_ascii=False, indent=2)


def main():
    lex, alias2rep, rep_meta = load_lexicon()
    new_count = {"unreviewed": 0, "pending": 0}

    def status_of(rk):
        return rep_meta.get(rk, {}).get("status", None)

    def resolve(name):
        k = canon(name)
        if k in alias2rep:
            rk = alias2rep[k]
            return rk, rep_meta[rk]["label"]
        return k, name

    def register(rk, label, status, source, pid):
        if rk in rep_meta:
            return
        lex[label] = {"aliases": [], "status": status, "definition": "",
                      "source": source, "first_seen": pid}
        rep_meta[rk] = {"label": label, "status": status}
        alias2rep[rk] = rk
        new_count[status] += 1

    nodes, edges = {}, []

    def ensure_concept(rk, label, definition="", def_status="n/a"):
        cid = f"concept:{rk}"
        if cid not in nodes:
            nodes[cid] = {"type": "concept", "canonical": label,
                          "definition": definition, "def_status": def_status,
                          "status": status_of(rk)}
        elif definition and not nodes[cid]["definition"]:
            nodes[cid]["definition"] = definition
            nodes[cid]["def_status"] = def_status
        return cid

    pids = [Path(f).name.split(".concepts")[0]
            for f in sorted(glob.glob(str(config.OUT_DIR / "*.concepts.json")))]

    for pid in pids:
        con = json.loads((config.OUT_DIR / f"{pid}.concepts.json").read_text())
        paper_id = f"paper:{pid}"
        nodes[paper_id] = {
            "type": "paper",
            "title": con.get("title", pid),
            "problem": con.get("problem", ""),
            "task": con.get("task", []),
            "domain": con.get("domain", "general"),
            "paper_type": con.get("paper_type", "other"),
        }

        for d in con.get("defines", []):
            rk, label = resolve(d["name"])
            register(rk, label, "unreviewed", "defines", pid)
            if status_of(rk) in NODE_OK:
                cid = ensure_concept(rk, label, d.get("definition", ""), "ok")
                edges.append({"type": "defines", "from": paper_id, "to": cid})

        rel_path = config.OUT_DIR / f"{pid}.relations.json"
        if rel_path.exists():
            rel = json.loads(rel_path.read_text())
            for name in rel.get("builds_on", []):
                rk, label = resolve(name)
                register(rk, label, "pending", "builds_on", pid)
                if status_of(rk) in NODE_OK:
                    cid = ensure_concept(rk, label, "", "placeholder")
                    edges.append({"type": "builds_on", "from": paper_id, "to": cid})

    save_lexicon(lex)
    OUT.write_text(json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2))

    papers = sum(1 for n in nodes.values() if n["type"] == "paper")
    concepts = sum(1 for n in nodes.values() if n["type"] == "concept")
    defines = sum(1 for e in edges if e["type"] == "defines")
    builds = sum(1 for e in edges if e["type"] == "builds_on")
    placeholders = sum(1 for n in nodes.values()
                       if n["type"] == "concept" and n["def_status"] == "placeholder")
    print(f"=== 논문 {papers} + 개념 {concepts} = 노드 {len(nodes)} / "
          f"엣지 {len(edges)} (defines {defines} · builds_on {builds}) ===")
    print(f"=== 빈 링 개념 {placeholders}개 / 사전 신규 {new_count} ===")


if __name__ == "__main__":
    main()
