# related work 추출 — 파싱 품질 검증 (추출 전용)

relate가 다음 단계에서 related work 섹션을 읽게 하기 위한 전제 작업. goldset 50편 PDF에서 related work/background 섹션을 **verbatim 추출**하고, 워커-무관한 **객관 신호 4개를 코드로 계산**해 trusted/suspect/no_section을 판정했다. 점수(P/R) 없음 — 이 통과율이 다음 단계 진행 여부를 정한다.

설계: 워커(서브에이전트 5명×10편)는 섹션 오프셋만 고르고 슬라이싱은 코드가 수행 → verbatim이 구조적으로 보장. 메인이 4개 신호를 독립 재계산해 검증.

신호: **verbatim_match**(공백정규화 후 원문 substring — 환각 닻), **char_count**(정상 400~8000), **citation_density**(per 1000자, 충분≥3.0), **heading_found**(직전/앞부분에 related-work류 헤딩).

## 1. 요약

- **trusted 46** / **suspect 2** / **no_section 2** (합 50).
- 게이트: trusted 전부 verbatim_match=true (환각 0) ✅.
- trusted 그룹 분해: new_collected 18 / from_corpus 28.

## 2. 분포 (이상치)

| 지표 | min | p25 | p50 | p75 | max |
|---|--:|--:|--:|--:|--:|
| char_count | 1416 | 2760 | 3788 | 4601 | 7901 |
| citation_density | 0.0 | 1.15 | 2.12 | 4.35 | 8.7 |

> char<400 또는 >8000, 또는 heading 없음+인용밀도<3.0 이면 suspect로 플래그.

## 3. suspect 목록 (사람 검토)

| id | 제목 | 그룹 | char | 인용밀도 | heading | verbatim | 깨진 신호 |
|---|---|---|--:|--:|:--:|:--:|---|
| 2501.12948 | DeepSeek-R1 | new_collected | 5203 | 1.15 | X | O | heading 없음 + 인용밀도 1.15<3.0(엉뚱 섹션 의심) |
| 2002.08909 | REALM | from_corpus | 2510 | 1.2 | X | O | heading 없음 + 인용밀도 1.2<3.0(엉뚱 섹션 의심) |

**메인 검토(Opus) — 두 건 모두 실제 related work가 맞다. heading 정규식의 위음성(false-negative)으로 플래그됨:**
- **DeepSeek-R1** — 본문엔 related work가 없고 부록 `H. Related Work`(H.1~H.3)가 유일. 헤딩이 *글자번호*("H.")라 `^(숫자)?related work` 정규식이 못 잡음. verbatim=true, 내용은 진짜 RW(인용밀도 낮은 건 부록이 서술형이라).
- **REALM** — 섹션 `5. Discussion and Related Work`(토론+계보 결합). 키워드가 제목 *앞*이 아니라("Discussion and …") 정규식이 못 잡음. verbatim=true, 내용 진짜.

→ 둘 다 **사실상 trusted**(추출 정확, 다음 단계 사용 가능). 위음성은 헤딩 형식(부록 글자번호·결합 제목) 한계지 추출 실패가 아님. **유효 사용가능 48/50.**

> 참고: ColBERT(2004.12832)는 1차 추출에서 워커가 모델 섹션(섹션3 "COLBERT" — 번호가 별도 줄이라 헤딩 정규식이 놓침)까지 흘려 19984자였음. **메인이 11717→16543으로 재슬라이스**해 4826자·trusted로 정정.

## 4. no_section 목록 (related work 정말 없나)

워커가 '없음' 판단 + 헤딩도 안 잡힘 = 정당한 없음 후보. 메인이 후보 헤딩을 재확인.

| id | 제목 | 그룹 |
|---|---|---|
| 2502.13957 | RAG-Gym | new_collected |
| 2501.09136 | Agentic RAG Survey | new_collected |

**메인 검토(Opus) — 둘 다 정당한 없음 확정:**
- **RAG-Gym** — Nature식 구성(Intro→Results→Discussion→Materials and Methods). `related work`/`background` 헤딩이 본문 어디에도 없음(grep 0건). 계보는 intro에 녹음. 진짜 없음.
- **Agentic RAG Survey** — survey 논문이라 본문 전체가 문헌 리뷰. 유일한 `Background` 헤딩(`3 Core Principles and Background of Agentic Intelligence`)은 *자기 주제 정의*지 선행기법 리뷰 섹션이 아님. dedicated related-work 섹션 없음으로 판정. (추출 실패 아님 — 구조적으로 없는 것.)

## 5. trusted 목록 (참고)

