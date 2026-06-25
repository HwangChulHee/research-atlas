"""필터 에이전트 1/3 — tool 스키마 + 스모크 테스트.

테스트 문장 5개를 LLM에 보내 의도한 tool call이 나오는지 검증한다.
이 스키마가 확정되면 api/(2/3)와 프론트(3/3)가 이걸 기준으로 만들어진다.
실행: uv run python -m agents.filter
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # prompts 패키지 — cwd 무관 import
from prompts.filter.command import build_system_prompt

load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # cwd 무관하게 루트 .env 명시
client = OpenAI()
MODEL = "gpt-5.4-mini"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "filter",
            "description": "그래프에서 조건에 맞는 노드만 강조하고 나머지는 흐리게 한다. 여러 조건은 AND로 결합된다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ptype": {
                        "type": "string",
                        "enum": ["technique", "benchmark", "analysis", "survey", "other"],
                        "description": "논문/노드 유형",
                    },
                    "domain": {
                        "type": "string",
                        "description": "적용 분야 (예: medical, general). 범용은 general",
                    },
                    "date_after": {
                        "type": "string",
                        "description": "YYYY-MM. 이 시점 이후 등장한 노드만 (예: '2024년 이후' -> '2024-01')",
                    },
                    "unreviewed_only": {
                        "type": "boolean",
                        "description": "'안 본 것만/내가 모르는 것/아직 안 익힌 것'이면 true — 검토함 표시한 개념 제외",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "focus_lineage",
            "description": "특정 노드의 계보(builds_on 조상/자손)만 보여준다. node는 반드시 시스템 프롬프트의 노드 목록에 있는 canonical 이름이어야 한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "노드 목록에 있는 canonical 이름 그대로"},
                    "direction": {
                        "type": "string",
                        "enum": ["ancestors", "descendants", "both"],
                        "description": "조상만/자손만/양쪽. 기본 both",
                    },
                },
                "required": ["node"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset",
            "description": "모든 필터를 해제하고 전체 그래프를 보여준다.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": (
                "사용자가 찾고 싶은 주제·아이디어·문제를 자유 문장으로 대충 묘사하면, "
                "의미(임베딩) 유사도로 지도에 *이미 있는* 개념·논문을 찾아 강조한다. "
                "정확한 노드 이름을 모를 때 쓴다. 예: '검색증강하면서 추론하는 방법 있어?', "
                "'~비슷한 논문 찾아줘', '이런 주제 뭐 있지?'. "
                "arXiv에서 새로 가져오지 않는다(그건 collect)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "찾고 싶은 주제 묘사(원문 그대로)"},
                },
                "required": ["query"],
            },
        },
    },
]


def load_node_names():
    """개념 canonical 이름 — 읽기 단일 진입점(라이브=Neo4j / 오프라인=normalized_v2.json)."""
    from graphdb.read import concept_names
    return concept_names()


# 라우팅 스모크 (Type B). (입력, 기대 tool). 1·6은 절대 엉뚱한 데로 안 새는 하드 기준.
# collect 도구 제거됨(수집은 채팅 [수집] 탭에서) → #4 '모아줘'는 도구 없이 안내 메시지(tool=None).
SMOKE_CASES = [
    ("검색증강 생성하면서 추론하는 방법 있어?", "semantic_search"),  # 자유 묘사, 정확 노드명 없음
    ("RAG 계보 보여줘", "focus_lineage"),                          # 정확 노드 + '계보' 신호
    ("2024년 이후 medical 논문만", "filter"),                       # 연도+분야 구조 속성
    ("그 주제 논문 더 모아줘", None),                               # 수집 의도 → 도구 없이 [수집] 탭 안내
    ("전체 다시 보여줘", "reset"),                                  # 필터 해제
    ("RAG 관련 논문 찾아줘", "semantic_search"),                    # '찾아줘'=기존 중 찾기 (counter)
]


def route_one(system, q):
    """질의 1개 → 호출된 tool 이름(없으면 None)."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": q}],
        tools=TOOLS,
    )
    msg = resp.choices[0].message
    if msg.tool_calls:
        return msg.tool_calls[0].function.name
    return None


def main():
    names = load_node_names()
    system = build_system_prompt(names)
    print(f"노드 {len(names)}개 로드, 시스템 프롬프트 {len(system)}자\n")

    npass = 0
    for q, expect in SMOKE_CASES:
        got = route_one(system, q)
        ok = got == expect
        npass += ok
        print(f'[{"PASS" if ok else "FAIL"}] "{q}"\n        기대={expect}  실제={got}')
    print(f"\n스모크: {npass}/{len(SMOKE_CASES)} PASS", "✅" if npass == len(SMOKE_CASES) else "❌")
    sys.exit(0 if npass == len(SMOKE_CASES) else 1)


if __name__ == "__main__":
    main()
