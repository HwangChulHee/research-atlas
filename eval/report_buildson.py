"""report_buildson: 채점 결과를 사람이 읽는 분석 문서로 렌더링.

측정은 score_buildson.py에서 끝났다. 이건 그 결과를 항목 단위로 펼치고
FP/FN을 종류별로 분류해 "무엇을 싸게 고칠 수 있고 무엇이 구조적 한계인지"
설명하는 문서를 만든다. 데이터·점수는 바꾸지 않는다(읽기 전용).

산출물(커밋 대상, eval/reports/):
- buildson_analysis_v1.md  — 사람이 읽는 자세한 분석
- buildson_items_v1.csv    — 항목 1줄씩(스프레드시트 슬라이스용)

실행: uv run python eval/report_buildson.py
"""
import sys
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from pipeline import config
from pipeline import normalize_core as nc

LABELS_PATH = ROOT / "eval/goldset/labels.json"
PAPERS_PATH = ROOT / "eval/goldset/papers.json"
REPORTS_DIR = ROOT / "eval/reports"

# ── FP 3분류 (canon 비교용 집합). normalize_core.canon으로 정규화해 대조.
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

# 사람이 읽는 태그
FN_TAG = {"lexicon_dropped": "[탈락]", "not_extracted": "[추출X]"}
FP_TAG = {"component_tool": "[부품/도구]", "substrate": "[substrate]",
          "method_misjudged": "[방법오인]"}


def load_labels():
    return json.load(open(LABELS_PATH))["labels"]


def load_groups():
    p = json.load(open(PAPERS_PATH))
    return {"new_collected": set(p["new_collected"]), "from_corpus": set(p["from_corpus"])}


def load_pred(pid):
    fp = config.OUT_DIR / f"{pid}.relations.json"
    if not fp.exists():
        return None
    return json.load(open(fp)).get("builds_on", [])


def fp_category(st, rk):
    """FP rep_key → component_tool / substrate / method_misjudged. (rk는 이미 canon값)"""
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

    TP = gold & pred
    FP = pred - gold
    FN = gold - pred

    fn_reason = {k: ("lexicon_dropped" if k in pred_raw else "not_extracted") for k in FN}
    fp_cat = {k: fp_category(st, k) for k in FP}

    tp, fp, fn = len(TP), len(FP), len(FN)
    P = tp / (tp + fp) if (tp + fp) else None
    R = tp / (tp + fn) if (tp + fn) else None

    return {
        "id": pid, "title": title, "group": group,
        "gold": sorted(gold), "pred": sorted(pred), "pred_raw": sorted(pred_raw),
        "TP": sorted(TP), "FP": sorted(FP), "FN": sorted(FN),
        "fn_reason": fn_reason, "fp_cat": fp_cat,
        "P": P, "R": R,
    }


def aggregate(rows):
    sTP = sum(len(r["TP"]) for r in rows)
    sFP = sum(len(r["FP"]) for r in rows)
    sFN = sum(len(r["FN"]) for r in rows)
    micro_p = sTP / (sTP + sFP) if (sTP + sFP) else None
    micro_r = sTP / (sTP + sFN) if (sTP + sFN) else None
    p_vals = [r["P"] for r in rows if r["P"] is not None]
    r_vals = [r["R"] for r in rows if r["R"] is not None]
    macro_p = sum(p_vals) / len(p_vals) if p_vals else None
    macro_r = sum(r_vals) / len(r_vals) if r_vals else None
    lex_drop = sum(1 for r in rows for v in r["fn_reason"].values() if v == "lexicon_dropped")
    not_ext = sum(1 for r in rows for v in r["fn_reason"].values() if v == "not_extracted")
    return {
        "n": len(rows), "sumTP": sTP, "sumFP": sFP, "sumFN": sFN,
        "micro_p": micro_p, "micro_r": micro_r,
        "macro_p": macro_p, "macro_r": macro_r,
        "fn_lex_drop": lex_drop, "fn_not_ext": not_ext,
    }


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else "—"


