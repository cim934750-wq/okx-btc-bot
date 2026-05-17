# Long2 Current Status

## 상태

Long2 research는 active 상태다. Long2는 Long1과 Short1이 closed된 뒤 열린 연구 트랙이다.

## Pre-Patch State

- Long2 execution path exists.
- Raw `add_long_signal = 3958`.
- Pre-patch active Long2 candidates = 1378.
- Pre-patch runtime `in_profit = 0 / 1378`.
- Scale-consistent diagnostic pass = 1324 / 1378.

## Validated Cause

원인은 validated 상태다.

`FractionalBacktest`는 runtime OHLC/entry를 `1e-08`로 scale하지만, ATR은 unscaled 상태로 남아 있었다. 따라서 Long2 `in_profit`은 scaled runtime Close/entry와 unscaled ATR distance를 섞고 있었다.

## Option A Patch State

Option A patch는 Windows D workspace에서 approved and applied 상태다.

Option A는 `research/strategy.py`의 runtime ATR-distance usage를 변경했다.

현재 Mac repo에는 해당 Windows workspace의 전체 research source와 prior `research_output/`가 없다. 따라서 이 Mac repo에서 patch source를 검증하거나 audit을 실행할 수 없다.

## After Patch Counts

| metric | before | after |
| --- | ---: | ---: |
| runtime `in_profit` | 0 / 1378 | 1034 / 1088 |
| all Long2 gates | n/a | 438 / 1088 |
| exported Long2 | 0 | 501 |
| Long1 | 872 | 1668 |
| Short1 | 184 | 527 |
| Short2 | 0 | 0 |

## Interpretation

Option A는 Long2 ATR-distance unit blocker를 제거했다. 하지만 Long1 / Short1 lifecycle이 materially changed 되었다. 따라서 다음 단계는 performance interpretation이 아니다.

다음 단계는 management-exit side-effect audit이다.

## Latest Side-Effect Result

`long2_option_a_side_effect_audit_round1`

| metric | before | after |
| --- | ---: | ---: |
| exported rows | 1056 | 2696 |
| Long1 | 872 | 1668 |
| Long2 | 0 | 501 |
| Short1 | 184 | 527 |
| Short2 | 0 | 0 |
| Long1 avg duration | 16.32 bars | 7.23 bars |
| Short1 avg duration | 109.66 bars | 9.29 bars |

Short2는 sparse active material과 no `in_profit` passes 때문에 계속 zero 상태다.

## Remaining Scale Risk

runtime Close vs unscaled EMA50 `trend_fail` comparisons는 별도 audit이 필요할 수 있다.

## Implementation Readiness

not ready.

## Next Safe Research Step

`long2_option_a_management_exit_audit_round1`

이 audit은 TP1, TP2, trailing stop, stop assignment, breakeven floor, `trend_fail`, runtime ATR-distance side effects를 검토해야 한다. Optimization, performance claims, implementation planning은 금지된다.
