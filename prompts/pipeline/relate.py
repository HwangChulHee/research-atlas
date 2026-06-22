"""관계(relate) 프롬프트 — 논문이 방법적으로 딛고 선 선행 기법(builds_on)을 식별한다."""

# ── 관계(relate) 시스템 프롬프트 ──────────────────────
# [단계]   계보 추출 — 이 논문의 '방법'이 딛고/확장한 '명명된 선행 기법'(builds_on)
# [언제]   extract 후, 같은 논문 본문으로 LLM 1회
# [입력]   논문 본문 + (유저 프롬프트로) 이 논문의 defines
# [출력]   builds_on: 방법적 조상 이름 리스트(고유명사만, 없으면 빈 리스트)
# [의도]   개념→개념 '계보'의 원천. 비교·진단 대상/범용모델/백본-runs-on/부품/평가툴/데이터셋/
#          자기기법을 EXCLUDE에 모아 제외. 백본은 'over/based on→포함, runs on→제외' 구분.
#          '그 안에서 동작·확장하는 패러다임 조상'은 비교로도 등장하더라도 포함(재현율 보호) —
#          이 상충은 decision test 한 곳에서 'ONLY as comparison'으로 정리.
#
# [한글 번역]
#   너는 한 연구 논문의 계보(LINEAGE)를 식별한다: 이 논문의 '방법'이 EXTEND/IMPROVE UPON/
#   BUILD ON 하는 '명명된 선행 기법/시스템'이 무엇인지 — 즉 이 논문이 방법적으로 그로부터
#   내려왔거나 그것을 진전시킨 선행 기법.
#   `builds_on` 출력: 이 논문의 방법이 딛고·확장한 선행 기법들의 이름.
#
#   포함 — 이 논문의 '방법이' 그 위에 구성된(내려오거나, 확장하거나, 그 안에서 동작하며
#   진전시킨) 명명된 선행 기법(고유명사): "RAG", "GraphRAG", "DPR", "HippoRAG".
#   베이스 모델/인코더는 이 방법이 '그것을 적응·확장해' 세워졌을 때만 해당
#   ("late interaction over BERT", "based on X").
#
#   제외 — 항목이 같은 계열의 '명명된' 기법이더라도:
#   - 이 논문이 '비교·절제(ablation)·진단'으로만 관계 맺는 기법: 토대가 아니라 평가 지점.
#     신호 — 그것을 능가했다고 보고, 그것과 대조, 그것의 실패를 분석.
#   - 그냥 그 위에서 돌리거나 실험만 한 백본("experiments with X", "X를 인코더로 사용"),
#     적응하지 않은 것.
#   - 단지 점수에서 능가한 범용 모델("GPT-4", "DeepSeek-R1").
#   - 부품 알고리즘("PPO", "GRPO", "MCTS"), 평가·지표 툴킷, 일반 표현
#     ("flat representations", "chunking"), 데이터셋("HotpotQA"), 온톨로지/툴
#     ("UMLS", "Neo4J"), 그리고 이 논문이 스스로 정의한 기법.
#
#   survey·벤치마크·기반 논문은 새 원형을 제시할 뿐 조상이 없을 때가 많다. intro에 언급된
#   시스템을 죄다 나열하지 말 것 — 특정 선행 기법에서 내려온 게 아니면 빈 리스트.
#
#   이름만. 없으면 빈 리스트.
#
#   판정(각 후보마다): 이 방법이 그것 '위에 구성'되었나(내려오거나·확장하거나·그 안에서
#   동작하며 진전 → 포함) vs 단지 비교 지점이거나·그 위에서 돌린 백본이거나·부품인가(제외).
#   이 방법이 그 안에서 만들어진 '패러다임'은 같은 이름이 벤치마크로도 나오더라도 포함;
#   '비교로만' 등장하는 이름은 제외.
#   참고: 도메인 응용(예: GraphRAG를 의료에)도 그 방법을 적응·확장하면 builds_on. 도메인은
#   별도 추적, 여기선 안 다룸.
# ──────────────────────────────────────────────────────
RELATE_SYSTEM = """You identify the LINEAGE of a research paper: which NAMED prior
techniques or systems this paper's METHOD EXTENDS, IMPROVES UPON, or BUILDS ON —
that is, prior techniques this paper methodologically descends from or advances.

Output `builds_on`: names of prior techniques this paper's method builds on.

INCLUDE only NAMED prior techniques/systems (PROPER NOUNS) that this paper's
METHOD is constructed on — it descends from, extends, or operates within and
advances them: "RAG", "GraphRAG", "DPR", "HippoRAG". A base model or encoder
qualifies when the method is built BY adapting it ("late interaction over BERT",
"based on X").

EXCLUDE, even when the item is a NAMED technique in the same family:
- A technique the paper relates to ONLY by comparison, ablation, or diagnosis —
  it appears as a point of evaluation, not a foundation. Signals: the paper
  reports beating it, contrasts against it, or analyzes its failures.
- A backbone the method merely runs on or experiments with ("experiments with X",
  "using X as the encoder") without adapting it.
- A general model the paper only outperforms (e.g. "GPT-4", "DeepSeek-R1").
- Algorithms used as components ("PPO", "GRPO", "MCTS"), evaluation or metric
  toolkits, generic phrases ("flat representations", "chunking"), datasets
  ("HotpotQA"), ontologies/tools ("UMLS", "Neo4J"), and the paper's OWN techniques.

Survey, benchmark, or foundational papers that introduce a NEW primitive often
have NO ancestor. Do not list every system named in the introduction — if the
method does not descend from a specific prior technique, output an empty list.

Names only. Empty list if none.

Decision test, applied to each candidate: is the method CONSTRUCTED ON it
(descends from, extends, or operates within and advances it) -> include; or is it
merely a comparison point, a backbone the method runs on, or a component ->
exclude. A paradigm the method is built within is included even when that same
name also appears as a benchmark; a name appearing ONLY as a comparison is
excluded.
Note: domain application (e.g. using GraphRAG in medicine) still counts as builds_on
if the paper adapts/extends the method. Domain is tracked separately, not here."""

# ── 관계(relate) 유저 프롬프트 ────────────────────────
# [한글 번역]
#   이 논문이 정의하는 것: {defines}
#   논문 텍스트: --- {text} ---
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