def verify(aggs):
    """§8 기대치 재현 확인. 다르면 멈춤."""
    exp = {
        "전체(50)": dict(mp=0.562, mr=0.683, Mp=0.708, Mr=0.785, ld=3, ne=16),
        "new_collected": dict(mp=0.708, mr=0.515, Mp=0.792, Mr=0.654, ld=3, ne=13),
        "from_corpus": dict(mp=0.490, mr=0.889, Mp=0.651, Mr=0.886, ld=0, ne=3),
    }
    ok = True
    for name, e in exp.items():
        a = aggs[name]
        checks = [
            abs(a["micro_p"] - e["mp"]) < 5e-4,
            abs(a["micro_r"] - e["mr"]) < 5e-4,
            abs(a["macro_p"] - e["Mp"]) < 5e-4,
            abs(a["macro_r"] - e["Mr"]) < 5e-4,
            a["fn_lex_drop"] == e["ld"], a["fn_not_ext"] == e["ne"],
        ]
        if not all(checks):
            ok = False
            print(f"[VERIFY FAIL] {name}: got micro({fmt(a['micro_p'])},{fmt(a['micro_r'])}) "
                  f"macro({fmt(a['macro_p'])},{fmt(a['macro_r'])}) FN({a['fn_lex_drop']}/{a['fn_not_ext']})")
    return ok


# ────────────────────────────────────────────────────────── CSV

def write_csv(st, rows, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["paper_id", "title", "group", "concept", "verdict",
                    "fn_reason", "fp_category", "concept_status"])
        n = 0
        for r in rows:
            for k in r["TP"]:
                w.writerow([r["id"], r["title"], r["group"], label_of(st, k),
                            "TP", "", "", nc.status_of(st, k)])
                n += 1
            for k in r["FP"]:
                w.writerow([r["id"], r["title"], r["group"], label_of(st, k),
                            "FP", "", r["fp_cat"][k], nc.status_of(st, k)])
                n += 1
            for k in r["FN"]:
                w.writerow([r["id"], r["title"], r["group"], label_of(st, k),
                            "FN", r["fn_reason"][k], "", nc.status_of(st, k)])
                n += 1
    return n


# ────────────────────────────────────────────────────────── MD

def join_tagged(st, keys, tagmap, reasons):
    if not keys:
        return "—"
    return ", ".join(f"{label_of(st, k)}{tagmap[reasons[k]]}" for k in keys)


