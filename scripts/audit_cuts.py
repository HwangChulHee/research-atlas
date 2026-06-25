"""STEP 0 — goldset 50편 전수, 다중 신호로 절단/과포착 의심편 색출.
   committed parsed.json vs PDF 원문(독립 추정)을 교차 점검."""
import json
import re
import sys

import pymupdf

from src import config

GOLD = json.load(open("eval/goldset/papers.json"))
IDS = GOLD["new_collected"] + GOLD["from_corpus"]

# 본문에 들어오면 안 되는 "다음 섹션" 신호 (과포착 탐지)
LEAK = re.compile(
    r"(?im)^[ \t]*(2[\.\)]?[ \t]+[A-Z]|related\s+work|background|preliminaries)[ \t]*$"
)
# intro가 보통 포함하는 마무리 신호 (없으면 조기절단 의심)
TAIL_HINT = re.compile(
    r"(?i)(contribution|in this (paper|work)|we (propose|present|introduce)|"
    r"organized as follows|summariz|the remainder)"
)


def main():
    for pid in IDS:
        d = json.load(open(f"data/outputs/{pid}.parsed.json"))
        t = d["text"]
        cm = d.get("cut_method")
        cc = d.get("char_count")

        doc = pymupdf.open(str(config.PDF_DIR / f"{pid}.pdf"))
        full = "".join(p.get_text() for p in doc)
        doc.close()

        signals = []
        if not t.rstrip().endswith((".", "!", "?", '"', ")")):
            signals.append("MIDSENT")
        if cm == "head6000":
            signals.append("FALLBACK")
        if LEAK.search(t):
            signals.append("OVERCAP")
        if cc < 3500:
            signals.append("SHORT")
        if not TAIL_HINT.search(t[-1200:]):
            signals.append("NO_TAIL_HINT")
        frac = cc / max(len(full), 1)
        if frac < 0.08:
            signals.append(f"LOWFRAC:{frac:.2f}")

        flag = " ".join(signals) if signals else "ok"
        print(f"{pid:14} {str(cm):9} {cc:>6} frac={frac:.2f}  {flag}")


if __name__ == "__main__":
    main()
