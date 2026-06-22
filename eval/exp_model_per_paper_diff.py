"""분석 전용: mini@0 vs full@0 를 논문 한 편씩 비교(builds_on 채점 결과 diff).

새 추출·LLM 호출 없음. 기존 결과(model_mini_t0/, model_full_t0/)와 exp_model_compare.py의
채점 함수를 그대로 재사용해(숫자 정합성 보장) 논문별 비교 행만 조립한다.

게이트: 논문별 TP/FP/FN 합이 집계 리포트(model_mini_vs_full.md)의 mini 47/31/13·full 49/12/11과
정확히 일치해야 한다(score_paper 재사용이 안 깨졌는지). 어긋나면 중단.

산출물: eval/reports/model_mini_vs_full_per_paper.md
실행: uv run python eval/exp_model_per_paper_diff.py
"""
import sys, json, importlib.util
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# exp_model_compare.py를 모듈로 로드(채점 로직 재사용 — 새로 안 짬)
_spec = importlib.util.spec_from_file_location("emc", ROOT / "eval/exp_model_compare.py")
emc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(emc)

REPORTS_DIR = ROOT / "eval/reports"
OUT_MD = REPORTS_DIR / "model_mini_vs_full_per_paper.md"

# 집계 리포트 기대 합(게이트)
EXPECT = {"mini": (47, 31, 13), "full": (49, 12, 11)}
# 집계 P/R(요약 표 — model_mini_vs_full.md에서 그대로)
SUMMARY = {
    "전체(50)": {"mini": (0.603, 0.783), "full": (0.803, 0.817)},
    "new_collected": {"mini": (0.667, 0.667), "full": (0.893, 0.758)},
    "from_corpus": {"mini": (0.556, 0.926), "full": (0.727, 0.889)},
}


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else "—"


def pr(r):
    tp, fp, fn = len(r["TP"]), len(r["FP"]), len(r["FN"])
    p = tp / (tp + fp) if (tp + fp) else None
    rec = tp / (tp + fn) if (tp + fn) else None
    return p, rec


