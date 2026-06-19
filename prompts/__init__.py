"""프롬프트 단일 패키지 — 목적(에이전트)별 하위 디렉토리 + 한 프롬프트당 한 파일.

  paper_type_criteria.py   paper_type 분류 기준(extract·gate 공유 조각, 최상위)
  pipeline/                ① 추출 파이프라인     extract / relate          (영어)
  collect/                 ② 수집 에이전트       gate / intent / report / expand
  filter/                  ③ 필터 에이전트       command (명령→tool 라우팅)

각 프롬프트 위에 5줄 메타 + [한글 번역] 주석. extract 영문은 동작 불변(byte-동일);
relate는 lineage-only로 전환(점수비교 baseline 제외 + 입력 필드 축소: problem/domain 제거).
프롬프트→에이전트→적용 위치 지도는 README.md 참고.
"""
