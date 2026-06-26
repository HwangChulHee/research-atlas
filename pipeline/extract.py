"""04 extract: parsed → 내용(defines/uses/task/problem/domain)."""
import argparse
import json

from pipeline import config
from prompts.pipeline.extract import EXTRACT_SYSTEM, EXTRACT_USER, EXTRACT_SCHEMA

client = config.make_openai_client()


def extract_one(text: str) -> dict:
    resp = client.chat.completions.create(
        model=config.MODEL_EXTRACT,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": EXTRACT_USER.format(text=text)},
        ],
        response_format={"type": "json_schema", "json_schema": EXTRACT_SCHEMA},
    )
    return json.loads(resp.choices[0].message.content)


def load_text(pid: str) -> str:
    return json.loads((config.OUT_DIR / f"{pid}.parsed.json").read_text())["text"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    ids = config.PAPER_IDS if args.run else config.PAPER_IDS[:2]
    n_new = n_skip = n_err = 0
    for pid in ids:
        out = config.OUT_DIR / f"{pid}.concepts.json"
        if args.run and out.exists() and not args.force:
            n_skip += 1; print(f"{pid}: skip"); continue
        try:                                  # 1편 실패가 배치 전체를 중단시키지 않게 격리
            c = extract_one(load_text(pid))
        except Exception as e:
            n_err += 1; print(f"{pid}: ERROR {type(e).__name__}: {e}"); continue
        if args.run:
            out.write_text(json.dumps(c, ensure_ascii=False, indent=2)); n_new += 1
        print(f"{pid}: [{c['paper_type']}] defines={[m['name'] for m in c['defines']]} domain={c['domain']}")
    if args.run:
        print(f"\n신규 {n_new}, skip {n_skip}, 실패 {n_err}")


if __name__ == "__main__":
    main()
