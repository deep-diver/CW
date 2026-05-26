"""FreshCart Market Tier A — 10× repeat cohort batch runner.

Runs all 9 models (M/T/F × openai/anthropic/google) × 10 repetitions = 90 tasks.
Generates blind candidates, evaluates against all scenarios, and aggregates
mean/std per model.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ModelSpec:
    model_tier: str
    slug: str
    provider: str
    model: str
    max_output_tokens: int = 48000
    base_url: str | None = None
    request_timeout: int = 600


TARGET_DIR = ROOT / "targets/web/freshcart_market/tier_a"
CONTRACT = TARGET_DIR / "contract.dsl.yaml"

VARIANT = (
    "FreshCart Market Tier A blind cohort. Build a polished commercial fresh "
    "grocery delivery service product UI with product catalog browsing, category "
    "filtering, add-to-cart actions, shopping cart with real-time order summary, "
    "coupon validation, delivery time slot selection, customer checkout, order "
    "placement, and receipt history with staff cancellation. The product must feel "
    "like a genuine consumer-facing grocery delivery service comparable to "
    "\ub9c8\ucf13\ucf5c\ub9ac or Instacart \u2014 with a clean modern visual design, green accent "
    "colors, product cards showing real grocery items, and responsive layout. It "
    "must NOT look like an internal dashboard, bare state manager, or developer "
    "debug tool. Keep all DetoxBench selectors directly actionable and implement "
    "the public DSL behavior exactly."
)

MODELS = [
    # Tier M
    ModelSpec("M", "gpt54_nano", "openai", "gpt-5.4-nano", max_output_tokens=48000),
    ModelSpec("M", "claude_haiku45", "anthropic", "claude-haiku-4-5", max_output_tokens=48000, base_url="https://api.anthropic.com", request_timeout=600),
    ModelSpec("M", "gemini31_flash_lite", "google", "gemini-3.1-flash-lite"),
    # Tier T
    ModelSpec("T", "gpt54_mini", "openai", "gpt-5.4-mini", max_output_tokens=48000),
    ModelSpec("T", "claude_sonnet46", "anthropic", "claude-sonnet-4-6", max_output_tokens=48000, base_url="https://api.anthropic.com", request_timeout=600),
    ModelSpec("T", "gemini_flash_latest", "google", "gemini-flash-latest", max_output_tokens=48000),
    # Tier F
    ModelSpec("F", "gpt54", "openai", "gpt-5.4", max_output_tokens=64000, request_timeout=900),
    ModelSpec("F", "claude_opus46", "anthropic", "claude-opus-4-6", max_output_tokens=64000, base_url="https://api.anthropic.com", request_timeout=900),
    ModelSpec("F", "gemini31_pro_preview", "google", "gemini-3.1-pro-preview", max_output_tokens=64000, request_timeout=900),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 10x FreshCart Market Tier A blind repeat cohorts.")
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--batch-id", default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--generation-workers", type=int, default=6)
    parser.add_argument("--evaluation-workers", type=int, default=3)
    parser.add_argument("--model-tiers", nargs="+", choices=["M", "T", "F"], default=["M", "T", "F"])
    parser.add_argument("--output-root", type=Path, default=TARGET_DIR / "cohorts" / "_batches")
    parser.add_argument("--max-retries", type=int, default=3)
    return parser.parse_args()


# ---------- helpers ----------

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def generation_ok(task: dict) -> bool:
    candidate_dir: Path = task["candidate_dir"]
    if not candidate_dir.is_dir():
        return False
    for name in ("index.html", "styles.css", "app.js"):
        p = candidate_dir / name
        if not p.is_file() or p.stat().st_size < 50:
            return False
    # Check that __DETOX_STATE__ is present
    for name in ("index.html", "app.js"):
        text = (candidate_dir / name).read_text(encoding="utf-8", errors="ignore")
        if "__DETOX_STATE__" in text:
            return True
    return False


def latest_summary(eval_dir: Path) -> dict | None:
    for run_dir in sorted(eval_dir.glob("*"), reverse=True):
        summary = run_dir / "summary.json"
        if summary.is_file():
            return json.loads(summary.read_text(encoding="utf-8"))
    return None


def tail(text: str, n: int = 500) -> str:
    lines = text.rstrip().splitlines()
    return "\n".join(lines[-n:])


def task_record(task: dict, **extra: Any) -> dict:
    r = {k: str(v) if isinstance(v, Path) else v for k, v in task.items()}
    r.update(extra)
    return r


def eval_record(task: dict, summary: dict, **extra: Any) -> dict:
    formal = summary.get("score", {}).get("formal", {})
    return task_record(
        task,
        status=extra.pop("status", "ok"),
        formal_earned=formal.get("earned", 0),
        formal_possible=formal.get("possible", 0),
        formal_ratio=formal.get("ratio", 0),
        stepwise_earned=summary.get("score", {}).get("stepwise", {}).get("earned", 0),
        stepwise_ratio=summary.get("score", {}).get("stepwise", {}).get("ratio", 0),
        passed=summary.get("passed", False),
        **extra,
    )


def status_line(phase: str, record: dict) -> str:
    status = record.get("status", "?")
    tier = record.get("model_tier", "?")
    slug = record.get("slug", "?")
    rep = record.get("rep", "?")
    msg = f"[{phase}] {tier}/{slug}/r{rep:02d} → {status}"
    if phase == "evaluate" and status == "ok":
        msg += f"  score={record.get('formal_ratio', 0):.1%}"
    return msg


# ---------- build tasks ----------

def build_tasks(args: argparse.Namespace, batch_root: Path) -> list[dict]:
    selected_models = [m for m in MODELS if m.model_tier in set(args.model_tiers)]
    tasks = []
    for model in selected_models:
        for rep in range(1, args.repetitions + 1):
            subject = f"freshcart_tier_a_{model.model_tier.lower()}_{model.slug}_r{rep:02d}"
            tier_batch_root = TARGET_DIR / "cohorts" / model.model_tier / batch_root.name
            candidate_dir = tier_batch_root / "candidates" / model.slug / f"r{rep:02d}"
            eval_dir = tier_batch_root / "runs" / model.slug / f"r{rep:02d}"
            tasks.append({
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
                "candidate_dir": candidate_dir,
                "eval_dir": eval_dir,
                "variant": f"{VARIANT} This is repetition {rep:02d} for Model Tier {model.model_tier}; do not use scenarios or hard-code expected test answers.",
            })
    return tasks


# ---------- generate ----------

def generate_task(task: dict, max_retries: int = 3) -> dict:
    if generation_ok(task):
        return task_record(task, status="skipped_existing")

    for attempt in range(1, max_retries + 1):
        timeout = task["request_timeout"] * (1 if attempt == 1 else 2)
        max_tokens = task["max_output_tokens"]
        # On retry > 1, bump tokens
        if attempt > 1:
            max_tokens = int(max_tokens * 1.5)

        cmd = [
            sys.executable,
            str(ROOT / "tools/generate_blind_dsl_static_app.py"),
            "--contract-dsl", str(task["contract"]),
            "--output-dir", str(task["candidate_dir"]),
            "--variant", task["variant"],
            "--provider", task["provider"],
            "--model", task["model"],
            "--max-output-tokens", str(max_tokens),
            "--request-timeout", str(timeout),
            "--member-id", task["subject"],
            "--metadata-output", str(task["candidate_dir"] / "generation.json"),
        ]
        if task["base_url"]:
            cmd.extend(["--base-url", task["base_url"]])

        # Clean partial output before retry
        if attempt > 1:
            for f in ("index.html", "styles.css", "app.js"):
                p = task["candidate_dir"] / f
                if p.exists():
                    p.unlink()

        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)

        if result.returncode == 0 and generation_ok(task):
            return task_record(
                task, status="ok",
                attempts=attempt,
                returncode=result.returncode,
                stdout_tail=tail(result.stdout),
                stderr_tail=tail(result.stderr),
            )

        # Check if it was a timeout or truncation
        err = (result.stderr or "") + (result.stdout or "")
        is_timeout = "timeout" in err.lower() or "timed out" in err.lower()
        is_truncated = "finish_reason" in err and "length" in err

        if attempt < max_retries:
            reason = "timeout" if is_timeout else ("truncated" if is_truncated else "failed")
            print(f"  [retry] {task['slug']}/r{task['rep']:02d} attempt {attempt} {reason}, retrying...", flush=True)

    return task_record(
        task, status="failed",
        attempts=max_retries,
        returncode=result.returncode,
        stdout_tail=tail(result.stdout),
        stderr_tail=tail(result.stderr),
    )


# ---------- evaluate ----------

def evaluate_task(task: dict) -> dict:
    summary = latest_summary(task["eval_dir"])
    if summary:
        return eval_record(task, summary, status="skipped_existing")

    cmd = [
        sys.executable, "-m", "detoxbench", "evaluate-dsl",
        "--target", str(task["target_dir"]),
        "--scenario-set", "all",
        "--static-dir", str(task["candidate_dir"]),
        "--output", str(task["eval_dir"]),
        "--run-subject", task["subject"],
        "--headless",
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)

    summary = latest_summary(task["eval_dir"])
    if summary:
        return eval_record(task, summary, status="ok")

    return task_record(
        task, status="eval_failed",
        returncode=result.returncode,
        stdout_tail=tail(result.stdout),
        stderr_tail=tail(result.stderr),
    )


# ---------- aggregate ----------

def aggregate_results(batch_root: Path, tasks: list[dict]) -> dict:
    progress_path = batch_root / "progress.jsonl"
    gen_records: list[dict] = []
    eval_records: list[dict] = []
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("phase") == "generate":
                gen_records.append(rec)
            elif rec.get("phase") == "evaluate":
                eval_records.append(rec)

    by_model: dict[str, list[dict]] = {}
    for rec in eval_records:
        if rec.get("status") not in ("ok", "skipped_existing"):
            continue
        key = f"{rec['model_tier']}_{rec['slug']}"
        by_model.setdefault(key, []).append(rec)

    model_summaries = []
    for key in sorted(by_model):
        recs = by_model[key]
        ratios = [r["formal_ratio"] for r in recs]
        stepwise = [r.get("stepwise_ratio", 0) for r in recs]
        earned = [r["formal_earned"] for r in recs]
        possible = recs[0]["formal_possible"] if recs else 0
        passed_counts = sum(1 for r in recs if r.get("passed"))

        model_summaries.append({
            "key": key,
            "model_tier": recs[0]["model_tier"],
            "slug": recs[0]["slug"],
            "provider": recs[0]["provider"],
            "model": recs[0]["model"],
            "n": len(recs),
            "mean_ratio": statistics.mean(ratios) if ratios else 0,
            "std_ratio": statistics.stdev(ratios) if len(ratios) > 1 else 0,
            "mean_stepwise": statistics.mean(stepwise) if stepwise else 0,
            "std_stepwise": statistics.stdev(stepwise) if len(stepwise) > 1 else 0,
            "mean_earned": statistics.mean(earned) if earned else 0,
            "possible": possible,
            "full_pass_count": passed_counts,
        })

    gen_ok = sum(1 for r in gen_records if r.get("status") in ("ok", "skipped_existing"))
    gen_total = len(gen_records)
    eval_ok = sum(1 for r in eval_records if r.get("status") in ("ok", "skipped_existing"))
    eval_total = len(eval_records)

    return {
        "batch_id": batch_root.name,
        "generated": gen_ok,
        "generation_total": gen_total,
        "evaluated": eval_ok,
        "evaluation_total": eval_total,
        "models": model_summaries,
    }


def render_markdown(agg: dict) -> str:
    lines = [
        f"# FreshCart Market Tier A — Repeat Cohort",
        f"",
        f"**Batch:** `{agg['batch_id']}`",
        f"",
        f"## Generation",
        f"",
        f"- Generated: {agg['generated']}/{agg['generation_total']}",
        f"- Evaluated: {agg['evaluated']}/{agg['evaluation_total']}",
        f"",
        f"## Results by Model",
        f"",
        f"| Tier | Model | Provider | N | Mean Score | Std | Mean Stepwise | Std | Full Pass |",
        f"|------|-------|----------|---|-----------|-----|--------------|-----|-----------|",
    ]
    for m in agg["models"]:
        lines.append(
            f"| {m['model_tier']} | {m['model']} | {m['provider']} | {m['n']} "
            f"| {m['mean_ratio']:.1%} | {m['std_ratio']:.1%} "
            f"| {m['mean_stepwise']:.1%} | {m['std_stepwise']:.1%} "
            f"| {m['full_pass_count']}/{m['n']} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------- main ----------

def main() -> int:
    args = parse_args()
    batch_root = (args.output_root / args.batch_id).resolve()
    batch_root.mkdir(parents=True, exist_ok=True)
    tasks = build_tasks(args, batch_root)

    manifest = {
        "batch_id": args.batch_id,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "repetitions": args.repetitions,
        "target": "freshcart_market_tier_a",
        "generation_workers": args.generation_workers,
        "evaluation_workers": args.evaluation_workers,
        "tasks": [task_record(t) for t in tasks],
    }
    write_json(batch_root / "manifest.json", manifest)

    progress_path = batch_root / "progress.jsonl"
    print(f"Batch: {batch_root}")
    print(f"Tasks: {len(tasks)} (generate + evaluate)")

    # Phase 1: Generate
    print(f"\n=== Phase 1: Generation ({args.generation_workers} workers) ===")
    with ThreadPoolExecutor(max_workers=args.generation_workers) as pool:
        futures = {pool.submit(generate_task, t, args.max_retries): t for t in tasks}
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(progress_path, {"phase": "generate", **record})
            print(status_line("generate", record), flush=True)

    generated = [t for t in tasks if generation_ok(t)]
    print(f"\nGenerated: {len(generated)}/{len(tasks)}")

    # Phase 2: Evaluate
    print(f"\n=== Phase 2: Evaluation ({args.evaluation_workers} workers) ===")
    with ThreadPoolExecutor(max_workers=args.evaluation_workers) as pool:
        futures = {pool.submit(evaluate_task, t): t for t in generated}
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(progress_path, {"phase": "evaluate", **record})
            print(status_line("evaluate", record), flush=True)

    # Phase 3: Aggregate
    print(f"\n=== Phase 3: Aggregation ===")
    aggregate = aggregate_results(batch_root, tasks)
    write_json(batch_root / "aggregate.json", aggregate)
    (batch_root / "README.md").write_text(render_markdown(aggregate), encoding="utf-8")

    print(f"\nAggregate: {batch_root / 'aggregate.json'}")
    print(f"Report: {batch_root / 'README.md'}")
    print("\n" + render_markdown(aggregate))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