| id | 제목 | 그룹 | char | 인용밀도 | heading |
|---|---|---|--:|--:|:--:|
| 2503.09516 | SEARCH-R1 | new_collected | 3454 | 5.5 | O |
| 2501.05366 | Search-o1 | new_collected | 2760 | 8.7 | O |
| 2505.17005 | R1-Searcher++ | new_collected | 4993 | 1.4 | O |
| 2504.03160 | DeepResearcher | new_collected | 5312 | 1.51 | O |
| 2503.19470 | ReSearch | new_collected | 2007 | 7.97 | O |
| 2502.01142 | DeepRAG | new_collected | 3136 | 1.28 | O |
| 2503.23513 | RARE | new_collected | 4394 | 7.06 | O |
| 2504.21776 | WebThinker | new_collected | 3218 | 6.53 | O |
| 2505.14146 | s3 | new_collected | 3332 | 1.2 | O |
| 2503.00223 | DeepRetrieval | new_collected | 7563 | 2.25 | O |
| 2504.20073 | RAGEN | new_collected | 1416 | 3.53 | O |
| 2504.14870 | OTC | new_collected | 2531 | 2.37 | O |
| 2509.25140 | ReasoningBank | new_collected | 3261 | 2.45 | O |
| 2509.26383 | KG-R1 | new_collected | 1558 | 3.85 | O |
| 2510.07794 | HiPRAG | new_collected | 3392 | 2.06 | O |
| 2510.20548 | GlobalRAG | new_collected | 2214 | 0.45 | O |
| 2510.27569 | MARAG-R1 | new_collected | 4791 | 1.46 | O |
| 2511.09109 | Bi-RAR | new_collected | 3788 | 1.32 | O |
| 2004.04906 | DPR | from_corpus | 3621 | 0.28 | O |
| 2004.12832 | ColBERT | from_corpus | 4826 | 4.77 | O |
| 2201.11903 | Chain-of-Thought | from_corpus | 1735 | 0.0 | O |
| 2203.11171 | Self-Consistency | from_corpus | 3686 | 2.44 | O |
| 2205.10625 | Least-to-Most | from_corpus | 6600 | 0.3 | O |
| 2210.03629 | ReAct | from_corpus | 4249 | 2.12 | O |
| 2301.12652 | REPLUG | from_corpus | 3997 | 0.5 | O |
| 2302.04761 | Toolformer | from_corpus | 5172 | 0.77 | O |
| 2303.11366 | Reflexion | from_corpus | 4542 | 3.96 | O |
| 2305.04091 | Plan-and-Solve | from_corpus | 3576 | 0.84 | O |
| 2305.14283 | Rewrite-Retrieve-Read | from_corpus | 5833 | 2.4 | O |
| 2305.16291 | Voyager | from_corpus | 4157 | 7.46 | O |
| 2308.00352 | MetaGPT | from_corpus | 4359 | 1.84 | O |
| 2310.04406 | LATS | from_corpus | 5235 | 2.87 | O |
| 2310.11511 | Self-RAG | from_corpus | 4007 | 1.0 | O |
| 2401.14887 | Power of Noise | from_corpus | 3967 | 6.05 | O |
| 2401.15884 | CRAG | from_corpus | 3517 | 0.57 | O |
| 2401.18059 | RAPTOR | from_corpus | 4199 | 0.71 | O |
| 2403.10131 | RAFT | from_corpus | 2416 | 1.24 | O |
| 2404.16130 | GraphRAG | from_corpus | 7901 | 0.51 | O |
| 2405.14831 | HippoRAG | from_corpus | 4601 | 4.35 | O |
| 2407.11005 | RAGBench | from_corpus | 2812 | 5.33 | O |
| 2408.04187 | MedGraphRAG | from_corpus | 1477 | 4.74 | O |
| 2406.17526 | LumberChunker | from_corpus | 1670 | 1.2 | O |
| 2410.05779 | LightRAG | from_corpus | 2706 | 0.0 | O |
| 2502.04413 | MedRAG | from_corpus | 4097 | 2.44 | O |
| 2502.14802 | From RAG to Memory (HippoRAG 2) | from_corpus | 4572 | 2.19 | O |
| 2503.21322 | HyperGraphRAG | from_corpus | 2418 | 4.96 | O |

## 6. 판정 / 다음 단계 의견

코드 신호 기준 **trusted 46/50 (92%)**, 메인 검토로 false-suspect 2건(DeepSeek-R1·REALM, 헤딩 형식 위음성)을 더하면 **유효 사용가능 48/50 (96%)**, 나머지 2건은 추출 실패가 아니라 **구조적 no_section**(RAG-Gym·Agentic RAG Survey). 즉 50편 전부가 "정확히 추출됐거나(48) 정당하게 related work가 없다(2)"로 깨끗이 갈렸고 — **환각·잘못 추출 0건**(verbatim_match 게이트 통과)이 닻이다. 분포(§2)를 보면 citation_density는 0~8.7로 넓게 퍼지는데, 낮은 값(DPR 0.28, CoT 0.0, LightRAG 0.0 등)은 추출 실패가 아니라 (a)저자-연도 인용을 pymupdf가 깨거나 (b)`[12]`식 번호인용을 안 쓰는 논문 탓이라 heading_found가 보완 통과시켰다 — 그래서 신호를 단독이 아니라 OR/AND로 조합한 게 맞았다. char_count는 1416~7901(ColBERT 정정 후)으로 정상 대역에 모였다. **판정: 이 통과율(48/50 사용가능, 환각 0)이면 다음 단계(relate가 related_work_text를 입력에 추가해 형제 계보를 잡게 하는 확장)로 가도 된다.** no_section 2편은 relate 입력에서 빈 값으로 두면 되고(없는 게 정상), DeepSeek-R1·REALM 같은 부록/결합형 헤딩은 이미 추출돼 있어 그대로 쓰면 된다. 다음 핸드오프에서 relate 입력 확장 시 이 50개 `eval/experiments/related_work/{id}.json`을 소스로 쓰면 된다.
