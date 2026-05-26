#!/usr/bin/env python3
"""Build ConformWeb paper visualization data and figures.

The script reads local, gitignored benchmark artifacts under targets/web and
produces publication-oriented CSV summaries plus figure candidates. It keeps
three data views separate:

  all_available_raw: every generated blind summary matching the cohort layout.
  current_raw: the latest/official raw cohorts that are present locally.
  paper_main_raw: current raw cohorts for the three main paper families.

High-level report figures are also generated from evaluation_report.md, because
some official Tier D rollups are present in reports even when raw artifacts are
not present in this workspace.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import textwrap
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import orjson
except ImportError:  # pragma: no cover
    orjson = None

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, FuncFormatter
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TARGET_ROOT = ROOT / "targets" / "web"
OUT_ROOT = ROOT / "reports" / "conformweb_visualizations"
DATA_DIR = OUT_ROOT / "data"
FIG_DIR = OUT_ROOT / "figures"
EVIDENCE_DIR = OUT_ROOT / "evidence"

SUITE_ORDER = [
    "stayflow_concierge",
    "freshcart_market",
    "clinic_shift_command",
    "campus_registrar_command",
    "media_campaign_launch_desk",
    "homefix_hub",
]

SUITE_LABELS: dict[str, str] = {}

TIER_ORDER = ["A", "B", "C", "D"]
TIER_DISPLAY_LABELS = {
    "A": "Consumer",
    "B": "Operational",
    "C": "Regulated",
    "D": "Release-stage",
}
MODEL_TIER_ORDER = ["M", "T", "F"]
MODEL_TIER_LABELS = {
    "M": "Small",
    "T": "Mid-range",
    "F": "Frontier",
}

PAPER_TERMS = {
    "formal": "Scenario-level conformance",
    "stepwise": "Step-level progress",
    "full_pass": "Full conformance",
    "tier": "Complexity variant",
    "suite": "Product family",
    "target": "Benchmark instance",
    "run": "Generated implementation",
}

FAILURE_SHORT_LABELS = {
    "wrong state transition": "wrong state",
    "missing interaction surface": "missing UI",
    "invalid observation surface": "bad observation",
    "route / persistence drift": "route drift",
    "rendered-projection mismatch": "projection mismatch",
    "action unavailable": "unactionable",
    "unavailable control": "unactionable",
    "service interaction failure": "service failure",
    "runtime error": "runtime error",
}

COLORS = {
    "ink": "#202124",
    "muted": "#5F6368",
    "line": "#DADCE0",
    "paper": "#FFFFFF",
    "black": "#000000",
    "orange": "#F9AB00",
    "sky": "#4FC3F7",
    "green": "#34A853",
    "yellow": "#FDD663",
    "blue": "#1A73E8",
    "vermillion": "#E8710A",
    "purple": "#A142F4",
    "gray": "#BDC1C6",
    "gray_light": "#F1F3F4",
    "gray_mid": "#80868B",
    # Backward-compatible semantic aliases used by older helper figures.
    "teal": "#1A73E8",
    "teal_light": "#4FC3F7",
    "sage": "#34A853",
    "sage_light": "#DFF4E8",
    "amber": "#F9AB00",
    "amber_light": "#FDD663",
    "rose": "#E8710A",
    "rose_light": "#FCE8D7",
    "plum": "#A142F4",
    "cyan": "#4FC3F7",
    "blue_dark": "#174EA6",
}

HEAT_CMAP = LinearSegmentedColormap.from_list(
    "conformweb_google_blue",
    ["#FFFFFF", "#E8F0FE", "#D2E3FC", "#AECBFA", "#669DF6", "#1A73E8", "#174EA6"],
)
FAIL_CMAP = LinearSegmentedColormap.from_list(
    "conformweb_google_failure",
    ["#FFFFFF", "#FCE8D7", "#FDD663", "#F9AB00", "#E8710A"],
)
COMPLEXITY_CMAP = LinearSegmentedColormap.from_list(
    "conformweb_google_blue_seq",
    ["#FFFFFF", "#E8F0FE", "#D2E3FC", "#AECBFA", "#669DF6", "#1A73E8", "#174EA6"],
)

SCENARIO_COLOR = COLORS["vermillion"]
STEP_COLOR = COLORS["blue"]
FULL_PASS_COLOR = COLORS["gray_mid"]
CONNECTOR_COLOR = "#B8CAD4"
MODEL_TIER_COLORS = {
    "M": COLORS["gray_mid"],
    "T": COLORS["purple"],
    "F": COLORS["green"],
}
FAILURE_LABELS = {
    "missing UI": "Missing surface",
    "bad observation": "Invalid observation",
    "unactionable": "Unavailable control",
    "wrong state": "Wrong transition",
    "route drift": "Route/persistence drift",
    "projection mismatch": "Projection mismatch",
}
FAILURE_ORDER = [
    "Missing surface",
    "Invalid observation",
    "Unavailable control",
    "Wrong transition",
    "Route/persistence drift",
    "Projection mismatch",
]
FAILURE_COLORS = {
    "Missing surface": "#009E73",
    "Invalid observation": COLORS["gray"],
    "Unavailable control": COLORS["yellow"],
    "Wrong transition": "#D55E00",
    "Route/persistence drift": "#CC79A7",
    "Projection mismatch": "#0072B2",
}

SUITE_LABEL_CACHE: dict[str, str] = {}
TARGET_INDEX_LABELS: dict[str, str] = {}

MODEL_LABELS = {
    "gpt54_nano": "GPT-5.4 nano",
    "claude_haiku45": "Claude Haiku 4.5",
    "gemini31_flash_lite": "Gemini 3.1 Flash Lite",
    "gpt54_mini": "GPT-5.4 mini",
    "claude_sonnet46": "Claude Sonnet 4.6",
    "gemini_flash_latest": "Gemini 3.1 Flash",
    "gpt54": "GPT-5.4",
    "claude_opus46": "Claude Opus 4.6",
    "gemini31_pro_preview": "Gemini 3.1 Pro Preview",
}

MODEL_ORDER = [
    "gpt54_nano",
    "claude_haiku45",
    "gemini31_flash_lite",
    "gpt54_mini",
    "claude_sonnet46",
    "gemini_flash_latest",
    "gpt54",
    "claude_opus46",
    "gemini31_pro_preview",
]

MODEL_ALIASES = {
    "gpt-5.4-nano": "gpt54_nano",
    "claude-haiku-4-5": "claude_haiku45",
    "gemini-3.1-flash-lite": "gemini31_flash_lite",
    "gpt-5.4-mini": "gpt54_mini",
    "claude-sonnet-4-6": "claude_sonnet46",
    "gemini-flash-latest": "gemini_flash_latest",
    "gemini flash latest": "gemini_flash_latest",
    "gemini flash": "gemini_flash_latest",
    "gpt-5.4": "gpt54",
    "claude-opus-4-6": "claude_opus46",
    "gemini-3.1-pro-preview": "gemini31_pro_preview",
}

MODEL_TO_TIER = {
    "gpt54_nano": "M",
    "claude_haiku45": "M",
    "gemini31_flash_lite": "M",
    "gpt54_mini": "T",
    "claude_sonnet46": "T",
    "gemini_flash_latest": "T",
    "gpt54": "F",
    "claude_opus46": "F",
    "gemini31_pro_preview": "F",
}

DOMAIN_LABELS = {
    "stayflow_concierge": "Travel",
    "freshcart_market": "Grocery",
    "clinic_shift_command": "Clinical Command",
    "campus_registrar_command": "Campus Registrar Command",
    "media_campaign_launch_desk": "Media Campaign Launch Desk",
    "homefix_hub": "Home Services",
}


CAPABILITY_ORDER = [
    "smoke",
    "core",
    "validation",
    "service",
    "upload",
    "permission",
    "persistence",
    "navigation",
    "journey",
    "operations",
    "release",
    "unclassified",
]

# Official/current raw cohorts available in this workspace. Some official Tier D
# report rows have no raw artifacts here; those are still covered by report
# rollups parsed from evaluation_report.md.
OFFICIAL_RAW_BATCHES: dict[tuple[str, str, str], set[str]] = {}


def _add_official(suite: str, tier: str, batch: str, mts: tuple[str, ...] = ("M", "T", "F")) -> None:
    for mt in mts:
        OFFICIAL_RAW_BATCHES.setdefault((suite, tier, mt), set()).add(batch)


_add_official("stayflow_concierge", "A", "20260511_stayflow_ab_mtf_10x")
_add_official("stayflow_concierge", "B", "20260511_stayflow_ab_mtf_10x")
_add_official("stayflow_concierge", "C", "stayflow-tier-c-20260511T153500Z")

_add_official("freshcart_market", "A", "20260511T180907Z")
_add_official("freshcart_market", "B", "20260512T015752Z_redesign", ("M",))
_add_official("freshcart_market", "B", "20260512T025450Z", ("T", "F"))
_add_official("freshcart_market", "C", "20260512T152227Z_tierc_mtf_10x_genairc")

_add_official("clinic_shift_command", "B", "20260513T022902Z_clinic_tierb_plus_mtf_10x")
_add_official("clinic_shift_command", "C", "20260513T072758Z_clinic_tierc_readiness_mtf_10x")

_add_official("homefix_hub", "A", "20260514_homefix_all_tiers_10x")
_add_official("homefix_hub", "B", "20260514_homefix_all_tiers_10x")
_add_official("homefix_hub", "C", "20260514_homefix_cd_recalibrated2_f_10x")
_add_official("homefix_hub", "D", "20260514_homefix_cd_recalibrated2_f_10x")

# Current manuscript figures should include every discovered/current product
# family. Earlier drafts focused on three families; the paper is now expected
# to absorb newly developed targets as they appear.
PAPER_MAIN_SUITES: set[str] = set()

FIGURE_NOTES: list[dict[str, str]] = []
EVIDENCE_NOTES: list[dict[str, str]] = []
PARSE_ERRORS: list[dict[str, Any]] = []


def ensure_dirs() -> None:
    for d in [
        DATA_DIR,
        FIG_DIR / "main",
        FIG_DIR / "reviewer_proposal",
        FIG_DIR / "appendix",
        FIG_DIR / "diagnostics",
        FIG_DIR / "atlases",
        EVIDENCE_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if orjson is not None:
        try:
            return orjson.loads(data)
        except Exception:
            # A few large browser traces contain non-standard numeric tokens
            # emitted by the browser/evaluator stack. Python's JSON parser is
            # intentionally tolerant of these tokens, while orjson is strict.
            # Falling back here preserves the completed evaluation artifact
            # instead of treating a valid run as locally missing.
            pass
    return json.loads(data)


def pct(x: float | int | None) -> float:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return np.nan
    return 100.0 * float(x)


def parse_percent(s: str) -> float:
    s = re.sub(r"[*_`]", "", str(s)).strip()
    if not s or s in {"--", "—", "N/A", "NA", "nan"}:
        return np.nan
    return float(s.rstrip("%")) / 100.0


def title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("_") if part)


def target_index_labels() -> dict[str, str]:
    global TARGET_INDEX_LABELS
    if TARGET_INDEX_LABELS:
        return TARGET_INDEX_LABELS
    readme = TARGET_ROOT / "README.md"
    labels: dict[str, str] = {}
    if readme.exists():
        for line in readme.read_text().splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3 or cells[0] in {"Suite", "---"}:
                continue
            m = re.search(r"`([^`]+)/tier_[a-d]/`", cells[2])
            if m:
                labels.setdefault(m.group(1), cells[0])
    TARGET_INDEX_LABELS = labels
    return TARGET_INDEX_LABELS


def suite_label(suite: str) -> str:
    if suite in SUITE_LABEL_CACHE:
        return SUITE_LABEL_CACHE[suite]
    index_labels = target_index_labels()
    if suite in index_labels:
        SUITE_LABEL_CACHE[suite] = index_labels[suite]
        return SUITE_LABEL_CACHE[suite]
    if suite in SUITE_LABELS:
        SUITE_LABEL_CACHE[suite] = SUITE_LABELS[suite]
        return SUITE_LABEL_CACHE[suite]
    contract = next((TARGET_ROOT / suite).glob("tier_*/contract.dsl.yaml"), None)
    if contract and contract.exists():
        try:
            obj = yaml.safe_load(contract.read_text()) or {}
            name = ((obj.get("app") or {}).get("name") or "").strip()
            if name:
                SUITE_LABEL_CACHE[suite] = name
                return name
        except Exception:
            pass
    SUITE_LABEL_CACHE[suite] = title_from_slug(suite)
    return SUITE_LABEL_CACHE[suite]


def discovered_suite_order(include_known: bool = True) -> list[str]:
    seen = {p.parent.parent.name for p in TARGET_ROOT.glob("*/tier_*/contract.dsl.yaml")}
    index_order = list(target_index_labels().keys())
    preferred = SUITE_ORDER if include_known else []
    ordered = [s for s in preferred if s in seen]
    ordered.extend(s for s in index_order if s in seen and s not in ordered)
    ordered.extend(sorted(s for s in seen if s not in ordered))
    return ordered


def suite_label_order(present: set[str] | None = None) -> list[str]:
    labels = [suite_label(s) for s in discovered_suite_order()]
    if present is not None:
        labels = [x for x in labels if x in present]
        labels.extend(sorted(present - set(labels)))
    return labels


def domain_label(suite: str) -> str:
    return DOMAIN_LABELS.get(suite, suite_label(suite))


def short_family_label(label: str) -> str:
    replacements = {
        "Campus Registrar Command": "Campus Registrar",
        "Media Campaign Launch Desk": "Media Campaign",
    }
    return replacements.get(str(label), str(label))


def compact_family_label(label: str) -> str:
    replacements = {
        "Clinical Command": "Clinical",
        "Campus Registrar Command": "Campus",
        "Media Campaign Launch Desk": "Media",
        "Home Services": "Home",
    }
    return replacements.get(str(label), str(label))


def target_label_order(df: pd.DataFrame, label_col: str = "suite_label", tier_col: str = "tier") -> list[str]:
    present = set((df[label_col].astype(str) + " " + df[tier_col].astype(str)).dropna())
    order: list[str] = []
    for suite in discovered_suite_order():
        for tier in TIER_ORDER:
            label = f"{suite_label(suite)} {tier}"
            if label in present:
                order.append(label)
    order.extend(sorted(present - set(order)))
    return order


def categorical_palette(n: int) -> list[str]:
    base = [
        COLORS["blue"],
        COLORS["orange"],
        COLORS["sky"],
        COLORS["green"],
        COLORS["yellow"],
        COLORS["vermillion"],
        COLORS["purple"],
        COLORS["gray_mid"],
    ]
    return [base[i % len(base)] for i in range(max(n, 1))]


def parse_pass_fraction(s: str) -> tuple[float, float, float]:
    m = re.search(r"(\d+)\s*/\s*(\d+)", str(s))
    if not m:
        return np.nan, np.nan, np.nan
    passed = float(m.group(1))
    total = float(m.group(2))
    return passed, total, passed / total if total else np.nan


def tier_from_dir(tier_dir: str) -> str:
    return tier_dir.replace("tier_", "").upper()


def raw_summary_paths() -> list[Path]:
    return sorted(TARGET_ROOT.glob("*/tier_*/cohorts/*/*/runs/*/*/*/summary.json"))


def parse_run_path(path: Path) -> dict[str, str]:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    # targets/web/<suite>/tier_<x>/cohorts/<M|T|F>/<batch>/runs/<model>/<rep>/<run-id>/summary.json
    return {
        "suite": parts[2],
        "tier": tier_from_dir(parts[3]),
        "model_tier": parts[5],
        "batch": parts[6],
        "model": parts[8],
        "rep": parts[9],
        "run_dir": str(path.parent),
        "summary_path": str(path),
    }


def is_current_raw(row: dict[str, Any]) -> bool:
    official = OFFICIAL_RAW_BATCHES.get((row["suite"], row["tier"], row["model_tier"]))
    if official:
        return row["batch"] in official
    # Future target families may not yet be listed above. Include them rather
    # than silently hiding newly discovered benchmark material.
    return True


def failure_label(raw: Any) -> str:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return "none"
    s = str(raw)
    lower = s.lower()
    if not s:
        return "unknown"
    if "invalid_state_hook" in lower or "state_hook" in lower or "observation" in lower:
        return "invalid observation surface"
    if "missing_component" in lower or "missing selector" in lower or "selector" in lower:
        return "missing interaction surface"
    if "timeout" in lower or "not visible" in lower or "disabled" in lower or "covered" in lower:
        return "unavailable control"
    if "browser_page" in lower or "route" in lower or "navigation" in lower or "reload" in lower:
        return "route / persistence drift"
    if "table" in lower or "rendered" in lower:
        return "rendered-projection mismatch"
    if "service" in lower or "network" in lower or "api" in lower:
        return "service interaction failure"
    if "state" in lower or "assertion" in lower or "delta" in lower:
        return "wrong state transition"
    if "crash" in lower or "exception" in lower or "error" in lower:
        return "runtime error"
    return s.replace("_", " ")


def short_failure_label(raw: Any) -> str:
    label = str(raw)
    return FAILURE_SHORT_LABELS.get(label, label.replace(" / ", " ").replace("-", " "))


def first_failure_token(scenario: dict[str, Any], first_failed_step: dict[str, Any] | None) -> str:
    candidates: list[Any] = [
        scenario.get("failure_category"),
    ]
    first_failure = scenario.get("first_failure")
    if isinstance(first_failure, dict):
        candidates.extend([first_failure.get("type"), first_failure.get("category"), first_failure.get("error")])
    elif first_failure:
        candidates.append(first_failure)
    if first_failed_step:
        for assertion in first_failed_step.get("assertions") or []:
            if not assertion.get("passed", True):
                candidates.append(assertion.get("type"))
                break
        if not candidates:
            candidates.append(first_failed_step.get("error"))
    for c in candidates:
        if c:
            return str(c)
    return "unknown"


def resolve_screenshot(summary_path: Path, scenario_id: str, screenshot_path: str | None) -> str:
    if not screenshot_path:
        return ""
    p = Path(screenshot_path)
    if p.exists():
        return str(p)
    local = summary_path.parent / "screenshots" / scenario_id / p.name
    if local.exists():
        return str(local)
    matches = list((summary_path.parent / "screenshots").glob(f"*/{p.name}"))
    if matches:
        return str(matches[0])
    return ""


def first_failed_step_for(scenario: dict[str, Any]) -> dict[str, Any] | None:
    idx = scenario.get("first_failed_step")
    steps = scenario.get("steps") or []
    if idx is not None and isinstance(idx, int):
        for step in steps:
            if step.get("step_index") == idx:
                return step
        if 0 <= idx - 1 < len(steps):
            return steps[idx - 1]
    for step in steps:
        if not step.get("passed", True):
            return step
    return None


def parse_raw_summaries() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    run_rows: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []
    capability_rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []

    paths = raw_summary_paths()
    for i, path in enumerate(paths, 1):
        meta = parse_run_path(path)
        try:
            obj = load_json(path)
        except Exception as exc:
            PARSE_ERRORS.append(
                {
                    **meta,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            print(f"skipping malformed summary: {path} ({type(exc).__name__}: {exc})")
            continue
        score = obj.get("score") or {}
        formal = score.get("formal") or {}
        stepwise = score.get("stepwise") or {}
        contract = score.get("contract") or {}
        probe = score.get("probe") or {}
        current = is_current_raw(meta)
        paper_main = current and (not PAPER_MAIN_SUITES or meta["suite"] in PAPER_MAIN_SUITES)
        run_key = {
            **meta,
            "run_id": obj.get("run_id", path.parent.name),
            "subject": obj.get("subject", ""),
            "suite_label": suite_label(meta["suite"]),
            "tier_label": meta["tier"],
            "model_tier_label": MODEL_TIER_LABELS.get(meta["model_tier"], meta["model_tier"]),
            "model_label": MODEL_LABELS.get(meta["model"], meta["model"]),
            "view_all_available_raw": True,
            "view_current_raw": current,
            "view_paper_main_raw": paper_main,
        }

        fb = score.get("failure_breakdown") or {}
        primary_failure = max(fb.items(), key=lambda kv: kv[1])[0] if fb else "none"
        run_rows.append(
            {
                **run_key,
                "passed": bool(obj.get("passed")),
                "formal_ratio": formal.get("ratio"),
                "stepwise_ratio": stepwise.get("ratio"),
                "formal_earned": formal.get("earned"),
                "formal_possible": formal.get("possible"),
                "stepwise_earned": stepwise.get("earned"),
                "stepwise_possible": stepwise.get("possible"),
                "conformance_gap": (stepwise.get("ratio") or 0) - (formal.get("ratio") or 0),
                "contract_ratio": contract.get("ratio"),
                "contract_failures": contract.get("failures"),
                "probe_passed": probe.get("passed"),
                "probe_total": probe.get("total"),
                "primary_raw_failure": primary_failure,
                "primary_failure_group": failure_label(primary_failure),
                "n_scenarios": len(obj.get("scenarios") or []),
            }
        )

        cap = score.get("by_capability") or score.get("by_tier") or {}
        for name, values in cap.items():
            capability_rows.append(
                {
                    **run_key,
                    "capability": name,
                    "scenario_ratio": values.get("scenario_ratio", values.get("ratio")),
                    "step_ratio": values.get("step_ratio"),
                    "passed": values.get("passed"),
                    "failed": values.get("failed"),
                    "total": values.get("total"),
                }
            )

        for scenario in obj.get("scenarios") or []:
            first_step = first_failed_step_for(scenario)
            first_token = first_failure_token(scenario, first_step)
            first_group = failure_label(first_token)
            expected = scenario.get("expected_step_count") or 0
            passed_until = scenario.get("passed_until_step")
            if passed_until is None:
                passed_until = scenario.get("passed_step_count")
            progress = (passed_until / expected) if expected else np.nan
            screenshots = (first_step or {}).get("screenshots") or {}
            first_before = resolve_screenshot(path, scenario.get("id", ""), screenshots.get("before"))
            first_after = resolve_screenshot(path, scenario.get("id", ""), screenshots.get("after"))
            scenario_rows.append(
                {
                    **run_key,
                    "scenario_id": scenario.get("id"),
                    "scenario_tier": scenario.get("tier") or "unclassified",
                    "kind": scenario.get("kind"),
                    "visibility": scenario.get("visibility"),
                    "difficulty": scenario.get("difficulty"),
                    "scenario_passed": bool(scenario.get("passed")),
                    "scenario_score_ratio": (scenario.get("score") or {}).get("ratio"),
                    "expected_step_count": scenario.get("expected_step_count"),
                    "completed_step_count": scenario.get("completed_step_count"),
                    "passed_step_count": scenario.get("passed_step_count"),
                    "passed_until_step": scenario.get("passed_until_step"),
                    "first_failed_step": scenario.get("first_failed_step"),
                    "step_progress_until_failure": progress,
                    "first_failed_action": (first_step or {}).get("action"),
                    "first_failed_component": (first_step or {}).get("component"),
                    "first_failed_actor": (first_step or {}).get("actor"),
                    "first_failure_raw": first_token,
                    "first_failure_group": first_group,
                    "first_failure_before_screenshot": first_before,
                    "first_failure_after_screenshot": first_after,
                }
            )

            for step in scenario.get("steps") or []:
                failed_assertions = [
                    a.get("type", "unknown")
                    for a in (step.get("assertions") or [])
                    if not a.get("passed", True)
                ]
                step_rows.append(
                    {
                        **run_key,
                        "scenario_id": scenario.get("id"),
                        "scenario_tier": scenario.get("tier") or "unclassified",
                        "visibility": scenario.get("visibility"),
                        "kind": scenario.get("kind"),
                        "step_index": step.get("step_index"),
                        "action": step.get("action"),
                        "component": step.get("component"),
                        "actor": step.get("actor"),
                        "step_passed": bool(step.get("passed")),
                        "n_assertions": len(step.get("assertions") or []),
                        "failed_assertion_types": ";".join(failed_assertions),
                        "is_first_failed_step": step.get("step_index") == scenario.get("first_failed_step"),
                    }
                )

        if i % 100 == 0:
            print(f"parsed {i}/{len(paths)} summaries")

    return (
        pd.DataFrame(run_rows),
        pd.DataFrame(scenario_rows),
        pd.DataFrame(capability_rows),
        pd.DataFrame(step_rows),
    )


def count_state_fields(schema: Any) -> int:
    if isinstance(schema, dict):
        if "type" in schema and "fields" not in schema and "items" not in schema:
            return 1
        return sum(count_state_fields(v) for v in schema.values())
    if isinstance(schema, list):
        return sum(count_state_fields(v) for v in schema)
    return 0


def count_scenario_file(path: Path) -> tuple[int, int, int]:
    if not path.exists():
        return 0, 0, 0
    obj = yaml.safe_load(path.read_text()) or {}
    scenarios = obj.get("scenarios") or []
    n_steps = sum(len(s.get("steps") or []) for s in scenarios)
    max_steps = max((len(s.get("steps") or []) for s in scenarios), default=0)
    return len(scenarios), n_steps, max_steps


def parse_suite_metrics() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for contract_path in sorted(TARGET_ROOT.glob("*/tier_*/contract.dsl.yaml")):
        rel = contract_path.relative_to(TARGET_ROOT)
        suite = rel.parts[0]
        tier = tier_from_dir(rel.parts[1])
        obj = yaml.safe_load(contract_path.read_text()) or {}
        runtime = obj.get("runtime") or {}
        components = obj.get("components") or {}
        component_actions = 0
        effects = 0
        for c in components.values():
            actions = c.get("actions") or {}
            component_actions += len(actions)
            for a in actions.values():
                effects += len(a.get("effects") or [])
        public_count, public_steps, public_max = count_scenario_file(contract_path.parent / "scenarios.public.dsl.yaml")
        private_count, private_steps, private_max = count_scenario_file(contract_path.parent / "scenarios.private.dsl.yaml")
        scenario_count = public_count + private_count
        scenario_steps = public_steps + private_steps
        rows.append(
            {
                "suite": suite,
                "suite_label": suite_label(suite),
                "tier": tier,
                "pages": len(runtime.get("pages") or {}),
                "components": len(components),
                "component_actions": component_actions,
                "effects": effects,
                "state_fields": count_state_fields((obj.get("state") or {}).get("schema") or {}),
                "services": len(runtime.get("services") or {}),
                "tables": len(runtime.get("tables") or {}),
                "derived_relations": len(obj.get("x-derived") or {}),
                "public_scenarios": public_count,
                "private_scenarios": private_count,
                "scenario_count": scenario_count,
                "scenario_steps": scenario_steps,
                "avg_steps_per_scenario": scenario_steps / scenario_count if scenario_count else np.nan,
                "max_steps_public": public_max,
                "max_steps_private": private_max,
                "max_steps": max(public_max, private_max),
            }
        )
    return pd.DataFrame(rows)


def parse_scenario_inventory() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scenario_path in sorted(TARGET_ROOT.glob("*/tier_*/scenarios*.dsl.yaml")):
        rel = scenario_path.relative_to(TARGET_ROOT)
        suite = rel.parts[0]
        tier = tier_from_dir(rel.parts[1])
        visibility = "public" if "public" in scenario_path.name else "held-out"
        obj = yaml.safe_load(scenario_path.read_text()) or {}
        for scenario in obj.get("scenarios") or []:
            steps = scenario.get("steps") or []
            rows.append(
                {
                    "suite": suite,
                    "suite_label": suite_label(suite),
                    "tier": tier,
                    "scenario_id": scenario.get("id"),
                    "scenario_tier": scenario.get("tier") or "unclassified",
                    "visibility": visibility,
                    "step_count": len(steps),
                    "source": "target_spec",
                }
            )
    return pd.DataFrame(rows)


def parse_contract_features() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for contract_path in sorted(TARGET_ROOT.glob("*/tier_*/contract.dsl.yaml")):
        rel = contract_path.relative_to(TARGET_ROOT)
        suite = rel.parts[0]
        tier = tier_from_dir(rel.parts[1])
        obj = yaml.safe_load(contract_path.read_text()) or {}
        runtime = obj.get("runtime") or {}
        components = obj.get("components") or {}
        action_names: list[str] = []
        for component in components.values():
            if not isinstance(component, dict):
                continue
            actions = component.get("actions") or {}
            if isinstance(actions, dict):
                action_names.extend(str(name).lower() for name in actions)
        rows.append(
            {
                "suite": suite,
                "tier": tier,
                "roles": bool(runtime.get("session")),
                "services_feature": bool(runtime.get("services")),
                "tables_feature": bool(runtime.get("tables")),
                "persistence_feature": bool(runtime.get("persistence")),
                "upload_feature": any("upload" in name for name in action_names),
                "derived_feature": bool(obj.get("x-derived")),
            }
        )
    return pd.DataFrame(rows)


def target_inventory(metrics: pd.DataFrame, scenarios: pd.DataFrame) -> pd.DataFrame:
    spec = parse_scenario_inventory()
    if not spec.empty:
        spec_agg = (
            spec.groupby(["suite", "suite_label", "tier"], observed=True)
            .agg(
                spec_scenarios=("scenario_id", "nunique"),
                spec_public=("visibility", lambda x: int((x == "public").sum())),
                spec_heldout=("visibility", lambda x: int((x == "held-out").sum())),
                spec_steps=("step_count", "sum"),
                spec_avg_steps=("step_count", "mean"),
                spec_max_steps=("step_count", "max"),
            )
            .reset_index()
        )
    else:
        spec_agg = pd.DataFrame(columns=["suite", "suite_label", "tier"])

    raw = view_filter(scenarios, "current_raw")
    raw = raw[raw["kind"] == "scoring"].copy()
    raw_dedup = raw.drop_duplicates(["suite", "tier", "scenario_id"])
    if not raw_dedup.empty:
        raw_agg = (
            raw_dedup.groupby(["suite", "suite_label", "tier"], observed=True)
            .agg(
                raw_scenarios=("scenario_id", "nunique"),
                raw_public=("visibility", lambda x: int((x == "public").sum())),
                raw_heldout=("visibility", lambda x: int((x != "public").sum())),
                raw_steps=("expected_step_count", "sum"),
                raw_avg_steps=("expected_step_count", "mean"),
                raw_max_steps=("expected_step_count", "max"),
            )
            .reset_index()
        )
    else:
        raw_agg = pd.DataFrame(columns=["suite", "suite_label", "tier"])

    base = metrics.copy()
    base = pd.merge(base, spec_agg, on=["suite", "suite_label", "tier"], how="outer")
    base = pd.merge(base, raw_agg, on=["suite", "suite_label", "tier"], how="outer", suffixes=("", "_raw"))
    if "suite_label_raw" in base:
        base["suite_label"] = base["suite_label"].fillna(base["suite_label_raw"])
        base = base.drop(columns=["suite_label_raw"])
    base["suite_label"] = base["suite_label"].fillna(base["suite"].map(suite_label))
    base = pd.merge(base, parse_contract_features(), on=["suite", "tier"], how="left")

    fill_pairs = [
        ("scenario_count", "spec_scenarios", "raw_scenarios"),
        ("public_scenarios", "spec_public", "raw_public"),
        ("private_scenarios", "spec_heldout", "raw_heldout"),
        ("scenario_steps", "spec_steps", "raw_steps"),
        ("avg_steps_per_scenario", "spec_avg_steps", "raw_avg_steps"),
        ("max_steps", "spec_max_steps", "raw_max_steps"),
    ]
    for out_col, spec_col, raw_col in fill_pairs:
        if out_col not in base:
            base[out_col] = np.nan
        if spec_col in base:
            base[out_col] = base[out_col].fillna(base[spec_col])
        if raw_col in base:
            base[out_col] = base[out_col].fillna(base[raw_col])

    for col in ["pages", "components", "component_actions", "state_fields", "services", "tables", "derived_relations"]:
        if col not in base:
            base[col] = np.nan
    for col in ["roles", "services_feature", "tables_feature", "persistence_feature", "upload_feature", "derived_feature"]:
        if col not in base:
            base[col] = False
        base[col] = base[col].where(base[col].notna(), False).astype(bool)

    base["suite_rank"] = base["suite"].map({s: i for i, s in enumerate(discovered_suite_order())}).fillna(999)
    base["tier_rank"] = base["tier"].map({t: i for i, t in enumerate(TIER_ORDER)}).fillna(999)
    return base.sort_values(["suite_rank", "suite_label", "tier_rank", "tier"]).reset_index(drop=True)


def scenario_bucket(label: Any) -> str:
    value = str(label or "unclassified").lower()
    if value in {"smoke", "core", "unclassified"}:
        return "core"
    if value in {"validation", "persistence", "table", "navigation"}:
        return "state"
    if value in {"service", "upload", "permission", "supplier", "support", "finance"}:
        return "runtime"
    return "journey"


def scenario_terrain_data(scenarios: pd.DataFrame) -> pd.DataFrame:
    spec = parse_scenario_inventory()
    raw = view_filter(scenarios, "current_raw")
    raw = raw[raw["kind"] == "scoring"].drop_duplicates(["suite", "tier", "scenario_id"])
    raw_steps = raw[
        ["suite", "suite_label", "tier", "scenario_id", "scenario_tier", "visibility", "expected_step_count"]
    ].rename(columns={"expected_step_count": "step_count"})
    raw_steps["visibility"] = raw_steps["visibility"].where(raw_steps["visibility"] == "public", "held-out")
    raw_steps["source"] = "raw_artifact"
    if not spec.empty:
        existing = set(zip(spec["suite"], spec["tier"], spec["scenario_id"], strict=False))
        raw_steps = raw_steps[
            ~raw_steps.apply(lambda r: (r["suite"], r["tier"], r["scenario_id"]) in existing, axis=1)
        ]
        terrain = pd.concat([spec, raw_steps], ignore_index=True)
    else:
        terrain = raw_steps
    terrain = terrain[terrain["tier"].isin(TIER_ORDER)].copy()
    terrain["bucket"] = terrain["scenario_tier"].map(scenario_bucket)
    terrain["visibility"] = terrain["visibility"].where(terrain["visibility"] == "public", "held-out")
    terrain["step_count"] = pd.to_numeric(terrain["step_count"], errors="coerce").fillna(0)
    return terrain


def extract_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    next_match = re.search(r"\n## ", text[start + len(marker) :])
    if next_match:
        return text[start : start + len(marker) + next_match.start()]
    return text[start:]


def markdown_tables(section: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    lines = section.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows: list[list[str]] = [header]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            tables.append(rows)
        else:
            i += 1
    return tables


def table_to_df(table: list[list[str]]) -> pd.DataFrame:
    if not table or len(table) < 2:
        return pd.DataFrame()
    header = table[0]
    rows = table[1:]
    return pd.DataFrame(rows, columns=header)


def split_tier_model_tier(value: Any) -> tuple[str, str | None]:
    text = re.sub(r"`", "", str(value)).strip()
    if "/" in text:
        parts = [p.strip() for p in text.split("/", 1)]
        return parts[0], parts[1] or None
    return text, None


def weighted_mean(series: pd.Series, weights: pd.Series) -> float:
    valid = series.notna() & weights.notna() & (weights > 0)
    if not valid.any():
        return np.nan
    return float(np.average(series[valid], weights=weights[valid]))


def canonical_model_id(value: Any) -> str:
    text = re.sub(r"[*_`]", "", str(value)).strip().lower()
    text = re.sub(r"\s+", " ", text)
    if text in MODEL_ALIASES:
        return MODEL_ALIASES[text]
    return text.replace(".", "").replace("-", "_").replace(" ", "_")


def model_tier_for_model(model_id: str) -> str:
    if model_id in MODEL_TO_TIER:
        return MODEL_TO_TIER[model_id]
    if any(token in model_id for token in ["nano", "haiku", "flash_lite"]):
        return "M"
    if any(token in model_id for token in ["mini", "sonnet", "flash"]):
        return "T"
    return "F"


def report_model_detail_row(suite: str, tier: str, row: pd.Series, source: str) -> dict[str, Any] | None:
    model_raw = row.get("Model")
    if model_raw is None or not str(model_raw).strip():
        return None
    model_text = re.sub(r"[*_`]", "", str(model_raw)).strip()
    if re.fullmatch(r"tier\s+[A-Z]", model_text, flags=re.IGNORECASE):
        return None
    model_id = canonical_model_id(model_raw)
    model_tier = model_tier_for_model(model_id)
    formal_col = "Formal mean" if "Formal mean" in row else "Formal"
    step_col = "Stepwise mean" if "Stepwise mean" in row else "Stepwise"
    passed, total, rate = parse_pass_fraction(row.get("Full pass", ""))
    try:
        runs = int(str(row["Runs"]).strip())
    except Exception:
        runs = total
    return {
        "suite": suite,
        "suite_label": suite_label(suite),
        "tier": tier,
        "model": model_id,
        "model_label": MODEL_LABELS.get(model_id, re.sub(r"`", "", str(model_raw)).strip()),
        "model_tier": model_tier,
        "model_tier_label": MODEL_TIER_LABELS.get(model_tier, model_tier),
        "runs": runs,
        "formal_mean": parse_percent(row.get(formal_col, "")),
        "stepwise_mean": parse_percent(row.get(step_col, "")),
        "full_pass": passed,
        "full_total": total,
        "full_pass_rate": rate,
        "report_view": "paper_main_reported",
        "source": source,
    }


def parse_report_per_model_details() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for report_path in sorted(TARGET_ROOT.glob("*/evaluation_report.md")):
        suite = report_path.parent.name
        text = report_path.read_text()
        for match in re.finditer(r"^## Tier ([A-D]) Model-Tier Detail\s*$", text, re.MULTILINE):
            tier = match.group(1)
            section_start = match.start()
            next_match = re.search(r"\n## ", text[match.end() :])
            section = text[section_start : match.end() + next_match.start()] if next_match else text[section_start:]
            for table in markdown_tables(section)[:1]:
                df = table_to_df(table)
                if "Model" not in df.columns:
                    continue
                for _, r in df.iterrows():
                    parsed = report_model_detail_row(suite, tier, r, "evaluation_report")
                    if parsed:
                        rows.append(parsed)

    for readme_path in sorted(TARGET_ROOT.glob("*/tier_*/README.md")):
        rel = readme_path.relative_to(TARGET_ROOT)
        suite = rel.parts[0]
        tier = tier_from_dir(rel.parts[1])
        text = readme_path.read_text()
        for table in markdown_tables(text):
            df = table_to_df(table)
            if "Model" not in df.columns or "Runs" not in df.columns:
                continue
            if not ({"Formal", "Formal mean"} & set(df.columns)):
                continue
            for _, r in df.iterrows():
                parsed = report_model_detail_row(suite, tier, r, "tier_readme")
                if parsed:
                    rows.append(parsed)

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Prefer consolidated evaluation reports when the same per-model row exists
    # in both the report and a tier README.
    source_rank = {"evaluation_report": 0, "tier_readme": 1}
    df["_source_rank"] = df["source"].map(source_rank).fillna(9)
    df = df.sort_values(["suite", "tier", "model", "_source_rank"])
    df = df.drop_duplicates(["suite", "tier", "model"], keep="first")
    return df.drop(columns=["_source_rank"]).reset_index(drop=True)


def parse_report_rollups() -> tuple[pd.DataFrame, pd.DataFrame]:
    tier_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []

    for suite_dir in sorted(TARGET_ROOT.glob("*/evaluation_report.md")):
        suite = suite_dir.parent.name
        text = suite_dir.read_text()
        # Any future product family with the same report sections is included
        # automatically. The paper can later decide which rows move into the
        # main text versus the appendix.
        if True:
            tier_section = extract_section(text, "Tier Rollup")
            tables = markdown_tables(tier_section)
            if tables:
                df = table_to_df(tables[0])
                tier_model_rows: list[dict[str, Any]] = []
                for _, r in df.iterrows():
                    passed, total, rate = parse_pass_fraction(r.get("Full pass", ""))
                    tier, model_tier = split_tier_model_tier(r["Tier"])
                    row = {
                        "suite": suite,
                        "suite_label": suite_label(suite),
                        "tier": tier,
                        "runs": int(str(r["Runs"]).strip()),
                        "formal_mean": parse_percent(r["Formal mean"]),
                        "stepwise_mean": parse_percent(r["Stepwise mean"]),
                        "full_pass": passed,
                        "full_total": total,
                        "full_pass_rate": rate,
                        "report_view": "paper_main_reported",
                    }
                    if model_tier:
                        model_row = {
                            **row,
                            "model_tier": model_tier,
                            "model_tier_label": MODEL_TIER_LABELS.get(model_tier, model_tier),
                        }
                        tier_model_rows.append(model_row)
                        model_rows.append(model_row)
                    else:
                        tier_rows.append(row)
                if tier_model_rows:
                    tier_model_df = pd.DataFrame(tier_model_rows)
                    for tier, group in tier_model_df.groupby("tier", sort=False):
                        runs = int(group["runs"].sum())
                        full_pass = int(group["full_pass"].sum())
                        full_total = int(group["full_total"].sum())
                        tier_rows.append(
                            {
                                "suite": suite,
                                "suite_label": suite_label(suite),
                                "tier": tier,
                                "runs": runs,
                                "formal_mean": weighted_mean(group["formal_mean"], group["runs"]),
                                "stepwise_mean": weighted_mean(group["stepwise_mean"], group["runs"]),
                                "full_pass": full_pass,
                                "full_total": full_total,
                                "full_pass_rate": full_pass / full_total if full_total else np.nan,
                                "report_view": "paper_main_reported",
                            }
                        )
            model_section = extract_section(text, "Model-Tier Detail")
            tables = markdown_tables(model_section)
            if tables:
                df = table_to_df(tables[0])
                for _, r in df.iterrows():
                    passed, total, rate = parse_pass_fraction(r.get("Full pass", ""))
                    model_rows.append(
                        {
                            "suite": suite,
                            "suite_label": suite_label(suite),
                            "tier": str(r["Target Tier"]).strip(),
                            "model_tier": str(r["Model Tier"]).strip(),
                            "model_tier_label": MODEL_TIER_LABELS.get(str(r["Model Tier"]).strip(), str(r["Model Tier"]).strip()),
                            "runs": int(str(r["Runs"]).strip()),
                            "formal_mean": parse_percent(r["Formal mean"]),
                            "stepwise_mean": parse_percent(r["Stepwise mean"]),
                            "full_pass": passed,
                            "full_total": total,
                            "full_pass_rate": rate,
                            "report_view": "paper_main_reported",
                        }
                    )

        if suite == "homefix_hub":
            # Preserve HomeFix as appendix/supplemental, with current C/D rows
            # taken from the recalibration section.
            original = extract_section(text, "Original Full-Cohort Rollup")
            for table in markdown_tables(original)[:1]:
                df = table_to_df(table)
                for _, r in df.iterrows():
                    passed, total, rate = parse_pass_fraction(r.get("Full pass", ""))
                    tier_rows.append(
                        {
                            "suite": suite,
                            "suite_label": suite_label(suite),
                            "tier": str(r["Tier"]).strip(),
                            "runs": int(str(r["Runs"]).strip()),
                            "formal_mean": parse_percent(r["Formal mean"]),
                            "stepwise_mean": parse_percent(r["Stepwise mean"]),
                            "full_pass": passed,
                            "full_total": total,
                            "full_pass_rate": rate,
                            "report_view": "homefix_original_reported",
                        }
                    )
            original_models = extract_section(text, "Original Model-Tier Detail")
            for table in markdown_tables(original_models)[:1]:
                df = table_to_df(table)
                for _, r in df.iterrows():
                    passed, total, rate = parse_pass_fraction(r.get("Full pass", ""))
                    model_rows.append(
                        {
                            "suite": suite,
                            "suite_label": suite_label(suite),
                            "tier": str(r["Target Tier"]).strip(),
                            "model_tier": str(r["Model Tier"]).strip(),
                            "model_tier_label": MODEL_TIER_LABELS.get(str(r["Model Tier"]).strip(), str(r["Model Tier"]).strip()),
                            "runs": int(str(r["Runs"]).strip()),
                            "formal_mean": parse_percent(r["Formal mean"]),
                            "stepwise_mean": parse_percent(r["Stepwise mean"]),
                            "full_pass": passed,
                            "full_total": total,
                            "full_pass_rate": rate,
                            "report_view": "homefix_original_reported",
                        }
                    )
            recal = extract_section(text, "Recalibration Check")
            tables = markdown_tables(recal)
            if tables:
                df = table_to_df(tables[0])
                for _, r in df.iterrows():
                    passed, total, rate = parse_pass_fraction(r.get("Full pass", ""))
                    tier_rows.append(
                        {
                            "suite": suite,
                            "suite_label": suite_label(suite),
                            "tier": str(r["Tier"]).strip(),
                            "runs": int(str(r["Runs"]).strip()),
                            "formal_mean": parse_percent(r["Formal mean"]),
                            "stepwise_mean": parse_percent(r["Stepwise mean"]),
                            "full_pass": passed,
                            "full_total": total,
                            "full_pass_rate": rate,
                            "report_view": "homefix_recalibrated_reported",
                        }
                    )
            if len(tables) >= 2:
                df = table_to_df(tables[1])
                for _, r in df.iterrows():
                    passed, total, rate = parse_pass_fraction(r.get("Full pass", ""))
                    model_rows.append(
                        {
                            "suite": suite,
                            "suite_label": suite_label(suite),
                            "tier": str(r["Target Tier"]).strip(),
                            "model_tier": str(r["Model Tier"]).strip(),
                            "model_tier_label": MODEL_TIER_LABELS.get(str(r["Model Tier"]).strip(), str(r["Model Tier"]).strip()),
                            "runs": int(str(r["Runs"]).strip()),
                            "formal_mean": parse_percent(r["Formal mean"]),
                            "stepwise_mean": parse_percent(r["Stepwise mean"]),
                            "full_pass": passed,
                            "full_total": total,
                            "full_pass_rate": rate,
                            "report_view": "homefix_recalibrated_reported",
                        }
                    )

    return pd.DataFrame(tier_rows), pd.DataFrame(model_rows)


def augment_report_rollups_from_raw(
    runs: pd.DataFrame,
    report_tiers: pd.DataFrame,
    report_models: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fill maintained suite/tier gaps in report rollups from current raw runs.

    Some reports deliberately summarize only the maintained tiers while the
    repository still contains validated raw cohorts for the omitted tier. Paper
    figures should make every existing A-D target visible, so we add fallback
    rows only when the report rollup has no row for that suite/tier.
    """
    if runs.empty:
        return report_tiers, report_models
    raw = runs[runs.get("view_current_raw", False).astype(bool)].copy()
    if raw.empty:
        return report_tiers, report_models
    raw = raw[raw["tier"].isin(TIER_ORDER)].copy()
    raw["passed"] = raw["passed"].astype(bool)

    existing_tier_pairs = set(zip(report_tiers.get("suite", pd.Series(dtype=str)), report_tiers.get("tier", pd.Series(dtype=str)), strict=False))
    tier_missing = raw[
        ~raw.apply(lambda r: (r["suite"], r["tier"]) in existing_tier_pairs, axis=1)
    ].copy()
    if not tier_missing.empty:
        tier_fallback = (
            tier_missing.groupby(["suite", "suite_label", "tier"], observed=True)
            .agg(
                runs=("run_id", "count"),
                formal_mean=("formal_ratio", "mean"),
                stepwise_mean=("stepwise_ratio", "mean"),
                full_pass=("passed", "sum"),
            )
            .reset_index()
        )
        tier_fallback["full_pass"] = tier_fallback["full_pass"].astype(int)
        tier_fallback["full_total"] = tier_fallback["runs"].astype(int)
        tier_fallback["full_pass_rate"] = tier_fallback["full_pass"] / tier_fallback["full_total"].replace(0, np.nan)
        tier_fallback["report_view"] = "raw_current_fallback"
        report_tiers = pd.concat([report_tiers, tier_fallback[report_tiers.columns]], ignore_index=True)

    existing_model_pairs = set(
        zip(
            report_models.get("suite", pd.Series(dtype=str)),
            report_models.get("tier", pd.Series(dtype=str)),
            report_models.get("model_tier", pd.Series(dtype=str)),
            strict=False,
        )
    )
    model_missing = raw[
        ~raw.apply(lambda r: (r["suite"], r["tier"], r["model_tier"]) in existing_model_pairs, axis=1)
    ].copy()
    if not model_missing.empty:
        model_fallback = (
            model_missing.groupby(["suite", "suite_label", "tier", "model_tier", "model_tier_label"], observed=True)
            .agg(
                runs=("run_id", "count"),
                formal_mean=("formal_ratio", "mean"),
                stepwise_mean=("stepwise_ratio", "mean"),
                full_pass=("passed", "sum"),
            )
            .reset_index()
        )
        model_fallback["full_pass"] = model_fallback["full_pass"].astype(int)
        model_fallback["full_total"] = model_fallback["runs"].astype(int)
        model_fallback["full_pass_rate"] = model_fallback["full_pass"] / model_fallback["full_total"].replace(0, np.nan)
        model_fallback["report_view"] = "raw_current_fallback"
        report_models = pd.concat([report_models, model_fallback[report_models.columns]], ignore_index=True)

    return report_tiers, report_models


