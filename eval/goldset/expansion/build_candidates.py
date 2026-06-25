#!/usr/bin/env python
"""survey 4편(s1·s2 GitHub 목록 / s3 GitHub 목록 / s4 Figure-3 taxonomy) →
통합 section_tag 부여 → 코퍼스 dedup → candidates.csv.

section_tag 통제 어휘(=TAXONOMY_SUMMARY.ko.md 의 분류축):
  질의계획 검색시점 정보필터링 지식경계 메모리 생성 추론워크플로우
  그래프RAG 에이전트오케스트레이션 학습형RL RAG강화추론 사전정의 평가 기타
"""
import csv
import glob
import json
import re
from pathlib import Path

# 레포 루트 기준 경로 자동 해소(이 스크립트가 expansion/ 안에 있어도 동작)
ROOT = Path(__file__).resolve().parents[3]   # expansion/ → goldset → eval → root
SUR = ROOT / "eval/goldset/expansion/surveys"

# 기존 코퍼스 arXiv ID = data/outputs/ ∪ goldset papers.json(new_collected+from_corpus)
corpus = {Path(f).name.split(".concepts.json")[0]
          for f in glob.glob(str(ROOT/"data/outputs/*.concepts.json"))}
_g = json.load(open(ROOT/"eval/goldset/papers.json"))
corpus |= set(_g.get("new_collected", [])) | set(_g.get("from_corpus", []))

def aid(s):
    m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', s)
    return m.group(1) if m else ""

def norm_title(t):
    t = re.sub(r'\s+', ' ', t).strip().lower()
    t = re.sub(r'[^a-z0-9 ]', '', t)
    return t

# (title, arxiv_id, survey, unified_tag)
records = []

# ---------- map raw section breadcrumb -> unified tag ----------
def map_tag(survey, sec):
    s = sec.lower()
    if survey == "s1":
        if "retrieval optimization" in s: return "질의계획"
        if "integration enhancement" in s: return "정보필터링"
        if "generation enhancement" in s: return "생성"
        if "knowledge base" in s: return "그래프RAG"
        if "web retrieval" in s or "tool using" in s: return "RAG강화추론"
        if "prior experience" in s: return "메모리"
        if "example or training" in s: return "RAG강화추론"
        if "chain-based" in s or "tree-based" in s: return "추론워크플로우"
        if "graph-based" in s: return "그래프RAG"
        if "single-agent" in s or "multi-agent" in s: return "에이전트오케스트레이션"
        if "benchmark" in s or "dataset" in s: return "평가"
    if survey == "s2":
        if "query planning" in s: return "질의계획"
        if "knowledge boundary" in s: return "지식경계"
        if "retrieval timing" in s: return "검색시점"
        if "information filtering" in s: return "정보필터링"
        if "memory" in s: return "메모리"
        if "answer generation" in s: return "생성"
        if "fine-tuning" in s or "reinforcement learning" in s: return "학습형RL"
        if "benchmark" in s or "dataset" in s: return "평가"
    if survey == "s3":
        if "retrieval control" in s: return "검색시점"
        if "query optimization" in s: return "질의계획"
        if "reasoning" in s and "integration" in s: return "학습형RL"
        if "multi" in s and "agent" in s: return "에이전트오케스트레이션"
        if "tool" in s and "knowledge" in s: return "RAG강화추론"
        if "benchmark" in s or "dataset" in s or "evaluation" in s: return "평가"
    return "기타"

# ---------- s1: awesome-list (markdown bullets under headers) ----------
def parse_s1():
    top=h3=h4=""
    started=False
    for ln in (SUR/"s1_github_README.md").read_text().splitlines():
        s=ln.strip()
        if s.startswith("## Reasoning-Enhanced RAG"): started=True
        if not started: continue
        if s.startswith("## "):
            t=s[3:].strip()
            if t.startswith("🤝") or "Contributing" in t: break
            top=t; h3=h4=""
        elif s.startswith("### "): h3=s[4:].strip(); h4=""
        elif s.startswith("#### "): h4=s[5:].strip()
        elif s.startswith("- "):
            url_arx = aid(s)
            # title: strip leading "- (venue)" then cut at first '[' bracket group
            body = s[2:]
            body = re.sub(r'^\((?:[^()]|\([^()]*\))*\)\s*', '', body)  # remove leading (venue ...)
            title = re.split(r'\[\[?(?:Paper|Code|paper|code)', body)[0]
            title = title.replace("**","").strip().rstrip("[").strip()
            if not title: continue
            sec = ">".join(x for x in (top,h3,h4) if x)
            records.append((title, url_arx, "s1", map_tag("s1", sec)))
    # benchmarks section
    started=False
    for ln in (SUR/"s1_github_README.md").read_text().splitlines():
        s=ln.strip()

