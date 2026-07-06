#!/usr/bin/env python
"""PHASE B3 — 집중 on-topic 평가/신뢰성 방법 후보 fetch + parse (LLM 없음).

사용자 결정(집중: on-topic 평가방법만). 손선별 16편 = 에이전트 메모리 방법 + 평가 방법 +
RAG/신뢰성 방법(벤치마크·순수 LLM보안 제외). arXiv PDF → parse(abstract+intro) → parsed/.
"""
import json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
from pipeline import fetch, parse  # noqa: E402

EXP = ROOT / "eval/goldset/expansion_eval"
PARSED = EXP / "parsed"; PARSED.mkdir(parents=True, exist_ok=True)

# 손선별 on-topic 방법 풀
IDS = sorted([
    "2310.08560", "2502.12110", "2402.09727", "2409.14908", "2401.02777",  # 메모리 방법
    "2410.10934", "2407.01502", "2310.01798",                              # 평가/자기교정 방법
    "2406.10400", "2501.00879", "2409.17275", "2410.14262",                # 신뢰성/RAG 방법
    "2309.15817", "2406.09187", "2404.15269", "2502.11127",                # 안전평가/가드/정렬 방법
])
json.dump({"fetch_ids": IDS, "note": "집중 on-topic 평가/신뢰성 방법(손선별). 벤치마크·LLM보안 제외."},
          open(EXP/"fetch_plan_eval.json", "w"), ensure_ascii=False, indent=1)

print(f"대상 {len(IDS)}편")
ok, failed = 0, []
for n, pid in enumerate(IDS, 1):
    out = PARSED / f"{pid}.parsed.json"
    if out.exists():
        ok += 1; print(f"[{n:2}/{len(IDS)}] {pid}: skip"); continue
    dl_ok, dl_msg = fetch.download_one(pid)
    if not dl_ok:
        failed.append((pid, dl_msg)); print(f"[{n:2}/{len(IDS)}] {pid}: FETCH FAIL {dl_msg}")
        if "skip" not in dl_msg: time.sleep(1.5)
        continue
    r = parse.parse_one(pid)
    if not r.get("ok"):
        failed.append((pid, r.get("reason"))); print(f"[{n:2}/{len(IDS)}] {pid}: PARSE FAIL {r.get('reason')}")
    else:
        out.write_text(json.dumps(r, ensure_ascii=False, indent=2))
        ok += 1; print(f"[{n:2}/{len(IDS)}] {pid}: {r['char_count']}자 [{r['cut_method']}]")
    if "skip" not in dl_msg: time.sleep(1.5)

if failed:
    (PARSED/"_failed.txt").write_text("\n".join(f"{p}\t{w}" for p,w in failed)+"\n")
print(f"\n완료: {ok}/{len(IDS)} · 실패 {len(failed)}")
for p,w in failed: print(f"  {p}: {w}")