def save_table(df: pd.DataFrame, name: str) -> None:
    df.to_csv(DATA_DIR / name, index=False)


def set_theme() -> None:
    sns.set_theme(
        context="paper",
        style="white",
        font="DejaVu Sans",
        rc={
            "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "axes.edgecolor": COLORS["line"],
            "axes.labelcolor": COLORS["ink"],
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
            "text.color": COLORS["ink"],
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "semibold",
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "legend.title_fontsize": 8,
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
        },
    )


def save_figure(fig: plt.Figure, name: str, group: str, note: str, paper_use: str) -> None:
    out_dir = FIG_DIR / group
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{name}.pdf"
    svg_path = out_dir / f"{name}.svg"
    png_path = out_dir / f"{name}.png"
    for path in [pdf_path, svg_path, png_path]:
        kwargs: dict[str, Any] = {"bbox_inches": "tight", "facecolor": "white"}
        if path.suffix == ".png":
            kwargs["dpi"] = 300
        fig.savefig(path, **kwargs)
    plt.close(fig)
    FIGURE_NOTES.append(
        {
            "group": group,
            "name": name,
            "pdf": str(pdf_path.relative_to(OUT_ROOT)),
            "svg": str(svg_path.relative_to(OUT_ROOT)),
            "png": str(png_path.relative_to(OUT_ROOT)),
            "paper_use": paper_use,
            "note": note,
        }
    )


