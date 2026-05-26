import json
from pathlib import Path

import pytest

from detoxbench.cohorts import cohort_fingerprint, load_cohort_manifest
from detoxbench.core.models import AssertionResult, RunResult, ScenarioResult, StepResult
from detoxbench.dsl.compiler import DslCompileError
from detoxbench.dsl.scenario_sets import discover_scenario_paths, load_scenario_bundles
from detoxbench.known_bad import assess_known_bad_result, load_known_bad_fixtures


def test_split_scenario_bundles_are_discovered_and_filtered(tmp_path: Path) -> None:
    public = tmp_path / "scenarios.public.dsl.yaml"
    private = tmp_path / "scenarios.private.dsl.yaml"
    public.write_text(
        """
dsl_version: "2.0.0"
visibility: public
tier_weights: {smoke: 1}
scenarios:
  - id: public_smoke
    tier: smoke
    steps:
      - do: reset_button.click
""".lstrip(),
        encoding="utf-8",
    )
    private.write_text(
        """
dsl_version: "2.0.0"
visibility: private
tier_weights: {journey: 5}
scenarios:
  - id: private_journey
    tier: journey
    steps:
      - do: reset_button.click
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "scenarios.dsl.yaml").write_text("dsl_version: '2.0.0'\nscenarios: []\n", encoding="utf-8")

    assert discover_scenario_paths(tmp_path, scenario_set="all") == [public, private]
    assert discover_scenario_paths(tmp_path, scenario_set="public") == [public]
    assert discover_scenario_paths(tmp_path, scenario_set="private") == [private]

    merged = load_scenario_bundles([public, private], scenario_set="all")
    assert [scenario["id"] for scenario in merged["scenarios"]] == [
        "public_smoke",
        "private_journey",
    ]
    assert [scenario["visibility"] for scenario in merged["scenarios"]] == [
        "public",
        "private",
    ]
    assert merged["tier_weights"] == {"smoke": 1.0, "journey": 5.0}

    private_only = load_scenario_bundles([public, private], scenario_set="private")
    assert [scenario["id"] for scenario in private_only["scenarios"]] == ["private_journey"]


def test_known_bad_manifest_and_assessment(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures" / "known_bad" / "wrong_delta"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
    manifest = tmp_path / "fixtures" / "known_bad" / "manifest.yaml"
    manifest.write_text(
        """
fixtures:
  - id: wrong_delta
    expected:
      passed: false
      min_failed_scenarios: 1
      failure_categories: [assertion_state_delta]
""".lstrip(),
        encoding="utf-8",
    )

    [fixture] = load_known_bad_fixtures(tmp_path)
    assert fixture.id == "wrong_delta"
    assert fixture.path == fixture_dir.resolve()
    assert fixture.allowed_failure_categories == ("assertion_state_delta",)

    run = RunResult(
        run_id="run",
        subject="known_bad_wrong_delta",
        output_dir=str(tmp_path),
        scenarios=[
            ScenarioResult(
                id="delta",
                passed=False,
                steps=[
                    StepResult(
                        scenario_id="delta",
                        step_index=1,
                        action="click",
                        component="increment_button",
                        before_state={"value": 0},
                        after_state={"value": 0},
                        before_screenshot="before.png",
                        after_screenshot="after.png",
                        assertions=[
                            AssertionResult(
                                type="state_delta",
                                passed=False,
                                message="value should change",
                                actual=0,
                                expected=2,
                            )
                        ],
                    )
                ],
            )
        ],
    )
    assessment = assess_known_bad_result(fixture, run)
    assert assessment.passed
    assert assessment.errors == ()


def test_invalid_scenario_visibility_is_rejected(tmp_path: Path) -> None:
    scenario_file = tmp_path / "scenarios.public.dsl.yaml"
    scenario_file.write_text(
        """
dsl_version: "2.0.0"
visibility: public
scenarios:
  - id: broken_visibility
    visibility: shared
    steps:
      - do: reset_button.click
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(DslCompileError, match="visibility must be public or private"):
        load_scenario_bundles([scenario_file], scenario_set="public")


def test_cohort_manifest_fingerprint_includes_contract_hash(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    contract = target / "contract.dsl.yaml"
    contract.write_text("dsl_version: '2.0.0'\napp: {id: demo}\n", encoding="utf-8")
    manifest = tmp_path / "cohort.yaml"
    manifest.write_text(
        """
version: "1"
name: demo-cohort
members:
  - id: gpt54_default
    model: gpt-5.4
targets:
  - target_dir: target
    contract: contract.dsl.yaml
""".lstrip(),
        encoding="utf-8",
    )

    cohort = load_cohort_manifest(manifest)
    fingerprint = cohort_fingerprint(cohort)

    assert fingerprint["name"] == "demo-cohort"
    assert fingerprint["member_count"] == 1
    assert fingerprint["target_count"] == 1
    assert fingerprint["targets"][0]["contract_sha256"]
    json.dumps(fingerprint)
