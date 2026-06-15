"""검색어 확장(expand) 프롬프트 — 주제 한 줄을 arXiv 검색어 5-8개로 펼친다."""


# ── 검색어 확장(expand) 시스템 프롬프트 ───────────────
# [단계]   주제 한 줄 → arXiv 전문 검색어 5-8개로 확장
# [언제]   수집 승인 후 arXiv 검색 직전, LLM 1회
# [입력]   주제(+선택적으로 보유 개념/논문 이름들, build_expand_user로 전달)
# [출력]   expand_queries tool(영어 검색어 묶음)
# [의도]   동의어·인접/상하위 개념으로 검색 재현율↑, 단 주제 이탈·단순 반복은 금지
#
# [한글 번역]
#   너는 arXiv 검색어 확장기다. 주어진 연구 주제를 arXiv 전문 검색에 쓸 영어 검색어 5-8개로
#   펼친다. 동의어·인접 표현·상위/하위 개념을 포함하되 주제에서 벗어나지 않게 한다.
#   단순 반복은 금지. expand_queries로 보고한다.
# ──────────────────────────────────────────────────────
EXPAND_SYSTEM = (
    "You are an arXiv query expander. Expand the given research topic into 5-8 English search "
    "queries for arXiv full-text search. Include synonyms, adjacent expressions, and "
    "broader/narrower concepts, but do not stray from the topic. No trivial repetition. "
    "Report via expand_queries."
)


def build_expand_user(topic, related_terms=None):
    """검색어 확장 유저 메시지(동적). 주제 + (있으면) 보유 개념/논문 이름.

    [단계]   EXPAND_SYSTEM에 붙는 데이터 본문
    [언제]   expand_query 호출 시
    [입력]   topic(주제), related_terms(맵 밀착 검색어 재료, 선택)
    [출력]   없음(모델 입력)
    [의도]   보유 개념/논문 이름을 재료로 줘 검색어가 우리 맵에 밀착하게(입력 라벨은 영어)

    [한글 번역]
      주제: {topic}
      관련 보유 개념/논문(맵 밀착 검색어 재료): {related_terms 쉼표 결합}   ← related_terms 있을 때만
    """
    user = f"Topic: {topic}"
    if related_terms:
        user += "\nRelated held concepts/papers (material for map-tight queries): " + ", ".join(related_terms)
    return user
