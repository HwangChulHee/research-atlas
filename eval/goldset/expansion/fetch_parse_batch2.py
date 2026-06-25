#!/usr/bin/env python
"""batch2 90편 fetch + parse (LLM 없음 — extract 파이프라인 미진입).

candidates.csv에서 규칙으로 90 ID 결정적 재생성 → arXiv PDF 다운로드(data/pdfs/, 캐시) →
pymupdf parse(abstract+intro, References 절단) → eval/goldset/expansion/parsed/{id}.parsed.json.
실패는 parsed/_failed.txt 에 기록하고 계속. data/outputs·lexicon·papers.json 등은 안 건드림.
"""
import csv, json, random, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
from src import fetch, parse  # noqa: E402

EXP = ROOT / "eval/goldset/expansion"
PARSED = EXP / "parsed"; PARSED.mkdir(parents=True, exist_ok=True)
(EXP / "review").mkdir(parents=True, exist_ok=True)

CORE = {"학습형RL","RAG강화추론","검색시점","질의계획","추론워크플로우",
        "지식경계","정보필터링","사전정의","생성"}

rows = list(csv.DictReader(open(EXP/"candidates.csv")))
pool = [r for r in rows if r["in_corpus"]=="no" and r["arxiv_id"].strip()
        and (set(r["section_tag"].split(";")) & CORE)]
ids = [r["arxiv_id"] for r in pool]
random.seed(42)
sample = set(random.sample(ids, 90))
meta = {r["arxiv_id"]: r for r in rows}   # id → row(meta)
json.dump({i: {"section_tag": meta[i]["section_tag"],
               "survey_source": meta[i]["survey_source"],
               "paper_name": meta[i]["paper_name"]} for i in sample},
          open(EXP/"batch2_meta.json","w"), ensure_ascii=False, indent=1)

ok, failed = 0, []
for n, pid in enumerate(sorted(sample), 1):
    out = PARSED / f"{pid}.parsed.json"
    if out.exists():
        ok += 1; print(f"[{n:2}/90] {pid}: skip(파싱됨)"); continue
    dl_ok, dl_msg = fetch.download_one(pid)
    if not dl_ok:
        failed.append((pid, f"fetch: {dl_msg}")); print(f"[{n:2}/90] {pid}: FETCH FAIL {dl_msg}")
        if "skip" not in dl_msg: time.sleep(1.5)
        continue
    r = parse.parse_one(pid)
    if not r.get("ok"):
        failed.append((pid, f"parse: {r.get('reason')}")); print(f"[{n:2}/90] {pid}: PARSE FAIL {r.get('reason')}")
    else:
        out.write_text(json.dumps(r, ensure_ascii=False, indent=2))
        ok += 1; print(f"[{n:2}/90] {pid}: {r['char_count']}자 [{r['cut_method']}]")
    if "skip" not in dl_msg: time.sleep(1.5)   # arXiv 예의

if failed:
    (PARSED/"_failed.txt").write_text("\n".join(f"{p}\t{why}" for p,why in failed)+"\n")
print(f"\n완료: parse 성공 {ok}/90 · 실패 {len(failed)}")
