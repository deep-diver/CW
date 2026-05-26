import json
from pathlib import Path

from detoxbench.gallery import GalleryConfig, build_gallery_data


def test_gallery_discovers_targets_and_summarizes_latest_runs(tmp_path: Path) -> None:
    targets_root = tmp_path / "targets" / "web"
    target_dir = targets_root / "portfolio"
    target_dir.mkdir(parents=True)
    (target_dir / "contract.dsl.yaml").write_text(
        """
dsl_version: "1.0.0"
app:
  id: web.portfolio
  name: Portfolio Console
  capability: test fixture
runtime:
  target: web
  state_probe:
    expression: window.__DETOX_STATE__
state:
  initial: {}
  schema: {}
components: {}
""".lstrip(),
        encoding="utf-8",
    )
    (target_dir / "scenarios.dsl.yaml").write_text(
        """
dsl_version: "1.0.0"
scenarios:
  - id: open_console
    tier: smoke
    kind: scoring
    weight: 1
    steps:
      - do: snapshot
""".lstrip(),
        encoding="utf-8",
    )
    summary_path = target_dir / "artifacts" / "runs" / "reference" / "20260508-010000-good" / "summary.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(
        json.dumps(
            {
                "run_id": "20260508-010000-good",
                "subject": "reference",
                "passed": True,
                "output_dir": str(summary_path.parent),
                "score": {
                    "formal": {"earned": 1.0, "possible": 1.0, "ratio": 1.0},
                    "by_tier": {
                        "smoke": {
                            "earned": 1.0,
                            "possible": 1.0,
                            "passed": 1,
                            "failed": 0,
                            "total": 1,
                            "ratio": 1.0,
                        }
                    },
                    "probe": {"passed": 0, "total": 0},
                },
                "scenarios": [
                    {
                        "id": "open_console",
                        "tier": "smoke",
                        "kind": "scoring",
                        "weight": 1.0,
                        "passed": True,
                        "error": None,
                        "expected_step_count": 1,
                        "completed_step_count": 0,
                        "passed_step_count": 0,
                        "passed_until_step": 1,
                        "steps": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    data = build_gallery_data(
        GalleryConfig(
            targets_root=targets_root,
            output=tmp_path / "artifacts" / "gallery" / "index.html",
            title="Suite",
        )
    )

    assert data["targets"] == [
        {
            "id": "portfolio",
            "label": "Portfolio Console",
            "target_path": str(target_dir.resolve()),
            "dashboard_ref": None,
            "preview_ref": None,
            "scenario_count": 1,
            "subject_count": 1,
            "run_count": 1,
            "failure_count": 0,
            "best_score": 1.0,
            "reference_score": 1.0,
            "tiers": {"smoke": 1},
        }
    ]


def test_gallery_manifest_resolves_paths_relative_to_manifest(tmp_path: Path) -> None:
    suite_dir = tmp_path / "targets" / "web"
    target_dir = suite_dir / "orders"
    target_dir.mkdir(parents=True)
    (target_dir / "contract.dsl.yaml").write_text(
        """
dsl_version: "1.0.0"
app:
  id: web.orders
  name: Orders Desk
  capability: test fixture
runtime:
  target: web
  state_probe:
    expression: window.__DETOX_STATE__
state:
  initial: {}
  schema: {}
components: {}
""".lstrip(),
        encoding="utf-8",
    )
    (target_dir / "scenarios.dsl.yaml").write_text(
        """
dsl_version: "1.0.0"
scenarios: []
""".lstrip(),
        encoding="utf-8",
    )
    manifest = suite_dir / "suite.yaml"
    manifest.write_text(
        """
targets:
  - target_dir: orders
""".lstrip(),
        encoding="utf-8",
    )

    data = build_gallery_data(
        GalleryConfig(
            manifest=manifest,
            output=tmp_path / "artifacts" / "gallery" / "index.html",
            title="Suite",
        )
    )

    assert data["targets"][0]["id"] == "orders"
    assert data["targets"][0]["target_path"] == str(target_dir.resolve())


def test_gallery_discovers_nested_tier_targets(tmp_path: Path) -> None:
    targets_root = tmp_path / "targets" / "web"
    target_dir = targets_root / "suite" / "tier_a"
    target_dir.mkdir(parents=True)
    (target_dir / "contract.dsl.yaml").write_text(
        """
dsl_version: "1.0.0"
app:
  id: nested.target
  name: Nested Target
  capability: test fixture
runtime:
  target: web
  state_probe:
    expression: window.__DETOX_STATE__
state:
  initial: {}
  schema: {}
components: {}
""".lstrip(),
        encoding="utf-8",
    )
    (target_dir / "scenarios.public.dsl.yaml").write_text(
        """
dsl_version: "1.0.0"
visibility: public
scenarios:
  - id: open_console
    tier: smoke
    steps:
      - do: snapshot
""".lstrip(),
        encoding="utf-8",
    )

    data = build_gallery_data(
        GalleryConfig(
            targets_root=targets_root,
            output=tmp_path / "reports" / "gallery" / "index.html",
            title="Suite",
        )
    )

    assert data["targets"][0]["id"] == "tier_a"
    assert data["targets"][0]["label"] == "Nested Target"
    assert data["targets"][0]["target_path"] == str(target_dir.resolve())
