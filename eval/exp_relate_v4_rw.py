"""실험 v4: relate 입력에 related work(RW)를 라벨 붙여 추가 (한 변수: RW 입력 추가).

v2 시스템 프롬프트(규칙)는 그대로. 유저 프롬프트에만 라벨된 RW 블록을 본문 뒤·출력지시 앞에
삽입한다. 모델(config.MODEL=gpt-5.4-mini)·lexicon(버킷1)·goldset·스키마(builds_on=list-of-strings)
전부 v2와 동일. 변수는 "RW 입력 추가" 하나.

대상 분할(데이터로 확정):
- copy 12편: gold builds_on==[] (survey/benchmark/foundational) OR rw verdict==no_section.
  RW 먹이면 baseline FP만 늘 위험 → v2 출력을 byte-동일 복사(재추출 안 함). 채점엔 포함(정답 []
  FP 감시). 그래서 점수는 v2와 동일 → RW 효과는 나머지 38편에서만.
- RW 38편: 나머지 전부(suspect 2편도 실제 RW라 포함).

불변: RELATE_SYSTEM(v2 규칙) 무수정, lexicon/labels/채점/config.MODEL 무수정,
baseline relate_v2·data/outputs 덮어쓰기 금지. v4 출력은 relate_v4_rw/ 에만.

서브커맨드:
  one <pid> [--force]   RW 붙여 1편 재추출 → relate_v4_rw/{id}.json (워커용, 병렬)
  copy                  copy 12편을 relate_v2 → relate_v4_rw 로 byte-복사
  split                 분할 목록 출력(워커 배치용)
  report                v4 조립(38+12) + v2 게이트 + v4 채점 + md 리포트 (메인)

실행: uv run python eval/exp_relate_v4_rw.py <cmd> ...
"""
import sys, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))            # prompts 패키지
sys.path.insert(0, str(ROOT / "src"))    # config / normalize_core
import config
import normalize_core as nc
from prompts.pipeline.relate import RELATE_SYSTEM, RELATE_USER, RELATE_SCHEMA

LABELS_PATH = ROOT / "eval/goldset/labels.json"
PAPERS_PATH = ROOT / "eval/goldset/papers.json"
V2_DIR = ROOT / "eval/experiments/relate_v2"
RW_DIR = ROOT / "eval/experiments/related_work"
V4_DIR = ROOT / "eval/experiments/relate_v4_rw"
V4_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = ROOT / "eval/reports"
OUT_MD = REPORTS_DIR / "buildson_rw_v4.md"

# §6 v2@버킷1 기준값 (게이트1)
EXPECT_V2_FULL = (0.616, 0.750)

# ── 유저 프롬프트 RW 확장 (시스템 규칙 불변) ──
RW_BLOCK = """

Related work section (prior methods the paper situates itself against — many are
comparison baselines, not ancestors; apply the same lineage-vs-comparison test):
---
{related_work}
---"""
OUTPUT_SENTINEL = "Output `builds_on` (NAMED prior techniques this paper's method builds on) as JSON."


def load_labels():
    return json.load(open(LABELS_PATH))["labels"]


def rw_verdict(pid):
    return json.load(open(RW_DIR / f"{pid}.json")).get("verdict")


def rw_text(pid):
    return json.load(open(RW_DIR / f"{pid}.json")).get("related_work_text", "")


def split():
    """(rw_pids, copy_pids) — gold []·no_section은 copy, 나머지는 RW."""
    labels = load_labels()
    rw, copy = [], []
    for pid in labels:
        if len(labels[pid]["builds_on"]) == 0 or rw_verdict(pid) == "no_section":
            copy.append(pid)
        else:
            rw.append(pid)
    return rw, copy


