# PR Review Summary: migration/0412 Research Workspace

This package prepares `migration/0412-research-workspace` for review-only PR discussion.

## Purpose

This branch carries the migrated research workspace plus approved Long2 unit-fix work. It should be reviewed as a research and source-scope branch, not as a production deployment branch.

## Current Diff Surface

- Branch diff after cleanup: `284 files changed, 306929 insertions(+), 4 deletions(-)`.
- `research_output` was reduced from `823` retained files to `226` retained files in the PR surface.
- `data/*.csv` remains at `20` files for reproducibility review.
- Cleanup removed `603` redundant generated artifacts from Git tracking while preserving local copies.

## What Changed

- Added the research workspace under `research/`.
- Retained 4h/1h local market CSVs under `data/`.
- Retained compact research evidence under `research_output/`.
- Added app/server webhook code under `app.py` and `server/*`.
- Updated `requirements.txt` with web/research dependencies.
- Applied approved unit fixes in `research/strategy.py` only.

## What Was Fixed

- ATR-distance runtime unit consistency: unscaled ATR distances are converted to runtime units before runtime price comparisons.
- trend_fail EMA runtime unit consistency: unscaled `ema50` is converted into runtime price units before comparison with runtime `Close`.

## Research State

- Long2 tags became accessible after unit fixes.
- Long2 nonzero tags do not prove profitability.
- Lifecycle compression remains after both unit fixes.
- Short2 remains zero in the accepted post-fix state.
- Implementation readiness remains closed / not ready.

## Recommended Review Focus

- `research/strategy.py`: approved unit-fix source changes.
- `requirements.txt`: dependency scope and runtime implications.
- `app.py` and `server/*`: webhook/OKX code presence and whether it belongs in this PR.
- `data/*.csv`: retained data size and reproducibility need.
- `research_output/*`: compact retained research evidence and cleanup decisions.

## Boundary

This PR should not be read as a performance claim, profitability claim, live-readiness claim, or dry-run deployment request.
