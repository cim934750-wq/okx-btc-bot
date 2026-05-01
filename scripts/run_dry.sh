#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "Missing .venv. Create it with: python3 -m venv .venv"
  exit 1
fi

source .venv/bin/activate

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export DRY_RUN=1
export BOT_MODE=live_loop
python -m src.bot --live-loop --dry-run --okx-demo
