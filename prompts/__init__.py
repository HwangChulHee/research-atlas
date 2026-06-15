"""프롬프트 단일 패키지 — 한 논리적 프롬프트당 한 파일.

  paper_type_criteria.py  paper_type 분류 기준(extract·gate 공유 조각)
  extract.py              추출: 논문 내용 필드            (영어)
  relate.py               관계: builds_on 계보 식별         (영어)
  gate.py                 관문: 초록만 보고 1차 판정        (영어, GATE_PROMPT_VER 포함)
  intent.py               의도 파싱: 수집 명령 구조화       (영어)
  report.py               현황 보고: 커버리지 종합         (영어 지시 / 한국어 출력)
  expand.py               검색어 확장: arXiv 검색어         (영어)
  command.py              필터: 명령→tool 라우팅           (영어 지시 / 한국어 트리거 유지)

각 프롬프트 위에 5줄 메타 + [한글 번역] 주석. extract/relate 영문은 동작 불변(byte-동일).
"""
