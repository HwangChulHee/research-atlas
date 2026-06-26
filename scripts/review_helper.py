"""HITL 검토 도우미 — 제안만, 결정 안 함 (read-only).

검토 대기 개념(status ∈ {pending, unreviewed})마다 "리뷰 카드"를 만든다:
근거(evidence) + 분류(category) + 제안 행동(approve/reject/merge) + 확신도.
**lexicon.json은 절대 안 건드린다** — 순수 제안 리포트. approve/reject/merge는 사람이 최종 클릭.

왜 결정 안 하나: P0.82의 신뢰는 "기계가 뽑고 사람이 검증"에서 나온다. 도우미가 판정하면
"LLM을 LLM이 검증"이 되어 그 신뢰가 증발한다. 그래서 출력은 제안+근거+확신도일 뿐이다.

입력(전부 기존 데이터 재사용):
- data/lexicon.json (검토 대기 = pending/unreviewed)
- data/outputs/{id}.concepts.json (defines: 정의된 논문 + 정의문, title)
- data/outputs/{id}.relations.json (builds_on: 조상으로 언급된 논문)
- pipeline/normalize_core.py 의 resolve/status_of/load_lex_state (표기 정규화·기존 개념 조회 재사용)

출력: eval/reports/review_suggestions.json + .md

실행: uv run python scripts/review_helper.py
      uv run python scripts/review_helper.py --smoke   # 가설 5개만 PASS/FAIL
"""
import argparse
import glob
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
from pipeline import config
from pipeline import normalize_core as nc

OUT_DIR = config.OUT_DIR
REPORT_DIR = ROOT / "eval" / "reports"
REVIEW_STATUSES = {"pending", "unreviewed"}

client = config.make_openai_client()

RUBRIC_SYSTEM = """\
너는 논문 지식그래프 사전(lexicon)의 검토를 *돕는* 도우미다. 너는 결정하지 않는다 —
분류·근거·제안만 하고 사람이 최종 승인/거부/병합한다. 그러니 단정 대신 근거를 인용하라.

개념 후보 하나의 근거(evidence)를 읽고, 아래 루브릭으로 분류·제안하라.

분류(category)와 기본 행동(action):
- lineage → approve : 본문에 고유명사로 나오는 *명명된 방법/기법*(다른 논문이 extends/improves 대상).
- component → reject : 학습 부품(PPO, GRPO, MCTS, SFT, RL 등) — 명명된 방법 노드가 아님.
- generic → reject : 일반어(RL, SFT, fine-tuning, "attention mechanisms" 등).
- substrate → reject : 실험 백본으로 *그냥 돌린* 베이스모델("experiments with Qwen").
- author_year → reject : "Brown et al. (2020)" 같은 저자-연도 인용.
- umbrella → reject : 변별력 낮은 모호 우산 범주(Tool-Integrated Reasoning/TIR 류).
- duplicate → merge : 기존 개념의 표기 변종(similar_existing가 그 후보). merge_into에 기존 개념명.

핵심 가드(이름만으로 판정 금지 — evidence를 읽어라):
- "X를 적응·확장해 방법을 세움(over/based on X)"이면 substrate가 아니라 lineage다
  (예: ColBERT = "late interaction over BERT" → BERT는 lineage).
- 어떤 이름이 다른 논문의 builds_on(조상)으로 인용됐다는 사실 자체가 계보 신호다.
  베이스모델처럼 보여도 계보 부모일 수 있다(예: DeepSeek-V3-Base가 DeepSeek-R1의 부모).
  → 이런 경우 substrate로 high-confidence reject 하지 마라. lineage이거나, 애매하면 confidence=low.
- "Active RAG", "agentic RAG"처럼 일반어/우산처럼 보여도 명명된 패러다임일 수 있다.
  → 자동 reject 말고 confidence=low로 사람에게 넘겨라.
- 애매하면 confidence=low로 두고 action은 보수적으로(reject로 단정 말 것).

reason은 **반드시 한국어로** 한 문장(영어로 쓰지 말 것). 가능하면 evidence(정의문/인용 논문)를 인용하라.
confidence: high(명백) / med / low(애매 — 사람 주목).
"""

RESP_SCHEMA = {
    "name": "review_suggestion",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["lineage", "component", "generic", "substrate",
                         "author_year", "umbrella", "duplicate"],
            },
            "action": {"type": "string", "enum": ["approve", "reject", "merge"]},
            "merge_into": {"type": ["string", "null"]},
            "reason": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "med", "low"]},
        },
        "required": ["category", "action", "merge_into", "reason", "confidence"],
        "additionalProperties": False,
    },
}


