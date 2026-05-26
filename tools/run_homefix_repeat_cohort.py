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
        target_dir=ROOT / "targets/web/homefix_hub/tier_a",
        visual=(
            "HomeFix Hub Tier A repeat cohort. Build a polished mass-market home "
            "repair booking service UI with customer-facing service cards, quote "
            "readiness, visit scheduling, contractor confirmation, and a tidy "
            "status ledger. The product should feel like a real commercial "
            "end-user service, not a bare state dashboard."
        ),
    ),
    base.TargetSpec(
        tier="B",
        target_dir=ROOT / "targets/web/homefix_hub/tier_b",
        visual=(
            "HomeFix Hub Tier B repeat cohort. Build a polished field scheduler "
            "and dispatch operations product UI with triage intake, crew "
            "assignment, parts readiness, route timing, visit lifecycle controls, "
            "and customer handoff. The interface should feel like a production "
            "home services operations tool with strong visual hierarchy, not a "
            "plain checklist."
        ),
    ),
    base.TargetSpec(
        tier="C",
        target_dir=ROOT / "targets/web/homefix_hub/tier_c",
        visual=(
            "HomeFix Hub Tier C repeat cohort. Build a polished evidence QA and "
            "repair clearance product UI with permit/document upload, inspection "
            "queues, technician notes, post-QA rework review, supplement invoice "
            "readiness, and customer release packet controls. The result should "
            "feel like a premium commercial "
            "operations service with a distinct QA-lab visual language while "
            "keeping all DetoxBench selectors directly actionable."
        ),
    ),
    base.TargetSpec(
        tier="D",
        target_dir=ROOT / "targets/web/homefix_hub/tier_d",
        visual=(
            "HomeFix Hub Tier D repeat cohort. Build a polished claims conveyor "
            "and warranty command product UI with insurance preauthorization, "
            "materials reconciliation, risk and compliance gates, QA/invoice "
            "handoffs, warranty seal ledger, carrier hold, customer acknowledgement, "
            "reseal, material reopen loops, and post-service customer closure. "
            "The app should look like a production-grade enterprise home-services "
            "platform with dense but legible workflow surfaces, rich visual "
            "structure, and all DetoxBench selectors directly actionable."
        ),
    ),
]

_BASE_RENDER_MARKDOWN = base.render_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HomeFix Hub blind repeat cohorts.")
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
        help="HomeFix Hub target tiers to run.",
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
        default=ROOT / "targets/web/homefix_hub/cohorts/_batches",
    )
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


def render_markdown(aggregate: dict) -> str:
    return _BASE_RENDER_MARKDOWN(aggregate).replace(
        "# StayFlow Repeat Cohort",
        "# HomeFix Hub Repeat Cohort",
        1,
    )


def main() -> int:
    base.TARGETS = TARGETS
    base.parse_args = parse_args
    base.render_markdown = render_markdown
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
