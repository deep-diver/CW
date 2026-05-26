from __future__ import annotations

from pathlib import Path
from typing import Any

from detoxbench.dsl.compiler import DslCompileError
from detoxbench.dsl.compiler import load_dsl_yaml


SCENARIO_SET_CHOICES = {"all", "public", "private"}


def discover_scenario_paths(
    target_dir: Path,
    *,
    scenario_set: str = "all",
) -> list[Path]:
    if scenario_set not in SCENARIO_SET_CHOICES:
        raise DslCompileError(
            "scenario_set must be one of " + ", ".join(sorted(SCENARIO_SET_CHOICES))
        )

    split_paths = {
        "public": target_dir / "scenarios.public.dsl.yaml",
        "private": target_dir / "scenarios.private.dsl.yaml",
    }
    existing_split = {key: path for key, path in split_paths.items() if path.exists()}
    if existing_split:
        if scenario_set == "all":
            return [existing_split[key] for key in ("public", "private") if key in existing_split]
        return [existing_split[scenario_set]] if scenario_set in existing_split else []

    legacy = target_dir / "scenarios.dsl.yaml"
    if legacy.exists():
        return [legacy]
    return []


def load_scenario_bundles(paths: list[Path], *, scenario_set: str = "all") -> dict[str, Any]:
    if scenario_set not in SCENARIO_SET_CHOICES:
        raise DslCompileError(
            "scenario_set must be one of " + ", ".join(sorted(SCENARIO_SET_CHOICES))
        )
    if not paths:
        raise DslCompileError("At least one scenario DSL file is required")

    merged: dict[str, Any] = {
        "dsl_version": None,
        "tier_weights": {},
        "scenarios": [],
        "_sources": [],
    }
    seen_ids: set[str] = set()
    for path in paths:
        source_path = path.resolve()
        raw = load_dsl_yaml(source_path)
        version = raw.get("dsl_version")
        if merged["dsl_version"] is None:
            merged["dsl_version"] = version
        elif version != merged["dsl_version"]:
            raise DslCompileError(
                f"Scenario bundle {source_path} uses dsl_version {version!r}, "
                f"expected {merged['dsl_version']!r}"
            )

        visibility = infer_visibility(raw, source_path)
        _merge_tier_weights(merged["tier_weights"], raw.get("tier_weights", {}), source_path)
        scenarios = raw.get("scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            raise DslCompileError(f"{source_path} scenarios must be a non-empty list")
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                raise DslCompileError(f"Every scenario in {source_path} must be a mapping")
            scenario_id = scenario.get("id")
            if not isinstance(scenario_id, str) or not scenario_id:
                raise DslCompileError(f"Every scenario in {source_path} must have a non-empty id")
            if scenario_id in seen_ids:
                raise DslCompileError(f"Duplicate scenario id across bundles: {scenario_id}")
            seen_ids.add(scenario_id)
            scenario_visibility = _parse_visibility(
                scenario.get("visibility", visibility),
                source=f"{source_path} scenario {scenario_id!r}",
            )
            if scenario_set != "all" and scenario_visibility != scenario_set:
                continue
            enriched = dict(scenario)
            enriched.setdefault("visibility", scenario_visibility)
            enriched["_source_path"] = str(source_path)
            merged["scenarios"].append(enriched)
        merged["_sources"].append(str(source_path))

    if merged["dsl_version"] is None:
        raise DslCompileError("Scenario bundle dsl_version is required")
    if not merged["scenarios"]:
        raise DslCompileError(f"No scenarios selected for scenario_set={scenario_set!r}")
    return merged


def infer_visibility(raw: dict[str, Any], path: Path) -> str:
    explicit = raw.get("visibility") or raw.get("scenario_visibility")
    if explicit is not None:
        return _parse_visibility(explicit, source=str(path))
    name = path.name
    if ".public." in name:
        return "public"
    if ".private." in name:
        return "private"
    return "private"


def _parse_visibility(value: Any, *, source: str) -> str:
    if not isinstance(value, str) or value not in {"public", "private"}:
        raise DslCompileError(f"{source} visibility must be public or private")
    return value


def _merge_tier_weights(target: dict[str, float], raw: Any, path: Path) -> None:
    if raw in (None, {}):
        return
    if not isinstance(raw, dict):
        raise DslCompileError(f"{path} tier_weights must be a mapping")
    for tier, value in raw.items():
        if not isinstance(tier, str) or not tier:
            raise DslCompileError(f"{path} tier_weights keys must be non-empty strings")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or float(value) <= 0:
            raise DslCompileError(f"{path} tier_weights.{tier} must be a positive number")
        parsed = float(value)
        if tier in target and target[tier] != parsed:
            raise DslCompileError(
                f"Conflicting tier weight for {tier!r}: {target[tier]} vs {parsed}"
            )
        target[tier] = parsed