# ── 근거 인덱스 (concepts/relations 전체 1회 스캔) ─────────────────────────
def build_evidence_index(st):
    """resolve로 표기 정규화하며 rk별 근거 모음. (수기 alias 맵 금지 — resolve 재사용.)"""
    defined, cited, paper_title = {}, {}, {}
    for fp in glob.glob(str(OUT_DIR / "*.concepts.json")):
        pid = Path(fp).name.rsplit(".concepts.json", 1)[0]
        con = json.loads(Path(fp).read_text())
        paper_title[pid] = con.get("title", pid)
        for d in con.get("defines", []):
            rk, _ = nc.resolve(st, d["name"])
            defined.setdefault(rk, []).append(
                {"paper": pid, "definition": d.get("definition", "")}
            )
    for fp in glob.glob(str(OUT_DIR / "*.relations.json")):
        pid = Path(fp).name.rsplit(".relations.json", 1)[0]
        rel = json.loads(Path(fp).read_text())
        for nm in rel.get("builds_on", []):
            rk, _ = nc.resolve(st, nm)
            cited.setdefault(rk, []).append(pid)
    return defined, cited, paper_title


def _tokens(s):
    return set(nc.canon(s).split())


def _initials(s):
    return "".join(t[0] for t in nc.canon(s).split() if t)


def find_similar(st, cand_rk, cand_label):
    """기존 *승인된(approved)* 개념 중 표기 변종 후보 1개(문자열 휴리스틱). 없으면 None.
    merge는 '정당한 노드로의 통합'이라 대상은 approved만(미검토끼리 merge하면 부품→부품 통합이
    돼버려 분류 판단을 가린다 — 그 경우 후보 자체를 reject로 판단하게 둔다). acronym > 부분집합 > Jaccard."""
    ca, ta, ia = nc.canon(cand_label), _tokens(cand_label), _initials(cand_label)
    best, best_score = None, 0.0
    for rk, meta in st["rep_meta"].items():
        if rk == cand_rk or meta.get("status") != "approved":
            continue
        lb = meta["label"]
        cb, tb, ib = nc.canon(lb), _tokens(lb), _initials(lb)
        if ca == cb:
            continue
        score = 0.0
        # acronym 양방향 (한쪽이 단일 토큰일 때)
        if (len(tb) == 1 and ia and ia == cb) or (len(ta) == 1 and ib and ib == ca):
            score = max(score, 0.95)
        # 토큰 부분집합
        if ta and tb and (ta <= tb or tb <= ta):
            score = max(score, 0.8)
        # 토큰 Jaccard
        if ta and tb:
            j = len(ta & tb) / len(ta | tb)
            if j >= 0.6:
                score = max(score, j)
        if score > best_score:
            best, best_score = lb, score
    return best if best_score > 0 else None


def make_card_input(st, name, meta, defined, cited, paper_title):
    rk = nc.canon(name)
    defs = defined.get(rk, [])
    cites = list(dict.fromkeys(cited.get(rk, [])))  # dedup, 순서 보존
    definition = meta.get("definition", "") or (defs[0]["definition"] if defs else "")
    similar = find_similar(st, rk, name)
    evidence = {
        "name": name,
        "status": meta.get("status"),
        "definition": definition,
        "defined_in": [
            {"paper": d["paper"], "title": paper_title.get(d["paper"], d["paper"]),
             "definition": d["definition"]}
            for d in defs[:3]
        ],
        "cited_as_ancestor_in": [
            {"paper": p, "title": paper_title.get(p, p)} for p in cites[:6]
        ],
        "similar_existing_concept": similar,
    }
    return rk, evidence, similar


def suggest_one(evidence):
    resp = client.chat.completions.create(
        model=config.MODEL_RELATE,  # 판단 → full(relate에서 +0.20 입증). 97개라 비용 무의미.
        temperature=0,
        messages=[
            {"role": "system", "content": RUBRIC_SYSTEM},
            {"role": "user", "content": json.dumps(evidence, ensure_ascii=False)},
        ],
        response_format={"type": "json_schema", "json_schema": RESP_SCHEMA},
    )
    return json.loads(resp.choices[0].message.content)


