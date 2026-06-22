"""실험 채점: relate 프롬프트 v1(baseline) vs v2 를 '같은 규칙'으로 채점하고 diff.

한 변수만 바뀐 비교다. 채점 규칙은 score_buildson.py / report_buildson.py 와 동일:
- nc.resolve()로 gold/pred를 rep_key 공간에 둔다(alias 흡수 + canon).
- pred에만 status 필터: nc.status_of(rk) ∈ NODE_OK(approved/unreviewed).
- gold은 표기만 정규화(status 필터 X).
- TP=gold&pred, FP=pred-gold, FN=gold-pred. FN분류: pred_raw에 있으면 lexicon_dropped, 아니면 not_extracted.
- FP분류: component_tool / substrate / method_misjudged (report_buildson과 동일 집합).

pred 소스:
- v1(baseline) = data/outputs/{id}.relations.json  (절대 안 건드림, 읽기만)
- v2           = eval/experiments/relate_v2/{id}.relations.json

검증 게이트(HANDOFF §7): v1 재계산이 기존 채점 숫자를 재현해야 한다. 다르면 중단.

산출물: eval/reports/buildson_promptv2_vs_v1.md (커밋 대상)
실행: uv run python eval/exp_compare_v1_v2.py
"""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import config
import normalize_core as nc

LABELS_PATH = ROOT / "eval/goldset/labels.json"
PAPERS_PATH = ROOT / "eval/goldset/papers.json"
V2_DIR = ROOT / "eval/experiments/relate_v2"
REPORTS_DIR = ROOT / "eval/reports"
OUT_MD = REPORTS_DIR / "buildson_promptv2_vs_v1.md"

# FP 3분류 (report_buildson.py와 동일 집합 — canon으로 정규화 후 대조)
_COMPONENT_TOOL = [
    "PPO", "GRPO", "Group Relative Policy Optimization",
    "Monte Carlo Tree Search", "MCTS", "RL", "reinforcement learning",
    "RAGAS", "ARES", "TruLens",
]
_SUBSTRATE = [
    "BERT", "RoBERTa", "GPT-2", "GPT-3", "GPT-J", "T5", "PaLM", "OPT",
    "BLOOM", "Qwen", "Qwen-2.5", "LLaMA", "Llama",
]
COMPONENT_TOOL = {nc.canon(x) for x in _COMPONENT_TOOL}
SUBSTRATE = {nc.canon(x) for x in _SUBSTRATE}

# §7 검증 기대치 (v1 baseline 재현 대상)
EXPECT_V1 = {
    "전체(50)":       dict(mp=0.562, mr=0.683, Mp=0.708, Mr=0.785),
    "new_collected": dict(mp=0.708, mr=0.515, Mp=0.792, Mr=0.654),
    "from_corpus":   dict(mp=0.490, mr=0.889, Mp=0.651, Mr=0.886),
}


def load_labels():
    return json.load(open(LABELS_PATH))["labels"]


def load_groups():
    p = json.load(open(PAPERS_PATH))
    return {"new_collected": set(p["new_collected"]), "from_corpus": set(p["from_corpus"])}


def load_pred_v1(pid):
    fp = config.OUT_DIR / f"{pid}.relations.json"
    return json.load(open(fp)).get("builds_on", []) if fp.exists() else None


def load_pred_v2(pid):
    fp = V2_DIR / f"{pid}.relations.json"
    return json.load(open(fp)).get("builds_on", []) if fp.exists() else None


def fp_category(rk):
    if rk in COMPONENT_TOOL:
        return "component_tool"
    if rk in SUBSTRATE:
        return "substrate"
    return "method_misjudged"


def label_of(st, rk):
    return st["rep_meta"].get(rk, {}).get("label", rk)


def score_paper(st, pid, title, group, gold_names, pred_names):
    gold = {nc.resolve(st, n)[0] for n in gold_names}
    pred_raw = {nc.resolve(st, n)[0] for n in pred_names}
    pred = {k for k in pred_raw if nc.status_of(st, k) in nc.NODE_OK}
    TP, FP, FN = gold & pred, pred - gold, gold - pred
    fn_reason = {k: ("lexicon_dropped" if k in pred_raw else "not_extracted") for k in FN}
    fp_cat = {k: fp_category(k) for k in FP}
    return {
        "id": pid, "title": title, "group": group,
        "gold": gold, "pred": pred, "pred_raw": pred_raw,
        "TP": TP, "FP": FP, "FN": FN,
        "fn_reason": fn_reason, "fp_cat": fp_cat,
    }