def main():
    st = emc.nc.load_lex_state()
    COMP, SUB = emc._sets()
    labels = emc.load_labels()
    pp = json.load(open(emc.PAPERS_PATH))
    groups = {"new_collected": set(pp["new_collected"]), "from_corpus": set(pp["from_corpus"])}

    def grp(pid):
        return ("new_collected" if pid in groups["new_collected"]
                else "from_corpus" if pid in groups["from_corpus"] else "?")

    # 논문별 채점(양 run)
    rows = {}
    for pid in labels:
        mini = emc.score_paper(st, labels[pid]["builds_on"], emc.names("mini", pid), COMP, SUB)
        full = emc.score_paper(st, labels[pid]["builds_on"], emc.names("full", pid), COMP, SUB)
        rows[pid] = {"mini": mini, "full": full}

    # ── 게이트: 합산 == 집계 ──
    for tag in ("mini", "full"):
        sTP = sum(len(rows[p][tag]["TP"]) for p in labels)
        sFP = sum(len(rows[p][tag]["FP"]) for p in labels)
        sFN = sum(len(rows[p][tag]["FN"]) for p in labels)
        if (sTP, sFP, sFN) != EXPECT[tag]:
            print(f"[GATE FAIL] {tag} 합산 ({sTP},{sFP},{sFN}) != 집계 {EXPECT[tag]} — 중단.")
            sys.exit(1)
    print(f"게이트 OK — 합산이 집계 리포트와 일치 (mini {EXPECT['mini']}, full {EXPECT['full']}).")

    # diff 여부: (TP,FP) 집합이 다르면 diff
    def differs(pid):
        a, b = rows[pid]["mini"], rows[pid]["full"]
        return a["TP"] != b["TP"] or a["FP"] != b["FP"]

    diff_pids = [p for p in labels if differs(p)]
    same_pids = [p for p in labels if not differs(p)]
    assert len(diff_pids) + len(same_pids) == 50

    # 정렬: |mini FP − full FP| 큰 순, 동률이면 |mini TP − full TP| 큰 순, pid
    def sortkey(pid):
        m, f = rows[pid]["mini"], rows[pid]["full"]
        return (-abs(len(m["FP"]) - len(f["FP"])), -abs(len(m["TP"]) - len(f["TP"])), pid)
    diff_pids.sort(key=sortkey)

    # 한 줄 진단
    def one_line(pid):
        m, f = rows[pid]["mini"], rows[pid]["full"]
        removed = m["FP"] - f["FP"]      # full이 없앤 FP
        added = f["FP"] - m["FP"]        # full이 새로 낸 FP
        rec = f["TP"] - m["TP"]          # full이 더 맞힘
        lost = m["TP"] - f["TP"]         # full이 잃음
        parts = []
        rc = Counter(m["fp_cat"][k] for k in removed)
        for cat, n in rc.most_common():
            parts.append(f"full이 {cat} {n} 제거")
        ac = Counter(f["fp_cat"][k] for k in added)
        for cat, n in ac.most_common():
            parts.append(f"full이 {cat} {n} 추가")
        if rec:
            parts.append("full이 " + ", ".join(emc.label_of(st, k) for k in sorted(rec)) + " 회복")
        if lost:
            parts.append("full이 " + ", ".join(emc.label_of(st, k) for k in sorted(lost)) + " 잃음")
        return "; ".join(parts) if parts else "(채점 동일 항목 차이 없음)"

    # 한 run의 항목 표시: TP 먼저, 그다음 FP(종류)
    def render_run(r):
        toks = []
        for k in sorted(r["TP"]):
            toks.append(f"{emc.label_of(st,k)}[TP]")
        for k in sorted(r["FP"]):
            toks.append(f"{emc.label_of(st,k)}[FP·{r['fp_cat'][k]}]")
        return "  ".join(toks) if toks else "—"

    def render_gold(pid):
        m, f = rows[pid]["mini"], rows[pid]["full"]
        gold = sorted(m["gold"])         # mini/full 동일
        toks = []
        for k in gold:
            both_fn = (k in m["FN"]) and (k in f["FN"])
            toks.append(f"{emc.label_of(st,k)}{'(미추출)' if both_fn else ''}")
        return "  ".join(toks) if toks else "—(gold 없음)"

    # ── md ──
    L = []; A = L.append
    A("# 모델 비교 — mini@0 vs full@0, 논문 단위 diff (분석 전용)")
    A("")
    A("집계(정밀도 +0.20)는 `model_mini_vs_full.md`에 있다. 이 문서는 **논문 한 편씩** builds_on을 "
      "어떻게 다르게 뽑았는지 펼친다. 새 추출·LLM 호출 없음 — 기존 결과와 `exp_model_compare.py`의 "
      "채점 함수 재사용(숫자 정합성 게이트 통과). 항목은 resolve 후 rep_key 라벨, status로 그래프에서 "
      "빠진 pred는 채점과 동일하게 표시 안 함.")
    A("")

    # ① 요약
    A("## ① 요약")
    A("")
    A("| 그룹 | mini@0 P | mini@0 R | full@0 P | full@0 R |")
    A("|---|--:|--:|--:|--:|")
    for name in ["전체(50)", "new_collected", "from_corpus"]:
        s = SUMMARY[name]
        A(f"| {name} | {fmt(s['mini'][0])} | {fmt(s['mini'][1])} | {fmt(s['full'][0])} | {fmt(s['full'][1])} |")
    A("")
    A(f"- **diff 논문 {len(diff_pids)}편 / 동일 {len(same_pids)}편** (builds_on 채점 결과 집합 기준, 합 50).")
    A(f"- 합산 게이트: mini ΣTP/FP/FN = {EXPECT['mini']}, full = {EXPECT['full']} — 집계 리포트와 일치 ✅.")
    A("")

    # ② diff 논문
    A("## ② 차이 있는 논문 (FP 차 큰 순)")
    A("")
    for pid in diff_pids:
        m, f = rows[pid]["mini"], rows[pid]["full"]
        mp, mr = pr(m); fp_, fr = pr(f)
        A(f"**{labels[pid]['title']}** ({pid}, {grp(pid)})  ·  mini P{fmt(mp)}/R{fmt(mr)} → full P{fmt(fp_)}/R{fmt(fr)}")
        A("```")
        A(f"gold:  {render_gold(pid)}")
        A(f"mini:  {render_run(m)}")
        A(f"full:  {render_run(f)}")
        A("```")
        A(f"→ {one_line(pid)}")
        A("")

    # ③ 동일 논문(접기)
    A("## ③ 동일한 논문 (채점 결과 같음)")
    A("")
    A(f"<details><summary>{len(same_pids)}편 — 펼치기</summary>")
    A("")
    A("| id | 제목 | 그룹 | P | R |")
    A("|---|---|---|--:|--:|")
    for pid in same_pids:
        m = rows[pid]["mini"]; p, r = pr(m)
        A(f"| {pid} | {labels[pid]['title']} | {grp(pid)} | {fmt(p)} | {fmt(r)} |")
    A("")
    A("</details>")
    A("")

    # ④ 마무리
    # diff 전체에서 FP 종류별 제거/추가 합
    rem = Counter(); add = Counter()
    rec_n = lost_n = 0
    for pid in diff_pids:
        m, f = rows[pid]["mini"], rows[pid]["full"]
        for k in (m["FP"] - f["FP"]):
            rem[m["fp_cat"][k]] += 1
        for k in (f["FP"] - m["FP"]):
            add[f["fp_cat"][k]] += 1
        rec_n += len(f["TP"] - m["TP"])
        lost_n += len(m["TP"] - f["TP"])
    A("## ④ 마무리")
    A("")
    A(f"diff {len(diff_pids)}편에서 full이 없앤 FP는 "
      f"{', '.join(f'{c} {n}' for c, n in rem.most_common()) or '없음'} "
      f"(새로 낸 FP {', '.join(f'{c} {n}' for c, n in add.most_common()) or '없음'}). "
      f"TP는 full이 {rec_n} 회복 / {lost_n} 잃음. "
      f"즉 full의 강점은 압도적으로 **method_misjudged(비교 baseline을 계보로 오인) 제거**와 "
      f"**component_tool/substrate(부품·백본 혼입) 제거**에 몰려 있다 — 같은 v2 규칙을 더 정확히 "
      f"적용한 결과지 새 정보를 본 게 아니다(입력 동일). 재현율 변화가 작은 것도 이와 일치"
      f"(남은 FN은 입력에 없는 not_extracted). 채택 판단은 사람.")
    A("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))
    print(f"diff {len(diff_pids)} / same {len(same_pids)}")
    print(f"full 없앤 FP {dict(rem)} / 새 FP {dict(add)} / TP 회복 {rec_n} 잃음 {lost_n}")
    print(f"생성: {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
