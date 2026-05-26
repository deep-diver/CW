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
        target_dir=ROOT / "targets/web/media_campaign_launch_desk/tier_a",
        visual=(
            "Media Campaign Launch Desk Tier A repeat cohort. Build a polished "
            "campaign planning and asset intake product with brief review, channel "
            "selection, budget or launch readiness state, and clear customer-facing "
            "progress surfaces. The interface should feel like a real media "
            "workflow product, not a bare state dashboard."
        ),
    ),
    base.TargetSpec(
        tier="B",
        target_dir=ROOT / "targets/web/media_campaign_launch_desk/tier_b",
        visual=(
            "Media Campaign Launch Desk Tier B repeat cohort. Build a polished "
            "creative operations product with asset review queues, campaign status "
            "tables, derived readiness counters, staff actions, and rendered "
            "evidence that stays synchronized with public state."
        ),
    ),
    base.TargetSpec(
        tier="C",
        target_dir=ROOT / "targets/web/media_campaign_launch_desk/tier_c",
        visual=(
            "Media Campaign Launch Desk Tier C repeat cohort. Build a polished "
            "regulated campaign approval product with role-gated review, upload "
            "or asset evidence, deterministic service checks, policy conflicts, "
            "persistent records, and audit-ready rendered projections. Implement "
            "all public DSL behavior exactly."
        ),
    ),
    base.TargetSpec(
        tier="D",
        target_dir=ROOT / "targets/web/media_campaign_launch_desk/tier_d",
        visual=(
            "Media Campaign Launch Desk Tier D repeat cohort. Build a polished "
            "release-stage campaign launch command product with final approval, "
            "channel synchronization, browser history and reload persistence, "
            "release ledgers, reopen behavior, and long workflow consistency. "
            "Keep all declared tables, routes, services, roles, events, and public "
            "state paths synchronized."
        ),
    ),
]

_BASE_RENDER_MARKDOWN = base.render_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Media Campaign Launch Desk blind repeat cohorts.")
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
        help="Media Campaign Launch Desk target tiers to run.",
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
        default=ROOT / "targets/web/media_campaign_launch_desk/cohorts/_batches",
    )
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


def render_markdown(aggregate: dict) -> str:
    return _BASE_RENDER_MARKDOWN(aggregate).replace(
        "# StayFlow Repeat Cohort",
        "# Media Campaign Launch Desk Repeat Cohort",
        1,
    )


def main() -> int:
    base.TARGETS = TARGETS
    base.parse_args = parse_args
    base.render_markdown = render_markdown
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
