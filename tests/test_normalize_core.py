"""normalize_core 의 표기 정규화/해소 — lexicon 채점·정규화의 토대."""
from src import normalize_core as nc


def test_canon_lowercases_collapses_and_hyphen_to_space():
    assert nc.canon("Self-RAG") == "self rag"
    assert nc.canon("Chain-of-Thought") == "chain of thought"
    assert nc.canon("  GraphRAG  ") == "graphrag"
    assert nc.canon("DENSE   passage") == "dense passage"


def _state(reps, aliases=None):
    """최소 lex_state 구성: reps={label:status}, aliases={alias:rep_label}."""
    st = {"lex": {}, "alias2rep": {}, "rep_meta": {}, "new": {}}
    for label, status in reps.items():
        rk = nc.canon(label)
        st["rep_meta"][rk] = {"label": label, "status": status}
        st["alias2rep"][rk] = rk
    for alias, rep in (aliases or {}).items():
        st["alias2rep"][nc.canon(alias)] = nc.canon(rep)
    return st


def test_resolve_alias_maps_to_representative_label():
    st = _state({"Retrieval-Augmented Generation": "approved"},
                {"RAG": "Retrieval-Augmented Generation"})
    rk, label = nc.resolve(st, "RAG")
    assert label == "Retrieval-Augmented Generation"
    assert rk == nc.canon("Retrieval-Augmented Generation")


def test_resolve_paren_acronym_fallback():
    # 직접 매칭 실패 시 "... (RAG)" 의 괄호 약어로 기존 대표개념에 연결.
    st = _state({"Retrieval-Augmented Generation": "approved"},
                {"RAG": "Retrieval-Augmented Generation"})
    rk, label = nc.resolve(st, "Some Long Phrase (RAG)")
    assert label == "Retrieval-Augmented Generation"


def test_resolve_unknown_returns_canon_key_and_original_name():
    st = _state({})
    rk, label = nc.resolve(st, "BrandNewMethod")
    assert rk == "brandnewmethod"
    assert label == "BrandNewMethod"
