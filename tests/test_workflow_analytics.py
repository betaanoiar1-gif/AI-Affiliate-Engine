from core.analytics import aggregate_attribution, portfolio_summary
from core.workflow import Stage, WorkflowState, validate_path


def test_workflow_retries_and_terminal_state():
    state = WorkflowState("run-1")
    state.fail("temporary")
    assert state.retryable(3)
    state.advance(Stage.NORMALIZE)
    state.advance(Stage.SCORE)
    assert state.stage is Stage.SCORE
    state.fail("policy block", terminal=True)
    assert not state.retryable()
    assert state.stage is Stage.BLOCKED


def test_workflow_path_rejects_backtracking():
    assert validate_path([Stage.DISCOVER, Stage.NORMALIZE, Stage.SCORE])
    assert not validate_path([Stage.DISCOVER, Stage.SCORE, Stage.NORMALIZE])


def test_attribution_aggregation_is_deterministic():
    metrics = aggregate_attribution([
        {"key": "offer-a", "impressions": 100, "clicks": 10, "conversions": 2, "commission": 8},
        {"key": "offer-a", "impressions": 50, "clicks": 5, "conversions": 1, "commission": 4},
    ])
    assert metrics["offer-a"].clicks == 15
    assert metrics["offer-a"].conversions == 3
    assert portfolio_summary(metrics)["epc"] == 0.8
