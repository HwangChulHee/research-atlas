#!/usr/bin/env python
"""수집 에이전트 반자동 diff 테스트 (rough — 7월 정식 평가의 선행 버전).

한 번 실행 = 한 회차:
    백업 → 자동수집(interrupt 자동통과) → normalize 반영 → diff → 복원.
데이터는 매번 원상복구되어 다음 실행도 같은 출발점에서 시작한다.

핵심 원칙: 실제 normalized_v2.json / lexicon.json / papers.json 등을 건드리므로,
에러·Ctrl-C 무엇에도 try/finally 로 복원이 보장된다. 수집 로직·프롬프트·그래프 정의는
일절 건드리지 않고 agent_collect 의 기존 함수를 호출만 한다.

사용:
    uv run python test_collect.py "llm 에이전트 메모리 관련 조사해줘"
    uv run python test_collect.py --query-file queries.txt   # 줄단위, 각각 독립 회차

범위 밖(7월): 같은 질문 자동 N회 반복 루프·일관성 메트릭·정답지 대조.
"""
import datetime
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUTS = DATA / "outputs"
PDFS = DATA / "pdfs"                    # 추출이 PDF를 받는 곳(백업 범위 밖·재다운로드 가능)
LEXICON = DATA / "lexicon.json"
NORMALIZED = OUTPUTS / "normalized_v2.json"
SNAP = DATA / "_snapshot_test"          # 완료된 백업(= pristine 본)
SNAP_TMP = DATA / "_snapshot_test.tmp"  # 작성 중 백업(원자적 rename 전)
RUNS = DATA / "test_runs"               # 회차 산출물(JSON, gitignore)

sys.path.insert(0, str(ROOT))
# agent_collect import 는 OpenAI 클라이언트·임베딩 로더를 띄움(수집에 필요) — 정상.
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from agent_collect import _run_scenario, build_collect_graph  # noqa: E402


# ---------- 백업 / 복원 (데이터 안전) ----------
def backup():
    """data/outputs/ 통째 + lexicon.json 을 스냅샷으로. 작성 후 원자적 rename →
    SNAP 이름이 보이면 항상 '완전한' 백업임이 보장된다(부분 스냅샷 방지)."""
    if SNAP_TMP.exists():
        shutil.rmtree(SNAP_TMP)
    SNAP_TMP.mkdir(parents=True)
    shutil.copytree(OUTPUTS, SNAP_TMP / "outputs")
    shutil.copy2(LEXICON, SNAP_TMP / "lexicon.json")
    SNAP_TMP.rename(SNAP)


def restore():
    """스냅샷 → data/outputs/, lexicon.json 되돌리고 스냅샷 정리. 멱등(스냅샷 없으면 무동작)."""
    if not SNAP.exists():
        return
    if OUTPUTS.exists():
        shutil.rmtree(OUTPUTS)
    shutil.copytree(SNAP / "outputs", OUTPUTS)
    shutil.copy2(SNAP / "lexicon.json", LEXICON)
    shutil.rmtree(SNAP)


def preflight():
    """실행 전 안전 점검: 부분 스냅샷 청소, 직전 미복원 스냅샷 자동 복구, data/ dirty 경고."""
    if SNAP_TMP.exists():  # 직전 실행이 백업 도중 죽음 → 불완전, 버림
        shutil.rmtree(SNAP_TMP)
    if SNAP.exists():
        # 완료 스냅샷이 남아있음 = 직전 실행이 복원 못 하고 종료. 스냅샷이 pristine 본이므로 복구.
        print("⚠ 이전 스냅샷 발견 — 직전 실행이 복원 전에 끝난 듯. 먼저 복구합니다.")
        restore()
    r = subprocess.run(["git", "status", "--porcelain", "data/"],
                       cwd=str(ROOT), capture_output=True, text=True)
    dirty = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if dirty:
        print(f"⚠ 커밋 안 된 data/ 변경 {len(dirty)}건 — 스냅샷/복원이 덮을 수 있어요(계속 진행).")
        for ln in dirty[:8]:
            print("   ", ln)


# ---------- 상태 로드 (diff 기준선) ----------
def _strip(nid):
    return nid.split(":", 1)[1] if ":" in nid else nid


def load_view(path):
    """normalized_v2.json → diff용 요약 {concepts, papers, lineage}.

    개념간 builds_on(계보)은 normalized_v2 에 직접 저장돼 있지 않고 paper→concept 엣지에서
    유도된다. build_graph_view(api/main.py)의 파생 규칙을 읽기 전용으로 미러(home concept =
    그 논문이 처음 defines 한 개념, 그 개념 → builds_on 대상들). 진단만, 아무것도 안 고침.
    """
    raw = json.loads(path.read_text())
    nodes, edges = raw["nodes"], raw["edges"]
    concepts = {_strip(k): n.get("canonical", _strip(k))
                for k, n in nodes.items() if n.get("type") == "concept"}
    papers = {_strip(k) for k, n in nodes.items() if n.get("type") == "paper"}

    defines_first, builds_by_paper = {}, {}
    for e in edges:
        pid, rk = e["from"], _strip(e["to"])
        if e["type"] == "defines":
            defines_first.setdefault(pid, rk)
        elif e["type"] == "builds_on":
            builds_by_paper.setdefault(pid, []).append(rk)

    lineage = set()
    for pid, targets in builds_by_paper.items():
        src = defines_first.get(pid)
        if src is None:           # defines 없는 논문 → 개념간 계보 없음
            continue
        for tgt in targets:
            if tgt != src and tgt in concepts:
                lineage.add((src, tgt))
    return {"concepts": concepts, "papers": papers, "lineage": lineage}


