#!/usr/bin/env python
"""PHASE C2 — 신규 두 배치(multiagent_b3 + eval_b4) 적재: extract + relate.

롤백된 baseline 파이프라인(MODEL_EXTRACT=mini / MODEL_RELATE=full / temp0 / few-shot 없음)으로
parsed(expansion_ma·expansion_eval) 재사용해 예측 생성 → data/outputs/{id}.{concepts,relations}.json.
lexicon·normalize 미실행(provisional, 라이브 미오염). ATLAS_OFFLINE.
"""
import os
import json
import shutil
os.environ.setdefault("ATLAS_OFFLINE", "1")
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path("/home/hch/research-atlas")
import sys; sys.path.insert(0, str(ROOT))
from pipeline import config
from pipeline.extract import extract_one
from pipeline.relate import relate_one

OUT = config.OUT_DIR
papers = json.load(open(ROOT/"eval/goldset/papers.json"))
ids = sorted(set(papers["multiagent_b3"]) | set(papers["eval_b4"]))
SRC = [ROOT/"eval/goldset/expansion_ma/parsed", ROOT/"eval/goldset/expansion_eval/parsed"]

def parsed_path(pid):
    for d in SRC:
        p = d / f"{pid}.parsed.json"
        if p.exists(): return p
    return None

# 1) parsed → data/outputs 복사(없는 것만)
copied = 0
for pid in ids:
    dst = OUT / f"{pid}.parsed.json"
    if dst.exists(): continue
    src = parsed_path(pid)
    if src is None: print(f"⚠ parsed 없음: {pid}"); continue
    shutil.copy(src, dst); copied += 1
print(f"parsed 복사: {copied}편 (총 대상 {len(ids)})")

# 2) extract + relate (per-paper, ThreadPool)
def work(pid):
    text = json.loads((OUT/f"{pid}.parsed.json").read_text())["text"]
    concepts = extract_one(text)
    (OUT/f"{pid}.concepts.json").write_text(json.dumps(concepts, ensure_ascii=False, indent=2))
    rel = relate_one(concepts, text)
    (OUT/f"{pid}.relations.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2))
    return pid, rel.get("builds_on", [])

print(f"extract(mini)+relate(full,temp0,few-shot없음) — model_extract={config.MODEL_EXTRACT} model_relate={config.MODEL_RELATE}")
ok, fail = 0, []
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(work, pid): pid for pid in ids}
    for fut in as_completed(futs):
        pid = futs[fut]
        try:
            pid, bo = fut.result(); ok += 1
            print(f"[{ok}/{len(ids)}] {pid}: builds_on={bo}", flush=True)
        except Exception as e:
            fail.append((pid, repr(e))); print(f"FAIL {pid}: {e!r}", flush=True)
print(f"\n완료 ok={ok} fail={len(fail)}")
for p, e in fail: print(f"  {p}: {e}")
