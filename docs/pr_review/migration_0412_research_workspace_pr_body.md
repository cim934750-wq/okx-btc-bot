## What changed

This review-only PR packages the migrated `migration/0412-research-workspace` branch after cleanup.

It includes:

- Research workspace files under `research/`.
- Approved unit-fix source changes in `research/strategy.py`.
- Retained local market data under `data/*.csv`.
- Compact retained research evidence under `research_output/`.
- PR review docs under `docs/pr_review/`.
- Existing app/server files under `app.py` and `server/*` that need explicit scope review.
- `requirements.txt` dependency changes that need review.

The cleanup commit reduced the branch review surface from `881 files / 533503 insertions` to `284 files / 306929 insertions`, and reduced retained `research_output` files from `823` to `226`. It removed `603` redundant generated artifacts from Git tracking while preserving local copies.

## Why this branch exists

The branch carries the MacBook research workspace migration and the completed Long2 Option A unit-fix validation chain. It exists to let reviewers inspect the unit-fix source changes and the compact research evidence that supports the validation boundary.

## What was fixed

- ATR-distance runtime unit fix: unscaled ATR-distance values are converted into runtime price units before runtime price comparisons.
- trend_fail EMA runtime unit fix: unscaled `ema50` is converted into runtime price units before comparison with runtime `Close`.

## What was NOT proven

- This PR does not prove profitability.
- This PR does not prove strategy readiness.
- This PR does not prove live or dry-run readiness.
- Long2 tags becoming accessible proves gate accessibility only, not performance.
- Lifecycle compression remains after the unit fixes.
- Short2 remains zero in the accepted post-fix state.

## Files reviewers should inspect

- `research/strategy.py`: approved unit-fix implementation.
- `requirements.txt`: dependency changes.
- `app.py`: server entry point.
- `server/*`: webhook and OKX order-handling code present on the branch.
- `data/*.csv`: retained local data files for reproducibility review.
- `research_output/long2_post_unit_fix_exit_synthesis_round1.*`: synthesis of the post-unit-fix state.
- `research_output/migration_branch_cleanup_round1.*`: cleanup decisions and retained/removed file classification.
- `research_output/migration_branch_review_round1.*`: branch review state before cleanup.

## Known risks

- The branch still includes app/server code, which may be outside a narrow research PR scope.
- `requirements.txt` includes web server and research dependencies and should be reviewed separately from strategy logic.
- The retained data files are sizable but were kept because they may be needed for reproducibility.
- The retained research outputs are summary-level evidence, not the entire generated artifact set.
- Lifecycle compression remains and should be reviewed as an unresolved research interpretation boundary.

## Explicit no-performance-claim boundary

No profitability claim is made in this PR. Counts, tags, gate accessibility, and lifecycle summaries are validation evidence only.

## Implementation readiness

Implementation readiness is not ready / closed. This PR should not be used to request or approve live trading, dry-run deployment, or production merge-to-deploy behavior.

## Recommended review focus

Please review source scope, unit consistency, retained research evidence, and whether the app/server/data surfaces belong in this PR. No live/dry-run step should happen until a separate explicit approval after post-fix performance validation.
