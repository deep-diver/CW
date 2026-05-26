from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import run_stayflow_repeat_cohort as base  # noqa: E402


TARGETS = [
    base.TargetSpec(
        tier="A",
        target_dir=ROOT / "targets/web/campus_registrar_command/tier_a",
        visual=(
            "Campus Registrar Command Tier A repeat cohort. Build a polished "
            "student-facing registration and advising product with course search, "
            "schedule planning, prerequisite feedback, enrollment state, and clear "
            "confirmation surfaces. The result should feel like a real university "
            "registration service, not a bare test dashboard."
        ),
    ),
    base.TargetSpec(
        tier="B",
        target_dir=ROOT / "targets/web/campus_registrar_command/tier_b",
        visual=(
            "Campus Registrar Command Tier B repeat cohort. Build a polished "
            "registrar operations product with waitlist review, capacity and "
            "section management, student record queues, rendered operational "
            "tables, and staff workflow controls. Keep every declared selector "
            "directly actionable and every public state projection synchronized."
        ),
    ),
    base.TargetSpec(
        tier="C",
        target_dir=ROOT / "targets/web/campus_registrar_command/tier_c",
        visual=(
            "Campus Registrar Command Tier C repeat cohort. Build a polished "
            "policy-sensitive registrar command product with role-gated approvals, "
            "appeal or document handling, deterministic service checks, persistent "
            "records, and audit-ready rendered evidence. Implement the public DSL "
            "behavior exactly and keep denied actions directly actionable."
        ),
    ),
    base.TargetSpec(
        tier="D",
        target_dir=ROOT / "targets/web/campus_registrar_command/tier_d",
        visual=(
            "Campus Registrar Command Tier D repeat cohort. Build a polished "
            "release-stage registrar operations product with final enrollment "
            "certification, policy reconciliation, browser history and reload "
            "persistence, multi-view ledgers, reopen behavior, and end-to-end "
            "release synchronization. Keep all declared tables, routes, roles, "
            "events, and public state paths synchronized."
        ),
    ),
]

_BASE_RENDER_MARKDOWN = base.render_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Campus Registrar Command blind repeat cohorts.")
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
        default=["A", "B", "C", "D"],
        help="Campus Registrar Command target tiers to run.",
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
        default=ROOT / "targets/web/campus_registrar_command/cohorts/_batches",
    )
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


def render_markdown(aggregate: dict) -> str:
    return _BASE_RENDER_MARKDOWN(aggregate).replace(
        "# StayFlow Repeat Cohort",
        "# Campus Registrar Command Repeat Cohort",
        1,
    )


def main() -> int:
    base.TARGETS = TARGETS
    base.parse_args = parse_args
    base.render_markdown = render_markdown
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
