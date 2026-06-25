"""score_buildson: builds_on 정답지(50편, frozen) vs 파이프라인 출력 정밀도/재현율 측정.

측정만 한다. lexicon/labels/relate/normalize 어떤 것도 고치지 않는다(읽기 전용).

핵심 변환(HANDOFF 4):
- 예측·정답 이름을 nc.resolve()로 rep_key 공간에 둔다(alias 흡수 + canon 정규화).
- 예측에만 status 필터: nc.status_of(rk) ∈ NODE_OK(approved/unreviewed) 인 것만 남긴다.
  pending/rejected/None은 그래프에 안 보이므로 채점에서도 뺀다.
- 정답에는 표기만 정규화하고 status 필터는 걸지 않는다(정답은 진실이지 lexicon 상태로 거를 대상이 아님).

실행:
- uv run python eval/score_buildson.py          # 스모크 5편 PASS/FAIL (기본)
- uv run python eval/score_buildson.py --run     # 50편 전체 채점 + eval/runs 저장
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
from src import config
from src import normalize_core as nc

LABELS_PATH = ROOT / "eval/goldset/labels.json"
PAPERS_PATH = ROOT / "eval/goldset/papers.json"
RUNS_DIR = ROOT / "eval/runs"

# FN 진단 분류 라벨
FN_LEX_DROP = "추출O·lexicon탈락"   # raw 예측엔 있으나 pending/rejected라 그래프 탈락 → lexicon 리뷰 백로그 후보
FN_NOT_EXTRACTED = "추출X"          # raw 예측에도 없음 → abstract-only 추출 한계


def load_labels():
    return json.load(open(LABELS_PATH))["labels"]


def load_groups():
    p = json.load(open(PAPERS_PATH))
    return {"new_collected": set(p["new_collected"]), "from_corpus": set(p["from_corpus"])}


def load_pred(pid):
    """data/outputs/{id}.relations.json 의 builds_on 리스트(없으면 [])."""
    fp = config.OUT_DIR / f"{pid}.relations.json"
    if not fp.exists():
        return None
    return json.load(open(fp)).get("builds_on", [])


def score_paper(st, pid, gold_names, pred_names):
    """논문 1편 채점 → 결과 dict. rep_key 공간에서 TP/FP/FN + FN 진단."""
    # 표기 정규화: gold/pred 모두 rep_key로. status 필터는 pred에만.
    gold = {nc.resolve(st, n)[0] for n in gold_names}
    pred_raw = {nc.resolve(st, n)[0] for n in pred_names}
    pred = {k for k in pred_raw if nc.status_of(st, k) in nc.NODE_OK}

    TP = gold & pred
    FP = pred - gold
    FN = gold - pred

    fn_diag = {}
    for k in FN:
        fn_diag[k] = FN_LEX_DROP if k in pred_raw else FN_NOT_EXTRACTED

    return {
        "id": pid,
        "gold": sorted(gold),
        "pred": sorted(pred),
        "pred_raw": sorted(pred_raw),
        "TP": sorted(TP),
        "FP": sorted(FP),
        "FN": sorted(FN),
        "fn_diag": fn_diag,
    }


def label_of(st, rk):
    """rep_key → 사람이 읽을 라벨(lexicon 대표라벨, 없으면 rep_key 그대로)."""
    return st["rep_meta"].get(rk, {}).get("label", rk)


def aggregate(rows):
    """rows(채점 결과 리스트) → micro/macro 집계.

    micro: TP/FP/FN 전부 합산 후 P,R.
    macro: 논문별 P,R 평균. P는 pred≠∅ 논문만, R은 gold≠∅ 논문만 분모.
    """
    sTP = sum(len(r["TP"]) for r in rows)
    sFP = sum(len(r["FP"]) for r in rows)
    sFN = sum(len(r["FN"]) for r in rows)
    micro_p = sTP / (sTP + sFP) if (sTP + sFP) else None
    micro_r = sTP / (sTP + sFN) if (sTP + sFN) else None

    p_vals, r_vals = [], []
    for r in rows:
        tp, fp, fn = len(r["TP"]), len(r["FP"]), len(r["FN"])
        if (tp + fp) > 0:            # pred≠∅ → P 정의됨
            p_vals.append(tp / (tp + fp))
        if (tp + fn) > 0:            # gold≠∅ → R 정의됨
            r_vals.append(tp / (tp + fn))
    macro_p = sum(p_vals) / len(p_vals) if p_vals else None
    macro_r = sum(r_vals) / len(r_vals) if r_vals else None

    # FN 진단 그룹 카운트
    lex_drop = sum(1 for r in rows for d in r["fn_diag"].values() if d == FN_LEX_DROP)
    not_ext = sum(1 for r in rows for d in r["fn_diag"].values() if d == FN_NOT_EXTRACTED)

    return {
        "n_papers": len(rows),
        "sumTP": sTP, "sumFP": sFP, "sumFN": sFN,
        "micro_p": micro_p, "micro_r": micro_r,
        "macro_p": macro_p, "macro_r": macro_r,
        "n_pred_nonempty": len(p_vals),
        "n_gold_nonempty": len(r_vals),
        "fn_lex_drop": lex_drop, "fn_not_extracted": not_ext,
    }


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else "—"


# ────────────────────────────────────────────────────────── 스모크

SMOKE = {
    "2503.09516": dict(title="SEARCH-R1", TP=1, FP=1, FN=1, P=0.5, R=0.5),
    "2501.12948": dict(title="DeepSeek-R1", TP=1, FP=0, FN=1, P=1.0, R=0.5),
    "2302.04761": dict(title="Toolformer", TP=0, FP=1, FN=0, P=0.0, R=None),
    "2502.14802": dict(title="HippoRAG 2", TP=2, FP=0, FN=0, P=1.0, R=1.0),
    "2509.26383": dict(title="KG-R1", TP=1, FP=0, FN=4, P=1.0, R=0.2),
}


def run_smoke(st, labels):
    print("=" * 70)
    print("SMOKE TEST — 5편 (예상값 대조)")
    print("=" * 70)
    ok = True
    for pid, exp in SMOKE.items():
        gold = labels[pid]["builds_on"]
        pred = load_pred(pid)
        if pred is None:
            print(f"[FAIL] {pid}: 출력 파일 없음")
            ok = False
            continue
        r = score_paper(st, pid, gold, pred)
        tp, fp, fn = len(r["TP"]), len(r["FP"]), len(r["FN"])
        p = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else None

        checks = [tp == exp["TP"], fp == exp["FP"], fn == exp["FN"]]
        # P 비교 (gold∅인 Toolformer도 P=0.0은 정의됨)
        checks.append(abs(p - exp["P"]) < 1e-9 if exp["P"] is not None else True)
        # R 비교 (None끼리, 또는 값끼리)
        if exp["R"] is None:
            checks.append(rec is None)
        else:
            checks.append(rec is not None and abs(rec - exp["R"]) < 1e-9)

        passed = all(checks)
        ok = ok and passed
        tag = "PASS" if passed else "FAIL"
        rstr = "—(gold∅)" if rec is None else f"{rec:.3f}"
        print(f"[{tag}] {exp['title']:14} ({pid})  "
              f"TP={tp} FP={fp} FN={fn}  P={p:.3f} R={rstr}")
        if not passed:
            print(f"       기대: TP={exp['TP']} FP={exp['FP']} FN={exp['FN']} "
                  f"P={exp['P']} R={exp['R']}")
            print(f"       gold={r['gold']}")
            print(f"       pred_raw={r['pred_raw']}  pred={r['pred']}")
            print(f"       FN_diag={ {label_of(st,k): d for k,d in r['fn_diag'].items()} }")
    print("-" * 70)
    print("스모크 결과:", "PASS ✅" if ok else "FAIL ❌")
    return ok


# ────────────────────────────────────────────────────────── 전체 채점

def print_agg_table(st, name, agg):
    print(f"\n[{name}]  (n={agg['n_papers']})")
    print(f"  micro  P={fmt(agg['micro_p'])}  R={fmt(agg['micro_r'])}   "
          f"(ΣTP={agg['sumTP']} ΣFP={agg['sumFP']} ΣFN={agg['sumFN']})")
    print(f"  macro  P={fmt(agg['macro_p'])}  R={fmt(agg['macro_r'])}   "
          f"(P분모 pred≠∅ {agg['n_pred_nonempty']}편, R분모 gold≠∅ {agg['n_gold_nonempty']}편)")
    print(f"  FN진단 추출O·lexicon탈락={agg['fn_lex_drop']}  추출X={agg['fn_not_extracted']}")


def run_full(st, labels, groups):
    rows = []
    missing = []
    for pid, lab in labels.items():
        pred = load_pred(pid)
        if pred is None:
            missing.append(pid)
            continue
        r = score_paper(st, pid, lab["builds_on"], pred)
        r["title"] = lab["title"]
        r["group"] = ("new_collected" if pid in groups["new_collected"]
                      else "from_corpus" if pid in groups["from_corpus"] else "?")
        rows.append(r)

    if missing:
        print(f"⚠️  매칭 누락 {len(missing)}편: {missing}")

    by_group = {
        "전체(50)": rows,
        "new_collected": [r for r in rows if r["group"] == "new_collected"],
        "from_corpus": [r for r in rows if r["group"] == "from_corpus"],
    }
    aggs = {name: aggregate(rs) for name, rs in by_group.items()}

    # ── 콘솔: 집계 3세트
    print("=" * 70)
    print("BUILDS_ON 채점 결과")
    print("=" * 70)
    for name in ["전체(50)", "new_collected", "from_corpus"]:
        print_agg_table(st, name, aggs[name])

    # ── 콘솔: FP 전체 목록
    print("\n" + "=" * 70)
    print("FALSE POSITIVES (헛것 — gold에 없는데 그래프에 남은 노드)")
    print("=" * 70)
    fp_any = False
    for r in rows:
        for k in r["FP"]:
            fp_any = True
            print(f"  {r['title']:30} [{r['group']:13}]  {label_of(st, k)}")
    if not fp_any:
        print("  (없음)")

    # ── 콘솔: FN 전체 목록 (진단 분류 포함)
    print("\n" + "=" * 70)
    print("FALSE NEGATIVES (놓침 — gold에 있으나 그래프에 없는 노드)")
    print("=" * 70)
    fn_any = False
    for r in rows:
        for k in r["FN"]:
            fn_any = True
            print(f"  {r['title']:30} [{r['group']:13}]  "
                  f"{label_of(st, k):28} {r['fn_diag'][k]}")
    if not fn_any:
        print("  (없음)")

    save_run(st, rows, aggs)
    return rows, aggs


# ────────────────────────────────────────────────────────── 저장

def save_run(st, rows, aggs):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = RUNS_DIR / f"score_buildson_{ts}"

    # rep_key → label 변환해 사람이 읽기 쉽게
    def labelize(keys):
        return [label_of(st, k) for k in keys]

    papers_json = []
    for r in rows:
        papers_json.append({
            "id": r["id"], "title": r["title"], "group": r["group"],
            "gold": labelize(r["gold"]),
            "pred": labelize(r["pred"]),
            "pred_raw": labelize(r["pred_raw"]),
            "TP": labelize(r["TP"]),
            "FP": labelize(r["FP"]),
            "FN": labelize(r["FN"]),
            "fn_diag": {label_of(st, k): d for k, d in r["fn_diag"].items()},
        })

    out_json = {
        "kind": "score_buildson",
        "time": datetime.now().isoformat(timespec="seconds"),
        "labels_path": str(LABELS_PATH.relative_to(ROOT)),
        "aggregates": aggs,
        "papers": papers_json,
    }
    json.dump(out_json, open(f"{base}.json", "w"), ensure_ascii=False, indent=2)

    # ── .md
    L = []
    L.append("# builds_on 채점 — score_buildson")
    L.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    L.append("")
    L.append("측정 전용(읽기 전용). 예측만 lexicon status 필터(NODE_OK=approved/unreviewed), "
             "gold는 표기만 정규화.")
    L.append("")
    L.append("## 집계")
    L.append("")
    L.append("| 그룹 | n | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN | FN:lexicon탈락 | FN:추출X |")
    L.append("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for name in ["전체(50)", "new_collected", "from_corpus"]:
        a = aggs[name]
        L.append(f"| {name} | {a['n_papers']} | {fmt(a['micro_p'])} | {fmt(a['micro_r'])} | "
                 f"{fmt(a['macro_p'])} | {fmt(a['macro_r'])} | {a['sumTP']} | {a['sumFP']} | "
                 f"{a['sumFN']} | {a['fn_lex_drop']} | {a['fn_not_extracted']} |")
    L.append("")
    L.append("> macro P 분모=pred≠∅ 논문, macro R 분모=gold≠∅ 논문(empty gold 11편 제외).")
    L.append("")

    L.append("## False Positives (헛것)")
    L.append("")
    L.append("| 논문 | 그룹 | rep_label |")
    L.append("|---|---|---|")
    fp_any = False
    for r in rows:
        for k in r["FP"]:
            fp_any = True
            L.append(f"| {r['title']} | {r['group']} | {label_of(st, k)} |")
    if not fp_any:
        L.append("| (없음) | | |")
    L.append("")

    L.append("## False Negatives (놓침)")
    L.append("")
    L.append("| 논문 | 그룹 | rep_label | 진단 |")
    L.append("|---|---|---|---|")
    fn_any = False
    for r in rows:
        for k in r["FN"]:
            fn_any = True
            L.append(f"| {r['title']} | {r['group']} | {label_of(st, k)} | {r['fn_diag'][k]} |")
    if not fn_any:
        L.append("| (없음) | | | |")
    L.append("")

    open(f"{base}.md", "w").write("\n".join(L))
    print(f"\n저장: {base.relative_to(ROOT)}.json / .md")


# ──────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="50편 전체 채점(없으면 스모크만)")
    args = ap.parse_args()

    st = nc.load_lex_state()
    labels = load_labels()

    if not args.run:
        ok = run_smoke(st, labels)
        if not ok:
            print("\n스모크 FAIL → --run 거부. 먼저 불일치를 해결하라.")
            sys.exit(1)
        print("\n스모크 PASS. 전체 채점은 `--run` 으로 실행.")
        return

    # --run 이어도 안전장치로 스모크 먼저 통과해야 진행
    ok = run_smoke(st, labels)
    if not ok:
        print("\n스모크 FAIL → 전체 채점 중단.")
        sys.exit(1)
    print()
    groups = load_groups()
    run_full(st, labels, groups)


if __name__ == "__main__":
    main()