def load_lex_status(path):
    techs = json.loads(path.read_text()).get("techniques", {})
    return {name: meta.get("status", "unreviewed") for name, meta in techs.items()}


# ---------- diff ----------
def build_record(query, before, after, lex_before, lex_after):
    name = lambda rk: after["concepts"].get(rk, rk)  # noqa: E731
    add_concepts = sorted(after["concepts"][rk] for rk in after["concepts"]
                          if rk not in before["concepts"])
    add_papers = sorted(p for p in after["papers"] if p not in before["papers"])
    add_edges = sorted(f"{name(a)} → {name(b)}" for a, b in after["lineage"]
                       if (a, b) not in before["lineage"])
    add_lex = sorted(n for n in lex_after if n not in lex_before)
    new_unreviewed = sorted(n for n in add_lex if lex_after[n] == "unreviewed")
    return {
        "query": query,
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "added_concepts": add_concepts,
        "added_papers": add_papers,
        "added_edges": add_edges,
        "lexicon_added": add_lex,
        "lexicon_new_unreviewed": new_unreviewed,
    }


def print_diff(r):
    print(f'\n질문: "{r["query"]}"   ({r["time"].replace("T", " ")})')
    nc, npp, ne = r["added_concepts"], r["added_papers"], r["added_edges"]
    if not (nc or npp or ne or r["lexicon_added"]):
        print("+ 추가 없음 (전부 기존/dedup)")
        return
    if nc:
        print(f"+ 개념 {len(nc)}:  " + ", ".join(nc))
    if npp:
        print(f"+ 논문 {len(npp)}:  " + ", ".join(npp))
    if ne:
        print(f"+ 계보 {len(ne)}:  " + ", ".join(ne))
    if r["lexicon_added"]:
        print(f"+ lexicon: unreviewed 신규 {len(r['lexicon_new_unreviewed'])}  (검수 대기)")


def write_record(r):
    RUNS.mkdir(parents=True, exist_ok=True)
    fn = RUNS / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    fn.write_text(json.dumps(r, ensure_ascii=False, indent=2))
    print(f"기록: {fn.relative_to(ROOT)}")


# ---------- 한 회차 ----------
def run_one(query):
    """백업 → 수집 → normalize → diff → (finally)복원. 복원은 무슨 일이 있어도 실행."""
    backup()
    # 이번 회차가 새로 받은 PDF만 정리하기 위한 기준(기존 PDF는 절대 안 건드림).
    pdfs_before = {p.name for p in PDFS.glob("*")} if PDFS.exists() else set()
    try:
        before = load_view(NORMALIZED)
        lex_before = load_lex_status(LEXICON)

        # --- 수집 (interrupt 3개를 'proceed' 자동응답으로 통과, MAX_EXTRACT 상한) ---
        # 세션 DB(SqliteSaver) 오염 방지 위해 MemorySaver 휘발성 그래프 사용.
        graph = build_collect_graph(MemorySaver())
        tid = "test-" + uuid.uuid4().hex[:8]
        print(f"\n=== 수집 시작: {query!r} (thread {tid}) ===")
        _run_scenario(graph, tid, query, ["proceed", "proceed", "proceed"])

        # --- normalize 반영 (추출분 → 노드/lexicon) ---
        print("\n=== normalize_v2 반영 ===")
        proc = subprocess.run([sys.executable, str(ROOT / "src" / "normalize_v2.py")],
                             cwd=str(ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"normalize_v2 실패:\n{proc.stderr or proc.stdout}")

        # --- diff ---
        after = load_view(NORMALIZED)
        lex_after = load_lex_status(LEXICON)
        record = build_record(query, before, after, lex_before, lex_after)
        print_diff(record)
        write_record(record)
        return record
    finally:
        restore()
        # 이번 회차가 새로 받은 PDF 부산물만 제거(기존 캐시는 보존).
        if PDFS.exists():
            for p in PDFS.glob("*"):
                if p.name not in pdfs_before:
                    p.unlink()
        print("복원 완료 — data/ 원상복구.\n")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--query-file":
        if len(args) < 2:
            sys.exit('사용: test_collect.py --query-file <파일>')
        lines = Path(args[1]).read_text().splitlines()
        queries = [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    elif args:
        queries = [" ".join(args)]  # 따옴표 없이 줘도 한 질문으로 합침
    else:
        sys.exit('사용: test_collect.py "질문"   또는   test_collect.py --query-file <파일>')

    if not queries:
        sys.exit("질문이 비어 있음.")

    preflight()
    for i, q in enumerate(queries):
        if i:
            print("=" * 64)
        run_one(q)


if __name__ == "__main__":
    main()
