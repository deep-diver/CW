from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class TargetSpec:
    tier: str
    target_dir: Path
    visual: str


@dataclass(frozen=True)
class ModelSpec:
    model_tier: str
    slug: str
    provider: str
    model: str
    max_output_tokens: int = 24000
    base_url: str | None = None
    request_timeout: int = 240


TARGETS = [
    TargetSpec(
        tier="A",
        target_dir=ROOT / "targets/web/stayflow_concierge/tier_a",
        visual=(
            "StayFlow Concierge Tier A repeat cohort. Build a polished commercial "
            "travel booking and concierge product UI with itinerary browsing, stay "
            "selection, guest validation, add-ons, upload, service checks, and role "
            "confirmation. The product should feel like a real customer-facing "
            "travel service, not a state dashboard."
        ),
    ),
    TargetSpec(
        tier="B",
        target_dir=ROOT / "targets/web/stayflow_concierge/tier_b",
        visual=(
            "StayFlow Concierge Tier B repeat cohort. Build a polished commercial "
            "multi-city travel concierge operations UI with ordered itinerary legs, "
            "quote operations, traveler manifest upload, role-gated ops checklist, "
            "persistence, and full journey confirmation. The product should feel "
            "like a real premium travel operations service, not a state dashboard."
        ),
    ),
    TargetSpec(
        tier="C",
        target_dir=ROOT / "targets/web/stayflow_concierge/tier_c",
        visual=(
            "StayFlow Concierge Tier C repeat cohort. Build a polished commercial "
            "consumer travel booking product UI comparable in care and finish to a "
            "premium hotel/travel marketplace: destination discovery, curated stay "
            "cards with rich visual hierarchy, guest/document readiness, concierge "
            "partner availability, secure checkout, and reservation confirmation. "
            "The product must feel like a real customer-facing travel service, not "
            "an internal command console or bare state dashboard, while keeping all "
            "DetoxBench selectors directly actionable and implementing the public "
            "DSL behavior exactly."
        ),
    ),
    TargetSpec(
        tier="D",
        target_dir=ROOT / "targets/web/stayflow_concierge/tier_d",
        visual=(
            "StayFlow Concierge Tier D repeat cohort. Build a polished commercial "
            "premium travel release war-room UI comparable to the reference target "
            "quality. Follow the contract app.ui_ux_brief exactly: rich travel "
            "discovery, route economics, traveler/document readiness, supplier "
            "version control, payment authorization, manager approval, final "
            "booking confirmation, and the post-confirmation release-seal ledger "
            "must feel like one production service. Implement the public DSL "
            "behavior exactly, keep all DetoxBench selectors directly actionable, "
            "and keep rendered table/list cells synchronized with public state."
        ),
    ),
]


