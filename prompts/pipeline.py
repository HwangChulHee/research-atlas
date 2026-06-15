"""파이프라인 프롬프트 모음 — extract(내용+domain) / relate(builds_on) + paper_type 기준."""

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

# ── 관계(relate) 시스템 프롬프트 ──────────────────────
# [단계]   계보 추출 — 이 논문이 딛고 선 '명명된 선행 기법'(builds_on)
# [언제]   extract 후, 같은 논문 본문으로 LLM 1회
# [입력]   논문 본문 + (유저 프롬프트로) 이 논문의 defines/domain/problem
# [출력]   builds_on: 선행 기법 이름 리스트(고유명사만, 없으면 빈 리스트)
# [의도]   개념→개념 계보의 원천. 데이터셋·툴·자기 기법은 제외해 노이즈 컷
#
# [한글 번역]
#   너는 한 연구 논문의 계보(LINEAGE)를 식별한다: 이 논문이 EXTEND/IMPROVE UPON 하거나
#   baseline으로 COMPARE AGAINST 하는 '명명된 선행 기법/시스템'이 무엇인지.
#   `builds_on` 출력: 이 논문이 넘어선 선행 기법들의 이름.
#   - 명명된 선행 기법/시스템(고유명사)만 포함: "RAG", "GraphRAG", "DPR", "HippoRAG".
#   - 일반 표현("flat representations", "chunking"), 데이터셋("HotpotQA"),
#     온톨로지/툴("UMLS", "Neo4J"), 그리고 이 논문이 스스로 정의한 기법은 제외.
#   - 이름만. 없으면 빈 리스트.
#
#   참고: 도메인 응용(예: GraphRAG를 의료에 적용)도 그 방법을 적응/확장하면 builds_on에 해당.
#   도메인은 별도로 추적하며 여기서 다루지 않는다.
# ──────────────────────────────────────────────────────
RELATE_SYSTEM = """You identify the LINEAGE of a research paper: which NAMED prior
techniques or systems this paper EXTENDS, IMPROVES UPON, or COMPARES AGAINST as a baseline.

Output `builds_on`: names of prior techniques this paper advances beyond.
- INCLUDE only NAMED prior techniques/systems (PROPER NOUNS): "RAG", "GraphRAG", "DPR", "HippoRAG".
- EXCLUDE generic phrases ("flat representations", "chunking"), datasets ("HotpotQA"),
  ontologies/tools ("UMLS", "Neo4J"), and the paper's OWN defined techniques.
- Names only. Empty list if none.

Note: domain application (e.g. using GraphRAG in medicine) still counts as builds_on
if the paper adapts/extends the method. Domain is tracked separately, not here."""

# ── 관계(relate) 유저 프롬프트 ────────────────────────
# [단계]   계보 판단에 필요한 맥락(이 논문의 defines/domain/problem) + 본문 전달
# [언제]   RELATE_SYSTEM과 함께 같은 호출에서
# [입력]   {defines} {domain} {problem} {text}
# [출력]   없음(모델 입력) — builds_on JSON 출력 유도
# [의도]   자기 기법(defines)을 미리 알려줘 builds_on에서 자기 자신을 빼게 도움
#
# [한글 번역]
#   이 논문이 정의하는 것: {defines}
#   이 논문의 도메인: {domain}
#   이 논문의 문제: {problem}
#
#   논문 텍스트:
#   ---
#   {text}
#   ---
#   `builds_on`(이 논문이 넘어선 명명된 선행 기법)을 JSON으로 출력하라.
# ──────────────────────────────────────────────────────
RELATE_USER = """This paper defines: {defines}
Its domain: {domain}
Its problem: {problem}

Paper text:
---
{text}
---
Output `builds_on` (NAMED prior techniques this paper advances beyond) as JSON."""

RELATE_SCHEMA = {
    "name": "paper_relations",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "builds_on": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["builds_on"],
        "additionalProperties": False,
    },
}
