"""related work 추출 + 파싱 품질 검증 (추출 전용 — 점수 안 냄).

목적: relate가 다음 단계에서 related work 섹션을 읽게 하기 위한 전제 작업. 이 스크립트는
goldset 50편 PDF에서 related work / background 섹션을 verbatim 추출하고, 워커-무관한
객관 신호 4개를 코드로 계산해 trusted/suspect/no_section 판정을 닻으로 깐다.

설계: 워커(서브에이전트)는 섹션 '오프셋'만 고르고, 슬라이싱은 이 스크립트가 한다
→ verbatim이 구조적으로 보장됨(환각 불가). 메인은 4개 신호를 독립 재계산해 검증.

서브커맨드:
  dump <pid>           PDF 전체 텍스트를 /tmp/rw_dump_<pid>.txt 에 쓰고, 섹션 헤딩 후보를
                       (char_offset, 줄내용)으로 출력 → 워커가 related work 경계를 빨리 찾게.
  slice <pid> <s> <e>  full_text[s:e]를 verbatim으로 잘라 {pid}.json 저장(reason=ok).
  nosection <pid>      related work 없음 → 빈 텍스트 + reason=no_section 저장.
  report               50편 json을 읽어 신호 4개 계산 + 판정 + json에 기록 + md 리포트.

불변: relate/relations/lexicon/parse.py/채점 무수정. 추출 결과는 related_work/ 에만.
실행: uv run python eval/exp_related_work_extract.py <subcommand> ...
"""
import sys, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import config
import pymupdf

OUT_DIR = ROOT / "eval/experiments/related_work"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = ROOT / "eval/reports"
LABELS_PATH = ROOT / "eval/goldset/labels.json"
PAPERS_PATH = ROOT / "eval/goldset/papers.json"
OUT_MD = REPORTS_DIR / "related_work_parse_quality.md"

# ── 신호 임계값 ────────────────────────────────
CHAR_MIN = 400        # 미만 = 헤딩만 긁음 의심
CHAR_MAX = 8000       # 초과 = 다음 섹션까지 흘림 의심
CITE_MIN = 3.0        # per 1000자 — 이상이면 '인용 충분'(related work 다움)

# ── parse.py SECTION_KEYWORD 어휘 재사용 (heading_found 신호) ──
#   줄머리에서 (선택)섹션번호 + related-work류 제목.
HEADING_RE = re.compile(
    r"(?im)^[ \t]*(?:\d+(?:\.\d+)*[.)]?[ \t]*)?"
    r"(related works?|background|preliminaries|methodolog\w*|methods?|approach)\b"
)
# 인용 패턴 (citation_density)
CITE_NUM = re.compile(r"\[\d+(?:\s*,\s*\d+)*\]")            # [12] / [1, 2, 3]
CITE_AY = re.compile(r"\([A-Z][a-z]+ et al\.?,? \d{4}\)")    # (Smith et al., 2020)


def full_pdf_text(pid: str) -> str:
    """PDF 전체 페이지 텍스트 concat (결정적). slice/report가 같은 함수를 써 오프셋 정합 보장."""
    doc = pymupdf.open(str(config.PDF_DIR / f"{pid}.pdf"))
    parts = [page.get_text() for page in doc]
    doc.close()
    return "".join(parts)


def norm_ws(s: str) -> str:
    return " ".join(s.split())


# ── 신호 계산 (메인) ─────────────────────────────
def compute_signals(pid: str, rw_text: str, full: str) -> dict:
    char_count = len(rw_text)
    # citation_density: per 1000자
    cites = len(CITE_NUM.findall(rw_text)) + len(CITE_AY.findall(rw_text))
    density = (cites / char_count * 1000) if char_count else 0.0
    # verbatim_match: 공백 정규화 후 원문 substring인가 (환각 닻)
    verbatim = bool(rw_text.strip()) and norm_ws(rw_text) in norm_ws(full)
    # heading_found: 반환 텍스트 직전 200자 + 텍스트 앞부분에 related-work류 헤딩
    heading = False
    if rw_text.strip():
        idx = full.find(rw_text)
        if idx >= 0:
            window = full[max(0, idx - 200): idx + 200]
        else:
            window = rw_text[:300]
        heading = bool(HEADING_RE.search(window))
    return {
        "heading_found": heading,
        "char_count": char_count,
        "citation_density": round(density, 2),
        "verbatim_match": verbatim,
    }


def verdict_of(reason: str, sig: dict) -> tuple[str, list]:
    """(verdict, broken_signals)."""
    broken = []
    if not sig["verbatim_match"] and reason != "no_section":
        broken.append("verbatim_match=false(워커가 지어냄/오타)")
    if reason != "no_section":
        if sig["char_count"] < CHAR_MIN:
            broken.append(f"char {sig['char_count']}<{CHAR_MIN}(헤딩만 긁음 의심)")
        elif sig["char_count"] > CHAR_MAX:
            broken.append(f"char {sig['char_count']}>{CHAR_MAX}(다음 섹션 흘림 의심)")
        if not sig["heading_found"] and sig["citation_density"] < CITE_MIN:
            broken.append(f"heading 없음 + 인용밀도 {sig['citation_density']}<{CITE_MIN}(엉뚱 섹션 의심)")

    if reason == "no_section":
        # 워커가 없음 판단 + 헤딩도 안 잡힘 → 정당한 없음 후보
        return ("no_section" if not sig["heading_found"] else "suspect"), (
            [] if not sig["heading_found"] else ["no_section인데 heading 잡힘 — 놓쳤을 수 있음"])
    if not broken:
        return "trusted", []
    return "suspect", broken


