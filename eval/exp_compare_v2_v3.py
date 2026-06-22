"""실험 채점: relate v2(baseline) vs v3(evidence) 비교 + evidence 분석.

한 변수만 바뀐 비교 — evidence 요구 on/off. 채점 규칙은 score_buildson.py / exp_compare_v1_v2.py
와 동일(normalize_core 재사용). 두 출력 형태가 다름:
  v2 = ["RAG", ...]                         (문자열 리스트)
  v3 = [{"name":"RAG","evidence":"..."}, ...] (객체 리스트)
v3은 name만 뽑아 채점하고, evidence는 리포트에만 쓴다.

pred 소스:
- v2(baseline) = eval/experiments/relate_v2/{id}.relations.json        (덮어쓰기 금지, 읽기만)
- v3           = eval/experiments/relate_v3_evidence/{id}.relations.json

검증 게이트(HANDOFF §7): v2 재계산이 직전 v2 숫자(전체 P0.597/R0.667 등)를 재현해야 한다.

이 실험의 목적은 점수 상승이 아니라 (1) legibility(왜 골랐나를 본문 인용으로) (2) grounding이
비교-baseline FP(method_misjudged)를 줄이는지. 노이즈 바닥 미측정 → 작은 Δ는 단정 금지.

산출물: eval/reports/buildson_evidence_v3.md (커밋 대상)
실행: uv run python eval/exp_compare_v2_v3.py
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
V3_DIR = ROOT / "eval/experiments/relate_v3_evidence"
REPORTS_DIR = ROOT / "eval/reports"
OUT_MD = REPORTS_DIR / "buildson_evidence_v3.md"

# FP 3분류 (report_buildson.py / exp_compare_v1_v2.py 와 동일 집합)
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

# §7 검증 기대치 (v2 baseline 재현 대상) — micro P/R
EXPECT_V2 = {
    "전체(50)":       dict(mp=0.597, mr=0.667),
    "new_collected": dict(mp=0.654, mr=0.515),
    "from_corpus":   dict(mp=0.561, mr=0.852),
}


def load_labels():
    return json.load(open(LABELS_PATH))["labels"]


def load_groups():
    p = json.load(open(PAPERS_PATH))
    return {"new_collected": set(p["new_collected"]), "from_corpus": set(p["from_corpus"])}


def load_pred_v2(pid):
    """v2: builds_on = 문자열 리스트."""
    fp = V2_DIR / f"{pid}.relations.json"
    if not fp.exists():
        return None
    return json.load(open(fp)).get("builds_on", [])


def load_v3_raw(pid):
    """v3: builds_on = [{name, evidence}]. 원형 그대로(이름+근거)."""
    fp = V3_DIR / f"{pid}.relations.json"
    if not fp.exists():
        return None
    return json.load(open(fp)).get("builds_on", [])


def names_of_v3(raw):
    return [b["name"] for b in raw]


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
        "TP": TP, "FP": FP, "FN": FN, "fn_reason": fn_reason, "fp_cat": fp_cat,
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
    return {
        "n": len(rows), "sumTP": sTP, "sumFP": sFP, "sumFN": sFN,
        "micro_p": micro_p, "micro_r": micro_r, "macro_p": macro_p, "macro_r": macro_r,
    }


def score_all(st, labels, groups, get_names):
    rows, missing = [], []
    for pid, lab in labels.items():
        names = get_names(pid)
        if names is None:
            missing.append(pid)
            continue
        grp = ("new_collected" if pid in groups["new_collected"]
               else "from_corpus" if pid in groups["from_corpus"] else "?")
        rows.append(score_paper(st, pid, lab["title"], grp, lab["builds_on"], names))
    return rows, missing


def aggs_by_group(rows):
    return {
        "전체(50)": aggregate(rows),
        "new_collected": aggregate([r for r in rows if r["group"] == "new_collected"]),
        "from_corpus": aggregate([r for r in rows if r["group"] == "from_corpus"]),
    }


def verify_v2(aggs):
    ok = True
    for name, e in EXPECT_V2.items():
        a = aggs[name]
        if not (abs(a["micro_p"] - e["mp"]) < 5e-4 and abs(a["micro_r"] - e["mr"]) < 5e-4):
            ok = False
            print(f"[VERIFY FAIL] {name}: got micro({a['micro_p']:.3f},{a['micro_r']:.3f}) "
                  f"기대 ({e['mp']},{e['mr']})")
    return ok


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else "—"


def delta(v2, v1):
    if v2 is None or v1 is None:
        return "—"
    d = v2 - v1
    return f"{'+' if d >= 0 else '−'}{abs(d):.3f}"


def item_set(rows, key):
    return {(r["id"], k) for r in rows for k in r[key]}


def by_id(rows):
    return {r["id"]: r for r in rows}


def md_escape(s):
    return s.replace("|", "\\|").replace("\n", " ").strip()


EV_CLIP = 200   # evidence 표시 상한(자). 모델이 가끔 구조토큰을 문자열에 흘려 runaway 발생.


def clip(s):
    s = s.strip()
    return s if len(s) <= EV_CLIP else s[:EV_CLIP] + " …[clipped]"


def build_md(st, rows2, rows3, a2, a3, v3_raw, labels):
    L = []; A = L.append
    m2, m3 = by_id(rows2), by_id(rows3)

    A("# builds_on — evidence(v3) vs v2 (한 변수: 본문 근거 요구)")
    A("")
    A("라이브 프롬프트는 v2 유지. 그 위에 builds_on 각 항목에 **본문 근거(evidence)**를 같이 "
      "뽑게 한 v3과 비교. 같은 모델(`gpt-5.4-mini`)·lexicon(frozen)·goldset(50편)·채점 규칙. "
      "v3은 `name`만 채점, `evidence`는 리포트용. 라이브 relate.py·normalize·lexicon 무수정.")
    A("")
    A("> ⚠️ **노이즈 바닥 미측정** — 직전 실험에서 프롬프트 효과가 run-to-run 노이즈(±0.04) "
      "수준이었다. 작은 Δ는 해석 보류. **FP 종류 변화·회귀 목록·evidence 인용**만 신뢰하라. "
      "이 실험의 주 목적은 점수가 아니라 (1) legibility (2) grounding의 method_misjudged 억제 여부.")
    A("")
    A("- v2(baseline) pred = `eval/experiments/relate_v2/{id}.relations.json` (보존)")
    A("- v3 pred = `eval/experiments/relate_v3_evidence/{id}.relations.json`")
    A("- v2 재계산이 §7 직전 v2 숫자를 재현함을 확인하고 작성됨(검증 게이트 통과).")
    A("")

    # ── 1. 점수 비교 ──
    A("## 1. 점수 비교 (v2 / v3 / Δ)")
    A("")
    A("| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |")
    A("|---|--:|--:|--:|--:|--:|--:|--:|")
    for name in ["전체(50)", "new_collected", "from_corpus"]:
        x, y = a2[name], a3[name]
        A(f"| **{name}** v2 | {fmt(x['micro_p'])} | {fmt(x['micro_r'])} | {fmt(x['macro_p'])} | "
          f"{fmt(x['macro_r'])} | {x['sumTP']} | {x['sumFP']} | {x['sumFN']} |")
        A(f"| **{name}** v3 | {fmt(y['micro_p'])} | {fmt(y['micro_r'])} | {fmt(y['macro_p'])} | "
          f"{fmt(y['macro_r'])} | {y['sumTP']} | {y['sumFP']} | {y['sumFN']} |")
        A(f"| Δ | {delta(y['micro_p'],x['micro_p'])} | {delta(y['micro_r'],x['micro_r'])} | "
          f"{delta(y['macro_p'],x['macro_p'])} | {delta(y['macro_r'],x['macro_r'])} | "
          f"{y['sumTP']-x['sumTP']:+d} | {y['sumFP']-x['sumFP']:+d} | {y['sumFN']-x['sumFN']:+d} |")
    A("")
    A("> Δ = v3 − v2. 노이즈 바닥 미측정이므로 작은 micro Δ는 단정 금지.")
    A("")

    # ── 2. FP 변화 ──
    fp2, fp3 = item_set(rows2, "FP"), item_set(rows3, "FP")
    fp_gone, fp_new = fp2 - fp3, fp3 - fp2

    def cat_of(rows_map, pid, k):
        r = rows_map.get(pid)
        return r["fp_cat"].get(k, "method_misjudged") if r else "method_misjudged"

    def breakdown(items, rows_map):
        d = {"component_tool": [], "substrate": [], "method_misjudged": []}
        for pid, k in sorted(items):
            d[cat_of(rows_map, pid, k)].append((pid, k))
        return d

    gone_b, new_b = breakdown(fp_gone, m2), breakdown(fp_new, m3)
    mm_v2 = sum(1 for r in rows2 for k in r["FP"] if r["fp_cat"][k] == "method_misjudged")
    mm_v3 = sum(1 for r in rows3 for k in r["FP"] if r["fp_cat"][k] == "method_misjudged")

    A("## 2. FP 변화 (grounding이 헛것을 줄였나)")
    A("")
    A(f"v2 FP {len(fp2)}건 → v3 FP {len(fp3)}건. 사라진 FP **{len(fp_gone)}**, 새 FP **{len(fp_new)}**.")
    A("")
    A("| 종류 | 사라진(v2→없음) | 새(v3) | 순변화 |")
    A("|---|--:|--:|--:|")
    for cat in ["component_tool", "substrate", "method_misjudged"]:
        g, n = len(gone_b[cat]), len(new_b[cat])
        A(f"| {cat} | −{g} | +{n} | {n-g:+d} |")
    A("")
    A(f"**method_misjudged FP: v2 {mm_v2} → v3 {mm_v3} ({mm_v3-mm_v2:+d}).** "
      f"(grounding이 비교-baseline 오인을 줄였는지의 핵심 지표.)")
    A("")
    A("**사라진 FP:**")
    A("")
    if not fp_gone:
        A("- (없음)")
    for cat in ["method_misjudged", "component_tool", "substrate"]:
        for pid, k in gone_b[cat]:
            A(f"- [{cat}] {label_of(st,k)} — {m2[pid]['title']} ({pid}, {m2[pid]['group']})")
    A("")
    A("**새로 생긴 FP:**")
    A("")
    if not fp_new:
        A("- (없음)")
    for cat in ["method_misjudged", "component_tool", "substrate"]:
        for pid, k in new_b[cat]:
            A(f"- [{cat}] {label_of(st,k)} — {m3[pid]['title']} ({pid}, {m3[pid]['group']})")
    A("")

    # ── 3. 회귀 체크 ──
    tp2, tp3 = item_set(rows2, "TP"), item_set(rows3, "TP")
    regressions = tp2 - tp3
    gained = tp3 - tp2

    def fn_reason_of(rows_map, pid, k):
        r = rows_map.get(pid)
        return r["fn_reason"].get(k, "?") if r else "?"

    A("## 3. 회귀 체크 — v2에서 TP였는데 v3에서 잃은 항목")
    A("")
    A(f"TP: v2 {len(tp2)} → v3 {len(tp3)} (새로 맞힘 {len(gained)}, 잃음 {len(regressions)}). "
      f"잃은 항목은 gold이므로 v3에선 FN.")
    A("")
    if not regressions:
        A("- (없음) ✅")
    for pid, k in sorted(regressions):
        A(f"- {label_of(st,k)} — {m3[pid]['title']} ({pid}, {m3[pid]['group']}) "
          f"[v3 진단: {fn_reason_of(m3, pid, k)}]")
    A("")
    if gained:
        A("**참고 — v3에서 새로 맞힌 TP:**")
        A("")
        for pid, k in sorted(gained):
            A(f"- {label_of(st,k)} — {m3[pid]['title']} ({pid}, {m3[pid]['group']})")
        A("")

    # ── 4. ★ evidence 항목 표 (주 산출물) ──
    A("## 4. ★ evidence 항목 표 (주 산출물 — 모델이 왜 골랐나)")
    A("")
    A("v3가 emit한 builds_on 항목 전부(채점 후). 판정=TP/FP(채점은 rep_key 공간, lexicon "
      "status 필터 후). **FP를 위로** 정렬. evidence가 비교 문장이면(예 \"we compare against X\") "
      "→ 모델이 비교를 build-on으로 오독한 grounding 실패가 인용으로 드러난다.")
    A("")
    A("> 주의: status 필터로 그래프에서 빠진 항목(pending/rejected)은 채점 pred에 없어 "
      "여기 verdict가 `dropped`로 뜬다(헛것도 정답도 아님 — lexicon 미등록 신개념).")
    A("")
    A("| 논문 | id | name(emit) | 판정 | FP종류 | evidence 인용 |")
    A("|---|---|---|---|---|---|")

    # verdict 계산: emit된 각 name → rep_key → TP/FP/dropped
    def verdict_for(pid, name):
        r = m3.get(pid)
        rk = nc.resolve(st, name)[0]
        if r is None:
            return rk, "?", ""
        if rk in r["TP"]:
            return rk, "TP", ""
        if rk in r["FP"]:
            return rk, "FP", r["fp_cat"][rk]
        return rk, "dropped", ""   # status 필터로 그래프에서 빠짐(pred에 없음)

    table_rows = []
    for pid in labels:
        for b in v3_raw.get(pid, []):
            rk, verdict, fpcat = verdict_for(pid, b["name"])
            table_rows.append({
                "pid": pid, "title": m3[pid]["title"] if pid in m3 else pid,
                "name": b["name"], "verdict": verdict, "fpcat": fpcat,
                "evidence": b.get("evidence", ""),
            })
    # FP 먼저, 그다음 dropped, 그다음 TP
    order = {"FP": 0, "dropped": 1, "TP": 2, "?": 3}
    table_rows.sort(key=lambda t: (order.get(t["verdict"], 9), t["pid"]))
    for t in table_rows:
        A(f"| {md_escape(t['title'])} | {t['pid']} | {md_escape(t['name'])} | {t['verdict']} | "
          f"{t['fpcat'] or '—'} | {md_escape(clip(t['evidence']))} |")
    A("")
    n_fp = sum(1 for t in table_rows if t["verdict"] == "FP")
    n_tp = sum(1 for t in table_rows if t["verdict"] == "TP")
    n_drop = sum(1 for t in table_rows if t["verdict"] == "dropped")
    n_runaway = sum(1 for t in table_rows if len(t["evidence"]) > EV_CLIP)
    A(f"합계 emit {len(table_rows)}건 = TP {n_tp} + FP {n_fp} + dropped {n_drop}. "
      f"(evidence가 {EV_CLIP}자 초과라 클립된 항목 {n_runaway}건 — 일부는 모델이 구조토큰 "
      f"`}}]}}`을 문자열에 흘린 runaway 출력으로, evidence 자체의 신뢰성 한계를 보여줌.)")
    A("")

    # ── 5. 해석 ──
    A("## 5. 해석")
    A("")
    t2, t3 = a2["전체(50)"], a3["전체(50)"]
    A(f"전체 micro P {fmt(t2['micro_p'])}→{fmt(t3['micro_p'])} ({delta(t3['micro_p'],t2['micro_p'])}), "
      f"R {fmt(t2['micro_r'])}→{fmt(t3['micro_r'])} ({delta(t3['micro_r'],t2['micro_r'])}). "
      f"노이즈 바닥(±0.04) 미측정이라 이 micro Δ 자체는 단정하지 않는다. "
      f"메커니즘 지표인 **method_misjudged FP는 {mm_v2}→{mm_v3}건**으로 움직였고, "
      f"v2에서 맞혔다 v3에서 잃은 회귀는 {len(regressions)}건이다. "
      f"evidence 표(§4)는 emit {len(table_rows)}건 각각에 본문 인용을 붙여, 특히 FP {n_fp}건이 "
      f"'정말 build-on 근거가 있어 골랐는지' vs '비교 문장을 오독했는지'를 인용 한 줄로 "
      f"판별 가능하게 한다 — 이게 이 실험의 주 산출물(legibility)이다. "
      f"evidence가 (a) FP를 줄였는지는 위 method_misjudged 순변화로, (b) 인용이 FP 원인 진단에 "
      f"쓸 만한지는 §4 표의 인용 품질로 사람이 판단한다. 채택은 숫자/인용을 본 뒤 별도 작업.")
    A("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))


def main():
    st = nc.load_lex_state()
    labels = load_labels()
    groups = load_groups()

    rows2, miss2 = score_all(st, labels, groups, load_pred_v2)
    # v3: 원형(name+evidence) 로드 후 이름만 채점에 사용
    v3_raw = {}
    miss3 = []
    for pid in labels:
        raw = load_v3_raw(pid)
        if raw is None:
            miss3.append(pid)
        else:
            v3_raw[pid] = raw
    if miss2:
        print(f"⚠️ v2 누락 {len(miss2)}편: {miss2} — 중단"); sys.exit(1)
    if miss3:
        print(f"⚠️ v3 누락 {len(miss3)}편: {miss3} — exp_relate_v3_evidence.py 먼저 완주. 중단")
        sys.exit(1)

    rows3, _ = score_all(st, labels, groups, lambda pid: names_of_v3(v3_raw[pid]))

    a2 = aggs_by_group(rows2)
    a3 = aggs_by_group(rows3)

    if not verify_v2(a2):
        print("\n검증 실패 — v2 재계산이 §7 숫자와 불일치. 중단."); sys.exit(1)
    print("검증 OK — v2 재계산이 §7 표 재현 일치.")

    for name in ["전체(50)", "new_collected", "from_corpus"]:
        x, y = a2[name], a3[name]
        print(f"\n[{name}]")
        print(f"  v2  microP={fmt(x['micro_p'])} microR={fmt(x['micro_r'])} (TP{x['sumTP']}/FP{x['sumFP']}/FN{x['sumFN']})")
        print(f"  v3  microP={fmt(y['micro_p'])} microR={fmt(y['micro_r'])} (TP{y['sumTP']}/FP{y['sumFP']}/FN{y['sumFN']})")

    build_md(st, rows2, rows3, a2, a3, v3_raw, labels)
    print(f"\n생성: {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
