# BTC Google Cloud Paper Observation Guide

## Purpose

This guide shows how to run a fresh BTC paper-mode observation on a Google Cloud Compute Engine VM. A VM is better suited than a laptop for uninterrupted 24-hour or multi-day observation.

This is paper observation only. It does not add an `OrderIntentWriter`, does not create `runtime/order_intents/`, does not add exchange adapters, does not call private APIs, does not require API keys, does not read account data, does not place orders, and does not enable testnet or live trading.

Do not treat a VM observation as a continuation of a laptop observation if the move creates a gap. Start a new VM-labeled observation window and keep the local partial run labeled partial.

## Cost Warning

Google Cloud charges for Compute Engine resources while they exist and may charge for disk, network, and storage. Stop or delete the VM when the observation is finished.

## Local Preflight

From the local repository, verify the remote URL and branch:

```bash
git remote -v
git branch --show-current
```

Expected branch:

```text
automation/btc-signal-response-mvp
```

Current remote example:

```text
https://github.com/cim934750-wq/okx-btc-bot.git
```

If your remote is different, replace the repo URL in the commands below.

## Create Or Select Google Cloud Project

```bash
gcloud config set project <PROJECT_ID>
```

Replace `<PROJECT_ID>` with your Google Cloud project ID. This guide does not create a VM automatically from Codex; run these commands yourself only when you intend to incur VM costs.

## Create A Small Ubuntu VM

Example region/zone near Korea:

```bash
gcloud compute instances create btc-paper-observer \
  --zone=asia-northeast3-a \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB
```

Notes:

- `e2-micro` is usually enough for this paper observation workflow.
- Use `e2-small` if dependency install or pandas work is too slow.
- Costs accrue while the VM exists and is running.

## SSH Into The VM

```bash
gcloud compute ssh btc-paper-observer --zone=asia-northeast3-a
```

## Install System Packages

On the VM:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip screen tmux
```

## Clone Repo And Checkout Branch

```bash
git clone https://github.com/cim934750-wq/okx-btc-bot.git okx-btc-bot
cd okx-btc-bot
git checkout automation/btc-signal-response-mvp
```

If the repo URL changes, replace it with the output from local `git remote -v`.

## Set Up Python Environment

```bash
python3 -m venv .venv-btc-signal-mvp
. .venv-btc-signal-mvp/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-research.txt
```

If a development requirements file is needed for tests:

```bash
pip install -r requirements-research-dev.txt
```

Do not install global Python packages for this workflow.

## Verify Safety Before Observation

Run these on the VM:

```bash
python scripts/audit_btc_order_intent_schema.py
python scripts/review_btc_order_intent_writer_design.py
python scripts/report_btc_paper_status.py
```

Expected safety properties:

- Schema audit reports `PASS`.
- Writer review reports `PASS`, but that is not approval to implement a writer or trade.
- Paper status uses local/public data and requires no API keys.

Verify no order-intent files exist:

```bash
test ! -d runtime/order_intents && echo "OK: no order intents"
```

Verify no obvious credential environment variables are present:

```bash
env | grep -Ei 'OKX|API|SECRET|PASSPHRASE|TOKEN' || true
```

If credential variables appear, do not use them for this paper observation.

## Start A Screen Session

```bash
screen -S btc24h_observer
```

Detach without stopping the process:

```text
Ctrl+A, then D
```

Reattach:

```bash
screen -r btc24h_observer
```

List sessions:

```bash
screen -ls
```

## Start A Fresh VM 24-Hour Observation

Use the safe launcher:

```bash
python scripts/run_btc_24h_paper_observation_cycle.py \
  --duration-hours 24 \
  --interval-minutes 245
