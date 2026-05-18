from research.config import BacktestConfig, StrategyParams


def test_research_modules_import() -> None:
    import research.config
    import research.data
    import research.indicators
    import research.strategy

    assert research.config is not None
    assert research.data is not None
    assert research.indicators is not None
    assert research.strategy is not None


def test_research_config_instantiates() -> None:
    backtest_config = BacktestConfig()
    strategy_params = StrategyParams()

    assert backtest_config.initial_cash > 0
    assert strategy_params.exec_fast_length > 0
