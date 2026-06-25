"""api 라우터 공유 — 경로 상수 · lexicon 입출력 · 파이프라인 subprocess 스텝."""
import json
import subprocess
import sys
from pathlib import Path

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LEX_PATH = DATA_DIR / "lexicon.json"
NORMALIZED_V2_PATH = DATA_DIR / "outputs" / "normalized_v2.json"  # v2 이중 노드 — 현재 소스
# 개인화 상태(검토함). 정본(추출+lexicon)과 분리 → 재빌드가 안 건드림(wipe 안 됨).
REVIEWED_PATH = DATA_DIR / "reviewed.json"


def load_lexicon() -> dict:
    """lexicon.json 전체(dict). techniques 키 하위에 개념들."""
    if not LEX_PATH.exists():
        raise HTTPException(500, f"lexicon.json 없음: {LEX_PATH}")
    return json.loads(LEX_PATH.read_text())


def save_lexicon(lex: dict) -> None:
    LEX_PATH.write_text(json.dumps(lex, ensure_ascii=False, indent=2))


def run_step(name: str, *args: str) -> str:
    """파이프라인 스텝을 subprocess로 실행. 실패 시 stdout/stderr 묶어 HTTP 500."""
    proc = subprocess.run([sys.executable, *args], cwd=str(ROOT),
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise HTTPException(500, f"{name} 실패:\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout
