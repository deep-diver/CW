"""FreshCart Market Tier B — Model Tier T & F 10× repeat cohort runner."""
from __future__ import annotations

import argparse, json, statistics, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class ModelSpec:
    model_tier: str; slug: str; provider: str; model: str
    max_output_tokens: int = 48000; base_url: str | None = None; request_timeout: int = 600

TARGET_DIR = ROOT / "targets/web/freshcart_market/tier_b"
CONTRACT = TARGET_DIR / "contract.dsl.yaml"

VARIANT = (
    "GreenCart Premium — Multi-vendor gourmet food marketplace blind cohort. "
    "Build a polished premium gourmet food delivery service product UI with "
    "vendor-grouped product catalog, persistent cart sidebar, basket review with "
    "item preparation options (sashimi cut, deveined, gift wrap), "
    "coupon validation, loyalty point redemption, express delivery and gift wrap toggles, "
    "4-tier delivery fee, delivery slot selection, customer checkout, order placement "
    "with audit trail, order history with fulfillment checklist (verify, pack, dispatch), "
    "and staff delivery confirmation with 3-gate permission. "
    "The product must feel like a genuine premium food marketplace comparable to "
    "Market Kurly or Instacart — with a deep teal and cream visual theme, gold accents, "
    "product cards showing real grocery items with food emojis, vendor color coding, "
    "delivery progress bar, and responsive layout. It must NOT look like an internal "
    "dashboard, bare state manager, or developer debug tool. Keep all DetoxBench "
    "selectors directly actionable and implement the public DSL behavior exactly. "
    "The app has 4 pages: market, basket, checkout, orders. "
    "IMPORTANT: The contract uses x-derived anchors for reusable state computations. "
    "Derived fields (cart_count, cart_subtotal, delivery_fee, order_total, vendor counts, "
    "service call counts, audit_count) are computed from other state paths, not set directly."
)

