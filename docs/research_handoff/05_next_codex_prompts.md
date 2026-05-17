# Next Codex Prompts

## A. Windows Migration Prompt Placeholder

Purpose: `D:\Bot\0412_Bot_short1_research_workspace`를 찾고, 전체 research workspace를 GitHub branch로 commit/push한다.

Target branch:

`migration/0412-research-workspace`

Prompt:

```text
DO ACTUAL WORK NOW.

Find the Windows research workspace:
D:\Bot\0412_Bot_short1_research_workspace

Verify it contains research/strategy.py, research/config.py, research/indicators.py, data/, research_output/, and prior Long2 outputs.

Do not run audits.
Do not run backtests.
Do not modify strategy logic.

Create or switch to branch:
migration/0412-research-workspace

Commit the complete verified research workspace state and push it to GitHub.
Report exact files included, missing files if any, commit SHA, and push result.
```

## B. Mac Verification Prompt Placeholder

Purpose: full migrated workspace가 Mac에서 정상적으로 존재하는지 검증한다.

Required checks:

- `research/strategy.py`
- `research/config.py`
- `research/indicators.py`
- `data/`
- `research_output/`
- Long2 prior outputs

Prompt:

```text
DO ACTUAL WORK NOW.

Verify the migrated Mac research workspace:
~/Documents/Bot/0412_Bot_mac_research_workspace

Check for:
- research/strategy.py
- research/config.py
- research/indicators.py
- data/
- research_output/
- research_output/long2_scale_reference_option_a_patch_round1.*
- research_output/long2_option_a_side_effect_audit_round1.*

Do not run audits.
Do not run backtests.
Do not modify files.
Report READY only if all required files exist.
```

## C. Next Long2 Audit Prompt Placeholder

Title:

`long2_option_a_management_exit_audit_round1`

Purpose: Option A 이후 TP1, TP2, trailing stop, stop assignment, breakeven floor, `trend_fail`, runtime ATR-distance side effects를 inspect한다.

Boundary:

- no optimization
- no performance claims
- no implementation planning

Prompt:

```text
DO ACTUAL WORK NOW.

Run Long2 management-exit side-effect audit:
long2_option_a_management_exit_audit_round1

Inspect TP1, TP2, trailing stop, stop assignment, breakeven floor, trend_fail, and runtime ATR-distance side effects after Option A.

Boundary:
- no optimization
- no performance claims
- no implementation planning
- preserve Long1, Short1, Long2 labels and lifecycle counts

Output audit artifacts under research_output/ with the title:
long2_option_a_management_exit_audit_round1

Report counts, changed lifecycle paths, scale-risk findings, and whether implementation readiness remains blocked.
```
