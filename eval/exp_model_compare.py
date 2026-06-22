"""실험: 모델 비교 gpt-5.4-mini vs gpt-5.4(full), 둘 다 temperature=0.

프로젝트 핵심 질문 = "굳이 더 큰/비싼 모델이 필요한가." 라이브 v2 프롬프트 그대로, 모델만
바꿔 50편 재추출 → 재채점 → head-to-head. 같은 프롬프트(v2)·lexicon(버킷1)·goldset·채점규칙.
변수는 모델 하나. evidence(v3)·RW(v4)는 안 씀.

temp=0 이유: 직전 실험들에서 효과가 run-to-run 노이즈(±0.04)에 묻혔다. 두 모델 다 temp=0로
샘플링 분산을 제거 → P/R 차이 = 모델 능력 차이. determinism 체크로 temp=0가 실제 결정적인지 확인.

불변: 라이브 relate.py(v2)·config.py(MODEL) 무수정 — 이 스크립트가 모델을 인자로 오버라이드.
lexicon/labels/채점 무수정, baseline 덮어쓰기 금지. 출력은 model_*_t0/ 에만.

서브커맨드:
  one <tag> <pid> [--force]   tag∈{mini,full} 모델로 1편 추출(temp=0) → model_<tag>_t0/{id}.json (워커용)
  determinism                 두 모델 각 10편 1회 재호출해 builds_on byte-동일 확인 → 결과 저장
  report                      두 디렉토리 채점 + determinism + FP/FN + 비용/속도 + md (메인)

실행: uv run python eval/exp_model_compare.py <cmd> ...
"""
import sys, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))            # prompts
sys.path.insert(0, str(ROOT / "src"))    # config / normalize_core
import config
import normalize_core as nc
from prompts.pipeline.relate import RELATE_SYSTEM, RELATE_USER, RELATE_SCHEMA

LABELS_PATH = ROOT / "eval/goldset/labels.json"
PAPERS_PATH = ROOT / "eval/goldset/papers.json"
REPORTS_DIR = ROOT / "eval/reports"
OUT_MD = REPORTS_DIR / "model_mini_vs_full.md"

MODELS = {"mini": "gpt-5.4-mini", "full": "gpt-5.4"}
DIRS = {tag: ROOT / f"eval/experiments/model_{tag}_t0" for tag in MODELS}
for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)
DET_PATH = ROOT / "eval/experiments/model_determinism.json"

# determinism 체크 대상: gold 앞 10편(고정)
def det_pids():
    return list(json.load(open(LABELS_PATH))["labels"])[:10]

# 기존 mini(기본온도,버킷1) 전체 micro — 근접 게이트(온도차라 정확히 같진 않음)
MINI_DEFAULT_FULL = (0.616, 0.750)


def load_labels():
    return json.load(open(LABELS_PATH))["labels"]


def _inputs(pid):
    parsed = json.load(open(config.OUT_DIR / f"{pid}.parsed.json"))["text"]
    concepts = json.load(open(config.OUT_DIR / f"{pid}.concepts.json"))
    defines = ", ".join(m["name"] for m in concepts.get("defines", [])) or "(none)"
    return defines, parsed


def relate_call(model, pid):
    """(builds_on, latency_s, usage) — temp=0, v2 프롬프트/스키마."""
    from openai import OpenAI
    client = OpenAI()
    defines, text = _inputs(pid)
    user = RELATE_USER.format(defines=defines, text=text)
    t0 = time.time()
    resp = client.chat.completions.create(
        model=model, temperature=0,
        messages=[{"role": "system", "content": RELATE_SYSTEM},
                  {"role": "user", "content": user}],
        response_format={"type": "json_schema", "json_schema": RELATE_SCHEMA},
    )
    dt = time.time() - t0
    bo = json.loads(resp.choices[0].message.content)["builds_on"]
    u = resp.usage
    usage = {"prompt": u.prompt_tokens, "completion": u.completion_tokens, "total": u.total_tokens}
    return bo, dt, usage


