#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git tmux

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

mkdir -p logs data runtime

echo "Oracle Ubuntu setup complete."
echo "No web server was installed and no ports were opened."