def build_card(st, name, meta, defined, cited, paper_title):
    rk, evidence, similar = make_card_input(st, name, meta, defined, cited, paper_title)
    s = suggest_one(evidence)
    action = s["action"]
    if action == "merge":
        action_str = f"merge_into:{s.get('merge_into') or similar or '?'}"
    else:
        action_str = action
    return {
        "concept": name,
        "status": meta.get("status"),
        "evidence": {
            "defined_in": evidence["defined_in"],
            "cited_in": [c["paper"] for c in evidence["cited_as_ancestor_in"]],
            "definition": evidence["definition"],
        },
        "similar_existing": similar,
        "suggestion": {
            "category": s["category"],
            "action": action_str,
            "reason": s["reason"],
            "confidence": s["confidence"],
        },
    }


# ── 출력 ──────────────────────────────────────────────────────────────────
CONF_ORDER = {"low": 0, "med": 1, "high": 2}


def render_md(cards):
    n = len(cards)
    appr = sum(1 for c in cards if c["suggestion"]["action"] == "approve")
    rej = sum(1 for c in cards if c["suggestion"]["action"] == "reject")
    mrg = sum(1 for c in cards if c["suggestion"]["action"].startswith("merge"))
    low = [c for c in cards if c["suggestion"]["confidence"] == "low"]

    L = ["# 검토 도우미 — 제안 리포트 (결정 아님 · lexicon 무변경)", ""]
    L.append(f"검토 대기 **{n}개** · 제안 분포: approve {appr} · reject {rej} · merge {mrg}")
    L.append(f"· **확신 낮음 {len(low)}개**(사람 우선 검토)")
    L.append("")
    L.append("> 이 문서는 *제안*이다. approve/reject/merge는 사람이 최종 클릭한다.")
    L.append("")

    def card_block(c):
        s = c["suggestion"]
        out = [f"### {c['concept']}  `{c['status']}`",
               f"- 제안: **{s['action']}** · {s['category']} · 확신 {s['confidence']}",
               f"- 근거: {s['reason']}"]
        if c["similar_existing"]:
            out.append(f"- 유사 기존 개념: `{c['similar_existing']}`")
        if c["evidence"]["definition"]:
            out.append(f"- 정의: {c['evidence']['definition'][:240]}")
        if c["evidence"]["defined_in"]:
            ps = ", ".join(d["paper"] for d in c["evidence"]["defined_in"])
            out.append(f"- 정의한 논문: {ps}")
        if c["evidence"]["cited_in"]:
            out.append(f"- 조상으로 인용: {', '.join(c['evidence']['cited_in'])}")
        out.append("")
        return out

    # 확신 오름차순(low 먼저 — 사람 주의가 애매한 데 가게)
    detailed = sorted(
        [c for c in cards if c["suggestion"]["confidence"] in ("low", "med")],
        key=lambda c: CONF_ORDER[c["suggestion"]["confidence"]],
    )
    L.append("## ⚠️ 확신 낮음·중간 — 한 장씩 검토")
    L.append("")
    if not detailed:
        L.append("(없음)\n")
    for c in detailed:
        L += card_block(c)

    # high-confidence는 category별로 묶어 일괄
    high = [c for c in cards if c["suggestion"]["confidence"] == "high"]
    L.append("## ✅ 확신 높음 — category별 일괄 검토")
    L.append("")
    by_cat = {}
    for c in high:
        by_cat.setdefault(c["suggestion"]["category"], []).append(c)
    for cat in sorted(by_cat):
        rows = by_cat[cat]
        L.append(f"### {cat} — {len(rows)}개")
        for c in rows:
            sim = f" → {c['similar_existing']}" if c["similar_existing"] else ""
            L.append(f"- **{c['concept']}** ({c['suggestion']['action']}{sim}) — {c['suggestion']['reason']}")
        L.append("")
    return "\n".join(L)


# ── 스모크 ────────────────────────────────────────────────────────────────
SMOKE = {
    "GRPO": dict(action="reject", conf_high_ok=True, must_not_reject_high=False),
    "DeepSeek-R1": dict(action="approve", conf_high_ok=True, must_not_reject_high=False),
    "Dense Passage Retriever": dict(action="merge", conf_high_ok=True, must_not_reject_high=False),
    "DeepSeek-V3-Base": dict(action=None, conf_high_ok=True, must_not_reject_high=True),
    "Active RAG": dict(action=None, conf_high_ok=True, must_not_reject_high=True),
}


