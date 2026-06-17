"""정답지 50편 번역 워크시트 '스켈레톤' 생성 (라벨링 준비).

입력: 이미 있는 data/outputs/{id}.parsed.json 의 text(= abstract+intro, 파이프라인이 본 그 텍스트).
출력: eval/goldset/translations/{id}.md — 원문 + 번역 placeholder + 빈 'builds_on' 칸.

번역은 외부 API가 아니라 Claude Code(클로드)가 직접 채운다 — 스켈레톤의
'<!-- TODO: 한글 번역 -->' placeholder 를 클로드가 한 편씩 읽고 한국어 전문번역으로 교체.
(번역 품질↑ + 별도 API 비용 없음. 번역은 채점 대상 아니라 모델 자유.)

정답지 무결성: 파이프라인 추출 결과(builds_on/defines)를 워크시트에 절대 넣지 않는다
(독립 라벨링 보장). 번역과 라벨링(대화)은 섞지 않는다 — 이 스크립트는 빈 워크시트까지.

실행: uv run python scripts/make_goldset_worksheets.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TODO_KO = "<!-- TODO: 한글 번역 (클로드가 채움) -->"

OUT = ROOT / "eval" / "goldset" / "translations"
OUT.mkdir(parents=True, exist_ok=True)
roster = json.loads((ROOT / "eval" / "goldset" / "papers.json").read_text())
IDS = roster["new_collected"] + roster["from_corpus"]

RUBRIC = (
    "> **라벨링 규칙(잠정 — 라벨링 시작 때 relate 프롬프트와 대조해 확정)**\n"
    "> 이 논문이 **명시적으로 딛고·확장·기반으로 삼은 named 선행 기법**만 적는다.\n"
    "> - 포함: 확장/개선/기반으로 삼은 기존 방법·모델·프레임워크(예: RAG, DPR, ReAct).\n"
    "> - 제외: 평가용 데이터셋·벤치마크(방법적으로 딛은 게 아니면), 너무 일반적인 개념(LLM, Transformer 등).\n"
    "> - **abstract+intro에 근거한 것만** — 전문 지식으로 추가하지 말 것(파이프라인과 같은 입력으로 공정 비교).\n"
)

def main():
    for i, pid in enumerate(IDS, 1):
        parsed = json.loads((ROOT / "data" / "outputs" / f"{pid}.parsed.json").read_text())
        con = json.loads((ROOT / "data" / "outputs" / f"{pid}.concepts.json").read_text())
        title = con.get("title", pid)
        en = parsed["text"]
        md = (
            f"# {title}\n\n"
            f"https://arxiv.org/abs/{pid}  ·  `{pid}`\n\n"
            f"{RUBRIC}\n"
            f"## 원문 (abstract + intro)\n\n{en}\n\n"
            f"## 한글 번역\n\n{TODO_KO}\n\n"
            f"---\n\n"
            f"## 진짜 builds_on (직접 작성)\n\n- \n\n"
            f"## 메모 (판단 근거 · 선택)\n\n"
        )
        (OUT / f"{pid}.md").write_text(md, encoding="utf-8")
        print(f"[{i}/{len(IDS)}] {pid}  {title[:50]}  (EN {len(en)}자)", flush=True)
    print(f"\n완료(스켈레톤): {OUT} 에 {len(IDS)}개 — 번역 placeholder 대기")


if __name__ == "__main__":
    main()