# ---------- generic markdown-table parser (s2, s3) ----------
def parse_table_readme(fname, survey, start_pat, stop_keys, title_col, breadcrumb_levels=3):
    top=h2=h3=""; started=False
    for ln in (SUR/fname).read_text().splitlines():
        s=ln.strip()
        if not started:
            if re.search(start_pat, s): started=True
            continue
        if s.startswith("#"):
            t=s.lstrip("#").strip()
            if any(k in t for k in stop_keys): break
            lvl=len(s)-len(s.lstrip("#"))
            if lvl<=2: top=t; h2=h3="" if lvl==1 else h3
            if lvl==2: h2=t; h3=""
            if lvl==1: top=t; h2=h3=""
            if lvl==3: h3=t
            if lvl==4: h3=t
            continue
        if s.startswith("|"):
            cells=[c.strip() for c in s.strip("|").split("|")]
            if len(cells)<=title_col: continue
            cell=cells[title_col]
            if "http" not in cell and "[" not in cell:
                # header/separator rows
                pass
            # title from [Title](url) or plain
            m=re.search(r'\[([^\]]+)\]\((https?://[^)]+)\)', cell)
            if m:
                title=m.group(1).strip()
            else:
                title=cell
            if not title or title.lower() in ("paper title","method","time","paper") or set(title)<=set("-: "):
                continue
            if "http" not in s:   # keep any row that carries a link (arxiv or aclanthology/openreview → blank id ok)
                continue
            sec=">".join(x for x in (top,h2,h3) if x)
            records.append((title, aid(s), survey, map_tag(survey, sec)))

parse_s1()
n1=len(records)
print(f"s1: {n1}")

# s2: tables under Reading List
parse_table_readme("s2_github_README.md","s2","Reading List",
                   ("Acknowledgement","Contact","Citation"), title_col=2)
n2=len(records)-n1
print(f"s2: {n2}")

# s3: only "Functional Roles" dimension (#### subcats) + Evaluation tables (평가).
# "Optimization Scopes"(Agent/Step/Module/System-level) 는 같은 논문 재분류라 제외(중복·기타 방지).
def parse_s3():
    txt=(SUR/"s3_github_README.md").read_text().splitlines()
    h2=""; h3=""; cur=""
    for ln in txt:
        s=ln.strip()
        if s.startswith("## ") and not s.startswith("###"):
            h2=s[3:].strip(); h3=""; cur=""
        elif s.startswith("### "):
            h3=s[4:].strip(); cur=""
        elif s.startswith("#### "):
            cur=s[5:].strip()
        if not s.startswith("|"): continue
        in_roles = ("Functional Roles" in h3) and cur
        in_eval  = (h2.startswith("Evaluation")) and ("Benchmark" in h3 or "Evaluation" in h3 or "Datasets" in h3)
        if not (in_roles or in_eval): continue
        joined=" | ".join(c.strip() for c in s.strip("|").split("|"))
        m=re.search(r'\[([^\]]+)\]\((https?://[^)]+arxiv[^)]*)\)', joined) or \
          re.search(r'\[([^\]]+)\]\((https?://[^)]+)\)', joined)
        if not m: continue
        title=m.group(1).strip()
        if title.lower() in ("paper title","method","code","model","dataset") or "http" in title: continue
        sec = cur if in_roles else "Evaluation Datasets/Benchmark"
        records.append((title, aid(s), "s3", map_tag("s3", sec)))
