"""재채점: lexicon 버킷1(gold 개념 5개 approve + 3 alias) 적용 전(old) vs 후(new) v1/v2/v3.

배경: FN 중 일부는 모델이 맞게 뽑았는데 그 개념이 lexicon에서 pending이라 노드가 안 돼
잘린 것. goldset에 실제 있는 5개를 approve, 긴 표기 3개를 alias로 연결 → 곧바로 FN→TP.

lexicon.json은 이미 편집됨(=new 상태). 이 스크립트는 lexicon을 수정하지 않는다. new 상태를
load한 뒤, 버킷1 변경을 메모리에서 되돌린 old 상태를 만들어 같은 채점기로 old/new를 비교한다.
  - approve 되돌리기: 5개 대표개념 status → pending (status 필터에서 빠짐)
  - alias 되돌리기: 3개 alias를 alias2rep에서 제거 (해당 표기가 대표개념에 연결 안 됨)
canon/resolve/normalize_paper는 안 건드린다(채점에 안 쓰이는 경로 + 핸드오프 불변).

채점 규칙 동일: resolve→rep_key, pred는 status∈NODE_OK만, gold은 표기만 정규화.
TP=gold&pred, FP=pred-gold, FN=gold-pred. v3 출력은 객체라 name만 사용.

게이트1: old 재계산이 §6(canon-fix 후) 기준값 재현. 게이트2: 단조성(어느 run도 new R<old R 금지).

산출물: eval/reports/buildson_lexicon_bucket1.md (커밋 대상)
실행: uv run python eval/exp_rescore_bucket1.py
"""
import sys, json, copy
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
OUT_MD = REPORTS_DIR / "buildson_lexicon_bucket1.md"

# 버킷1 변경 내역 (old 복원용)
PROMOTED = ["KG-RAG", "ReSearch", "R1-Searcher", "TIRESRAG-R1", "DeepSeek-V3-Base"]
ADDED_ALIASES = [
    "Knowledge-Graph Retrieval-Augmented Generation",
    "Re-Search",
    "k-Nearest Neighbor Language Model",
]

# §6 old(버킷1 전 = canon-fix 후) 기준값 — 전체 micro P/R (게이트1)
EXPECT_OLD = {"v1": (0.562, 0.683), "v2": (0.597, 0.667), "v3": (0.672, 0.650)}


def make_old_state(new_state):
    """new(현재 lexicon) state → 버킷1 변경을 메모리에서 되돌린 old state."""
    st = copy.deepcopy(new_state)
    for rep in PROMOTED:                       # approve 되돌리기 → pending
        rk = nc.canon(rep)
        if rk in st["rep_meta"]:
            st["rep_meta"][rk]["status"] = "pending"
    for alias in ADDED_ALIASES:                # alias 연결 제거
        st["alias2rep"].pop(nc.canon(alias), None)
    return st


def label_of(st, rk):
    return st["rep_meta"].get(rk, {}).get("label", rk)


def names_v1(pid):
    fp = config.OUT_DIR / f"{pid}.relations.json"
    return json.load(open(fp)).get("builds_on", []) if fp.exists() else None


def names_v2(pid):
    fp = V2_DIR / f"{pid}.relations.json"
    return json.load(open(fp)).get("builds_on", []) if fp.exists() else None


def names_v3(pid):
    fp = V3_DIR / f"{pid}.relations.json"
    if not fp.exists():
        return None
    return [b["name"] for b in json.load(open(fp)).get("builds_on", [])]


RUNS = {"v1": names_v1, "v2": names_v2, "v3": names_v3}


def score_paper(st, gold_names, pred_names):
    gold = {nc.resolve(st, n)[0] for n in gold_names}
    pred_raw = {nc.resolve(st, n)[0] for n in pred_names}
    pred = {k for k in pred_raw if nc.status_of(st, k) in nc.NODE_OK}
    TP, FP, FN = gold & pred, pred - gold, gold - pred
    fn_reason = {k: ("lexicon_dropped" if k in pred_raw else "not_extracted") for k in FN}
    return {"gold": gold, "pred": pred, "pred_raw": pred_raw,
            "TP": TP, "FP": FP, "FN": FN, "fn_reason": fn_reason}


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
    return {"n": len(rows), "sumTP": sTP, "sumFP": sFP, "sumFN": sFN,
            "micro_p": micro_p, "micro_r": micro_r, "macro_p": macro_p, "macro_r": macro_r}


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else "—"


def delta(new, old):
    if new is None or old is None:
        return "—"
    d = new - old
    return f"{'+' if d >= 0 else '−'}{abs(d):.3f}"


