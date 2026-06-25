"""score_buildson 의 P/R 채점 — "측정으로 결정" 서사의 측정기 자체. 회귀 방지.
eval/ 는 패키지가 아니므로 파일 경로로 로드한다."""
import importlib.util
from pathlib import Path

from src import normalize_core as nc

_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("score_buildson", _ROOT / "eval/score_buildson.py")
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)


def test_aggregate_micro_and_macro_pr():
    rows = [
        {"TP": ["a", "b"], "FP": ["c"], "FN": [], "fn_diag": {}},                 # p=2/3, r=1
        {"TP": ["d"], "FP": [], "FN": ["e"], "fn_diag": {"e": sb.FN_NOT_EXTRACTED}},  # p=1, r=1/2
    ]
    agg = sb.aggregate(rows)
    assert (agg["sumTP"], agg["sumFP"], agg["sumFN"]) == (3, 1, 1)
    assert agg["micro_p"] == 3 / 4      # 3 / (3+1)
    assert agg["micro_r"] == 3 / 4      # 3 / (3+1)
    assert abs(agg["macro_p"] - (2 / 3 + 1) / 2) < 1e-9
    assert abs(agg["macro_r"] - (1 + 1 / 2) / 2) < 1e-9
    assert agg["fn_not_extracted"] == 1
    assert agg["n_papers"] == 2


def test_aggregate_handles_empty_pred_and_gold_denominators():
    rows = [{"TP": [], "FP": [], "FN": [], "fn_diag": {}}]  # pred=∅, gold=∅
    agg = sb.aggregate(rows)
    assert agg["micro_p"] is None and agg["micro_r"] is None
    assert agg["macro_p"] is None and agg["macro_r"] is None


def _state(reps):
    st = {"lex": {}, "alias2rep": {}, "rep_meta": {}, "new": {}}
    for label, status in reps.items():
        rk = nc.canon(label)
        st["rep_meta"][rk] = {"label": label, "status": status}
        st["alias2rep"][rk] = rk
    return st


def test_score_paper_filters_non_node_status_from_predictions():
    # RAG/DPR 는 노드(approved), FooPending 은 pending → 예측에서 탈락(FP 아님).
    st = _state({"RAG": "approved", "DPR": "approved", "FooPending": "pending"})
    res = sb.score_paper(st, "p1", gold_names=["RAG", "DPR"],
                         pred_names=["RAG", "FooPending"])
    assert res["TP"] == ["rag"]
    assert res["FP"] == []                       # FooPending 은 status 필터로 빠져 FP 아님
    assert res["FN"] == ["dpr"]                   # gold인데 예측 못함
    assert "foopending" in res["pred_raw"]        # raw 에는 남아 진단 가능
    assert res["fn_diag"]["dpr"] == sb.FN_NOT_EXTRACTED
