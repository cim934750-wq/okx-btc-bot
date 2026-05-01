#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_NAME="okx-btc-bot"
SERVICE_SOURCE="$SCRIPT_DIR/$SERVICE_NAME.service"
SERVICE_TARGET="/etc/systemd/system/$SERVICE_NAME.service"
DEFAULT_PROJECT_DIR="/home/ubuntu/okx-btc-bot"

sed "s|$DEFAULT_PROJECT_DIR|$PROJECT_DIR|g" "$SERVICE_SOURCE" | sudo tee "$SERVICE_TARGET" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "Service installed and restarted."
echo "Project directory: $PROJECT_DIR"
echo
echo "Useful commands:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  journalctl -u $SERVICE_NAME -f"