# ── RW 붙여 1편 추출 (워커) ──
def relate_v4_one(pid):
    from openai import OpenAI
    client = OpenAI()
    parsed = json.load(open(config.OUT_DIR / f"{pid}.parsed.json"))
    concepts = json.loads((config.OUT_DIR / f"{pid}.concepts.json").read_text())
    defines = ", ".join(m["name"] for m in concepts.get("defines", [])) or "(none)"
    text = parsed["text"]
    rw = rw_text(pid)
    # str.replace로 조립 (본문/RW에 중괄호 있어도 안전 — .format 미사용)
    user = RELATE_USER.replace("{defines}", defines).replace("{text}", text)
    rw_block = RW_BLOCK.replace("{related_work}", rw)
    user = user.replace(OUTPUT_SENTINEL, rw_block + "\n\n" + OUTPUT_SENTINEL)
    resp = client.chat.completions.create(
        model=config.MODEL,
        messages=[
            {"role": "system", "content": RELATE_SYSTEM},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_schema", "json_schema": RELATE_SCHEMA},
    )
    return json.loads(resp.choices[0].message.content)


def cmd_one(pid, force=False):
    rw_pids, copy_pids = split()
    if pid in copy_pids:
        print(f"{pid}: copy 대상(RW 안 붙임) — one 대상 아님. copy 커맨드로 처리."); return
    out = V4_DIR / f"{pid}.relations.json"
    if out.exists() and not force:
        print(f"{pid}: skip (이미 있음)"); return
    r = relate_v4_one(pid)
    out.write_text(json.dumps(r, ensure_ascii=False, indent=2))
    print(f"{pid}: {r['builds_on']}")


def cmd_copy():
    _, copy_pids = split()
    n = 0
    for pid in copy_pids:
        shutil.copyfile(V2_DIR / f"{pid}.relations.json", V4_DIR / f"{pid}.relations.json")
        n += 1
    print(f"copy 완료 {n}편 (relate_v2 → relate_v4_rw, byte-동일).")


def cmd_split():
    rw, copy = split()
    print(f"RW붙임 {len(rw)}편:"); print(" ".join(rw))
    print(f"\nv2복사 {len(copy)}편:"); print(" ".join(copy))


# ── 채점 (normalize_core 재사용, 버킷1 lexicon) ──
_COMPONENT_TOOL = ["PPO", "GRPO", "Group Relative Policy Optimization",
    "Monte Carlo Tree Search", "MCTS", "RL", "reinforcement learning",
    "RAGAS", "ARES", "TruLens"]
_SUBSTRATE = ["BERT", "RoBERTa", "GPT-2", "GPT-3", "GPT-J", "T5", "PaLM", "OPT",
    "BLOOM", "Qwen", "Qwen-2.5", "LLaMA", "Llama"]


def _setsfor(st):
    return ({nc.canon(x) for x in _COMPONENT_TOOL}, {nc.canon(x) for x in _SUBSTRATE})


def fp_category(rk, COMP, SUB):
    if rk in COMP:
        return "component_tool"
    if rk in SUB:
        return "substrate"
    return "method_misjudged"


def label_of(st, rk):
    return st["rep_meta"].get(rk, {}).get("label", rk)


def names_v2(pid):
    return json.load(open(V2_DIR / f"{pid}.relations.json")).get("builds_on", [])


def names_v4(pid):
    return json.load(open(V4_DIR / f"{pid}.relations.json")).get("builds_on", [])


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
    sTP = sum(len(r["TP"]) for r in rows)
    sFP = sum(len(r["FP"]) for r in rows)
    sFN = sum(len(r["FN"]) for r in rows)
    mp = sTP / (sTP + sFP) if (sTP + sFP) else None
    mr = sTP / (sTP + sFN) if (sTP + sFN) else None
    pv, rv = [], []
    for r in rows:
        tp, fp, fn = len(r["TP"]), len(r["FP"]), len(r["FN"])
        if tp + fp > 0:
            pv.append(tp / (tp + fp))
        if tp + fn > 0:
            rv.append(tp / (tp + fn))
    Mp = sum(pv) / len(pv) if pv else None
    Mr = sum(rv) / len(rv) if rv else None
    return {"n": len(rows), "sumTP": sTP, "sumFP": sFP, "sumFN": sFN,
            "micro_p": mp, "micro_r": mr, "macro_p": Mp, "macro_r": Mr}


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else "—"


def delta(n, o):
    if n is None or o is None:
        return "—"
    d = n - o
    return f"{'+' if d >= 0 else '−'}{abs(d):.3f}"


def cmd_report():
    st = nc.load_lex_state()
    COMP, SUB = _setsfor(st)
    labels = load_labels()
    pp = json.load(open(PAPERS_PATH))
    groups = {"new_collected": set(pp["new_collected"]), "from_corpus": set(pp["from_corpus"])}

    def grp(pid):
        return ("new_collected" if pid in groups["new_collected"]
                else "from_corpus" if pid in groups["from_corpus"] else "?")

    rw_pids, copy_pids = split()

    # 자동 copy(멱등) — 12편 byte-동일 보장
    for pid in copy_pids:
        shutil.copyfile(V2_DIR / f"{pid}.relations.json", V4_DIR / f"{pid}.relations.json")

    # 38편 추출 존재 확인
    miss = [pid for pid in rw_pids if not (V4_DIR / f"{pid}.relations.json").exists()]
    if miss:
        print(f"⚠️ RW 38편 중 미추출 {len(miss)}: {miss} — 워커 미완. 중단."); sys.exit(1)

    # v2 / v4 채점
    v2_rows, v4_rows = {}, {}
    for pid in labels:
        v2_rows[pid] = score_paper(st, labels[pid]["builds_on"], names_v2(pid), COMP, SUB)
        v4_rows[pid] = score_paper(st, labels[pid]["builds_on"], names_v4(pid), COMP, SUB)

    # 게이트1: v2 전체가 §6 재현
    a2_full = aggregate(list(v2_rows.values()))
    if not (abs(a2_full["micro_p"] - EXPECT_V2_FULL[0]) < 5e-4
            and abs(a2_full["micro_r"] - EXPECT_V2_FULL[1]) < 5e-4):
        print(f"[GATE1 FAIL] v2 전체 ({a2_full['micro_p']:.3f},{a2_full['micro_r']:.3f}) "
              f"기대 {EXPECT_V2_FULL} — 중단."); sys.exit(1)
    print("게이트1 OK — v2 전체가 §6 재현.")

    # 게이트2: copy 12편 byte-동일 + 점수 동일
    bad = [pid for pid in copy_pids
           if (V4_DIR / f"{pid}.relations.json").read_bytes() != (V2_DIR / f"{pid}.relations.json").read_bytes()]
    if bad:
        print(f"[GATE2 FAIL] copy 12편 중 byte 불일치: {bad} — 중단."); sys.exit(1)
    for pid in copy_pids:
        if (sorted(v2_rows[pid]["TP"]) != sorted(v4_rows[pid]["TP"])
                or sorted(v2_rows[pid]["FP"]) != sorted(v4_rows[pid]["FP"])):
            print(f"[GATE2 FAIL] copy {pid} 점수 불일치 — 중단."); sys.exit(1)
    print(f"게이트2 OK — copy {len(copy_pids)}편 byte+점수 동일.")

    # 게이트3: RW 38편 재현율 단조(안 내려감)
    a2_rw = aggregate([v2_rows[p] for p in rw_pids])
    a4_rw = aggregate([v4_rows[p] for p in rw_pids])
    if a4_rw["micro_r"] + 1e-9 < a2_rw["micro_r"]:
        print(f"[GATE3 FAIL] RW38 재현율 {a2_rw['micro_r']:.3f}->{a4_rw['micro_r']:.3f} 하락 — 점검.")
        sys.exit(1)
    print(f"게이트3 OK — RW38 재현율 단조 ({a2_rw['micro_r']:.3f}->{a4_rw['micro_r']:.3f}).")

    # 집계 세트
    def agg_set(pids):
        return (aggregate([v2_rows[p] for p in pids]), aggregate([v4_rows[p] for p in pids]))

    SETS = {
        "전체(50)": list(labels),
        "RW붙인(38)": rw_pids,
        "v2복사(12)": copy_pids,
    }
    GROUPS_IN_RW = {
        "RW·new_collected": [p for p in rw_pids if grp(p) == "new_collected"],
        "RW·from_corpus": [p for p in rw_pids if grp(p) == "from_corpus"],
    }

    # 회복(not_extracted FN→TP) / 새 FP (38편)
    recovered, new_fps = [], []
    for pid in rw_pids:
        o, n = v2_rows[pid], v4_rows[pid]
        for rk in sorted(n["TP"] - o["TP"]):
            was_ne = (rk in o["FN"] and o["fn_reason"].get(rk) == "not_extracted")
            recovered.append((pid, rk, was_ne))
        for rk in sorted(n["FP"] - o["FP"]):
            new_fps.append((pid, rk, n["fp_cat"][rk]))

    # RW 신호(상관용)
    rwsig = {pid: json.load(open(RW_DIR / f"{pid}.json"))["signals"] for pid in rw_pids}

    # ── md ──
    L = []; A = L.append
    A("# builds_on — relate RW 확장(v4) vs v2 (한 변수: RW 입력 추가)")
    A("")
    A("v2 시스템 규칙은 그대로 두고, **유저 프롬프트에 라벨된 related work 블록만 추가**해 재추출. "
      "같은 모델(`gpt-5.4-mini`)·lexicon(버킷1)·goldset·채점규칙. 변수는 RW 입력 하나. "
      "진짜 질문: baseline 빽빽한 RW를 먹였을 때 v2의 '비교/진단 대상 제외' 규칙이 버티나 "
      "= 재현율 회복 대비 정밀도 하락폭.")
    A("")
    A(f"분할(데이터 확정): **RW붙임 {len(rw_pids)}편**(gold≠[] AND rw∈trusted/suspect) / "
      f"**v2복사 {len(copy_pids)}편**(gold=[] survey/benchmark OR no_section — RW 먹이면 FP만 늘 위험, "
      "v2 byte-복사하되 채점엔 포함). copy 12편은 v2와 동일 → RW 효과는 38편에 집중.")
    A("")
    A("> 게이트: v2 전체 §6 재현 ✅, copy 12편 byte+점수 동일 ✅, RW38 재현율 단조 ✅.")
    A("")

    A("## 1. 점수표 (v2 → v4, 3세트)")
    A("")
    for name, pids in SETS.items():
        o, n = agg_set(pids)
        A(f"### {name}")
        A("")
        A("| | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |")
        A("|---|--:|--:|--:|--:|--:|--:|--:|")
        A(f"| v2 | {fmt(o['micro_p'])} | {fmt(o['micro_r'])} | {fmt(o['macro_p'])} | {fmt(o['macro_r'])} | {o['sumTP']} | {o['sumFP']} | {o['sumFN']} |")
        A(f"| v4 | {fmt(n['micro_p'])} | {fmt(n['micro_r'])} | {fmt(n['macro_p'])} | {fmt(n['macro_r'])} | {n['sumTP']} | {n['sumFP']} | {n['sumFN']} |")
        A(f"| Δ | {delta(n['micro_p'],o['micro_p'])} | {delta(n['micro_r'],o['micro_r'])} | {delta(n['macro_p'],o['macro_p'])} | {delta(n['macro_r'],o['macro_r'])} | {n['sumTP']-o['sumTP']:+d} | {n['sumFP']-o['sumFP']:+d} | {n['sumFN']-o['sumFN']:+d} |")
        A("")
    A("> v2복사(12)는 Δ 전부 0이어야 정상(복사 정합성).")
    A("")

    A("## 2. 그룹 분리 (RW붙인 38편 안)")
    A("")
    A("| 그룹 | v2 microP | v4 microP | ΔP | v2 microR | v4 microR | ΔR |")
    A("|---|--:|--:|--:|--:|--:|--:|")
    for name, pids in GROUPS_IN_RW.items():
        o, n = agg_set(pids)
        A(f"| {name} ({len(pids)}) | {fmt(o['micro_p'])} | {fmt(n['micro_p'])} | {delta(n['micro_p'],o['micro_p'])} | "
          f"{fmt(o['micro_r'])} | {fmt(n['micro_r'])} | {delta(n['micro_r'],o['micro_r'])} |")
    A("")

    A("## 3. 재현율 회복 (RW로 형제 계보를 봄 → FN→TP)")
    A("")
    ne_rec = [x for x in recovered if x[2]]
    A(f"회복 {len(recovered)}건 (그 중 직전 not_extracted였던 것 {len(ne_rec)}건 — RW 추가의 직접 효과).")
    A("")
    for pid, rk, was_ne in recovered:
        tag = " [이전 not_extracted]" if was_ne else ""
        A(f"- **{label_of(st,rk)}** — {labels[pid]['title']} ({pid}, {grp(pid)}){tag}")
    if not recovered:
        A("- (없음)")
    A("")

    A("## 4. ★ 정밀도 하락 — RW에서 새로 빨려든 FP (핵심)")
    A("")
    A(f"v2 exclude 규칙을 뚫고 들어온 항목 **{len(new_fps)}건**. 종류·RW 신호(char/인용밀도)와 함께 — "
      "길고 빽빽한 RW에 FP가 몰리는지 본다.")
    A("")
    A("| 논문 | id | 그룹 | name | FP종류 | RW char | RW 인용밀도 |")
    A("|---|---|---|---|---|--:|--:|")
    for pid, rk, cat in sorted(new_fps, key=lambda x: -rwsig[x[0]]["char_count"]):
        s = rwsig[pid]
        A(f"| {labels[pid]['title']} | {pid} | {grp(pid)} | {label_of(st,rk)} | {cat} | "
          f"{s['char_count']} | {s['citation_density']} |")
    if not new_fps:
        A("| (없음) | | | | | | |")
    A("")
    # 종류 분해
    from collections import Counter
    catc = Counter(c for _, _, c in new_fps)
    A(f"종류 분해: " + ", ".join(f"{k} {v}" for k, v in catc.most_common()) + ("." if catc else "(없음)."))
    A("")

    A("## 5. 해석")
    A("")
    o50, n50 = agg_set(list(labels))
    o38, n38 = agg_set(rw_pids)
    A(f"전체50 micro P {fmt(o50['micro_p'])}→{fmt(n50['micro_p'])} ({delta(n50['micro_p'],o50['micro_p'])}), "
      f"R {fmt(o50['micro_r'])}→{fmt(n50['micro_r'])} ({delta(n50['micro_r'],o50['micro_r'])}). "
      f"효과가 집중된 RW38: P {fmt(o38['micro_p'])}→{fmt(n38['micro_p'])} ({delta(n38['micro_p'],o38['micro_p'])}), "
      f"R {fmt(o38['micro_r'])}→{fmt(n38['micro_r'])} ({delta(n38['micro_r'],o38['micro_r'])}). "
      f"재현율 회복 {len(ne_rec)}건(not_extracted→TP) 대비 새 FP {len(new_fps)}건이 정밀도 하락의 실체다. "
      f"새 FP의 종류 분포({', '.join(f'{k} {v}' for k,v in catc.most_common()) or '없음'})와 RW 신호 상관(§4)이 "
      f"'v2 exclude 규칙이 RW에서 버텼는지'의 판정 재료 — method_misjudged가 많으면 비교-baseline을 "
      f"계보로 오인한 것(규칙이 RW 밀집도에 밀림), component/substrate가 많으면 부품·백본 혼입이다. "
      f"채택(=RW를 라이브 relate에 넣을지)은 이 재현율 회복 vs 정밀도 하락 트레이드오프를 보고 사람이 정한다.")
    A("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))

    for name, pids in SETS.items():
        o, n = agg_set(pids)
        print(f"{name}: P {fmt(o['micro_p'])}->{fmt(n['micro_p'])}  R {fmt(o['micro_r'])}->{fmt(n['micro_r'])}")
    print(f"회복 {len(recovered)}(ne {len(ne_rec)}) / 새FP {len(new_fps)}")
    print(f"\n생성: {OUT_MD.relative_to(ROOT)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "one":
        cmd_one(sys.argv[2], "--force" in sys.argv)
    elif cmd == "copy":
        cmd_copy()
    elif cmd == "split":
        cmd_split()
    elif cmd == "report":
        cmd_report()
    else:
        print(f"unknown cmd: {cmd}"); sys.exit(1)


if __name__ == "__main__":
    main()