```

The launcher runs only existing safe paper commands:

```bash
python scripts/refresh_btcusdt_4h_data.py
python scripts/run_btc_signal_once.py
python scripts/report_btc_paper_status.py --format json
python scripts/report_btc_dry_run_status.py --format json
python scripts/review_btc_daily_dry_run.py --format json
python scripts/summarize_btc_daily_alerts.py --format json
python scripts/print_btc_operator_checklist.py --format json
python scripts/audit_btc_order_intent_schema.py --format json
python scripts/review_btc_order_intent_writer_design.py --format json
```

It writes runtime observation summaries under:

```text
runtime/observation/
```

It does not create `runtime/order_intents/`, does not call private APIs, does not require API keys, and cannot place exchange orders.

## Manual Alternative Without The Launcher

Run the safe sequence manually:

```bash
python scripts/refresh_btcusdt_4h_data.py
python scripts/run_btc_signal_once.py
python scripts/report_btc_paper_status.py
python scripts/report_btc_dry_run_status.py
python scripts/review_btc_daily_dry_run.py
python scripts/summarize_btc_daily_alerts.py
python scripts/print_btc_operator_checklist.py
```

Repeat after completed 4h candles, or use a shell loop inside `screen`:

```bash
while true; do
  date -u
  python scripts/refresh_btcusdt_4h_data.py
  python scripts/run_btc_signal_once.py
  python scripts/report_btc_paper_status.py
  python scripts/report_btc_dry_run_status.py
  python scripts/review_btc_daily_dry_run.py
  python scripts/summarize_btc_daily_alerts.py
  python scripts/print_btc_operator_checklist.py
  sleep 14700
done
```

`sleep 14700` is about 4 hours and 5 minutes. Stop manually after the intended observation window. Do not add private or trading commands to this loop.

## After 24 Hours

Run a final read-only review:

```bash
python scripts/report_btc_paper_status.py
python scripts/report_btc_dry_run_status.py
python scripts/review_btc_daily_dry_run.py
python scripts/summarize_btc_daily_alerts.py
python scripts/print_btc_operator_checklist.py
```

Collect:

- VM observation start time.
- VM observation end time.
- `completed_24h` true/false.
- Refresh attempts and success/failure counts.
- Old/new latest candle timestamps.
- Latest candle freshness and age.
- Signal decision counts.
- Response action counts.
- Risk level counts.
- Risk flag counts.
- `stale_data` count.
- Long1 active count.
- `PAPER_LONG` count.
- `BLOCK` count.
- Daily review count.
- Alert severity counts.
- Checklist severity counts.
- Paper state consistency.
- Whether `runtime/order_intents` stayed absent.
- Whether any private API, order, or credential path was touched.
- Whether any stop condition occurred.

## Retrieve Runtime Outputs

View on the VM:

```bash
cat runtime/observation/btc_24h_vm_observation_summary_latest.json
less runtime/observation/btc_24h_vm_observation_summary_latest.md
```

Copy outputs from VM to local machine:

```bash
gcloud compute scp --recurse \
  btc-paper-observer:~/okx-btc-bot/runtime/observation \
  ./btc_vm_observation_output \
  --zone=asia-northeast3-a
```

You can also copy:

```bash
gcloud compute scp --recurse \
  btc-paper-observer:~/okx-btc-bot/runtime/daily_reviews \
  ./btc_vm_daily_reviews \
  --zone=asia-northeast3-a
```

Do not commit runtime observation files unless explicitly requested later.

## Stop Or Delete VM

Stop to avoid compute charges while preserving disk:

```bash
gcloud compute instances stop btc-paper-observer --zone=asia-northeast3-a
```

Delete if no longer needed:

```bash
gcloud compute instances delete btc-paper-observer --zone=asia-northeast3-a
```

## Handling stale_data

If `stale_data` appears:

1. Refresh public BTC data manually.
2. Rerun one signal check.
3. Rerun paper status.
4. Rerun daily review.
5. Rerun alert summary.
6. Rerun operator checklist.
7. Never override `BLOCK` manually.

Commands:

```bash
python scripts/refresh_btcusdt_4h_data.py
python scripts/run_btc_signal_once.py
python scripts/report_btc_paper_status.py
python scripts/review_btc_daily_dry_run.py
python scripts/summarize_btc_daily_alerts.py
python scripts/print_btc_operator_checklist.py
```

## Forbidden In VM Observation

- No API keys.
- No private OKX or exchange API calls.
- No account reads.
- No exchange order placement.
- No real position management.
- No OrderIntentWriter.
- No `runtime/order_intents/`.
- No exchange adapter.
- No simulated adapter unless separately approved as local-only design.
- No testnet trading.
- No live trading.
- No external notifications.
- No strategy threshold changes.
- No profitability or readiness claims.
