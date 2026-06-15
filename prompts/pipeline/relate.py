"""관계(relate) 프롬프트 — 논문이 딛고 선 선행 기법(builds_on)을 식별한다."""

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

