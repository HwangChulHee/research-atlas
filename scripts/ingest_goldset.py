"""정답지 신규 21편을 arXiv ID로 직접 적재(라이브 Neo4j 증분쓰기).

토픽검색·관문·interrupt 없이 extract_pipeline 을 ID마다 직접 호출한다
(큐레이션은 핸드오프 T1 에서 끝났으므로 관문 불필요).
fetch→parse→extract→relate→write_paper(Neo4j 증분) 한 편 전부를 extract_pipeline 이 수행.

실행: uv run python scripts/ingest_goldset.py   (Docker/Neo4j 기동 + ATLAS_OFFLINE 미설정 필수)
"""
import os
import sys
from collections import defaultdict

# 라이브 모드 확인: 오프라인이면 Neo4j 미반영 → 정답지 적재가 안 됨.
assert os.environ.get("ATLAS_OFFLINE") != "1", "라이브 모드로 실행할 것(Neo4j 반영)"

from backend.agents.collect import extract_pipeline  # noqa: E402

IDS = [  # T1(arXiv API 제목/초록 대조)에서 21/21 검증 통과
    "2501.12948", "2503.09516", "2501.05366", "2505.17005", "2504.03160", "2503.19470",
    "2502.01142", "2503.23513", "2504.21776", "2502.13957", "2505.14146", "2503.00223",
    "2501.09136", "2504.20073", "2504.14870", "2509.25140", "2509.26383", "2510.07794",
    "2510.20548", "2510.27569", "2511.09109",
]


def main():
    ledger = defaultdict(dict)  # extract_pipeline 이 ledger[aid]["extracted"]=True 만 씀
    results = []
    for aid in IDS:
        try:
            ok, msg, concepts = extract_pipeline(aid, ledger)
        except Exception as e:  # noqa: BLE001
            ok, msg, concepts = False, f"예외 {type(e).__name__}: {e}", None
        pt = (concepts or {}).get("paper_type", "?")
        ndef = len((concepts or {}).get("defines", []))
        print(f"{aid}  {'OK  ' if ok else 'FAIL'}  type={pt:10} defines={ndef:2}  {msg}", flush=True)
        results.append((aid, ok, pt, ndef, msg))

    nok = sum(1 for r in results if r[1])
    print(f"\n성공 {nok}/{len(IDS)}")
    if nok < len(IDS):
        print("실패:")
        for aid, ok, pt, ndef, msg in results:
            if not ok:
                print(f"  {aid}: {msg}")
    # paper_type 분포
    from collections import Counter
    dist = Counter(pt for _aid, ok, pt, _n, _m in results if ok)
    print("paper_type 분포:", dict(dist))
    zerodef = [aid for aid, ok, pt, ndef, _m in results if ok and ndef == 0]
    print("defines 0개 논문:", zerodef if zerodef else "없음")


if __name__ == "__main__":
    main()
