"""FreshCart Market Tier C — M/T/F 10x blind repeat cohort runner."""
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
TARGET_DIR = ROOT / "targets/web/freshcart_market/tier_c"
CONTRACT = TARGET_DIR / "contract.dsl.yaml"
PUBLIC_SCENARIOS = TARGET_DIR / "scenarios.public.dsl.yaml"


@dataclass(frozen=True)
class ModelSpec:
    model_tier: str
    slug: str
    provider: str
    model: str
    max_output_tokens: int = 64000
    base_url: str | None = None
    request_timeout: int = 900


VARIANT = (
    "FreshCart Market Tier C blind cohort. Build a polished, production-quality "
    "cold-chain grocery delivery product UI comparable to the reference target "
    "quality and to premium consumer services such as Market Kurly, Instacart, "
    "or a boutique fresh-food fulfillment app. The app should feel like a real "
    "end-user service, not an internal dashboard, state debugger, or bare test "
    "harness. Use a refined retail visual system, responsive layout, attractive "
    "product cards, clear basket preparation and substitution controls, a clean "
    "checkout experience, credible order operations, and customer support flows. "
    "Implement FreshCart Tier C behavior exactly: cold-chain catalog filtering, "
    "cart economics, preparation services, substitution credit, coupons, wallet "
    "redemption, slot quote service calls, rush delivery, restricted-item "
    "review, staff/manager permissions, fulfillment checklist, support tickets, "
    "reload persistence, and browser route history. Keep all DetoxBench selectors "
    "directly actionable and keep rendered table cells synchronized with public "
    "state. You receive only the public contract and public scenario examples; "
    "do not use private scenarios, evaluator logs, reference screenshots, or "
    "hard-coded hidden answers."
)


MODELS = [
    ModelSpec("M", "gpt54_nano", "openai", "gpt-5.4-nano", max_output_tokens=64000, request_timeout=900),
    ModelSpec("M", "claude_haiku45", "anthropic", "claude-haiku-4-5", max_output_tokens=64000, base_url="https://api.anthropic.com", request_timeout=900),
    ModelSpec("M", "gemini31_flash_lite", "google", "gemini-3.1-flash-lite", max_output_tokens=64000, request_timeout=900),
    ModelSpec("T", "gpt54_mini", "openai", "gpt-5.4-mini", max_output_tokens=64000, request_timeout=900),
    ModelSpec("T", "claude_sonnet46", "anthropic", "claude-sonnet-4-6", max_output_tokens=64000, base_url="https://api.anthropic.com", request_timeout=900),
    ModelSpec("T", "gemini_flash_latest", "google", "gemini-flash-latest", max_output_tokens=64000, request_timeout=900),
    ModelSpec("F", "gpt54", "openai", "gpt-5.4", max_output_tokens=80000, request_timeout=1200),
    ModelSpec("F", "claude_opus46", "anthropic", "claude-opus-4-6", max_output_tokens=80000, base_url="https://api.anthropic.com", request_timeout=1200),
    ModelSpec("F", "gemini31_pro_preview", "google", "gemini-3.1-pro-preview", max_output_tokens=80000, request_timeout=1200),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FreshCart Market Tier C blind repeat cohorts.")
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--batch-id", default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--generation-workers", type=int, default=6)
    parser.add_argument("--evaluation-workers", type=int, default=6)
    parser.add_argument("--model-tiers", nargs="+", choices=["M", "T", "F"], default=["M", "T", "F"])
    parser.add_argument("--output-root", type=Path, default=TARGET_DIR / "cohorts" / "_batches")
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def tail(text: str, n: int = 500) -> str:
    return "\n".join(text.rstrip().splitlines()[-n:])


def generation_ok(task: dict[str, Any]) -> bool:
    candidate_dir: Path = task["candidate_dir"]
    if not candidate_dir.is_dir():
        return False
    for name in ("index.html", "styles.css", "app.js"):
        file_path = candidate_dir / name
        if not file_path.is_file() or file_path.stat().st_size < 50:
            return False
    return any(
        "__DETOX_STATE__" in (candidate_dir / name).read_text(encoding="utf-8", errors="ignore")
        for name in ("index.html", "app.js")
    )


def latest_summary(eval_dir: Path) -> dict[str, Any] | None:
    for run_dir in sorted(eval_dir.glob("*"), reverse=True):
        summary = run_dir / "summary.json"
        if summary.is_file():
            return json.loads(summary.read_text(encoding="utf-8"))
    return None


def task_record(task: dict[str, Any], **extra: Any) -> dict[str, Any]:
    record = {key: str(value) if isinstance(value, Path) else value for key, value in task.items()}
    record.update(extra)
    return record