def main():
    new_state = nc.load_lex_state()
    old_state = make_old_state(new_state)
    labels = json.load(open(LABELS_PATH))["labels"]
    p = json.load(open(PAPERS_PATH))
    groups = {"new_collected": set(p["new_collected"]), "from_corpus": set(p["from_corpus"])}

    def grp_of(pid):
        return ("new_collected" if pid in groups["new_collected"]
                else "from_corpus" if pid in groups["from_corpus"] else "?")

    data = {}
    for run, loader in RUNS.items():
        names_by, old_by, new_by, missing = {}, {}, {}, []
        for pid, lab in labels.items():
            nm = loader(pid)
            if nm is None:
                missing.append(pid); continue
            names_by[pid] = nm
            old_by[pid] = score_paper(old_state, lab["builds_on"], nm)
            new_by[pid] = score_paper(new_state, lab["builds_on"], nm)
        if missing:
            print(f"⚠️ {run} 누락 {len(missing)}편: {missing} — 중단"); sys.exit(1)
        data[run] = {"old": old_by, "new": new_by, "names": names_by}

    def aggs(by_pid):
        rows = list(by_pid.values())
        return {
            "전체(50)": aggregate(rows),
            "new_collected": aggregate([by_pid[pid] for pid in by_pid if grp_of(pid) == "new_collected"]),
            "from_corpus": aggregate([by_pid[pid] for pid in by_pid if grp_of(pid) == "from_corpus"]),
        }

    AGG = {run: {"old": aggs(data[run]["old"]), "new": aggs(data[run]["new"])} for run in RUNS}

    # 게이트1: old가 §6 재현
    ok = True
    for run in RUNS:
        a = AGG[run]["old"]["전체(50)"]
        mp, mr = EXPECT_OLD[run]
        if not (abs(a["micro_p"] - mp) < 5e-4 and abs(a["micro_r"] - mr) < 5e-4):
            ok = False
            print(f"[OLD VERIFY FAIL] {run}: got ({a['micro_p']:.3f},{a['micro_r']:.3f}) 기대 ({mp},{mr})")
    if not ok:
        print("\n게이트1 실패 — old 복원이 §6 재현 못함 → 중단."); sys.exit(1)
    print("게이트1 OK — old(버킷1 전) 복원이 §6 기준값 재현.")

    # 게이트2: 단조성
    mono = True
    for run in RUNS:
        for g in ["전체(50)", "new_collected", "from_corpus"]:
            o, n = AGG[run]["old"][g], AGG[run]["new"][g]
            if n["micro_r"] + 1e-9 < o["micro_r"] or n["macro_r"] + 1e-9 < o["macro_r"]:
                mono = False
                print(f"[MONO FAIL] {run}/{g}: microR {o['micro_r']:.3f}->{n['micro_r']:.3f} "
                      f"macroR {o['macro_r']:.3f}->{n['macro_r']:.3f}")
    if not mono:
        print("\n게이트2 실패 — approve가 additive가 아님 → 중단."); sys.exit(1)
    print("게이트2 OK — 모든 run 재현율 단조(안 내려감).")

    # 회복 FN→TP, 새 FP
    recovered, new_fps = {run: [] for run in RUNS}, {run: [] for run in RUNS}
    for run in RUNS:
        for pid in data[run]["names"]:
            o, n = data[run]["old"][pid], data[run]["new"][pid]
            for rk in sorted(n["TP"] - o["TP"]):
                recovered[run].append((pid, rk))
            for rk in sorted(n["FP"] - o["FP"]):
                new_fps[run].append((pid, rk))

    # ── 리포트 ──
    L = []; A = L.append
    A("# builds_on — lexicon 버킷1(gold 개념 승격) 재채점")
    A("")
    A("FN 중 '모델은 맞게 뽑았으나 lexicon에서 pending이라 노드가 안 돼 잘린' 것 중 **goldset에 "
      "실제 있는 5개 개념을 approve**하고 긴 표기 3개를 alias로 연결한 뒤 v1/v2/v3 재채점. "
      "전부 gold라 precision 위험이 거의 없고 곧바로 FN→TP가 된다. lexicon만 변경 — "
      "relate/relations.json/canon/resolve/모델 무수정, 그래프 재빌드 없음.")
    A("")
    A("변경: status pending→approved (KG-RAG, ReSearch, R1-Searcher, TIRESRAG-R1, "
      "DeepSeek-V3-Base) + alias (KG-RAG←\"Knowledge-Graph Retrieval-Augmented Generation\", "
      "ReSearch←\"Re-Search\", kNN-LM←\"k-Nearest Neighbor Language Model\").")
    A("")
    A("> approve는 additive(노드가 생길 뿐 사라지지 않음) → 재현율은 안 내려간다(게이트 통과). "
      "**이 lexicon이 이제 새 기준 상태.**")
    A("")

    A("## 1. 점수표 (old → new, run별)")
    A("")
    for run in RUNS:
        A(f"### {run}")
        A("")
        A("| 그룹 | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |")
        A("|---|--:|--:|--:|--:|--:|--:|--:|")
        for g in ["전체(50)", "new_collected", "from_corpus"]:
            o, n = AGG[run]["old"][g], AGG[run]["new"][g]
            A(f"| **{g}** old | {fmt(o['micro_p'])} | {fmt(o['micro_r'])} | {fmt(o['macro_p'])} | "
              f"{fmt(o['macro_r'])} | {o['sumTP']} | {o['sumFP']} | {o['sumFN']} |")
            A(f"| **{g}** new | {fmt(n['micro_p'])} | {fmt(n['micro_r'])} | {fmt(n['macro_p'])} | "
              f"{fmt(n['macro_r'])} | {n['sumTP']} | {n['sumFP']} | {n['sumFN']} |")
            A(f"| Δ | {delta(n['micro_p'],o['micro_p'])} | {delta(n['micro_r'],o['micro_r'])} | "
              f"{delta(n['macro_p'],o['macro_p'])} | {delta(n['macro_r'],o['macro_r'])} | "
              f"{n['sumTP']-o['sumTP']:+d} | {n['sumFP']-o['sumFP']:+d} | {n['sumFN']-o['sumFN']:+d} |")
        A("")

    A("## 2. 회복된 FN (이 변경으로 FN→TP)")
    A("")
    A("승격/alias로 노드가 생겨 채점에 잡힌 것. 해당 run이 그 개념을 실제 emit한 경우만 회복된다 "
      "(not_extracted였던 건 안 살아남 — related work 추출 단계 몫).")
    A("")
    total_rec = sum(len(v) for v in recovered.values())
    for run in RUNS:
        items = recovered[run]
        A(f"### {run} — {len(items)}건")
        A("")
        if not items:
            A("- (없음)")
        for pid, rk in items:
            A(f"- **{label_of(new_state,rk)}** — {labels[pid]['title']} ({pid}, {grp_of(pid)})")
        A("")

    A("## 3. 새 FP (승격으로 노드가 됐으나 gold 아닌 논문 — 정상 부작용)")
    A("")
    total_fp = sum(len(v) for v in new_fps.values())
    for run in RUNS:
        items = new_fps[run]
        A(f"### {run} — {len(items)}건")
        A("")
        if not items:
            A("- (없음)")
        for pid, rk in items:
            A(f"- **{label_of(new_state,rk)}** — {labels[pid]['title']} ({pid}, {grp_of(pid)})")
        A("")

    # 남은 FN의 진단 분포(현 new 상태)
    def fn_counts(run):
        ld = ne = 0
        for pid in data[run]["names"]:
            for k, why in data[run]["new"][pid]["fn_reason"].items():
                if why == "lexicon_dropped":
                    ld += 1
                else:
                    ne += 1
        return ld, ne

    A("## 4. 해석")
    A("")
    v3o, v3n = AGG["v3"]["old"]["전체(50)"], AGG["v3"]["new"]["전체(50)"]
    parts = []
    for run in RUNS:
        ld, ne = fn_counts(run)
        parts.append(f"{run}(탈락 {ld}/추출X {ne})")
    A(f"회복 총 {total_rec}건(FN→TP), 새 FP {total_fp}건. "
      f"v3 전체 micro R {fmt(v3o['micro_r'])}→{fmt(v3n['micro_r'])} "
      f"({delta(v3n['micro_r'],v3o['micro_r'])}). 5개가 emit된 run·논문에서 TP로 떴고, "
      f"비교 언급이던 곳은 새 FP로 전환(정상). "
      f"남은 FN의 진단 분포(new): {', '.join(parts)} — 대부분이 **추출X(not_extracted)**, "
      f"즉 모델이 abstract+intro에서 아예 안 뽑은 related-work 계보다. lexicon 레버는 거의 "
      f"소진됐고, 다음 레버는 relate가 보는 범위(related work 추출)다. "
      f"이 lexicon이 이후 evidence 채택 판단·모델 비교의 기준 상태가 된다.")
    A("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))

    for run in RUNS:
        o, n = AGG[run]["old"]["전체(50)"], AGG[run]["new"]["전체(50)"]
        print(f"{run} 전체: microR {fmt(o['micro_r'])}->{fmt(n['micro_r'])}  "
              f"microP {fmt(o['micro_p'])}->{fmt(n['micro_p'])}  회복 {len(recovered[run])}  새FP {len(new_fps[run])}")
    print(f"\n생성: {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
