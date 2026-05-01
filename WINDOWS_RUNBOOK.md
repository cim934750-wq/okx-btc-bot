# Windows Dry-Run Runbook

This runbook is for running the OKX BTC bot in Windows dry-run mode from an external drive. Do not reuse the macOS `.venv`; Windows must use `.venv-win`.

## Project Path

Example:

```powershell
E:\Vibecoding\Demo_Bot
```

Open PowerShell in the project root before running commands.

## Create Windows Virtual Environment

```powershell
py -3 -m venv .venv-win
.\.venv-win\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## One-Cycle Smoke Test

```powershell
$env:BOT_MODE="once"
$env:DRY_RUN="1"
$env:OKX_DEMO="1"
$env:LOOP_INTERVAL_SECONDS="1"
python -m src.bot
```

## Long Dry-Run

```powershell
.\scripts\run_dry_windows.ps1
```

The script forces `DRY_RUN=1`, `OKX_DEMO=1`, and `BOT_MODE=live_loop`.
It does not edit `.env` and does not require API keys for market-data-only dry-run observation.

## Watch Heartbeat

```powershell
Get-Content logs\heartbeat.csv -Wait
```

## Analyze Runtime Logs

```powershell
python research\analyze_runtime_logs.py
```

## Disable Sleep While Plugged In

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
```

## Stop Bot

Press `Ctrl + C` in the PowerShell window running the bot.

## Cross-Platform Safety

- Do not run the bot from macOS and Windows at the same time on the same external drive.
- Do not unplug the external drive while the bot is running.
- Stop the bot before switching computers.
- Do not delete logs during a long dry-run.
- Do not remove `runtime/bot.lock` unless you are sure no bot process is running.
- Keep `DRY_RUN=1` and `OKX_DEMO=1` while observing behavior.

## Optional Git Workflow

Local commit works without internet:

```powershell
git status
git add src research deploy scripts README.md requirements.txt .env.example .gitignore WINDOWS_RUNBOOK.md
git commit -m "add windows dry-run runbook"
```

Push requires internet:

```powershell
git push
```