def eval_record(task: dict[str, Any], summary: dict[str, Any], **extra: Any) -> dict[str, Any]:
    score = summary.get("score", {})
    formal = score.get("formal", {})
    stepwise = score.get("stepwise", {})
    contract = score.get("contract", {})
    scenarios = summary.get("scenarios", [])
    failed = [scenario for scenario in scenarios if not scenario.get("passed")]
    return task_record(
        task,
        status=extra.pop("status", "ok"),
        run_id=summary.get("run_id"),
        output_dir=summary.get("output_dir"),
        formal_ratio=formal.get("ratio", 0),
        formal_earned=formal.get("earned", 0),
        formal_possible=formal.get("possible", 0),
        stepwise_ratio=stepwise.get("ratio", 0),
        contract_ratio=contract.get("ratio", 0),
        scenarios_passed=len(scenarios) - len(failed),
        scenarios_total=len(scenarios),
        passed=summary.get("passed", False),
        first_failure=failed[0].get("id") if failed else None,
        first_failure_category=failed[0].get("failure_category") if failed else None,
        **extra,
    )


def status_line(phase: str, record: dict[str, Any]) -> str:
    status = record.get("status", "?")
    tier = record.get("model_tier", "?")
    slug = record.get("slug", "?")
    rep = record.get("rep", "?")
    message = f"[{phase}] {tier}/{slug}/r{int(rep):02d} -> {status}"
    if phase == "evaluate" and status in {"ok", "skipped_existing"}:
        message += (
            f"  formal={record.get('formal_ratio', 0):.1%}"
            f"  stepwise={record.get('stepwise_ratio', 0):.1%}"
            f"  scenarios={record.get('scenarios_passed', 0)}/{record.get('scenarios_total', 0)}"
        )
    return message


def build_tasks(args: argparse.Namespace, batch_root: Path) -> list[dict[str, Any]]:
    selected_tiers = set(args.model_tiers)
    selected_models = [model for model in MODELS if model.model_tier in selected_tiers]
    tasks: list[dict[str, Any]] = []
    for model in selected_models:
        for rep in range(1, args.repetitions + 1):
            subject = f"freshcart_tier_c_{model.model_tier.lower()}_{model.slug}_r{rep:02d}"
            tier_batch_root = TARGET_DIR / "cohorts" / model.model_tier / batch_root.name
            tasks.append(
                {
                    "model_tier": model.model_tier,
                    "slug": model.slug,
                    "provider": model.provider,
                    "model": model.model,
                    "base_url": model.base_url,
                    "max_output_tokens": model.max_output_tokens,
                    "request_timeout": model.request_timeout,
                    "rep": rep,
                    "subject": subject,
                    "target_dir": TARGET_DIR,
                    "contract": CONTRACT,
                    "public_scenarios": PUBLIC_SCENARIOS,
                    "candidate_dir": tier_batch_root / "candidates" / model.slug / f"r{rep:02d}",
                    "eval_dir": tier_batch_root / "runs" / model.slug / f"r{rep:02d}",
                    "variant": (
                        f"{VARIANT} This is repetition {rep:02d} for Model Tier "
                        f"{model.model_tier} and model {model.slug}."
                    ),
                }
            )
    return tasks


def generate_task(task: dict[str, Any], max_retries: int) -> dict[str, Any]:
    if generation_ok(task):
        return task_record(task, status="skipped_existing")

    result = None
    for attempt in range(1, max_retries + 1):
        timeout = int(task["request_timeout"]) * (1 if attempt == 1 else 2)
        max_tokens = int(task["max_output_tokens"]) * (1 if attempt == 1 else 2)
        if attempt > 1:
            for name in ("index.html", "styles.css", "app.js"):
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
            error_text = (result.stderr or "") + (result.stdout or "")
            reason = "timeout" if "timeout" in error_text.lower() else "failed"
            print(f"  [retry] {task['model_tier']}/{task['slug']}/r{task['rep']:02d} attempt {attempt} {reason}", flush=True)

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
    existing = latest_summary(task["eval_dir"])
    if existing:
        return eval_record(task, existing, status="skipped_existing")
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
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    summary = latest_summary(task["eval_dir"])
    if summary:
        return eval_record(task, summary, status="ok", returncode=result.returncode)
    return task_record(
        task,
        status="eval_failed",
        returncode=result.returncode,
        stdout_tail=tail(result.stdout),
        stderr_tail=tail(result.stderr),
    )


