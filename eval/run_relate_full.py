"""full 승격 재실행: data/outputs/*.relations.json 존재 91편 전부를
relate(full, temp=0)로 재호출해 덮어쓴다. extract 재실행 없음(concepts 그대로).

병렬: ThreadPoolExecutor(워커 N). 각 워커는 relate_one만 호출, 메인이 기록.
JSON 파싱 실패는 relate_one 내부 json.loads 예외로 잡혀 카운트된다.
"""
import json, sys, glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "src"))
import config
from relate import relate_one

OUT = config.OUT_DIR
IDS = sorted(p.split("/")[-1].rsplit(".relations.json", 1)[0]
             for p in glob.glob(str(OUT / "*.relations.json")))
print(f"대상 {len(IDS)}편, model={config.MODEL_RELATE}, temp=0", flush=True)


def work(pid):
    concepts = json.loads((OUT / f"{pid}.concepts.json").read_text())
    text = json.loads((OUT / f"{pid}.parsed.json").read_text())["text"]
    return pid, relate_one(concepts, text)


ok, fail = 0, []
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(work, pid): pid for pid in IDS}
    for fut in as_completed(futs):
        pid = futs[fut]
        try:
            pid, r = fut.result()
            (OUT / f"{pid}.relations.json").write_text(
                json.dumps(r, ensure_ascii=False, indent=2))
            ok += 1
            print(f"[{ok}/{len(IDS)}] {pid}: builds_on={r['builds_on']}", flush=True)
        except Exception as e:
            fail.append((pid, repr(e)))
            print(f"FAIL {pid}: {e!r}", flush=True)

print(f"\n완료 ok={ok} fail={len(fail)}")
for pid, e in fail:
    print(f"  {pid}: {e}")
