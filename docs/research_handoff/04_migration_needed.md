# Migration Needed

## 현재 Mac Repo

`/Users/immuhyun/Documents/Coin_Demo/okx-btc-bot`

이 repo는 전체 Windows research workspace가 아니다.

## 현재 Mac Repo에 없는 항목

- `research/strategy.py`
- `research/config.py`
- `research/indicators.py`
- `research_output/`
- prior Long2 CSV outputs

## 가능한 작업

현재 Mac repo에서는 briefing docs를 저장할 수 있다.

## 불가능한 작업

현재 Mac repo만으로는 Long2 audits를 실행할 수 없다. 특히 `long2_option_a_management_exit_audit_round1`은 전체 Windows research workspace migration 또는 GitHub push가 선행되어야 한다.

누락된 `research_output/` 파일을 임의로 만들면 안 된다.

## Expected Windows Source Workspace

`D:\Bot\0412_Bot_short1_research_workspace`

## Expected Future Mac Research Workspace

`~/Documents/Bot/0412_Bot_mac_research_workspace`

## Migration 판단

Migration은 required 상태다. 이 문서들은 연구 상태를 잃지 않기 위한 local MacBook briefing이며, 연구 실행 가능한 workspace를 대체하지 않는다.
