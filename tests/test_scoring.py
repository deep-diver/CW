from detoxbench.core.models import (
    AssertionResult,
    RunResult,
    ScenarioResult,
    StepResult,
    classify_failure,
    compute_run_score,
)


def test_formal_score_excludes_probe_scenarios() -> None:
    scenarios = [
        ScenarioResult(
            id="smoke_ok",
            tier="smoke",
            difficulty="d1_smoke",
            kind="scoring",
            weight=1.0,
            passed=True,
            steps=[],
        ),
        ScenarioResult(
            id="journey_fail",
            tier="journey",
            difficulty="d4_adversarial",
            kind="scoring",
            weight=3.0,
            passed=False,
            steps=[],
        ),
        ScenarioResult(id="probe_fail", tier="smoke", kind="probe", weight=99.0, passed=False, steps=[]),
    ]

    score = compute_run_score(scenarios)
    run = RunResult(run_id="run", subject="candidate", output_dir="/tmp/run", scenarios=scenarios)

    assert not run.passed
    assert score["formal"] == {"earned": 1.0, "possible": 4.0, "ratio": 0.25}
    assert score["stepwise"] == {"earned": 1.0, "possible": 4.0, "ratio": 0.25}
    assert score["by_tier"]["smoke"]["passed"] == 1
    assert score["by_tier"]["journey"]["failed"] == 1
    assert score["by_difficulty"]["d1_smoke"]["passed"] == 1
    assert score["by_difficulty"]["d4_adversarial"]["failed"] == 1
    assert score["probe"] == {"passed": 0, "total": 1}


def test_failed_probe_does_not_fail_otherwise_passing_run() -> None:
    scenarios = [
        ScenarioResult(id="formal_ok", tier="behavior", kind="scoring", weight=2.0, passed=True, steps=[]),
        ScenarioResult(id="diagnostic_gap", tier="smoke", kind="probe", weight=1.0, passed=False, steps=[]),
    ]

    run = RunResult(run_id="run", subject="candidate", output_dir="/tmp/run", scenarios=scenarios)

    assert run.passed
    assert run.score["formal"]["ratio"] == 1.0
    assert run.score["stepwise"]["ratio"] == 1.0
    assert run.score["probe"] == {"passed": 0, "total": 1}


def test_stepwise_score_and_contract_breakdown_explain_cliff_failures() -> None:
    passed_step = StepResult(
        scenario_id="route_smoke",
        step_index=1,
        action="snapshot",
        component=None,
        before_state={},
        after_state={},
        before_screenshot="/tmp/before.png",
        after_screenshot="/tmp/after.png",
        assertions=[],
    )
    failed_step = StepResult(
        scenario_id="route_smoke",
        step_index=2,
        action="click",
        component="reset_button",
        before_state={},
        after_state={},
        before_screenshot="/tmp/before2.png",
        after_screenshot="/tmp/after2.png",
        assertions=[
            AssertionResult(
                type="browser_page_equals",
                passed=False,
                message="browser page should equal intake",
                actual=None,
                expected="intake",
            )
        ],
    )
    scenarios = [
        ScenarioResult(
            id="route_smoke",
            tier="smoke",
            difficulty="d2_core",
            kind="scoring",
            weight=2.0,
            passed=False,
            steps=[passed_step, failed_step],
            expected_step_count=2,
        )
    ]

    score = compute_run_score(scenarios)

    assert score["formal"] == {"earned": 0.0, "possible": 2.0, "ratio": 0.0}
    assert score["stepwise"] == {"earned": 1.0, "possible": 2.0, "ratio": 0.5}
    assert score["by_capability"]["smoke"]["step_ratio"] == 0.5
    assert score["by_difficulty"]["d2_core"]["step_ratio"] == 0.5
    assert score["failure_breakdown"] == {"assertion_browser_page_equals": 1}
    assert score["contract"]["failures"] == 1
    assert score["contract"]["ratio"] == 0.0


def test_failure_classification_covers_common_fixture_failures() -> None:
    assert classify_failure(
        {
            "kind": "scenario_error",
            "message": "Error: Page.evaluate: TypeError: Cannot read properties of undefined (reading 'getState')",
        }
    ) == "missing_state_hook"
    assert classify_failure(
        {
            "kind": "scenario_error",
            "message": 'TimeoutError: Locator.click: Timeout 1000ms exceeded.\n  - waiting for locator("[data-testid=\\"save\\"]")',
        }
    ) == "missing_component"
    assert classify_failure(
        {
            "kind": "scenario_error",
            "message": (
                'TimeoutError: Locator.click: Timeout 1000ms exceeded.\n'
                '  - waiting for locator("[data-testid=\\"toggle\\"]")\n'
                "  - <span> intercepts pointer events"
            ),
        }
    ) == "action_unavailable"
    assert classify_failure(
        {
            "kind": "scenario_error",
            "message": (
                "TimeoutError: Page.screenshot: Timeout 5000ms exceeded.\n"
                "Call log:\n  - taking page screenshot"
            ),
        }
    ) == "screenshot_timeout"
    assert classify_failure(
        {
            "kind": "assertion",
            "assertion_type": "state_delta",
            "message": "count should change",
        }
    ) == "assertion_state_delta"
