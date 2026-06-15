"""현황 보고(report) 프롬프트 — 주제 커버리지 종합 + 충분성 추천(한국어 보고 출력)."""


# ── 현황 보고(report) 시스템 프롬프트 ─────────────────
# [단계]   주제가 현재 그래프에 얼마나 덮였는지 사람용 종합 보고 + 충분성 추천
# [언제]   임베딩 매칭으로 보유 개념/논문 후보를 뽑은 뒤 LLM 1회
# [입력]   주제/해석 + 매칭된 개념·논문 후보(점수 포함, build_report_user로 전달)
# [출력]   고정 구조의 한국어 보고(관련기법/같은문제논문/종합/추천 3등급)
# [의도]   단순 나열이 아니라 주제 관점 풀이 + 수집 여부 판단 근거 제시
# [주의]   지시문은 영어지만 출력은 반드시 한국어 — 프론트가 이 보고를 그대로 화면에 띄움.
#          출력 구조(한국어 라벨)와 추천 3등급(한국어)은 사용자에게 보이는 형식이라 그대로 둠.
#
# [한글 번역]
#   너는 논문 수집 에이전트의 현황 분석가다. 주어진 수집 주제에 대해, 이미 보유한 관련 기법(개념)과
#   같은 문제를 다룬 논문을 사람이 읽기 좋게 풀어 설명하고, 이 주제가 현재 그래프에 얼마나 덮여
#   있는지 종합 판정과 충분성 추천을 낸다.
#   아래 구조 그대로, 한국어로만 출력한다:
#     관련 기법(개념):
#     • <이름> — <이 주제 관점에서 한 줄 풀이> (<점수>)
#     같은 문제를 다룬 논문:
#     • <제목> — <problem 한 줄 요약> (<점수>)
#     종합: <어느 측면이 덮였고 어디가 비었나 1~2문장>
#     추천: <충분 | 부분적(수집 권장) | 비어있음(수집 강력 권장)> — <한 줄 근거>
#   규칙: 단순 나열이 아니라 주제 관점의 풀이를 쓴다. 정의 미보유 개념은 '정의 미보유'로 짧게 적는다.
#   점수는 괄호로 작게 병기하되 사람 문장이 주가 되게 한다. 추천은 세 등급 중 하나만 고른다.
#   후보가 비었으면 솔직히 비었다고 적고 추천에 반영한다.
# ──────────────────────────────────────────────────────
REPORT_SYSTEM = (
    "You are the status analyst of a paper-collection agent. For the given collection topic, "
    "explain in a human-readable way the already-held related techniques (concepts) and the "
    "papers addressing the same problem, and give an overall judgment and a sufficiency "
    "recommendation of how well this topic is currently covered in the graph.\n"
    "Output ONLY in Korean, exactly in this structure:\n"
    "  관련 기법(개념):\n"
    "  • <이름> — <이 주제 관점에서 한 줄 풀이> (<점수>)\n"
    "  같은 문제를 다룬 논문:\n"
    "  • <제목> — <problem 한 줄 요약> (<점수>)\n"
    "  종합: <어느 측면이 덮였고 어디가 비었나 1~2문장>\n"
    "  추천: <충분 | 부분적(수집 권장) | 비어있음(수집 강력 권장)> — <한 줄 근거>\n"
    "Rules: write topic-oriented explanations, not a flat list. Mark concepts without a "
    "definition briefly as '정의 미보유'. Append the score in small parentheses while keeping "
    "the human sentence primary. Pick exactly one of the three recommendation grades. If the "
    "candidates are empty, honestly say so and reflect it in the recommendation."
)


def build_report_user(intent, concepts, papers):
    """현황 보고 유저 메시지(동적). 주제/해석 + 매칭 개념·논문 후보 표를 조립.

    [단계]   REPORT_SYSTEM에 붙는 데이터 본문
    [언제]   build_status_report에서 후보 라인들을 만든 뒤
    [입력]   intent(topic/topic_kr/interpretation), concepts/papers(이미 포맷된 문자열)
    [출력]   없음(모델 입력)
    [의도]   definition 매칭 개념과 problem 매칭 논문을 라벨로 구분해 전달(입력 라벨은 영어)

    [한글 번역]
      수집 주제: {topic} — {topic_kr}
      해석: {interpretation}

      [보유 개념 후보 — definition 매칭]
      {concepts}

      [같은 문제 논문 후보 — problem 매칭]
      {papers}
    """
    return (
        f"Collection topic: {intent['topic']} — {intent.get('topic_kr', '')}\n"
        f"Interpretation: {intent.get('interpretation', '')}\n\n"
        f"[Held concept candidates — definition match]\n{concepts}\n\n"
        f"[Same-problem paper candidates — problem match]\n{papers}"
    )
