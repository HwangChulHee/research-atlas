"""필터 에이전트(agent_filter) 프롬프트 — 자연어 명령을 화면 조작 tool call로 라우팅."""


def build_system_prompt(names):
    """명령→tool 라우팅 시스템 프롬프트(동적). 현재 노드 canonical 목록을 끼워 만든다.

    [단계]   자연어 화면 조작 명령 → tool call(filter/focus_lineage/reset/collect) 번역
    [언제]   /api/command 매 호출. names는 그래프의 현재 개념 canonical 목록
    [입력]   names(노드 canonical 이름 리스트)
    [출력]   없음(시스템 프롬프트 문자열)
    [의도]   목록에 없는 노드는 임의 대체 금지 — 환각 라우팅 차단
    [주의]   지시문은 영어지만, 사용자가 입력하는 한국어 트리거 단어(보여줘/가져와 등)와
             노드 미발견 시 사용자에게 돌려줄 한국어 문장('해당 노드를 찾지 못했다')은 그대로 둔다.

    [한글 번역]
      너는 논문 지식그래프 화면을 조작하는 에이전트다. 사용자의 한국어/영어 명령을 tool call로
      번역한다. 말로 답하지 말고 반드시 tool을 호출한다.
      보여줘/강조/필터/계보는 filter·focus_lineage·reset로, 가져와/수집/찾아와/모아줘(arXiv에서
      새 논문을 지도에 추가)는 collect로 보낸다.
      사용자가 노드를 지칭하면 아래 목록에서 가장 가까운 canonical 이름을 골라 그대로 쓴다. 단,
      목록에 명백히 대응하는 이름이 없으면(오타·무관한 단어) 절대 임의의 노드로 대체하지 말고
      tool을 호출하지 말고 '해당 노드를 찾지 못했다'고 한 문장으로 답한다.
      노드 목록: {names 쉼표 결합}
    """
    return (
        "You are an agent that manipulates a paper knowledge-graph screen. "
        "Translate the user's Korean/English command into a tool call. "
        "Do not answer in words — you must call a tool.\n"
        "Route 보여줘/강조/필터/계보 (show/highlight/filter/lineage) to filter·focus_lineage·reset, "
        "and 가져와/수집/찾아와/모아줘 (fetch/collect — adding new papers from arXiv to the map) to collect.\n"
        "When the user refers to a node, pick the closest canonical name from the list below and use "
        "it verbatim. But if there is clearly no matching name in the list (typo / unrelated word), "
        "never substitute an arbitrary node, do not call any tool, and reply with a single Korean "
        "sentence saying the node was not found ('해당 노드를 찾지 못했다').\n"
        f"Node list: {', '.join(names)}"
    )