def run_smoke(st, defined, cited, paper_title):
    lex = st["lex"]

    def find_meta(name):
        # 정확 매칭 우선, 없으면 resolve로 대표 찾기
        if name in lex:
            return name, lex[name]
        rk, label = nc.resolve(st, name)
        return (label, lex.get(label)) if label in lex else (name, None)

    print("=" * 64)
    print("SMOKE — 가설 대조")
    print("=" * 64)
    ok = True
    for name, exp in SMOKE.items():
        label, meta = find_meta(name)
        if meta is None:
            print(f"[SKIP] {name}: 사전에 없음")
            continue
        card = build_card(st, label, meta, defined, cited, paper_title)
        s = card["suggestion"]
        act, conf = s["action"], s["confidence"]
        passed = True
        # 하드 가드: high-confidence reject로 나오면 안 되는 반례
        if exp["must_not_reject_high"] and act == "reject" and conf == "high":
            passed = False
        # 기대 action(있으면)
        if exp["action"] == "merge" and not act.startswith("merge"):
            passed = False
        elif exp["action"] in ("approve", "reject") and act != exp["action"]:
            passed = False
        ok = ok and passed
        tag = "PASS" if passed else "FAIL"
        print(f"[{tag}] {label:32} → {act} ({s['category']}/{conf})")
        print(f"        {s['reason']}")
    print("-" * 64)
    print("스모크:", "PASS ✅" if ok else "FAIL ❌")
    return ok


def generate_cards(candidates, st, defined, cited, paper_title):
    """후보 리스트 → 카드 리스트(병렬). (생성된 카드, 실패목록) 반환."""
    cards = [None] * len(candidates)
    fail = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {
            ex.submit(build_card, st, name, meta, defined, cited, paper_title): i
            for i, (name, meta) in enumerate(candidates)
        }
        done = 0
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                cards[i] = fut.result()
            except Exception as e:  # noqa: BLE001
                fail.append((candidates[i][0], repr(e)))
            done += 1
            if done % 20 == 0:
                print(f"  {done}/{len(candidates)}", flush=True)
    return [c for c in cards if c], fail


def write_reports(cards):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "review_suggestions.json").write_text(
        json.dumps(cards, ensure_ascii=False, indent=2)
    )
    (REPORT_DIR / "review_suggestions.md").write_text(render_md(cards))


def load_existing_cards():
    p = REPORT_DIR / "review_suggestions.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def summary(cards):
    appr = sum(1 for c in cards if c["suggestion"]["action"] == "approve")
    rej = sum(1 for c in cards if c["suggestion"]["action"] == "reject")
    mrg = sum(1 for c in cards if c["suggestion"]["action"].startswith("merge"))
    low = sum(1 for c in cards if c["suggestion"]["confidence"] == "low")
    return f"{len(cards)}개 · approve {appr} · reject {rej} · merge {mrg} · 확신낮음 {low}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="가설 5개만 PASS/FAIL")
    ap.add_argument("--incremental", action="store_true",
                    help="기존 스냅샷 유지하고, 카드 없는 신규 검토대기 개념만 생성")
    args = ap.parse_args()

    st = nc.load_lex_state()
    defined, cited, paper_title = build_evidence_index(st)

    if args.smoke:
        run_smoke(st, defined, cited, paper_title)
        return

    candidates = [
        (name, meta) for name, meta in st["lex"].items()
        if meta.get("status") in REVIEW_STATUSES
    ]

    if args.incremental:
        existing = {c["concept"]: c for c in load_existing_cards()}
        cand_names = {name for name, _ in candidates}
        kept = [existing[n] for n in cand_names if n in existing]  # 아직 대기 중인 기존 카드만
        todo = [(name, meta) for name, meta in candidates if name not in existing]
        print(f"증분: 기존 카드 {len(kept)} 유지 · 신규 {len(todo)} 생성 "
              f"(model={config.MODEL_RELATE}, temp=0)…", flush=True)
        new_cards, fail = generate_cards(todo, st, defined, cited, paper_title)
        cards = kept + new_cards
    else:
        print(f"검토 대기 {len(candidates)}개 — 제안 생성"
              f"(model={config.MODEL_RELATE}, temp=0)…", flush=True)
        cards, fail = generate_cards(candidates, st, defined, cited, paper_title)

    if fail:
        print(f"⚠️ 실패 {len(fail)}: {fail[:3]}")
    write_reports(cards)
    print(f"\n완료 {summary(cards)}")
    print("저장: eval/reports/review_suggestions.{json,md}")


if __name__ == "__main__":
    main()