MODELS = [
    ModelSpec("M", "gpt54_nano", "openai", "gpt-5.4-nano", max_output_tokens=48000),
    ModelSpec("M", "claude_haiku45", "anthropic", "claude-haiku-4-5", max_output_tokens=48000, base_url="https://api.anthropic.com", request_timeout=600),
    ModelSpec("M", "gemini31_flash_lite", "google", "gemini-3.1-flash-lite"),
    ModelSpec("T", "gpt54_mini", "openai", "gpt-5.4-mini"),
    ModelSpec("T", "claude_sonnet46", "anthropic", "claude-sonnet-4-6", max_output_tokens=48000, base_url="https://api.anthropic.com", request_timeout=600),
    ModelSpec("T", "gemini_flash_latest", "google", "gemini-flash-latest", max_output_tokens=48000),
    ModelSpec("F", "gpt54", "openai", "gpt-5.4", max_output_tokens=80000, request_timeout=1200),
    ModelSpec("F", "claude_opus46", "anthropic", "claude-opus-4-6", max_output_tokens=80000, base_url="https://api.anthropic.com", request_timeout=1200),
    ModelSpec("F", "gemini31_pro_preview", "google", "gemini-3.1-pro-preview", max_output_tokens=80000, request_timeout=1200),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 10x StayFlow blind repeat cohorts.")
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument(
        "--batch-id",
        default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        help="Output batch id. Defaults to current UTC timestamp.",
    )
    parser.add_argument("--generation-workers", type=int, default=6)
    parser.add_argument("--evaluation-workers", type=int, default=3)
    parser.add_argument(
        "--targets",
        nargs="+",
        choices=["A", "B", "C", "D"],
        default=["A", "B"],
        help="StayFlow target tiers to run.",
    )
    parser.add_argument(
        "--model-tiers",
        nargs="+",
        choices=["M", "T", "F"],
        default=["M", "T", "F"],
        help="Model tiers to run.",
    )
    parser.add_argument(
        "--model-slugs",
        nargs="+",
        help="Optional exact model slugs to run, e.g. gemini31_flash_lite gemini_flash_latest.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "targets/web/stayflow_concierge/cohorts/_batches",
    )
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    batch_root = (args.output_root / args.batch_id).resolve()
    batch_root.mkdir(parents=True, exist_ok=True)
    tasks = build_tasks(args, batch_root)

    manifest = {
        "batch_id": args.batch_id,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "repetitions": args.repetitions,
        "generation_workers": args.generation_workers,
        "evaluation_workers": args.evaluation_workers,
        "tasks": [task_manifest(task) for task in tasks],
    }
    write_json(batch_root / "manifest.json", manifest)

    progress_path = batch_root / "progress.jsonl"
    print(f"Batch: {batch_root}")
    print(f"Tasks: {len(tasks)}")

    with ThreadPoolExecutor(max_workers=args.generation_workers) as pool:
        futures = {pool.submit(generate_task, task): task for task in tasks}
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(progress_path, {"phase": "generate", **record})
            print(status_line("generate", record), flush=True)

    generated = [task for task in tasks if generation_ok(task)]
    print(f"Generated candidates ready for evaluation: {len(generated)} / {len(tasks)}")

    with ThreadPoolExecutor(max_workers=args.evaluation_workers) as pool:
        futures = {pool.submit(evaluate_task, task): task for task in generated}
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(progress_path, {"phase": "evaluate", **record})
            print(status_line("evaluate", record), flush=True)

    aggregate = aggregate_results(batch_root, tasks)
    write_json(batch_root / "aggregate.json", aggregate)
    (batch_root / "README.md").write_text(render_markdown(aggregate), encoding="utf-8")
    print(f"Aggregate: {batch_root / 'aggregate.json'}")
    print(f"Report: {batch_root / 'README.md'}")
    return 0


def build_tasks(args: argparse.Namespace, batch_root: Path) -> list[dict[str, Any]]:
    selected_targets = [target for target in TARGETS if target.tier in set(args.targets)]
    selected_models = [model for model in MODELS if model.model_tier in set(args.model_tiers)]
    if getattr(args, "model_slugs", None):
        selected_models = [model for model in selected_models if model.slug in set(args.model_slugs)]
    tasks = []
    for target in selected_targets:
        for model in selected_models:
            for rep in range(1, args.repetitions + 1):
                subject = f"repeat_tier_{target.tier.lower()}_{model.model_tier.lower()}_{model.slug}_r{rep:02d}"
                tier_batch_root = target.target_dir / "cohorts" / model.model_tier / batch_root.name
                candidate_dir = tier_batch_root / "candidates" / model.slug / f"r{rep:02d}"
                eval_dir = tier_batch_root / "runs" / model.slug / f"r{rep:02d}"
                tasks.append(
                    {
                        "target_tier": target.tier,
                        "model_tier": model.model_tier,
                        "slug": model.slug,
                        "provider": model.provider,
                        "model": model.model,
                        "base_url": model.base_url,
                        "max_output_tokens": model.max_output_tokens,
                        "request_timeout": model.request_timeout,
                        "max_retries": args.max_retries,
                        "rep": rep,
                        "subject": subject,
                        "target_dir": target.target_dir,
                        "contract": target.target_dir / "contract.dsl.yaml",
                        "public_scenarios": target.target_dir / "scenarios.public.dsl.yaml",
                        "candidate_dir": candidate_dir,
                        "eval_dir": eval_dir,
                        "variant": (
                            f"{target.visual} This is repetition {rep:02d} for "
                            f"Model Tier {model.model_tier}; do not use scenarios or "
                            "hard-code expected test answers."
                        ),
                    }
                )
    return tasks


def task_manifest(task: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in task.items():
        result[key] = str(value) if isinstance(value, Path) else value
    return result


def generate_task(task: dict[str, Any]) -> dict[str, Any]:
    if generation_ok(task):
        return task_record(task, status="skipped_existing")

    result = None
    max_retries = int(task.get("max_retries", 1))
    for attempt in range(1, max_retries + 1):
        timeout = int(task["request_timeout"]) * (1 if attempt == 1 else 2)
        max_tokens = int(task["max_output_tokens"]) * (1 if attempt == 1 else 2)
        if attempt > 1:
            for name in ("index.html", "styles.css", "app.js", "generation.json"):
                partial = task["candidate_dir"] / name
                if partial.exists():
                    partial.unlink()

        cmd = [
            sys.executable,
            str(ROOT / "tools/generate_blind_dsl_static_app.py"),
            "--contract-dsl",
            str(task["contract"]),
            "--public-scenarios-dsl",
            str(task["public_scenarios"]),
            "--output-dir",
            str(task["candidate_dir"]),
            "--variant",
            task["variant"],
            "--provider",
            task["provider"],
            "--model",
            task["model"],
            "--max-output-tokens",
            str(max_tokens),
            "--request-timeout",
            str(timeout),
            "--member-id",
            task["subject"],
            "--metadata-output",
            str(task["candidate_dir"] / "generation.json"),
        ]
        if task["base_url"]:
            cmd.extend(["--base-url", task["base_url"]])

        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode == 0 and generation_ok(task):
            return task_record(
                task,
                status="ok",
                attempts=attempt,
                returncode=result.returncode,
                stdout_tail=tail(result.stdout),
                stderr_tail=tail(result.stderr),
            )
        if attempt < max_retries:
            print(
                f"  [retry] tier={task['target_tier']} group={task['model_tier']} "
                f"model={task['slug']} rep={task['rep']:02d} attempt={attempt}",
                flush=True,
            )

    assert result is not None
    return task_record(
        task,
        status="failed",
        attempts=max_retries,
        returncode=result.returncode,
        stdout_tail=tail(result.stdout),
        stderr_tail=tail(result.stderr),
    )


def evaluate_task(task: dict[str, Any]) -> dict[str, Any]:
    summary = latest_summary(task["eval_dir"])
    if summary:
        return eval_record(task, summary, status="skipped_existing")

    cmd = [
        sys.executable,
        "-m",
        "detoxbench",
        "evaluate-dsl",
        "--target",
        str(task["target_dir"]),
        "--scenario-set",
        "all",
        "--static-dir",
        str(task["candidate_dir"]),
        "--output",
        str(task["eval_dir"]),
        "--run-subject",
        task["subject"],
        "--headless",
        "--json",
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    summary = latest_summary(task["eval_dir"])
    if summary:
        return eval_record(
            task,
            summary,
            status="ok",
            returncode=result.returncode,
            stdout_tail=tail(result.stdout),
            stderr_tail=tail(result.stderr),
        )
    return task_record(
        task,
        status="failed",
        returncode=result.returncode,
        stdout_tail=tail(result.stdout),
        stderr_tail=tail(result.stderr),
    )


def generation_ok(task: dict[str, Any]) -> bool:
    candidate_dir = task["candidate_dir"]
    return all((candidate_dir / name).exists() for name in ("index.html", "styles.css", "app.js", "generation.json"))


def latest_summary(eval_dir: Path) -> dict[str, Any] | None:
    summaries = sorted(eval_dir.glob("*/summary.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for summary_path in summaries:
        try:
            return json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Some long browser traces were interrupted while the JSON report was
            # being written. Treat those artifacts as absent so the same
            # candidate can be evaluated again.
            continue
    return None


def task_record(task: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "target_tier": task["target_tier"],
        "model_tier": task["model_tier"],
        "slug": task["slug"],
        "model": task["model"],
        "rep": task["rep"],
        "subject": task["subject"],
        "candidate_dir": str(task["candidate_dir"]),
        "eval_dir": str(task["eval_dir"]),
        **extra,
    }


def eval_record(task: dict[str, Any], summary: dict[str, Any], **extra: Any) -> dict[str, Any]:
    score = summary.get("score", {})
    scenarios = summary.get("scenarios", [])
    first_failure = next((scenario.get("id") for scenario in scenarios if not scenario.get("passed")), None)
    return {
        **task_record(task),
        "run_id": summary.get("run_id"),
        "passed": summary.get("passed"),
        "scenarios_passed": sum(1 for scenario in scenarios if scenario.get("passed")),
        "scenarios_total": len(scenarios),
        "formal_ratio": safe_get(score, "formal", "ratio"),
        "stepwise_ratio": safe_get(score, "stepwise", "ratio"),
        "contract_ratio": safe_get(score, "contract", "ratio"),
        "first_failure": first_failure,
        "failure_breakdown": score.get("failure_breakdown", {}),
        "summary_path": str(Path(summary.get("output_dir", "")) / "summary.json"),
        **extra,
    }


def aggregate_results(batch_root: Path, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for task in tasks:
        summary = latest_summary(task["eval_dir"])
        if summary:
            rows.append(eval_record(task, summary, status="ok"))
        else:
            rows.append(task_record(task, status="missing_eval" if generation_ok(task) else "missing_generation"))

    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = f"tier_{row['target_tier']}/model_tier_{row['model_tier']}/{row['slug']}"
        groups.setdefault(key, []).append(row)

    group_stats = []
    for key, group_rows in sorted(groups.items()):
        evaluated = [row for row in group_rows if row.get("formal_ratio") is not None]
        group_stats.append(
            {
                "group": key,
                "target_tier": group_rows[0]["target_tier"],
                "model_tier": group_rows[0]["model_tier"],
                "slug": group_rows[0]["slug"],
                "model": group_rows[0]["model"],
                "runs": len(group_rows),
                "evaluated": len(evaluated),
                "generation_or_eval_missing": len(group_rows) - len(evaluated),
                "scenario_pass_mean": mean([row.get("scenarios_passed") for row in evaluated]),
                "scenario_pass_sd": stdev([row.get("scenarios_passed") for row in evaluated]),
                "formal_mean": mean([row.get("formal_ratio") for row in evaluated]),
                "formal_sd": stdev([row.get("formal_ratio") for row in evaluated]),
                "stepwise_mean": mean([row.get("stepwise_ratio") for row in evaluated]),
                "stepwise_sd": stdev([row.get("stepwise_ratio") for row in evaluated]),
                "contract_mean": mean([row.get("contract_ratio") for row in evaluated]),
                "contract_sd": stdev([row.get("contract_ratio") for row in evaluated]),
                "first_failures": top_counts([row.get("first_failure") for row in evaluated if row.get("first_failure")]),
            }
        )

    tier_group_stats = []
    for target_tier in sorted({row["target_tier"] for row in rows}):
        for model_tier in sorted({row["model_tier"] for row in rows}):
            evaluated = [
                row
                for row in rows
                if row["target_tier"] == target_tier
                and row["model_tier"] == model_tier
                and row.get("formal_ratio") is not None
            ]
            if not evaluated:
                continue
            tier_group_stats.append(
                {
                    "target_tier": target_tier,
                    "model_tier": model_tier,
                    "evaluated": len(evaluated),
                    "formal_mean": mean([row.get("formal_ratio") for row in evaluated]),
                    "formal_sd": stdev([row.get("formal_ratio") for row in evaluated]),
                    "stepwise_mean": mean([row.get("stepwise_ratio") for row in evaluated]),
                    "stepwise_sd": stdev([row.get("stepwise_ratio") for row in evaluated]),
                    "contract_mean": mean([row.get("contract_ratio") for row in evaluated]),
                    "contract_sd": stdev([row.get("contract_ratio") for row in evaluated]),
                }
            )

    return {
        "batch_root": str(batch_root),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "total_tasks": len(tasks),
        "evaluated": sum(1 for row in rows if row.get("formal_ratio") is not None),
        "rows": rows,
        "model_stats": group_stats,
        "tier_group_stats": tier_group_stats,
    }


def render_markdown(aggregate: dict[str, Any]) -> str:
    lines = [
        "# StayFlow Repeat Cohort",
        "",
        f"Batch root: `{aggregate['batch_root']}`",
        "",
        f"Evaluated: {aggregate['evaluated']} / {aggregate['total_tasks']}",
        "",
        "## Tier x Model Group",
        "",
        "| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate["tier_group_stats"]:
        lines.append(
            "| {target_tier} | {model_tier} | {evaluated} | {formal_mean:.3f} ± {formal_sd:.3f} | "
            "{stepwise_mean:.3f} ± {stepwise_sd:.3f} | {contract_mean:.3f} ± {contract_sd:.3f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Model Detail",
            "",
            "| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |",
            "|---|---:|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in aggregate["model_stats"]:
        lines.append(
            "| {target_tier} | {model_tier} | `{model}` | {evaluated}/{runs} | "
            "{scenario_pass_mean:.2f} ± {scenario_pass_sd:.2f} | "
            "{formal_mean:.3f} ± {formal_sd:.3f} | "
            "{stepwise_mean:.3f} ± {stepwise_sd:.3f} | "
            "{contract_mean:.3f} ± {contract_sd:.3f} | {failures} |".format(
                failures=", ".join(f"{k} ({v})" for k, v in row["first_failures"].items()) or "-",
                **row,
            )
        )
    return "\n".join(lines) + "\n"


def safe_get(mapping: dict[str, Any], *path: str) -> Any:
    current: Any = mapping
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def mean(values: list[Any]) -> float:
    numbers = [float(value) for value in values if value is not None]
    return statistics.fmean(numbers) if numbers else 0.0


def stdev(values: list[Any]) -> float:
    numbers = [float(value) for value in values if value is not None]
    return statistics.stdev(numbers) if len(numbers) > 1 else 0.0


def top_counts(values: list[str], limit: int = 3) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit])


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def tail(text: str, limit: int = 2000) -> str:
    return text[-limit:] if len(text) > limit else text


def status_line(phase: str, record: dict[str, Any]) -> str:
    prefix = (
        f"[{phase}] tier={record['target_tier']} group={record['model_tier']} "
        f"model={record['slug']} rep={record['rep']:02d} status={record.get('status')}"
    )
    if phase == "evaluate" and record.get("formal_ratio") is not None:
        return (
            f"{prefix} scenarios={record.get('scenarios_passed')}/{record.get('scenarios_total')} "
            f"formal={record.get('formal_ratio'):.3f} stepwise={record.get('stepwise_ratio'):.3f} "
            f"contract={record.get('contract_ratio'):.3f}"
        )
    if record.get("returncode") not in (None, 0):
        return f"{prefix} returncode={record.get('returncode')}"
    return prefix


if __name__ == "__main__":
    raise SystemExit(main())