# ── 서브커맨드 ───────────────────────────────────
def cmd_dump(pid):
    full = full_pdf_text(pid)
    tmp = Path(f"/tmp/rw_dump_{pid}.txt")
    tmp.write_text(full)
    print(f"[{pid}] full_text {len(full)}자 → {tmp}")
    print("=== 섹션 헤딩 후보 (char_offset | 줄) ===")
    # 줄별 오프셋 추적
    off = 0
    n = 0
    for line in full.split("\n"):
        ls = line.strip()
        # 헤딩 후보: related-work 어휘 매칭 OR (짧고 번호로 시작하는 대문자 제목)
        is_kw = HEADING_RE.search(ls) is not None
        is_numtitle = re.match(r"^\d+(\.\d+)*[.)]?\s+[A-Z][A-Za-z].{0,40}$", ls) is not None
        if (is_kw or is_numtitle) and len(ls) <= 60:
            print(f"{off:7d} | {ls}")
            n += 1
        off += len(line) + 1
    if not n:
        print("(후보 없음 — related work가 intro에 녹았거나 헤딩 비표준)")
    print(f"=== 후보 {n}개. related work 시작 offset과 다음 섹션 시작 offset(=end)을 골라 "
          f"`slice {pid} <start> <end>` 실행. 없으면 `nosection {pid}`. ===")


