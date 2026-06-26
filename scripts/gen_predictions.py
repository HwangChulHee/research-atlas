"""eval 예측 생성 — 주어진 골든셋 그룹에 extract/relate를 돌려 concepts/relations JSON 생성.

라이브 Neo4j 미접촉(graphdb 호출 없음, JSON 파일만 생성). score_buildson가 읽는
config.OUT_DIR(data/outputs/)에 기록. 모델/temp는 pipeline.config 단일 출처.

용례(batch2 out-of-sample 적재, B안):
  # frozen 50 재측정(few-shot 포함 현 relate 프롬프트로 baseline 재생성 — relate만, --force)
  uv run python scripts/gen_predictions.py --groups new_collected,from_corpus --relate --force
  # batch2 85 신규 생성(parsed 재사용 → extract → relate)
  uv run python scripts/gen_predictions.py --groups survey_sourced_b2 \
      --parsed-src eval/goldset/expansion/parsed --extract --relate --force
"""
import argparse
import json
import shutil

from pipeline import config
from pipeline import extract as extract_mod
from pipeline import relate as relate_mod

PAPERS = config.ROOT / "eval/goldset/papers.json"


def ids_for(groups):
    p = json.loads(PAPERS.read_text())
    ids = []
    for g in groups:
        if g not in p:
            raise SystemExit(f"papers.json에 그룹 없음: {g}")
        ids += p[g]
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", required=True, help="papers.json 그룹들(쉼표구분)")
    ap.add_argument("--parsed-src", help="parsed.json 출처 디렉토리(없으면 OUT_DIR 가정)")
    ap.add_argument("--extract", action="store_true", help="extract 실행(concepts 생성)")
    ap.add_argument("--relate", action="store_true", help="relate 실행(relations 생성)")
    ap.add_argument("--force", action="store_true", help="기존 산출물 덮어쓰기")
    args = ap.parse_args()

    groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    ids = ids_for(groups)
    O = config.OUT_DIR
    print(f"대상 {len(ids)}편 (groups={groups}) | extract={args.extract} relate={args.relate} "
          f"force={args.force}")
    print(f"models: extract={config.MODEL_EXTRACT} relate={config.MODEL_RELATE} (relate temp=0)")

    # parsed 확보(필요 시 복사 — PDF/parse 재실행 금지, 재사용만)
    if args.parsed_src:
        src = config.ROOT / args.parsed_src
        copied = 0
        for pid in ids:
            sp = src / f"{pid}.parsed.json"
            dp = O / f"{pid}.parsed.json"
            if sp.exists() and not dp.exists():
                shutil.copy2(sp, dp); copied += 1
        print(f"parsed 복사: {copied}편 ({src} → {O})")

    n_ex = n_re = n_skip = n_err = 0
    for i, pid in enumerate(ids, 1):
        parsed = O / f"{pid}.parsed.json"
        if not parsed.exists():
            print(f"[{i}/{len(ids)}] {pid}: parsed 없음 — skip"); n_err += 1; continue
        text = json.loads(parsed.read_text())["text"]

        # extract
        cpath = O / f"{pid}.concepts.json"
        if args.extract and (args.force or not cpath.exists()):
            try:
                c = extract_mod.extract_one(text)
                cpath.write_text(json.dumps(c, ensure_ascii=False, indent=2)); n_ex += 1
            except Exception as e:
                print(f"[{i}/{len(ids)}] {pid}: EXTRACT ERROR {type(e).__name__}: {e}"); n_err += 1; continue

        # relate (concepts 필요)
        rpath = O / f"{pid}.relations.json"
        if args.relate and (args.force or not rpath.exists()):
            if not cpath.exists():
                print(f"[{i}/{len(ids)}] {pid}: concepts 없음 — relate skip"); n_err += 1; continue
            try:
                concepts = json.loads(cpath.read_text())
                r = relate_mod.relate_one(concepts, text)
                rpath.write_text(json.dumps(r, ensure_ascii=False, indent=2)); n_re += 1
                print(f"[{i}/{len(ids)}] {pid}: builds_on={r.get('builds_on')}")
            except Exception as e:
                print(f"[{i}/{len(ids)}] {pid}: RELATE ERROR {type(e).__name__}: {e}"); n_err += 1; continue
        else:
            n_skip += 1

    print(f"\n완료 — extract {n_ex}, relate {n_re}, skip {n_skip}, 실패 {n_err}")


if __name__ == "__main__":
    main()
