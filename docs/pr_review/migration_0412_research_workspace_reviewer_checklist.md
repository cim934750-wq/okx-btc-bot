# Reviewer Checklist: migration/0412 Research Workspace

Use this checklist for review-only PR evaluation.

## Branch Scope

- [ ] Confirm the branch is `migration/0412-research-workspace`.
- [ ] Confirm the PR is review-only, not production merge-to-deploy.
- [ ] Confirm no profitability claim is made.
- [ ] Confirm implementation readiness is stated as not ready.

## Source Review

- [ ] Review `research/strategy.py` for the ATR-distance runtime unit fix.
- [ ] Review `research/strategy.py` for the trend_fail EMA runtime unit fix.
- [ ] Confirm `research/config.py` does not contain post-cleanup parameter changes.
- [ ] Confirm `research/indicators.py` signal construction was not changed by cleanup.
- [ ] Confirm Long2 add-on logic was not broadened beyond approved unit fixes.

## Dependency And App Surface

- [ ] Review `requirements.txt` dependency changes.
- [ ] Review `app.py` entry point.
- [ ] Review `server/*`, especially OKX order-placement paths.
- [ ] Decide whether app/server files belong in this review-only PR or should be separated.

## Data And Research Evidence

- [ ] Review retained `data/*.csv` files and confirm they are acceptable for PR size/reproducibility.
- [ ] Review retained compact `research_output/*` evidence.
- [ ] Review `research_output/migration_branch_cleanup_round1.*` for cleanup decisions.
- [ ] Confirm redundant generated artifacts were removed from Git tracking.

## Interpretation Boundaries

- [ ] Long2 tags becoming accessible is treated only as gate-access validation.
- [ ] Lifecycle compression remains and is not ignored.
- [ ] Short2 remains zero and is not treated as solved.
- [ ] No live/dry-run step is requested.

## PR Outcome

- [ ] Review source scope.
- [ ] Review research evidence sufficiency.
- [ ] Request cleanup or branch split if app/server/data scope is too broad.
- [ ] Do not approve production deployment from this PR alone.