def cmd_one(tag, pid, force=False):
    out = DIRS[tag] / f"{pid}.relations.json"
    if out.exists() and not force:
        print(f"{tag}/{pid}: skip"); return
    bo, dt, usage = relate_call(MODELS[tag], pid)
    out.write_text(json.dumps({"builds_on": bo}, ensure_ascii=False, indent=2))
    (DIRS[tag] / f"{pid}.meta.json").write_text(
        json.dumps({"latency_s": round(dt, 3), "usage": usage}, ensure_ascii=False, indent=2))
    print(f"{tag}/{pid}: {bo}  ({dt:.1f}s, {usage['total']}tok)")


def cmd_determinism():
    res = {}
    for tag in MODELS:
        rows = []
        for pid in det_pids():
            stored = json.load(open(DIRS[tag] / f"{pid}.relations.json"))["builds_on"]
            bo2, _, _ = relate_call(MODELS[tag], pid)
            same = json.dumps(stored, ensure_ascii=False) == json.dumps(bo2, ensure_ascii=False)
            rows.append({"pid": pid, "same": same,
                         "stored": stored, "rerun": bo2})
            print(f"{tag}/{pid}: {'SAME' if same else 'DIFF'}")
        res[tag] = {"n": len(rows), "same": sum(r["same"] for r in rows), "rows": rows}
    DET_PATH.write_text(json.dumps(res, ensure_ascii=False, indent=2))
    for tag in MODELS:
        print(f"{tag}: {res[tag]['same']}/{res[tag]['n']} 재현 동일")
    print(f"저장: {DET_PATH.relative_to(ROOT)}")


# ── 채점 (normalize_core, 버킷1 lexicon) ──
_COMPONENT_TOOL = ["PPO", "GRPO", "Group Relative Policy Optimization",
    "Monte Carlo Tree Search", "MCTS", "RL", "reinforcement learning",
    "RAGAS", "ARES", "TruLens"]
_SUBSTRATE = ["BERT", "RoBERTa", "GPT-2", "GPT-3", "GPT-J", "T5", "PaLM", "OPT",
    "BLOOM", "Qwen", "Qwen-2.5", "LLaMA", "Llama"]


def _sets():
    return ({nc.canon(x) for x in _COMPONENT_TOOL}, {nc.canon(x) for x in _SUBSTRATE})


def fp_category(rk, COMP, SUB):
    if rk in COMP:
        return "component_tool"
    if rk in SUB:
        return "substrate"
    return "method_misjudged"


def label_of(st, rk):
    return st["rep_meta"].get(rk, {}).get("label", rk)


def names(tag, pid):
    return json.load(open(DIRS[tag] / f"{pid}.relations.json")).get("builds_on", [])


def score_paper(st, gold_names, pred_names, COMP, SUB):
    gold = {nc.resolve(st, n)[0] for n in gold_names}
    pred_raw = {nc.resolve(st, n)[0] for n in pred_names}
    pred = {k for k in pred_raw if nc.status_of(st, k) in nc.NODE_OK}
    TP, FP, FN = gold & pred, pred - gold, gold - pred
    fn_reason = {k: ("lexicon_dropped" if k in pred_raw else "not_extracted") for k in FN}
    fp_cat = {k: fp_category(k, COMP, SUB) for k in FP}
    return {"gold": gold, "pred": pred, "pred_raw": pred_raw,
            "TP": TP, "FP": FP, "FN": FN, "fn_reason": fn_reason, "fp_cat": fp_cat}


def aggregate(rows):
    sTP = sum(len(r["TP"]) for r in rows); sFP = sum(len(r["FP"]) for r in rows)
    sFN = sum(len(r["FN"]) for r in rows)
    mp = sTP / (sTP + sFP) if (sTP + sFP) else None
    mr = sTP / (sTP + sFN) if (sTP + sFN) else None
    pv, rv = [], []
    for r in rows:
        tp, fp, fn = len(r["TP"]), len(r["FP"]), len(r["FN"])
        if tp + fp > 0: pv.append(tp / (tp + fp))
        if tp + fn > 0: rv.append(tp / (tp + fn))
    Mp = sum(pv) / len(pv) if pv else None
    Mr = sum(rv) / len(rv) if rv else None
    fp_by = {"component_tool": 0, "substrate": 0, "method_misjudged": 0}
    for r in rows:
        for k in r["FP"]: fp_by[r["fp_cat"][k]] += 1
    ld = sum(1 for r in rows for v in r["fn_reason"].values() if v == "lexicon_dropped")
    ne = sum(1 for r in rows for v in r["fn_reason"].values() if v == "not_extracted")
    return {"n": len(rows), "sumTP": sTP, "sumFP": sFP, "sumFN": sFN,
            "micro_p": mp, "micro_r": mr, "macro_p": Mp, "macro_r": Mr,
            "fp_by": fp_by, "fn_lex": ld, "fn_ne": ne}


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else "—"


