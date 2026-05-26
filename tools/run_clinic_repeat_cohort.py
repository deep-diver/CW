"""Shared helpers for Clinic Shift Command blind repeat cohort runners."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
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
    max_output_tokens: int = 64000
    base_url: str | None = None
    request_timeout: int = 900


MODELS = [
    ModelSpec("M", "gpt54_nano", "openai", "gpt-5.4-nano", max_output_tokens=64000, request_timeout=900),
    ModelSpec(
        "M",
        "claude_haiku45",
        "anthropic",
        "claude-haiku-4-5",
        max_output_tokens=64000,
        base_url="https://api.anthropic.com",
        request_timeout=900,
    ),
    ModelSpec("M", "gemini31_flash_lite", "google", "gemini-3.1-flash-lite", max_output_tokens=64000, request_timeout=900),
    ModelSpec("T", "gpt54_mini", "openai", "gpt-5.4-mini", max_output_tokens=64000, request_timeout=900),
    ModelSpec(
        "T",
        "claude_sonnet46",
        "anthropic",
        "claude-sonnet-4-6",
        max_output_tokens=64000,
        base_url="https://api.anthropic.com",
        request_timeout=900,
    ),
    ModelSpec("T", "gemini_flash_latest", "google", "gemini-flash-latest", max_output_tokens=64000, request_timeout=900),
    ModelSpec("F", "gpt54", "openai", "gpt-5.4", max_output_tokens=80000, request_timeout=1200),
    ModelSpec(
        "F",
        "claude_opus46",
        "anthropic",
        "claude-opus-4-6",
        max_output_tokens=80000,
        base_url="https://api.anthropic.com",
        request_timeout=1200,
    ),
    ModelSpec("F", "gemini31_pro_preview", "google", "gemini-3.1-pro-preview", max_output_tokens=80000, request_timeout=1200),
]


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
