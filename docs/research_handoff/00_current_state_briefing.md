# Current Research State Briefing

이 문서는 MacBook에서 현재 확인 가능한 Long1 / Short1 / Long2 연구 상태를 보존하기 위한 briefing이다.

## 범위

- 현재 Mac repo: `/Users/immuhyun/Documents/Coin_Demo/okx-btc-bot`
- 이 repo는 전체 Windows research workspace가 아니다.
- 현재 Mac repo에는 전체 `0412_Bot` 연구 파일과 prior `research_output/` 산출물이 없다.
- 이 문서는 연구 상태 보존용이며, backtest, audit, optimization, implementation planning 결과가 아니다.

## Global State

Long1은 closed 상태다. Long1은 BTC-specific redesign evidence로 남지만, cross-market transfer는 sparse and mixed였다. Larger market-basket validation은 Long1을 broad implementation candidate로 격상하지 못했다. 따라서 Long1 implementation planning은 열려 있지 않다.

Short1은 `short1_discovery_stop_marker_round1`에서 first discovery round가 closed 상태다. 핵심 parent는 `below-EMA20 displacement mainly protects against adverse-dominant failure`이며, leading diagnostic antecedent는 `entry_short_ema20_gap_atr`이다.

Long2는 Long1과 Short1이 closed된 뒤 열린 active research track이다. Long2 execution path는 존재하지만, Option A 이후 Long1 / Short1 lifecycle이 materially changed 되었으므로 performance interpretation이나 implementation planning으로 넘어가면 안 된다. 다음 안전한 연구 단계는 `long2_option_a_management_exit_audit_round1`이다.

## 금지 사항

- `entry_short_ema20_gap_atr`를 threshold, rule, filter, implementation layer로 변환 금지.
- Long1 / Short1 implementation planning 재개 금지.
- Long2 Option A 결과를 성과 개선으로 해석 금지.
- 전체 Windows research workspace가 migrate되기 전 Mac에서 Long2 audit 실행 금지.
- 누락된 `research_output/` CSV를 임의 생성 금지.

## 현재 결론

MacBook은 briefing docs를 저장할 수 있다. 하지만 현재 repo만으로는 Long2 audit, backtest, implementation readiness 판정을 수행할 수 없다. 전체 Windows research workspace migration 또는 GitHub push가 선행되어야 한다.
