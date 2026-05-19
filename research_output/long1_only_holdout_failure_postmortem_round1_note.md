# long1_only_holdout_failure_postmortem_round1

## Scope
This is a research-only failure/postmortem scope note for `long1_only_holdout_validation_round1`. It does not run a new backtest, validation, optimization, threshold sweep, data fetch, source edit, PR change, dry-run plan, or live-trading plan.

## Validation Result
The predeclared holdout validation failed. The decision remains: **Fail — park Long1-only; no implementation.**

Reference strength and holdout failure must be separated. The 70% reference segment was strong: 1191 trades, net PnL 5275.31, PF 1.2571, positive markets 13/19. The 30% holdout did not confirm it: 360 trades, net PnL -69.89, PF 0.9832, positive markets 8/19, negative markets 7/19, flat/no-trade markets 4/19.

## Why Long1-only Failed the Predeclared Gate
The candidate failed three decisive predeclared gates: aggregate holdout PnL was non-positive, aggregate PF was below 1.00, and BTCUSDT holdout was negative. It also missed the breadth pass gate of at least 10 positive markets, with only 8/19 positive.

## BTCUSDT Interpretation
BTCUSDT failure is serious for this project. BTCUSDT holdout had 47 trades, net PnL -50.21, PF 0.8475, max DD 0.1581%, and win rate 65.96%. BTC support would have been useful but not sufficient; BTC failure blocks promotion more directly.

## UNI/DOT Pockets Do Not Rescue the Candidate
UNI was positive at 405.20 with PF 2.0461. DOT was slightly positive at 7.81 with PF 1.1487, but had only 3 trades. These pockets do not override aggregate failure, BTC failure, or weak breadth.

## Weak Markets Cannot Be Removed Post-result
DOGE remained weak at -287.14 with PF 0.3586. DOGE, DOT, and UNI were predeclared weak-market checks and must remain visible. Removing weak markets after seeing holdout results would be cherry-picking. Any future exclusion/filter must be separately predeclared and validated.

## Concentration Interpretation
Concentration evidence cannot be used as pass evidence when aggregate holdout PnL is negative. The concentration gates are blocked by aggregate failure. For context, top positive markets were UNIUSDT, AAVEUSDT, TRXUSDT, but the worst 3 markets SOLUSDT, DOGEUSDT, NEARUSDT totaled -804.05. Top-trade contribution is also not pass evidence under negative aggregate PnL.

## Closed Work
Closed from this validation: Long1-only as the current base candidate, Long1-only dry-run discussion, production implementation, profitability claims, and implementation-readiness claims.

## Allowed Remaining Work
Allowed only as research: postmortem-only analysis, separate BTC-only research path only if explicitly approved and predeclared, new candidate research with fresh predeclared gates, and weak-market failure review without cherry-picking.

## Recommendation
Park Long1-only. Do not advance to dry-run. Do not use it as the implementation base. Require a new research hypothesis for any future candidate work.
