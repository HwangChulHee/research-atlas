"""STEP 3 — parse 수정 회귀 검증.
   (a) baseline = git HEAD의 parsed.json  (b) 수정된 parse로 goldset 50편 재파싱(working tree 덮어씀)
   (c) HEAD vs working tree diff.
   PDF 무드리프트 확인됨(OLD 코드 + 새 PDF == HEAD). 따라서 차이는 전부 코드 수정의 효과.

   합격: 라벨완료 7편 바이트 동일, Related Work 누출 없음. 타깃은 길어지고 섹션 컷.
   그 외 변경분은 사람 검토용으로 나열."""
import json
import re
import subprocess
import sys

from pipeline import config
from pipeline import parse

LABELED = {"2503.09516", "2501.12948", "2501.05366", "2505.17005",
           "2504.03160", "2503.19470", "2502.01142"}
# STEP 0/1 확정 타깃 (§1의 8편 + 감사로 추가된 5편)
TARGETS = {"2503.23513", "2510.07794", "2405.14831", "2503.00223",
           "2308.00352", "2302.04761", "2401.18059", "2509.25140",
           "2504.14870", "2509.26383", "2504.20073", "2305.16291", "2408.04187"}

GOLD = json.load(open("eval/goldset/papers.json"))
IDS = GOLD["new_collected"] + GOLD["from_corpus"]

# git 루트가 상위 디렉터리일 수 있으므로(예: 모노레포) HEAD 경로 접두사 보정.
GIT_PREFIX = subprocess.run(["git", "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()

# Related Work/Background 본문이 끝에 누출됐는지(섹션-2 헤딩 줄이 텍스트 안에).
LEAK = re.compile(
    r"(?im)^[ \t]*(?:\d{1,4}[ \t]*\n[ \t]*)?"
    r"2[.)]?[ \t]*\n?[ \t]*(related works?|background)[ \t]*$"
)


def baseline_text(pid):
    r = subprocess.run(
        ["git", "show", f"HEAD:{GIT_PREFIX}data/outputs/{pid}.parsed.json"],
        capture_output=True, text=True)
    return json.loads(r.stdout)["text"]


def reparse_and_write(pid):
    r = parse.parse_one(pid)
    (config.OUT_DIR / f"{pid}.parsed.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2)
    )
    return r


def ends_clean(t):
    return t.rstrip().endswith((".", "!", "?", '"', ")"))


def main():
    fail = False
    changed_other = []
    for pid in IDS:
        base = baseline_text(pid)
        r = reparse_and_write(pid)
        new = r["text"]
        changed = base != new

        if pid in LABELED:
            if changed:
                print(f"[HARD FAIL] {pid} 라벨완료인데 변경됨 "
                      f"{len(base)}->{len(new)}")
                fail = True
            continue

        leak = LEAK.search(new) is not None
        if leak:
            print(f"[HARD FAIL/LEAK] {pid} 끝부분에 Related Work/Background 헤딩 누출")
            fail = True

        if pid in TARGETS:
            longer = len(new) >= len(base)
            # 섹션 컷이면 진짜 헤딩 직전 종료 → 절단 아님(끝 글자 각주 숫자 등은 무방).
            ok = longer and not leak and r["cut_method"] == "section"
            tag = "OK" if ok else "CHECK"
            print(f"[TARGET] {pid} [{r['cut_method']:8}] clean={ends_clean(new)} "
                  f"{len(base)}->{len(new)}  end={new.rstrip()[-44:]!r}  {tag}")
            if not ok:
                fail = True
        elif changed:
            changed_other.append((pid, len(base), len(new), r["cut_method"], new))

    if changed_other:
        print("\n--- [CHANGED] 라벨/타깃 외 변경분 (사람 검토 대기) ---")
        for pid, lb, ln, cm, new in changed_other:
            print(f"[CHANGED] {pid} [{cm:8}] {lb}->{ln}  end={new.rstrip()[-44:]!r}")

    print("\n=== 검증", "FAIL" if fail else "PASS", "===")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
