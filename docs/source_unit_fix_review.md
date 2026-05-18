# Source Unit-Fix Review

## Purpose

This small PR extracts only the source-level runtime unit consistency changes from the broader research archive branch into a focused review branch.

## Source Files Included

- `research/strategy.py`
- `research/__init__.py`
- `research/config.py`
- `research/data.py`
- `research/indicators.py`

The supporting `research/` files are included because `research/strategy.py` imports them and `main` does not currently contain the research package.

## What Was Fixed

1. ATR-distance runtime scale consistency
   - Unscaled ATR-derived distances are converted into runtime-scaled distances before comparisons with runtime-scaled prices such as `Close`, `High`, `Low`, entry, and average entry.
   - This applies to TP, SL, trailing, breakeven, and add-on distance logic.

2. trend_fail EMA runtime scale consistency
   - Unscaled `ema50` is converted into runtime-scaled price units before comparison with runtime-scaled `Close`.
   - This applies only to long/short `trend_fail` comparisons.

## What Is Not Claimed

- No profitability claim is made.
- No implementation readiness is claimed.
- No live/dry-run readiness is claimed.
- No optimization or threshold sweep is included.

## Relation To PR #1

PR #1 remains the broad review-only research archive. This branch is the smaller source-review branch for the runtime unit consistency patch.

## Known Remaining Risk

- Long1/Short1 lifecycle compression still requires caution when interpreting strategy behavior.
- Long2 accessibility proves the gate opens after unit fixes; it does not prove strategy quality or profitability.
