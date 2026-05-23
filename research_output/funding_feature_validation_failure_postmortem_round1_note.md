# Funding Feature Validation Failure Postmortem Round 1

## Scope

This is a research-only postmortem for `funding_feature_validation_round1`. It does not run validation, fetch data, tune funding thresholds, change Candidate D rules, use OI as a replacement feature, remove markets, restart dry-run, create live-trading plans, or claim implementation readiness.

## Candidate Tested

The validation tested whether `funding_extreme_avoidance_filter_round1` could improve the frozen Candidate D 4h mean-reversion base stream. Candidate D remained a research baseline only:

- RSI14 <= 28.
- Close <= EMA20 - 1.5 * ATR14.
- Close > previous close.
- Initial stop = recent 10-candle low - 0.5 * ATR14.
- Exits = EMA20 touch, 1.5R take profit, or 8 completed 4h candle time stop.
- No averaging down and no add-on entries.

The funding gate was frozen as market-specific same/prior 8h funding, max 4h staleness, 180 prior funding observations, rolling percentile from prior observations only, positive extreme blocking long entries, negative extreme diagnostic only, and OI diagnostic-only.

## Validation Result

The filter reduced the base later-data loss but failed to create positive expectancy.

- Base Candidate D later-data: 15 trades, net PnL -174.23, PF 0.1313.
- Funding-gated Candidate D: 7 trades, net PnL -126.24, PF 0.0000, max DD 0.1262%, win rate 0.00%.
- Improvement versus base: +47.99, but still negative.
- No-trade remained better by 126.24.

## Why The Gate Failed

The predeclared gate required positive after-fee performance, no-trade beaten, PF at least 1.10 minimum, sufficient evidence that the filter improved expectancy rather than merely reducing trades, and BTCUSDT not negative if meaningful BTC trades existed. The funding-gated stream failed those conditions.

PF 0.0000 and win rate 0.00% are decisive. The filtered stream did not produce any winning trades in the later-data window. Reduced loss is not the same as positive edge: the gate removed some bad entries, but the remaining allowed entries still lost money.

BTCUSDT also remained negative: 1 filtered trade, net PnL -11.62, PF 0.0. Because BTCUSDT was visible and the candidate remained BTC-relevant through the same 19-market framework, this blocks advancement.

## Loss Reduction Versus Edge

The funding filter blocked 10 entries. Of the blocked entries matched to base trades, it avoided 7 losers totaling -85.02 and missed 2 winners totaling +26.34, with blocked base net PnL of -58.68. That explains why the filtered version improved by +47.99 versus the base stream.

However, the post-filter trade set was still entirely losing. A filter that removes some losing trades but leaves only losing trades is not a tradable edge. The result supports the statement that the frozen funding gate had some loss-reduction behavior, not that it created a robust positive strategy.

## Funding Bucket Interpretation

The gated trades occurred only in p00-p10 and p10-p50 funding buckets, and both buckets were negative. The p50-p90 and p90-p100 buckets were blocked or absent from the gated stream, but the remaining neutral-to-negative funding conditions did not produce profitable mean reversion. Negative funding was only diagnostic and did not rescue performance.

The bucket evidence does not support implementation. It suggests the relationship between this funding percentile rule and Candidate D entries was insufficient in the tested later-data window.

## Market And Family Interpretation

DOGE and UNI had no filtered trades, DOT remained negative at -9.89, and BTCUSDT remained negative at -11.62. Family results were also unfavorable: majors -22.31, large_alts -24.81, other -79.13, with defi and meme_high_beta flat due no trades. The filtered candidate did not show broad positive behavior.

## What Is Closed

The following are closed for implementation purposes:

- Candidate D implementation path.
- `funding_extreme_avoidance_filter_round1` as currently frozen.
- Direct funding-gated Candidate D path.
- Dry-run/live planning from this result.
- Implementation readiness.

No threshold tuning, percentile-window changes, staleness changes, Candidate D rule changes, market removal, or OI substitution is authorized from this postmortem.

## What Remains Allowed

The allowed continuation remains conservative:

- No-trade / capital preservation default.
- Benchmark-only monitoring.
- Future OI/funding research only with a fresh frozen definition and explicit approval.
- Deeper exact-instrument OI audit if desired.
- A genuinely different feature-class inventory, if explicitly approved.

Funding-first remains potentially useful as a research feature class, but this frozen gate on the Candidate D base stream failed and should not be tuned into a result after the fact.

## Recommendation

Pause active trading research from this path and keep no-trade as default. If research continues, use either benchmark-only observation, a deeper exact-instrument OI audit, or a fresh funding/OI feature inventory with a predeclared frozen definition. Do not tune the funding threshold or Candidate D rules from this failure.
