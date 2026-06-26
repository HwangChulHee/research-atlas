"""경로 / 모델 상수 + 공용 OpenAI 클라이언트 팩토리."""
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# OpenAI 호출 견고성 — 모든 호출 지점이 make_openai_client()를 거친다.
# timeout 없으면 멈춘 요청이 동기 핸들러 스레드/배치를 무한 점유(서버 프리즈·배치 정지).
# max_retries는 SDK 내장 지수 백오프(429/5xx/연결오류/타임아웃) — 별도 backoff 루프 불필요.
OPENAI_TIMEOUT = 60.0
OPENAI_MAX_RETRIES = 3


def make_openai_client():
    """timeout·재시도가 박힌 공용 OpenAI 클라이언트."""
    return OpenAI(timeout=OPENAI_TIMEOUT, max_retries=OPENAI_MAX_RETRIES)

DATA_DIR = ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"          # PDF는 공용 (논문 겹쳐도 중복 다운 안 함)

OUT_DIR = DATA_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_EXTRACT = "gpt-5.4-mini"   # 검증된 구성: extract는 mini 유지(개념 집합 불변)
MODEL_RELATE  = "gpt-5.4"        # 승격: relate만 full (모델 비교 결론 — 정밀도 +0.20)
MODEL_COLLECT = "gpt-5.4-mini"   # 수집 에이전트(의도 파싱·게이트·검색어 확장)
MODEL_COMMAND = "gpt-5.4-mini"   # 명령·필터 에이전트(자연어→tool call)
# 임베딩 모델 — 벡터를 '만드는 쪽'(embed_nodes_v2)과 '질의하는 쪽'(graphdb.write·agents.collect)이
# 반드시 동일해야 함(다르면 공간 불일치로 검색이 조용히 깨짐). 이 한 곳이 단일 출처.
EMBED_MODEL   = "text-embedding-3-small"

# 범용+RAG+에이전트 논문
FULL_IDS = [
    "2203.02155", "2305.18290", "2212.08073",
    "2201.11903", "2203.11171", "2305.10601", "2210.03629",
    "2205.10625", "2303.17651",
    "1706.03762", "1810.04805", "2005.14165", "1910.10683", "2312.00752",
    "2001.08361", "2203.15556", "2206.07682", "2204.02311",
    "2302.13971", "2307.09288",
    "2302.04761", "2303.11366", "2305.16291", "2304.03442",
    "2005.11401", "2002.08909",
    "2106.09685", "2305.14314", "2205.14135",
    "2109.01652", "2212.10560",
    "2101.03961",
    "2004.04906", "2004.12832", "2212.10496", "2310.11511",
    "2305.06983", "2301.12652", "2401.15884", "2304.09542", "2312.10997",
    "2401.18059", "2409.04701", "2312.06648", "2406.17526", "2410.12788",
    "2004.05150", "2310.19923", "2305.14283",
    "2308.08155", "2308.00352", "2303.17580", "2310.04406", "2305.04091",
]

PAPER_IDS = FULL_IDS
