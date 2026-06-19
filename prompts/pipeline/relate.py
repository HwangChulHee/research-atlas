"""관계(relate) 프롬프트 — 논문이 방법적으로 딛고 선 선행 기법(builds_on)을 식별한다."""

# ── 관계(relate) 시스템 프롬프트 ──────────────────────
# [단계]   계보 추출 — 이 논문의 '방법'이 딛고/확장한 '명명된 선행 기법'(builds_on)
# [언제]   extract 후, 같은 논문 본문으로 LLM 1회
# [입력]   논문 본문 + (유저 프롬프트로) 이 논문의 defines/domain/problem
# [출력]   builds_on: 방법적 조상 이름 리스트(고유명사만, 없으면 빈 리스트)
# [의도]   개념→개념 '계보'의 원천. 점수비교 baseline·부품·데이터셋·툴·자기기법 제외해 노이즈 컷
#
# [한글 번역]
#   너는 한 연구 논문의 계보(LINEAGE)를 식별한다: 이 논문의 '방법'이 EXTEND/IMPROVE UPON/
#   BUILD ON 하는 '명명된 선행 기법/시스템'이 무엇인지 — 즉 이 논문이 방법적으로 그로부터
#   내려왔거나 그것을 진전시킨 선행 기법.
#   `builds_on` 출력: 이 논문이 방법적으로 딛고·확장한 선행 기법들의 이름.
#   - 포함: 명명된 선행 기법/시스템(고유명사)으로, 이 논문의 '방법이' 그 위에 서거나 그것을
#     발전시킨 것: "RAG", "GraphRAG", "DPR", "HippoRAG".
#   - 제외(중요): 이 논문이 '단지 성능을 비교한' baseline(예: 단순히 점수에서 능가한
#     범용 모델 "GPT-4", "DeepSeek-R1"). 방법적 후예가 아니라 비교 대상일 뿐이면 제외.
#   - 제외: 부품으로 사용한 알고리즘("PPO", "GRPO", "MCTS"), 일반 표현("flat
#     representations", "chunking"), 데이터셋("HotpotQA"), 온톨로지/툴("UMLS", "Neo4J"),
#     그리고 이 논문이 스스로 정의한 기법.
#   - 이름만. 없으면 빈 리스트.
#
#   핵심 판정: "이 논문의 방법이 X에서 내려왔거나 X를 진전시켰나(포함) vs 단지 X보다
#   점수가 높거나 X를 부품으로 썼나(제외)."
#   참고: 도메인 응용(예: GraphRAG를 의료에 적용)도 그 방법을 적응/확장하면 builds_on에 해당.
#   도메인은 별도로 추적하며 여기서 다루지 않는다.
# ──────────────────────────────────────────────────────
RELATE_SYSTEM = """You identify the LINEAGE of a research paper: which NAMED prior
techniques or systems this paper's METHOD EXTENDS, IMPROVES UPON, or BUILDS ON —
that is, prior techniques this paper methodologically descends from or advances.

Output `builds_on`: names of prior techniques this paper's method builds on.
- INCLUDE only NAMED prior techniques/systems (PROPER NOUNS) that this paper's
  METHOD descends from or advances: "RAG", "GraphRAG", "DPR", "HippoRAG".
- EXCLUDE baselines the paper merely COMPARES SCORES against without building on
  them methodologically (e.g. a general model like "GPT-4" or "DeepSeek-R1" that the
  paper only outperforms). Comparison alone is NOT builds_on.
- EXCLUDE algorithms used as components ("PPO", "GRPO", "MCTS"), generic phrases
  ("flat representations", "chunking"), datasets ("HotpotQA"), ontologies/tools
  ("UMLS", "Neo4J"), and the paper's OWN defined techniques.
- Names only. Empty list if none.

Decision test: "Does this paper's METHOD descend from or advance X (include),
or does it merely score higher than X / use X as a component (exclude)?"
Note: domain application (e.g. using GraphRAG in medicine) still counts as builds_on
if the paper adapts/extends the method. Domain is tracked separately, not here."""

# ── 관계(relate) 유저 프롬프트 ────────────────────────
# [단계]   계보 판단 맥락(자기 기법 defines) + 본문 전달
# [언제]   RELATE_SYSTEM과 함께 같은 호출에서
# [입력]   {defines} {text}   ← problem/domain 제거(아래 [의도])
# [출력]   없음(모델 입력) — builds_on JSON 출력 유도
# [의도]   defines로 자기 자신 배제. problem/domain은 extract 파생물이라 제거 —
#          단계 오류 전파 + problem 간섭(single-prompt 안티패턴) 차단, 본문만이 계보 근거(루브릭 ①)
#
# [한글 번역]
#   이 논문이 정의하는 것: {defines}
#
#   논문 텍스트:
#   ---
#   {text}
#   ---
#   `builds_on`(이 논문의 방법이 딛고·확장한 명명된 선행 기법)을 JSON으로 출력하라.
# ──────────────────────────────────────────────────────
RELATE_USER = """This paper defines: {defines}

Paper text:
---
{text}
---
Output `builds_on` (NAMED prior techniques this paper's method builds on) as JSON."""

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