def aggregate(rows):
    sTP = sum(len(r["TP"]) for r in rows)
    sFP = sum(len(r["FP"]) for r in rows)
    sFN = sum(len(r["FN"]) for r in rows)
    micro_p = sTP / (sTP + sFP) if (sTP + sFP) else None
    micro_r = sTP / (sTP + sFN) if (sTP + sFN) else None
    p_vals, r_vals = [], []
    for r in rows:
        tp, fp, fn = len(r["TP"]), len(r["FP"]), len(r["FN"])
        if (tp + fp) > 0:
            p_vals.append(tp / (tp + fp))
        if (tp + fn) > 0:
            r_vals.append(tp / (tp + fn))
    macro_p = sum(p_vals) / len(p_vals) if p_vals else None
    macro_r = sum(r_vals) / len(r_vals) if r_vals else None
    lex_drop = sum(1 for r in rows for v in r["fn_reason"].values() if v == "lexicon_dropped")
    not_ext = sum(1 for r in rows for v in r["fn_reason"].values() if v == "not_extracted")
    return {
        "n": len(rows), "sumTP": sTP, "sumFP": sFP, "sumFN": sFN,
        "micro_p": micro_p, "micro_r": micro_r, "macro_p": macro_p, "macro_r": macro_r,
        "fn_lex_drop": lex_drop, "fn_not_ext": not_ext,
    }


def score_all(st, labels, groups, load_pred):
    rows, missing = [], []
    for pid, lab in labels.items():
        pred = load_pred(pid)
        if pred is None:
            missing.append(pid)
            continue
        grp = ("new_collected" if pid in groups["new_collected"]
               else "from_corpus" if pid in groups["from_corpus"] else "?")
        rows.append(score_paper(st, pid, lab["title"], grp, lab["builds_on"], pred))
    return rows, missing


def aggs_by_group(rows):
    return {
        "전체(50)": aggregate(rows),
        "new_collected": aggregate([r for r in rows if r["group"] == "new_collected"]),
        "from_corpus": aggregate([r for r in rows if r["group"] == "from_corpus"]),
    }


def verify_v1(aggs):
    ok = True
    for name, e in EXPECT_V1.items():
        a = aggs[name]
        checks = [
            abs(a["micro_p"] - e["mp"]) < 5e-4, abs(a["micro_r"] - e["mr"]) < 5e-4,
            abs(a["macro_p"] - e["Mp"]) < 5e-4, abs(a["macro_r"] - e["Mr"]) < 5e-4,
        ]
        if not all(checks):
            ok = False
            print(f"[VERIFY FAIL] {name}: got micro({a['micro_p']:.3f},{a['micro_r']:.3f}) "
                  f"macro({a['macro_p']:.3f},{a['macro_r']:.3f}) "
                  f"기대 micro({e['mp']},{e['mr']}) macro({e['Mp']},{e['Mr']})")
    return ok


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else "—"


def delta(v2, v1):
    if v2 is None or v1 is None:
        return "—"
    d = v2 - v1
    sign = "+" if d >= 0 else "−"
    return f"{sign}{abs(d):.3f}"


# ── item 집합 헬퍼 (pid, rep_key) 단위 diff ──────────────
def item_set(rows, key):       # key ∈ {"TP","FP","FN"}
    return {(r["id"], k) for r in rows for k in r[key]}


def by_id(rows):
    return {r["id"]: r for r in rows}