def write_md(st, rows, aggs, path):
    L = []
    A = L.append

    # (1) 머리말
    A("# builds_on 채점 결과 — 항목별 분석 (v1)")
    A("")
    A("이 문서는 `eval/score_buildson.py`가 낸 채점 결과를 **항목 단위로 펼쳐** "
      "읽기 쉽게 푼 분석이다. 정답지(`eval/goldset/labels.json`, 50편, frozen) 대비 "
      "파이프라인이 뽑은 builds_on(논문→방법적 조상 계보) 항목을, 논문 50편 각각에 대해 "
      "맞힘/틀리게추가/놓침으로 나누고, 틀린 것들을 종류별로 분류한다. "
      "**측정은 이미 끝났고, 여기서 데이터·점수를 바꾸지 않는다.**")
    A("")
    A("## 용어")
    A("")
    A("- **TP (맞힘)** — 정답에도 있고 파이프라인도 맞게 댄 항목.")
    A("- **FP (틀리게 더 붙임)** — 파이프라인이 댔는데 정답엔 없는 항목.")
    A("- **FN (놓침)** — 정답엔 있는데 파이프라인이 못 댄 항목.")
    A("- **lexicon 필터** — 파이프라인 날것(relate 출력) 중 사전(lexicon)에서 "
      "`approved`/`unreviewed`인 개념만 그래프에 노드로 남고, `pending`/`rejected`는 빠진다. "
      "채점도 그래프에 실제로 남는 것(=필터 통과분)만 본다. 그래서 파이프라인이 옳게 뱉어도 "
      "그 개념이 아직 `pending`이면 채점에선 놓침(FN)으로 잡힌다.")
    A("- **P(정밀도)** = TP/(TP+FP), **R(재현율)** = TP/(TP+FN).")
    A("")

    # (2) 점수 요약
    A("## 1. 점수 요약")
    A("")
    A("| 그룹 | n | micro P | micro R | macro P | macro R | FN: lexicon탈락 | FN: 추출X |")
    A("|---|--:|--:|--:|--:|--:|--:|--:|")
    for name in ["전체(50)", "new_collected", "from_corpus"]:
        a = aggs[name]
        A(f"| {name} | {a['n']} | {fmt(a['micro_p'])} | {fmt(a['micro_r'])} | "
          f"{fmt(a['macro_p'])} | {fmt(a['macro_r'])} | {a['fn_lex_drop']} | {a['fn_not_ext']} |")
    A("")
    A("- **전체** micro P=0.562 / R=0.683 — 댄 것의 56%가 맞고, 정답의 68%를 잡았다.")
    A("- **new_collected** P=0.708 / R=0.515 — *정밀도는 높지만 재현율이 낮다*. 댄 건 대체로 "
      "맞는데 최근 논문의 형제 계보를 절반 가까이 놓친다.")
    A("- **from_corpus** P=0.490 / R=0.889 — *정반대*. 뻔한 조상은 거의 다 잡지만(R↑) "
      "intro의 비교·부품까지 과추출해 정밀도가 절반(P↓).")
    A("- macro는 논문별 P·R 평균(P는 pred≠∅ 논문만, R은 gold≠∅ 논문만 분모) — "
      "큰 정답을 가진 소수 논문에 덜 휘둘린 값이라 micro보다 높다.")
    A("")

    # (3) 논문별 상세 표
    A("## 2. 논문별 상세 (50편)")
    A("")
    A("> FN 태그: `[탈락]`=lexicon에서 pending/rejected라 잘림(검수하면 복구), "
      "`[추출X]`=애초에 안 뽑힘(abstract-only 한계). "
      "FP 태그: `[부품/도구]`=계보 아님(reject 후보), `[substrate]`=백본(문맥의존), "
      "`[방법오인]`=진짜 방법인데 이 논문에선 baseline/비교.")
    A("")
    A("| id | 제목 | 그룹 | 정답(gold) | 맞힘(TP) | 틀리게추가(FP) | 놓침(FN) | P | R |")
    A("|---|---|---|---|---|---|---|--:|--:|")
    for r in rows:
        gold = ", ".join(label_of(st, k) for k in r["gold"]) or "—(없음)"
        tp = ", ".join(label_of(st, k) for k in r["TP"]) or "—"
        fp = join_tagged(st, r["FP"], FP_TAG, r["fp_cat"])
        fn = join_tagged(st, r["FN"], FN_TAG, r["fn_reason"])
        rstr = fmt(r["R"]) if r["R"] is not None else "—(gold∅)"
        A(f"| {r['id']} | {r['title']} | {r['group']} | {gold} | {tp} | {fp} | {fn} | "
          f"{fmt(r['P'])} | {rstr} |")
    A("")

    # (4) FP 분석
    fp_by_cat = {"component_tool": [], "substrate": [], "method_misjudged": []}
    for r in rows:
        for k in r["FP"]:
            fp_by_cat[r["fp_cat"][k]].append((r, k))
    total_fp = sum(len(v) for v in fp_by_cat.values())

    A("## 3. FP 분석 — 정밀도를 깎는 것")
    A("")
    A(f"틀리게 더 붙인 항목 총 **{total_fp}건**. 종류별로 갈라야 \"정밀도를 싸게 고칠 수 있나\"의 "
      "답이 나온다.")
    A("")
    cat_desc = {
        "component_tool": "**부품/도구 (reject 후보, 싸게 제거 가능)** — PPO·MCTS·RAGAS 같은 "
        "학습 부품·평가도구. 영영 계보가 아니므로 lexicon에서 reject하면 그래프에서 전역 제거된다. "
        "가장 싸게 정밀도를 올릴 수 있는 부분.",
        "substrate": "**substrate / 백본 (문맥의존, 전역 reject 불가)** — BERT·GPT-3·T5 등. "
        "이건 DPR·ColBERT 같은 논문에선 *정답 계보*이기도 해서 전역 reject가 불가능하다. "
        "논문별로 baseline인지 계보인지 판단이 필요 → 사전 하나로 못 고침.",
        "method_misjudged": "**방법 오인 (relate 판단 문제, 사전으로 못 고침)** — Self-RAG·ReAct·"
        "RAG·GraphRAG처럼 진짜 방법 노드인데 *이 논문에선* baseline/비교로 등장한 걸 계보로 오인한 것. "
        "개념 자체는 유효(approved/unreviewed)라 lexicon으로 못 거른다. relate.py가 본문 맥락에서 "
        "\"딛고 선 것\"과 \"비교 대상\"을 구분해야 풀린다.",
    }
    for cat in ["component_tool", "substrate", "method_misjudged"]:
        items = fp_by_cat[cat]
        A(f"### {FP_TAG[cat]} {cat} — {len(items)}건")
        A("")
        A(cat_desc[cat])
        A("")
        if not items:
            A("- (없음)")
        else:
            for r, k in items:
                A(f"- {label_of(st, k)} — {r['title']} ({r['id']}, {r['group']})")
        A("")

    # (5) FN 분석
    A("## 4. FN 분석 — 재현율을 깎는 것")
    A("")
    fn_lex, fn_not = [], []
    for r in rows:
        for k in r["FN"]:
            (fn_lex if r["fn_reason"][k] == "lexicon_dropped" else fn_not).append((r, k))
    A(f"놓친 항목 총 **{len(fn_lex) + len(fn_not)}건** = lexicon탈락 {len(fn_lex)} + 추출X {len(fn_not)}.")
    A("")
    A("### [탈락] lexicon_dropped — 검수하면 복구되는 놓침")
    A("")
    A("파이프라인은 **맞게 뱉었는데** 그 개념이 사전에서 `pending`이라 그래프에서 잘렸다. "
      "lexicon 검수로 approve하면 즉시 TP로 살아난다 — *추출 품질 문제가 아니다*.")
    A("")
    if not fn_lex:
        A("- (없음)")
    for r, k in fn_lex:
        A(f"- {label_of(st, k)} — {r['title']} ({r['id']}, {r['group']}, status={nc.status_of(st, k)})")
    A("")
    A("### [추출X] not_extracted — abstract-only의 본질적 한계")
    A("")
    A("애초에 파이프라인이 뽑지도 못한 것. 대부분 related work에 나열되는 *형제 계보*(같은 시기 경쟁 "
      "방법)로, abstract+intro만 보는 현재 입력에선 \"딛고 선 조상\"으로 드러나지 않는다.")
    A("")
    for grp in ["new_collected", "from_corpus"]:
        sub = [(r, k) for (r, k) in fn_not if r["group"] == grp]
        A(f"**{grp} ({len(sub)}건):**")
        A("")
        if not sub:
            A("- (없음)")
        for r, k in sub:
            A(f"- {label_of(st, k)} — {r['title']} ({r['id']})")
        A("")

    # (6) 관찰/해석
    A("## 5. 관찰 / 해석")
    A("")
    A("**두 그룹이 정반대다.** from_corpus(오래된·확립된 논문)는 재현율↑·정밀도↓ — 뻔한 조상(거의 "
      "RAG)은 잘 잡지만 intro에 같이 언급되는 형제·baseline·부품까지 과추출한다. "
      "new_collected(최근 수집 논문)는 정밀도↑·재현율↓ — 댄 건 대체로 맞지만 최근 형제 계보를 "
      "놓치고, 일부는 사전 미검수(pending)로 탈락한다.")
    A("")
    A("**둘 다 한 뿌리다.** abstract+intro는 \"무엇이 계보고 무엇이 비교/부품인지\"를 명시하지 "
      "않는다. 단순한 논문에선 언급된 방법을 죄다 계보로 과발화(정밀도↓), 복잡한 논문에선 본문 "
      "깊숙이 있는 형제 계보를 놓친다(재현율↓). 같은 입력 한계의 양면.")
    A("")
    a = aggs["전체(50)"]
    cheap_fp = len(fp_by_cat["component_tool"])
    hard_fp = len(fp_by_cat["substrate"]) + len(fp_by_cat["method_misjudged"])
    A("**고칠 수 있는 것 vs 구조적 한계.**")
    A("")
    A(f"- *싸게 개선 가능(lexicon 작업)*: lexicon_dropped FN {a['fn_lex_drop']}건(검수로 approve) "
      f"+ component_tool FP {cheap_fp}건(reject). 둘 다 사전 차원에서 끝난다.")
    A(f"- *구조적 한계(abstract-only)*: not_extracted FN {a['fn_not_ext']}건 + "
      f"method_misjudged FP {len(fp_by_cat['method_misjudged'])}건. 이건 사전이 아니라 입력 범위·"
      f"relate 판단의 문제라 lexicon으로 안 풀린다. substrate FP {len(fp_by_cat['substrate'])}건은 "
      f"문맥의존이라 전역 처리 불가(논문별 판단 필요).")
    A("")
    A("> 요약: 사전 작업으로 손볼 수 있는 건 소수고, 점수를 크게 좌우하는 다수(method_misjudged FP, "
      "not_extracted FN)는 abstract+intro만 보는 입력의 본질적 한계다. 다음 레버는 lexicon이 아니라 "
      "relate가 보는 범위/맥락이다.")
    A("")

    open(path, "w").write("\n".join(L))


