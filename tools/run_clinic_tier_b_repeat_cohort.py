"""Clinic Shift Command Tier B M/T/F 10x blind repeat cohort runner."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
import json
from pathlib import Path
import statistics
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.run_clinic_repeat_cohort import MODELS
from tools.run_clinic_repeat_cohort import append_jsonl
from tools.run_clinic_repeat_cohort import evaluate_task
from tools.run_clinic_repeat_cohort import generate_task
from tools.run_clinic_repeat_cohort import generation_ok
from tools.run_clinic_repeat_cohort import status_line
from tools.run_clinic_repeat_cohort import task_record
from tools.run_clinic_repeat_cohort import write_json


TARGET_DIR = ROOT / "targets/web/clinic_shift_command/tier_b"
CONTRACT = TARGET_DIR / "contract.dsl.yaml"
PUBLIC_SCENARIOS = TARGET_DIR / "scenarios.public.dsl.yaml"
TARGET_ID = "clinic_shift_command_tier_b"


VARIANT = (
    "Clinic Shift Command Tier B blind cohort. Build a polished, production-quality "
    "multi-role ambulatory clinic operations command center comparable to the "
    "reference target quality. Follow the contract app.ui_ux_brief exactly as the "
    "shared visual and interaction quality brief. The app should visibly feel more "
    "complex than Clinic Shift Command Tier A in a desktop screenshot: it should show "
    "queue pressure, selected patient workup, room capacity, prior authorization, "
    "diagnostic orders, referral packet upload, escalations, and shift handoff as a "
    "coordinated clinical SaaS product. It must not look like a grocery app, hotel "
    "app, generic analytics dashboard, landing page, state debugger, or bare test "
    "harness. Implement Clinic Shift Command Tier B behavior exactly: four role "
    "switching, critical/procedure/authorization queue filters, patient selection, "
    "charge-nurse capacity assignment and blocked cleaning rooms, insurance and prior "
    "auth service flows, clinician assessment validation, diagnostic order creation, "
    "diagnostic release only after coverage and prior-auth clearance, CSV referral "
    "upload, escalation creation and closure, final handoff packet creation only "
    "after released diagnostics, uploaded referrals, and closed escalation, rendered "
    "queue/room/order/referral/escalation/handoff-packet tables, browser route "
    "history, and reload persistence. Keep "
    "all DetoxBench selectors directly actionable and keep rendered table/list cells "
    "synchronized with public state. You receive only the public contract and public "
    "scenario examples; do not use private scenarios, evaluator logs, reference "
    "screenshots, or hard-coded hidden answers."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Clinic Shift Command Tier B blind repeat cohorts.")
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--batch-id", default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--generation-workers", type=int, default=9)
    parser.add_argument("--evaluation-workers", type=int, default=9)
    parser.add_argument("--model-tiers", nargs="+", choices=["M", "T", "F"], default=["M", "T", "F"])
    parser.add_argument("--output-root", type=Path, default=TARGET_DIR / "cohorts" / "_batches")
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


def build_tasks(args: argparse.Namespace, batch_root: Path) -> list[dict[str, Any]]:
    selected_tiers = set(args.model_tiers)
    selected_models = [model for model in MODELS if model.model_tier in selected_tiers]
    tasks: list[dict[str, Any]] = []
    for model in selected_models:
        for rep in range(1, args.repetitions + 1):
            subject = f"clinic_shift_tier_b_{model.model_tier.lower()}_{model.slug}_r{rep:02d}"
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
        "target": TARGET_ID,
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
            "target": TARGET_ID,
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
            f"n={item['n']:02d} formal={item['formal_mean']:.1%}+/-{item['formal_std']:.1%} "
            f"stepwise={item['stepwise_mean']:.1%} full_pass={item['full_pass_count']}/{item['n']}"
        )
    print("Tier-level:")
    for item in aggregate["tier_summaries"]:
        print(
            f"  Tier {item['model_tier']} n={item['n']:02d} "
            f"formal={item['formal_mean']:.1%}+/-{item['formal_std']:.1%} "
            f"full_pass={item['full_pass_count']}/{item['n']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
