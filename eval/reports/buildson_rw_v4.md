# builds_on — relate RW 확장(v4) vs v2 (한 변수: RW 입력 추가)

v2 시스템 규칙은 그대로 두고, **유저 프롬프트에 라벨된 related work 블록만 추가**해 재추출. 같은 모델(`gpt-5.4-mini`)·lexicon(버킷1)·goldset·채점규칙. 변수는 RW 입력 하나. 진짜 질문: baseline 빽빽한 RW를 먹였을 때 v2의 '비교/진단 대상 제외' 규칙이 버티나 = 재현율 회복 대비 정밀도 하락폭.

분할(데이터 확정): **RW붙임 38편**(gold≠[] AND rw∈trusted/suspect) / **v2복사 12편**(gold=[] survey/benchmark OR no_section — RW 먹이면 FP만 늘 위험, v2 byte-복사하되 채점엔 포함). copy 12편은 v2와 동일 → RW 효과는 38편에 집중.

> 게이트: v2 전체 §6 재현 ✅, copy 12편 byte+점수 동일 ✅, RW38 재현율 단조 ✅.

## 1. 점수표 (v2 → v4, 3세트)

### 전체(50)

| | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| v2 | 0.616 | 0.750 | 0.722 | 0.803 | 45 | 28 | 15 |
| v4 | 0.495 | 0.767 | 0.585 | 0.792 | 46 | 47 | 14 |
| Δ | −0.122 | +0.017 | −0.136 | −0.011 | +1 | +19 | -1 |

### RW붙인(38)

| | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| v2 | 0.786 | 0.746 | 0.858 | 0.798 | 44 | 12 | 15 |
| v4 | 0.592 | 0.763 | 0.688 | 0.787 | 45 | 31 | 14 |
| Δ | −0.194 | +0.017 | −0.171 | −0.011 | +1 | +19 | -1 |

### v2복사(12)

| | micro P | micro R | macro P | macro R | ΣTP | ΣFP | ΣFN |
|---|--:|--:|--:|--:|--:|--:|--:|
| v2 | 0.059 | 1.000 | 0.125 | 1.000 | 1 | 16 | 0 |
| v4 | 0.059 | 1.000 | 0.125 | 1.000 | 1 | 16 | 0 |
| Δ | +0.000 | +0.000 | +0.000 | +0.000 | +0 | +0 | +0 |

> v2복사(12)는 Δ 전부 0이어야 정상(복사 정합성).

## 2. 그룹 분리 (RW붙인 38편 안)

| 그룹 | v2 microP | v4 microP | ΔP | v2 microR | v4 microR | ΔR |
|---|--:|--:|--:|--:|--:|--:|
| RW·new_collected (16) | 0.724 | 0.564 | −0.160 | 0.656 | 0.688 | +0.031 |
| RW·from_corpus (22) | 0.852 | 0.622 | −0.230 | 0.852 | 0.852 | +0.000 |

## 3. 재현율 회복 (RW로 형제 계보를 봄 → FN→TP)

회복 5건 (그 중 직전 not_extracted였던 것 5건 — RW 추가의 직접 효과).

- **CoT** — DeepSeek-R1 (2501.12948, new_collected) [이전 not_extracted]
- **RAG** — DeepResearcher (2504.03160, new_collected) [이전 not_extracted]
- **SEARCH-R1** — s3 (2505.14146, new_collected) [이전 not_extracted]
- **RAG** — GlobalRAG (2510.20548, new_collected) [이전 not_extracted]
- **RAG** — RAPTOR (2401.18059, from_corpus) [이전 not_extracted]

## 4. ★ 정밀도 하락 — RW에서 새로 빨려든 FP (핵심)

v2 exclude 규칙을 뚫고 들어온 항목 **22건**. 종류·RW 신호(char/인용밀도)와 함께 — 길고 빽빽한 RW에 FP가 몰리는지 본다.

| 논문 | id | 그룹 | name | FP종류 | RW char | RW 인용밀도 |
|---|---|---|---|---|--:|--:|
| Rewrite-Retrieve-Read | 2305.14283 | from_corpus | ReAct | method_misjudged | 5833 | 2.4 |
| Rewrite-Retrieve-Read | 2305.14283 | from_corpus | REPLUG | method_misjudged | 5833 | 2.4 |
| LATS | 2310.04406 | from_corpus | Reflexion | method_misjudged | 5235 | 2.87 |
| LATS | 2310.04406 | from_corpus | Self-Refine | method_misjudged | 5235 | 2.87 |
| R1-Searcher++ | 2505.17005 | new_collected | DeepSeek-R1 | method_misjudged | 4993 | 1.4 |
| MARAG-R1 | 2510.27569 | new_collected | HippoRAG | method_misjudged | 4791 | 1.46 |
| MARAG-R1 | 2510.27569 | new_collected | ReAct | method_misjudged | 4791 | 1.46 |
| HippoRAG | 2405.14831 | from_corpus | Personalized PageRank | method_misjudged | 4601 | 4.35 |
| Reflexion | 2303.11366 | from_corpus | Self-Refine | method_misjudged | 4542 | 3.96 |
| ReAct | 2210.03629 | from_corpus | SayCan | method_misjudged | 4249 | 2.12 |
| RAPTOR | 2401.18059 | from_corpus | REALM | method_misjudged | 4199 | 0.71 |
| Self-RAG | 2310.11511 | from_corpus | RLHF | method_misjudged | 4007 | 1.0 |
| Bi-RAR | 2511.09109 | new_collected | IRCoT | method_misjudged | 3788 | 1.32 |
| Bi-RAR | 2511.09109 | new_collected | Search-o1 | method_misjudged | 3788 | 1.32 |
| Plan-and-Solve | 2305.04091 | from_corpus | Zero-shot-Program-of-Thought Prompting | method_misjudged | 3576 | 0.84 |
| SEARCH-R1 | 2503.09516 | new_collected | IRCoT | method_misjudged | 3454 | 5.5 |
| SEARCH-R1 | 2503.09516 | new_collected | ReAct | method_misjudged | 3454 | 5.5 |
| SEARCH-R1 | 2503.09516 | new_collected | Toolformer | method_misjudged | 3454 | 5.5 |
| HiPRAG | 2510.07794 | new_collected | DeepRAG | method_misjudged | 3392 | 2.06 |
| HiPRAG | 2510.07794 | new_collected | ReAct | method_misjudged | 3392 | 2.06 |
| DeepRAG | 2502.01142 | new_collected | Self-RAG | method_misjudged | 3136 | 1.28 |
| LumberChunker | 2406.17526 | from_corpus | HyDE | method_misjudged | 1670 | 1.2 |

종류 분해: method_misjudged 22.

## 5. 해석

전체50 micro P 0.616→0.495 (−0.122), R 0.750→0.767 (+0.017). 효과가 집중된 RW38: P 0.786→0.592 (−0.194), R 0.746→0.763 (+0.017). 재현율 회복 5건(not_extracted→TP) 대비 새 FP 22건이 정밀도 하락의 실체다. 새 FP의 종류 분포(method_misjudged 22)와 RW 신호 상관(§4)이 'v2 exclude 규칙이 RW에서 버텼는지'의 판정 재료 — method_misjudged가 많으면 비교-baseline을 계보로 오인한 것(규칙이 RW 밀집도에 밀림), component/substrate가 많으면 부품·백본 혼입이다. 채택(=RW를 라이브 relate에 넣을지)은 이 재현율 회복 vs 정밀도 하락 트레이드오프를 보고 사람이 정한다.
