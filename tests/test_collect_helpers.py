"""agents.collect 의 순수 헬퍼 — 편수 산정·arXiv id 정규화·코사인 매칭."""
import numpy as np

from agents import collect


def test_extract_target_default_and_hard_cap():
    assert collect.extract_target({}) == collect.DEFAULT_EXTRACT          # 미언급 → 기본
    assert collect.extract_target({"count": None}) == collect.DEFAULT_EXTRACT
    assert collect.extract_target({"count": 0}) == collect.DEFAULT_EXTRACT  # 0 falsy → 기본
    assert collect.extract_target({"count": 5}) == 5
    assert collect.extract_target({"count": 999}) == collect.HARD_CAP      # 상한 적용


def test_norm_arxiv_id_strips_version_and_url():
    assert collect._norm_arxiv_id("http://arxiv.org/abs/2401.12345v2") == "2401.12345"
    assert collect._norm_arxiv_id("2401.12345v3") == "2401.12345"
    assert collect._norm_arxiv_id("2401.12345") == "2401.12345"
    assert collect._norm_arxiv_id("https://arxiv.org/abs/2401.12345/") == "2401.12345"
    assert collect._norm_arxiv_id("") == ""


def _unit(v):
    a = np.array(v, dtype=np.float32)
    return a / np.linalg.norm(a)


def test_match_cosine_orders_and_applies_floor():
    keys = ["a", "b", "c"]
    mat = np.array([_unit([1, 0]), _unit([0, 1]), _unit([0.6, 0.8])], dtype=np.float32)
    q = _unit([1, 0])
    res = collect.match(q, keys, mat, top=8, floor=0.30)
    # b(sim 0)는 floor 탈락, 나머지는 cosine 내림차순(a=1.0 > c=0.6)
    assert [k for k, _ in res] == ["a", "c"]
    assert res[0][1] > res[1][1]


def test_match_top_limit_and_none_matrix():
    keys = ["a", "b", "c"]
    mat = np.array([_unit([1, 0]), _unit([0, 1]), _unit([0.6, 0.8])], dtype=np.float32)
    q = _unit([1, 0])
    assert [k for k, _ in collect.match(q, keys, mat, top=1, floor=0.0)] == ["a"]
    assert collect.match(q, keys, None) == []