def _write(pid, rw_text, reason, full):
    rec = {"paper_id": pid, "related_work_text": rw_text,
           "source_len": len(full), "reason": reason}
    (OUT_DIR / f"{pid}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2))
    print(f"[{pid}] reason={reason} char={len(rw_text)} → {OUT_DIR.name}/{pid}.json")


def cmd_slice(pid, s, e):
    full = full_pdf_text(pid)
    s, e = int(s), int(e)
    rw = full[s:e]
    _write(pid, rw, "ok", full)


def cmd_nosection(pid):
    full = full_pdf_text(pid)
    _write(pid, "", "no_section", full)


# ── report (메인) ────────────────────────────────
def fmt_pct(n, d):
    return f"{n}/{d}"


def cmd_report():
    labels = json.load(open(LABELS_PATH))["labels"]
    pp = json.load(open(PAPERS_PATH))
    groups = {"new_collected": set(pp["new_collected"]), "from_corpus": set(pp["from_corpus"])}

    def grp(pid):
        return ("new_collected" if pid in groups["new_collected"]
                else "from_corpus" if pid in groups["from_corpus"] else "?")

    rows, missing = [], []
    for pid in labels:
        fp = OUT_DIR / f"{pid}.json"
        if not fp.exists():
            missing.append(pid); continue
        rec = json.load(open(fp))
        full = full_pdf_text(pid)
        sig = compute_signals(pid, rec.get("related_work_text", ""), full)
        verdict, broken = verdict_of(rec.get("reason", "ok"), sig)
        rec["signals"] = sig
        rec["verdict"] = verdict
        rec["broken"] = broken
        fp.write_text(json.dumps(
            {k: rec[k] for k in ["paper_id", "related_work_text", "source_len",
                                 "reason", "signals", "verdict", "broken"]},
            ensure_ascii=False, indent=2))
        rows.append({"pid": pid, "title": labels[pid]["title"], "grp": grp(pid),
                     "reason": rec.get("reason", "ok"), "sig": sig,
                     "verdict": verdict, "broken": broken})

    if missing:
        print(f"⚠️ 결과 누락 {len(missing)}편: {missing} — 워커 미완. 중단.")
        sys.exit(1)

    trusted = [r for r in rows if r["verdict"] == "trusted"]
    suspect = [r for r in rows if r["verdict"] == "suspect"]
    nosec = [r for r in rows if r["verdict"] == "no_section"]

    # ── 게이트: trusted는 전부 verbatim_match=true ──
    bad = [r for r in trusted if not r["sig"]["verbatim_match"]]
    if bad:
        print(f"[GATE FAIL] trusted인데 verbatim_match=false {len(bad)}편: {[r['pid'] for r in bad]}")
        print("분류 버그 → 중단."); sys.exit(1)
    print(f"게이트 OK — trusted {len(trusted)}편 전부 verbatim_match=true (환각 0).")

    # ── 분포 ──
    chars = sorted(r["sig"]["char_count"] for r in rows if r["reason"] != "no_section")
    dens = sorted(r["sig"]["citation_density"] for r in rows if r["reason"] != "no_section")

    def pct(xs, p):
        if not xs:
            return 0
        return xs[min(len(xs) - 1, int(len(xs) * p))]

    # ── md ──
    L = []; A = L.append
    A("# related work 추출 — 파싱 품질 검증 (추출 전용)")
    A("")
    A("relate가 다음 단계에서 related work 섹션을 읽게 하기 위한 전제 작업. goldset 50편 PDF에서 "
      "related work/background 섹션을 **verbatim 추출**하고, 워커-무관한 **객관 신호 4개를 코드로 "
      "계산**해 trusted/suspect/no_section을 판정했다. 점수(P/R) 없음 — 이 통과율이 다음 단계 "
      "진행 여부를 정한다.")
    A("")
    A("설계: 워커(서브에이전트 5명×10편)는 섹션 오프셋만 고르고 슬라이싱은 코드가 수행 → "
      "verbatim이 구조적으로 보장. 메인이 4개 신호를 독립 재계산해 검증.")
    A("")
    A("신호: **verbatim_match**(공백정규화 후 원문 substring — 환각 닻), **char_count**"
      f"(정상 {CHAR_MIN}~{CHAR_MAX}), **citation_density**(per 1000자, 충분≥{CITE_MIN}), "
      "**heading_found**(직전/앞부분에 related-work류 헤딩).")
    A("")
    A("## 1. 요약")
    A("")
    A(f"- **trusted {len(trusted)}** / **suspect {len(suspect)}** / **no_section {len(nosec)}** "
      f"(합 {len(rows)}).")
    A(f"- 게이트: trusted 전부 verbatim_match=true (환각 0) ✅.")
    gt = {"new_collected": 0, "from_corpus": 0}
    for r in trusted:
        gt[r["grp"]] = gt.get(r["grp"], 0) + 1
    A(f"- trusted 그룹 분해: new_collected {gt.get('new_collected',0)} / from_corpus {gt.get('from_corpus',0)}.")
    A("")

    A("## 2. 분포 (이상치)")
    A("")
    A("| 지표 | min | p25 | p50 | p75 | max |")
    A("|---|--:|--:|--:|--:|--:|")
    if chars:
        A(f"| char_count | {chars[0]} | {pct(chars,.25)} | {pct(chars,.5)} | {pct(chars,.75)} | {chars[-1]} |")
    if dens:
        A(f"| citation_density | {dens[0]} | {pct(dens,.25)} | {pct(dens,.5)} | {pct(dens,.75)} | {dens[-1]} |")
    A("")
    A(f"> char<{CHAR_MIN} 또는 >{CHAR_MAX}, 또는 heading 없음+인용밀도<{CITE_MIN} 이면 suspect로 플래그.")
    A("")

    A("## 3. suspect 목록 (사람 검토)")
    A("")
    if not suspect:
        A("- (없음)")
    else:
        A("| id | 제목 | 그룹 | char | 인용밀도 | heading | verbatim | 깨진 신호 |")
        A("|---|---|---|--:|--:|:--:|:--:|---|")
        for r in suspect:
            s = r["sig"]
            A(f"| {r['pid']} | {r['title']} | {r['grp']} | {s['char_count']} | "
              f"{s['citation_density']} | {'O' if s['heading_found'] else 'X'} | "
              f"{'O' if s['verbatim_match'] else 'X'} | {'; '.join(r['broken'])} |")
    A("")

    A("## 4. no_section 목록 (related work 정말 없나)")
    A("")
    if not nosec:
        A("- (없음)")
    else:
        A("워커가 '없음' 판단 + 헤딩도 안 잡힘 = 정당한 없음 후보. 메인이 후보 헤딩을 재확인.")
        A("")
        A("| id | 제목 | 그룹 |")
        A("|---|---|---|")
        for r in nosec:
            A(f"| {r['pid']} | {r['title']} | {r['grp']} |")
    A("")

    A("## 5. trusted 목록 (참고)")
    A("")
    A("| id | 제목 | 그룹 | char | 인용밀도 | heading |")
    A("|---|---|---|--:|--:|:--:|")
    for r in trusted:
        s = r["sig"]
        A(f"| {r['pid']} | {r['title']} | {r['grp']} | {s['char_count']} | "
          f"{s['citation_density']} | {'O' if s['heading_found'] else 'X'} |")
    A("")

    A("## 6. 판정 / 다음 단계 의견")
    A("")
    rate = len(trusted) / len(rows) * 100
    A(f"trusted {len(trusted)}/{len(rows)} ({rate:.0f}%). _아래 한 문단은 report 실행 후 메인이 채움._")
    A("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))
    print(f"\ntrusted {len(trusted)} / suspect {len(suspect)} / no_section {len(nosec)}")
    print(f"생성: {OUT_MD.relative_to(ROOT)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "dump":
        cmd_dump(sys.argv[2])
    elif cmd == "slice":
        cmd_slice(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "nosection":
        cmd_nosection(sys.argv[2])
    elif cmd == "report":
        cmd_report()
    else:
        print(f"unknown cmd: {cmd}"); sys.exit(1)


if __name__ == "__main__":
    main()
