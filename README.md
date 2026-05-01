# OKX BTC-USDT Trading Bot Skeleton

Safe, modular Python skeleton for observing an OKX BTC/USDT strategy in demo and dry-run mode. This is not a profitability guarantee.

## Safety Defaults

- `DRY_RUN=1` by default; `execution.py` never calls `create_order()` while dry-run is active.
- `OKX_DEMO=1` by default and OKX simulated trading headers are enabled.
- API keys are loaded from `.env`; keys and secrets are never hardcoded.
- Missing API keys are allowed for market-data-only dry-run mode.
- Never enable withdrawal permission on OKX API keys.
- `KILL_SWITCH=1` blocks entries and real trading startup.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.bot
```

The default `BOT_MODE` is `live_loop`, so the bot runs continuously. For a single cycle:

```bash
BOT_MODE=once DRY_RUN=1 python -m src.bot
```

## Windows Dry-Run

Windows should use a separate virtual environment named `.venv-win`; do not reuse the macOS `.venv` from an external drive. See [WINDOWS_RUNBOOK.md](WINDOWS_RUNBOOK.md) for the full PowerShell setup and dry-run commands.

For a long Windows dry-run:

```powershell
.\scripts\run_dry_windows.ps1
```

The Windows runner forces `DRY_RUN=1`, `OKX_DEMO=1`, and `BOT_MODE=live_loop`.

## Cross-Platform Safety

- Do not run the bot from macOS and Windows at the same time on the same external drive.
- Do not unplug the external drive while the bot is running.
- Stop the bot before switching computers.
- Do not delete logs during a long dry-run.
- Do not remove `runtime/bot.lock` unless you are sure no bot process is running.

## Project Structure

```text
src/config.py
src/exchange.py
src/data.py
src/strategy.py
src/risk.py
src/execution.py
src/bot.py
research/backtest.py
scripts/setup_oracle_ubuntu.sh
scripts/run_dry.sh
scripts/run_dry_windows.ps1
deploy/okx-btc-bot.service
deploy/install_systemd_service.sh
WINDOWS_RUNBOOK.md
```

## Logs And State

- Paper state: `data/paper_state.json`
- Heartbeats: `logs/heartbeat.csv`
- Trade intents and simulated trades: `logs/trades.csv`

## Backtest

```bash
python research/backtest.py
```

The research backtest is intentionally basic and includes fee/slippage assumptions from `.env`.

## Oracle Cloud 24/7 dry-run deployment

Local:

```bash
git init
git add .
git commit -m "initial okx btc bot"
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

Oracle VM:

```bash
ssh ubuntu@<ORACLE_VM_PUBLIC_IP>
git clone <YOUR_REPO_URL>
cd okx-btc-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Test one dry run:

```bash
DRY_RUN=1 python -m src.bot
```

Run with systemd:

```bash
chmod +x deploy/install_systemd_service.sh
./deploy/install_systemd_service.sh
```

Watch logs:

```bash
journalctl -u okx-btc-bot -f
```

Stop:

```bash
sudo systemctl stop okx-btc-bot
```

Restart:

```bash
sudo systemctl restart okx-btc-bot
```

Disable:

```bash
sudo systemctl disable okx-btc-bot
```
