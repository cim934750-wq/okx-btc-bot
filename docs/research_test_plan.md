# Research Package Smoke Test Plan

## Purpose

This PR adds minimal dependency and smoke-test support for the `research/` package introduced in the source unit-fix PR.

It is intentionally dependency/test integration only.

## What It Tests

- `research.config` imports.
- `research.data` imports.
- `research.indicators` imports.
- `research.strategy` imports.
- `BacktestConfig` instantiation.
- `StrategyParams` instantiation.
- Feature-frame construction on deterministic synthetic OHLCV data.
- Required indicator and signal columns are produced.

## Test Environment

Use Python 3.10 or newer because the research package uses `dataclass(slots=True)`. Install only the narrow research dependencies with `pip install -r requirements-research.txt` before running the pytest smoke tests.

## What It Does Not Test

- Profitability.
- Strategy quality.
- Implementation readiness.
- Live/dry-run readiness.
- Optimization.
- Threshold sweeps.
- Full historical backtests.
- Multi-market validation.

## Backtest Smoke

No `run_backtest` smoke test is included in this PR. The smoke surface is limited to imports, config construction, and feature-frame construction so the review does not drift into strategy behavior or performance validation.

## Relationship To PR #2

PR #2 is the source unit-fix review for the `research/` package. This PR adds the minimal dependency and smoke-test support needed to review whether that package can import, compile, and construct features.

## Relationship To PR #1

PR #1 remains the broad archive-only research evidence PR.

## Known Limitation

This PR makes no production claim, no strategy-quality claim, and no readiness claim.