def aggregate_results(batch_root: Path) -> dict[str, Any]:
    progress_path = batch_root / "progress.jsonl"
    records: list[dict[str, Any]] = []
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("phase") == "evaluate" and record.get("status") in {"ok", "skipped_existing"}:
                records.append(record)

    def summarize(group: list[dict[str, Any]]) -> dict[str, Any]:
        formal = [record.get("formal_ratio", 0) for record in group]
        stepwise = [record.get("stepwise_ratio", 0) for record in group]
        contract = [record.get("contract_ratio", 0) for record in group]
        return {
            "n": len(group),
            "formal_mean": statistics.mean(formal) if formal else 0,
            "formal_std": statistics.stdev(formal) if len(formal) > 1 else 0,
            "stepwise_mean": statistics.mean(stepwise) if stepwise else 0,
            "stepwise_std": statistics.stdev(stepwise) if len(stepwise) > 1 else 0,
            "contract_mean": statistics.mean(contract) if contract else 0,
            "contract_std": statistics.stdev(contract) if len(contract) > 1 else 0,
            "full_pass_count": sum(1 for record in group if record.get("passed")),
        }

    by_model: dict[str, list[dict[str, Any]]] = {}
    by_tier: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_model.setdefault(record["slug"], []).append(record)
        by_tier.setdefault(record["model_tier"], []).append(record)

    models = []
    for slug, group in sorted(by_model.items()):
        summary = summarize(group)
        summary.update(
            {
                "model_tier": group[0]["model_tier"],
                "slug": slug,
                "provider": group[0]["provider"],
                "model": group[0]["model"],
            }
        )
        models.append(summary)

    tiers = []
    for tier, group in sorted(by_tier.items()):
        summary = summarize(group)
        summary.update({"model_tier": tier})
        tiers.append(summary)

    generation_records = []
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                if record.get("phase") == "generate":
                    generation_records.append(record)

    return {
        "batch_id": batch_root.name,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "target": "freshcart_market_tier_c",
        "evaluated": len(records),
        "generated": sum(
            1
            for record in generation_records
            if record.get("status") in {"ok", "skipped_existing"}
        ),
        "generation_total": len(generation_records),
        "model_summaries": models,
        "tier_summaries": tiers,
    }


def main() -> int:
    args = parse_args()
    batch_root = (args.output_root / args.batch_id).resolve()
    batch_root.mkdir(parents=True, exist_ok=True)
    tasks = build_tasks(args, batch_root)
    write_json(
        batch_root / "manifest.json",
        {
            "batch_id": args.batch_id,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "target": "freshcart_market_tier_c",
            "target_dir": str(TARGET_DIR),
            "contract": str(CONTRACT),
            "public_scenarios": str(PUBLIC_SCENARIOS),
            "repetitions": args.repetitions,
            "model_tiers": args.model_tiers,
            "generation_workers": args.generation_workers,
            "evaluation_workers": args.evaluation_workers,
            "tasks": [task_record(task) for task in tasks],
        },
    )
    progress_path = batch_root / "progress.jsonl"
    print(f"Batch: {batch_root}")
    print(f"Tasks: {len(tasks)}")

    print(f"\n=== Phase 1: Generation ({args.generation_workers} workers) ===")
    with ThreadPoolExecutor(max_workers=args.generation_workers) as pool:
        futures = {pool.submit(generate_task, task, args.max_retries): task for task in tasks}
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(progress_path, {"phase": "generate", **record})
            print(status_line("generate", record), flush=True)

    generated = [task for task in tasks if generation_ok(task)]
    print(f"\nGenerated: {len(generated)}/{len(tasks)}")

    print(f"\n=== Phase 2: Evaluation ({args.evaluation_workers} workers) ===")
    with ThreadPoolExecutor(max_workers=args.evaluation_workers) as pool:
        futures = {pool.submit(evaluate_task, task): task for task in generated}
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(progress_path, {"phase": "evaluate", **record})
            print(status_line("evaluate", record), flush=True)

    print("\n=== Phase 3: Aggregation ===")
    aggregate = aggregate_results(batch_root)
    write_json(batch_root / "aggregate.json", aggregate)
    print(f"Aggregate: {batch_root / 'aggregate.json'}")
    for item in aggregate["model_summaries"]:
        print(
            f"  {item['model_tier']}/{item['slug']:22s} "
            f"n={item['n']:02d} formal={item['formal_mean']:.1%}±{item['formal_std']:.1%} "
            f"stepwise={item['stepwise_mean']:.1%} full_pass={item['full_pass_count']}/{item['n']}"
        )
    print("Tier-level:")
    for item in aggregate["tier_summaries"]:
        print(
            f"  Tier {item['model_tier']} n={item['n']:02d} "
            f"formal={item['formal_mean']:.1%}±{item['formal_std']:.1%} "
            f"full_pass={item['full_pass_count']}/{item['n']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
