## Purpose

This PR extracts the minimal source changes from the broader research archive branch into a smaller reviewable unit-fix PR.

The broad archive PR remains open separately as review-only research evidence.

## What changed

- Adds or updates `research/strategy.py` with runtime unit consistency fixes.
- Converts unscaled ATR-derived distances into runtime-scaled distances before comparing with runtime-scaled prices.
- Converts unscaled `ema50` into runtime-scaled price level before trend_fail comparisons.

## What this fixes

- Long2 add-on `in_profit` gate previously mixed runtime-scaled Close/entry with unscaled ATR distance.
- trend_fail previously mixed runtime-scaled Close with unscaled `ema50`.

## What this does NOT prove

- This does not prove profitability.
- This does not prove implementation readiness.
- This does not justify live/dry-run deployment.
- This does not claim Long2 is a successful strategy.

## Known remaining concerns

- Long1/Short1 lifecycle compression remains a validation concern.
- Long2 accessibility proves the gate opens after unit fixes, not that it is profitable.
- Broader research evidence remains in PR #1 / `migration/0412-research-workspace`.

## Review focus

Please review:
- runtime scaling helper usage
- ATR-distance vs price-level scaling separation
- possible double-scaling risks
- whether this small PR is appropriately scoped
