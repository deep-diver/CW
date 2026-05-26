#!/usr/bin/env python3
"""Update local reports from completed rerun aggregate artifacts.

The reruns are used to recover model-level detail that was missing from the
retained paper rollups. This script never infers model-level values from group
averages; it only reads completed aggregate.json files and their per-run rows.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "reports" / "conformweb_visualizations" / "data"
REPORT_DIR = ROOT / "reports" / "conformweb_visualizations"


@dataclass(frozen=True)
class BatchSpec:
    family: str
    suite: str
    path: Path
    source_label: str


FAMILY_BY_SUITE = {
    "stayflow_concierge": "Travel",
    "freshcart_market": "Grocery",
    "clinic_shift_command": "Clinical Command",
    "campus_registrar_command": "Campus Registrar",
    "media_campaign_launch_desk": "Media Campaign",
    "homefix_hub": "Home Services",
}


def discover_batches() -> list[BatchSpec]:
    specs: list[BatchSpec] = []
    for path in sorted((ROOT / "targets/web").glob("*/cohorts/_batches/rerun_missing*/aggregate.json")):
        suite = path.parts[path.parts.index("web") + 1]
        batch = path.parent.name
        source = "recovered rerun"
        if "nongemini" in batch:
            source += ": non-Gemini subset"
        elif "gemini" in batch:
            source += ": Gemini subset"
        else:
            source += ": mixed subset"
        specs.append(BatchSpec(FAMILY_BY_SUITE.get(suite, suite), suite, path, source))
    for path in sorted((ROOT / "targets/web").glob("*/tier_d/cohorts/_batches/rerun_missing*/aggregate.json")):
        suite = path.parts[path.parts.index("web") + 1]
        batch = path.parent.name
        source = "recovered rerun"
        if "nongemini" in batch:
            source += ": non-Gemini subset"
        elif "gemini" in batch:
            source += ": Gemini subset"
        else:
            source += ": mixed subset"
        specs.append(BatchSpec(FAMILY_BY_SUITE.get(suite, suite), suite, path, source))
    return specs

MODEL_ORDER = [
    "gpt-5.4-nano",
    "claude-haiku-4-5",
    "gemini-3.1-flash-lite",
    "gpt-5.4-mini",
    "claude-sonnet-4-6",
    "gemini-flash-latest",
    "gpt-5.4",
    "claude-opus-4-6",
    "gemini-3.1-pro-preview",
]

MODEL_GROUP = {
    "gpt-5.4-nano": "M",
    "claude-haiku-4-5": "M",
    "gemini-3.1-flash-lite": "M",
    "gpt-5.4-mini": "T",
    "claude-sonnet-4-6": "T",
    "gemini-flash-latest": "T",
    "gpt-5.4": "F",
    "claude-opus-4-6": "F",
    "gemini-3.1-pro-preview": "F",
}

MODEL_BY_SLUG = {
    "gpt54_nano": "gpt-5.4-nano",
    "claude_haiku45": "claude-haiku-4-5",
    "gemini31_flash_lite": "gemini-3.1-flash-lite",
    "gpt54_mini": "gpt-5.4-mini",
    "claude_sonnet46": "claude-sonnet-4-6",
    "gemini_flash_latest": "gemini-flash-latest",
    "gpt54": "gpt-5.4",
    "claude_opus46": "claude-opus-4-6",
    "gemini31_pro_preview": "gemini-3.1-pro-preview",
}

SCENARIOS_BY_TIER = {
    ("stayflow_concierge", "D"): 28,
    ("freshcart_market", "D"): 34,
    ("clinic_shift_command", "D"): 55,
    ("campus_registrar_command", "C"): 29,
    ("campus_registrar_command", "D"): 34,
    ("media_campaign_launch_desk", "C"): 44,
    ("media_campaign_launch_desk", "D"): 48,
}


def load_rows() -> list[dict[str, Any]]:
    summary_rows = load_rows_from_summaries()
    if summary_rows:
        return summary_rows

    rows: list[dict[str, Any]] = []
    for spec in discover_batches():
        if not spec.path.exists():
            continue
        aggregate = json.loads(spec.path.read_text(encoding="utf-8"))
        per_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in aggregate.get("rows", []):
            model = str(row.get("model"))
            tier = str(row.get("target_tier"))
            group = str(row.get("model_tier"))
            per_key[(tier, group, model)].append(row)
        for (tier, group, model), group_rows in sorted(per_key.items()):
            evaluated = [r for r in group_rows if r.get("formal_ratio") is not None]
            if not evaluated:
                continue
            runs = len(group_rows)
            reportable = len(evaluated)
            full_pass = sum(1 for r in evaluated if bool(r.get("passed")))
            scenarios_total = int(evaluated[0].get("scenarios_total") or SCENARIOS_BY_TIER.get((spec.suite, tier), 0))
            rows.append(
                {
                    "family": spec.family,
                    "suite": spec.suite,
                    "tier": tier,
                    "model_group": group,
                    "model": model,
                    "runs": runs,
                    "reportable_runs": reportable,
                    "scenario_total": scenarios_total,
                    "scenario_pass_mean": mean([r.get("scenarios_passed") for r in evaluated]),
                    "formal_mean": mean([r.get("formal_ratio") for r in evaluated]),
                    "stepwise_mean": mean([r.get("stepwise_ratio") for r in evaluated]),
                    "contract_mean": mean([r.get("contract_ratio") for r in evaluated]),
                    "full_pass": full_pass,
                    "source": spec.source_label,
                    "aggregate_path": str(spec.path.relative_to(ROOT)),
                }
            )
        if not aggregate.get("rows"):
            target_tier = str(aggregate.get("target", "")).rsplit("_tier_", 1)[-1].upper()[:1]
            for summary in aggregate.get("model_summaries", []):
                model = str(summary.get("model"))
                tier = target_tier
                reportable = int(summary.get("n") or summary.get("evaluated") or 0)
                if not reportable:
                    continue
                rows.append(
                    {
                        "family": spec.family,
                        "suite": spec.suite,
                        "tier": tier,
                        "model_group": str(summary.get("model_tier")),
                        "model": model,
                        "runs": reportable,
                        "reportable_runs": reportable,
                        "scenario_total": SCENARIOS_BY_TIER.get((spec.suite, tier), 0),
                        "scenario_pass_mean": "",
                        "formal_mean": float(summary.get("formal_mean") or 0),
                        "stepwise_mean": float(summary.get("stepwise_mean") or 0),
                        "contract_mean": float(summary.get("contract_mean") or 0),
                        "full_pass": int(summary.get("full_pass_count") or 0),
                        "source": spec.source_label,
                        "aggregate_path": str(spec.path.relative_to(ROOT)),
                    }
                )
    return rows


def load_rows_from_summaries() -> list[dict[str, Any]]:
    """Load rerun rows from per-run summary files, deduped by suite/tier/model/rep.

    Several recovery sweeps append duplicate progress lines when retrying failed
    generations in the same batch. The summary files are the stable evaluation
    artifacts, so this reader ignores aggregate.json counts and keeps the newest
    summary for each logical run.
    """

    latest: dict[tuple[str, str, str, str, int], Path] = {}
    for path in sorted((ROOT / "targets/web").glob("*/tier_*/cohorts/*/rerun_missing*/runs/*/r*/20*/summary.json")):
        parts = path.parts
        try:
            web_idx = parts.index("web")
            suite = parts[web_idx + 1]
            tier_part = next(part for part in parts if part.startswith("tier_"))
            tier = tier_part.rsplit("_", 1)[-1].upper()[:1]
            cohorts_idx = parts.index("cohorts")
            group = parts[cohorts_idx + 1]
            batch = parts[cohorts_idx + 2]
            runs_idx = parts.index("runs")
            slug = parts[runs_idx + 1]
            rep = int(parts[runs_idx + 2].lstrip("r"))
        except Exception:
            continue
        if not batch.startswith("rerun_missing"):
            continue
        key = (suite, tier, group, slug, rep)
        if key not in latest or path.parent.name > latest[key].parent.name:
            latest[key] = path

    per_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    source_by_key: dict[tuple[str, str, str, str], str] = {}
    batch_path_by_key: dict[tuple[str, str, str, str], str] = {}
    for (suite, tier, group, slug, rep), path in latest.items():
        model = MODEL_BY_SLUG.get(slug)
        if not model:
            continue
        parts = path.parts
        cohorts_idx = parts.index("cohorts")
        batch = parts[cohorts_idx + 2]
        data = json.loads(path.read_text(encoding="utf-8"))
        score = data.get("score", {})
        scenarios = [
            s for s in data.get("scenarios", [])
            if s.get("score", {}).get("included", True) and s.get("kind", "scoring") == "scoring"
        ]
        row = {
            "passed": bool(data.get("passed")),
            "scenarios_passed": sum(1 for s in scenarios if bool(s.get("passed"))),
            "scenarios_total": len(scenarios) or SCENARIOS_BY_TIER.get((suite, tier), 0),
            "formal_ratio": float(score.get("formal", {}).get("ratio") or 0),
            "stepwise_ratio": float(score.get("stepwise", {}).get("ratio") or 0),
            "contract_ratio": float(score.get("contract", {}).get("ratio") or 1.0),
        }
        aggregate_key = (suite, tier, group, model)
        per_key[aggregate_key].append(row)
        source = "recovered rerun summaries"
        source_by_key[aggregate_key] = source
        cohort_path = ROOT / "targets" / "web" / suite / f"tier_{tier.lower()}" / "cohorts" / group
        batch_path_by_key[aggregate_key] = str(cohort_path.relative_to(ROOT))

    rows: list[dict[str, Any]] = []
    for (suite, tier, group, model), group_rows in sorted(per_key.items()):
        if not group_rows:
            continue
        reportable = len(group_rows)
        rows.append(
            {
                "family": FAMILY_BY_SUITE.get(suite, suite),
                "suite": suite,
                "tier": tier,
                "model_group": group,
                "model": model,
                "runs": reportable,
                "reportable_runs": reportable,
                "scenario_total": int(group_rows[0]["scenarios_total"]),
                "scenario_pass_mean": mean([r["scenarios_passed"] for r in group_rows]),
                "formal_mean": mean([r["formal_ratio"] for r in group_rows]),
                "stepwise_mean": mean([r["stepwise_ratio"] for r in group_rows]),
                "contract_mean": mean([r["contract_ratio"] for r in group_rows]),
                "full_pass": sum(1 for r in group_rows if r["passed"]),
                "source": source_by_key[(suite, tier, group, model)],
                "aggregate_path": batch_path_by_key[(suite, tier, group, model)],
            }
        )
    return rows


def mean(values: list[Any]) -> float:
    xs = [float(v) for v in values if v is not None]
    return sum(xs) / len(xs) if xs else 0.0


def weighted_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(r["reportable_runs"]) for r in rows)
    if total == 0:
        raise ValueError("cannot summarize empty group")
    scenario_total = int(rows[0]["scenario_total"])
    return {
        "runs": total,
        "scenario_total": scenario_total,
        "scenario_pass_mean": sum(r["scenario_pass_mean"] * r["reportable_runs"] for r in rows) / total,
        "formal_mean": sum(r["formal_mean"] * r["reportable_runs"] for r in rows) / total,
        "stepwise_mean": sum(r["stepwise_mean"] * r["reportable_runs"] for r in rows) / total,
        "contract_mean": sum(r["contract_mean"] * r["reportable_runs"] for r in rows) / total,
        "full_pass": sum(int(r["full_pass"]) for r in rows),
    }


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def scenario_cell(row: dict[str, Any]) -> str:
    return f"{row['scenario_pass_mean']:.2f}/{int(row['scenario_total'])}"


def model_line(row: dict[str, Any], source: str | None = None) -> str:
    src = source or str(row["source"])
    return (
        f"| {row['model_group']} | `{row['model']}` | {int(row['reportable_runs'])} | "
        f"{scenario_cell(row)} | {pct(float(row['formal_mean']))} | "
        f"{pct(float(row['stepwise_mean']))} | {pct(float(row['contract_mean']))} | "
        f"{int(row['full_pass'])}/{int(row['reportable_runs'])} | {src} |"
    )


def group_line(group: str, rows: list[dict[str, Any]], source: str) -> str:
    row = weighted_group(rows)
    return (
        f"| {group} | **Group aggregate** | {int(row['runs'])} | "
        f"{scenario_cell(row)} | {pct(float(row['formal_mean']))} | "
        f"{pct(float(row['stepwise_mean']))} | {pct(float(row['contract_mean']))} | "
        f"{int(row['full_pass'])}/{int(row['runs'])} | {source} |"
    )


def campus_section(rows: list[dict[str, Any]], tier: str, existing_f_lines: list[str]) -> str:
    tier_rows = [r for r in rows if r["suite"] == "campus_registrar_command" and r["tier"] == tier]
    by_group = {g: [r for r in tier_rows if r["model_group"] == g] for g in ["M", "T"]}
    lines = [
        f"## Tier {tier} Model-Tier Detail",
        "",
        "M/T model-level rows were recovered from completed 2026-05-25 blind rerun",
        "artifacts generated from the same public contracts and evaluated with the",
        "same DSL browser evaluator. F rows remain from the retained tier README.",
        "",
        "| Group | Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Contract mean | Full pass | Source |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for group in ["M", "T"]:
        ordered = sorted(by_group[group], key=lambda r: MODEL_ORDER.index(r["model"]))
        lines.append(group_line(group, ordered, "recovered rerun"))
        for row in ordered:
            lines.append(model_line(row, "recovered rerun"))
    lines.extend(existing_f_lines)
    return "\n".join(lines)


def replace_section(text: str, heading: str, replacement: str) -> str:
    start = text.index(heading)
    next_start = text.find("\n## ", start + len(heading))
    if next_start == -1:
        return text[:start] + replacement.rstrip() + "\n"
    return text[:start] + replacement.rstrip() + "\n\n" + text[next_start + 1 :]


def update_campus_report(rows: list[dict[str, Any]]) -> None:
    path = ROOT / "targets/web/campus_registrar_command/evaluation_report.md"
    text = path.read_text(encoding="utf-8")
    f_c = [
        "| F | **Group aggregate** | 30 | 21.00/29 | 71.0% | 83.9% | -- | 4/30 | retained report |",
        "| F | `gpt-5.4` | 10 | 21.90/29 | 75.6% | 80.2% | -- | 2/10 | tier README |",
        "| F | `claude-opus-4-6` | 10 | 22.40/29 | 73.4% | 89.5% | -- | 1/10 | tier README |",
        "| F | `gemini-3.1-pro-preview` | 10 | 18.70/29 | 64.1% | 81.9% | -- | 1/10 | tier README |",
    ]
    f_d = [
        "| F | **Group aggregate** | 30 | 26.83/34 | 77.4% | 89.0% | -- | 1/30 | retained report |",
        "| F | `gpt-5.4` | 10 | 24.80/34 | 70.5% | 82.7% | -- | 1/10 | tier README |",
        "| F | `claude-opus-4-6` | 10 | 30.40/34 | 91.4% | 98.9% | -- | 0/10 | tier README |",
        "| F | `gemini-3.1-pro-preview` | 10 | 25.30/34 | 70.2% | 85.6% | -- | 0/10 | tier README |",
    ]
    text = replace_section(text, "## Tier C Model-Tier Detail", campus_section(rows, "C", f_c))
    text = replace_section(text, "## Tier D Model-Tier Detail", campus_section(rows, "D", f_d))
    path.write_text(text, encoding="utf-8")


def write_csv(rows: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = DATA_DIR / "rerun_available_model_rollups.csv"
    fields = [
        "family",
        "suite",
        "tier",
        "model_group",
        "model",
        "runs",
        "reportable_runs",
        "scenario_total",
        "scenario_pass_mean",
        "formal_mean",
        "stepwise_mean",
        "contract_mean",
        "full_pass",
        "source",
        "aggregate_path",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["suite"], r["tier"], r["model_group"], MODEL_ORDER.index(r["model"]))):
            writer.writerow({field: row.get(field, "") for field in fields})


def write_status(rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in rows:
        grouped[(str(row["family"]), str(row["tier"]), str(row["source"]))] += int(row["reportable_runs"])
    lines = [
        "# Rerun Update Status",
        "",
        "Per-run summary artifacts have been deduped into `data/rerun_available_model_rollups.csv`.",
        "The reader ignores retry-inflated aggregate counts and keeps the newest summary for",
        "each `(suite, tier, model group, model, repetition)` key.",
        "",
        "## Available recovered slices",
        "",
    ]
    for (family, tier, source), count in sorted(grouped.items()):
        lines.append(f"- {family} Tier {tier}: {count} reportable runs ({source}).")
    (REPORT_DIR / "rerun_update_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = load_rows()
    write_csv(rows)
    update_campus_report(rows)
    write_status(rows)
    print(f"wrote {DATA_DIR / 'rerun_available_model_rollups.csv'}")
    print(f"wrote {REPORT_DIR / 'rerun_update_status.md'}")
    print("updated targets/web/campus_registrar_command/evaluation_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
