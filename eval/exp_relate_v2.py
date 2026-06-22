"""실험: relate 프롬프트 v2로 goldset 50편 builds_on 재추출 (별도 디렉토리).

한 변수만 바뀐다 — relate 프롬프트만 v1→v2. 모델(config.MODEL=gpt-5.4-mini)·입력
(config.OUT_DIR의 concepts/parsed)·lexicon·goldset은 전부 v1 실험과 동일.

- relate.main()을 쓰지 않는다: main()은 config.PAPER_IDS(코퍼스 54편)만 돌아
  goldset 50편과 불일치(new_collected 21편 누락). 여기선 labels.json의 50편을 직접 순회.
- baseline 출력 data/outputs/{id}.relations.json 은 절대 안 건드린다.
  v2 결과는 eval/experiments/relate_v2/{id}.relations.json 에만 쓴다.
- 이미 있는 출력은 skip(--force로 재실행). LLM 50회 호출.

실행: uv run python eval/exp_relate_v2.py [--force]
"""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import config
from relate import relate_one            # src/relate.py의 핵심 함수 재사용 (config.MODEL 그대로)

V2_DIR = ROOT / "eval/experiments/relate_v2"
V2_DIR.mkdir(parents=True, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="기존 출력 무시하고 재추출")
    args = ap.parse_args()

    gold = json.loads((ROOT / "eval/goldset/labels.json").read_text())["labels"]
    n_new = n_skip = 0
    for pid in gold:                          # 50편 (new_collected + from_corpus 전부)
        out = V2_DIR / f"{pid}.relations.json"
        if out.exists() and not args.force:
            n_skip += 1
            print(f"{pid}: skip (이미 있음)")
            continue
        concepts = json.loads((config.OUT_DIR / f"{pid}.concepts.json").read_text())
        text = json.loads((config.OUT_DIR / f"{pid}.parsed.json").read_text())["text"]
        r = relate_one(concepts, text)        # config.MODEL = gpt-5.4-mini 그대로
        out.write_text(json.dumps(r, ensure_ascii=False, indent=2))
        n_new += 1
        print(f"{pid}: {r['builds_on']}")
    print(f"\n신규 {n_new}, skip {n_skip}, 총 {len(gold)}편 → {V2_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
