"""수집 에이전트 스모크 — agents.collect의 부품을 호출만 하는 검증 진입점.

각 스모크는 한 단계군을 돌려보고 하드 게이트(assert)로 회귀를 잡는다. 수집 로직·
프롬프트·그래프 정의는 일절 건드리지 않고 agents.collect 의 기존 함수만 부른다.
(라이브 모드 — collect_extract_smoke·graph_smoke 정상경로는 실제 추출/Neo4j 반영.
 eval 격리가 필요하면 eval/test_collect.py 를 쓴다.)

실행(레포 루트에서):
    uv run python eval/smoke_collect.py                       # [1][2] intent_smoke (기본)
    uv run python eval/smoke_collect.py --collect-smoke       # [3][4][5]
    uv run python eval/smoke_collect.py --collect-extract-smoke  # …→[6][7][8]
    uv run python eval/smoke_collect.py --graph-smoke         # LangGraph 흐름 3시나리오
"""
import json
import sys


from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from backend.agents.collect import (  # noqa: E402
    DEFAULT_EXTRACT,
    EMBED_MODEL,
    PAPERS_LEDGER,
    build_collect_graph,
    build_status_report,
    config,
    dedup_new_candidates,
    embed_query,
    expand_query,
    extract_pipeline,
    extract_target,
    gate_one,
    load_embeddings,
    match,
    parse_intent,
    save_ledger,
    search_arxiv,
    upsert_ledger,
    _run_scenario,
)

SMOKE = [
    "2024년 RAG 강건성 논문 가져와줘",
    "knowledge graph 만드는 논문들 찾아와",
    "멀티에이전트 협업 관련 최신 논문 수집해줘",
]


