"""goldset 50편 PDF를 arXiv에서 data/pdfs/로. fetch.download_one 재사용.
   config.PAPER_IDS(=FULL_IDS)는 goldset과 다르므로 별도 fetch가 필요."""
import json
import sys
import time
from pathlib import Path

from pipeline import config
from pipeline import fetch

GOLD = json.load(open("eval/goldset/papers.json"))
IDS = GOLD["new_collected"] + GOLD["from_corpus"]


def main():
    config.PDF_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, pid in enumerate(IDS, 1):
        ok, msg = fetch.download_one(pid)
        print(f"[{i:2}/{len(IDS)}] {pid}: {msg}", flush=True)
        if not ok:
            failed.append(pid)
        if "skip" not in msg and i < len(IDS):
            time.sleep(fetch.DELAY)
    print(f"\n완료: {len(IDS) - len(failed)}/{len(IDS)}")
    if failed:
        print(f"실패: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