def ordered_categories(series: pd.Series, order: list[str]) -> pd.Categorical:
    present = [x for x in order if x in set(series.dropna())]
    extra = sorted([x for x in set(series.dropna()) if x not in present])
    return pd.Categorical(series, categories=present + extra, ordered=True)


def style_existing_legend(ax: plt.Axes, **kwargs: Any) -> None:
    legend = ax.get_legend()
    if legend is not None:
        legend.set_frame_on(False)
        title = kwargs.get("title")
        if title is not None:
            legend.set_title(title)
        loc = kwargs.get("loc")
        if loc is not None:
            legend.set_loc(loc)


def preferred_report_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Rows to use for manuscript-facing report figures.

    Generic target reports use `paper_main_reported`. HomeFix has an original
    A-D batch plus recalibrated C/D rows; use original A/B and recalibrated C/D
    so the family appears once per complexity variant.
    """
    if df.empty:
        return df.copy()
    generic = df[df["report_view"].isin(["paper_main_reported", "raw_current_fallback"])].copy()
    homefix_ab = df[
        (df["report_view"] == "homefix_original_reported")
        & (df["suite"] == "homefix_hub")
        & (df["tier"].isin(["A", "B"]))
    ].copy()
    homefix_cd = df[
        (df["report_view"] == "homefix_recalibrated_reported")
        & (df["suite"] == "homefix_hub")
        & (df["tier"].isin(["C", "D"]))
    ].copy()
    return pd.concat([generic, homefix_ab, homefix_cd], ignore_index=True)


def paper_main_reported_rows(df: pd.DataFrame) -> pd.DataFrame:
    return preferred_report_rows(df)


def report_suite_order(df: pd.DataFrame) -> list[str]:
    present = set(df["suite"].dropna()) if "suite" in df.columns else set()
    ordered = [s for s in discovered_suite_order() if s in present]
    ordered.extend(sorted(present - set(ordered)))
    return ordered


def strip_background(ax: plt.Axes) -> None:
    ax.grid(False)
    ax.set_facecolor("white")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(COLORS["line"])
        ax.spines[spine].set_linewidth(0.65)
    ax.tick_params(colors=COLORS["ink"], labelsize=8, width=0.65, length=3)
    ax.title.set_color(COLORS["ink"])
    ax.xaxis.label.set_color(COLORS["ink"])
    ax.yaxis.label.set_color(COLORS["ink"])


def add_y_grid(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=COLORS["line"], linewidth=0.45, alpha=0.55)
    ax.grid(axis="x", visible=False)


def pct_formatter(decimals: int = 0) -> FuncFormatter:
    return FuncFormatter(lambda v, pos: f"{v:.{decimals}f}%")


def panel_title(ax: plt.Axes, label: str, title: str, y: float = 1.06) -> None:
    ax.text(
        0.0,
        y,
        f"({label})",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.6,
        fontweight="bold",
        color=COLORS["ink"],
    )
    ax.text(
        0.075,
        y,
        title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.2,
        fontweight="semibold",
        color=COLORS["ink"],
    )


def apply_percent_ticks(ax: plt.Axes, axis: str = "y", ticks: list[int] | None = None) -> None:
    ticks = ticks or [0, 25, 50, 75, 100]
    locator = FixedLocator(ticks)
    formatter = pct_formatter()
    if axis == "y":
        ax.yaxis.set_major_locator(locator)
        ax.yaxis.set_major_formatter(formatter)
    else:
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)


def aggregate_family_report(report_tiers: pd.DataFrame) -> pd.DataFrame:
    main = preferred_report_rows(report_tiers)
    rows = []
    for suite, g in main.groupby("suite", sort=False):
        runs = g["runs"].sum()
        rows.append(
            {
                "suite": suite,
                "suite_label": suite_label(suite),
                "runs": runs,
                "formal_mean": np.average(g["formal_mean"], weights=g["runs"]),
                "stepwise_mean": np.average(g["stepwise_mean"], weights=g["runs"]),
                "full_pass": g["full_pass"].sum(),
                "full_total": g["full_total"].sum(),
                "full_pass_rate": g["full_pass"].sum() / g["full_total"].sum(),
            }
        )
    return pd.DataFrame(rows)


def plot_reported_main_overview(report_tiers: pd.DataFrame) -> None:
    df = aggregate_family_report(report_tiers)
    order = suite_label_order(set(df["suite_label"]))
    df["suite_label"] = ordered_categories(df["suite_label"], order)
    df = df.sort_values("suite_label").reset_index(drop=True)
    plot_df = df.melt(
        id_vars=["suite_label", "full_pass", "full_total", "full_pass_rate", "runs"],
        value_vars=["formal_mean", "stepwise_mean"],
        var_name="metric",
        value_name="score",
    )
    plot_df["metric"] = plot_df["metric"].map(
        {"formal_mean": "Scenario-level conformance", "stepwise_mean": "Step-level progress"}
    )
    fig, ax = plt.subplots(figsize=(6.6, 3.45))
    sns.barplot(
        data=plot_df,
        x="suite_label",
        y="score",
        hue="metric",
        order=order,
        palette=[COLORS["teal"], COLORS["teal_light"]],
        ax=ax,
    )
    ax.set_ylim(0, 0.68)
    ax.set_ylabel("Mean score")
    ax.set_xlabel("")
    ax.set_title("Partial progress outpaces full behavioral conformance")
    ax.yaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    for i, row in df.reset_index(drop=True).iterrows():
        y = min(max(row.formal_mean, row.stepwise_mean) + 0.045, 0.62)
        ax.text(
            i,
            y,
            f"{int(row.full_pass)}/{int(row.full_total)} full conformance",
            ha="center",
            va="bottom",
            fontsize=8,
            color=COLORS["muted"],
        )
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.03), ncols=2)
    strip_background(ax)
    save_figure(
        fig,
        "reported_main_score_gap_by_family",
        "appendix",
        "Product-family score gap between strict scenario-level conformance and step-level progress.",
        "Appendix or secondary Results: compact aggregate evidence for the core claim.",
    )


def plot_reported_tier_ladder(report_tiers: pd.DataFrame) -> None:
    df = preferred_report_rows(report_tiers)
    df["tier"] = ordered_categories(df["tier"], TIER_ORDER)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.25), sharey=True)
    for ax, metric, title in [
        (axes[0], "formal_mean", "Scenario-level conformance"),
        (axes[1], "stepwise_mean", "Step-level progress"),
    ]:
        sns.lineplot(
            data=df,
            x="tier",
            y=metric,
            hue="suite_label",
            marker="o",
            linewidth=2,
            palette=categorical_palette(df["suite_label"].nunique()),
            ax=ax,
        )
        ax.set_title(title)
        ax.set_xlabel("Complexity variant")
        ax.set_ylabel("Mean score" if metric == "formal_mean" else "")
        ax.yaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
        ax.set_ylim(0, 0.62)
        strip_background(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    for ax in axes:
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()
    fig.legend(handles, labels, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncols=min(4, len(labels)))
    fig.subplots_adjust(top=0.78, wspace=0.20)
    save_figure(
        fig,
        "reported_main_complexity_ladder",
        "appendix",
        "Scenario-level conformance and step-level progress across complexity variants.",
        "Appendix or secondary Results: supports the tier-ladder narrative.",
    )


def plot_reported_full_pass_heatmap(report_tiers: pd.DataFrame) -> None:
    df = preferred_report_rows(report_tiers)
    matrix = df.pivot(index="suite_label", columns="tier", values="full_pass_rate")
    matrix = matrix.reindex(suite_label_order(set(matrix.index)))
    matrix = matrix.reindex(columns=TIER_ORDER)
    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    sns.heatmap(
        matrix * 100,
        annot=True,
        fmt=".1f",
        cmap=HEAT_CMAP,
        cbar_kws={"label": "Full-conformance rate (%)"},
        linewidths=0.45,
        linecolor="#F4F1EB",
        ax=ax,
    )
    ax.set_xlabel("Complexity variant")
    ax.set_ylabel("")
    ax.set_title("Full conformance remains scarce")
    save_figure(
        fig,
        "reported_main_full_pass_heatmap",
        "appendix",
        "Full-conformance rate by product family and complexity variant.",
        "Appendix or secondary Results: a small heatmap that makes the low full-pass rate memorable.",
    )


def plot_reported_model_tier_matrix(report_models: pd.DataFrame) -> None:
    df = preferred_report_rows(report_models)
    df["row"] = df["suite_label"] + " " + df["tier"]
    order = target_label_order(df, label_col="suite_label", tier_col="tier")
    matrix = df.pivot(index="row", columns="model_tier", values="formal_mean").reindex(order)
    matrix = matrix.reindex(columns=MODEL_TIER_ORDER)
    fig, ax = plt.subplots(figsize=(4.8, 6.0))
    sns.heatmap(
        matrix * 100,
        annot=True,
        fmt=".1f",
        cmap=HEAT_CMAP,
        cbar_kws={"label": "Scenario-level conformance (%)"},
        linewidths=0.45,
        linecolor="#F4F1EB",
        ax=ax,
    )
    ax.set_xlabel("Model group")
    ax.set_ylabel("")
    ticks = ax.get_xticks()
    ax.set_xticks(ticks, [MODEL_TIER_LABELS.get(c.get_text(), c.get_text()) for c in ax.get_xticklabels()])
    ax.set_title("Capability helps, but does not close the conformance gap")
    save_figure(
        fig,
        "reported_main_model_tier_matrix",
        "appendix",
        "Scenario-level conformance by benchmark instance and model group.",
        "Appendix or secondary Results: compact model-group comparison.",
    )


def plot_suite_complexity(metrics: pd.DataFrame) -> None:
    df = metrics.copy()
    df["target"] = df["suite_label"] + " " + df["tier"]
    order = target_label_order(df, label_col="suite_label", tier_col="tier")
    cols = [
        "pages",
        "scenario_count",
        "max_steps",
        "components",
        "component_actions",
        "state_fields",
        "services",
        "tables",
        "derived_relations",
    ]
    matrix = df.set_index("target").reindex(order)[cols]
    norm = (matrix - matrix.min()) / (matrix.max() - matrix.min())
    fig, ax = plt.subplots(figsize=(8.0, 6.2))
    sns.heatmap(
        norm,
        annot=matrix,
        fmt=".0f",
        cmap=COMPLEXITY_CMAP,
        linewidths=0.45,
        linecolor="#F4F1EB",
        cbar_kws={"label": "Column-normalized size"},
        ax=ax,
    )
    ax.set_title("Complexity variants expand behavioral surface, not only pages")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ticks = ax.get_xticks()
    ax.set_xticks(
        ticks,
        [
            "pages",
            "tests",
            "max steps",
            "components",
            "actions",
            "state fields",
            "services",
            "tables",
            "derived",
        ],
        rotation=35,
        ha="right",
    )
    save_figure(
        fig,
        "suite_complexity_matrix",
        "appendix",
        "Contract and interaction-test complexity metrics extracted from benchmark instance files.",
        "Benchmark Suite or Appendix: explains what changes across variants.",
    )


def plot_main_benchmark_suite_anatomy(metrics: pd.DataFrame, scenarios: pd.DataFrame) -> None:
    inv = target_inventory(metrics, scenarios)
    inv = inv[inv["tier"].isin(TIER_ORDER)].copy()
    terrain = scenario_terrain_data(scenarios)
    families = suite_label_order(set(inv["suite_label"]))
    tier_to_x = {tier: i for i, tier in enumerate(TIER_ORDER)}
    family_to_y = {family: len(families) - 1 - i for i, family in enumerate(families)}
    fig, ax = plt.subplots(figsize=(8.35, 5.65))

    ax.set_title("Benchmark Suite Terrain", loc="left", fontsize=13, fontweight="semibold", pad=12)
    ax.set_xlim(-0.72, len(TIER_ORDER) + 0.86)
    ax.set_ylim(-0.72, len(families) - 0.10)
    ax.set_xticks(range(len(TIER_ORDER)), TIER_ORDER)
    ax.set_yticks([family_to_y[f] for f in families], families)
    ax.set_xlabel("Complexity variant")
    ax.set_ylabel("")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    max_steps = inv["max_steps"].fillna(0)
    max_step_global = max(1.0, float(terrain["step_count"].max() if not terrain.empty else max_steps.max()))
    surface_cols = [
        ("P", "pages"),
        ("A", "component_actions"),
        ("S", "state_fields"),
        ("R", "derived_relations"),
        ("V", "services"),
        ("T", "tables"),
    ]
    surface_max = {col: max(1.0, float(inv[col].fillna(0).max())) for _, col in surface_cols}
    surface_score_cols = [col for _, col in surface_cols]
    feature_labels = [
        ("R", "roles"),
        ("S", "services_feature"),
        ("T", "tables_feature"),
        ("P", "persistence_feature"),
        ("U", "upload_feature"),
        ("D", "derived_feature"),
    ]
    bucket_x = {"core": -0.25, "state": -0.08, "runtime": 0.09, "journey": 0.26}
    visibility_color = {"public": COLORS["teal_light"], "held-out": COLORS["teal"]}

    for family in families:
        for tier in TIER_ORDER:
            x = tier_to_x[tier]
            y = family_to_y[family]
            ax.add_patch(
                plt.Rectangle(
                    (x - 0.44, y - 0.39),
                    0.88,
                    0.78,
                    facecolor="#FBFAF7",
                    edgecolor="#D8DDD9",
                    linewidth=0.8,
                    zorder=0,
                )
            )
            row = inv[(inv["suite_label"] == family) & (inv["tier"] == tier)]
            if row.empty:
                ax.text(x, y, "N/A", ha="center", va="center", fontsize=7, color=COLORS["muted"])
                continue
            r = row.iloc[0]
            steps = int(r.get("max_steps", 0) or 0)
            cell = terrain[(terrain["suite_label"] == family) & (terrain["tier"] == tier)].copy()
            if not cell.empty:
                for idx, srow in cell.reset_index(drop=True).iterrows():
                    bucket = srow["bucket"]
                    jitter = (((idx * 37) % 17) - 8) / 17 * 0.065
                    px = x + bucket_x.get(bucket, 0.0) + jitter
                    py = y - 0.30 + 0.53 * min(float(srow["step_count"]) / max_step_global, 1.0)
                    color = visibility_color.get(str(srow["visibility"]), COLORS["teal"])
                    marker_size = 14 + 36 * min(float(srow["step_count"]) / max_step_global, 1.0)
                    ax.scatter(
                        [px],
                        [py],
                        s=marker_size,
                        color=color,
                        edgecolor="white",
                        linewidth=0.30,
                        alpha=0.86,
                        zorder=3,
                    )
            tests = len(cell) if not cell.empty else int(r.get("scenario_count", 0) or 0)
            ax.text(
                x - 0.36,
                y + 0.31,
                f"{tests} tests",
                ha="left",
                va="center",
                fontsize=6.6,
                color=COLORS["ink"],
                fontweight="semibold",
            )
            ax.text(
                x + 0.37,
                y + 0.31,
                f"{steps} max",
                ha="right",
                va="center",
                fontsize=6.4,
                color=COLORS["muted"],
            )

            normalized_surface = [
                min(float(r.get(col, 0) or 0) / surface_max[col], 1.0)
                for col in surface_score_cols
            ]
            surface_score = float(np.mean(normalized_surface))
            rail_h = 0.10 + 0.54 * surface_score
            ax.add_patch(
                plt.Rectangle(
                    (x + 0.385, y - 0.31),
                    0.030,
                    rail_h,
                    facecolor=COLORS["sage"],
                    edgecolor="none",
                    alpha=0.92,
                    zorder=2,
                )
            )

            chip_x0 = x - 0.35
            for idx, (label, field) in enumerate(feature_labels):
                active = bool(r.get(field))
                cx = chip_x0 + idx * 0.115
                ax.text(
                    cx,
                    y - 0.34,
                    label,
                    ha="center",
                    va="center",
                    fontsize=5.4,
                    color="white" if active else "#9EA9AE",
                    bbox={
                        "boxstyle": "round,pad=0.16",
                        "facecolor": COLORS["teal"] if active else "#EEF2F1",
                        "edgecolor": "none",
                    },
                )

    legend_x = len(TIER_ORDER) + 0.10
    legend_y = len(families) - 0.62
    ax.text(legend_x, legend_y, "Encodings", fontsize=9.2, fontweight="semibold", color=COLORS["ink"])
    ax.scatter([legend_x + 0.05], [legend_y - 0.28], s=45, color=COLORS["teal_light"], edgecolor="white", linewidth=0.30)
    ax.text(legend_x + 0.16, legend_y - 0.28, "public interaction test", va="center", fontsize=7.1, color=COLORS["muted"])
    ax.scatter([legend_x + 0.05], [legend_y - 0.55], s=45, color=COLORS["teal"], edgecolor="white", linewidth=0.30)
    ax.text(legend_x + 0.16, legend_y - 0.55, "held-out interaction test", va="center", fontsize=7.1, color=COLORS["muted"])
    ax.plot([legend_x, legend_x + 0.55], [legend_y - 0.84, legend_y - 0.84], color="#C9D7CE", linewidth=1)
    for idx, bucket in enumerate(["core", "state", "runtime", "journey"]):
        ax.text(legend_x + idx * 0.16, legend_y - 0.99, bucket, rotation=28, ha="center", va="top", fontsize=5.8, color=COLORS["muted"])
    ax.text(legend_x + 0.62, legend_y - 0.84, "semantic lanes", va="center", fontsize=7.1, color=COLORS["muted"])
    ax.add_patch(plt.Rectangle((legend_x + 0.02, legend_y - 1.42), 0.035, 0.46, facecolor=COLORS["sage"], edgecolor="none"))
    ax.text(legend_x + 0.16, legend_y - 1.19, "contract surface rail", va="center", fontsize=7.1, color=COLORS["muted"])
    ax.text(
        -0.58,
        -0.57,
        "One dot = one interaction test; vertical position = browser-step length. Feature chips: R role, S service, T table, P persistence, U upload, D derived relation.",
        fontsize=7.0,
        color=COLORS["muted"],
        ha="left",
        va="center",
    )
    save_figure(
        fig,
        "main_benchmark_suite_anatomy",
        "main",
        "Full-width benchmark-suite anatomy: product families, complexity variants, behavioral coverage, scenario horizons, and held-out tests.",
        "Main Benchmark Suite: shows that ConformWeb varies behavioral coupling rather than only visual surface.",
    )


def plot_main_model_tier_results(report_models: pd.DataFrame) -> None:
    df = preferred_report_rows(report_models)
    df = df[df["model_tier"].isin(MODEL_TIER_ORDER)].copy()
    df["row"] = df["suite_label"] + " " + df["tier"]
    order = target_label_order(df, label_col="suite_label", tier_col="tier")
    formal = df.pivot(index="row", columns="model_tier", values="formal_mean").reindex(order).reindex(columns=MODEL_TIER_ORDER)
    stepwise = df.pivot(index="row", columns="model_tier", values="stepwise_mean").reindex(order).reindex(columns=MODEL_TIER_ORDER)
    full = df.pivot(index="row", columns="model_tier", values="full_pass").reindex(order).reindex(columns=MODEL_TIER_ORDER)
    total = df.pivot(index="row", columns="model_tier", values="full_total").reindex(order).reindex(columns=MODEL_TIER_ORDER)

    fig, ax = plt.subplots(figsize=(6.25, 6.25))
    sns.heatmap(
        formal * 100,
        annot=False,
        cmap=HEAT_CMAP,
        vmin=0,
        vmax=90,
        linewidths=0.45,
        linecolor="#F4F1EB",
        cbar=True,
        cbar_kws={"label": "Scenario-level conformance (%)"},
        ax=ax,
    )
    for i, row_label in enumerate(formal.index):
        for j, col in enumerate(formal.columns):
            if pd.isna(formal.loc[row_label, col]):
                ax.text(j + 0.5, i + 0.5, "n/a", ha="center", va="center", fontsize=7, color=COLORS["muted"])
                continue
            f = formal.loc[row_label, col] * 100
            s = stepwise.loc[row_label, col] * 100
            fp = int(full.loc[row_label, col]) if not pd.isna(full.loc[row_label, col]) else 0
            ft = int(total.loc[row_label, col]) if not pd.isna(total.loc[row_label, col]) else 0
            text_color = "white" if f >= 45 else COLORS["ink"]
            ax.text(
                j + 0.5,
                i + 0.38,
                f"{f:.0f}%",
                ha="center",
                va="center",
                fontsize=8.2,
                fontweight="bold",
                color=text_color,
            )
            ax.text(
                j + 0.5,
                i + 0.64,
                f"step {s:.0f}% | full {fp}/{ft}",
                ha="center",
                va="center",
                fontsize=5.8,
                color=text_color,
            )
    ax.set_title("Model-tier outcomes by benchmark instance", fontsize=12, fontweight="semibold", pad=12)
    ax.set_xlabel("Model group")
    ax.set_ylabel("")
    ax.set_xticks(ax.get_xticks(), [MODEL_TIER_LABELS.get(t, t) for t in MODEL_TIER_ORDER], rotation=0)
    ax.set_yticks(ax.get_yticks(), formal.index, rotation=0, fontsize=7.6)
    ax.text(
        0.0,
        -0.095,
        "Each cell: top = scenario-level conformance; bottom = step-level progress and full-conformance count.",
        transform=ax.transAxes,
        fontsize=7.2,
        color=COLORS["muted"],
        ha="left",
        va="top",
    )
    fig.subplots_adjust(left=0.22, bottom=0.12, right=0.98, top=0.92)
    save_figure(
        fig,
        "main_model_tier_results",
        "main",
        "Benchmark-by-model-tier outcome matrix; cell color is scenario-level conformance, text adds step-level progress and full-conformance counts.",
        "Main Results: shows progress, strict conformance, and full-pass scarcity across model tiers.",
    )


def select_audit_example(df: pd.DataFrame) -> pd.Series:
    candidates = df.copy()
    candidates = candidates[candidates["first_failure_before_screenshot"].fillna("").astype(str).map(lambda p: Path(p).exists())]
    candidates = candidates[candidates["first_failure_after_screenshot"].fillna("").astype(str).map(lambda p: Path(p).exists())]
    preferred = candidates[
        (candidates["suite_label"] == "FreshCart")
        & (candidates["tier"] == "C")
        & (candidates["first_failure_group"] == "wrong state transition")
    ]
    if not preferred.empty:
        candidates = preferred
    candidates = candidates.copy()
    candidates["model_rank"] = candidates["model_tier"].map({"F": 0, "T": 1, "M": 2}).fillna(9)
    candidates["progress_rank"] = candidates["step_progress_until_failure"].fillna(-1)
    return candidates.sort_values(["model_rank", "progress_rank", "expected_step_count"], ascending=[True, False, False]).iloc[0]


def plot_main_audit_analysis(scenarios: pd.DataFrame) -> None:
    df = view_filter(scenarios, "current_raw")
    df = df[(df["kind"] == "scoring") & (~df["scenario_passed"])].copy()
    if df.empty:
        return
    df["failure_short"] = df["first_failure_group"].map(short_failure_label)
    df["action_short"] = (
        df["first_failed_action"]
        .fillna("observation")
        .astype(str)
        .replace({"unknown": "observation", "nan": "observation", "": "observation"})
        .str.replace("_", " ", regex=False)
        .str.replace("click", "click", regex=False)
    )
    fig = plt.figure(figsize=(8.25, 6.0), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, height_ratios=[0.95, 1.25], width_ratios=[1.04, 1.06, 1.10])
    ax_cat = fig.add_subplot(gs[0, 0])
    ax_pos = fig.add_subplot(gs[0, 1])
    ax_family = fig.add_subplot(gs[0, 2])
    ax_action = fig.add_subplot(gs[1, :2])
    ax_late = fig.add_subplot(gs[1, 2])

    counts = df["failure_short"].value_counts().sort_values()
    ax_cat.barh(counts.index, counts.values, color=COLORS["teal"])
    ax_cat.set_title("First failing check", fontsize=10, fontweight="semibold")
    ax_cat.set_xlabel("Failed interaction tests")
    ax_cat.set_ylabel("")
    strip_background(ax_cat)

    pos_df = df[df["step_progress_until_failure"].notna()].copy()
    sns.histplot(
        data=pos_df,
        x="step_progress_until_failure",
        hue="model_tier",
        hue_order=MODEL_TIER_ORDER,
        palette=[COLORS["rose"], COLORS["amber"], COLORS["teal"]],
        bins=np.linspace(0, 1, 9),
        multiple="stack",
        ax=ax_pos,
    )
    ax_pos.xaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax_pos.set_title("Where failures occur", fontsize=10, fontweight="semibold")
    ax_pos.set_xlabel("Trace completed")
    ax_pos.set_ylabel("Failures")
    style_existing_legend(ax_pos, title="Model group")
    strip_background(ax_pos)

    fam = (
        df.groupby(["suite_label", "failure_short"], observed=True)
        .size()
        .reset_index(name="count")
    )
    fam["share"] = fam["count"] / fam.groupby("suite_label", observed=True)["count"].transform("sum")
    matrix = fam.pivot(index="suite_label", columns="failure_short", values="share").fillna(0)
    matrix = matrix.reindex(suite_label_order(set(matrix.index)))
    matrix = matrix[matrix.sum(axis=0).sort_values(ascending=False).index]
    sns.heatmap(
        matrix * 100,
        cmap=FAIL_CMAP,
        annot=True,
        fmt=".0f",
        cbar=False,
        linewidths=0.45,
        linecolor="#F4F1EB",
        ax=ax_family,
    )
    ax_family.set_title("Failure mix by family (%)", fontsize=10, fontweight="semibold")
    ax_family.set_xlabel("")
    ax_family.set_ylabel("")
    ax_family.set_xticks(ax_family.get_xticks(), ax_family.get_xticklabels(), rotation=32, ha="right", fontsize=7)
    ax_family.set_yticks(ax_family.get_yticks(), ax_family.get_yticklabels(), rotation=0, fontsize=8)

    action_counts = df["action_short"].value_counts()
    top_actions = list(action_counts.head(9).index)
    action_df = df[df["action_short"].isin(top_actions)].copy()
    action_matrix = (
        action_df.groupby(["action_short", "failure_short"], observed=True)
        .size()
        .reset_index(name="count")
        .pivot(index="action_short", columns="failure_short", values="count")
        .fillna(0)
    )
    action_matrix = action_matrix.reindex(action_counts.loc[top_actions].index)
    action_matrix = action_matrix[action_matrix.sum(axis=0).sort_values(ascending=False).index]
    action_share = action_matrix.div(action_matrix.sum(axis=0).replace(0, np.nan), axis=1).fillna(0) * 100
    sns.heatmap(
        action_share,
        cmap=FAIL_CMAP,
        annot=True,
        fmt=".0f",
        cbar_kws={"label": "Share within failure category (%)"},
        linewidths=0.45,
        linecolor="#F4F1EB",
        ax=ax_action,
    )
    ax_action.set_title("Which browser action exposes each failure type?", fontsize=10, fontweight="semibold")
    ax_action.set_xlabel("Failure category")
    ax_action.set_ylabel("First failed action")
    ax_action.set_xticks(ax_action.get_xticks(), ax_action.get_xticklabels(), rotation=26, ha="right", fontsize=7)
    ax_action.set_yticks(ax_action.get_yticks(), ax_action.get_yticklabels(), rotation=0, fontsize=7.4)

    late_df = df[df["step_progress_until_failure"].notna()].copy()
    top_failures = list(df["failure_short"].value_counts().head(5).index)
    late_df = late_df[late_df["failure_short"].isin(top_failures)].copy()
    order = (
        late_df.groupby("failure_short", observed=True)["step_progress_until_failure"]
        .median()
        .sort_values()
        .index
    )
    sns.boxplot(
        data=late_df,
        y="failure_short",
        x="step_progress_until_failure",
        order=order,
        color="#DCEBE8",
        fliersize=1.5,
        linewidth=0.8,
        ax=ax_late,
    )
    sns.stripplot(
        data=late_df.sample(min(len(late_df), 1800), random_state=7),
        y="failure_short",
        x="step_progress_until_failure",
        order=order,
        color=COLORS["teal"],
        alpha=0.20,
        size=1.5,
        jitter=0.16,
        ax=ax_late,
    )
    ax_late.xaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax_late.set_title("How late each failure appears", fontsize=10, fontweight="semibold")
    ax_late.set_xlabel("Trace completed")
    ax_late.set_ylabel("")
    strip_background(ax_late)
    save_figure(
        fig,
        "main_audit_analysis",
        "main",
        "Failure analysis figure combining first-failure categories, failure position, family-level failure mix, action-by-category evidence, and category-level lateness.",
        "Main Error Analysis: demonstrates that ConformWeb yields auditable failure evidence, not only scalar scores.",
    )


def plot_figure2_conformance_gap(report_tiers: pd.DataFrame) -> None:
    df = preferred_report_rows(report_tiers)
    rows: list[dict[str, Any]] = []
    for suite, group in df.groupby("suite", sort=False):
        runs = group["runs"].sum()
        if runs <= 0:
            continue
        scen = np.average(group["formal_mean"], weights=group["runs"])
        step = np.average(group["stepwise_mean"], weights=group["runs"])
        rows.append(
            {
                "suite": suite,
                "domain": domain_label(suite),
                "scenario": scen,
                "step": step,
                "gap": step - scen,
                "runs": runs,
            }
        )
    plot_df = pd.DataFrame(rows).sort_values("gap", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot_df))

    fig, ax = plt.subplots(figsize=(5.55, 3.15))
    ax.hlines(
        y,
        plot_df["scenario"] * 100,
        plot_df["step"] * 100,
        color="#B9C9CA",
        linewidth=5.0,
        alpha=0.88,
        zorder=1,
    )
    ax.scatter(
        plot_df["scenario"] * 100,
        y,
        s=82,
        color=COLORS["rose"],
        edgecolor="white",
        linewidth=1.0,
        zorder=3,
        label=r"$S_{\mathrm{scen}}$",
    )
    ax.scatter(
        plot_df["step"] * 100,
        y,
        s=82,
        color=COLORS["teal"],
        edgecolor="white",
        linewidth=1.0,
        zorder=3,
        label=r"$S_{\mathrm{step}}$",
    )
    for yi, row in zip(y, plot_df.itertuples(index=False), strict=False):
        ax.text(
            row.step * 100 + 1.6,
            yi,
            f"+{row.gap * 100:.1f} pp",
            va="center",
            ha="left",
            fontsize=8,
            color=COLORS["muted"],
        )
    ax.set_yticks(y, plot_df["domain"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Mean score")
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(lambda v, pos: f"{v:.0f}%")
    ax.set_title("The Conformance Gap", loc="left", fontsize=12.5, fontweight="semibold", pad=10)
    ax.text(
        0.0,
        0.995,
        "Models often complete local browser steps without satisfying the full interaction test.",
        transform=ax.transAxes,
        fontsize=8.1,
        color=COLORS["muted"],
        ha="left",
        va="bottom",
    )
    ax.legend(
        frameon=False,
        loc="upper right",
        bbox_to_anchor=(0.98, 1.34),
        ncols=2,
        handletextpad=0.4,
        columnspacing=1.1,
        borderaxespad=0.0,
    )
    strip_background(ax)
    ax.spines["left"].set_visible(False)
    fig.subplots_adjust(left=0.29, right=0.98, top=0.74, bottom=0.18)
    save_figure(
        fig,
        "figure2_conformance_gap",
        "main",
        "Dumbbell plot comparing step-level progress against scenario-level conformance by benchmark domain.",
        "Main Figure 2: visualizes the central gap between partial progress and behavioral conformance.",
    )


def survival_curve(points: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    if points.empty:
        return np.array([0, 1]), np.array([1, 1])
    passed = points["scenario_passed"].astype(bool)
    times = points["step_progress_until_failure"].fillna(0).clip(0, 1)
    failure_times = np.sort(times[~passed].unique())
    xs = [0.0]
    ys = [1.0]
    for t in failure_times:
        xs.append(float(t))
        ys.append(float((passed | (times > t)).mean()))
    xs.append(1.0)
    ys.append(float(passed.mean()))
    return np.array(xs), np.array(ys)


def event_marker_positions(df: pd.DataFrame) -> list[tuple[str, float]]:
    markers = [
        ("upload", r"upload"),
        ("role gate", r"role|permission|authorize|manager|quality"),
        ("final approval", r"approve|dispatch|seal|place_order|submit"),
    ]
    rows: list[tuple[str, float]] = []
    components = df["first_failed_component"].fillna("").astype(str)
    actions = df["first_failed_action"].fillna("").astype(str)
    for label, pattern in markers:
        mask = components.str.contains(pattern, case=False, regex=True) | actions.str.contains(pattern, case=False, regex=True)
        subset = df[mask & df["step_progress_until_failure"].notna()]
        if len(subset) >= 20:
            rows.append((label, float(subset["step_progress_until_failure"].median())))
    return rows


def plot_figure3_error_dynamics(scenarios: pd.DataFrame) -> None:
    df = view_filter(scenarios, "current_raw")
    df = df[df["kind"] == "scoring"].copy()
    df["scenario_passed"] = df["scenario_passed"].astype(bool)
    df["step_progress_until_failure"] = pd.to_numeric(df["step_progress_until_failure"], errors="coerce")
    failures = df[~df["scenario_passed"]].copy()
    failures["failure_short"] = failures["first_failure_group"].map(short_failure_label)

    fig, (ax_surv, ax_stack) = plt.subplots(
        2,
        1,
        figsize=(7.2, 5.35),
        gridspec_kw={"height_ratios": [1.08, 1.0], "hspace": 0.46},
    )

    model_colors = {"M": COLORS["rose"], "T": COLORS["amber"], "F": COLORS["teal"]}
    for model_tier in MODEL_TIER_ORDER:
        subset = df[df["model_tier"] == model_tier]
        xs, ys = survival_curve(subset)
        ax_surv.step(
            xs * 100,
            ys * 100,
            where="post",
            linewidth=2.5,
            color=model_colors.get(model_tier, COLORS["muted"]),
            label=MODEL_TIER_LABELS.get(model_tier, model_tier),
        )
    for label, pos in event_marker_positions(failures):
        ax_surv.axvline(pos * 100, color=COLORS["line"], linestyle=":", linewidth=1.0, zorder=0)
        ax_surv.text(
            pos * 100 + 1.2,
            7,
            label,
            rotation=90,
            va="bottom",
            ha="left",
            fontsize=6.8,
            color=COLORS["muted"],
        )
    ax_surv.set_xlim(0, 100)
    ax_surv.set_ylim(0, 102)
    ax_surv.xaxis.set_major_formatter(lambda v, pos: f"{v:.0f}%")
    ax_surv.yaxis.set_major_formatter(lambda v, pos: f"{v:.0f}%")
    ax_surv.set_xlabel("Workflow progress")
    ax_surv.set_ylabel("Survival rate")
    ax_surv.set_title("(a) Workflow survival", loc="left", fontsize=11.2, fontweight="semibold")
    ax_surv.legend(frameon=False, loc="upper right", ncols=3, title="Model group")
    strip_background(ax_surv)

    categories = ["missing UI", "unactionable", "bad observation", "route drift", "projection mismatch", "wrong state"]
    category_colors = {
        "missing UI": COLORS["amber"],
        "unactionable": COLORS["orange"],
        "bad observation": COLORS["gray"],
        "route drift": COLORS["plum"],
        "projection mismatch": COLORS["cyan"],
        "wrong state": COLORS["rose"],
    }
    counts = (
        failures.groupby(["tier", "failure_short"], observed=True)
        .size()
        .reset_index(name="count")
        .pivot(index="tier", columns="failure_short", values="count")
        .reindex(TIER_ORDER)
        .fillna(0)
    )
    counts = counts.reindex(columns=categories).fillna(0)
    shares = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * 100
    bottoms = np.zeros(len(shares))
    x = np.arange(len(shares))
    for cat in categories:
        vals = shares[cat].to_numpy()
        ax_stack.bar(
            x,
            vals,
            bottom=bottoms,
            color=category_colors[cat],
            width=0.72,
            edgecolor="white",
            linewidth=0.7,
            label=cat,
        )
        for xi, val, bottom in zip(x, vals, bottoms, strict=False):
            if val >= 11:
                ax_stack.text(
                    xi,
                    bottom + val / 2,
                    f"{val:.0f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if cat in {"wrong state", "route drift", "projection mismatch"} else COLORS["ink"],
                    fontweight="semibold",
                )
        bottoms += vals
    ax_stack.set_xticks(x, [TIER_DISPLAY_LABELS.get(t, t) for t in TIER_ORDER])
    ax_stack.set_ylim(0, 100)
    ax_stack.yaxis.set_major_formatter(lambda v, pos: f"{v:.0f}%")
    ax_stack.set_xlabel("Complexity variant")
    ax_stack.set_ylabel("Failure composition")
    ax_stack.set_title("(b) Failure composition shifts with complexity", loc="left", fontsize=11.2, fontweight="semibold")
    ax_stack.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.26),
        ncols=3,
        fontsize=7.1,
        handlelength=1.2,
        columnspacing=1.0,
    )
    strip_background(ax_stack)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.95, bottom=0.20)
    save_figure(
        fig,
        "figure3_error_dynamics",
        "main",
        "Two-panel error-dynamics figure: Kaplan-Meier style workflow survival and 100% stacked failure composition by complexity variant.",
        "Main Figure 3: shows when generated runs fail and how failure types change with workflow complexity.",
    )


def aggregate_report_by_domain(report_tiers: pd.DataFrame) -> pd.DataFrame:
    df = paper_main_reported_rows(report_tiers)
    rows: list[dict[str, Any]] = []
    for suite, group in df.groupby("suite", sort=False):
        runs = float(group["runs"].sum())
        full = float(group["full_pass"].sum())
        total = float(group["full_total"].sum())
        rows.append(
            {
                "suite": suite,
                "domain": domain_label(suite),
                "runs": runs,
                "full_pass": full,
                "full_total": total,
                "full_pass_rate": full / total if total else np.nan,
                "scenario": np.average(group["formal_mean"], weights=group["runs"]),
                "step": np.average(group["stepwise_mean"], weights=group["runs"]),
            }
        )
    return pd.DataFrame(rows)


def plot_figure2_conformance_gap_wide(report_tiers: pd.DataFrame) -> None:
    family = aggregate_report_by_domain(report_tiers)
    df = paper_main_reported_rows(report_tiers).copy()
    suite_order = report_suite_order(df)
    domain_order = [domain_label(s) for s in suite_order]
    family["domain"] = pd.Categorical(family["domain"], categories=domain_order, ordered=True)
    family = family.sort_values("domain")
    total_runs = int(df["runs"].sum())
    full_pass = int(df["full_pass"].sum())
    full_total = int(df["full_total"].sum())
    generated_total = full_total if full_total else total_runs
    scenario = np.average(df["formal_mean"], weights=df["runs"])
    step = np.average(df["stepwise_mean"], weights=df["runs"])
    full_rate = full_pass / generated_total if generated_total else np.nan

    overall = pd.DataFrame(
        [
            {
                "suite": "overall",
                "domain": "Overall",
                "runs": generated_total,
                "full_pass": full_pass,
                "full_total": generated_total,
                "full_pass_rate": full_rate,
                "scenario": scenario,
                "step": step,
            }
        ]
    )
    rows = pd.concat([overall, family], ignore_index=True)
    rows["display"] = rows["domain"].map(short_family_label)

    fig, ax = plt.subplots(figsize=(7.55, 3.85))
    y = np.arange(len(rows))

    ax.hlines(y, rows["scenario"] * 100, rows["step"] * 100, color=CONNECTOR_COLOR, linewidth=3.0, zorder=1)
    ax.scatter(rows["full_pass_rate"] * 100, y, color=FULL_PASS_COLOR, s=42, edgecolor="white", linewidth=0.75, zorder=3)
    ax.scatter(rows["scenario"] * 100, y, color=SCENARIO_COLOR, s=46, edgecolor="white", linewidth=0.75, zorder=4)
    ax.scatter(rows["step"] * 100, y, color=STEP_COLOR, s=46, edgecolor="white", linewidth=0.75, zorder=4)

    for yi, row in zip(y, rows.itertuples(index=False), strict=False):
        x_text = min(max(float(row.full_pass_rate) * 100 + 1.5, 3.2), 62.0)
        ax.text(
            x_text,
            yi,
            f"{int(row.full_pass)}/{int(row.full_total):,}",
            ha="left",
            va="center",
            fontsize=7.0,
            color=COLORS["muted"],
        )

    ax.axhline(0.5, color=COLORS["line"], linewidth=0.8, alpha=0.9)
    ax.set_yticks(y, rows["display"], fontsize=8.0)
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.invert_yaxis()
    ax.set_xlim(0, 65)
    ax.xaxis.set_major_locator(FixedLocator([0, 15, 30, 45, 60]))
    ax.xaxis.set_major_formatter(pct_formatter())
    ax.set_xlabel("Score")
    ax.set_ylabel("")

    metric_handles = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=FULL_PASS_COLOR, markeredgecolor="white", markeredgewidth=0.7, markersize=6.0, label="Full pass"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=SCENARIO_COLOR, markeredgecolor="white", markeredgewidth=0.7, markersize=6.0, label="Scenario-level"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=STEP_COLOR, markeredgecolor="white", markeredgewidth=0.7, markersize=6.0, label="Step-level"),
    ]
    fig.legend(
        handles=metric_handles,
        frameon=False,
        ncols=3,
        loc="lower center",
        bbox_to_anchor=(0.56, 0.02),
        fontsize=7.2,
        handlelength=0.9,
        columnspacing=1.4,
        handletextpad=0.35,
    )
    strip_background(ax)
    ax.grid(axis="x", color=COLORS["line"], linewidth=0.45, alpha=0.45)
    ax.tick_params(axis="y", length=0)
    fig.subplots_adjust(left=0.20, right=0.985, top=0.95, bottom=0.20)
    save_figure(
        fig,
        "figure2_conformance_gap_wide",
        "reviewer_proposal",
        "Single wide score-profile plot with an Overall row and family-level rows; the scenario-to-step connector shows the partial-progress gap.",
        "Main Figure 2: full-width integrated conformance-gap figure for a LaTeX figure* environment.",
    )


def bootstrap_proportion_ci(successes: int, total: int, n_boot: int = 5000, seed: int = 17) -> tuple[float, float]:
    if total <= 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    values = np.concatenate([np.ones(successes), np.zeros(total - successes)])
    samples = rng.choice(values, size=(n_boot, total), replace=True).mean(axis=1)
    return float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def plot_reviewer_figure3_model_capability(report_models: pd.DataFrame) -> None:
    df = paper_main_reported_rows(report_models)
    plot_df = df.melt(
        id_vars=["suite", "suite_label", "tier", "model_tier", "model_tier_label"],
        value_vars=["formal_mean", "stepwise_mean"],
        var_name="metric",
        value_name="score",
    )
    plot_df["metric"] = plot_df["metric"].map(
        {"formal_mean": "Scenario-level", "stepwise_mean": "Step-level"}
    )
    plot_df["score_pct"] = plot_df["score"] * 100
    plot_df["model_tier"] = ordered_categories(plot_df["model_tier"], MODEL_TIER_ORDER)

    fig, (ax_box, ax_full) = plt.subplots(1, 2, figsize=(7.25, 3.18), gridspec_kw={"width_ratios": [1.58, 1.0]})
    sns.boxplot(
        data=plot_df,
        x="model_tier",
        y="score_pct",
        hue="metric",
        order=MODEL_TIER_ORDER,
        palette=[SCENARIO_COLOR, STEP_COLOR],
        width=0.58,
        fliersize=0,
        linewidth=0.8,
        ax=ax_box,
    )
    sns.stripplot(
        data=plot_df,
        x="model_tier",
        y="score_pct",
        hue="metric",
        dodge=True,
        order=MODEL_TIER_ORDER,
        palette=[SCENARIO_COLOR, STEP_COLOR],
        alpha=0.42,
        size=3.0,
        edgecolor="white",
        linewidth=0.25,
        ax=ax_box,
    )
    handles, labels = ax_box.get_legend_handles_labels()
    legend = ax_box.get_legend()
    if legend is not None:
        legend.remove()
    fig.legend(
        handles[:2],
        labels[:2],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.48, 0.96),
        ncols=2,
        fontsize=6.9,
        handlelength=1.0,
        columnspacing=1.0,
    )
    ax_box.set_xticks(ax_box.get_xticks(), [MODEL_TIER_LABELS.get(t, t) for t in MODEL_TIER_ORDER])
    ax_box.yaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
    ax_box.yaxis.set_major_formatter(pct_formatter())
    ax_box.set_ylim(0, 102)
    ax_box.set_xlabel("Model group")
    ax_box.set_ylabel("Benchmark-instance average")
    panel_title(ax_box, "a", "Progress vs. conformance")
    strip_background(ax_box)
    add_y_grid(ax_box)

    rows = []
    for mt, group in df.groupby("model_tier", observed=True):
        success = int(group["full_pass"].sum())
        total = int(group["full_total"].sum())
        lo, hi = bootstrap_proportion_ci(success, total, seed=41 + MODEL_TIER_ORDER.index(mt))
        rows.append(
            {
                "model_tier": mt,
                "label": MODEL_TIER_LABELS.get(mt, mt),
                "rate": success / total if total else np.nan,
                "lo": lo,
                "hi": hi,
                "success": success,
                "total": total,
            }
        )
    full_df = pd.DataFrame(rows)
    full_df["model_tier"] = ordered_categories(full_df["model_tier"], MODEL_TIER_ORDER)
    full_df = full_df.sort_values("model_tier")
    x = np.arange(len(full_df))
    rates = full_df["rate"].to_numpy() * 100
    lo = full_df["lo"].to_numpy() * 100
    hi = full_df["hi"].to_numpy() * 100
    ax_full.bar(x, rates, color=[MODEL_TIER_COLORS[t] for t in full_df["model_tier"]], width=0.62, linewidth=0)
    ax_full.errorbar(
        x,
        rates,
        yerr=[rates - lo, hi - rates],
        fmt="none",
        ecolor=COLORS["ink"],
        elinewidth=1.0,
        capsize=3,
    )
    y_top = max(20, math.ceil((float(np.nanmax(hi)) + 5.0) / 5.0) * 5)
    for xi, row in zip(x, full_df.itertuples(index=False), strict=False):
        y_text = min(row.hi * 100 + 0.9, y_top - 1.0)
        ax_full.text(xi, y_text, f"{row.success}/{row.total}", ha="center", va="bottom", fontsize=7.4, color=COLORS["muted"])
    ax_full.set_xticks(x, full_df["label"])
    ax_full.yaxis.set_major_locator(FixedLocator(np.arange(0, y_top + 0.1, 5)))
    ax_full.yaxis.set_major_formatter(pct_formatter())
    ax_full.set_ylim(0, y_top)
    ax_full.set_xlabel("Model group")
    ax_full.set_ylabel("Full-pass rate")
    panel_title(ax_full, "b", "Full completion")
    strip_background(ax_full)
    add_y_grid(ax_full)
    fig.subplots_adjust(wspace=0.35, top=0.80, bottom=0.18, left=0.09, right=0.98)
    save_figure(
        fig,
        "reviewer_figure3_model_capability",
        "reviewer_proposal",
        "Two-panel model-capability figure: score distributions by model group and full-pass rates with bootstrap intervals.",
        "Reviewer-proposed Figure 3: stronger models improve progress more than full completion.",
    )


def plot_reviewer_figure4_complexity_ladder(report_tiers: pd.DataFrame) -> None:
    df = paper_main_reported_rows(report_tiers).copy()
    df["domain"] = df["suite"].map(domain_label)
    row_order = [domain_label(s) for s in report_suite_order(df)]
    matrix = df.pivot(index="domain", columns="tier", values="formal_mean").reindex(row_order).reindex(columns=TIER_ORDER)
    run_matrix = df.pivot(index="domain", columns="tier", values="runs").reindex(row_order).reindex(columns=TIER_ORDER)
    cmap = HEAT_CMAP.copy()
    cmap.set_bad(COLORS["gray_light"])
    fig, ax = plt.subplots(figsize=(7.35, 3.95))
    sns.heatmap(
        matrix * 100,
        annot=False,
        cmap=cmap,
        vmin=0,
        vmax=100,
        linewidths=0.6,
        linecolor="white",
        cbar_kws={"label": "Scenario-level conformance", "ticks": [0, 25, 50, 75, 100], "format": pct_formatter()},
        ax=ax,
    )
    for row_idx, domain in enumerate(matrix.index):
        for col_idx, tier in enumerate(matrix.columns):
            if pd.isna(matrix.loc[domain, tier]):
                ax.text(
                    col_idx + 0.5,
                    row_idx + 0.5,
                    "N/A",
                    ha="center",
                    va="center",
                    fontsize=8.0,
                    color=COLORS["muted"],
                )
                continue
            score = float(matrix.loc[domain, tier]) * 100
            runs = run_matrix.loc[domain, tier]
            ax.text(
                col_idx + 0.5,
                row_idx + 0.43,
                f"{score:.0f}%",
                ha="center",
                va="center",
                fontsize=8.7,
                color=COLORS["ink"],
            )
            ax.text(
                col_idx + 0.5,
                row_idx + 0.68,
                f"n={int(runs):,}" if pd.notna(runs) else "",
                ha="center",
                va="center",
                fontsize=5.8,
                color=COLORS["muted"],
            )
    tier_labels = [f"Tier {t}\n{TIER_DISPLAY_LABELS.get(t, t)}" for t in TIER_ORDER]
    ax.set_xticks(ax.get_xticks(), tier_labels, rotation=0, fontsize=7.6)
    ax.set_yticks(ax.get_yticks(), [short_family_label(t.get_text()) for t in ax.get_yticklabels()], rotation=0, fontsize=8.0)
    ax.set_xlabel("Complexity variant")
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelrotation=0)
    fig.subplots_adjust(left=0.22, right=0.91, top=0.94, bottom=0.22)
    save_figure(
        fig,
        "reviewer_figure4_complexity_ladder_heatmap",
        "reviewer_proposal",
        "Complexity ladder heatmap of scenario-level conformance by domain and variant.",
        "Reviewer-proposed Figure 4: summarizes conformance across behavioral coupling levels.",
    )


def failure_taxonomy_frame(scenarios: pd.DataFrame) -> pd.DataFrame:
    df = view_filter(scenarios, "current_raw")
    df = df[(df["kind"] == "scoring") & (~df["scenario_passed"])].copy()
    df["failure_short"] = df["first_failure_group"].map(short_failure_label)
    df["step_progress_until_failure"] = pd.to_numeric(df["step_progress_until_failure"], errors="coerce")
    return df


def plot_reviewer_figure5_first_failure_taxonomy(scenarios: pd.DataFrame) -> None:
    df = failure_taxonomy_frame(scenarios)
    df["failure_label"] = df["failure_short"].map(FAILURE_LABELS).fillna(df["failure_short"])
    categories = FAILURE_ORDER
    counts = (
        df.groupby(["tier", "failure_label"], observed=True)
        .size()
        .reset_index(name="count")
        .pivot(index="tier", columns="failure_label", values="count")
        .reindex(TIER_ORDER)
        .reindex(columns=categories)
        .fillna(0)
    )
    shares = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * 100
    fig, (ax_stack, ax_median) = plt.subplots(1, 2, figsize=(8.35, 3.75), gridspec_kw={"width_ratios": [1.22, 1.0]})
    y = np.arange(len(shares))
    left = np.zeros(len(shares))
    for cat in categories:
        vals = shares[cat].to_numpy()
        ax_stack.barh(
            y,
            vals,
            left=left,
            color=FAILURE_COLORS[cat],
            edgecolor="white",
            linewidth=0.7,
            label=cat,
        )
        left += vals
    ax_stack.set_yticks(y, [TIER_DISPLAY_LABELS.get(t, t) for t in TIER_ORDER])
    ax_stack.invert_yaxis()
    ax_stack.set_xlim(0, 100)
    ax_stack.xaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
    ax_stack.xaxis.set_major_formatter(pct_formatter())
    ax_stack.set_xlabel("Share of failed scenarios")
    ax_stack.set_ylabel("Complexity variant")
    panel_title(ax_stack, "a", "Failure mix by complexity")
    strip_background(ax_stack)
    ax_stack.grid(axis="x", color=COLORS["line"], linewidth=0.45, alpha=0.45)

    med = (
        df[df["step_progress_until_failure"].notna()]
        .groupby("failure_label", observed=True)["step_progress_until_failure"]
        .agg(["median", "count"])
        .reindex(categories)
        .dropna()
    )
    med["share"] = med["count"] / med["count"].sum()
    y_med = np.arange(len(med))
    med_colors = [FAILURE_COLORS[c] for c in med.index]
    ax_median.scatter(
        med["median"] * 100,
        y_med,
        s=55 + med["share"] * 950,
        color=med_colors,
        alpha=0.88,
        edgecolor="white",
        linewidth=0.65,
        zorder=3,
    )
    for yi, row in enumerate(med.itertuples()):
        ax_median.hlines(yi, 0, row.median * 100, color=COLORS["line"], linewidth=1.0, zorder=0)
        median_pct = row.median * 100
        if row.Index == "Projection mismatch":
            label_x = median_pct - 5.0
            label_ha = "right"
        elif row.Index == "Wrong transition":
            label_x = min(median_pct + 16.0, 91.0)
            label_ha = "left"
        else:
            label_x = min(median_pct + 7.0, 91.0)
            label_ha = "left"
        ax_median.text(
            label_x,
            yi,
            f"median {row.median:.0%}",
            va="center",
            ha=label_ha,
            fontsize=6.8,
            color=COLORS["muted"],
        )
    median_labels = [
        str(label)
        .replace("Invalid observation", "Invalid\nobservation")
        .replace("Unavailable control", "Unavailable\ncontrol")
        .replace("Route/persistence drift", "Route/\npersistence drift")
        .replace("Projection mismatch", "Projection\nmismatch")
        for label in med.index
    ]
    ax_median.set_yticks(y_med, median_labels)
    ax_median.invert_yaxis()
    ax_median.set_xlim(0, 100)
    ax_median.xaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
    ax_median.xaxis.set_major_formatter(pct_formatter())
    ax_median.set_xlabel("Median normalized first-failure step")
    panel_title(ax_median, "b", "Failure timing")
    ax_median.text(0.0, 1.005, "Bubble size = share of failed scenarios", transform=ax_median.transAxes, fontsize=6.9, color=COLORS["muted"], ha="left", va="bottom")
    strip_background(ax_median)
    ax_median.spines["left"].set_visible(False)
    ax_median.grid(axis="x", color=COLORS["line"], linewidth=0.45, alpha=0.45)
    legend_handles = [Patch(facecolor=FAILURE_COLORS[cat], edgecolor="none", label=cat) for cat in categories]
    fig.legend(
        handles=legend_handles,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.035),
        ncols=3,
        fontsize=6.9,
        handlelength=1.0,
        columnspacing=1.3,
        handletextpad=0.45,
    )
    fig.subplots_adjust(wspace=0.82, bottom=0.29, top=0.86)
    save_figure(
        fig,
        "reviewer_figure5_first_failure_taxonomy",
        "reviewer_proposal",
        "First-failure taxonomy with complexity-stage composition and median normalized first-failure step by category.",
        "Reviewer-proposed Figure 5: explains why generated runs fail.",
    )


def plot_reviewer_figure6_long_horizon_survival(scenarios: pd.DataFrame) -> None:
    df = view_filter(scenarios, "current_raw")
    df = df[df["kind"] == "scoring"].copy()
    df["scenario_passed"] = df["scenario_passed"].astype(bool)
    df["step_progress_until_failure"] = pd.to_numeric(df["step_progress_until_failure"], errors="coerce")
    failures = df[~df["scenario_passed"]].copy()
    fig, ax = plt.subplots(figsize=(7.0, 3.15))
    curve_ends: list[tuple[str, float, str]] = []
    for model_tier in MODEL_TIER_ORDER:
        subset = df[df["model_tier"] == model_tier]
        xs, ys = survival_curve(subset)
        ax.step(
            xs * 100,
            ys * 100,
            where="post",
            linewidth=2.45,
            color=MODEL_TIER_COLORS[model_tier],
            label=MODEL_TIER_LABELS[model_tier],
        )
        curve_ends.append((MODEL_TIER_LABELS[model_tier], float(ys[-1] * 100), MODEL_TIER_COLORS[model_tier]))
    for label, pos in event_marker_positions(failures):
        ax.axvline(pos * 100, color=COLORS["line"], linestyle=":", linewidth=0.8, alpha=0.45)
        ax.text(pos * 100, 99.0, label, rotation=0, va="top", ha="center", fontsize=6.5, color=COLORS["muted"])
    for label, y_end, color in curve_ends:
        ax.text(101.2, y_end, label, color=color, fontsize=7.6, va="center", ha="left", clip_on=False)
    ax.set_xlim(0, 108)
    ax.set_ylim(0, 102)
    ax.xaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
    ax.yaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
    ax.xaxis.set_major_formatter(pct_formatter())
    ax.yaxis.set_major_formatter(pct_formatter())
    ax.set_xlabel("Normalized scenario progress")
    ax.set_ylabel("Scenarios not yet failed")
    strip_background(ax)
    add_y_grid(ax)
    fig.subplots_adjust(left=0.11, right=0.88, top=0.93, bottom=0.20)
    save_figure(
        fig,
        "reviewer_figure6_long_horizon_survival",
        "reviewer_proposal",
        "Standalone long-horizon survival curve by model group with workflow event markers.",
        "Reviewer-proposed Figure 6: visualizes near-misses and long-horizon drift.",
    )


def plot_appendix_a1_per_model_heatmap(
    runs: pd.DataFrame,
    report_tiers: pd.DataFrame,
    report_models: pd.DataFrame,
) -> None:
    del runs
    df = paper_main_reported_rows(report_models).copy()
    if df.empty:
        return
    df["tier"] = df["tier"].astype(str).str.strip()
    df["target"] = df["suite"].map(domain_label) + " " + df["tier"].astype(str)
    df["_suite_rank"] = df["suite"].map({s: i for i, s in enumerate(discovered_suite_order())}).fillna(999)
    df["_tier_rank"] = df["tier"].map({t: i for i, t in enumerate(TIER_ORDER)}).fillna(999)
    order: list[str] = []
    target_rows = preferred_report_rows(report_tiers).copy()
    if target_rows.empty:
        target_rows = df[["suite", "tier"]].drop_duplicates().copy()
    target_suites = sorted(
        target_rows["suite"].dropna().unique(),
        key=lambda s: (df.loc[df["suite"] == s, "_suite_rank"].min() if (df["suite"] == s).any() else 999, str(s)),
    )
    for suite in target_suites:
        for tier in TIER_ORDER:
            label = f"{domain_label(suite)} {tier}"
            has_target = ((target_rows["suite"] == suite) & (target_rows["tier"] == tier)).any()
            if has_target:
                order.append(label)
    order.extend(sorted(set(df["target"]) - set(order)))
    group_order = [MODEL_TIER_LABELS[t] for t in MODEL_TIER_ORDER]
    matrix = df.pivot(index="model_tier_label", columns="target", values="formal_mean").reindex(group_order).reindex(columns=order)
    run_matrix = df.pivot(index="model_tier_label", columns="target", values="runs").reindex(group_order).reindex(columns=order)
    cmap = HEAT_CMAP.copy()
    cmap.set_bad(COLORS["gray_light"])
    fig, ax = plt.subplots(figsize=(9.6, 3.15))
    sns.heatmap(
        matrix * 100,
        cmap=cmap,
        annot=False,
        vmin=0,
        vmax=100,
        linewidths=0.35,
        linecolor="white",
        cbar_kws={"label": "Scenario-level conformance", "ticks": [0, 25, 50, 75, 100], "format": pct_formatter()},
        ax=ax,
    )
    for row_idx, model_group in enumerate(matrix.index):
        for col_idx, target in enumerate(matrix.columns):
            value = matrix.loc[model_group, target]
            if pd.isna(value):
                continue
            ax.text(
                col_idx + 0.5,
                row_idx + 0.42,
                f"{float(value) * 100:.0f}%",
                ha="center",
                va="center",
                fontsize=5.8,
                color=COLORS["ink"],
            )
            runs_value = run_matrix.loc[model_group, target]
            ax.text(
                col_idx + 0.5,
                row_idx + 0.66,
                f"n={int(runs_value):,}" if pd.notna(runs_value) else "",
                ha="center",
                va="center",
                fontsize=4.8,
                color=COLORS["muted"],
            )
    family_seen: list[str] = []
    for target in order:
        family_seen.append(target.rsplit(" ", 1)[0])
    has_missing = bool(matrix.isna().any().any())
    if has_missing:
        for row_idx, model_group in enumerate(matrix.index):
            for col_idx, target in enumerate(matrix.columns):
                if pd.isna(matrix.loc[model_group, target]):
                    ax.add_patch(
                        plt.Rectangle(
                            (col_idx, row_idx),
                            1,
                            1,
                            facecolor=COLORS["gray_light"],
                            edgecolor="white",
                            hatch="///",
                            linewidth=0.35,
                            zorder=3,
                        )
                    )
    for idx in range(1, len(family_seen)):
        if family_seen[idx] != family_seen[idx - 1]:
            ax.axvline(idx, color=COLORS["gray_mid"], linewidth=0.8)
    start = 0
    while start < len(family_seen):
        end = start + 1
        while end < len(family_seen) and family_seen[end] == family_seen[start]:
            end += 1
        ax.text(
            (start + end) / 2,
            -0.50,
            compact_family_label(family_seen[start]),
            ha="center",
            va="bottom",
            fontsize=7.2,
            fontweight="semibold",
            color=COLORS["ink"],
            clip_on=False,
        )
        start = end
    ax.set_xlabel("Benchmark instance")
    ax.set_ylabel("Model group")
    ax.set_xticks(
        ax.get_xticks(),
        [str(label).rsplit(" ", 1)[-1] for label in order],
        rotation=0,
        ha="center",
        fontsize=6.5,
    )
    ax.set_yticks(ax.get_yticks(), ax.get_yticklabels(), rotation=0, fontsize=7.2)
    if has_missing:
        na_patch = Patch(facecolor=COLORS["gray_light"], edgecolor=COLORS["gray_mid"], hatch="///", label="N/A")
        ax.legend(handles=[na_patch], frameon=False, loc="upper right", bbox_to_anchor=(1.0, 1.18), fontsize=7.0, handlelength=1.2)
    fig.subplots_adjust(left=0.14, right=0.94, top=0.78, bottom=0.23)
    save_figure(
        fig,
        "appendix_a1_model_group_instance_heatmap",
        "appendix",
        "Model-group by benchmark-instance heatmap of scenario-level conformance from latest manuscript-facing rollups.",
        "Appendix Figure A1: model-group result matrix without centering the main paper on a leaderboard.",
    )


def plot_appendix_a2_contract_feature_difficulty(report_models: pd.DataFrame, metrics: pd.DataFrame, scenarios: pd.DataFrame) -> None:
    df = paper_main_reported_rows(report_models).copy()
    inv = target_inventory(metrics, scenarios)
    feature_cols = [
        "upload_feature",
        "tables_feature",
        "derived_feature",
        "pages",
        "component_actions",
        "state_fields",
        "services",
        "max_steps",
        "scenario_count",
    ]
    joined = df.merge(inv[["suite", "tier", *feature_cols]], on=["suite", "tier"], how="left")
    joined = joined.dropna(subset=["formal_mean"]).copy()
    model_dummies = pd.get_dummies(joined["model_tier"], prefix="model", drop_first=True, dtype=float)
    X = joined[feature_cols].astype(float).replace([np.inf, -np.inf], np.nan).copy()
    for col in X.columns:
        fill = X[col].median()
        X[col] = X[col].fillna(0.0 if pd.isna(fill) else fill)
    X = pd.concat([X, model_dummies], axis=1)
    std = X.std(axis=0).replace(0, np.nan)
    X = X.loc[:, std.notna()]
    std = X.std(axis=0).replace(0, np.nan)
    X_std = ((X - X.mean()) / std).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    y = joined["formal_mean"].to_numpy(dtype=float)
    X_design = np.column_stack([np.ones(len(X_std)), X_std.to_numpy(dtype=float)])
    beta = np.linalg.pinv(X_design) @ y
    coef = beta[1:]
    residual = y - X_design @ beta
    dof = max(1, len(y) - X_design.shape[1])
    sigma2 = float((residual @ residual) / dof)
    cov = sigma2 * np.linalg.pinv(X_design.T @ X_design)
    se = np.sqrt(np.diag(cov))[1:]
    coef_df = pd.DataFrame({"feature": X_std.columns, "coef": coef, "se": se})
    labels = {
        "upload_feature": "Upload",
        "tables_feature": "Rendered table",
        "derived_feature": "Derived relations",
        "pages": "Pages",
        "component_actions": "Actions",
        "state_fields": "State fields",
        "services": "Services",
        "max_steps": "Max scenario steps",
        "scenario_count": "Scenario count",
        "model_M": "Small model",
        "model_T": "Mid-range model",
        "model_F": "Frontier model",
    }
    coef_df["label"] = coef_df["feature"].map(labels).fillna(coef_df["feature"])
    coef_df = coef_df.sort_values("coef")
    y_pos = np.arange(len(coef_df))
    fig, ax = plt.subplots(figsize=(5.7, max(3.2, 0.32 * len(coef_df))))
    ax.axvline(0, color=COLORS["ink"], linewidth=0.8, alpha=0.65)
    coef_colors = np.where(coef_df["coef"] >= 0, STEP_COLOR, COLORS["orange"])
    for yi, row, color in zip(y_pos, coef_df.itertuples(index=False), coef_colors, strict=False):
        ax.errorbar(
            row.coef,
            yi,
            xerr=1.96 * row.se,
            fmt="o",
            color=color,
            ecolor=COLORS["gray_mid"],
            elinewidth=0.9,
            capsize=2,
            markersize=4.6,
        )
    ax.set_yticks(y_pos, coef_df["label"])
    ax.set_xlabel("Standardized association with scenario-level conformance")
    ax.set_ylabel("")
    strip_background(ax)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=COLORS["line"], linewidth=0.45, alpha=0.45)
    fig.subplots_adjust(left=0.38, right=0.98, top=0.96, bottom=0.14)
    save_figure(
        fig,
        "appendix_a2_contract_feature_difficulty",
        "appendix",
        "Exploratory association, not a causal estimate: standardized linear coefficients relating target features and model group to scenario-level conformance.",
        "Appendix Figure A2: exploratory association analysis for behavioral-coupling features.",
    )


def plot_appendix_a3_generation_variance(runs: pd.DataFrame) -> None:
    df = view_filter(runs, "current_raw")
    df["model_group"] = df["model_tier"].map(MODEL_TIER_LABELS).fillna(df["model_tier"])
    df["formal_pct"] = df["formal_ratio"] * 100
    model_order = [MODEL_LABELS[m] for m in MODEL_ORDER if MODEL_LABELS[m] in set(df["model_label"])]
    model_groups = (
        df[["model_label", "model_tier"]]
        .drop_duplicates()
        .set_index("model_label")["model_tier"]
        .to_dict()
    )
    fig, ax = plt.subplots(figsize=(8.2, 3.9))
    sns.boxplot(
        data=df,
        x="model_label",
        y="formal_pct",
        order=model_order,
        color=COLORS["gray_light"],
        fliersize=0,
        linewidth=0.8,
        ax=ax,
    )
    group_palette = {MODEL_TIER_LABELS[k]: v for k, v in MODEL_TIER_COLORS.items()}
    sns.stripplot(
        data=df,
        x="model_label",
        y="formal_pct",
        order=model_order,
        hue="model_group",
        hue_order=[MODEL_TIER_LABELS[t] for t in MODEL_TIER_ORDER],
        palette=group_palette,
        alpha=0.34,
        size=2.0,
        jitter=0.25,
        ax=ax,
    )
    medians = df.groupby("model_label", observed=True)["formal_pct"].median().reindex(model_order)
    ax.scatter(np.arange(len(model_order)), medians, marker="D", s=18, color=COLORS["ink"], edgecolor="white", linewidth=0.45, zorder=4, label="Median")
    ordered_tiers = [model_groups.get(m, "") for m in model_order]
    for idx in range(1, len(ordered_tiers)):
        if ordered_tiers[idx] != ordered_tiers[idx - 1]:
            ax.axvline(idx - 0.5, color=COLORS["line"], linewidth=0.9)
    ax.yaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
    ax.yaxis.set_major_formatter(pct_formatter())
    ax.set_ylim(0, 102)
    ax.set_xlabel("")
    ax.set_ylabel("Scenario-level conformance")
    ax.set_xticks(ax.get_xticks(), ax.get_xticklabels(), rotation=35, ha="right", fontsize=7)
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()
    handles = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=MODEL_TIER_COLORS[t], markeredgecolor="none", alpha=0.50, markersize=4.5, label=MODEL_TIER_LABELS[t])
        for t in MODEL_TIER_ORDER
    ]
    handles.append(Line2D([0], [0], marker="D", linestyle="none", markerfacecolor=COLORS["ink"], markeredgecolor="white", markersize=5.0, label="Median"))
    ax.legend(handles=handles, frameon=False, ncols=4, loc="upper right", bbox_to_anchor=(1.0, 1.18), fontsize=7.2, columnspacing=1.0, handletextpad=0.35)
    strip_background(ax)
    add_y_grid(ax)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.82, bottom=0.34)
    save_figure(
        fig,
        "appendix_a3_generation_variance",
        "appendix",
        "Distribution of scenario-level conformance across repeated generations for each model.",
        "Appendix Figure A3: separates stable capability from generation luck.",
    )


def build_paper_figure_review_bundle() -> None:
    """Create a single contact sheet for rapid visual QA of manuscript figures."""
    figure2 = (FIG_DIR / "reviewer_proposal" / "figure2_conformance_gap_wide.png", "Figure 2: The Conformance Gap (wide, figure* preview)")
    items = [
        (FIG_DIR / "reviewer_proposal" / "reviewer_figure3_model_capability.png", "Figure 3: Capability vs. Completion"),
        (FIG_DIR / "reviewer_proposal" / "reviewer_figure4_complexity_ladder_heatmap.png", "Figure 4: Complexity Ladder"),
        (FIG_DIR / "reviewer_proposal" / "reviewer_figure5_first_failure_taxonomy.png", "Figure 5: First-failure Taxonomy"),
        (FIG_DIR / "reviewer_proposal" / "reviewer_figure6_long_horizon_survival.png", "Figure 6: Long-horizon Survival"),
        (FIG_DIR / "appendix" / "appendix_a1_model_group_instance_heatmap.png", "Appendix A1: Model-group Matrix"),
        (FIG_DIR / "appendix" / "appendix_a2_contract_feature_difficulty.png", "Appendix A2: Feature Associations"),
        (FIG_DIR / "appendix" / "appendix_a3_generation_variance.png", "Appendix A3: Generation Variance"),
    ]
    items = [(path, label) for path, label in items if path.exists()]
    if not figure2[0].exists() and not items:
        return
    out_dir = FIG_DIR / "review_bundle"
    pdf_path = out_dir / "paper_figure_review_sheet.pdf"
    png_path = out_dir / "paper_figure_review_sheet.png"
    if figure2[0].exists():
        made_pdf = make_wide_first_contact_sheet(figure2, items, pdf_path, columns=2, thumb_w=760, thumb_h=440, wide_h=620, label_h=48)
        made_png = make_wide_first_contact_sheet(figure2, items, png_path, columns=2, thumb_w=760, thumb_h=440, wide_h=620, label_h=48)
    else:
        made_pdf = make_contact_sheet(items, pdf_path, columns=2, thumb_w=760, thumb_h=440, label_h=48)
        made_png = make_contact_sheet(items, png_path, columns=2, thumb_w=760, thumb_h=440, label_h=48)
    if made_pdf:
        note = {
            "group": "review_bundle",
            "name": "paper_figure_review_sheet",
            "pdf": str(pdf_path.relative_to(OUT_ROOT)),
            "paper_use": "Review bundle: all main candidates and Appendix A figures in one page.",
            "note": "Contact sheet for rapid typography, color, and layout QA across the manuscript figure set.",
        }
        if made_png:
            note["png"] = str(png_path.relative_to(OUT_ROOT))
        FIGURE_NOTES.append(note)


def view_filter(df: pd.DataFrame, view: str) -> pd.DataFrame:
    if view == "all_available_raw":
        return df[df["view_all_available_raw"]].copy()
    if view == "current_raw":
        return df[df["view_current_raw"]].copy()
    if view == "paper_main_raw":
        return df[df["view_paper_main_raw"]].copy()
    raise ValueError(view)


def plot_raw_score_distributions(runs: pd.DataFrame, view: str) -> None:
    df = view_filter(runs, view)
    df["model_tier"] = ordered_categories(df["model_tier"], MODEL_TIER_ORDER)
    plot_df = df.melt(
        id_vars=["model_tier", "model_tier_label", "suite_label"],
        value_vars=["formal_ratio", "stepwise_ratio"],
        var_name="metric",
        value_name="score",
    )
    plot_df["metric"] = plot_df["metric"].map(
        {"formal_ratio": "Scenario-level conformance", "stepwise_ratio": "Step-level progress"}
    )
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    sns.violinplot(
        data=plot_df,
        x="model_tier",
        y="score",
        hue="metric",
        split=True,
        inner="quart",
        palette=[COLORS["teal"], COLORS["teal_light"]],
        cut=0,
        ax=ax,
    )
    ticks = ax.get_xticks()
    labels = [MODEL_TIER_LABELS.get(t.get_text(), t.get_text()) for t in ax.get_xticklabels()]
    ax.set_xticks(ticks, labels)
    ax.yaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Model group")
    ax.set_ylabel("Generated implementation score")
    ax.set_title("Distribution of behavioral conformance across implementations")
    ax.legend(frameon=False, loc="upper left")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_score_distributions_by_model_group",
        "diagnostics",
        f"Generated-implementation score distributions for {view}.",
        "Appendix: shows variance and near-miss mass beyond means.",
    )


def plot_raw_scatter_gap(runs: pd.DataFrame, view: str) -> None:
    df = view_filter(runs, view)
    fig, ax = plt.subplots(figsize=(4.4, 4.1))
    sns.scatterplot(
        data=df,
        x="formal_ratio",
        y="stepwise_ratio",
        hue="model_tier",
        hue_order=MODEL_TIER_ORDER,
        palette=[COLORS["rose"], COLORS["amber"], COLORS["teal"]],
        alpha=0.55,
        s=24,
        edgecolor="none",
        ax=ax,
    )
    ax.plot([0, 1], [0, 1], color=COLORS["line"], linestyle="--", linewidth=1)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.xaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax.yaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax.set_xlabel("Scenario-level conformance")
    ax.set_ylabel("Step-level progress")
    ax.set_title("Many implementations make progress before violating the contract")
    ax.legend(frameon=False, title="Model group")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_formal_vs_stepwise_scatter",
        "diagnostics",
        f"Scenario-level conformance vs step-level progress scatter for {view}.",
        "Appendix or Results: visualizes long-horizon near misses.",
    )


def plot_raw_ecdf(runs: pd.DataFrame, view: str) -> None:
    df = view_filter(runs, view)
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    for ax, metric, title in [
        (axes[0], "formal_ratio", "Scenario-level conformance"),
        (axes[1], "stepwise_ratio", "Step-level progress"),
    ]:
        sns.ecdfplot(
            data=df,
            x=metric,
            hue="model_tier",
            hue_order=MODEL_TIER_ORDER,
            palette=[COLORS["rose"], COLORS["amber"], COLORS["teal"]],
            ax=ax,
        )
        ax.xaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
        ax.set_xlim(0, 1)
        ax.set_xlabel("Generated implementation score")
        ax.set_ylabel("Cumulative share" if metric == "formal_ratio" else "")
        ax.set_title(title)
        style_existing_legend(ax, title="Model group")
        strip_background(ax)
    save_figure(
        fig,
        f"{view}_score_ecdf_by_model_group",
        "diagnostics",
        f"ECDF of generated-implementation scores for {view}.",
        "Appendix: makes distributional shifts visible.",
    )


def plot_raw_fullpass_counts(runs: pd.DataFrame, view: str) -> None:
    df = view_filter(runs, view)
    grouped = (
        df.groupby(["suite_label", "tier"], observed=True)
        .agg(runs=("run_id", "count"), full_pass=("passed", "sum"))
        .reset_index()
    )
    grouped["fail"] = grouped["runs"] - grouped["full_pass"]
    grouped["target"] = grouped["suite_label"] + " " + grouped["tier"]
    order = target_label_order(grouped.assign(suite_label=grouped["suite_label"], tier=grouped["tier"]))
    grouped = grouped.set_index("target").reindex(order).reset_index()
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    ax.bar(grouped["target"], grouped["fail"], color=COLORS["gray"], label="not fully conformant")
    ax.bar(grouped["target"], grouped["full_pass"], color=COLORS["teal"], label="full conformance")
    ax.set_ylabel("Generated implementations")
    ax.set_xlabel("")
    ax.set_title("Full-conformant implementations are rare")
    ax.tick_params(axis="x", rotation=40)
    for i, r in grouped.iterrows():
        ax.text(i, r["runs"] + 1, f"{int(r['full_pass'])}/{int(r['runs'])}", ha="center", fontsize=7)
    ax.legend(frameon=False, loc="upper right")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_fullpass_counts_by_target",
        "diagnostics",
        f"Full-conformance counts by benchmark instance for {view}.",
        "Appendix: absolute counts, useful beside percentages.",
    )


def plot_raw_family_tier_heatmap(runs: pd.DataFrame, view: str, metric: str) -> None:
    df = view_filter(runs, view)
    matrix = (
        df.groupby(["suite_label", "tier"], observed=True)[metric]
        .mean()
        .reset_index()
        .pivot(index="suite_label", columns="tier", values=metric)
    )
    row_order = suite_label_order(set(matrix.index))
    matrix = matrix.reindex(row_order).reindex(columns=TIER_ORDER)
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    sns.heatmap(
        matrix * 100,
        annot=True,
        fmt=".1f",
        cmap=HEAT_CMAP,
        linewidths=0.45,
        linecolor="#F4F1EB",
        cbar_kws={"label": "Mean score (%)"},
        ax=ax,
    )
    title = "Scenario-level conformance" if metric == "formal_ratio" else "Step-level progress"
    ax.set_title(f"{title} by product family and variant")
    ax.set_xlabel("Complexity variant")
    ax.set_ylabel("")
    save_figure(
        fig,
        f"{view}_{metric}_family_tier_heatmap",
        "diagnostics",
        f"{title} heatmap by product family and complexity variant for {view}.",
        "Appendix: benchmark-instance score matrix.",
    )


def plot_capability_heatmap(capabilities: pd.DataFrame, view: str) -> None:
    df = view_filter(capabilities, view)
    df = df[df["capability"].notna()].copy()
    grouped = (
        df.groupby(["capability", "model_tier"], observed=True)["scenario_ratio"]
        .mean()
        .reset_index()
    )
    order = [c for c in CAPABILITY_ORDER if c in set(grouped["capability"])]
    order += sorted(set(grouped["capability"]) - set(order))
    matrix = grouped.pivot(index="capability", columns="model_tier", values="scenario_ratio")
    matrix = matrix.reindex(order).reindex(columns=MODEL_TIER_ORDER)
    fig, ax = plt.subplots(figsize=(4.4, max(3.0, 0.32 * len(matrix))))
    sns.heatmap(
        matrix * 100,
        annot=True,
        fmt=".1f",
        cmap=COMPLEXITY_CMAP,
        linewidths=0.6,
        linecolor="#F4F1EB",
        cbar_kws={"label": "Scenario-level conformance (%)"},
        ax=ax,
    )
    ax.set_xlabel("Model group")
    ax.set_ylabel("Behavioral capability")
    ticks = ax.get_xticks()
    ax.set_xticks(ticks, [MODEL_TIER_LABELS.get(t.get_text(), t.get_text()) for t in ax.get_xticklabels()])
    ax.set_title("Conformance varies by behavioral capability")
    save_figure(
        fig,
        f"{view}_capability_score_heatmap",
        "appendix",
        f"Behavioral-capability conformance heatmap for {view}.",
        "Error Analysis or Appendix: connects failures to behavioral capability classes.",
    )


def plot_failure_breakdowns(scenarios: pd.DataFrame, view: str) -> None:
    df = view_filter(scenarios, view)
    df = df[(df["kind"] == "scoring") & (~df["scenario_passed"])].copy()
    if df.empty:
        return
    counts = df["first_failure_group"].value_counts().reset_index()
    counts.columns = ["failure_group", "count"]
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    sns.barplot(
        data=counts,
        y="failure_group",
        x="count",
        color=COLORS["teal"],
        ax=ax,
    )
    ax.set_xlabel("Failed interaction tests")
    ax.set_ylabel("")
    ax.set_title("First failures become auditable categories")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_first_failure_categories",
        "diagnostics",
        f"First failure category counts for failed interaction tests in {view}.",
        "Error Analysis: the core diagnostic bar chart.",
    )

    grouped = (
        df.groupby(["suite_label", "first_failure_group"], observed=True)
        .size()
        .reset_index(name="count")
    )
    matrix = grouped.pivot(index="first_failure_group", columns="suite_label", values="count").fillna(0)
    matrix = matrix.loc[matrix.sum(axis=1).sort_values(ascending=False).index]
    matrix = matrix.reindex(columns=suite_label_order(set(matrix.columns)))
    fig, ax = plt.subplots(figsize=(5.5, max(3.0, 0.35 * len(matrix))))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".0f",
        cmap=FAIL_CMAP,
        linewidths=0.45,
        linecolor="#F4F1EB",
        cbar_kws={"label": "Failed interaction tests"},
        ax=ax,
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("Failure modes differ by product family")
    save_figure(
        fig,
        f"{view}_failure_category_by_family",
        "appendix",
        f"Failure category heatmap by family for {view}.",
        "Error Analysis Appendix: demonstrates failure-mode diversity.",
    )


def plot_first_failure_progress(scenarios: pd.DataFrame, view: str) -> None:
    df = view_filter(scenarios, view)
    df = df[(df["kind"] == "scoring") & (~df["scenario_passed"])].copy()
    df = df[df["step_progress_until_failure"].notna()]
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    sns.histplot(
        data=df,
        x="step_progress_until_failure",
        hue="model_tier",
        hue_order=MODEL_TIER_ORDER,
        palette=[COLORS["rose"], COLORS["amber"], COLORS["teal"]],
        bins=np.linspace(0, 1, 11),
        multiple="stack",
        ax=ax,
    )
    ax.xaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax.set_xlabel("Fraction of interaction test completed before first failure")
    ax.set_ylabel("Failed interaction tests")
    ax.set_title("Many failures arrive late in the browser trace")
    style_existing_legend(ax, title="Model group")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_first_failure_progress_histogram",
        "diagnostics",
        f"Histogram of normalized first-failure position for {view}.",
        "Error Analysis: supports the long-horizon drift story.",
    )


def plot_scenario_length_vs_pass_rate(scenarios: pd.DataFrame, view: str) -> None:
    df = view_filter(scenarios, view)
    df = df[df["kind"] == "scoring"].copy()
    grouped = (
        df.groupby(["suite_label", "tier", "scenario_id", "scenario_tier"], observed=True)
        .agg(
            expected_step_count=("expected_step_count", "median"),
            pass_rate=("scenario_passed", "mean"),
            runs=("run_id", "count"),
        )
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    sns.scatterplot(
        data=grouped,
        x="expected_step_count",
        y="pass_rate",
        hue="scenario_tier",
        size="runs",
        sizes=(20, 110),
        alpha=0.72,
        edgecolor="white",
        linewidth=0.4,
        ax=ax,
    )
    ax.yaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax.set_xlabel("Interaction-test length (expected browser steps)")
    ax.set_ylabel("Pass rate")
    ax.set_title("Longer browser traces expose compositional failures")
    ax.legend(frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_scenario_length_vs_pass_rate",
        "appendix",
        f"Interaction-test length vs pass rate for {view}.",
        "Appendix: explains why long trajectories matter.",
    )


def plot_visibility_pass_rate(scenarios: pd.DataFrame, view: str) -> None:
    df = view_filter(scenarios, view)
    df = df[df["kind"] == "scoring"].copy()
    grouped = (
        df.groupby(["visibility", "model_tier"], observed=True)["scenario_passed"]
        .mean()
        .reset_index()
    )
    grouped["model_tier"] = ordered_categories(grouped["model_tier"], MODEL_TIER_ORDER)
    fig, ax = plt.subplots(figsize=(4.7, 3.0))
    sns.barplot(
        data=grouped,
        x="visibility",
        y="scenario_passed",
        hue="model_tier",
        hue_order=MODEL_TIER_ORDER,
        palette=[COLORS["rose"], COLORS["amber"], COLORS["teal"]],
        ax=ax,
    )
    ax.yaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax.set_xlabel("Interaction-test disclosure")
    ax.set_ylabel("Pass rate")
    ax.set_title("Held-out compositions remain harder than public examples")
    ax.legend(frameon=False, title="Model group")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_public_private_pass_rate",
        "appendix",
        f"Public vs held-out interaction-test pass rate for {view}.",
        "Appendix: documents held-out test behavior.",
    )


def plot_model_leaderboard(runs: pd.DataFrame, view: str) -> None:
    df = view_filter(runs, view)
    grouped = (
        df.groupby(["model", "model_label", "model_tier"], observed=True)
        .agg(
            runs=("run_id", "count"),
            formal_mean=("formal_ratio", "mean"),
            stepwise_mean=("stepwise_ratio", "mean"),
            full_pass_rate=("passed", "mean"),
        )
        .reset_index()
    )
    grouped["model"] = pd.Categorical(
        grouped["model"],
        categories=[m for m in MODEL_ORDER if m in set(grouped["model"])],
        ordered=True,
    )
    grouped = grouped.sort_values(["model_tier", "model"])
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    y = np.arange(len(grouped))
    ax.hlines(y, grouped["formal_mean"], grouped["stepwise_mean"], color=COLORS["line"], linewidth=2)
    ax.scatter(grouped["formal_mean"], y, color=COLORS["teal"], label="Scenario-level conformance", zorder=3)
    ax.scatter(grouped["stepwise_mean"], y, color=COLORS["teal_light"], label="Step-level progress", zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(grouped["model_label"])
    ax.xaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Mean generated-implementation score")
    ax.set_title("Per-model means show the progress/conformance gap")
    ax.legend(frameon=False, loc="lower right")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_model_score_lollipop",
        "appendix",
        f"Per-model scenario-level conformance and step-level progress chart for {view}.",
        "Appendix: model detail without overemphasizing leaderboard ranking.",
    )


def plot_action_failure_counts(scenarios: pd.DataFrame, view: str) -> None:
    df = view_filter(scenarios, view)
    df = df[(df["kind"] == "scoring") & (~df["scenario_passed"])].copy()
    counts = df["first_failed_action"].fillna("unknown").value_counts().head(14).reset_index()
    counts.columns = ["action", "count"]
    fig, ax = plt.subplots(figsize=(5.7, 3.0))
    sns.barplot(data=counts, y="action", x="count", color=COLORS["plum"], ax=ax)
    ax.set_xlabel("Failed interaction tests")
    ax.set_ylabel("First failed action")
    ax.set_title("Failures concentrate at concrete browser operations")
    strip_background(ax)
    save_figure(
        fig,
        f"{view}_first_failed_action_counts",
        "appendix",
        f"First failed action counts for {view}.",
        "Error Analysis Appendix: ties semantic failures to browser actions.",
    )


def plot_selected_scenario_heatmap(scenarios: pd.DataFrame, view: str) -> None:
    df = view_filter(scenarios, view)
    target = df[(df["suite"] == "freshcart_market") & (df["tier"] == "C") & (df["kind"] == "scoring")].copy()
    if target.empty:
        target = df[df["kind"] == "scoring"].copy()
    grouped = (
        target.groupby(["scenario_id", "model_tier"], observed=True)["scenario_passed"]
        .mean()
        .reset_index()
    )
    order_df = (
        target.groupby("scenario_id", observed=True)
        .agg(expected_step_count=("expected_step_count", "median"), pass_rate=("scenario_passed", "mean"))
        .reset_index()
        .sort_values(["expected_step_count", "pass_rate", "scenario_id"], ascending=[True, False, True])
    )
    scenario_order = list(order_df["scenario_id"])[:45]
    matrix = grouped.pivot(index="scenario_id", columns="model_tier", values="scenario_passed")
    matrix = matrix.reindex(scenario_order).reindex(columns=MODEL_TIER_ORDER)
    fig, ax = plt.subplots(figsize=(4.8, max(5.5, 0.18 * len(matrix))))
    sns.heatmap(
        matrix * 100,
        annot=False,
        cmap=HEAT_CMAP,
        linewidths=0.3,
        linecolor="#F4F1EB",
        cbar_kws={"label": "Pass rate (%)"},
        ax=ax,
    )
    ax.set_xlabel("Model group")
    ax.set_ylabel("Scenario")
    ax.set_title("FreshCart C scenario pass-rate profile")
    ticks = ax.get_xticks()
    ax.set_xticks(ticks, [MODEL_TIER_LABELS.get(t.get_text(), t.get_text()) for t in ax.get_xticklabels()])
    save_figure(
        fig,
        f"{view}_freshcart_c_scenario_heatmap",
        "appendix",
        f"Scenario-by-model group heatmap for FreshCart C in {view}.",
        "Appendix: pairs well with the Figure 1 FreshCart example.",
    )


def make_contact_sheet(
    image_items: list[tuple[Path, str]],
    out_path: Path,
    columns: int = 4,
    thumb_w: int = 360,
    thumb_h: int = 230,
    label_h: int = 46,
) -> bool:
    if not image_items:
        return False
    rows = math.ceil(len(image_items) / columns)
    canvas = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for idx, (path, label) in enumerate(image_items):
        col = idx % columns
        row = idx // columns
        x = col * thumb_w
        y = row * (thumb_h + label_h)
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            continue
        img.thumbnail((thumb_w - 12, thumb_h - 12))
        img_x = x + (thumb_w - img.width) // 2
        img_y = y + 6
        canvas.paste(img, (img_x, img_y))
        wrapped = textwrap.wrap(label, width=max(24, thumb_w // 18))[:2]
        draw.text((x + 12, y + thumb_h + 6), "\n".join(wrapped), fill=(32, 33, 36), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() == ".pdf":
        canvas.save(out_path, "PDF", resolution=300.0)
    else:
        canvas.save(out_path)
    return True


def make_wide_first_contact_sheet(
    wide_item: tuple[Path, str],
    image_items: list[tuple[Path, str]],
    out_path: Path,
    *,
    columns: int = 2,
    thumb_w: int = 760,
    thumb_h: int = 440,
    wide_h: int = 620,
    label_h: int = 48,
) -> bool:
    all_items = [wide_item, *image_items]
    if not all_items:
        return False
    rows = math.ceil(len(image_items) / columns)
    canvas_w = columns * thumb_w
    canvas_h = wide_h + label_h + rows * (thumb_h + label_h)
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    def paste_fit(path: Path, x: int, y: int, w: int, h: int) -> None:
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            return
        img.thumbnail((w - 12, h - 12))
        canvas.paste(img, (x + (w - img.width) // 2, y + 6))

    wide_path, wide_label = wide_item
    paste_fit(wide_path, 0, 0, canvas_w, wide_h)
    draw.text((12, wide_h + 6), wide_label, fill=(32, 33, 36), font=font)

    y0 = wide_h + label_h
    for idx, (path, label) in enumerate(image_items):
        col = idx % columns
        row = idx // columns
        x = col * thumb_w
        y = y0 + row * (thumb_h + label_h)
        paste_fit(path, x, y, thumb_w, thumb_h)
        wrapped = textwrap.wrap(label, width=max(24, thumb_w // 18))[:2]
        draw.text((x + 12, y + thumb_h + 6), "\n".join(wrapped), fill=(32, 33, 36), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() == ".pdf":
        canvas.save(out_path, "PDF", resolution=300.0)
    else:
        canvas.save(out_path)
    return True


def clean_generated_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def slugify(value: Any, max_len: int = 90) -> str:
    s = str(value).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return (s or "item")[:max_len].strip("_")


def image_to_rgb(path: Path) -> Image.Image:
    img = Image.open(path)
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.getchannel("A"))
        return bg
    return img.convert("RGB")


def save_image_as_pdf(image_path: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = image_to_rgb(image_path)
    img.save(out_path, "PDF", resolution=300.0)


def paper_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    *,
    max_width: int,
    fill: str,
    line_gap: int = 6,
) -> int:
    x, y = xy
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y = bbox[3] + line_gap
    return y


def paste_fit(canvas: Image.Image, image_path: Path, box: tuple[int, int, int, int]) -> None:
    img = image_to_rgb(image_path)
    x0, y0, x1, y1 = box
    img.thumbnail((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    x = x0 + ((x1 - x0) - img.width) // 2
    y = y0 + ((y1 - y0) - img.height) // 2
    canvas.paste(img, (x, y))


def failure_reason(row: pd.Series) -> str:
    group = str(row.get("first_failure_group") or "contract violation")
    action = str(row.get("first_failed_action") or "browser action").replace("_", " ")
    if group == "rendered-projection mismatch":
        detail = "the rendered interface no longer agrees with the contract-visible state"
    elif group == "route / persistence drift":
        detail = "the browser reaches a navigation or reload boundary where required state is lost"
    elif group == "wrong state transition":
        detail = "the action is executable, but the resulting public state violates an expected relation"
    elif group == "missing interaction surface":
        detail = "the next required control is absent or cannot be selected"
    elif group == "unavailable control":
        detail = "the next required control exists but is not actionable at the failure point"
    else:
        detail = f"the first failed check is categorized as {group}"
    return (
        f"Why this pair matters: after the evaluator performs `{action}`, {detail}. "
        "The before panel anchors the last observable state; the after panel is the first state used for the failed contract check."
    )


def save_before_after_pdf(before: Path, after: Path, out_path: Path, row: pd.Series, reason: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1800, 1120
    margin = 70
    header_h = 126
    panel_w = 780
    panel_h = 560
    panel_y = header_h + 54
    left_x = margin
    right_x = width - margin - panel_w
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = paper_font(44, bold=True)
    subtitle_font = paper_font(25)
    label_font = paper_font(28, bold=True)
    body_font = paper_font(25)
    small_font = paper_font(21)

    target = f"{row.get('suite_label')} {row.get('tier')}"
    title = f"{target}: first failing browser observation"
    subtitle = (
        f"{row.get('scenario_id')} | {row.get('first_failure_group')} | "
        f"{row.get('model_tier_label')} model group"
    )
    draw.text((margin, 42), title, font=title_font, fill=COLORS["ink"])
    draw.text((margin, 92), subtitle, font=subtitle_font, fill=COLORS["muted"])

    for x, label, path in [(left_x, "Before", before), (right_x, "After", after)]:
        draw.rounded_rectangle(
            (x - 16, panel_y - 52, x + panel_w + 16, panel_y + panel_h + 16),
            radius=18,
            fill="#FBFAF7",
            outline="#D8DDD9",
            width=3,
        )
        draw.text((x, panel_y - 42), label, font=label_font, fill=COLORS["teal"] if label == "Before" else COLORS["rose"])
        paste_fit(canvas, path, (x, panel_y, x + panel_w, panel_y + panel_h))

    arrow_y = panel_y + panel_h // 2
    arrow_x0 = left_x + panel_w + 35
    arrow_x1 = right_x - 35
    draw.line((arrow_x0, arrow_y, arrow_x1, arrow_y), fill=COLORS["ink"], width=5)
    draw.polygon(
        [(arrow_x1, arrow_y), (arrow_x1 - 24, arrow_y - 14), (arrow_x1 - 24, arrow_y + 14)],
        fill=COLORS["ink"],
    )

    reason_y = panel_y + panel_h + 60
    draw.rounded_rectangle(
        (margin, reason_y, width - margin, height - 64),
        radius=20,
        fill="#FBF6EF",
        outline="#E4C8BF",
        width=3,
    )
    draw_wrapped_text(
        draw,
        (margin + 30, reason_y + 28),
        reason,
        body_font,
        max_width=width - 2 * margin - 60,
        fill=COLORS["ink"],
        line_gap=8,
    )
    meta = (
        f"Failure step: {row.get('first_failed_step')} / {row.get('expected_step_count')}    "
        f"Actor: {row.get('first_failed_actor') or 'n/a'}    "
        f"Component: {row.get('first_failed_component') or 'n/a'}"
    )
    draw.text((margin + 30, height - 106), meta, font=small_font, fill=COLORS["muted"])
    canvas.save(out_path, "PDF", resolution=300.0)


def reference_screenshot_for_target(suite: str, tier: str) -> Path | None:
    directory = TARGET_ROOT / suite / f"tier_{tier.lower()}" / "screenshots"
    candidates = sorted(directory.glob("*.png"))
    if not candidates:
        return None

    def score(path: Path) -> tuple[int, int, int, str]:
        stem = path.stem.lower()
        first = 0 if stem.startswith("01") or stem.startswith("1_") else 1
        desktop = 0 if "desktop" in stem else 1
        return first, desktop, len(path.name), path.name

    return sorted(candidates, key=score)[0]


def raw_screenshot_for_target(scenarios: pd.DataFrame, suite: str, tier: str) -> Path | None:
    df = view_filter(scenarios, "current_raw")
    df = df[(df["suite"] == suite) & (df["tier"] == tier)].copy()
    for col in ["first_failure_before_screenshot", "first_failure_after_screenshot"]:
        for value in df[col].dropna().astype(str):
            if not value:
                continue
            path = Path(value)
            if path.exists():
                return path
    return None


def build_representative_screenshot_exports(metrics: pd.DataFrame, scenarios: pd.DataFrame) -> None:
    out_dir = EVIDENCE_DIR / "representative_screenshots"
    clean_generated_dir(out_dir)
    metric_targets = metrics[["suite", "suite_label", "tier"]].drop_duplicates()
    raw_targets = view_filter(scenarios, "current_raw")[["suite", "suite_label", "tier"]].drop_duplicates()
    targets = pd.concat([metric_targets, raw_targets], ignore_index=True).drop_duplicates()
    targets["suite_rank"] = targets["suite"].map({s: i for i, s in enumerate(discovered_suite_order())}).fillna(999)
    targets["tier_rank"] = targets["tier"].map({t: i for i, t in enumerate(TIER_ORDER)}).fillna(999)
    targets = targets.sort_values(["suite_rank", "suite_label", "tier_rank", "tier"])

    rows: list[dict[str, Any]] = []
    for _, row in targets.iterrows():
        suite = str(row["suite"])
        tier = str(row["tier"])
        target = f"{row['suite_label']} {tier}"
        source = reference_screenshot_for_target(suite, tier)
        source_kind = "target reference screenshot"
        reason = "selected from the target's curated reference screenshots"
        if source is None:
            source = raw_screenshot_for_target(scenarios, suite, tier)
            source_kind = "current raw browser screenshot"
            reason = "no curated reference screenshot was found, so the first available current-run browser screenshot was used"
        slug = slugify(f"{row['suite_label']}_{tier}_representative")
        output = out_dir / f"{slug}.pdf"
        status = "missing"
        if source and source.exists():
            save_image_as_pdf(source, output)
            status = "written"
        rows.append(
            {
                "target_label": target,
                "suite": suite,
                "suite_label": row["suite_label"],
                "tier": tier,
                "status": status,
                "source_kind": source_kind if source else "missing",
                "selection_reason": reason if source else "no reference or raw browser screenshot was found",
                "source_path": str(source) if source else "",
                "output_pdf": str(output.relative_to(OUT_ROOT)) if status == "written" else "",
            }
        )
    metadata = out_dir / "representative_screenshots_metadata.csv"
    pd.DataFrame(rows).to_csv(metadata, index=False)
    EVIDENCE_NOTES.append(
        {
            "name": "representative_screenshots",
            "path": str(out_dir.relative_to(OUT_ROOT)),
            "metadata": str(metadata.relative_to(OUT_ROOT)),
            "note": f"{sum(r['status'] == 'written' for r in rows)} target-level representative screenshots, one PDF per target.",
        }
    )


def existing_path_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).map(lambda value: bool(value) and Path(value).exists())


def build_failure_pair_exports(scenarios: pd.DataFrame, view: str = "current_raw") -> None:
    out_dir = EVIDENCE_DIR / "failure_pairs" / view
    clean_generated_dir(out_dir)
    df = view_filter(scenarios, view)
    df = df[(df["kind"] == "scoring") & (~df["scenario_passed"])].copy()
    df = df[existing_path_series(df["first_failure_before_screenshot"])]
    df = df[existing_path_series(df["first_failure_after_screenshot"])]
    if df.empty:
        return
    df["target_label"] = df["suite_label"].astype(str) + " " + df["tier"].astype(str)
    df["model_rank"] = df["model_tier"].map({"F": 0, "T": 1, "M": 2}).fillna(9)
    df["progress_rank"] = df["step_progress_until_failure"].fillna(-1)
    df["length_rank"] = df["expected_step_count"].fillna(-1)
    candidate_cols = [
        "suite",
        "suite_label",
        "tier",
        "target_label",
        "model_tier",
        "model_tier_label",
        "model",
        "model_label",
        "batch",
        "run_id",
        "scenario_id",
        "visibility",
        "difficulty",
        "expected_step_count",
        "passed_until_step",
        "first_failed_step",
        "step_progress_until_failure",
        "first_failed_action",
        "first_failed_component",
        "first_failed_actor",
        "first_failure_group",
        "first_failure_raw",
        "first_failure_before_screenshot",
        "first_failure_after_screenshot",
    ]
    candidates_path = out_dir / f"{view}_failure_evidence_candidates.csv"
    df[candidate_cols].sort_values(["suite_label", "tier", "first_failure_group", "scenario_id"]).to_csv(
        candidates_path,
        index=False,
    )

    selected = (
        df.sort_values(
            [
                "suite_label",
                "tier",
                "first_failure_group",
                "model_rank",
                "progress_rank",
                "length_rank",
                "scenario_id",
            ],
            ascending=[True, True, True, True, False, False, True],
        )
        .groupby(["suite_label", "tier", "first_failure_group"], as_index=False, sort=False)
        .head(1)
        .copy()
    )

    rows: list[dict[str, Any]] = []
    used: Counter[str] = Counter()
    for _, row in selected.iterrows():
        base = slugify(f"{row['suite_label']}_{row['tier']}_{row['first_failure_group']}")
        used[base] += 1
        evidence_id = base if used[base] == 1 else f"{base}_{used[base]:02d}"
        before = Path(str(row["first_failure_before_screenshot"]))
        after = Path(str(row["first_failure_after_screenshot"]))
        before_pdf = out_dir / f"{evidence_id}_before.pdf"
        after_pdf = out_dir / f"{evidence_id}_after.pdf"
        paired_pdf = out_dir / f"{evidence_id}_before_after.pdf"
        reason = failure_reason(row)
        save_image_as_pdf(before, before_pdf)
        save_image_as_pdf(after, after_pdf)
        save_before_after_pdf(before, after, paired_pdf, row, reason)
        rows.append(
            {
                **{col: row.get(col) for col in candidate_cols},
                "evidence_id": evidence_id,
                "selection_reason": (
                    "Selected as the highest-progress current-run failure for this target and failure category, "
                    "preferring stronger model groups when available."
                ),
                "combined_figure_reason_text": reason,
                "before_pdf": str(before_pdf.relative_to(OUT_ROOT)),
                "after_pdf": str(after_pdf.relative_to(OUT_ROOT)),
                "before_after_pdf": str(paired_pdf.relative_to(OUT_ROOT)),
            }
        )
    selected_path = out_dir / f"{view}_failure_evidence_selected.csv"
    pd.DataFrame(rows).to_csv(selected_path, index=False)
    EVIDENCE_NOTES.append(
        {
            "name": f"{view}_failure_pairs",
            "path": str(out_dir.relative_to(OUT_ROOT)),
            "metadata": str(selected_path.relative_to(OUT_ROOT)),
            "note": (
                f"{len(rows)} selected before/after failure pairs as separate PDFs plus paired before-after PDFs; "
                f"{len(df):,} valid candidates are listed in {candidates_path.name}."
            ),
        }
    )


def build_reference_screenshot_atlas() -> None:
    items: list[tuple[Path, str]] = []
    for p in sorted(TARGET_ROOT.glob("*/tier_*/screenshots/*.png")):
        suite = p.parts[-4]
        tier = tier_from_dir(p.parts[-3])
        label = f"{suite_label(suite)} {tier}: {p.stem}"
        items.append((p, label))
    out = FIG_DIR / "atlases" / "reference_screenshot_atlas.pdf"
    if make_contact_sheet(items, out, columns=4):
        FIGURE_NOTES.append(
            {
                "group": "atlases",
                "name": "reference_screenshot_atlas",
                "pdf": str(out.relative_to(OUT_ROOT)),
                "paper_use": "Appendix screenshot atlas.",
                "note": "Contact sheet of curated reference screenshots committed with target specs.",
            }
        )


def build_failure_evidence_atlas(scenarios: pd.DataFrame, view: str) -> None:
    df = view_filter(scenarios, view)
    df = df[(df["kind"] == "scoring") & (~df["scenario_passed"])].copy()
    df = df[df["first_failure_after_screenshot"].notna()]
    df = df[df["first_failure_after_screenshot"].astype(str).str.len() > 0]
    if df.empty:
        return
    selected: list[tuple[Path, str]] = []
    seen: set[tuple[str, str]] = set()
    for _, row in df.sort_values(["first_failure_group", "suite_label", "tier"]).iterrows():
        key = (row["first_failure_group"], row["suite_label"])
        if key in seen:
            continue
        seen.add(key)
        before_raw = row.get("first_failure_before_screenshot")
        after_raw = row.get("first_failure_after_screenshot")
        before = Path(str(before_raw)) if pd.notna(before_raw) and str(before_raw) else None
        after = Path(str(after_raw)) if pd.notna(after_raw) and str(after_raw) else None
        if before and before.exists():
            selected.append((before, f"{row['suite_label']} {row['tier']} before | {row['first_failure_group']}"))
        if after and after.exists():
            selected.append((after, f"{row['suite_label']} {row['tier']} after | {row['scenario_id']}"))
        if len(selected) >= 32:
            break
    out = FIG_DIR / "atlases" / f"{view}_failure_evidence_atlas.pdf"
    if make_contact_sheet(selected, out, columns=4):
        FIGURE_NOTES.append(
            {
                "group": "atlases",
                "name": f"{view}_failure_evidence_atlas",
                "pdf": str(out.relative_to(OUT_ROOT)),
                "paper_use": "Appendix error analysis screenshot atlas.",
                "note": f"Selected before/after screenshots for first failures in {view}.",
            }
        )


def write_index(
    runs: pd.DataFrame,
    scenarios: pd.DataFrame,
    capabilities: pd.DataFrame,
    steps: pd.DataFrame,
    metrics: pd.DataFrame,
    report_tiers: pd.DataFrame,
    report_models: pd.DataFrame,
    report_per_models: pd.DataFrame,
) -> None:
    lines = [
        "# ConformWeb Paper Visualizations",
        "",
        "Generated by `tools/build_paper_visualizations.py`.",
        "",
        "## Data Views",
        "",
        "- `reported_current`: manuscript-facing rollups from each product family's `evaluation_report.md`, with missing maintained suite/tier cells filled from validated current raw cohorts when available.",
        "- `paper_main_raw`: current local artifact cohorts for every discovered product family, including newly added targets not yet listed in the official-batch map.",
        "- `current_raw`: latest/official local artifact cohorts; for newly discovered families without an official-batch map, all found cohorts are included.",
        "- `all_available_raw`: every generated implementation found under the cohort layout, including historical and recalibration cohorts.",
        "",
        "## Parsed Data",
        "",
        f"- `data/raw_runs.csv`: {len(runs):,} generated implementations.",
        f"- `data/raw_scenarios.csv`: {len(scenarios):,} interaction-test records.",
        f"- `data/raw_capability_scores.csv`: {len(capabilities):,} run-capability records.",
        f"- `data/raw_steps.csv`: {len(steps):,} browser-step records.",
        f"- `data/suite_metrics.csv`: {len(metrics):,} benchmark-instance metric rows.",
        f"- `data/report_tier_rollups.csv`: {len(report_tiers):,} report rollups by complexity variant.",
        f"- `data/report_model_tier_rollups.csv`: {len(report_models):,} report rollups by model group.",
        f"- `data/report_per_model_rollups.csv`: {len(report_per_models):,} report/raw rollups by model.",
        "",
        "## Figure Inventory",
        "",
        "| Group | Figure | Assets | Use | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in FIGURE_NOTES:
        link = item["pdf"]
        assets = f"[PDF]({item['pdf']})"
        if "svg" in item:
            assets += f" / [SVG]({item['svg']})"
        if "png" in item:
            assets += f" / [PNG]({item['png']})"
        lines.append(
            f"| {item['group']} | [{item['name']}]({link}) | {assets} | {item['paper_use']} | {item['note']} |"
        )
    if EVIDENCE_NOTES:
        lines.extend(
            [
                "",
                "## Evidence Exports",
                "",
                "| Export | Directory | Metadata | Note |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in EVIDENCE_NOTES:
            lines.append(
                f"| {item['name']} | [{item['path']}]({item['path']}) | "
                f"[metadata]({item['metadata']}) | {item['note']} |"
            )
    lines.extend(
        [
            "",
            "## Suggested Main-Paper Picks",
            "",
            "1. `figure2_conformance_gap_wide`: the primary full-width Conformance Gap figure for a LaTeX `figure*`; combines the Overall row, family-level rows, and scenario-vs-step paired scores.",
            "2. `reviewer_figure6_long_horizon_survival`: the long-horizon trace figure; shows when generated runs drift during multi-step browser workflows.",
            "3. `reviewer_figure5_first_failure_taxonomy`: the error-analysis figure; explains what fails and where failures first appear.",
            "4. `reviewer_figure3_model_capability`: optional main or appendix figure; shows that stronger models improve progress more than full completion.",
            "5. `reviewer_figure4_complexity_ladder_heatmap`: optional main or appendix figure; summarizes conformance across product families and complexity variants.",
            "",
            "## Notes",
            "",
            "- Use reported figures for main-paper aggregate claims because they include report-only rows whose raw artifacts may not be present locally.",
            "- Use artifact-derived figures for appendix diagnostics, failure categories, distributional analysis, interaction-test behavior, and screenshot atlases.",
            "- Figure labels use paper-facing terms: product family, complexity variant, interaction test, browser step, scenario-level conformance, step-level progress, and full conformance.",
        ]
    )
    (OUT_ROOT / "README.md").write_text("\n".join(lines) + "\n")


def remove_generated_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def clean_figure_outputs(curated_only: bool = False) -> None:
    ds_store = FIG_DIR / ".DS_Store"
    if ds_store.exists():
        ds_store.unlink()
    for group in ["main", "reviewer_proposal", "review_bundle", "appendix", "diagnostics", "atlases"]:
        path = FIG_DIR / group
        if curated_only:
            remove_generated_dir(path)
        else:
            clean_generated_dir(path)


def build_all_figures(
    runs: pd.DataFrame,
    scenarios: pd.DataFrame,
    capabilities: pd.DataFrame,
    steps: pd.DataFrame,
    metrics: pd.DataFrame,
    report_tiers: pd.DataFrame,
    report_models: pd.DataFrame,
    report_per_models: pd.DataFrame,
    curated_only: bool = False,
) -> None:
    set_theme()
    clean_figure_outputs(curated_only=curated_only)

    if not curated_only:
        plot_figure2_conformance_gap(report_tiers)
        plot_figure3_error_dynamics(scenarios)

    plot_figure2_conformance_gap_wide(report_tiers)
    plot_reviewer_figure3_model_capability(report_models)
    plot_reviewer_figure4_complexity_ladder(report_tiers)
    plot_reviewer_figure5_first_failure_taxonomy(scenarios)
    plot_reviewer_figure6_long_horizon_survival(scenarios)
    plot_appendix_a1_per_model_heatmap(runs, report_tiers, report_models)
    plot_appendix_a2_contract_feature_difficulty(report_models, metrics, scenarios)
    plot_appendix_a3_generation_variance(runs)
    build_paper_figure_review_bundle()

    if curated_only:
        build_representative_screenshot_exports(metrics, scenarios)
        build_failure_pair_exports(scenarios, "current_raw")
        return

    plot_reported_main_overview(report_tiers)
    plot_reported_tier_ladder(report_tiers)
    plot_reported_full_pass_heatmap(report_tiers)
    plot_reported_model_tier_matrix(report_models)
    plot_suite_complexity(metrics)

    for view in ["paper_main_raw", "current_raw", "all_available_raw"]:
        if view_filter(runs, view).empty:
            continue
        plot_raw_score_distributions(runs, view)
        plot_raw_scatter_gap(runs, view)
        plot_raw_ecdf(runs, view)
        plot_raw_fullpass_counts(runs, view)
        plot_raw_family_tier_heatmap(runs, view, "formal_ratio")
        plot_raw_family_tier_heatmap(runs, view, "stepwise_ratio")
        plot_capability_heatmap(capabilities, view)
        plot_failure_breakdowns(scenarios, view)
        plot_first_failure_progress(scenarios, view)
        plot_scenario_length_vs_pass_rate(scenarios, view)
        plot_visibility_pass_rate(scenarios, view)
        plot_model_leaderboard(runs, view)
        plot_action_failure_counts(scenarios, view)
        plot_selected_scenario_heatmap(scenarios, view)

    build_reference_screenshot_atlas()
    build_failure_evidence_atlas(scenarios, "current_raw")
    build_representative_screenshot_exports(metrics, scenarios)
    build_failure_pair_exports(scenarios, "current_raw")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-cache", action="store_true", help="Use CSVs in reports/conformweb_visualizations/data if present.")
    parser.add_argument("--no-figures", action="store_true", help="Only parse data and write CSVs.")
    parser.add_argument(
        "--curated-only",
        action="store_true",
        help="Generate only the polished paper figures, review bundle, and evidence exports.",
    )
    args = parser.parse_args()

    ensure_dirs()
    cache_files = [
        DATA_DIR / "raw_runs.csv",
        DATA_DIR / "raw_scenarios.csv",
        DATA_DIR / "raw_capability_scores.csv",
        DATA_DIR / "raw_steps.csv",
        DATA_DIR / "suite_metrics.csv",
        DATA_DIR / "report_tier_rollups.csv",
        DATA_DIR / "report_model_tier_rollups.csv",
        DATA_DIR / "report_per_model_rollups.csv",
    ]

    if args.reuse_cache and all(p.exists() for p in cache_files):
        print("loading cached CSVs")
        runs = pd.read_csv(DATA_DIR / "raw_runs.csv")
        scenarios = pd.read_csv(DATA_DIR / "raw_scenarios.csv")
        capabilities = pd.read_csv(DATA_DIR / "raw_capability_scores.csv")
        steps = pd.read_csv(DATA_DIR / "raw_steps.csv")
        metrics = pd.read_csv(DATA_DIR / "suite_metrics.csv")
        report_tiers = pd.read_csv(DATA_DIR / "report_tier_rollups.csv")
        report_models = pd.read_csv(DATA_DIR / "report_model_tier_rollups.csv")
        report_per_models = pd.read_csv(DATA_DIR / "report_per_model_rollups.csv")
        report_tiers, report_models = augment_report_rollups_from_raw(runs, report_tiers, report_models)
    else:
        print("parsing raw summaries")
        runs, scenarios, capabilities, steps = parse_raw_summaries()
        print("parsing target metrics")
        metrics = parse_suite_metrics()
        print("parsing evaluation reports")
        report_tiers, report_models = parse_report_rollups()
        report_per_models = parse_report_per_model_details()
        report_tiers, report_models = augment_report_rollups_from_raw(runs, report_tiers, report_models)
        save_table(runs, "raw_runs.csv")
        save_table(scenarios, "raw_scenarios.csv")
        save_table(capabilities, "raw_capability_scores.csv")
        save_table(steps, "raw_steps.csv")
        save_table(metrics, "suite_metrics.csv")
        save_table(report_tiers, "report_tier_rollups.csv")
        save_table(report_models, "report_model_tier_rollups.csv")
        save_table(report_per_models, "report_per_model_rollups.csv")
        save_table(pd.DataFrame(PARSE_ERRORS), "parse_errors.csv")

    if not args.no_figures:
        print("building figures")
        build_all_figures(
            runs,
            scenarios,
            capabilities,
            steps,
            metrics,
            report_tiers,
            report_models,
            report_per_models,
            curated_only=args.curated_only,
        )

    write_index(runs, scenarios, capabilities, steps, metrics, report_tiers, report_models, report_per_models)
    print(f"wrote {OUT_ROOT}")


if __name__ == "__main__":
    main()
