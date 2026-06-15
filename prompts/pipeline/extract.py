"""추출(extract) 프롬프트 — 논문 본문에서 내용 필드를 뽑는다."""
from prompts.paper_type_criteria import PAPER_TYPE_CRITERIA

# ── 추출(extract) 시스템 프롬프트 ─────────────────────
# [단계]   논문 내용 추출 — title/task/defines/uses/problem/domain/paper_type
# [언제]   parse 후, 논문 본문(제목+초록+서론)을 받아 LLM 1회
# [입력]   논문 텍스트(제목+초록+서론). 다른 논문과의 관계는 여기서 안 봄
# [출력]   구조화 JSON(EXTRACT_SCHEMA). defines는 보통 단 1개의 고유명사
# [의도]   "이 논문이 무엇을 정의/사용/대상하는가"만 뽑음 — 계보는 relate 단계
#
# [한글 번역]
#   너는 LLM/NLP/RAG/에이전트 논문의 내용(CONTENT)을 추출한다.
#   제목·초록·서론이 주어지면 아래 필드를 뽑는다. 여기서 다른 논문과의 관계는 판단하지 마라.
#   - title: 원문 그대로.
#   - task: 작업의 종류(들), 짧은 명사구. 리스트.
#   - defines: 이 논문이 정의하거나 대표되는 '주된 명명된 기법/시스템'만
#       (보통 하나, "LightRAG", "MedGraphRAG" 같은 고유명사). 각 항목 = {name, definition}.
#       definition = 한 문장. 하위 구성요소를 defines에 넣지 마라 — 그건 `uses`에.
#   - uses: 이 논문이 내부적으로 사용하는 기법/구성요소의 이름. 이름만.
#   - problem: 이 논문이 다루는 결함, 한 문장.
#   - domain: 이 논문이 겨냥한 응용 도메인, 한 개의 짧은 소문자 단어/구
#       (예: "medical", "legal", "finance", "code"). 범용이면 "general" 출력.
#   - paper_type: 이 논문이 어떤 종류인지. 정확히 다음 중 하나:
#   (여기에 PAPER_TYPE_CRITERIA 5개 유형 정의가 들어감)
#
#   예시 (MedGraphRAG — GraphRAG의 의료 응용):
#   { ... title/task/defines/uses/problem/domain 예시 ... }
# ──────────────────────────────────────────────────────
EXTRACT_SYSTEM = """You extract the CONTENT of an LLM/NLP/RAG/agent paper.
Given title, abstract, introduction, extract these fields. Do NOT judge relations to other papers here.

- title: verbatim.
- task: type(s) of work, short noun phrases. A list.
- defines: ONLY the main NAMED technique/system this paper defines or is known for
    (usually ONE, a proper noun like "LightRAG", "MedGraphRAG"). Each = {name, definition}.
    definition = ONE sentence. Do NOT list sub-components as defines — put those in `uses`.
- uses: names of techniques/components THIS paper uses internally. Names only.
- problem: the deficiency the paper addresses, ONE sentence.
- domain: the application domain this paper targets, as ONE short lowercase word/phrase
    (e.g. "medical", "legal", "finance", "code"). If general-purpose, output "general".
- paper_type: what KIND of paper this is. EXACTLY one of:
""" + PAPER_TYPE_CRITERIA + """

Example (MedGraphRAG — a medical application of GraphRAG):
{
  "title": "Medical Graph RAG: Towards Safe Medical LLM via Graph RAG",
  "task": ["medical question answering"],
  "defines": [{"name": "MedGraphRAG", "definition": "A graph-based RAG framework for the medical domain using triple graph construction and U-retrieval."}],
  "uses": ["triple graph construction", "U-retrieval"],
  "problem": "General RAG lacks the safety and evidence grounding needed for clinical use.",
  "domain": "medical"
}
"""

# ── 추출(extract) 유저 프롬프트 ───────────────────────
# [단계]   추출 시스템 프롬프트에 붙는 실제 논문 텍스트 전달
# [언제]   EXTRACT_SYSTEM과 함께 같은 호출에서
# [입력]   {text} = 제목+초록+서론
# [출력]   없음(모델 입력) — JSON으로 내용 필드 출력 유도
# [의도]   본문을 구분선으로 감싸 모델이 경계를 명확히 인식하게
#
# [한글 번역]
#   논문 텍스트 (제목 + 초록 + 서론):
#   ---
#   {text}
#   ---
#   내용 필드를 JSON으로 추출하라.
# ──────────────────────────────────────────────────────
EXTRACT_USER = """Paper text (title + abstract + introduction):
---
{text}
---
Extract the content fields as JSON."""

EXTRACT_SCHEMA = {
    "name": "paper_content",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "task": {"type": "array", "items": {"type": "string"}},
            "defines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "definition": {"type": "string"}},
                    "required": ["name", "definition"], "additionalProperties": False,
                },
            },
            "uses": {"type": "array", "items": {"type": "string"}},
            "problem": {"type": "string"},
            "domain": {"type": "string"},
            "paper_type": {"type": "string", "enum": ["technique","benchmark","analysis","survey","other"]},
        },
        "required": ["title", "task", "defines", "uses", "problem", "domain", "paper_type"],
        "additionalProperties": False,
    },
}

