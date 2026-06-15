"""관문(gate) 프롬프트 — 초록만 보고 paper_type을 1차 판정(technique만 통과)."""
from prompts.paper_type_criteria import PAPER_TYPE_CRITERIA

# 관문 프롬프트 버전 — 바뀌면 재판정 판별용.
# v2: 프롬프트를 한국어→영어로 전환(gate-v1 캐시 무효화 → 재판정 유도).
GATE_PROMPT_VER = "gate-v2"


# ── 관문(gate) 시스템 프롬프트 ────────────────────────
# [단계]   수집 후보를 본맵에 넣을지 거르는 1차 판정(이진: technique만 통과)
# [언제]   arXiv 검색 결과의 각 논문 제목+초록을 받은 직후(PDF 없이)
# [입력]   논문 제목 + 초록 (GATE_USER로 전달)
# [출력]   paper_type 분류 + 사유(classify_paper tool)
# [의도]   초록만으로 싸게 노이즈 컷 — 정밀 판정/추출은 다음 단계
#
# [한글 번역]
#   너는 논문 관문 분류기다. 제목과 초록만 보고(PDF 없이) paper_type을 정확히 하나로 분류한다.
#   paper_type 기준 — 정확히 다음 중 하나:
#   (여기에 PAPER_TYPE_CRITERIA 5개 유형 정의가 들어감)
#   classify_paper로 보고한다.
# ──────────────────────────────────────────────────────
GATE_SYSTEM = (
    "You are a paper gate classifier. Looking only at the title and abstract (no PDF), "
    "classify the paper_type as EXACTLY one.\n"
    "paper_type criteria — EXACTLY one of:\n" + PAPER_TYPE_CRITERIA +
    "\nReport via classify_paper."
)

# ── 관문(gate) 유저 프롬프트 ──────────────────────────
# [단계]   관문 판정에 넣을 제목/초록 전달
# [언제]   GATE_SYSTEM과 함께 같은 호출에서
# [입력]   {title} {abstract}
# [출력]   없음(모델 입력)
# [의도]   제목·초록을 라벨로 구분해 모델이 둘을 구분 인식하게
#
# [한글 번역]
#   제목: {title}
#
#   초록: {abstract}
# ──────────────────────────────────────────────────────
GATE_USER = "Title: {title}\n\nAbstract: {abstract}"
