#!/usr/bin/env python
"""PHASE A1/A2 — 멀티에이전트 후보 풀 생성 (재현 가능, seed 고정).

소스:
  1) Guo survey(2402.01680) awesome-list 스냅샷: surveys/guo_2402.01680_README.md
     섹션→CORE 매핑: Framework·Orchestration = CORE / Problem Solving = CORE(방법) /
     World Simulation = 도메인시뮬(non-core) / Datasets&Benchmarks = 제외(사용자 규칙).
  2) 기존 candidates.csv 의 '에이전트오케스트레이션' 태그 행(RAG survey들에서 나온 것).

dedup 대상 = frozen 50 + RAG batch2 85 + 전체 corpus(data/outputs) + candidates in_corpus.
출력: expansion_ma/candidates_ma.csv  (paper_name,arxiv_id,source,guo_section,core,in_corpus)
"""
import csv
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXP_MA = ROOT / "eval/goldset/expansion_ma"
GUO = EXP_MA / "surveys/guo_2402.01680_README.md"

# ── dedup 집합: corpus(data/outputs) ∪ goldset(frozen50 + RAG85)
corpus = {Path(f).name.split(".concepts.json")[0]
          for f in glob.glob(str(ROOT/"data/outputs/*.concepts.json"))}
g = json.load(open(ROOT/"eval/goldset/papers.json"))
for k in ("new_collected", "from_corpus", "survey_sourced_b2"):
    corpus |= set(g.get(k, []))

def aid(s):
    m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', s)
    return m.group(1) if m else ""

def norm_title(t):
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return re.sub(r'[^a-z0-9 ]', '', t)

# ── Guo README 파싱: # 헤더로 top-level 섹션 추적, bullet(\[YYYY/MM\] …)에서 title+id
SECTION_CORE = {
    "Multi-Agents Framework": ("framework", True),
    "Multi-Agents Orchestration and Efficiency": ("orchestration", True),
    "Multi-Agents for Problem Solving": ("problem_solving", True),
    "Multi-Agents for World Simulation": ("world_sim", False),
    "Multi-Agents Datasets and Benchmarks": ("benchmarks", False),  # 제외 대상
}
records = []  # (title, id, source, guo_section, core)
top = None
for ln in GUO.read_text().splitlines():
    s = ln.strip()
    hm = re.match(r'^#\s+(.*)$', s)
    if hm:
        name = re.sub(r'[🔥🆕📌🤝]', '', hm.group(1)).strip()
        top = name
        continue
    # bullet: starts with escaped-date "\[YYYY/MM\]"
    if not re.match(r'^\\\[\d{4}/\d{2}\\\]', s):
        continue
    if top not in SECTION_CORE:
        continue
    sec, core = SECTION_CORE[top]
    if sec == "benchmarks":
        continue  # 사용자 규칙: benchmark 제외
    body = re.sub(r'^\\\[\d{4}/\d{2}\\\]\s*', '', s)          # 날짜 제거
    idv = aid(s)
    # title = 첫 ". " 이전(저자 앞) 또는 "[" 이전
    title = re.split(r'\.\s+[A-Z][a-z]+.*et al\.|\.\s*\[', body)[0]
    title = re.split(r'\s*\[\\?\[?(?:paper|code|repo)', title)[0]
    title = title.replace("\\", "").strip().rstrip(".").strip()
    if not title:
        continue
    records.append((title, idv, "guo", sec, core))

n_guo = len(records)

# ── 기존 candidates.csv 의 에이전트오케스트레이션 행 합치기
for r in csv.DictReader(open(ROOT/"eval/goldset/expansion/candidates.csv")):
    tags = set(r["section_tag"].split(";"))
    if "에이전트오케스트레이션" in tags:
        records.append((r["paper_name"], r["arxiv_id"].strip(),
                        f"cand:{r['survey_source']}", "orchestration", True))

# ── 병합: id 있으면 id, 없으면 norm_title
merged = {}
for t, a, src, sec, core in records:
    key = ("id", a) if a else ("ti", norm_title(t))
    if key not in merged:
        merged[key] = {"title": t, "id": a, "srcs": set(), "secs": set(), "core": False}
    m = merged[key]
    m["srcs"].add(src); m["secs"].add(sec); m["core"] = m["core"] or core
    if a and not m["id"]:
        m["id"] = a
    if len(t) > len(m["title"]):
        m["title"] = t

rows = []
for m in merged.values():
    inc = "yes" if (m["id"] and m["id"] in corpus) else "no"
    core = "core" if m["core"] and "world_sim" not in m["secs"] else \
           ("core" if m["core"] else "noncore")
    # world_sim이 유일 섹션이면 noncore
    if m["secs"] == {"world_sim"}:
        core = "noncore"
    rows.append([m["title"], m["id"], ";".join(sorted(m["srcs"])),
                 ";".join(sorted(m["secs"])), core, inc])

rows.sort(key=lambda r: (r[4] != "core", r[5] == "yes", r[0].lower()))
out = EXP_MA / "candidates_ma.csv"
with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["paper_name", "arxiv_id", "source", "guo_section", "core", "in_corpus"])
    w.writerows(rows)

from collections import Counter
print(f"Guo 파싱: {n_guo}편 (benchmark 제외)")
print(f"병합 후 총: {len(rows)}행 → {out.relative_to(ROOT)}")
print("core:", dict(Counter(r[4] for r in rows)))
print("in_corpus:", dict(Counter(r[5] for r in rows)))
print("id 있음:", sum(1 for r in rows if r[1]), "/ blank:", sum(1 for r in rows if not r[1]))
# 신규 CORE 후보(적재 대상): core & in_corpus=no & id 있음
newcore = [r for r in rows if r[4] == "core" and r[5] == "no" and r[1]]
print(f"\n★ 신규 CORE 후보(dedup 후, id 있음): {len(newcore)}편")
