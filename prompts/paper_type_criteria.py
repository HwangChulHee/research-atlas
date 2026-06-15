"""paper_type 분류 기준(공유 조각) — extract와 gate가 함께 참조하는 단일 출처."""

# ── paper_type 분류 기준 ──────────────────────────────
# [단계]   논문 유형(technique/benchmark/analysis/survey/other) 분류 기준 텍스트
# [언제]   extract(본문 추출)와 관문(gate, 초록만 보는 1차 판정)이 함께 참조
# [입력]   (조각) — 다른 프롬프트에 끼워 넣는 5개 유형 정의
# [출력]   없음(프롬프트 본문 일부) — 모델은 이 기준으로 paper_type 한 개 고름
# [의도]   유형 정의를 한 곳에 두어 extract·gate 판정 기준을 1:1로 일치시킴
#
# [한글 번역]
#   "technique"  - 새 방법/시스템을 제안한다 (대부분의 논문)
#   "benchmark"  - 평가용 벤치마크/프레임워크/지표를 제안한다
#   "analysis"   - 기존 방법을 연구/분석하고 발견을 보고, 새 방법은 없음
#   "survey"     - 한 분야를 리뷰/분류한다
#   "other"      - 위 어느 것도 아님
# ──────────────────────────────────────────────────────
PAPER_TYPE_CRITERIA = """\
    "technique"  - proposes a new method/system (most papers)
    "benchmark"  - proposes an evaluation benchmark/framework/metric
    "analysis"   - studies/analyzes existing methods, reports findings, no new method
    "survey"     - reviews/categorizes a field
    "other"      - none of the above"""

