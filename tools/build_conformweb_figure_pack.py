#!/usr/bin/env python3
"""Build the ConformWeb paper figure pack.

This script intentionally reads the latest report rollups for all aggregate
paper figures. Trace-level figures use the raw trace artifacts that are present
locally; the validation report states that scope explicitly.
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_paper_visualizations as base  # noqa: E402

OUT_ROOT = ROOT / "reports" / "conformweb_visualizations"
DATA_DIR = OUT_ROOT / "data"
FIG_DIR = OUT_ROOT / "figures"
TABLE_DIR = OUT_ROOT / "tables"
TARGET_ROOT = ROOT / "targets" / "web"

MAIN_DIR = FIG_DIR / "main"
MOA_DIR = FIG_DIR / "main_or_appendix"
APP_DIR = FIG_DIR / "appendix"
REVIEW_DIR = FIG_DIR / "review"

FAMILY_ORDER = [
    "Travel",
    "Grocery",
    "Clinical Command",
    "Campus Registrar",
    "Media Campaign",
    "Home Services",
]
SUITE_TO_FAMILY = {
    "stayflow_concierge": "Travel",
    "freshcart_market": "Grocery",
    "clinic_shift_command": "Clinical Command",
    "campus_registrar_command": "Campus Registrar",
    "media_campaign_launch_desk": "Media Campaign",
    "homefix_hub": "Home Services",
}
TIER_ORDER = ["A", "B", "C", "D"]
TIER_NAME = {
    "A": "Consumer",
    "B": "Operational",
    "C": "Regulated",
    "D": "Release-stage",
}
TIER_FULL = {t: f"Tier {t}\n{TIER_NAME[t]}" for t in TIER_ORDER}
MODEL_ORDER = ["M", "T", "F"]
MODEL_NAME = {"M": "Mini", "T": "Turbo", "F": "Frontier"}
MODEL_SHORT = {"M": "M", "T": "T", "F": "F"}

COL = {
    "ink": "#202124",
    "muted": "#5F6368",
    "grid": "#E4E7EB",
    "full": "#3C4043",
    "scenario": "#E8710A",
    "step": "#1A73E8",
    "mini": "#78909C",
    "turbo": "#F29900",
    "frontier": "#673AB7",
    "blue": "#1A73E8",
    "blue2": "#4285F4",
    "lightblue": "#D2E3FC",
    "orange": "#E8710A",
    "yellow": "#F9AB00",
    "green": "#34A853",
    "purple": "#A142F4",
    "teal": "#00ACC1",
    "pink": "#CC79A7",
    "gray": "#BDC1C6",
    "lightgray": "#F1F3F4",
}
MODEL_COLORS = {"M": COL["mini"], "T": COL["turbo"], "F": COL["frontier"]}
FAILURE_ORDER = [
    "Missing surface",
    "Invalid observation",
    "Unavailable control",
    "Wrong transition",
    "Route / persistence drift",
    "Projection mismatch",
    "Async failure",
    "Long-horizon drift",
]
FAILURE_COLORS = {
    # Palette family adapted from the supplied basic/intermediate/complex/edge
    # example. Exact contract-reference colors are intentionally not reused here.
    "Missing surface": "#E6675E",
    "Invalid observation": "#9AA0A6",
    "Unavailable control": "#E2A72E",
    "Wrong transition": "#4D83E6",
    "Route / persistence drift": "#2AAAB2",
    "Projection mismatch": "#7B61D1",
    "Async failure": "#BF4B45",
    "Long-horizon drift": "#4E5A64",
}
HEAT = LinearSegmentedColormap.from_list(
    "cw_blue",
    ["#FFFFFF", "#E8F0FE", "#D2E3FC", "#AECBFA", "#669DF6", "#1A73E8", "#174EA6"],
)
COUPLING = LinearSegmentedColormap.from_list(
    "cw_coupling",
    ["#FFFFFF", "#E0F7FA", "#B2EBF2", "#80DEEA", "#26C6DA", "#00838F"],
)

README_ROWS: list[dict[str, str]] = []
VALIDATION_LINES: list[str] = []


def setup_style() -> None:
    sns.set_theme(context="paper", style="white")
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.dpi": 140,
            "savefig.dpi": 300,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#B8BCC2",
            "axes.linewidth": 0.8,
        }
    )


def ensure_dirs() -> None:
    for d in [MAIN_DIR, MOA_DIR, APP_DIR, REVIEW_DIR, TABLE_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def save(fig: mpl.figure.Figure, stem: Path, source: str, location: str, message: str) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    for suffix in [".pdf", ".png"]:
        fig.savefig(stem.with_suffix(suffix), bbox_inches="tight", dpi=300)
    plt.close(fig)
    README_ROWS.append(
        {
            "filename": str(stem.relative_to(OUT_ROOT)),
            "source_data": source,
            "script": "tools/build_conformweb_figure_pack.py",
            "location": location,
            "message": message,
        }
    )


def pct_axis(x: float, _pos: int | None = None) -> str:
    return f"{int(round(x))}%"


def fmt_pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def fmt_count(a: float | int, b: float | int) -> str:
    return f"{int(round(a)):,}/{int(round(b)):,}"


def family_from_suite(suite: str) -> str:
    return SUITE_TO_FAMILY.get(str(suite), base.short_family_label(base.domain_label(str(suite))))


def add_family_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["family"] = df["suite"].map(family_from_suite)
    df["family"] = pd.Categorical(df["family"], FAMILY_ORDER, ordered=True)
    if "model_tier" in df:
        df["model_group"] = df["model_tier"].map(MODEL_NAME)
    return df


def weighted_mean(df: pd.DataFrame, value: str, weight: str = "runs") -> float:
    d = df[[value, weight]].dropna()
    total = d[weight].sum()
    if total <= 0:
        return np.nan
    return float((d[value] * d[weight]).sum() / total)


def load_report() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tier = pd.read_csv(DATA_DIR / "report_tier_rollups.csv")
    model_tier = pd.read_csv(DATA_DIR / "report_model_tier_rollups.csv")
    per_model = pd.read_csv(DATA_DIR / "report_per_model_rollups.csv")
    tier = add_family_cols(base.preferred_report_rows(tier))
    model_tier = add_family_cols(base.preferred_report_rows(model_tier))
    per_model = add_family_cols(base.preferred_report_rows(per_model))
    return tier, model_tier, per_model


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    runs = pd.read_csv(DATA_DIR / "raw_runs.csv")
    scen = pd.read_csv(DATA_DIR / "raw_scenarios.csv")
    steps = pd.read_csv(DATA_DIR / "raw_steps.csv")
    for df in [runs, scen, steps]:
        df["family"] = df["suite"].map(family_from_suite)
        df["family"] = pd.Categorical(df["family"], FAMILY_ORDER, ordered=True)
        df["model_group"] = df["model_tier"].map(MODEL_NAME)
    return runs, scen, steps


def report_family_summary(tier: pd.DataFrame, *, missing_as_failed: bool = False) -> pd.DataFrame:
    df = tier.copy()
    if missing_as_failed:
        expected_total = 90.0
        df["_denom"] = df["full_total"].clip(lower=expected_total)
        df["_formal_num"] = df["formal_mean"] * df["full_total"]
        df["_step_num"] = df["stepwise_mean"] * df["full_total"]
    else:
        df["_denom"] = df["full_total"]
        df["_formal_num"] = df["formal_mean"] * df["runs"]
        df["_step_num"] = df["stepwise_mean"] * df["runs"]

    def adjusted_mean(sub: pd.DataFrame, numerator: str) -> float:
        denom = sub["_denom"].sum()
        if denom <= 0:
            return np.nan
        return float(sub[numerator].sum() / denom)

    rows = []
    overall = {
        "family": "Overall",
        "runs": df["_denom"].sum(),
        "full_pass": df["full_pass"].sum(),
        "full_total": df["_denom"].sum(),
        "full_pass_rate": df["full_pass"].sum() / df["_denom"].sum(),
        "formal_mean": adjusted_mean(df, "_formal_num"),
        "stepwise_mean": adjusted_mean(df, "_step_num"),
    }
    rows.append(overall)
    for fam in FAMILY_ORDER:
        sub = df[df["family"] == fam]
        rows.append(
            {
                "family": fam,
                "runs": sub["_denom"].sum(),
                "full_pass": sub["full_pass"].sum(),
                "full_total": sub["_denom"].sum(),
                "full_pass_rate": sub["full_pass"].sum() / sub["_denom"].sum(),
                "formal_mean": adjusted_mean(sub, "_formal_num"),
                "stepwise_mean": adjusted_mean(sub, "_step_num"),
            }
        )
    return pd.DataFrame(rows)


def normalize_failure(raw: Any) -> str:
    s = str(raw).strip().lower()
    if "missing" in s:
        return "Missing surface"
    if "invalid" in s or "observation" in s or "state_hook" in s:
        return "Invalid observation"
    if "unavailable" in s or "action unavailable" in s or "disabled" in s:
        return "Unavailable control"
    if "route" in s or "persistence" in s or "browser" in s or "reload" in s:
        return "Route / persistence drift"
    if "table" in s or "rendered" in s or "projection" in s:
        return "Projection mismatch"
    if "async" in s or "timeout" in s:
        return "Async failure"
    if "long" in s or "drift" in s:
        return "Long-horizon drift"
    if "wrong" in s or "state" in s or "assertion" in s:
        return "Wrong transition"
    return "Wrong transition"


def iter_scenarios(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    obj = yaml.safe_load(path.read_text()) or {}
    return list(obj.get("scenarios") or [])


def walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def count_string_hits(obj: Any, pattern: str) -> int:
    rx = re.compile(pattern, re.I)
    count = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if rx.search(str(k)):
                count += 1
            count += count_string_hits(v, pattern)
    elif isinstance(obj, list):
        for v in obj:
            count += count_string_hits(v, pattern)
    elif isinstance(obj, str):
        if rx.search(obj):
            count += 1
    return count


def scenario_lengths_for(suite: str, tier: str) -> tuple[list[int], dict[str, int]]:
    tdir = TARGET_ROOT / suite / f"tier_{tier.lower()}"
    counts = {"public": 0, "private": 0, "probe": 0, "validation": 0}
    lengths: list[int] = []
    for vis in ["public", "private"]:
        scenarios = iter_scenarios(tdir / f"scenarios.{vis}.dsl.yaml")
        counts[vis] += len(scenarios)
        for sc in scenarios:
            lengths.append(len(sc.get("steps") or []))
    for name in ["scenarios.probe.dsl.yaml", "scenarios.validation.dsl.yaml"]:
        scenarios = iter_scenarios(tdir / name)
        key = "probe" if "probe" in name else "validation"
        counts[key] += len(scenarios)
        for sc in scenarios:
            lengths.append(len(sc.get("steps") or []))
    return lengths, counts


def build_inventory(tier: pd.DataFrame) -> pd.DataFrame:
    suite_metrics = pd.read_csv(DATA_DIR / "suite_metrics.csv") if (DATA_DIR / "suite_metrics.csv").exists() else pd.DataFrame()
    raw_scen = pd.read_csv(DATA_DIR / "raw_scenarios.csv") if (DATA_DIR / "raw_scenarios.csv").exists() else pd.DataFrame()
    raw_steps = pd.read_csv(DATA_DIR / "raw_steps.csv") if (DATA_DIR / "raw_steps.csv").exists() else pd.DataFrame()
    metric_lookup = {
        (r.suite, str(r.tier)): r
        for r in suite_metrics.itertuples(index=False)
    }
    rows: list[dict[str, Any]] = []
    for r in tier.sort_values(["family", "tier"]).itertuples(index=False):
        suite, tier_code = str(r.suite), str(r.tier)
        tdir = TARGET_ROOT / suite / f"tier_{tier_code.lower()}"
        contract_path = tdir / "contract.dsl.yaml"
        contract_text = contract_path.read_text() if contract_path.exists() else ""
        contract = yaml.safe_load(contract_text) if contract_text else {}
        runtime = (contract or {}).get("runtime") or {}
        state = (contract or {}).get("state") or {}
        components = (contract or {}).get("components") or {}
        lengths, split = scenario_lengths_for(suite, tier_code)
        raw_scen_fallback = pd.DataFrame()
        raw_steps_fallback = pd.DataFrame()
        if not raw_scen.empty:
            raw_scen_fallback = raw_scen[
                (raw_scen["view_current_raw"] == True)  # noqa: E712
                & (raw_scen["suite"] == suite)
                & (raw_scen["tier"].astype(str) == tier_code)
                & (raw_scen["kind"] == "scoring")
            ].copy()
        if not raw_steps.empty:
            raw_steps_fallback = raw_steps[
                (raw_steps["view_current_raw"] == True)  # noqa: E712
                & (raw_steps["suite"] == suite)
                & (raw_steps["tier"].astype(str) == tier_code)
                & (raw_steps["kind"] == "scoring")
            ].copy()
        if not lengths and not raw_scen_fallback.empty:
            dedup = raw_scen_fallback.sort_values("expected_step_count").drop_duplicates("scenario_id")
            lengths = dedup["expected_step_count"].dropna().astype(int).tolist()
            split["public"] = int((dedup["visibility"] == "public").sum())
            split["private"] = int((dedup["visibility"] == "private").sum())
        metrics = metric_lookup.get((suite, tier_code))
        def metric(name: str, default: float = 0.0) -> float:
            if metrics is not None and hasattr(metrics, name):
                val = getattr(metrics, name)
                if not pd.isna(val):
                    return float(val)
            return default
        state_schema = state.get("schema") if isinstance(state, dict) else {}
        pages = runtime.get("pages") if isinstance(runtime, dict) else []
        roles = (((runtime.get("session") or {}) if isinstance(runtime, dict) else {}).get("roles") or [])
        services = runtime.get("services") if isinstance(runtime, dict) else []
        tables = runtime.get("tables") if isinstance(runtime, dict) else []
        selector_count = sum(1 for obj in walk(contract) if isinstance(obj, dict) and "selector" in obj)
        if selector_count == 0 and not raw_steps_fallback.empty:
            selector_count = int(raw_steps_fallback["component"].dropna().nunique())
        raw_action_count = (
            int(raw_steps_fallback[["action", "component"]].dropna(how="all").drop_duplicates().shape[0])
            if not raw_steps_fallback.empty
            else len(components)
        )
        row = {
            "instance_id": f"{suite}_tier_{tier_code.lower()}",
            "suite": suite,
            "family": family_from_suite(suite),
            "tier": tier_code,
            "tier_name": TIER_NAME[tier_code],
            "contract_tokens": len(contract_text.split()),
            "num_selectors": selector_count,
            "num_actions": metric("component_actions", raw_action_count),
            "num_state_paths": metric("state_fields", len(state_schema) if isinstance(state_schema, dict) else 0),
            "num_routes": metric("pages", len(pages) if isinstance(pages, list) else 0),
            "num_roles": len(roles) if isinstance(roles, list) else 0,
            "num_service_fixtures": metric("services", len(services) if isinstance(services, list) else 0),
            "num_upload_specs": count_string_hits(contract, r"\bupload\b|file"),
            "num_rendered_tables": metric("tables", len(tables) if isinstance(tables, list) else 0),
            "has_persistence": int(bool(runtime.get("persistence")) if isinstance(runtime, dict) else False),
            "has_browser_history": int("history" in contract_text.lower() or "back" in contract_text.lower()),
            "num_scoring_scenarios": split["public"] + split["private"],
            "num_public_scenarios": split["public"],
            "num_private_scenarios": split["private"],
            "num_probe_scenarios": split["probe"],
            "num_validation_scenarios": split["validation"],
            "median_steps_per_scenario": float(np.median(lengths)) if lengths else np.nan,
            "p90_steps_per_scenario": float(np.percentile(lengths, 90)) if lengths else np.nan,
        }
        rows.append(row)
    inv = pd.DataFrame(rows)
    inv["family"] = pd.Categorical(inv["family"], FAMILY_ORDER, ordered=True)
    inv["tier"] = pd.Categorical(inv["tier"], TIER_ORDER, ordered=True)
    feature_cols = [
        "median_steps_per_scenario",
        "p90_steps_per_scenario",
        "num_routes",
        "num_roles",
        "num_service_fixtures",
        "num_upload_specs",
        "num_rendered_tables",
        "has_persistence",
        "has_browser_history",
        "num_state_paths",
    ]
    score = np.zeros(len(inv), dtype=float)
    weights = {
        "median_steps_per_scenario": 1.1,
        "p90_steps_per_scenario": 0.9,
        "num_routes": 0.9,
        "num_roles": 0.8,
        "num_service_fixtures": 0.8,
        "num_upload_specs": 0.9,
        "num_rendered_tables": 0.8,
        "has_persistence": 0.7,
        "has_browser_history": 0.5,
        "num_state_paths": 0.7,
    }
    for col in feature_cols:
        vals = inv[col].astype(float).fillna(0).to_numpy()
        if vals.max() > vals.min():
            vals = (vals - vals.min()) / (vals.max() - vals.min())
        else:
            vals = vals * 0
        score += weights[col] * vals
    score = 10 + 90 * (score - score.min()) / max(score.max() - score.min(), 1e-9)
    inv["behavioral_coupling_score"] = score
    return inv.sort_values(["family", "tier"]).reset_index(drop=True)


def figure_conformance_gap(tier: pd.DataFrame, *, square: bool = False) -> None:
    df = report_family_summary(tier, missing_as_failed=True)
    y = np.arange(len(df), dtype=float)
    if len(y) > 1:
        y[1:] += 0.35
    if square:
        fig, ax = plt.subplots(figsize=(7.6, 7.6), dpi=300)
        count_font = 10.0
        ytick_font = 12.0
        xtick_font = 11.8
        xlabel_font = 13.0
        legend_font = 12.0
        marker_scale = 1.12
    else:
        fig, ax = plt.subplots(figsize=(8.55, 4.25))
        count_font = 8.7
        ytick_font = 9.8
        xtick_font = 9.5
        xlabel_font = 10.2
        legend_font = 8.8
        marker_scale = 1.0
    ax.set_axisbelow(True)
    for x in [0, 25, 50, 75, 100]:
        ax.axvline(x, color=COL["grid"], lw=0.8, zorder=0)
    scen = df["formal_mean"] * 100
    step = df["stepwise_mean"] * 100
    full = df["full_pass_rate"] * 100
    for i in range(len(df)):
        ax.plot([scen.iloc[i], step.iloc[i]], [y[i], y[i]], color="#AAB7C4", lw=2.2, solid_capstyle="round", zorder=1)
    ax.scatter(full, y, s=46 * marker_scale, color=COL["full"], marker="D", label="Full pass", zorder=3)
    ax.scatter(scen, y, s=58 * marker_scale, color=COL["scenario"], edgecolor="white", lw=0.7, label="Scenario-level", zorder=4)
    ax.scatter(step, y, s=58 * marker_scale, color=COL["step"], edgecolor="white", lw=0.7, label="Step-level", zorder=4)
    for i, r in df.iterrows():
        count_label = fmt_count(r.full_pass, r.full_total)
        if not square:
            count_label = f"{count_label} ({100 * r.full_pass_rate:.1f}%)"
        ax.text(
            min(full.iloc[i] + 2.1, 94),
            y[i],
            count_label,
            va="center",
            ha="left",
            fontsize=count_font,
            fontweight="bold",
            color=COL["ink"],
        )
    ax.axhline((y[0] + y[1]) / 2, color="#C9CDD3", lw=0.9)
    labels = list(df["family"])
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    for label in ax.get_yticklabels():
        label.set_fontsize(ytick_font)
        label.set_fontweight("bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(y[-1] + 0.6, y[0] - 0.95)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.set_xlabel("Score")
    leg = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.52, 1.04),
        ncol=3,
        frameon=False,
        handletextpad=0.4,
        columnspacing=1.2,
        prop={"weight": "bold", "size": legend_font},
    )
    for lh in leg.legend_handles:
        if hasattr(lh, "set_sizes"):
            lh.set_sizes([45])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=xtick_font)
    for label in ax.get_xticklabels():
        label.set_fontweight("bold")
    ax.xaxis.label.set_fontsize(xlabel_font)
    ax.xaxis.label.set_fontweight("bold")
    if square:
        fig.subplots_adjust(left=0.34, right=0.94, top=0.86, bottom=0.12)
        stem = MAIN_DIR / "figure_conformance_gap_square"
        stem.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(stem.with_suffix(".pdf"))
        fig.savefig(stem.with_suffix(".png"), dpi=300)
        plt.close(fig)
        README_ROWS.append(
            {
                "filename": str(stem.relative_to(OUT_ROOT)),
                "source_data": "data/report_tier_rollups.csv",
                "script": "tools/build_conformweb_figure_pack.py",
                "location": "Main or Appendix",
                "message": "Square conformance-gap variant for side-by-side figure composition.",
            }
        )
    else:
        save(
            fig,
            MAIN_DIR / "figure_conformance_gap",
            "data/report_tier_rollups.csv",
            "Main",
            "Generated apps make partial progress, but strict full-pass rates remain low across all six families.",
        )


def figure_model_capability(model_tier: pd.DataFrame) -> None:
    df = model_tier.copy()
    expected_per_instance_group = 30.0
    df["_denom"] = df["full_total"].clip(lower=expected_per_instance_group)
    df["_formal_num"] = df["formal_mean"] * df["full_total"]
    df["_step_num"] = df["stepwise_mean"] * df["full_total"]
    df["model_group"] = df["model_tier"].map(MODEL_NAME)
    df["x"] = df["model_tier"].map({m: i for i, m in enumerate(MODEL_ORDER)})
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(7.6, 3.35), gridspec_kw={"width_ratios": [1.45, 1.0], "wspace": 0.36}
    )
    offsets = {"formal_mean": -0.12, "stepwise_mean": 0.12}
    colors = {"formal_mean": COL["scenario"], "stepwise_mean": COL["step"]}
    labels = {"formal_mean": "Scenario-level", "stepwise_mean": "Step-level"}
    for metric in ["formal_mean", "stepwise_mean"]:
        for mt in MODEL_ORDER:
            sub = df[df.model_tier == mt]
            x = MODEL_ORDER.index(mt) + offsets[metric]
            vals = sub[metric].dropna().to_numpy() * 100
            if len(vals):
                jitter = np.linspace(-0.035, 0.035, len(vals))
                ax1.scatter(
                    np.full(len(vals), x) + jitter,
                    vals,
                    s=16,
                    color=colors[metric],
                    alpha=0.42,
                    linewidth=0,
                )
                numerator = "_formal_num" if metric == "formal_mean" else "_step_num"
                mean = 100 * sub[numerator].sum() / sub["_denom"].sum()
                se = vals.std(ddof=1) / math.sqrt(len(vals)) if len(vals) > 1 else 0
                ax1.errorbar(
                    [x],
                    [mean],
                    yerr=[1.96 * se],
                    fmt="o",
                    color=colors[metric],
                    markersize=8.2,
                    capsize=3.5,
                    lw=1.5,
                    zorder=5,
                    label=labels[metric] if mt == "M" else None,
                )
    ax1.set_xticks(range(3))
    ax1.set_xticklabels([MODEL_NAME[m] for m in MODEL_ORDER])
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("Score")
    ax1.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax1.grid(axis="y", color=COL["grid"], lw=0.8)
    ax1.set_title("(a) Partial progress scales faster", loc="left", fontweight="bold")
    ax1.legend(loc="upper left", frameon=False, ncol=1, prop={"weight": "bold", "size": 8.8})

    grp = (
        df.groupby("model_tier", observed=True)
        .agg(full_pass=("full_pass", "sum"), full_total=("_denom", "sum"))
        .reindex(MODEL_ORDER)
    )
    rates = grp["full_pass"] / grp["full_total"] * 100
    bars = ax2.bar(range(3), rates, width=0.58, color=[MODEL_COLORS[m] for m in MODEL_ORDER], alpha=0.9)
    for i, (bar, mt) in enumerate(zip(bars, MODEL_ORDER)):
        rate = 100 * grp.loc[mt, "full_pass"] / grp.loc[mt, "full_total"]
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.2,
            f"{fmt_count(grp.loc[mt, 'full_pass'], grp.loc[mt, 'full_total'])}\n({rate:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=8.6,
            fontweight="bold",
            linespacing=0.95,
            color=COL["ink"],
        )
    ax2.set_xticks(range(3))
    ax2.set_xticklabels([MODEL_NAME[m] for m in MODEL_ORDER])
    ax2.set_ylim(0, max(33, float(rates.max()) + 10))
    ax2.set_ylabel("Full-pass rate")
    ax2.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax2.grid(axis="y", color=COL["grid"], lw=0.8)
    ax2.set_title("(b) Completion remains hard", loc="left", fontweight="bold")
    for ax in (ax1, ax2):
        ax.tick_params(axis="both", labelsize=9.4)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontweight("bold")
        ax.xaxis.label.set_fontweight("bold")
        ax.yaxis.label.set_fontweight("bold")
        ax.title.set_fontsize(10.4)
    save(
        fig,
        MOA_DIR / "figure_model_capability",
        "data/report_model_tier_rollups.csv",
        "Main or Appendix",
        "Small points are family-tier instances; large points are run-weighted model-group means with intervals. Capability improves step-level progress more than strict full conformance.",
    )


def figure_complexity_heatmap(tier: pd.DataFrame) -> None:
    mat = tier.pivot_table(index="family", columns="tier", values="formal_mean", observed=True).reindex(FAMILY_ORDER)[TIER_ORDER]
    count = tier.pivot_table(index="family", columns="tier", values="runs", observed=True).reindex(FAMILY_ORDER)[TIER_ORDER]
    ann = mat.copy().astype(object)
    for fam in FAMILY_ORDER:
        for t in TIER_ORDER:
            val = mat.loc[fam, t]
            if pd.isna(val):
                ann.loc[fam, t] = "N/A"
            else:
                ann.loc[fam, t] = f"{val*100:.0f}%\nn={int(count.loc[fam, t])}"
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    sns.heatmap(
        mat * 100,
        ax=ax,
        cmap=HEAT,
        vmin=0,
        vmax=100,
        annot=ann,
        fmt="",
        linewidths=1.0,
        linecolor="white",
        cbar_kws={"label": "Scenario-level conformance", "ticks": [0, 25, 50, 75, 100]},
        annot_kws={"fontsize": 8},
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticklabels([f"Tier {t}\n{TIER_NAME[t]}" for t in TIER_ORDER], rotation=0)
    ax.set_yticklabels(FAMILY_ORDER, rotation=0)
    save(
        fig,
        MOA_DIR / "figure_complexity_ladder_heatmap",
        "data/report_tier_rollups.csv",
        "Main or Appendix",
        "Conformance varies across empirical behavioral-coupling tiers and product families.",
    )


def figure_difficulty_scaling(model_tier: pd.DataFrame) -> None:
    agg = []
    for (tier, mt), sub in model_tier.groupby(["tier", "model_tier"], observed=True):
        agg.append(
            {
                "tier": tier,
                "model_tier": mt,
                "formal_mean": weighted_mean(sub, "formal_mean"),
                "stepwise_mean": weighted_mean(sub, "stepwise_mean"),
                "full_pass_rate": float(sub["full_pass"].sum() / sub["full_total"].sum())
                if sub["full_total"].sum() > 0
                else np.nan,
            }
        )
    df = pd.DataFrame(agg)
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.05), gridspec_kw={"wspace": 0.28})
    for ax, metric, title in zip(
        axes,
        ["formal_mean", "stepwise_mean", "full_pass_rate"],
        ["(a) Scenario-level", "(b) Step-level", "(c) Full-pass rate"],
    ):
        for mt in MODEL_ORDER:
            sub = df[df.model_tier == mt].set_index("tier").reindex(TIER_ORDER)
            values = sub[metric] * 100
            ax.plot(
                range(4),
                values,
                color=MODEL_COLORS[mt],
                marker="o",
                lw=2.0,
                label=MODEL_NAME[mt],
            )
            ax.text(
                3.10,
                values.iloc[-1],
                MODEL_SHORT[mt],
                color=MODEL_COLORS[mt],
                va="center",
                fontsize=8,
                fontweight="bold",
            )
        ax.set_xticks(range(4))
        ax.set_xticklabels(TIER_ORDER)
        ax.set_xlim(-0.12, 3.32)
        if metric == "full_pass_rate":
            ax.set_ylim(0, 50)
            ax.set_yticks([0, 10, 20, 30, 40, 50])
        else:
            ax.set_ylim(0, 100)
            ax.set_yticks([0, 20, 40, 60, 80, 100])
        ax.grid(axis="y", color=COL["grid"], lw=0.8)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    axes[0].set_ylabel("Score")
    handles = [Line2D([0], [0], color=MODEL_COLORS[m], marker="o", lw=2, label=MODEL_NAME[m]) for m in MODEL_ORDER]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=3, frameon=False)
    fig.subplots_adjust(bottom=0.22)
    save(
        fig,
        MOA_DIR / "figure_difficulty_scaling_curve",
        "data/report_model_tier_rollups.csv",
        "Main or Appendix",
        "Capability bands degrade differently across the Tier A-D ladder. A=Consumer, B=Operational, C=Regulated, D=Release-stage.",
    )


def trace_scope_scenarios(scen: pd.DataFrame) -> pd.DataFrame:
    return scen[(scen["view_current_raw"] == True) & (scen["kind"] == "scoring")].copy()  # noqa: E712


def dominant_drop_label(sub: pd.DataFrame, band_name: str = "") -> str:
    if sub.empty:
        return "few failures"
    labels = sub["first_failure_group"].map(normalize_failure).fillna("Wrong transition")
    shares = labels.value_counts(normalize=True)
    surface_share = float(shares.get("Invalid observation", 0) + shares.get("Missing surface", 0))
    projection_route_share = float(shares.get("Projection mismatch", 0) + shares.get("Route / persistence drift", 0))
    missing_share = float(shares.get("Missing surface", 0))
    if band_name == "early" and surface_share >= 0.20:
        return "state / observation"
    if band_name == "middle" and missing_share >= 0.15:
        return "state / controls"
    if band_name == "late" and projection_route_share >= 0.18:
        return "projection / route"
    top_failure = str(labels.value_counts().idxmax())
    tiers = sub["scenario_tier"].fillna("workflow").astype(str).str.replace("_", " ", regex=False)
    top_tier = str(tiers.value_counts().idxmax())
    if top_failure == "Wrong transition":
        return f"{top_tier}\nstate checks"
    if top_failure == "Invalid observation":
        return f"{top_tier}\nobservation"
    if top_failure == "Missing surface":
        return f"{top_tier}\nmissing surface"
    if top_failure == "Route / persistence drift":
        return f"{top_tier}\nroute/reload"
    if top_failure == "Projection mismatch":
        return f"{top_tier}\nprojection"
    return f"{top_tier}\n{top_failure.lower()}"


def figure_failure_taxonomy(scen: pd.DataFrame, steps: pd.DataFrame) -> None:
    df = trace_scope_scenarios(scen)
    failed = df[df["scenario_passed"] == False].copy()  # noqa: E712
    failed["failure_label"] = failed["first_failure_group"].map(normalize_failure)
    failed["tier"] = pd.Categorical(failed["tier"], TIER_ORDER, ordered=True)
    mix = (
        failed.groupby(["tier", "failure_label"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(index=TIER_ORDER, columns=FAILURE_ORDER, fill_value=0)
    )
    mix_share = mix.div(mix.sum(axis=1), axis=0).fillna(0)

    failed["norm_pos"] = (failed["first_failed_step"].fillna(failed["expected_step_count"]) / failed["expected_step_count"]).clip(0, 1)
    timing = failed.groupby("failure_label", observed=True).agg(n=("scenario_id", "size"), median=("norm_pos", "median")).reindex(FAILURE_ORDER)
    timing = timing[timing["n"].fillna(0) > 0]

    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(10.45, 4.1),
        gridspec_kw={"width_ratios": [1.52, 0.98], "wspace": 0.46},
    )
    left = np.zeros(len(mix_share))
    y = np.arange(len(mix_share))
    for cat in FAILURE_ORDER:
        vals = mix_share[cat].to_numpy() * 100
        if vals.sum() == 0:
            continue
        ax1.barh(y, vals, left=left, color=FAILURE_COLORS[cat], edgecolor="white", lw=0.75, label=cat)
        left += vals
    ax1.set_yticks(y)
    ax1.set_yticklabels([TIER_FULL[t] for t in TIER_ORDER])
    ax1.set_xlim(0, 100)
    ax1.invert_yaxis()
    ax1.xaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax1.set_xlabel("Share of failed scenarios")
    ax1.set_title("(a) Failure mix by tier", loc="left", fontweight="bold", fontsize=10.8)
    ax1.grid(axis="x", color=COL["grid"], lw=0.8)

    yy = np.arange(len(timing))
    sizes = 1600 * timing["n"] / timing["n"].max()
    ax2.scatter(
        timing["median"] * 100,
        yy,
        s=sizes,
        c=[FAILURE_COLORS[c] for c in timing.index],
        alpha=0.82,
        edgecolor="white",
        lw=0.8,
    )
    for i, (cat, row) in enumerate(timing.iterrows()):
        raw_x = row["median"] * 100
        if raw_x >= 95:
            timing_label = "final check"
        elif raw_x >= 70:
            timing_label = "late"
        elif raw_x >= 40:
            timing_label = "middle"
        elif raw_x >= 15:
            timing_label = "early"
        else:
            timing_label = "start"
        if raw_x > 86:
            x, ha = 98, "right"
        else:
            x, ha = raw_x + 6.0, "left"
        ax2.text(
            x,
            i,
            timing_label,
            va="center",
            ha=ha,
            fontsize=8.9,
            fontweight="bold",
            color=COL["ink"],
        )
    wrap = {
        "Missing surface": "Missing\nsurface",
        "Invalid observation": "Invalid\nobservation",
        "Unavailable control": "Unavailable\ncontrol",
        "Wrong transition": "Wrong\ntransition",
        "Route / persistence drift": "Route /\npersistence",
        "Projection mismatch": "Projection\nmismatch",
        "Async failure": "Async\nfailure",
        "Long-horizon drift": "Long-horizon\ndrift",
    }
    ax2.set_yticks(yy)
    ax2.set_yticklabels([wrap.get(x, x) for x in timing.index])
    ax2.set_xlim(0, 106)
    ax2.set_xticks([0, 25, 50, 75, 100])
    ax2.set_xticklabels(["start", "early", "middle", "late", "final"])
    ax2.set_xlabel("First-failure stage\nbubble area = failed-scenario count")
    ax2.set_title("(b) Timing by category", loc="left", fontweight="bold", fontsize=10.8)
    ax2.grid(axis="x", color=COL["grid"], lw=0.8)
    handles = [
        Rectangle((0, 0), 1, 1, color=FAILURE_COLORS[c], label=c)
        for c in FAILURE_ORDER
        if c in mix.columns and mix[c].sum() > 0
    ]
    for ax in (ax1, ax2):
        ax.tick_params(axis="both", labelsize=9.2)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontweight("bold")
        ax.xaxis.label.set_fontsize(9.4)
        ax.xaxis.label.set_fontweight("bold")
        ax.yaxis.label.set_fontweight("bold")
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=3,
        frameon=False,
        prop={"weight": "bold", "size": 8.6},
    )
    fig.subplots_adjust(bottom=0.27)
    save(
        fig,
        MAIN_DIR / "figure_failure_taxonomy",
        "data/raw_scenarios.csv",
        "Main",
        "First-failure categories reveal both early surface errors and later behavioral drift.",
    )

    # Appendix: split wrong transitions into interpretable state-transition subtypes.
    br = failed[failed["failure_label"] == "Wrong transition"].copy()
    if not br.empty:
        br["wrong_transition_subtype"] = br.apply(wrong_transition_subtype, axis=1)
        order = [
            "validation mismatch",
            "counter / total mismatch",
            "service-response mismatch",
            "unauthorized mutation",
            "upload-derived state mismatch",
            "status transition mismatch",
            "other state-value mismatch",
        ]
        counts = br["wrong_transition_subtype"].value_counts().reindex(order).dropna().sort_values(ascending=True)
        fig2, ax = plt.subplots(figsize=(5.8, 2.8))
        ax.barh(counts.index, counts.values, color=COL["orange"])
        ax.set_xlabel("First failed scenarios")
        ax.grid(axis="x", color=COL["grid"], lw=0.8)
        save(
            fig2,
            APP_DIR / "appendix_wrong_transition_breakdown",
            "data/raw_scenarios.csv",
            "Appendix",
            "Wrong-transition failures are decomposed into validation, counter, service, authorization, upload, status, and residual state-value subtypes.",
        )


def wrong_transition_subtype(row: pd.Series) -> str:
    text = " ".join(
        str(row.get(k, ""))
        for k in [
            "first_failure_raw",
            "scenario_id",
            "first_failed_action",
            "first_failed_component",
            "first_failed_actor",
        ]
    ).lower()
    if any(tok in text for tok in ["validation", "required", "error", "conflict", "invalid"]):
        return "validation mismatch"
    if any(tok in text for tok in ["count", "total", "subtotal", "price", "amount", "delta", "length", "linear"]):
        return "counter / total mismatch"
    if any(tok in text for tok in ["service", "api", "quote", "insurance", "lookup", "weather", "payment"]):
        return "service-response mismatch"
    if any(tok in text for tok in ["unauthorized", "permission", "role", "cannot", "denied", "unchanged"]):
        return "unauthorized mutation"
    if any(tok in text for tok in ["upload", "file", "csv", "import", "transfer", "referral"]):
        return "upload-derived state mismatch"
    if any(tok in text for tok in ["status", "approve", "reject", "release", "dispatch", "seal", "handoff", "finalize", "one_of"]):
        return "status transition mismatch"
    return "other state-value mismatch"


def relation_group(raw: Any) -> str:
    s = str(raw).lower()
    if "validation" in s:
        return "validation mismatch"
    if "count" in s or "length" in s or "delta" in s or "linear" in s:
        return "counter / total mismatch"
    if "service" in s:
        return "service-response mismatch"
    if "unchanged" in s or "unauthorized" in s:
        return "unauthorized mutation"
    if "upload" in s or "file" in s:
        return "upload-derived state mismatch"
    if "status" in s or "one_of" in s:
        return "status transition mismatch"
    if "table" in s:
        return "rendered projection mismatch"
    if "browser" in s or "page" in s or "route" in s:
        return "route / persistence mismatch"
    if s == "nan" or not s:
        return "unknown assertion"
    return "state-value mismatch"


def figure_survival(scen: pd.DataFrame) -> None:
    df = trace_scope_scenarios(scen)
    df["norm_fail"] = np.where(
        df["scenario_passed"].astype(bool),
        1.0,
        (df["first_failed_step"].fillna(df["expected_step_count"]) / df["expected_step_count"]).clip(0, 1),
    )
    xs = np.linspace(0, 1, 101)
    failed = df[df["scenario_passed"] == False].copy()  # noqa: E712
    fig, ax = plt.subplots(figsize=(7.0, 3.75))

    # Show where first failures concentrate. The bands are descriptive: they
    # summarize the raw trace distribution rather than naming fixed workflow
    # milestones that every scenario must contain.
    bands = [(0.00, 0.25), (0.25, 0.60), (0.60, 1.0001)]
    band_names = ["EARLY", "MIDDLE", "LATE"]
    band_fills = ["#F8FBFF", "#FFF8F0", "#F7F4FF"]
    for (lo, hi), name, fill in zip(bands, band_names, band_fills):
        sub = failed[(failed["norm_fail"] >= lo) & (failed["norm_fail"] < hi)]
        if sub.empty:
            continue
        share = len(sub) / max(1, len(df))
        ax.axvspan(lo * 100, min(hi, 1.0) * 100, color=fill, zorder=-3)
        label = dominant_drop_label(sub, name.lower()).replace("\n", " ")
        ax.text(
            (lo + min(hi, 1.0)) * 50,
            1.045,
            f"{name} {lo:.0%}-{min(hi, 1.0):.0%}\n{share:.0%} traces\n{label}",
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="bottom",
            fontsize=8.0,
            fontweight="bold",
            color=COL["ink"],
            linespacing=1.05,
            clip_on=False,
        )
    for x in [25, 60]:
        ax.axvline(x, color="#DADCE0", lw=0.9, zorder=-2)

    for mt in MODEL_ORDER:
        sub = df[df.model_tier == mt]
        vals = sub["norm_fail"].dropna().to_numpy()
        ys = np.array([(vals >= x - 1e-9).mean() for x in xs])
        ax.step(xs * 100, ys * 100, where="post", color=MODEL_COLORS[mt], lw=2.3, label=MODEL_NAME[mt])
        ax.text(101, ys[-1] * 100, MODEL_NAME[mt], color=MODEL_COLORS[mt], va="center", fontsize=8, fontweight="bold")

    ax.set_xlim(0, 108)
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.set_xlabel("Normalized scenario progress")
    ax.set_ylabel("Scenarios not yet failed")
    ax.grid(axis="y", color=COL["grid"], lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(
        0,
        -0.28,
        "Shaded bands group where first failures occur along the normalized trace; passed scenarios survive through 100%.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.2,
        color=COL["muted"],
    )
    fig.subplots_adjust(bottom=0.24, right=0.88, top=0.78)
    save(
        fig,
        MOA_DIR / "figure_long_horizon_survival",
        "data/raw_scenarios.csv",
        "Main or Appendix",
        "Survival curve with data-derived first-failure mass markers; passed scenarios are counted as surviving through 100% progress.",
    )


def figure_instance_heatmap(model_tier: pd.DataFrame) -> None:
    df = model_tier.copy()
    df["col"] = df["family"].astype(str) + " " + df["tier"].astype(str)
    col_order = [f"{fam} {t}" for fam in FAMILY_ORDER for t in TIER_ORDER]
    pivot = df.pivot_table(index="model_tier", columns="col", values="formal_mean", observed=True).reindex(MODEL_ORDER)[col_order]
    fig, ax = plt.subplots(figsize=(10.8, 2.45))
    sns.heatmap(
        pivot * 100,
        ax=ax,
        cmap=HEAT,
        vmin=0,
        vmax=100,
        annot=True,
        fmt=".0f",
        linewidths=0.7,
        linecolor="white",
        cbar_kws={"label": "Mean scenario-level conformance", "ticks": [0, 25, 50, 75, 100]},
        annot_kws={"fontsize": 6.7},
    )
    ax.set_yticklabels([MODEL_NAME[m] for m in MODEL_ORDER], rotation=0)
    ax.set_xticklabels([c.split()[-1] for c in col_order], rotation=0)
    ax.set_xlabel("")
    ax.set_ylabel("")
    for i, fam in enumerate(FAMILY_ORDER):
        x0 = i * 4
        ax.axvline(x0, color="#AEB4BB", lw=0.8)
        fam_label = fam.replace("Clinical Command", "Clinical\nCommand").replace("Campus Registrar", "Campus\nRegistrar").replace("Media Campaign", "Media\nCampaign").replace("Home Services", "Home\nServices")
        ax.text(x0 + 2, -0.43, fam_label, ha="center", va="bottom", fontsize=7.6, fontweight="bold", clip_on=False, linespacing=0.9)
    ax.axvline(len(col_order), color="#AEB4BB", lw=0.8)
    save(
        fig,
        APP_DIR / "appendix_instance_heatmap",
        "data/report_model_tier_rollups.csv",
        "Appendix",
        "Model-group performance is shown for every validated family-tier instance.",
    )


def figure_contract_feature(inv: pd.DataFrame, model_tier: pd.DataFrame) -> None:
    features = [
        "contract_tokens",
        "num_state_paths",
        "num_selectors",
        "num_actions",
        "num_routes",
        "num_roles",
        "num_service_fixtures",
        "num_upload_specs",
        "num_rendered_tables",
        "has_persistence",
        "has_browser_history",
        "median_steps_per_scenario",
        "p90_steps_per_scenario",
    ]
    pretty = {
        "contract_tokens": "Contract tokens",
        "num_state_paths": "State paths",
        "num_selectors": "Selectors",
        "num_actions": "Actions",
        "num_routes": "Routes",
        "num_roles": "Roles",
        "num_service_fixtures": "Service fixtures",
        "num_upload_specs": "Uploads",
        "num_rendered_tables": "Rendered tables",
        "has_persistence": "Persistence",
        "has_browser_history": "Browser history",
        "median_steps_per_scenario": "Median scenario steps",
        "p90_steps_per_scenario": "P90 scenario steps",
    }
    df = model_tier.merge(inv[["suite", "tier", *features]], on=["suite", "tier"], how="left")
    rows = []
    for feat in features:
        x = df[feat].astype(float)
        y = df["formal_mean"].astype(float)
        ok = x.notna() & y.notna()
        if ok.sum() < 5 or x[ok].std() == 0:
            continue
        r = np.corrcoef(x[ok], y[ok])[0, 1]
        # Fisher SE for a compact descriptive interval.
        se = 1 / math.sqrt(max(ok.sum() - 3, 1))
        z = np.arctanh(np.clip(r, -0.999, 0.999))
        lo, hi = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
        rows.append({"feature": pretty[feat], "r": r, "lo": lo, "hi": hi})
    res = pd.DataFrame(rows).sort_values("r")
    fig, ax = plt.subplots(figsize=(5.6, 4.3))
    y = np.arange(len(res))
    colors = [COL["blue"] if v > 0 else COL["orange"] for v in res["r"]]
    ax.hlines(y, res["lo"], res["hi"], color="#AAB7C4", lw=2)
    ax.scatter(res["r"], y, color=colors, s=38, zorder=3)
    ax.axvline(0, color=COL["muted"], lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(res["feature"])
    ax.set_xlabel("Correlation with scenario-level conformance")
    ax.grid(axis="x", color=COL["grid"], lw=0.8)
    ax.text(
        0.01,
        -0.16,
        "Descriptive association only; not a causal estimate.",
        transform=ax.transAxes,
        fontsize=7.5,
        color=COL["muted"],
    )
    fig.subplots_adjust(bottom=0.17)
    save(
        fig,
        APP_DIR / "appendix_contract_feature_difficulty",
        "data/report_model_tier_rollups.csv + tables/appendix_benchmark_inventory.csv",
        "Appendix",
        "Exploratory contract-feature associations with scenario-level conformance.",
    )


def figure_generation_variance(raw_runs: pd.DataFrame) -> None:
    df = raw_runs[raw_runs["view_current_raw"] == True].copy()  # noqa: E712
    order = [m for m in base.MODEL_ORDER if m in set(df["model"])]
    df["model_label_short"] = df["model"].map(base.MODEL_LABELS).fillna(df["model"])
    fig, ax = plt.subplots(figsize=(8.6, 3.7))
    data = [df[df.model == m]["formal_ratio"].dropna() * 100 for m in order]
    box = ax.boxplot(data, positions=np.arange(len(order)), widths=0.55, patch_artist=True, showfliers=False, medianprops={"color": "black", "lw": 1.3})
    for patch, m in zip(box["boxes"], order):
        mt = base.MODEL_TO_TIER.get(m, "M")
        patch.set_facecolor(MODEL_COLORS[mt])
        patch.set_alpha(0.28)
        patch.set_edgecolor(MODEL_COLORS[mt])
    rng = np.random.default_rng(7)
    for i, m in enumerate(order):
        sub = df[df.model == m]
        mt = base.MODEL_TO_TIER.get(m, "M")
        x = i + rng.uniform(-0.18, 0.18, len(sub))
        ax.scatter(x, sub["formal_ratio"] * 100, s=8, alpha=0.23, color=MODEL_COLORS[mt], linewidth=0)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(
        [("Gemini 3.1 Flash" if m == "gemini_flash_latest" else base.MODEL_LABELS.get(m, m)) for m in order],
        rotation=35,
        ha="right",
    )
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.set_ylabel("Scenario-level conformance")
    ax.grid(axis="y", color=COL["grid"], lw=0.8)
    for x in [2.5, 5.5]:
        ax.axvline(x, color="#B8BCC2", lw=0.8)
    save(
        fig,
        APP_DIR / "appendix_generation_variance",
        "data/raw_runs.csv",
        "Appendix",
        "Independent generations vary substantially within the same model.",
    )


def figure_complexity_map(inv: pd.DataFrame) -> None:
    mat = inv.pivot_table(index="family", columns="tier", values="behavioral_coupling_score", observed=True).reindex(FAMILY_ORDER)[TIER_ORDER]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    sns.heatmap(
        mat,
        ax=ax,
        cmap=COUPLING,
        vmin=0,
        vmax=100,
        linewidths=1,
        linecolor="white",
        cbar_kws={"label": "Relative behavioral coupling", "ticks": [0, 25, 50, 75, 100]},
    )
    for i, fam in enumerate(FAMILY_ORDER):
        for j, t in enumerate(TIER_ORDER):
            row = inv[(inv.family.astype(str) == fam) & (inv.tier.astype(str) == t)]
            if row.empty:
                ax.text(j + 0.5, i + 0.5, "N/A", ha="center", va="center", fontsize=8, color=COL["muted"])
                continue
            r = row.iloc[0]
            txt = f"{r.behavioral_coupling_score:.0f}\n{int(r.num_scoring_scenarios)} scenarios\nmedian {r.median_steps_per_scenario:.0f} steps"
            ax.text(j + 0.5, i + 0.5, txt, ha="center", va="center", fontsize=7.0, color=COL["ink"], linespacing=1.05)
    ax.set_xticklabels([f"Tier {t}\n{TIER_NAME[t]}" for t in TIER_ORDER], rotation=0)
    ax.set_yticklabels(FAMILY_ORDER, rotation=0)
    ax.set_xlabel("")
    ax.set_ylabel("")
    save(
        fig,
        MAIN_DIR / "figure_benchmark_complexity_map",
        "targets/web/*/tier_*/contract.dsl.yaml + scenarios.*.dsl.yaml",
        "Main",
        "Main-simple behavioral coupling summary; scores are rescaled to a relative 10-100 range to avoid implying an absolute zero.",
    )

    fig2, ax2 = plt.subplots(figsize=(12.8, 6.25))
    sns.heatmap(
        mat,
        ax=ax2,
        cmap=COUPLING,
        vmin=0,
        vmax=100,
        linewidths=1,
        linecolor="white",
        cbar_kws={
            "label": "Coupling score",
            "ticks": [0, 25, 50, 75, 100],
            "shrink": 0.82,
            "pad": 0.02,
        },
    )
    cbar = ax2.collections[0].colorbar
    if cbar is not None:
        cbar.ax.tick_params(labelsize=10.0)
        cbar.ax.yaxis.label.set_size(11.0)
    for i, fam in enumerate(FAMILY_ORDER):
        for j, t in enumerate(TIER_ORDER):
            row = inv[(inv.family.astype(str) == fam) & (inv.tier.astype(str) == t)]
            if row.empty:
                ax2.text(j + 0.5, i + 0.5, "N/A", ha="center", va="center", fontsize=8, color=COL["muted"])
                continue
            r = row.iloc[0]
            score = float(r.behavioral_coupling_score)
            text_color = "white" if score >= 72 else COL["ink"]
            sub_color = "#F8FBFF" if score >= 72 else COL["muted"]
            ax2.text(
                j + 0.5,
                i + 0.18,
                f"{score:.0f}",
                ha="center",
                va="center",
                fontsize=18.5,
                fontweight="bold",
                color=text_color,
            )
            ax2.text(
                j + 0.5,
                i + 0.38,
                f"S{int(r.num_scoring_scenarios)} | M{r.median_steps_per_scenario:g}",
                ha="center",
                va="center",
                fontsize=13.0,
                fontweight="bold",
                color=sub_color,
            )
            feature_lines = [
                f"R{int(r.num_routes)}  Ro{int(r.num_roles)}  Sv{int(r.num_service_fixtures)}",
                f"U{int(r.num_upload_specs)}  Tb{int(r.num_rendered_tables)}  P{'+' if int(r.has_persistence) else '-'}",
            ]
            ax2.text(
                j + 0.5,
                i + 0.64,
                feature_lines[0],
                ha="center",
                va="center",
                fontsize=12.2,
                fontweight="bold",
                color=sub_color,
                fontfamily="DejaVu Sans Mono",
            )
            ax2.text(
                j + 0.5,
                i + 0.82,
                feature_lines[1],
                ha="center",
                va="center",
                fontsize=12.2,
                fontweight="bold",
                color=sub_color,
                fontfamily="DejaVu Sans Mono",
            )
    ax2.set_xticklabels([f"Tier {t}\n{TIER_NAME[t]}" for t in TIER_ORDER], rotation=0)
    ax2.set_yticklabels(FAMILY_ORDER, rotation=0)
    ax2.set_xlabel("")
    ax2.set_ylabel("")
    ax2.tick_params(axis="both", length=0)
    for label in ax2.get_xticklabels():
        label.set_fontsize(12.0)
    for label in ax2.get_yticklabels():
        label.set_fontsize(12.2)
    fig2.subplots_adjust(bottom=0.13, left=0.15, right=0.94, top=0.985)
    fig2.text(
        0.50,
        0.035,
        "Cell: score; S=scoring scenarios, M=median steps; R/Ro/Sv/U/Tb/P = routes/roles/services/uploads/rendered tables/persistence.",
        ha="center",
        va="center",
        fontsize=9.8,
        color=COL["muted"],
    )
    save(
        fig2,
        APP_DIR / "appendix_benchmark_complexity_map_detailed",
        "targets/web/*/tier_*/contract.dsl.yaml + scenarios.*.dsl.yaml",
        "Appendix",
        "Detailed behavioral coupling map with routes, roles, services, uploads, rendered tables, and persistence indicators.",
    )


def figure_step_distribution(inv: pd.DataFrame) -> None:
    rows = []
    for r in inv.itertuples(index=False):
        lengths, _ = scenario_lengths_for(r.suite, str(r.tier))
        for length in lengths:
            rows.append({"family": r.family, "tier": str(r.tier), "steps": length})
    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    sns.boxplot(data=df, x="tier", y="steps", hue="family", order=TIER_ORDER, hue_order=FAMILY_ORDER, ax=ax, fliersize=1.5, linewidth=0.8, palette="tab10")
    ax.set_xticks(range(len(TIER_ORDER)))
    ax.set_xticklabels([f"Tier {t}\n{TIER_NAME[t]}" for t in TIER_ORDER])
    ax.set_xlabel("")
    ax.set_ylabel("Steps per scoring scenario")
    ax.grid(axis="y", color=COL["grid"], lw=0.8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=False)
    fig.subplots_adjust(bottom=0.28)
    save(
        fig,
        APP_DIR / "appendix_scenario_step_distribution",
        "targets/web/*/tier_*/scenarios.*.dsl.yaml",
        "Appendix",
        "Workflow length grows across the benchmark tiers, with variation by product family.",
    )


def figure_scenario_split(inv: pd.DataFrame) -> None:
    df = inv.copy()
    df["instance"] = df["family"].astype(str).map(lambda x: x.split()[0]) + " " + df["tier"].astype(str)
    x = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    public = df["num_public_scenarios"].to_numpy()
    private = df["num_private_scenarios"].to_numpy()
    probe = df["num_probe_scenarios"].to_numpy()
    ax.bar(x, public, color=COL["blue"], label="Public examples")
    ax.bar(x, private, bottom=public, color=COL["orange"], label="Held-out scoring")
    if probe.sum() > 0:
        ax.bar(x, probe, bottom=public + private, color=COL["gray"], label="Probe / diagnostic")
    ax.set_xticks(x)
    ax.set_xticklabels(df["instance"], rotation=50, ha="right", fontsize=7.5)
    ax.set_ylabel("Scenario count")
    ax.grid(axis="y", color=COL["grid"], lw=0.8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.34), ncol=3 if probe.sum() > 0 else 2, frameon=False)
    fig.subplots_adjust(bottom=0.44)
    save(
        fig,
        APP_DIR / "appendix_scenario_split",
        "targets/web/*/tier_*/scenarios.*.dsl.yaml",
        "Appendix",
        "Scenario inventory separates disclosed examples from held-out scoring scenarios.",
    )


def figure_step_vs_scenario(raw_runs: pd.DataFrame) -> None:
    df = raw_runs[raw_runs["view_current_raw"] == True].copy()  # noqa: E712
    fig, ax = plt.subplots(figsize=(5.5, 4.4))
    for mt in MODEL_ORDER:
        sub = df[df.model_tier == mt]
        ax.scatter(
            sub["stepwise_ratio"] * 100,
            sub["formal_ratio"] * 100,
            s=14,
            alpha=0.35,
            color=MODEL_COLORS[mt],
            label=MODEL_NAME[mt],
            linewidth=0,
        )
    ax.plot([0, 100], [0, 100], color=COL["muted"], lw=1, ls="--")
    ax.add_patch(Rectangle((60, 0), 40, 35, facecolor=COL["lightblue"], edgecolor="none", alpha=0.38))
    ax.text(62, 32, "near-miss region", fontsize=8, color=COL["muted"])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.set_xlabel("Step-level progress")
    ax.set_ylabel("Scenario-level conformance")
    ax.grid(color=COL["grid"], lw=0.8)
    ax.legend(loc="lower right", frameon=False)
    save(
        fig,
        APP_DIR / "appendix_step_vs_scenario_scatter",
        "data/raw_runs.csv",
        "Appendix",
        "Near-miss region marks runs with at least 60% step-level progress but at most 35% scenario-level conformance.",
    )


def figure_failure_histogram(scen: pd.DataFrame) -> None:
    df = trace_scope_scenarios(scen)
    failed = df[df["scenario_passed"] == False].copy()  # noqa: E712
    failed["norm"] = (failed["first_failed_step"].fillna(failed["expected_step_count"]) / failed["expected_step_count"]).clip(0, 1)
    bins = [0, 0.1, 0.25, 0.5, 0.75, 1.0]
    labels = ["0-10%", "10-25%", "25-50%", "50-75%", "75-100%"]
    failed["bin"] = pd.cut(failed["norm"], bins=bins, labels=labels, include_lowest=True)
    tab = failed.groupby(["bin", "model_tier"], observed=True).size().unstack(fill_value=0).reindex(labels)
    fig, ax = plt.subplots(figsize=(5.8, 3.2))
    bottom = np.zeros(len(tab))
    for mt in MODEL_ORDER:
        vals = tab.get(mt, pd.Series(0, index=tab.index)).to_numpy()
        ax.bar(np.arange(len(tab)), vals, bottom=bottom, color=MODEL_COLORS[mt], label=MODEL_NAME[mt])
        bottom += vals
    ax.set_xticks(range(len(tab)))
    ax.set_xticklabels(labels)
    ax.set_xlabel("Normalized first-failure position")
    ax.set_ylabel("Failed scenarios")
    ax.grid(axis="y", color=COL["grid"], lw=0.8)
    ax.legend(loc="upper right", frameon=False)
    save(
        fig,
        APP_DIR / "appendix_first_failure_position_histogram",
        "data/raw_scenarios.csv",
        "Appendix",
        "First-failure positions show immediate failures and later workflow drift.",
    )


def figure_relation_breakdown(scen: pd.DataFrame) -> None:
    df = trace_scope_scenarios(scen)
    failed = df[df["scenario_passed"] == False].copy()  # noqa: E712
    counts = failed["first_failure_raw"].fillna("unknown").map(relation_group).value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    colors = [FAILURE_COLORS.get(normalize_failure(x), COL["blue"]) for x in counts.index]
    ax.barh(counts.index, counts.values, color=colors)
    ax.set_xlabel("First failed scenarios")
    ax.grid(axis="x", color=COL["grid"], lw=0.8)
    save(
        fig,
        APP_DIR / "appendix_relation_failure_breakdown",
        "data/raw_scenarios.csv",
        "Appendix",
        "First failed relation types identify which behavioral checks break most often.",
    )


def figure_reference_vs_generated(tier: pd.DataFrame, inv: pd.DataFrame) -> None:
    df = tier.copy().sort_values(["family", "tier"])
    fig, axes = plt.subplots(2, 3, figsize=(8.8, 4.6), sharey=True, gridspec_kw={"hspace": 0.42, "wspace": 0.18})
    axes = axes.ravel()
    for ax, fam in zip(axes, FAMILY_ORDER):
        sub = df[df["family"].astype(str) == fam].set_index("tier").reindex(TIER_ORDER)
        x = np.arange(len(TIER_ORDER))
        ax.hlines(100, -0.4, 3.4, color=COL["green"], lw=1.6)
        ax.scatter(x, sub["formal_mean"] * 100, s=34, color=COL["scenario"], zorder=3)
        ax.set_title(fam, loc="left", fontsize=8.5, fontweight="bold")
        ax.set_ylim(0, 105)
        ax.set_xlim(-0.4, 3.4)
        ax.set_xticks(x)
        ax.set_xticklabels(TIER_ORDER)
        ax.grid(axis="y", color=COL["grid"], lw=0.8)
        ax.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    for ax in axes[::3]:
        ax.set_ylabel("Scenario-level")
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COL["scenario"], markersize=6, label="Generated mean"),
        Line2D([0], [0], color=COL["green"], lw=1.8, label="Reference implementation"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=2, frameon=False)
    fig.subplots_adjust(bottom=0.16)
    save(
        fig,
        APP_DIR / "appendix_reference_vs_generated",
        "data/report_tier_rollups.csv",
        "Appendix",
        "Family-faceted reference control: validated references pass scoring tests while generated implementation means remain lower.",
    )
    ref = df.merge(inv[["suite", "tier", "num_scoring_scenarios"]], on=["suite", "tier"], how="left")
    tab = ref[
        ["suite", "family", "tier", "num_scoring_scenarios", "formal_mean", "full_pass_rate", "full_pass", "full_total"]
    ].copy()
    tab["reference_pass_rate"] = 1.0
    tab = tab.rename(
        columns={
            "formal_mean": "generated_mean_scenario_score",
            "full_pass_rate": "generated_full_pass_rate",
        }
    )
    tex = tab.to_latex(index=False, float_format=lambda x: f"{x:.3f}")
    (TABLE_DIR / "appendix_reference_validation.tex").write_text(tex)


def make_inventory_tables(inv: pd.DataFrame) -> None:
    cols = [
        "instance_id",
        "family",
        "tier",
        "contract_tokens",
        "num_selectors",
        "num_actions",
        "num_state_paths",
        "num_routes",
        "num_roles",
        "num_service_fixtures",
        "num_upload_specs",
        "num_rendered_tables",
        "has_persistence",
        "has_browser_history",
        "num_scoring_scenarios",
        "num_probe_scenarios",
        "median_steps_per_scenario",
        "p90_steps_per_scenario",
        "behavioral_coupling_score",
    ]
    out = inv[cols].copy()
    out.to_csv(TABLE_DIR / "appendix_benchmark_inventory.csv", index=False)
    (TABLE_DIR / "appendix_benchmark_inventory.tex").write_text(out.to_latex(index=False, float_format=lambda x: f"{x:.1f}"))


def make_excluded_runs_table(tier: pd.DataFrame) -> None:
    rows = []
    pe_path = DATA_DIR / "parse_errors.csv"
    if pe_path.exists() and pe_path.stat().st_size > 1:
        pe = pd.read_csv(pe_path)
        pe["family"] = pe["suite"].map(family_from_suite)
        grp = pe.groupby(["error_type", "family", "tier", "model_tier"], observed=True).size().reset_index(name="count")
        for r in grp.itertuples(index=False):
            rows.append(
                {
                    "reason": r.error_type,
                    "count": r.count,
                    "affected_family": r.family,
                    "affected_tier": r.tier,
                    "affected_model_group": MODEL_NAME.get(r.model_tier, r.model_tier),
                    "included_in_denominator": "no",
                }
            )
    # Surface aggregate rows with fewer than 90 reported runs.
    for r in tier.itertuples(index=False):
        if int(r.runs) < 90:
            rows.append(
                {
                    "reason": "missing reported generation",
                    "count": int(90 - r.runs),
                    "affected_family": r.family,
                    "affected_tier": r.tier,
                    "affected_model_group": "all",
                    "included_in_denominator": "no",
                }
            )
    ex = pd.DataFrame(rows)
    if ex.empty:
        ex = pd.DataFrame(columns=["reason", "count", "affected_family", "affected_tier", "affected_model_group", "included_in_denominator"])
    ex.to_csv(TABLE_DIR / "appendix_excluded_runs.csv", index=False)
    (TABLE_DIR / "appendix_excluded_runs.tex").write_text(ex.to_latex(index=False))


def make_review_sheet() -> None:
    items = [
        ("Benchmark complexity", MAIN_DIR / "figure_benchmark_complexity_map.png"),
        ("Conformance gap", MAIN_DIR / "figure_conformance_gap.png"),
        ("Model capability", MOA_DIR / "figure_model_capability.png"),
        ("Complexity heatmap", MOA_DIR / "figure_complexity_ladder_heatmap.png"),
        ("Failure taxonomy", MAIN_DIR / "figure_failure_taxonomy.png"),
        ("Survival curve", MOA_DIR / "figure_long_horizon_survival.png"),
        ("Instance heatmap", APP_DIR / "appendix_instance_heatmap.png"),
        ("Feature associations", APP_DIR / "appendix_contract_feature_difficulty.png"),
        ("Generation variance", APP_DIR / "appendix_generation_variance.png"),
        ("Step vs scenario", APP_DIR / "appendix_step_vs_scenario_scatter.png"),
        ("Failure histogram", APP_DIR / "appendix_first_failure_position_histogram.png"),
        ("Relation failures", APP_DIR / "appendix_relation_failure_breakdown.png"),
        ("Reference control", APP_DIR / "appendix_reference_vs_generated.png"),
        ("Representative screenshots", REVIEW_DIR / "representative_tier_screenshots_sheet.png"),
        ("Evidence by tier", REVIEW_DIR / "failure_evidence_by_tier_sheet.png"),
    ]
    cell_w, cell_h = 420, 310
    cols = 3
    rows = math.ceil(len(items) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, path) in enumerate(items):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        draw.text((x + 16, y + 10), label, fill=COL["ink"])
        if path.exists():
            im = Image.open(path).convert("RGB")
            im.thumbnail((cell_w - 32, cell_h - 48), Image.LANCZOS)
            sheet.paste(im, (x + (cell_w - im.width) // 2, y + 42))
        else:
            draw.rectangle([x + 16, y + 42, x + cell_w - 16, y + cell_h - 16], outline="#DADCE0")
            draw.text((x + 32, y + 150), "missing", fill=COL["muted"])
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_DIR / "figure_review_sheet.png", dpi=(220, 220))


def write_readme() -> None:
    lines = [
        "# ConformWeb Figure Pack",
        "",
        "All figures were generated by `tools/build_conformweb_figure_pack.py`.",
        "",
        "| Figure | Source data | Script | Intended location | Message |",
        "|---|---|---|---|---|",
    ]
    for r in README_ROWS:
        lines.append(f"| `{r['filename']}` | `{r['source_data']}` | `{r['script']}` | {r['location']} | {r['message']} |")
    lines.extend(
        [
            "",
            "## Caption Notes",
            "",
            "- `figure_difficulty_scaling_curve`: A=Consumer, B=Operational, C=Regulated, D=Release-stage.",
            "- `figure_benchmark_complexity_map`: the coupling score is a relative 10-100 index computed from contract and scenario features; it is not an objective difficulty ground truth.",
            "- `figure_model_capability`: small points are family-tier instances; large points are run-weighted model-group means with intervals.",
            "- `figure_long_horizon_survival`: passed scenarios are counted as surviving through 100% normalized progress.",
            "- `appendix_step_vs_scenario_scatter`: the shaded near-miss region marks runs with step-level progress >=60% and scenario-level conformance <=35%.",
            "- `figure_failure_taxonomy`: in the current normalized first-failure data, no cases are assigned to `Async failure` or `Long-horizon drift`; those labels are reserved and omitted from the legend when absent.",
            "",
            "## Editable Screenshot Packs",
            "",
            "| Pack | Path | Source | Message |",
            "|---|---|---|---|",
            "| Representative target-tier screenshots | `figures/appendix/representative_screenshots/` | `evidence/representative_screenshots/*.pdf` | One standalone PNG per product family and Tier A-D target for manual figure editing. |",
            "| Failure evidence by target tier | `figures/appendix/failure_evidence_by_tier/` | `evidence/failure_pairs/current_raw/*.pdf` | Before, after, and before/after PNG panels for selected target-tier failures. |",
            "| Representative screenshot contact sheet | `figures/review/representative_tier_screenshots_sheet.png` | exported representative PNGs | Quick visual scan of all 24 family-tier screenshots. |",
            "| Failure evidence contact sheet | `figures/review/failure_evidence_by_tier_sheet.png` | exported failure evidence PNGs | Quick visual scan of selected target-tier failure examples. |",
            "",
            "## Failure Taxonomy Labels",
            "",
            "| Short label | Full definition |",
            "|---|---|",
            "| Missing surface | Missing interaction surface |",
            "| Invalid observation | Invalid observation surface |",
            "| Unavailable control | Unavailable control |",
            "| Wrong transition | Wrong state transition |",
            "| Route / persistence drift | Route or persistence drift |",
            "| Projection mismatch | Rendered-projection mismatch |",
            "| Async failure | Asynchronous completion failure |",
            "| Long-horizon drift | Long-horizon drift |",
        ]
    )
    (FIG_DIR / "README.md").write_text("\n".join(lines) + "\n")


def write_validation(tier: pd.DataFrame, model_tier: pd.DataFrame, raw_runs: pd.DataFrame, raw_scen: pd.DataFrame) -> None:
    fam = report_family_summary(tier)
    total = fam.iloc[0]
    lines = [
        "# Validation Report",
        "",
        "## Latest Aggregate Scope",
        "",
        f"- Generated implementations: {int(total.runs):,}",
        f"- Full-pass implementations: {int(total.full_pass):,}/{int(total.full_total):,}",
        f"- Overall full-pass rate: {100 * total.full_pass_rate:.1f}%",
        f"- Scenario-level conformance: {100 * total.formal_mean:.1f}%",
        f"- Step-level progress: {100 * total.stepwise_mean:.1f}%",
        "",
        "## Family-Level Counts",
        "",
        "| Family | Runs | Full pass | Full-pass rate | Scenario-level | Step-level |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in fam.iloc[1:].itertuples(index=False):
        lines.append(
            f"| {r.family} | {int(r.runs):,} | {fmt_count(r.full_pass, r.full_total)} | {100*r.full_pass_rate:.1f}% | {100*r.formal_mean:.1f}% | {100*r.stepwise_mean:.1f}% |"
        )
    grp = model_tier.groupby("model_tier", observed=True).agg(runs=("runs", "sum"), full_pass=("full_pass", "sum"), full_total=("full_total", "sum"))
    lines.extend(["", "## Model-Group Counts", "", "| Group | Runs | Full pass | Full-pass rate |", "|---|---:|---:|---:|"])
    for mt in MODEL_ORDER:
        r = grp.loc[mt]
        lines.append(f"| {MODEL_NAME[mt]} ({mt}) | {int(r.runs):,} | {fmt_count(r.full_pass, r.full_total)} | {100*r.full_pass/r.full_total:.1f}% |")
    expected = set(FAMILY_ORDER)
    present = set(tier["family"].astype(str))
    raw_present = set(raw_runs[raw_runs.view_current_raw == True]["family"].astype(str))  # noqa: E712
    raw_scen_present = set(raw_scen[raw_scen.view_current_raw == True]["family"].astype(str))  # noqa: E712
    lines.extend(
        [
            "",
            "## Family Coverage Checks",
            "",
            f"- Aggregate report families present: {', '.join(sorted(present))}",
            f"- Required six families covered by aggregate figures: {'yes' if expected <= present else 'no'}",
            f"- Raw run trace families present: {', '.join(sorted(raw_present))}",
            f"- Raw scenario trace families present: {', '.join(sorted(raw_scen_present))}",
            "",
            "Trace-level diagnostics (failure taxonomy, survival, scatter, histograms, relation failures, screenshot evidence) use the current raw trace artifacts available locally. Aggregate score figures use the latest 2,157-run reported rollups.",
        ]
    )
    (OUT_ROOT / "validation_report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_dirs()
    setup_style()
    tier, model_tier, per_model = load_report()
    raw_runs, raw_scen, raw_steps = load_raw()
    inv = build_inventory(tier)

    figure_conformance_gap(tier)
    figure_conformance_gap(tier, square=True)
    figure_model_capability(model_tier)
    figure_complexity_heatmap(tier)
    figure_difficulty_scaling(model_tier)
    figure_failure_taxonomy(raw_scen, raw_steps)
    figure_survival(raw_scen)
    figure_instance_heatmap(model_tier)
    figure_contract_feature(inv, model_tier)
    figure_generation_variance(raw_runs)
    figure_complexity_map(inv)
    figure_step_distribution(inv)
    figure_scenario_split(inv)
    make_inventory_tables(inv)
    figure_step_vs_scenario(raw_runs)
    figure_failure_histogram(raw_scen)
    figure_relation_breakdown(raw_scen)
    figure_reference_vs_generated(tier, inv)
    make_excluded_runs_table(tier)
    make_review_sheet()
    write_validation(tier, model_tier, raw_runs, raw_scen)
    write_readme()


if __name__ == "__main__":
    main()