def build_md(st, rows1, rows2, a1, a2):
    L = []; A = L.append
    m1, m2 = by_id(rows1), by_id(rows2)

    A("# builds_on — relate 프롬프트 v2 vs v1 (한 변수 비교)")
    A("")
    A("같은 모델(`config.MODEL=gpt-5.4-mini`)·같은 lexicon(frozen)·같은 goldset(50편, frozen)·"
      "같은 채점 규칙으로, **relate 프롬프트만** v1→v2로 바꿨을 때의 변화. 측정 전용 — 채택 여부는 "
      "사람이 숫자를 보고 정한다.")
    A("")
    A("- v1(baseline) pred = `data/outputs/{id}.relations.json` (보존)")
    A("- v2 pred = `eval/experiments/relate_v2/{id}.relations.json`")
    A(f"- v1 재계산이 HANDOFF §7 기존 채점 숫자를 재현함을 확인하고 작성됨(검증 게이트 통과).")
    A("")

    # ── 1. 점수 비교 표 ──
    A("## 1. 점수 비교 (v1 / v2 / Δ)")
    A("")
    A("| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |")
    A("|---|--:|--:|--:|--:|--:|--:|--:|")
    for name in ["전체(50)", "new_collected", "from_corpus"]:
        x, y = a1[name], a2[name]
        A(f"| **{name}** v1 | {fmt(x['micro_p'])} | {fmt(x['micro_r'])} | {fmt(x['macro_p'])} | "
          f"{fmt(x['macro_r'])} | {x['sumTP']} | {x['sumFP']} | {x['sumFN']} |")
        A(f"| **{name}** v2 | {fmt(y['micro_p'])} | {fmt(y['micro_r'])} | {fmt(y['macro_p'])} | "
          f"{fmt(y['macro_r'])} | {y['sumTP']} | {y['sumFP']} | {y['sumFN']} |")
        A(f"| Δ | {delta(y['micro_p'],x['micro_p'])} | {delta(y['micro_r'],x['micro_r'])} | "
          f"{delta(y['macro_p'],x['macro_p'])} | {delta(y['macro_r'],x['macro_r'])} | "
          f"{y['sumTP']-x['sumTP']:+d} | {y['sumFP']-x['sumFP']:+d} | {y['sumFN']-x['sumFN']:+d} |")
    A("")
    A("> Δ = v2 − v1. (micro P↑ AND R not↓ 가 채택 신호.)")
    A("")

    # ── 2. FP 변화 ──
    fp1, fp2 = item_set(rows1, "FP"), item_set(rows2, "FP")
    fp_gone, fp_new = fp1 - fp2, fp2 - fp1

    def cat_of(rows_map, pid, k):
        r = rows_map.get(pid)
        return r["fp_cat"].get(k, "method_misjudged") if r else "method_misjudged"

    def fp_breakdown(items, rows_map):
        d = {"component_tool": [], "substrate": [], "method_misjudged": []}
        for pid, k in sorted(items):
            d[cat_of(rows_map, pid, k)].append((pid, k))
        return d

    gone_b = fp_breakdown(fp_gone, m1)   # 사라진 FP는 v1 분류로
    new_b = fp_breakdown(fp_new, m2)     # 새 FP는 v2 분류로

    A("## 2. FP 변화 (정밀도)")
    A("")
    A(f"v1 FP {len(fp1)}건 → v2 FP {len(fp2)}건. 사라진 FP **{len(fp_gone)}**, 새로 생긴 FP **{len(fp_new)}**.")
    A("")
    A("| 종류 | 사라진 FP(v1→없음) | 새 FP(v2에서 생김) | 순변화 |")
    A("|---|--:|--:|--:|")
    for cat in ["component_tool", "substrate", "method_misjudged"]:
        g, n = len(gone_b[cat]), len(new_b[cat])
        A(f"| {cat} | −{g} | +{n} | {n-g:+d} |")
    A("")
    A(f"**method_misjudged FP 순변화: {len(new_b['method_misjudged'])-len(gone_b['method_misjudged']):+d}** "
      f"(v1 {sum(1 for r in rows1 for k in r['FP'] if r['fp_cat'][k]=='method_misjudged')} → "
      f"v2 {sum(1 for r in rows2 for k in r['FP'] if r['fp_cat'][k]=='method_misjudged')}).")
    A("")
    A("**사라진 FP (정밀도 개선):**")
    A("")
    if not fp_gone:
        A("- (없음)")
    for cat in ["method_misjudged", "component_tool", "substrate"]:
        for pid, k in gone_b[cat]:
            A(f"- [{cat}] {label_of(st,k)} — {m1[pid]['title']} ({pid}, {m1[pid]['group']})")
    A("")
    A("**새로 생긴 FP (정밀도 악화):**")
    A("")
    if not fp_new:
        A("- (없음)")
    for cat in ["method_misjudged", "component_tool", "substrate"]:
        for pid, k in new_b[cat]:
            A(f"- [{cat}] {label_of(st,k)} — {m2[pid]['title']} ({pid}, {m2[pid]['group']})")
    A("")

    # ── 3. FN 변화 + 회귀 ──
    fn1, fn2 = item_set(rows1, "FN"), item_set(rows2, "FN")
    fn_recov, fn_newmiss = fn1 - fn2, fn2 - fn1
    tp1, tp2 = item_set(rows1, "TP"), item_set(rows2, "TP")
    regressions = tp1 - tp2     # v1 TP였는데 v2에서 빠진 것 (gold이므로 v2에선 FN)
    gained = tp2 - tp1          # v2에서 새로 맞힌 TP

    A("## 3. FN 변화 + 회귀 체크 (재현율)")
    A("")
    A(f"v1 FN {len(fn1)}건 → v2 FN {len(fn2)}건. 회복된 FN **{len(fn_recov)}**, 새로 놓친 FN **{len(fn_newmiss)}**.")
    A(f"TP: v1 {len(tp1)} → v2 {len(tp2)} (새로 맞힘 {len(gained)}, 잃음 {len(regressions)}).")
    A("")
    A("### 회복된 FN (v1 놓침 → v2 맞힘 또는 더이상 FN아님)")
    A("")

    def fn_reason_of(rows_map, pid, k):
        r = rows_map.get(pid)
        return r["fn_reason"].get(k, "?") if r else "?"

    if not fn_recov:
        A("- (없음)")
    for pid, k in sorted(fn_recov):
        was = fn_reason_of(m1, pid, k)
        now_tp = (pid, k) in tp2
        A(f"- {label_of(st,k)} — {m1[pid]['title']} ({pid}, {m1[pid]['group']}) "
          f"[v1: {was}{' → v2 TP' if now_tp else ' → v2 비FN'}]")
    A("")
    A("### 새로 놓친 FN (v1엔 없던 놓침이 v2에서 생김)")
    A("")
    if not fn_newmiss:
        A("- (없음)")
    for pid, k in sorted(fn_newmiss):
        now = fn_reason_of(m2, pid, k)
        A(f"- {label_of(st,k)} — {m2[pid]['title']} ({pid}, {m2[pid]['group']}) [v2: {now}]")
    A("")
    A("### ⚠️ 회귀 — v1에서 TP였는데 v2에서 잃은 항목 (가장 중요)")
    A("")
    A("v1에서 맞혔던 것을 v2가 놓친 것. gold 항목이므로 v2에선 FN(아래 진단).")
    A("")
    if not regressions:
        A("- (없음) ✅")
    for pid, k in sorted(regressions):
        now = fn_reason_of(m2, pid, k)
        A(f"- {label_of(st,k)} — {m2[pid]['title']} ({pid}, {m2[pid]['group']}) [v2 진단: {now}]")
    A("")

    # ── 4. 핵심 점검 2개 ──
    A("## 4. 핵심 점검")
    A("")
    rag = nc.canon("RAG")

    def verdict(rows_map, pid, k):
        r = rows_map.get(pid)
        if not r:
            return "논문없음"
        if k in r["TP"]:
            return "TP"
        if k in r["FP"]:
            return "FP"
        if k in r["FN"]:
            return f"FN({r['fn_reason'][k]})"
        return "—(미예측·미정답)"

    A("### (a) 패러다임 보호 작동? — RAPTOR / Rewrite-Retrieve-Read 가 RAG를 잡았나")
    A("")
    A("| 논문 | id | v1 RAG | v2 RAG |")
    A("|---|---|---|---|")
    for pid in ["2401.18059", "2305.14283"]:
        title = m1[pid]["title"] if pid in m1 else (m2[pid]["title"] if pid in m2 else pid)
        A(f"| {title} | {pid} | {verdict(m1,pid,rag)} | {verdict(m2,pid,rag)} |")
    A("")
    A("### (b) 회귀 없나? — v1에서 TP=RAG였던 논문 중 v2에서 RAG가 빠진 것")
    A("")
    rag_tp_v1 = [r for r in rows1 if rag in r["TP"]]
    A(f"v1에서 RAG가 TP였던 논문 {len(rag_tp_v1)}편. 그 중 v2에서 RAG를 잃은 것:")
    A("")
    lost_rag = [r for r in rag_tp_v1 if (r["id"], rag) not in tp2]
    if not lost_rag:
        A("- (없음) ✅ — ONLY-as-comparison 규칙의 RAG 부작용 없음")
    for r in lost_rag:
        A(f"- {r['title']} ({r['id']}, {r['group']}) [v2: {verdict(m2, r['id'], rag)}]")
    A("")

    # ── 5. 해석 ──
    A("## 5. 해석")
    A("")
    tot1, tot2 = a1["전체(50)"], a2["전체(50)"]
    dP = tot2["micro_p"] - tot1["micro_p"]
    dR = tot2["micro_r"] - tot1["micro_r"]
    direction = ("정밀도↑·재현율 유지/상승 — 채택 신호에 부합" if dP > 0 and dR >= -1e-9
                 else "정밀도↑이나 재현율↓ — ONLY-as-comparison 규칙이 일부 과하게 먹었을 수 있음(위 회귀 목록 확인)"
                 if dP > 0 else "정밀도↓ — v2가 기대와 반대" if dP < 0
                 else "정밀도 변화 미미")
    A(f"전체 micro P {fmt(tot1['micro_p'])}→{fmt(tot2['micro_p'])} ({delta(tot2['micro_p'],tot1['micro_p'])}), "
      f"micro R {fmt(tot1['micro_r'])}→{fmt(tot2['micro_r'])} ({delta(tot2['micro_r'],tot1['micro_r'])}). "
      f"{direction}. "
      f"method_misjudged FP는 {sum(1 for r in rows1 for k in r['FP'] if r['fp_cat'][k]=='method_misjudged')}"
      f"→{sum(1 for r in rows2 for k in r['FP'] if r['fp_cat'][k]=='method_misjudged')}건으로 변했고, "
      f"v1에서 맞혔다 v2에서 잃은 회귀는 {len(regressions)}건이다. "
      f"이름을 프롬프트에 박지 않았으므로(고유명사 예시 v1과 동일) 50편에서의 점수 변화는 "
      f"규칙 일반화의 효과이지 우연한 적합이 아니다. 채택 여부는 위 표와 회귀 목록을 보고 사람이 정한다.")
    A("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))


def main():
    st = nc.load_lex_state()
    labels = load_labels()
    groups = load_groups()

    rows1, miss1 = score_all(st, labels, groups, load_pred_v1)
    rows2, miss2 = score_all(st, labels, groups, load_pred_v2)
    if miss1:
        print(f"⚠️ v1 누락 {len(miss1)}편: {miss1} — 중단"); sys.exit(1)
    if miss2:
        print(f"⚠️ v2 누락 {len(miss2)}편: {miss2} — exp_relate_v2.py 먼저 완주 필요. 중단"); sys.exit(1)

    a1 = aggs_by_group(rows1)
    a2 = aggs_by_group(rows2)

    if not verify_v1(a1):
        print("\n검증 실패 — v1 재계산이 §7 기존 숫자와 불일치. 채점 구현 오류 → 중단."); sys.exit(1)
    print("검증 OK — v1 재계산이 §7 표 재현 일치.")

    # 콘솔 요약
    for name in ["전체(50)", "new_collected", "from_corpus"]:
        x, y = a1[name], a2[name]
        print(f"\n[{name}]")
        print(f"  v1  microP={fmt(x['micro_p'])} microR={fmt(x['micro_r'])} "
              f"macroP={fmt(x['macro_p'])} macroR={fmt(x['macro_r'])} (TP{x['sumTP']}/FP{x['sumFP']}/FN{x['sumFN']})")
        print(f"  v2  microP={fmt(y['micro_p'])} microR={fmt(y['micro_r'])} "
              f"macroP={fmt(y['macro_p'])} macroR={fmt(y['macro_r'])} (TP{y['sumTP']}/FP{y['sumFP']}/FN{y['sumFN']})")

    build_md(st, rows1, rows2, a1, a2)
    print(f"\n생성: {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
