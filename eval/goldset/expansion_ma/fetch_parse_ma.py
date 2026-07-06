#!/usr/bin/env python
"""PHASE A3 — fetch_plan.json 의 멀티에이전트 후보 fetch + parse (LLM 없음).

arXiv PDF 다운로드(data/pdfs/, 캐시) → pymupdf parse(abstract+intro, References 절단)
→ expansion_ma/parsed/{id}.parsed.json. 실패는 parsed/_failed.txt 기록 후 계속.
data/outputs·lexicon·papers.json 등 무변경.
"""
import json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
from pipeline import fetch, parse  # noqa: E402

EXP = ROOT / "eval/goldset/expansion_ma"
PARSED = EXP / "parsed"; PARSED.mkdir(parents=True, exist_ok=True)

ids = sorted(json.load(open(EXP/"fetch_plan.json"))["fetch_ids"])
print(f"대상 {len(ids)}편")
ok, failed = 0, []
for n, pid in enumerate(ids, 1):
    out = PARSED / f"{pid}.parsed.json"
    if out.exists():
        ok += 1; print(f"[{n:2}/{len(ids)}] {pid}: skip(파싱됨)"); continue
    dl_ok, dl_msg = fetch.download_one(pid)
    if not dl_ok:
        failed.append((pid, f"fetch: {dl_msg}")); print(f"[{n:2}/{len(ids)}] {pid}: FETCH FAIL {dl_msg}")
        if "skip" not in dl_msg: time.sleep(1.5)
        continue
    r = parse.parse_one(pid)
    if not r.get("ok"):
        failed.append((pid, f"parse: {r.get('reason')}")); print(f"[{n:2}/{len(ids)}] {pid}: PARSE FAIL {r.get('reason')}")
    else:
        out.write_text(json.dumps(r, ensure_ascii=False, indent=2))
        ok += 1; print(f"[{n:2}/{len(ids)}] {pid}: {r['char_count']}자 [{r['cut_method']}]")
    if "skip" not in dl_msg: time.sleep(1.5)

if failed:
    (PARSED/"_failed.txt").write_text("\n".join(f"{p}\t{why}" for p,why in failed)+"\n")
print(f"\n완료: parse 성공 {ok}/{len(ids)} · 실패 {len(failed)}")
for p, why in failed:
    print(f"  {p}: {why}")
