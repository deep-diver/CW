from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from detoxbench.core.models import RunResult
from detoxbench.core.yaml_loader import load_yaml


@dataclass(frozen=True)
class KnownBadFixture:
    id: str
    path: Path
    expected_passed: bool = False
    min_failed_scenarios: int = 1
    allowed_failure_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnownBadAssessment:
    fixture: KnownBadFixture
    run: RunResult
    passed: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture": self.fixture.id,
            "path": str(self.fixture.path),
            "run_id": self.run.run_id,
            "run_subject": self.run.subject,
            "run_passed": self.run.passed,
            "assessment_passed": self.passed,
            "errors": list(self.errors),
            "score": self.run.score,
            "failed_scenarios": [
                {
                    "id": scenario.id,
                    "failure_category": scenario.failure_category,
                    "first_failure": scenario.first_failure,
                }
                for scenario in self.run.scenarios
                if not scenario.passed
            ],
        }


def load_known_bad_fixtures(target_dir: Path) -> list[KnownBadFixture]:
    root = target_dir / "fixtures" / "known_bad"
    if not root.exists():
        return []

    manifest = root / "manifest.yaml"
    if manifest.exists():
        raw = load_yaml(manifest)
        fixtures = raw.get("fixtures", [])
        if not isinstance(fixtures, list):
            raise ValueError(f"{manifest} fixtures must be a list")
        return [_fixture_from_manifest(root, item, manifest) for item in fixtures]

    discovered = []
    for path in sorted(root.iterdir()):
        if path.is_dir() and (path / "index.html").exists():
            discovered.append(KnownBadFixture(id=path.name, path=path.resolve()))
    return discovered


def assess_known_bad_result(fixture: KnownBadFixture, run: RunResult) -> KnownBadAssessment:
    errors: list[str] = []
    if run.passed != fixture.expected_passed:
        expectation = "pass" if fixture.expected_passed else "fail"
        errors.append(f"expected fixture to {expectation}, got passed={run.passed}")

    failed = [scenario for scenario in run.scenarios if not scenario.passed]
    if len(failed) < fixture.min_failed_scenarios:
        errors.append(
            f"expected at least {fixture.min_failed_scenarios} failed scenarios, "
            f"got {len(failed)}"
        )

    if fixture.allowed_failure_categories:
        actual_categories = {
            scenario.failure_category
            for scenario in failed
            if scenario.failure_category is not None
        }
        if not actual_categories:
            errors.append("expected at least one categorized failure")
        unexpected = sorted(actual_categories - set(fixture.allowed_failure_categories))
        if unexpected:
            errors.append(
                "unexpected failure categories: "
                + ", ".join(unexpected)
                + "; allowed: "
                + ", ".join(fixture.allowed_failure_categories)
            )

    return KnownBadAssessment(
        fixture=fixture,
        run=run,
        passed=not errors,
        errors=tuple(errors),
    )


def _fixture_from_manifest(root: Path, item: Any, manifest: Path) -> KnownBadFixture:
    if not isinstance(item, dict):
        raise ValueError(f"{manifest} fixture entries must be mappings")
    fixture_id = item.get("id")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise ValueError(f"{manifest} fixture entry requires non-empty id")
    raw_path = item.get("path", fixture_id)
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError(f"{manifest} fixture {fixture_id!r} path must be a string")
    expected = item.get("expected", {})
    if expected is None:
        expected = {}
    if not isinstance(expected, dict):
        raise ValueError(f"{manifest} fixture {fixture_id!r} expected must be a mapping")
    expected_passed = bool(expected.get("passed", False))
    min_failed_scenarios = int(expected.get("min_failed_scenarios", 1))
    if min_failed_scenarios < 0:
        raise ValueError(
            f"{manifest} fixture {fixture_id!r} expected.min_failed_scenarios "
            "must be greater than or equal to 0"
        )
    categories = expected.get("failure_categories", [])
    if categories is None:
        categories = []
    if not isinstance(categories, list) or not all(
        isinstance(category, str) for category in categories
    ):
        raise ValueError(
            f"{manifest} fixture {fixture_id!r} expected.failure_categories must be a string list"
        )
    fixture_path = (root / raw_path).resolve()
    if not fixture_path.exists():
        raise FileNotFoundError(fixture_path)
    return KnownBadFixture(
        id=fixture_id,
        path=fixture_path,
        expected_passed=expected_passed,
        min_failed_scenarios=min_failed_scenarios,
        allowed_failure_categories=tuple(categories),
    )
