# Taker-Flow Data Availability Audit Round 1 Limitations

- The audit fetched only public taker-volume and public trade sample data.
- The OKX Rubik taker-volume endpoint appears to provide ccy/contracts aggregate taker flow, not proven exact instrument-level swap taker flow.
- Adding instId to the Rubik endpoint was treated only as a probe and not proof of exact instrument scope.
- Public trade samples show side/size/timestamp fields, but full historical reconstruction was not attempted.
- Trade reconstruction may be rate-limited, storage-heavy, and may not cover prior reference/holdout windows without a separate feasibility plan.
- Units remain endpoint-defined and are not accepted as cross-market normalized strategy features without a future unit/provenance plan.
- No OHLCV was fetched; range-volume impulse cannot be computed from taker-flow alone in this audit.
- No strategy was defined or validated, and no implementation/dry-run/live readiness is implied.
