"""parse.find_cut — abstract+intro 만 남기고 본문/References 를 자르는 로직.
batch2 등에서 핵심이었던 절단 동작의 회귀 방지."""
from src import parse


def test_find_cut_stops_at_section2_heading_and_excludes_references():
    abstract = "Abstract\n"
    # MIN_INTRO_CHARS(3000) 를 넘기는 intro 본문(문장 끝 마침표 유지).
    intro = "This paper studies retrieval augmented generation in depth. " * 120
    body = ("\n2 Related Work\n"
            "Prior systems include DPR and BM25.\n\n"
            "References\n[1] Lewis et al. 2020. RAG.\n")
    text = abstract + intro + body

    cut, method = parse.find_cut(text)

    assert method == "section"
    assert "retrieval augmented generation" in cut   # intro 보존
    assert "Related Work" not in cut                  # 헤딩 직전에서 절단
    assert "References" not in cut                     # 참고문헌 제외
    assert "Lewis et al" not in cut


def test_find_cut_falls_back_to_boundary_when_no_section_heading():
    # 섹션 헤딩도 'abstract' 헤딩도 없으면 fallback(문장 경계 절단).
    text = "Some plain narrative text that never declares sections. " * 40
    cut, method = parse.find_cut(text)
    assert method == "head6000"
    assert cut  # 비어있지 않게 일부 반환