# ──────────────────────────────────────────────────────────

def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    st = nc.load_lex_state()
    labels = load_labels()
    groups = load_groups()

    rows = []
    missing = []
    for pid, lab in labels.items():
        pred = load_pred(pid)
        if pred is None:
            missing.append(pid)
            continue
        grp = ("new_collected" if pid in groups["new_collected"]
               else "from_corpus" if pid in groups["from_corpus"] else "?")
        rows.append(score_paper(st, pid, lab["title"], grp, lab["builds_on"], pred))

    if missing:
        print(f"⚠️  매칭 누락 {len(missing)}편: {missing} — 중단")
        sys.exit(1)

    aggs = {
        "전체(50)": aggregate(rows),
        "new_collected": aggregate([r for r in rows if r["group"] == "new_collected"]),
        "from_corpus": aggregate([r for r in rows if r["group"] == "from_corpus"]),
    }

    if not verify(aggs):
        print("\n검증 실패 — 기존 채점 숫자와 불일치. 중단.")
        sys.exit(1)
    print("검증 OK — §8 그룹 숫자 재현 일치.")

    csv_path = REPORTS_DIR / "buildson_items_v1.csv"
    md_path = REPORTS_DIR / "buildson_analysis_v1.md"
    n_items = write_csv(st, rows, csv_path)
    write_md(st, rows, aggs, md_path)

    tot = sum(len(r["TP"]) + len(r["FP"]) + len(r["FN"]) for r in rows)
    assert n_items == tot, f"csv 행수 {n_items} != TP+FP+FN {tot}"
    print(f"CSV 행수 {n_items} = ΣTP+FP+FN {tot} ✓")
    print(f"생성: {csv_path.relative_to(ROOT)} ({n_items}행)")
    print(f"생성: {md_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
