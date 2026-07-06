#!/usr/bin/env python
"""PHASE B1/B2 — 평가/신뢰성 후보 풀 (Yehudai eval + Yu TrustAgent 목록 파싱).

section_tag: eval_capability / eval_appbench / eval_framework(Yehudai §)
             attack / defense / evaluation(TrustAgent Brain·Memory·Tool·A2A·A2E·A2U)
benchmark 휴리스틱: 제목에 Bench/Benchmark/Dataset/-Gym/Arena/Eval Suite → is_benchmark=yes(드롭 후보).
dedup 대상 = frozen50 + RAG85 + multiagent_b3 + 전체 corpus.
출력: candidates_eval.csv (title,arxiv_id,list,section,is_benchmark,in_corpus)
"""
import csv
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCR = Path("/tmp/claude-1000/-home-hch-research-atlas/bc3b4f80-ec33-4d42-8106-55c57f63f882/scratchpad")
EXP = ROOT / "eval/goldset/expansion_eval"

corpus = {Path(f).name.split(".concepts.json")[0]
          for f in glob.glob(str(ROOT/"data/outputs/*.concepts.json"))}
g = json.load(open(ROOT/"eval/goldset/papers.json"))
for k in ("new_collected","from_corpus","survey_sourced_b2","multiagent_b3"):
    corpus |= set(g.get(k, []))

def aid(s):
    m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', s)
    return m.group(1) if m else ""
BENCH = re.compile(r'\bbench|benchmark|dataset|[- ]gym\b|arena|eval\w* suite|testbed', re.I)

records = []  # (title,id,list,section)

# ── Yehudai: "*  **Title** [[paper]](url)" under ### sections
top = ""
for ln in (SCR/"yehudai_readme.md").read_text().splitlines():
    s = ln.strip()
    hm = re.match(r'^#{2,3}\s+(.*)$', s)
    if hm:
        t = re.sub(r':[a-z_]+:', '', hm.group(1)).strip()
        # 섹션 대분류
        if "Capabilities" in t or "§2" in t: top = "eval_capability"
        elif "Application-Specific" in t or "§3" in t: top = "eval_appbench"
        elif "Generalist" in t or "§4" in t: top = "eval_generalist"
        elif "Frameworks" in t or "Gym" in t or "§5" in t: top = "eval_framework"
        elif "Survey" in t: top = "survey"
        else: top = top  # keep
        continue
    if not s.startswith("*"): continue
    idv = aid(s)
    if not idv: continue
    m = re.search(r'\*\*(.+?)\*\*', s)
    title = (m.group(1) if m else s).strip().rstrip(":")
    records.append((title, idv, "yehudai", top))

# ── TrustAgent: "N. **"Title"** ... [Paper](url)" under #### Attack/Defense/Evaluation
sub = ""
for ln in (SCR/"trust_readme.md").read_text().splitlines():
    s = ln.strip()
    hm = re.match(r'^#{3,4}\s+(.*)$', s)
    if hm:
        t = re.sub(r'[🔺🛡️📊🔻#️⃣0-9️⃣🧠💾🛠️🤖🌍👤]', '', hm.group(1)).strip().lower()
        if "attack" in t: sub = "attack"
        elif "defen" in t: sub = "defense"
        elif "eval" in t: sub = "evaluation"
        else: sub = sub
        continue
    idv = aid(s)
    if not idv: continue
    m = re.search(r'\*\*[""]?(.+?)[""]?\*\*', s)
    title = (m.group(1) if m else s).strip().strip('"“”')
    records.append((title, idv, "trustagent", sub or "trust"))

# 병합(id 기준)
merged = {}
for t, a, lst, sec in records:
    if a not in merged:
        merged[a] = {"title": t, "id": a, "lists": set(), "secs": set()}
    merged[a]["lists"].add(lst); merged[a]["secs"].add(sec)
    if len(t) > len(merged[a]["title"]): merged[a]["title"] = t

rows = []
for m in merged.values():
    isb = "yes" if BENCH.search(m["title"]) else "no"
    inc = "yes" if m["id"] in corpus else "no"
    rows.append([m["title"], m["id"], ";".join(sorted(m["lists"])),
                 ";".join(sorted(m["secs"])), isb, inc])
rows.sort(key=lambda r: (r[5]=="yes", r[4]=="yes", r[3], r[0].lower()))

EXP.mkdir(parents=True, exist_ok=True)
with (EXP/"candidates_eval.csv").open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["title","arxiv_id","list","section","is_benchmark","in_corpus"])
    w.writerows(rows)

from collections import Counter
print(f"후보 {len(rows)}행 (Yehudai+TrustAgent 병합·dedup)")
print("in_corpus:", dict(Counter(r[5] for r in rows)))
print("is_benchmark:", dict(Counter(r[4] for r in rows)))
print("section:", dict(Counter(r[3] for r in rows)))
newmethod = [r for r in rows if r[5]=="no" and r[4]=="no"]
print(f"\n★ 신규(dedup) & 비벤치마크(제목휴리스틱): {len(newmethod)}편 — fetch+review 대상 풀")