def delta(n, o):
    if n is None or o is None: return "—"
    d = n - o
    return f"{'+' if d >= 0 else '−'}{abs(d):.3f}"


def cmd_report():
    st = nc.load_lex_state()
    COMP, SUB = _sets()
    labels = load_labels()
    pp = json.load(open(PAPERS_PATH))
    groups = {"new_collected": set(pp["new_collected"]), "from_corpus": set(pp["from_corpus"])}

    def grp(pid):
        return ("new_collected" if pid in groups["new_collected"]
                else "from_corpus" if pid in groups["from_corpus"] else "?")

    # 존재 확인
    for tag in MODELS:
        miss = [pid for pid in labels if not (DIRS[tag] / f"{pid}.relations.json").exists()]
        if miss:
            print(f"⚠️ {tag} 미추출 {len(miss)}: {miss} — 중단"); sys.exit(1)

    rows = {tag: {pid: score_paper(st, labels[pid]["builds_on"], names(tag, pid), COMP, SUB)
                  for pid in labels} for tag in MODELS}

    SETS = {
        "전체(50)": list(labels),
        "new_collected": [p for p in labels if grp(p) == "new_collected"],
        "from_corpus": [p for p in labels if grp(p) == "from_corpus"],
    }
    AGG = {tag: {name: aggregate([rows[tag][p] for p in pids]) for name, pids in SETS.items()}
           for tag in MODELS}

    # 게이트: mini@0 전체가 기존 mini(기본온도) 근처
    am = AGG["mini"]["전체(50)"]
    near = abs(am["micro_p"] - MINI_DEFAULT_FULL[0]) < 0.06 and abs(am["micro_r"] - MINI_DEFAULT_FULL[1]) < 0.06
    print(f"게이트(근접): mini@0 전체 ({am['micro_p']:.3f},{am['micro_r']:.3f}) vs 기존 {MINI_DEFAULT_FULL} "
          f"→ {'OK' if near else '⚠️ 차이 큼(점검)'}")

    # determinism
    det = json.load(open(DET_PATH)) if DET_PATH.exists() else None

    # 비용/속도 (meta)
    def meta_stats(tag):
        lat, tot = [], []
        for pid in labels:
            mp = DIRS[tag] / f"{pid}.meta.json"
            if mp.exists():
                m = json.load(open(mp)); lat.append(m["latency_s"]); tot.append(m["usage"]["total"])
        return (sum(lat)/len(lat) if lat else None, sum(tot)/len(tot) if tot else None, len(lat))
    cost = {tag: meta_stats(tag) for tag in MODELS}

    # full이 고친 mini의 오류 (mini FP - full FP), full이 새로 낸 FP, 재현율 회복
    def itemset(tag, key):
        return {(pid, k) for pid in labels for k in rows[tag][pid][key]}
    mini_fp, full_fp = itemset("mini", "FP"), itemset("full", "FP")
    fixed_fp = mini_fp - full_fp      # full이 없앤 mini FP
    new_fp = full_fp - mini_fp        # full이 새로 낸 FP
    mini_tp, full_tp = itemset("mini", "TP"), itemset("full", "TP")
    full_gain_tp = full_tp - mini_tp  # full이 더 맞힌 것
    full_lost_tp = mini_tp - full_tp  # full이 잃은 것

    def cat_at(tag, pid, k):
        r = rows[tag][pid]
        return r["fp_cat"].get(k, "?")

    # ── md ──
    L = []; A = L.append
    A("# 모델 비교 — gpt-5.4-mini vs gpt-5.4(full), temperature=0")
    A("")
    A("프로젝트 핵심 질문 = \"굳이 더 큰/비싼 모델이 필요한가.\" 라이브 v2 프롬프트 그대로, **모델만** "
      "`gpt-5.4-mini`→`gpt-5.4` 로 바꿔 50편 재추출·재채점. 같은 프롬프트·lexicon(버킷1)·goldset·"
      "채점규칙. 변수는 모델 하나. 두 모델 다 **temperature=0**(샘플링 분산 제거 → Δ=모델 능력 차).")
    A("")

    # determinism 먼저(게이트)
    A("## 1. determinism 체크 (temp=0가 결정적인가 — 1차 게이트)")
    A("")
    if det:
        for tag in MODELS:
            d = det[tag]
            A(f"- **{tag}** ({MODELS[tag]}): {d['same']}/{d['n']} 편 재호출 byte-동일.")
        allsame = all(det[tag]["same"] == det[tag]["n"] for tag in MODELS)
        if allsame:
            A("")
            A("→ 두 모델 모두 temp=0에서 **완전 결정적**(노이즈 바닥=0). 단일 run 비교를 신뢰할 수 있고, "
              "아래 Δ는 전부 모델 능력 차이지 샘플링 분산이 아니다.")
        else:
            A("")
            A("→ 일부 비결정적 — 아래 diff를 노이즈 바닥으로 보고 그보다 작은 Δ는 단정 보류.")
            for tag in MODELS:
                diffs = [r for r in det[tag]["rows"] if not r["same"]]
                for r in diffs:
                    A(f"  - {tag}/{r['pid']}: stored={r['stored']} vs rerun={r['rerun']}")
    else:
        A("- (determinism 미실행)")
    A("")

    # 점수표
    A("## 2. 점수표 (mini@0 / full@0 / Δ)")
    A("")
    for name in ["전체(50)", "new_collected", "from_corpus"]:
        m, f = AGG["mini"][name], AGG["full"][name]
        A(f"### {name}")
        A("")
        A("| | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |")
        A("|---|--:|--:|--:|--:|--:|--:|--:|")
        A(f"| mini@0 | {fmt(m['micro_p'])} | {fmt(m['micro_r'])} | {fmt(m['macro_p'])} | {fmt(m['macro_r'])} | {m['sumTP']} | {m['sumFP']} | {m['sumFN']} |")
        A(f"| full@0 | {fmt(f['micro_p'])} | {fmt(f['micro_r'])} | {fmt(f['macro_p'])} | {fmt(f['macro_r'])} | {f['sumTP']} | {f['sumFP']} | {f['sumFN']} |")
        A(f"| Δ | {delta(f['micro_p'],m['micro_p'])} | {delta(f['micro_r'],m['micro_r'])} | {delta(f['macro_p'],m['macro_p'])} | {delta(f['macro_r'],m['macro_r'])} | {f['sumTP']-m['sumTP']:+d} | {f['sumFP']-m['sumFP']:+d} | {f['sumFN']-m['sumFN']:+d} |")
        A("")

    # FP/FN 종류 변화
    A("## 3. FP/FN 종류 변화 (full이 mini의 무엇을 고치나)")
    A("")
    m, f = AGG["mini"]["전체(50)"], AGG["full"]["전체(50)"]
    A("| 종류 | mini@0 | full@0 | Δ |")
    A("|---|--:|--:|--:|")
    for cat in ["component_tool", "substrate", "method_misjudged"]:
        A(f"| FP:{cat} | {m['fp_by'][cat]} | {f['fp_by'][cat]} | {f['fp_by'][cat]-m['fp_by'][cat]:+d} |")
    A(f"| FN:lexicon탈락 | {m['fn_lex']} | {f['fn_lex']} | {f['fn_lex']-m['fn_lex']:+d} |")
    A(f"| FN:not_extracted | {m['fn_ne']} | {f['fn_ne']} | {f['fn_ne']-m['fn_ne']:+d} |")
    A("")
    A(f"**full이 없앤 mini FP {len(fixed_fp)}건:**")
    A("")
    for pid, k in sorted(fixed_fp):
        A(f"- [{cat_at('mini',pid,k)}] {label_of(st,k)} — {labels[pid]['title']} ({pid}, {grp(pid)})")
    if not fixed_fp: A("- (없음)")
    A("")
    A(f"**full이 새로 낸 FP {len(new_fp)}건:**")
    A("")
    for pid, k in sorted(new_fp):
        A(f"- [{cat_at('full',pid,k)}] {label_of(st,k)} — {labels[pid]['title']} ({pid}, {grp(pid)})")
    if not new_fp: A("- (없음)")
    A("")
    A(f"**재현율: full이 더 맞힌 TP {len(full_gain_tp)} / 잃은 TP {len(full_lost_tp)}** "
      "(모델만 바꾸면 not_extracted FN은 입력에 없어 안 변하는 게 정상 — 회복 있으면 본문에 있던 걸 mini가 놓친 것).")
    A("")
    for pid, k in sorted(full_gain_tp):
        A(f"- +TP {label_of(st,k)} — {labels[pid]['title']} ({pid})")
    for pid, k in sorted(full_lost_tp):
        A(f"- −TP {label_of(st,k)} — {labels[pid]['title']} ({pid})")
    A("")

    # 비용/속도
    A("## 4. 비용 / 속도 (호출당, 측정값)")
    A("")
    A("| 모델 | 평균 지연(s) | 평균 total tokens | n |")
    A("|---|--:|--:|--:|")
    for tag in MODELS:
        lat, tot, n = cost[tag]
        A(f"| {tag} ({MODELS[tag]}) | {lat:.2f} | {tot:.0f} | {n} |")
    lm, _, _ = cost["mini"]; lf, _, _ = cost["full"]
    A("")
    A(f"- 지연 비율 full/mini ≈ **{lf/lm:.1f}×** (측정). 토큰량은 입력이 같아 prompt는 비슷, "
      "차이는 completion. 달러 비용은 공급자 per-token 가격비에 비례(가격표 기준 별도 확인 — 본 리포트는 "
      "측정 가능한 토큰·지연만 보고).")
    A("")

    # 판정
    A("## 5. 판정 재료")
    A("")
    dP = f["micro_p"] - m["micro_p"]; dR = f["micro_r"] - m["micro_r"]
    deterministic = bool(det and all(det[t]["same"] == det[t]["n"] for t in MODELS))
    noise = "0(완전 결정적)" if deterministic else "비결정(위 §1)"
    delta_interp = "전부 모델 능력 차" if deterministic else "노이즈 위에서만 해석"
    prec_phrase = "component_tool/method_misjudged FP를 줄여 " if dP > 0 else ""
    recall_phrase = "거의 불변" if abs(dR) < 0.03 else (delta(f["micro_r"], m["micro_r"]) + " 변동")
    A(f"full@0 전체 micro P {fmt(m['micro_p'])}→{fmt(f['micro_p'])} ({delta(f['micro_p'],m['micro_p'])}), "
      f"R {fmt(m['micro_r'])}→{fmt(f['micro_r'])} ({delta(f['micro_r'],m['micro_r'])}). "
      f"determinism 노이즈 바닥={noise}이므로 이 Δ는 {delta_interp}. "
      f"full은 주로 {prec_phrase}정밀도에 작용했고(부품·baseline 오인 구분이 더 정확), "
      f"재현율은 {recall_phrase}"
      f"(남은 FN이 not_extracted라 모델 키워도 입력에 없는 건 못 뽑음 — 예상대로). "
      f"지연 {lf/lm:.1f}× 더 든다. **판정: full의 정밀도 이득이 노이즈를 넘는지 + 비용을 정당화하는지로 "
      f"업그레이드 여부를 사람이 정한다. full≈mini면 '미니로 충분'(프론티어 불필요)이 헤드라인 결론.**")
    A("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))

    for name in ["전체(50)", "new_collected", "from_corpus"]:
        m2, f2 = AGG["mini"][name], AGG["full"][name]
        print(f"{name}: mini P{fmt(m2['micro_p'])}/R{fmt(m2['micro_r'])}  full P{fmt(f2['micro_p'])}/R{fmt(f2['micro_r'])}")
    print(f"full 없앤 FP {len(fixed_fp)} / 새 FP {len(new_fp)} / +TP {len(full_gain_tp)} / -TP {len(full_lost_tp)}")
    print(f"\n생성: {OUT_MD.relative_to(ROOT)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "one":
        cmd_one(sys.argv[2], sys.argv[3], "--force" in sys.argv)
    elif cmd == "determinism":
        cmd_determinism()
    elif cmd == "report":
        cmd_report()
    else:
        print(f"unknown cmd: {cmd}"); sys.exit(1)


if __name__ == "__main__":
    main()
