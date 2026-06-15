"""프롬프트 단일 패키지 — 모든 LLM 프롬프트를 여기 모은다.

  pipeline.py  추출 파이프라인(extract/relate) + paper_type 분류 기준
  collect.py   수집 에이전트(agent_collect): 관문/의도/상태보고/검색어확장
  filter.py    필터 에이전트(agent_filter): 명령→tool 라우팅 시스템 프롬프트

영문/한글 프롬프트 본문은 동작 불변 — 한 글자도 바꾸지 않는다(번역은 주석으로만).
"""
