"""재채점: resolve() 괄호 fallback 패치 전(old) vs 후(new)로 v1/v2/v3를 다시 채점.

배경: 채점이 이름 정확일치라, 모델이 'Retrieval-Augmented Generation (RAG)'처럼 본문
정식명을 가져오면 frozen lexicon이 그 형태를 몰라 dropped→FN으로 깨졌다. resolve()에
괄호 약어 fallback(additive)을 넣어 그 표기 변종을 기존 대표개념에 연결한다.

이 스크립트는 normalize_core를 수정하지 않는다. 패치는 이미 src/normalize_core.resolve()에
반영돼 있고(=new), 여기선 old(패치 전) 동작을 로컬 함수로 재현해 동일 채점기로 양쪽을 돌려
old→new 비교한다.

채점 규칙은 기존과 동일: resolve→rep_key, pred는 status∈NODE_OK만, gold은 표기만 정규화.
TP=gold&pred, FP=pred-gold, FN=gold-pred. v3 출력은 객체라 name만 사용.

검증 게이트(§6): fallback은 additive → 어느 run에서도 new R < old R 이면 중단(구현 오류).
또 old 재계산이 §7 기준값을 재현해야 함(로컬 old 함수 정합성 확인).

산출물: eval/reports/buildson_canon_fix.md (커밋 대상)
실행: uv run python eval/exp_rescore_canonfix.py
"""
import sys, json, re
from collections import Counter
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
OUT_MD = REPORTS_DIR / "buildson_canon_fix.md"

# §7 old(패치 전) 기준값 — 로컬 old 함수 정합성 확인용 (micro P/R)
EXPECT_OLD = {
    "v1": {"전체(50)": (0.562, 0.683), "new_collected": (0.708, 0.515), "from_corpus": (0.490, 0.889)},
    "v2": {"전체(50)": (0.597, 0.667), "new_collected": (0.654, 0.515), "from_corpus": (0.561, 0.852)},
    "v3": {"전체(50)": (0.660, 0.517), "new_collected": (0.778, 0.424), "from_corpus": (0.586, 0.630)},
}


# ── resolve: old(패치 전 재현) / new(패치된 nc.resolve) ────
def resolve_old(st, name):
    """패치 전 resolve 동작 재현 — canon 직접 매칭만(괄호 fallback 없음)."""
    k = nc.canon(name)
    if k in st["alias2rep"]:
        return st["alias2rep"][k]
    return k


def resolve_new(st, name):
    return nc.resolve(st, name)[0]


def label_of(st, rk):
    return st["rep_meta"].get(rk, {}).get("label", rk)


# ── pred 이름 로더 (v3는 객체 → name만) ─────────────────
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


def score_paper(st, gold_names, pred_names, resolve_fn):
    gold = {resolve_fn(st, n) for n in gold_names}
    pred_raw = {resolve_fn(st, n) for n in pred_names}
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


def md_escape(s):
    return s.replace("|", "\\|").replace("\n", " ").strip()


