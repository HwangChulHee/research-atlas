#!/usr/bin/env python
"""PHASE A4/A5 집계 — 서브에이전트 결과(ma_res_0..7.json)를 모아:
  A4: keep_drop_ma.csv 매니페스트 + papers.json 에 multiagent_b3 그룹 append(포맷 보존)
  A5: labels.json 에 keep 논문 builds_on 초안 append(group 태그·draft, freeze 안 함)
      + boundary flag 요약 출력(A5 STOP 보고용)

가드: labels.json round-trip 안정성 확인 후에만 재덤프. papers.json은 외과적 텍스트 삽입.
frozen 50·RAG 85 라벨/relations 무변경. --write 없으면 dry-run.
"""
import json
import csv
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCR = Path("/tmp/claude-1000/-home-hch-research-atlas/bc3b4f80-ec33-4d42-8106-55c57f63f882/scratchpad")
EXP = ROOT / "eval/goldset/expansion_ma"
PAPERS = ROOT / "eval/goldset/papers.json"
LABELS = ROOT / "eval/goldset/labels.json"
WRITE = "--write" in sys.argv
GROUP = "multiagent_b3"

# ── 1. 서브에이전트 결과 수합
res = []
missing = []
for b in range(8):
    fp = SCR / f"ma_res_{b}.json"
    if not fp.exists():
        missing.append(b); continue
    res.extend(json.load(open(fp)))
if missing:
    print(f"⚠ 누락 배치: {missing} — 완료 대기 필요. 중단."); sys.exit(1)
res = {r["id"]: r for r in res}.values()  # dedup by id
res = sorted(res, key=lambda r: r["id"])
keep = [r for r in res if r["keep"]]
drop = [r for r in res if not r["keep"]]
print(f"수합 {len(res)}편 = keep {len(keep)} / drop {len(drop)}")

# ── 2. keep_drop_ma.csv
with (EXP/"keep_drop_ma.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["arxiv_id","decision","builds_on_draft","boundary_flags","drop_reason","one_line","title"])
    for r in res:
        w.writerow([r["id"], "keep" if r["keep"] else "drop",
                    ";".join(r.get("builds_on") or []),
                    ";".join(r.get("boundary_flags") or []),
                    r.get("drop_reason") or "",
                    r.get("one_line",""), r.get("title","")])
print(f"keep_drop_ma.csv 기록({len(res)}행)")

# ── 3. papers.json 외과적 삽입 (multiagent_b3 = keep ids, 6/줄)
keep_ids = sorted(r["id"] for r in keep)
raw = PAPERS.read_text()
if f'"{GROUP}"' in raw:
    print(f"⚠ papers.json 에 {GROUP} 이미 존재 — 삽입 스킵")
else:
    lines = []
    for i in range(0, len(keep_ids), 6):
        chunk = ", ".join(f'"{x}"' for x in keep_ids[i:i+6])
        lines.append("    " + chunk)
    block = f',\n  "{GROUP}": [\n' + ",\n".join(lines) + "\n  ]"
    # 마지막 배열 닫힘 "]" 다음(파일 끝 "}") 앞에 삽입
    m = list(re.finditer(r'\]', raw))
    last_bracket_end = m[-1].end()
    new_raw = raw[:last_bracket_end] + block + raw[last_bracket_end:]
    # 검증: 파싱되고 그룹이 keep_ids와 일치
    parsed = json.loads(new_raw)
    assert parsed[GROUP] == keep_ids, "papers.json 삽입 검증 실패"
    if WRITE:
        PAPERS.write_text(new_raw)
    print(f"papers.json {GROUP} 삽입: {len(keep_ids)}편 (검증 OK, write={WRITE})")

# ── 4. labels.json append (round-trip 가드)
orig = LABELS.read_text()
data = json.loads(orig)
# round-trip 안정성: 기존 내용이 json.dump(indent=2) 로 바이트 동일 재현되는지
roundtrip = json.dumps(data, ensure_ascii=False, indent=2)
if not orig.rstrip("\n") == roundtrip:
    print("⚠ labels.json round-trip 불안정 — 재덤프 시 대량 diff 위험. 외과 삽입 필요.")
    stable = False
else:
    stable = True
    print("labels.json round-trip 안정 확인")

added = 0
for r in keep:
    pid = r["id"]
    if pid in data["labels"]:
        continue
    data["labels"][pid] = {
        "title": r.get("title", pid),
        "builds_on": r.get("builds_on") or [],
        "group": GROUP,
        "draft": True,
    }
    added += 1
# _meta 갱신(주석만 — frozen 135 status 불변)
data["_meta"]["_draft_note_ma"] = (f"{GROUP} 초안 {added}편 append(2026-07-07, D1~D4). "
    f"draft:true·미freeze — 사용자 검수 대기. frozen 135(status labels_frozen)·baseline 불변.")
new_labels = json.dumps(data, ensure_ascii=False, indent=2)
if orig.endswith("\n"):
    new_labels += "\n"
if WRITE and stable:
    LABELS.write_text(new_labels)
print(f"labels.json {GROUP} 초안 append: {added}편 (write={WRITE and stable})")

# ── 5. boundary flag 요약(A5 STOP 보고)
print("\n=== 경계 플래그(A5 STOP 보고) ===")
nflag = 0
for r in res:
    fl = r.get("boundary_flags") or []
    if fl:
        nflag += 1
        print(f"  {r['id']} {r.get('title','')[:34]:34} {' | '.join(fl)}")
print(f"→ 경계 플래그 있는 논문: {nflag}편")
print("\n=== DROP 목록 ===")
for r in drop:
    print(f"  {r['id']} {r.get('title','')[:40]:40} — {r.get('drop_reason','')}")
