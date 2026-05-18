# Risk Notes: migration/0412 Research Workspace

## Review-Surface Risks

- The branch still contains `284` changed files after cleanup.
- Retained `data/*.csv` files add review weight but may be needed for reproducibility.
- Retained `research_output/*` files are compact evidence, not a full audit archive.
- App/server files are present and may be outside a pure research PR scope.
- `requirements.txt` changes include both web server and research dependencies.

## Source Risks

- `research/strategy.py` includes approved unit-fix changes and should be reviewed carefully.
- The ATR-distance fix changes runtime unit handling for management comparisons.
- The trend_fail fix changes EMA comparison units in long and short management paths.
- Lifecycle behavior changed materially during the unit-fix work and remains a research concern.

## Interpretation Risks

- Long2 nonzero tags prove only that the Long2 gate can open after unit fixes.
- Long2 nonzero tags do not prove profitability.
- Post-fix counts are not performance evidence.
- Lifecycle compression remains and should not be glossed over.
- Short2 remains zero and should not be described as fixed.

## Implementation Boundary

Implementation readiness is not established. No live or dry-run deployment should be requested from this PR. Any performance validation or implementation planning requires separate explicit approval after review.
