# BTC Multi-Day Paper Observation Plan

## Purpose

This plan defines how to operate the existing BTC Long1 paper-mode MVP for a 24-hour to 7-day observation window before any future non-executing `OrderIntentWriter` implementation is requested.

The plan uses only existing paper-mode commands. It does not add an `OrderIntentWriter`, write `runtime/order_intents/`, add adapters, call private APIs, use API keys, place orders, manage real positions, deploy to production, tune thresholds, claim profitability, or claim testnet/live readiness.

## Safety Boundary

- Paper/dry-run observation only.
- Public BTCUSDT 4h data refresh only.
- No private exchange or account endpoint.
- No API keys or credentials.
- No order placement.
- No real position management.
- No external notifications.
- No manual override of `BLOCK`, `WARN`, stale-data, malformed-input, or risk flags.
- No strategy threshold changes during the observation window.
- No OrderIntentWriter, adapter, testnet, or live trading implementation.

## Exact Safe Command Sequence

Run from the repository root:

```bash
python scripts/refresh_btcusdt_4h_data.py
python scripts/run_btc_signal_once.py
python scripts/report_btc_paper_status.py
python scripts/report_btc_dry_run_status.py
python scripts/review_btc_daily_dry_run.py
python scripts/summarize_btc_daily_alerts.py
python scripts/print_btc_operator_checklist.py
```

Developer-only safety checks can be run after the operating sequence:

```bash
python scripts/audit_btc_order_intent_schema.py
python scripts/review_btc_order_intent_writer_design.py
```

These commands are read-only unless explicitly documented otherwise. `refresh_btcusdt_4h_data.py` writes local public-market data and a provenance report. `run_btc_signal_once.py` writes local paper logs/state only. `review_btc_daily_dry_run.py` writes local daily review snapshots only.

## When To Run

- Once at the start of the observation window: run the full safe command sequence.
- After each completed 4h candle if manually observed: run data refresh, one signal check, paper status dashboard, monitoring report, alert summary, and checklist.
- Once per day: run the daily review, alert summary, and operator checklist.
- After any `stale_data`, `WARN`, or `BLOCKED` state: run the full safe command sequence and record the blocked/warn reason.
- Before discussing any `PAPER_LONG`: rerun paper status, monitoring, daily review, alert summary, and checklist.

## 24-Hour Routine

1. Start with a clean paper-mode review:

   ```bash
   python scripts/refresh_btcusdt_4h_data.py
   python scripts/run_btc_signal_once.py
   python scripts/report_btc_paper_status.py
   python scripts/report_btc_dry_run_status.py
   python scripts/review_btc_daily_dry_run.py
   python scripts/summarize_btc_daily_alerts.py
   python scripts/print_btc_operator_checklist.py
   ```

2. Record the manual fields from the observation summary template.
3. If checking after each completed 4h candle, rerun:

   ```bash
   python scripts/refresh_btcusdt_4h_data.py
   python scripts/run_btc_signal_once.py
   python scripts/report_btc_paper_status.py
   python scripts/report_btc_dry_run_status.py
   ```

4. At the end of the day, rerun:

   ```bash
   python scripts/review_btc_daily_dry_run.py
   python scripts/summarize_btc_daily_alerts.py
   python scripts/print_btc_operator_checklist.py
   ```

5. Answer the 24-hour review questions before continuing to a longer observation window.

## 7-Day Routine

- Day 1: run the full safe command sequence and confirm local files/logs are readable.
- Days 2 through 6: refresh public data and run one signal check after any manually observed completed 4h candle; run one daily review and alert/checklist sequence per day.
- Day 7: run the full safe command sequence, then complete the 7-day review questions and summary template.
- Do not change thresholds, strategy conditions, risk gates, or paper-state files during the observation window.
- Do not request an `OrderIntentWriter` until the observation summary shows stable data refresh, explainable alerts, consistent paper state, and no unresolved stop conditions.

## Manual Fields To Record

Record these fields after each full observation pass:

- Observation date/time in UTC and local time.
- Latest candle timestamp.
- Data freshness: stale or not stale.
- Signal decision.
- Long1 active or inactive.
- Confidence label.
- Passed condition count.
- Missing condition count.
- Main missing conditions.
- Risk level.
- Risk flags.
- Response action.
- Paper position open or closed.
- Paper side.
- Paper entry time and price, if any.
- Monitoring log entries read and summarized.
- Alert severity.
- Checklist primary reason.
- Operator action taken: observe, refresh, investigate, or stop.
- Notes on unexpected behavior.

## Observation Success Criteria

