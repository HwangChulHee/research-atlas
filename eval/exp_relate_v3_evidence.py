"""실험 v3: relate v2 프롬프트 위에 evidence(본문 근거)를 같이 뽑게 한 버전.

한 변수만 바뀐다 — evidence 요구 on/off. 모델(config.MODEL=gpt-5.4-mini)·입력
(config.OUT_DIR concepts/parsed)·lexicon·goldset은 v2 실험과 동일.

라이브 prompts/pipeline/relate.py 는 절대 안 건드린다(v2, builds_on=list-of-strings 유지).
여기서 v2 시스템/유저 프롬프트를 가져와 evidence 문장만 덧붙이고, builds_on을 객체 배열
([{"name","evidence"}])로 받는 스키마를 쓴다. 출력은 eval/experiments/relate_v3_evidence/.

grounding 규칙: build-on 근거 span을 못 찾으면 그 항목은 builds_on에서 뺀다(비교-baseline 거름).

실행: uv run python eval/exp_relate_v3_evidence.py [--force]  (50 LLM 호출)
"""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))            # 루트 — `prompts` 패키지 import용
sys.path.insert(0, str(ROOT / "src"))    # src — config import용
import config
from openai import OpenAI
from prompts.pipeline.relate import RELATE_SYSTEM, RELATE_USER   # v2 본문 재사용 (무수정)

client = OpenAI()
V3_DIR = ROOT / "eval/experiments/relate_v3_evidence"
V3_DIR.mkdir(parents=True, exist_ok=True)

EVIDENCE_RULE = (
    "\n\nFor EACH included technique, also output `evidence`: a SHORT verbatim span "
    "(one phrase or sentence) from the paper text above showing the method is "
    "CONSTRUCTED ON it (wording like \"we extend X\", \"built on X\", \"X over Y\"). "
    "If you cannot find such a grounding span, the item does NOT belong in builds_on "
    "— drop it."
)
SYSTEM_V3 = RELATE_SYSTEM + EVIDENCE_RULE
USER_V3 = RELATE_USER.replace(
    "Output `builds_on` (NAMED prior techniques this paper's method builds on) as JSON.",
    "Output `builds_on` as a JSON array of objects, each with `name` (the technique) "
    "and `evidence` (a short verbatim span from the text showing the method builds on it).",
)
SCHEMA_V3 = {
    "name": "paper_relations_evidence",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "builds_on": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "evidence": {"type": "string"},
                    },
                    "required": ["name", "evidence"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["builds_on"],
        "additionalProperties": False,
    },
}


def relate_v3(concepts, text):
    defines = ", ".join(m["name"] for m in concepts.get("defines", [])) or "(none)"
    resp = client.chat.completions.create(
        model=config.MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_V3},
            {"role": "user", "content": USER_V3.format(defines=defines, text=text)},
        ],
        response_format={"type": "json_schema", "json_schema": SCHEMA_V3},
    )
    return json.loads(resp.choices[0].message.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="기존 출력 무시하고 재추출")
    args = ap.parse_args()

    gold = json.loads((ROOT / "eval/goldset/labels.json").read_text())["labels"]
    n_new = n_skip = n_fail = 0
    for pid in gold:                       # 50편 (labels.json 직접 순회 — main()의 54편 함정 회피)
        out = V3_DIR / f"{pid}.relations.json"
        if out.exists() and not args.force:
            n_skip += 1
            print(f"{pid}: skip (이미 있음)")
            continue
        concepts = json.loads((config.OUT_DIR / f"{pid}.concepts.json").read_text())
        text = json.loads((config.OUT_DIR / f"{pid}.parsed.json").read_text())["text"]
        try:
            r = relate_v3(concepts, text)
        except Exception as e:
            n_fail += 1
            print(f"{pid}: FAIL — {type(e).__name__}: {e}")
            continue
        out.write_text(json.dumps(r, ensure_ascii=False, indent=2))
        n_new += 1
        print(f"{pid}: {[b['name'] for b in r['builds_on']]}")
    print(f"\n신규 {n_new}, skip {n_skip}, 실패 {n_fail}, 총 {len(gold)}편 "
          f"→ {V3_DIR.relative_to(ROOT)}")
    if n_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
