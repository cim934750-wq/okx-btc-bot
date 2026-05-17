# Short1 Closed Summary

## 상태

Short1 first discovery round는 `short1_discovery_stop_marker_round1`에서 closed 상태다.

## Main Parent

`below-EMA20 displacement mainly protects against adverse-dominant failure`

## Leading Diagnostic Antecedent

`entry_short_ema20_gap_atr`

`entry_short_ema20_gap_atr`는 diagnostic-only이다. 이 항목은 threshold, rule, filter, implementation layer로 변환하면 안 된다.

## Stable Failure Target

`adverse_dominant`가 stable main failure target이다.

`mixed_chop`과 `weak_followthrough`는 high-level `unresolved_non_clean` ledger item으로만 묶을 수 있다. 단, component labels는 analysis를 위해 유지해야 한다.

`failed_no_followthrough`는 표본이 너무 작아 해석하면 안 된다.

## Final Bucket Counts

### Executed

| bucket | count | status |
| --- | ---: | --- |
| clean_followthrough | 61 | included |
| adverse_dominant | 66 | included |
| mixed_chop | 16 | included |
| weak_followthrough | 11 | included |
| unresolved_non_clean | 27 | grouped ledger |
| failed_no_followthrough | 1 | excluded |

### Starter

| bucket | count | status |
| --- | ---: | --- |
| clean_followthrough | 176 | included |
| adverse_dominant | 227 | included |
| mixed_chop | 29 | included |
| weak_followthrough | 41 | included |
| unresolved_non_clean | 70 | grouped ledger |
| failed_no_followthrough | 1 | excluded |

## 금지 사항

- `entry_short_ema20_gap_atr`를 implementation rule로 변환 금지.
- `failed_no_followthrough` 해석 금지.
- Short1 implementation planning 재개 금지.

## 결론

Short1은 closed discovery state이며, `adverse_dominant` failure protection이 중심 해석이다.
