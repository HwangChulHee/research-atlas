"""필터 에이전트 1/3 — tool 스키마 + 스모크 테스트.

테스트 문장 5개를 LLM에 보내 의도한 tool call이 나오는지 검증한다.
이 스키마가 확정되면 api/(2/3)와 프론트(3/3)가 이걸 기준으로 만들어진다.
실행: uv run python agent_filter.py
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))  # prompts 패키지 — cwd 무관 import
from prompts.filter import build_system_prompt

load_dotenv(Path(__file__).resolve().parent / ".env")  # cwd 무관하게 루트 .env 명시
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
            "name": "collect",
            "description": "arXiv에서 특정 주제의 논문을 검색·수집해 지도에 추가하려는 요청. "
                           "'~논문 가져와/수집해/찾아와/모아줘' 류. 화면 조작(보여줘/강조)과 구분된다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_text": {"type": "string", "description": "수집 요청 원문(그대로)"},
                },
                "required": ["topic_text"],
            },
        },
    },
]


def load_node_names():
    d = json.loads(Path("data/outputs/normalized_v2.json").read_text())
    return sorted(v["canonical"] for v in d["nodes"].values() if v.get("type") == "concept")


SMOKE_QUERIES = [
    "벤치마크만 보여줘",                  # 기대: filter(ptype=benchmark)
    "RAG 계보만 보여줘",                  # 기대: focus_lineage(node=RAG계열 canonical)
    "2024년 이후 나온 것만",              # 기대: filter(date_after=2024-01)
    "medical 도메인 기법만",              # 기대: filter(ptype=technique, domain=medical)
    "다 보여줘",                          # 기대: reset()
]


def main():
    names = load_node_names()
    system = build_system_prompt(names)
    print(f"노드 {len(names)}개 로드, 시스템 프롬프트 {len(system)}자\n")

    for q in SMOKE_QUERIES:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": q}],
            tools=TOOLS,
        )
        msg = resp.choices[0].message
        if msg.tool_calls:
            for tc in msg.tool_calls:
                print(f'"{q}"\n  -> {tc.function.name}({tc.function.arguments})\n')
        else:
            print(f'"{q}"\n  -> [tool call 없음] {msg.content[:80]}\n')


if __name__ == "__main__":
    main()