- Public BTCUSDT 4h refresh works repeatedly without credentials.
- `stale_data` clears after a successful refresh when recent completed candles are available.
- Decision logs increase over time after signal checks.
- Daily reviews write snapshots and compare with prior snapshots correctly.
- Alert severity is explainable from stale status, signal evidence, risk flags, response action, and paper state.
- `BLOCK` and `WARN` states are not manually overridden.
- Paper state remains internally consistent with decision logs.
- Any `PAPER_LONG` is explainable from signal evidence, risk level, response action, and paper-state transition.
- Schema audit and writer review remain `PASS` without implying implementation or trading approval.

## Observation Stop Conditions

Stop observation and inspect local files before continuing if any condition appears:

- Public data refresh fails repeatedly.
- `stale_data` persists after refresh.
- Decision logs are malformed or stop increasing after signal checks.
- Daily review snapshots are malformed or cannot compare with prior snapshots.
- Paper state is missing, malformed, or inconsistent with recent decision logs.
- Risk flags appear that cannot be explained from the current status dashboard.
- `PAPER_LONG` appears but status, logs, daily review, or checklist cannot explain it.
- Response remains `BLOCK` after the documented remediation sequence.
- Any operator is tempted to override `BLOCK`, change thresholds, edit state manually, or infer missing data.
- Any path appears to require API keys, account data, exchange orders, testnet, or live trading.

## 24-Hour Review Questions

- Did commands run in the expected order?
- Did public BTC data refresh complete without API keys?
- Did `stale_data` clear after refresh when recent completed candles were available?
- Did decision logs and daily snapshots accumulate?
- Were all `BLOCK` and `WARN` states explainable?
- Did paper state remain closed or transition predictably?
- Did any `PAPER_LONG` occur?
- If `PAPER_LONG` occurred, did the evidence, risk, response, and paper-state transition explain it?
- Did any command require credentials, private APIs, or external notifications?
- Did any operator action bypass a documented safety gate?

## 7-Day Review Questions

- How many signal checks were run?
- How many `WAIT`, `WATCH`, `BLOCK`, and `PAPER_LONG` outcomes occurred?
- How often did `stale_data` occur?
- Which risk flags dominated the observation window?
- Did weekly/daily regime mismatch persist?
- Did paper entries and exits behave consistently with logs and paper state?
- Did monitoring log counts and daily snapshot comparisons behave consistently?
- Were alert severities stable and explainable?
- Were any stop conditions triggered?
- Is an `OrderIntentWriter` actually useful yet, or should paper observation continue?
- Are there unresolved strategy validation issues that make any future intent writer premature?

## Observation Summary Template

```text
Observation window:
Operator:
Repository branch:
Start timestamp:
End timestamp:

Signal checks run:
Daily reviews generated:
Alert summaries generated:
Operator checklists reviewed:

Latest candle timestamp:
Final stale status:
Final signal decision:
Final Long1 active:
Final confidence:
Final passed/missing condition counts:
Final risk level:
Final risk flags:
Final response action:
Final paper position state:

WAIT count:
WATCH count:
BLOCK count:
PAPER_LONG count:
stale_data count:
Top risk flags:

BLOCK/WARN states observed:
Were all BLOCK/WARN states explainable:
Any PAPER_LONG observed:
If PAPER_LONG observed, was it explainable:
Any malformed logs/state/snapshots:
Any stop condition triggered:

Operator conclusion:
Continue paper observation:
Request docs/tests only:
Request non-executing OrderIntentWriter design/implementation:
Do not proceed because:
```

## Operator Checklist

Before each observation pass:

- Confirm this is paper mode only.
- Confirm no API keys are configured or needed.
- Confirm the command sequence is local and inspectable.
- Confirm no runtime order-intent writer exists.
- Confirm no exchange adapter exists.
- Confirm no testnet/live trading path exists.

During each observation pass:

- Run commands in the documented order.
- Read the paper status dashboard before interpreting alerts.
- Read alert summary before using the operator checklist.
- Record all manual fields.
- Do not edit logs, snapshots, or paper state to force a better result.
- Do not change thresholds or strategy conditions.

After each observation pass:

- Confirm logs increased after signal checks.
- Confirm daily review snapshots compare correctly.
- Confirm alerts and checklist reasons are explainable.
- Stop if any stop condition appears.

## Relationship To Future OrderIntentWriter

This observation plan is a prerequisite review aid, not an implementation request. A future non-executing `OrderIntentWriter` should not be requested until the operator can show a stable observation summary with explainable alerts, consistent paper state, and no unresolved stop conditions.

Even after a successful observation window, live trading remains forbidden. Testnet remains approval-gated and future-only.
