"""01 parse: PDF → abstract+intro 텍스트 → {paper_id}.parsed.json
   섹션 경계로 자르되, 못 찾으면 HEAD_CHARS로 fallback."""
import json
import re
import sys
from pathlib import Path

import pymupdf

from pipeline import config

HEAD_CHARS = 6000       # 섹션 헤딩 못 찾을 때 fallback 상한
MIN_INTRO_CHARS = 3000  # 이보다 이른 헤딩 매칭은 건너뜀(가장 짧은 정상 intro도 ~4400자)
ABSTRACT_MAX_POS = 5000  # Abstract 헤딩은 1쪽에. 이보다 뒤의 'abstract'는 본문 단어로 보고 무시.

ABSTRACT = re.compile(r"(?i)\babstract\b")

# 진짜 "섹션 2" 헤딩 한 줄만 인정.
#  - IGNORECASE 안 씀: 제목 첫 글자 [A-Z] 강제 → 문장 도중 소문자 'acquisition/provide' 배제.
#  - 줄 끝($) 앵커 + 제목 문자셋 제한 → 문장/리스트 항목("2. X is a ... composer.")·
#    그림 데이터("2\nInventory (5/36): {…}")·URL 배제.
#  - 앞의 페이지번호 줄 1개를 선택적으로 흡수 → "…문장.\n2\n2\nRelated Work"에서
#    페이지번호 직전(문장 끝)까지만 자르도록.
SECTION_HEAD = re.compile(
    r"(?m)^[ \t]*(?:\d{1,4}[ \t]*\n[ \t]*)?"      # (선택) 페이지번호 줄
    r"2(?=[.)\s])[.)]?[ \t]*(?:\n[ \t]*)?"         # 섹션번호 2 (뒤에 . ) 공백 줄바꿈 필수: "2Wiki" 배제)
    r"([A-Z][A-Za-z0-9][A-Za-z0-9 \-&]{1,44})"     # 제목: 대문자 시작·짧음·문장부호 없음
    r"[ \t]*$"
)
# 번호 없이도 섹션 2로 흔히 쓰이는 제목(앞 문장이 마침표로 안 끝나도 인정).
SECTION_KEYWORD = re.compile(
    r"(?:related works?|background|preliminaries|methodolog\w*|methods?|approach)$"
)
# 번호 매겨진 목록(기여/발견 1.2.3.…) 판별: 헤딩 직후 가까이 '3.' 형제 항목이 오면 섹션 아님.
SIBLING3 = re.compile(r"(?m)^[ \t]*3[.)]?(?:[ \t]+|[ \t]*\n[ \t]*)[A-Z]")
# 문장이 끝났는지(마침표류 + 닫는 따옴표/괄호 허용).
SENT_END = re.compile(r"""[.!?]["')\]”’]*$""")


def _boundary_cut(text: str, limit: int) -> str:
    """헤딩 못 찾을 때: 단어 중간 절단 금지, 마지막 문장/문단 경계에서 자른다."""
    head = text[:limit]
    for sep in (".\n", ". ", "\n\n"):
        i = head.rfind(sep)
        if i > limit * 0.5:          # 너무 앞이면 무시
            return text[: i + 1]
    return head


def find_cut(text: str) -> tuple[str, str]:
    """(잘린 텍스트, 사용된 방식) 반환."""
    # 시작점: Abstract 위치. 단 1쪽 범위(ABSTRACT_MAX_POS) 안일 때만. 그 밖이면 본문 단어
    # 오매칭이므로 0부터(예: 2509.25140 — 'Abstract' 헤딩 없음, 본문 'abstract'가 16592자에).
    m_abs = ABSTRACT.search(text)
    start = m_abs.start() if (m_abs and m_abs.start() <= ABSTRACT_MAX_POS) else 0

    # 끝점: start + MIN_INTRO_CHARS 이후 첫 '진짜' 섹션 2 헤딩.
    for m in SECTION_HEAD.finditer(text, start + MIN_INTRO_CHARS):
        title = m.group(1).strip()
        prec = text[start:m.start()]
        is_keyword = SECTION_KEYWORD.match(title.lower()) is not None
        ends_sentence = SENT_END.search(prec.rstrip()) is not None
        # 키워드 헤딩이거나, 앞이 문장 끝(= 페이지번호 러닝헤더·문장도중 번호 배제)이라야 인정.
        if not (is_keyword or ends_sentence):
            continue
        # 곧바로 '3.' 형제 항목이 오면 기여/발견 목록 → 섹션 헤딩 아님.
        if SIBLING3.search(text, m.end(), m.end() + 600):
            continue
        return text[start:m.start()], "section"

    # 못 찾으면 fallback (문장 경계에서 절단).
    return _boundary_cut(text, HEAD_CHARS), "head6000"


def parse_one(paper_id: str) -> dict:
    pdf_path = config.PDF_DIR / f"{paper_id}.pdf"
    if not pdf_path.exists():
        return {"paper_id": paper_id, "ok": False, "reason": "PDF 없음", "text": ""}

    doc = pymupdf.open(str(pdf_path))
    # 앞쪽 몇 페이지면 abstract+intro 충분 (전체 안 읽음)
    parts, total = [], 0
    for page in doc:
        t = page.get_text()
        parts.append(t)
        total += len(t)
        if total >= 20000:  # 넉넉히 모아두고 그 안에서 경계 탐색
            break
    doc.close()
    full = "".join(parts)

    text, method = find_cut(full)
    return {
        "paper_id": paper_id,
        "ok": True,
        "cut_method": method,
        "char_count": len(text),
        "text": text,
    }


def main():
    for pid in config.PAPER_IDS:
        r = parse_one(pid)
        (config.OUT_DIR / f"{pid}.parsed.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=2)
        )
        if r["ok"]:
            print(f"{pid}: {r['char_count']}자 [{r['cut_method']}]")
        else:
            print(f"{pid}: 실패({r['reason']})")


if __name__ == "__main__":
    main()