def main():
    st = nc.load_lex_state()
    labels = json.load(open(LABELS_PATH))["labels"]
    p = json.load(open(PAPERS_PATH))
    groups = {"new_collected": set(p["new_collected"]), "from_corpus": set(p["from_corpus"])}

    def grp_of(pid):
        return ("new_collected" if pid in groups["new_collected"]
                else "from_corpus" if pid in groups["from_corpus"] else "?")

    # 각 run을 old/new 두 resolve로 채점. 누락 검사.
    data = {}   # run -> {"old": {pid: row}, "new": {pid: row}, "names": {pid: [...]}}
    for run, loader in RUNS.items():
        names_by, old_by, new_by, missing = {}, {}, {}, []
        for pid, lab in labels.items():
            nm = loader(pid)
            if nm is None:
                missing.append(pid); continue
            names_by[pid] = nm
            old_by[pid] = score_paper(st, lab["builds_on"], nm, resolve_old)
            new_by[pid] = score_paper(st, lab["builds_on"], nm, resolve_new)
        if missing:
            print(f"⚠️ {run} 누락 {len(missing)}편: {missing} — 중단"); sys.exit(1)
        data[run] = {"old": old_by, "new": new_by, "names": names_by}

    # 그룹별 집계
    def aggs(by_pid):
        rows = list(by_pid.values())
        return {
            "전체(50)": aggregate(rows),
            "new_collected": aggregate([by_pid[pid] for pid in by_pid if grp_of(pid) == "new_collected"]),
            "from_corpus": aggregate([by_pid[pid] for pid in by_pid if grp_of(pid) == "from_corpus"]),
        }

    AGG = {run: {"old": aggs(data[run]["old"]), "new": aggs(data[run]["new"])} for run in RUNS}

    # ── 게이트 1: old 재계산이 §7 재현 ──
    ok = True
    for run in RUNS:
        for g, (mp, mr) in EXPECT_OLD[run].items():
            a = AGG[run]["old"][g]
            if not (abs(a["micro_p"] - mp) < 5e-4 and abs(a["micro_r"] - mr) < 5e-4):
                ok = False
                print(f"[OLD VERIFY FAIL] {run}/{g}: got ({a['micro_p']:.3f},{a['micro_r']:.3f}) 기대 ({mp},{mr})")
    if not ok:
        print("\n로컬 old 함수가 §7 기준 재현 실패 → 중단."); sys.exit(1)
    print("게이트1 OK — old 재계산이 §7 기준값 재현.")

    # ── 게이트 2: 단조성 (어느 run/그룹도 new R < old R 금지) ──
    mono = True
    for run in RUNS:
        for g in ["전체(50)", "new_collected", "from_corpus"]:
            old_r, new_r = AGG[run]["old"][g]["micro_r"], AGG[run]["new"][g]["micro_r"]
            old_R, new_R = AGG[run]["old"][g]["macro_r"], AGG[run]["new"][g]["macro_r"]
            if new_r + 1e-9 < old_r or new_R + 1e-9 < old_R:
                mono = False
                print(f"[MONO FAIL] {run}/{g}: micro R {old_r:.3f}->{new_r:.3f}, macro R {old_R:.3f}->{new_R:.3f}")
    if not mono:
        print("\n단조성 위반 — fallback이 additive가 아님 → 중단."); sys.exit(1)
    print("게이트2 OK — 모든 run에서 재현율 단조(안 내려감).")

    # ── 회복 항목: old에서 TP 아니던 게 new에서 TP ──
    #   원인 표기 = pred_names 중 resolve_new==rk 이고 resolve_old!=rk 인 이름
    recovered = {run: [] for run in RUNS}
    for run in RUNS:
        for pid in data[run]["names"]:
            old_tp = data[run]["old"][pid]["TP"]
            new_tp = data[run]["new"][pid]["TP"]
            for rk in sorted(new_tp - old_tp):
                surfaces = [nm for nm in data[run]["names"][pid]
                            if resolve_new(st, nm) == rk and resolve_old(st, nm) != rk]
                recovered[run].append((pid, rk, surfaces))

    # ── 남은 lexicon탈락 변종(alias 후보): new resolve로도 status∉NODE_OK인 emit 표기 ──
    #   (추출O이나 lexicon에서 노드 안 됨 = '추출O·lexicon탈락'의 표면형). 빈도순.
    dropped_surface = Counter()
    dropped_examples = {}   # surface -> (run, pid)
    for run in RUNS:
        for pid in data[run]["names"]:
            for nm in data[run]["names"][pid]:
                rk = resolve_new(st, nm)
                if nc.status_of(st, rk) not in nc.NODE_OK:   # 그래프에서 빠지는 emit
                    key = nm.strip()
                    dropped_surface[key] += 1
                    dropped_examples.setdefault(key, (run, pid))

    # ── 리포트 ──
    L = []; A = L.append
    A("# builds_on — 작명 정규화(resolve 괄호 fallback) 재채점")
    A("")
    A("`src/normalize_core.resolve()`에 **괄호 약어 fallback**(additive)을 추가하고 v1/v2/v3를 "
      "같은 규칙으로 재채점한 결과. `Long Form (ACRONYM)` 표기가 직접 매칭에 실패하면 (a)괄호 안 "
      "약어, (b)괄호 뗀 본체로 재시도해 **이미 알려진 대표개념에만** 연결한다(새 개념 생성 안 함). "
      "lexicon/relations.json/모델 무수정, 그래프 재빌드 없음 — 점수 재측정만.")
    A("")
    A("> ⚠️ 이 변경으로 이전 §7 baseline은 무효(설계상 baseline이 바뀜). **new 값이 새 기준**, "
      "old는 비교용. fallback은 additive라 재현율은 패치 전보다 내려갈 수 없다(검증 게이트 통과).")
    A("")

    # 1) 점수표
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

    # 2) 회복 항목
    A("## 2. 회복된 항목 (패치로 TP가 된 것 — 표기 변종이 대표개념에 연결됨)")
    A("")
    for run in RUNS:
        items = recovered[run]
        A(f"### {run} — {len(items)}건")
        A("")
        if not items:
            A("- (없음)")
        for pid, rk, surfaces in items:
            title = labels[pid]["title"]
            surf = "; ".join(md_escape(s) for s in surfaces) or "(?)"
            A(f"- **{label_of(st,rk)}** ← `{surf}` — {title} ({pid}, {grp_of(pid)})")
        A("")

    # 3) 남은 변종 (사람 검토용)
    A("## 3. ★ 남은 lexicon탈락 변종 (사람 검토용 — alias 추가 후보, 자동등록 아님)")
    A("")
    A("패치 후에도 emit됐지만 lexicon에서 노드가 안 되는(status∉approved/unreviewed) 표기. "
      "대부분 괄호 아닌 변종(예: \"retrieval augmentation\", \"agentic RAG\")이라 판단이 필요 — "
      "**목록만 제공**, 다음 라운드에 사람이 alias로 승격할지 정한다. 빈도순.")
    A("")
    A("| 빈도 | emit 표기 | 예시(run, 논문) |")
    A("|--:|---|---|")
    for surf, cnt in dropped_surface.most_common():
        run, pid = dropped_examples[surf]
        A(f"| {cnt} | {md_escape(surf)} | {run}, {labels[pid]['title']} ({pid}) |")
    A("")
    A(f"총 고유 표기 {len(dropped_surface)}종 / emit 누계 {sum(dropped_surface.values())}건.")
    A("")

    # 4) 해석
    A("## 4. 해석")
    A("")
    v3o, v3n = AGG["v3"]["old"]["전체(50)"], AGG["v3"]["new"]["전체(50)"]
    v1o, v1n = AGG["v1"]["old"]["전체(50)"], AGG["v1"]["new"]["전체(50)"]
    A(f"v3 전체 micro R {fmt(v3o['micro_r'])}→{fmt(v3n['micro_r'])} "
      f"({delta(v3n['micro_r'],v3o['micro_r'])}), P {fmt(v3o['micro_p'])}→{fmt(v3n['micro_p'])} "
      f"({delta(v3n['micro_p'],v3o['micro_p'])}). 예상대로 v3(verbose 표기 多)가 가장 크게 회복됐다 — "
      f"`Retrieval-Augmented Generation (RAG)` 류가 RAG로 연결되며 dropped→TP. "
      f"v1은 micro R {fmt(v1o['micro_r'])}→{fmt(v1n['micro_r'])}로 거의 불변(이미 짧은 표기라 "
      f"fallback이 거의 안 먹음 — 패치가 과하지 않다는 신호). "
      f"정밀도는 양방향 가능: fallback이 pred의 미해결 표기도 대표개념에 연결시키므로 그 항목이 "
      f"gold면 TP(P↑), gold 아니면 FP(P↓)가 된다 — 위 표의 ΣFP 변화로 확인. "
      f"남은 변종 {len(dropped_surface)}종(§3)은 괄호 아닌 표기라 자동 연결 대상이 아니며, "
      f"사람이 alias 승격 여부를 다음 라운드에 정한다. 이로써 작명이 강건해져 evidence·모델비교의 "
      f"선결 조건이 갖춰졌다.")
    A("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))

    # 콘솔 요약
    for run in RUNS:
        o, n = AGG[run]["old"]["전체(50)"], AGG[run]["new"]["전체(50)"]
        print(f"{run} 전체: microR {fmt(o['micro_r'])}->{fmt(n['micro_r'])}  "
              f"microP {fmt(o['micro_p'])}->{fmt(n['micro_p'])}  회복 {len(recovered[run])}건")
    print(f"\n생성: {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