MODELS = [
    # Tier T
    ModelSpec("T", "gpt54_mini",            "openai",    "gpt-5.4-mini",         max_output_tokens=48000),
    ModelSpec("T", "claude_sonnet46",        "anthropic", "claude-sonnet-4-6",    max_output_tokens=48000, base_url="https://api.anthropic.com", request_timeout=600),
    ModelSpec("T", "gemini_flash_latest",    "google",    "gemini-flash-latest",  max_output_tokens=48000),
    # Tier F
    ModelSpec("F", "gpt54",                  "openai",    "gpt-5.4",              max_output_tokens=48000, request_timeout=900),
    ModelSpec("F", "claude_opus46",          "anthropic", "claude-opus-4-6",      max_output_tokens=48000, base_url="https://api.anthropic.com", request_timeout=900),
    ModelSpec("F", "gemini31_pro_preview",   "google",    "gemini-3.1-pro-preview", max_output_tokens=48000, request_timeout=900),
]

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--repetitions", type=int, default=10)
    p.add_argument("--batch-id", default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    p.add_argument("--generation-workers", type=int, default=6)
    p.add_argument("--evaluation-workers", type=int, default=3)
    p.add_argument("--output-root", type=Path, default=TARGET_DIR / "cohorts" / "_batches")
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--model-tiers", nargs="+", choices=["T", "F"], default=["T", "F"])
    return p.parse_args()

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def append_jsonl(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def generation_ok(task):
    d = task["candidate_dir"]
    if not d.is_dir(): return False
    for n in ("index.html", "styles.css", "app.js"):
        p = d / n
        if not p.is_file() or p.stat().st_size < 50: return False
    for n in ("index.html", "app.js"):
        if "__DETOX_STATE__" in (d / n).read_text(encoding="utf-8", errors="ignore"): return True
    return False

def latest_summary(eval_dir):
    for run_dir in sorted(eval_dir.glob("*"), reverse=True):
        s = run_dir / "summary.json"
        if s.is_file(): return json.loads(s.read_text(encoding="utf-8"))
    return None

def tail(text, n=500):
    lines = text.rstrip().splitlines()
    return "\n".join(lines[-n:])

def task_record(task, **extra):
    r = {k: str(v) if isinstance(v, Path) else v for k, v in task.items()}
    r.update(extra); return r

def eval_record(task, summary, **extra):
    formal = summary.get("score", {}).get("formal", {})
    scenarios = summary.get("scenarios", [])
    first_failure = next((s.get("id") for s in scenarios if not s.get("passed")), None)
    return task_record(task, status=extra.pop("status", "ok"),
        run_id=summary.get("run_id"),
        formal_ratio=formal.get("ratio", 0),
        stepwise_ratio=summary.get("score", {}).get("stepwise", {}).get("ratio", 0),
        contract_ratio=summary.get("score", {}).get("contract", {}).get("ratio", 0),
        scenarios_passed=sum(1 for s in scenarios if s.get("passed")),
        scenarios_total=len(scenarios),
        passed=summary.get("passed", False),
        first_failure=first_failure,
        **extra)

def status_line(phase, record):
    s = record.get("status", "?"); t = record.get("model_tier", "?")
    sl = record.get("slug", "?"); r = record.get("rep", "?")
    msg = f"[{phase}] {t}/{sl}/r{r:02d} → {s}"
    if phase == "evaluate" and s in ("ok", "skipped_existing") and record.get("formal_ratio") is not None:
        msg += f"  score={record['formal_ratio']:.1%}  stepwise={record.get('stepwise_ratio', 0):.1%}"
    return msg

def build_tasks(args, batch_root):
    selected_models = [m for m in MODELS if m.model_tier in set(args.model_tiers)]
    tasks = []
    for model in selected_models:
        for rep in range(1, args.repetitions + 1):
            subject = f"tierb_{model.model_tier.lower()}_{model.slug}_r{rep:02d}"
            tier_batch_root = TARGET_DIR / "cohorts" / model.model_tier / batch_root.name
            tasks.append({
                "model_tier": model.model_tier, "slug": model.slug,
                "provider": model.provider, "model": model.model,
                "base_url": model.base_url, "max_output_tokens": model.max_output_tokens,
                "request_timeout": model.request_timeout, "rep": rep,
                "subject": subject, "target_dir": TARGET_DIR, "contract": CONTRACT,
                "candidate_dir": tier_batch_root / "candidates" / model.slug / f"r{rep:02d}",
                "eval_dir": tier_batch_root / "runs" / model.slug / f"r{rep:02d}",
                "variant": f"{VARIANT} This is repetition {rep:02d}; do not use scenarios or hard-code expected test answers.",
            })
    return tasks

def generate_task(task, max_retries=3):
    if generation_ok(task): return task_record(task, status="skipped_existing")
    for attempt in range(1, max_retries + 1):
        timeout = task["request_timeout"] * (1 if attempt == 1 else 2)
        max_tokens = task["max_output_tokens"] * (1 if attempt == 1 else 2)
        cmd = [sys.executable, str(ROOT / "tools/generate_blind_dsl_static_app.py"),
            "--contract-dsl", str(task["contract"]), "--output-dir", str(task["candidate_dir"]),
            "--variant", task["variant"], "--provider", task["provider"],
            "--model", task["model"], "--max-output-tokens", str(max_tokens),
            "--request-timeout", str(timeout), "--member-id", task["subject"],
            "--metadata-output", str(task["candidate_dir"] / "generation.json")]
        if task["base_url"]: cmd.extend(["--base-url", task["base_url"]])
        if attempt > 1:
            for f in ("index.html", "styles.css", "app.js"):
                p = task["candidate_dir"] / f
                if p.exists(): p.unlink()
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode == 0 and generation_ok(task):
            return task_record(task, status="ok", attempts=attempt,
                stdout_tail=tail(result.stdout), stderr_tail=tail(result.stderr))
        err = (result.stderr or "") + (result.stdout or "")
        is_timeout = "timeout" in err.lower() or "timed out" in err.lower()
        is_truncated = "finish_reason" in err and "length" in err
        if attempt < max_retries:
            reason = "timeout" if is_timeout else ("truncated" if is_truncated else "failed")
            print(f"  [retry] {task['slug']}/r{task['rep']:02d} attempt {attempt} {reason}", flush=True)
    return task_record(task, status="failed", attempts=max_retries,
        returncode=result.returncode, stdout_tail=tail(result.stdout), stderr_tail=tail(result.stderr))

def evaluate_task(task):
    summary = latest_summary(task["eval_dir"])
    if summary: return eval_record(task, summary, status="skipped_existing")
    cmd = [sys.executable, "-m", "detoxbench", "evaluate-dsl",
        "--target", str(task["target_dir"]), "--scenario-set", "all",
        "--static-dir", str(task["candidate_dir"]), "--output", str(task["eval_dir"]),
        "--run-subject", task["subject"], "--headless"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    summary = latest_summary(task["eval_dir"])
    if summary: return eval_record(task, summary, status="ok")
    return task_record(task, status="eval_failed", returncode=result.returncode,
        stdout_tail=tail(result.stdout), stderr_tail=tail(result.stderr))

def aggregate_results(batch_root, tasks):
    progress_path = batch_root / "progress.jsonl"
    eval_records = []
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            rec = json.loads(line)
            if rec.get("phase") == "evaluate" and rec.get("status") in ("ok", "skipped_existing"):
                eval_records.append(rec)
    by_model = {}
    for rec in eval_records:
        key = rec["slug"]
        by_model.setdefault(key, []).append(rec)
    model_summaries = []
    for key in sorted(by_model):
        recs = by_model[key]
        ratios = [r["formal_ratio"] for r in recs]
        stepwise = [r.get("stepwise_ratio", 0) for r in recs]
        contract = [r.get("contract_ratio", 0) for r in recs]
        model_summaries.append({
            "key": key, "model_tier": recs[0]["model_tier"], "slug": recs[0]["slug"],
            "provider": recs[0]["provider"], "model": recs[0]["model"],
            "n": len(recs), "mean_ratio": statistics.mean(ratios) if ratios else 0,
            "std_ratio": statistics.stdev(ratios) if len(ratios) > 1 else 0,
            "mean_stepwise": statistics.mean(stepwise) if stepwise else 0,
            "std_stepwise": statistics.stdev(stepwise) if len(stepwise) > 1 else 0,
            "mean_contract": statistics.mean(contract) if contract else 0,
            "std_contract": statistics.stdev(contract) if len(contract) > 1 else 0,
            "full_pass_count": sum(1 for r in recs if r.get("passed")),
        })
    # tier-level aggregation
    tier_stats = []
    for mt in sorted({r["model_tier"] for r in eval_records}):
        tier_recs = [r for r in eval_records if r["model_tier"] == mt]
        ratios = [r["formal_ratio"] for r in tier_recs]
        tier_stats.append({
            "model_tier": mt, "n": len(tier_recs),
            "mean_ratio": statistics.mean(ratios) if ratios else 0,
            "std_ratio": statistics.stdev(ratios) if len(ratios) > 1 else 0,
        })
    return {
        "batch_id": batch_root.name,
        "generated": sum(1 for r in eval_records),
        "models": model_summaries,
        "tier_stats": tier_stats,
    }

def main():
    args = parse_args()
    batch_root = (args.output_root / args.batch_id).resolve()
    batch_root.mkdir(parents=True, exist_ok=True)
    tasks = build_tasks(args, batch_root)
    write_json(batch_root / "manifest.json", {
        "batch_id": args.batch_id, "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "repetitions": args.repetitions, "target": "freshcart_market_tier_b",
        "model_tiers": args.model_tiers,
        "generation_workers": args.generation_workers,
        "tasks": [task_record(t) for t in tasks],
    })
    progress_path = batch_root / "progress.jsonl"
    print(f"Batch: {batch_root}\nTasks: {len(tasks)}")

    print(f"\n=== Phase 1: Generation ({args.generation_workers} workers) ===")
    with ThreadPoolExecutor(max_workers=args.generation_workers) as pool:
        futures = {pool.submit(generate_task, t, args.max_retries): t for t in tasks}
        for f in as_completed(futures):
            record = f.result()
            append_jsonl(progress_path, {"phase": "generate", **record})
            print(status_line("generate", record), flush=True)

    generated = [t for t in tasks if generation_ok(t)]
    print(f"\nGenerated: {len(generated)}/{len(tasks)}")

    print(f"\n=== Phase 2: Evaluation ({args.evaluation_workers} workers) ===")
    with ThreadPoolExecutor(max_workers=args.evaluation_workers) as pool:
        futures = {pool.submit(evaluate_task, t): t for t in generated}
        for f in as_completed(futures):
            record = f.result()
            append_jsonl(progress_path, {"phase": "evaluate", **record})
            print(status_line("evaluate", record), flush=True)

    print(f"\n=== Phase 3: Aggregation ===")
    aggregate = aggregate_results(batch_root, tasks)
    write_json(batch_root / "aggregate.json", aggregate)
    print(f"\nAggregate: {batch_root / 'aggregate.json'}")
    for m in aggregate["models"]:
        print(f"  {m['slug']:25s} | n={m['n']} | formal={m['mean_ratio']:.1%}±{m['std_ratio']:.1%} | stepwise={m['mean_stepwise']:.1%} | contract={m['mean_contract']:.1%}")
    print("\nTier-level:")
    for t in aggregate["tier_stats"]:
        print(f"  Tier {t['model_tier']}: n={t['n']} | mean={t['mean_ratio']:.1%}±{t['std_ratio']:.1%}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