def intent_smoke():
    """[1][2] 스모크 — 의도파싱 + 현황확인 + 현황보고."""
    model, norm, (ck, cm), (pk, pm) = load_embeddings()
    try:
        assert model == EMBED_MODEL, f"model 불일치: {model}"
        assert len(ck) == 73, f"개념 임베딩 73 기대, 실제 {len(ck)}"
        assert len(pk) == 68, f"논문 임베딩 68 기대, 실제 {len(pk)}"
    except AssertionError as e:
        print(f"게이트 실패: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"게이트 통과: 개념 {len(ck)} + 논문 {len(pk)} (model={model})\n")
    for query in SMOKE:
        intent = parse_intent(query)
        q = embed_query(intent["topic"], model)
        cm_hits = match(q, ck, cm)
        pm_hits = match(q, pk, pm)
        report = build_status_report(intent, cm_hits, pm_hits, norm)
        print(f'"{query}"\n  topic: {intent["topic"]}')
        print(report)
        print()


def collect_smoke():
    """[3][4][5] 스모크 — 검색어 확장 → arXiv 검색 → 장부 upsert → 신규 후보."""
    model, norm, (ck, cm), (pk, pm) = load_embeddings()
    query = "RAG 강건성 논문 찾아줘"  # period 없음(전체 기간) — 결과 비어있지 않게
    intent = parse_intent(query)
    topic = intent["topic"]

    # [2] 관련어 추출 — 보유 개념/논문을 검색어 확장 재료로
    qv = embed_query(topic, model)
    cm_hits, pm_hits = match(qv, ck, cm), match(qv, pk, pm)
    related = [norm[k]["canonical"] for k, _ in cm_hits if k in norm]
    related += [norm[k].get("title", "") for k, _ in pm_hits if k in norm]
    related = [r for r in related if r][:10]

    queries = expand_query(topic, related)            # [3]
    found = search_arxiv(queries, intent.get("period_from", ""),
                         intent.get("period_to", ""))  # [4]
    ledger = upsert_ledger(found)
    new, counts = dedup_new_candidates(found, ledger)  # [5]

    # --- 출력 (게이트보다 먼저 — 실패해도 출력은 보이게) ---
    print(f'"{query}"  →  topic: {topic}\n')
    print(f"[3] 검색어 {len(queries)}개:")
    for q in queries:
        print(f"   • {q}")
    print(f"\n[4] arXiv 발견 {counts['found']}편 (검색어 {len(queries)}개, 검색어당 max 50)")
    print("   샘플 3편:")
    for aid in list(found)[:3]:
        m = found[aid]
        print(f"   • {aid} [{m['published']}] {m['title']}")
        print(f"     {m['abstract'][:160]}…")
    print(f"\n[5] dedup: 발견 {counts['found']} / 보유제외 {counts['owned_excluded']} / "
          f"관문탈락제외 {counts['gate_excluded']} / 신규 {counts['new']}")
    print(f"   장부: {PAPERS_LEDGER} (총 {len(ledger)}편 누적)")

    # --- 하드 게이트 ---
    try:
        assert isinstance(queries, list) and all(isinstance(x, str) for x in queries) \
            and len(queries) >= 3, f"검색어 확장 실패: {queries}"
        assert len(found) > 0, "arXiv 검색 결과 0편 (네트워크/파싱 실패 의심)"
        complete = sum(1 for m in found.values()
                       if m["title"] and m["abstract"] and m["published"])
        assert complete * 2 >= len(found), f"메타 완전성 과반 미달: {complete}/{len(found)}"
        assert isinstance(json.loads(PAPERS_LEDGER.read_text()), dict), "papers.json 파싱 실패"
    except AssertionError as e:
        print(f"\n게이트 실패: {e}", file=sys.stderr)
        sys.exit(1)
    print("\n게이트 통과: 검색어 확장·arXiv 검색·메타 완전성·장부 OK")


def collect_extract_smoke():
    """[3][4][5] → [6] 물량승인(CLI) → [7] 관문 → [8] 통과분 상위 target편 추출."""
    model, norm, (ck, cm), (pk, pm) = load_embeddings()
    query = "RAG 강건성 논문 찾아줘"
    intent = parse_intent(query)
    topic = intent["topic"]
    target = extract_target(intent)   # 편수 미언급 → DEFAULT_EXTRACT

    qv = embed_query(topic, model)
    cm_hits, pm_hits = match(qv, ck, cm), match(qv, pk, pm)
    related = [norm[k]["canonical"] for k, _ in cm_hits if k in norm]
    related += [norm[k].get("title", "") for k, _ in pm_hits if k in norm]
    related = [r for r in related if r][:10]

    queries = expand_query(topic, related)
    found = search_arxiv(queries, intent.get("period_from", ""), intent.get("period_to", ""))
    ledger = upsert_ledger(found)
    new, counts = dedup_new_candidates(found, ledger)
    print(f'"{query}"  →  topic: {topic}')
    print(f"[3][4][5] 검색어 {len(queries)} / 발견 {counts['found']} / "
          f"보유제외 {counts['owned_excluded']} / 신규 {counts['new']}\n")

    # --- [6] 물량 승인 (CLI 임시) ---
    ans = input(f"신규 후보 {counts['new']}편 발견. 관문+추출 진행? (PDF를 받습니다) [y/N]: ").strip().lower()
    if ans != "y":
        print("중단 — 관문/추출 안 함.")
        return

    # --- [7] 관문: 후보 전체 분류 ---
    print("\n[7] 관문(초록만 보고 분류):")
    passed, gate_calls = [], 0
    for aid in new:
        verdict, ok, cached = gate_one(aid, ledger)
        gate_calls += 0 if cached else 1
        mark = "통과" if ok else "—"
        print(f"   {aid} [{verdict:9}] {mark}{' (캐시)' if cached else ''}  {ledger[aid]['title'][:58]}")
        if ok:
            passed.append(aid)
    save_ledger(ledger)
    print(f"   → 통과 {len(passed)}/{len(new)} (관문 LLM {gate_calls}회, 캐시 {len(new) - gate_calls}회)")

    # --- [8] 추출: 통과분 상위 target편 ---
    to_extract = passed[:target]
    if len(passed) > target:
        print(f"\n   목표로 {target}편만 추출 (통과 {len(passed)}편 중 나머지는 관문 기록만)")
    print(f"\n[8] 추출 {len(to_extract)}편 (PDF 다운로드 시작):")
    extracted = []
    for aid in to_extract:
        ok, msg, concepts = extract_pipeline(aid, ledger)
        if ok:
            extracted.append(aid)
            print(f"   {aid}: {msg} — [{concepts['paper_type']}] "
                  f"defines={[m['name'] for m in concepts['defines']]}")
        else:
            print(f"   {aid}: {msg} (스킵)")  # 실패해도 중단 안 함
    save_ledger(ledger)
    print(f"\n추출 완료 {len(extracted)}편 (Neo4j 반영 완료).")

    # --- 하드 게이트 ---
    try:
        assert new, "신규 후보 0편 — 관문/추출 검증 불가"
        assert all(ledger[a].get("gate") for a in new), "관문 미기록 후보 있음"
        assert len(extracted) <= target, f"목표 편수 초과: {len(extracted)} > {target}"
        for a in extracted:
            assert (config.OUT_DIR / f"{a}.concepts.json").exists() \
                and (config.OUT_DIR / f"{a}.relations.json").exists(), f"{a} 추출 파일 없음"
    except AssertionError as e:
        print(f"\n게이트 실패: {e}", file=sys.stderr)
        sys.exit(1)
    print("게이트 통과: 관문 전체 기록·추출 상한·추출 파일 생성 OK")


def graph_smoke():
    graph = build_collect_graph(MemorySaver())  # 스모크는 휘발성(db 파일 안 건드림)
    Q = "RAG 강건성 논문 찾아줘"

    print("=" * 64)
    print("시나리오 A: 취소 경로 (proceed → cancel)")
    r_cancel, s_cancel = _run_scenario(graph, "smoke-cancel", Q, ["proceed", "cancel"])

    print("\n" + "=" * 64)
    print("시나리오 B: 수정 경로 (revise → 재해석 → proceed → cancel)")
    r_rev, s_rev = _run_scenario(graph, "smoke-revise", Q,
                                 ["revise: RAG robustness to noisy retrieval", "proceed", "cancel"])

    print("\n" + "=" * 64)
    print("시나리오 C: 정상 경로 (proceed → proceed → proceed → 추출)")
    r_norm, s_norm = _run_scenario(graph, "smoke-normal", Q, ["proceed", "proceed", "proceed"])

    # --- 하드 게이트 ---
    try:
        # 1: compile 성공 (여기 도달했으면 OK)
        # 2: interrupt 1에서 멈춤 — status_report 있고 expand 아직 안 됨
        p_payload, p_vals = s_norm[0]
        assert p_payload["stage"] == "interpret", "첫 멈춤이 해석확인이 아님"
        assert p_vals.get("status_report"), "멈춤 시 status_report 없음"
        assert not p_vals.get("counts"), "멈춤 시 이미 expand됨(counts 존재)"
        # interrupt 3개: interpret → approve → extract_confirm
        assert len(s_norm) == 3, f"정상경로 멈춤 3회 아님: {len(s_norm)}"
        assert [s[0]["stage"] for s in s_norm] == ["interpret", "approve", "extract_confirm"], \
            "멈춤 순서가 interpret→approve→extract_confirm 아님"
        # 핵심: extract_confirm 멈춤 시점에 추출은 아직 0편(관문·추출 분리 증거)
        assert not s_norm[2][1].get("extracted"), "추출승인 멈춤인데 이미 추출됨"
        # 3: cancel → 추출 0
        assert r_cancel.get("extracted", []) == [], f"취소인데 추출됨: {r_cancel.get('extracted')}"
        # 4: 정상 → 추출 ≤ 목표(편수 미언급이라 DEFAULT_EXTRACT), 파일 생성
        ex = r_norm.get("extracted", [])
        assert len(ex) <= DEFAULT_EXTRACT, f"추출 목표 초과: {ex}"
        for a in ex:
            assert (config.OUT_DIR / f"{a}.concepts.json").exists(), f"{a} 추출 파일 없음"
        # revise: 재해석으로 돌아가 interrupt 1 재멈춤(깨지지 않음)
        assert len(s_rev) >= 2 and s_rev[0][0]["stage"] == "interpret" \
            and s_rev[1][0]["stage"] == "interpret", "수정 후 재해석 재멈춤 아님"
        assert r_rev.get("extracted", []) == [], "수정→취소인데 추출됨"
    except AssertionError as e:
        print(f"\n게이트 실패: {e}", file=sys.stderr)
        sys.exit(1)
    print("\n게이트 통과: compile·interrupt 멈춤(3회)·관문/추출 분리·cancel 추출0·정상 추출≤상한·revise 재해석 OK")


if __name__ == "__main__":
    if "--graph-smoke" in sys.argv:
        graph_smoke()
    elif "--collect-extract-smoke" in sys.argv:
        collect_extract_smoke()
    elif "--collect-smoke" in sys.argv:
        collect_smoke()
    else:
        intent_smoke()