parse_s3()
n3=len(records)-n1-n2
print(f"s3: {n3}")

# ---------- s4: Figure-3 named taxonomy (resolve ids via lookup) ----------
title_lookup={}  # norm_title -> arxiv_id
for t,a,_,_ in records:
    if a and norm_title(t) not in title_lookup:
        title_lookup[norm_title(t)]=a
# known canonical ids for s4 systems (high confidence, from these surveys)
S4 = [
 ("RAGate","검색시점",""),
 ("Self-Route","검색시점",""),
 ("Self-RAG","검색시점","2310.11511"),
 ("Corrective Retrieval Augmented Generation (CRAG)","검색시점","2401.15884"),
 ("RAPTOR","추론워크플로우","2401.18059"),
 ("MCTS-RAG","추론워크플로우","2503.20757"),
 ("Adaptive-RAG","검색시점","2403.14403"),
 ("Modular-RAG","사전정의","2407.21059"),
 ("ReAct","검색시점","2210.03629"),
 ("Self-Ask (Measuring and Narrowing the Compositionality Gap)","검색시점","2210.03350"),
 ("Search-o1","검색시점","2501.05366"),
 ("DeepRetrieval","질의계획","2503.00223"),
 ("Search-R1","학습형RL","2503.09516"),
 ("R1-Searcher","학습형RL","2503.05592"),
 ("ReZero","학습형RL","2504.11001"),
 ("DeepResearcher","학습형RL","2504.03160"),
]
for t,tag,a in S4:
    if not a:
        a=title_lookup.get(norm_title(t),"")
    records.append((t,a,"s4",tag))
print(f"s4: {len(S4)}")
print(f"total raw records: {len(records)}")

# ---------- backfill: same paper cited as aclanthology(blank) in one survey and
# arxiv in another → give the blank one its arxiv id so they merge into one row ----------
title2id={}
for t,a,_,_ in records:
    if a: title2id.setdefault(norm_title(t), a)
records=[(t,(a or title2id.get(norm_title(t),"")),sv,tag) for t,a,sv,tag in records]

# ---------- merge: by arxiv_id (if present) else by norm title ----------
merged={}  # key -> dict
def key_for(t,a):
    return ("id",a) if a else ("ti",norm_title(t))
for t,a,sv,tag in records:
    k=key_for(t,a)
    if k not in merged:
        merged[k]={"title":t,"arxiv_id":a,"sources":set(),"tags":set()}
    m=merged[k]
    m["sources"].add(sv); m["tags"].add(tag)
    if a and not m["arxiv_id"]: m["arxiv_id"]=a
    # prefer a longer/cleaner title
    if len(t)>len(m["title"]): m["title"]=t

rows=[]
order={"s1":1,"s2":2,"s3":3,"s4":4}
tagorder=["질의계획","검색시점","정보필터링","지식경계","메모리","생성","추론워크플로우",
          "그래프RAG","에이전트오케스트레이션","학습형RL","RAG강화추론","사전정의","평가","기타"]
ti={t:i for i,t in enumerate(tagorder)}
for m in merged.values():
    src=";".join(sorted(m["sources"],key=lambda x:order[x]))
    tag=";".join(sorted(m["tags"],key=lambda x:ti.get(x,99)))
    inc="yes" if (m["arxiv_id"] and m["arxiv_id"] in corpus) else "no"
    rows.append([m["title"], m["arxiv_id"], src, tag, inc])

rows.sort(key=lambda r:(r[2], r[3], r[0].lower()))
out=ROOT/"eval/goldset/expansion/candidates.csv"
with out.open("w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["paper_name","arxiv_id","survey_source","section_tag","in_corpus"])
    w.writerows(rows)

from collections import Counter
print(f"\n=== candidates.csv: {len(rows)} rows ===")
print("in_corpus:", dict(Counter(r[4] for r in rows)))
print("survey_source:", dict(Counter(r[2] for r in rows)))
print("with arxiv_id:", sum(1 for r in rows if r[1]), "/ blank:", sum(1 for r in rows if not r[1]))
print("section_tag (primary):", dict(Counter(r[3].split(';')[0] for r in rows)))
