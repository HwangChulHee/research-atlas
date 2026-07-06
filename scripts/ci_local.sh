#!/usr/bin/env bash
#
# ci_local.sh — push 전에 로컬에서 도는 CI.
# 예전 .github/workflows/ci.yml(GitHub Actions)의 검사를 그대로 재현한다.
#   backend : uv sync → uv run ruff check . → uv run pytest
#   frontend: frontend/에서 npm ci → npm run lint → npm run build
#
# 어느 단계든 실패하면 즉시 non-zero로 종료(set -e). 어디서 호출해도
# 레포 루트 기준으로 동작한다. npm 미설치 환경이나 SKIP_FRONTEND=1이면
# frontend 단계는 경고 후 스킵(하드 실패 아님).
set -euo pipefail

# 이 스크립트 위치(scripts/) 기준으로 레포 루트를 잡는다 → cwd 무관.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log() { printf '\n>>> %s\n' "$*"; }

cd "${REPO_ROOT}"

# PYTHONPATH 중화 — GitHub 클린 러너와 달리 로컬 셸엔 ROS(jazzy) 등이 PYTHONPATH를
# 주입해 pytest 수집이 외부 패키지(launch_testing 등)를 끌어와 깨진다(README "개발·테스트"
# 참고). editable 설치라 절대 import엔 PYTHONPATH가 불필요하므로 비워 hermetic하게 만든다.
export PYTHONPATH=""

# ── backend ────────────────────────────────────────────────────────────
log "[backend 1/3] uv sync (의존성 + editable 설치)"
uv sync

log "[backend 2/3] uv run ruff check . (린트)"
uv run ruff check .

log "[backend 3/3] uv run pytest (단위테스트)"
uv run pytest

# ── frontend ───────────────────────────────────────────────────────────
if [ "${SKIP_FRONTEND:-0}" = "1" ]; then
  log "[frontend] SKIP_FRONTEND=1 → 스킵"
elif ! command -v npm >/dev/null 2>&1; then
  log "[frontend] npm 미설치 → 스킵 (경고: 프론트 lint/build 검증 안 됨)"
else
  log "[frontend 1/3] npm ci (frontend/, 잠금 기반 설치)"
  ( cd "${REPO_ROOT}/frontend" && npm ci )

  log "[frontend 2/3] npm run lint (eslint, 경고도 실패)"
  ( cd "${REPO_ROOT}/frontend" && npm run lint )

  log "[frontend 3/3] npm run build (프로덕션 번들)"
  ( cd "${REPO_ROOT}/frontend" && npm run build )
fi

log "CI 통과 ✅"
