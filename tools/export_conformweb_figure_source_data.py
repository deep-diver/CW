#!/usr/bin/env python3
"""Export source data for selected ConformWeb paper figures.

The output is a single tidy CSV containing the values needed to redraw:
- figure_conformance_gap_only
- figure_model_capability
- figure_difficulty_scaling_curve
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


figpack = load_module("conformweb_figpack_source_data", ROOT / "tools" / "build_conformweb_figure_pack.py")

OUT_ROOT = ROOT / "reports" / "conformweb_visualizations"
TABLE_DIR = OUT_ROOT / "tables"
OUT_CSV = TABLE_DIR / "figure_source_data_conformance_model_difficulty.csv"

METRIC_LABEL = {
    "full_pass_rate": "Full pass",
    "formal_mean": "Scenario-level conformance",
    "stepwise_mean": "Step-level progress",
}
METRIC_ORDER = {
    "full_pass_rate": 1,
    "formal_mean": 2,
    "stepwise_mean": 3,
}
MODEL_ORDER_IDX = {m: i for i, m in enumerate(figpack.MODEL_ORDER)}
TIER_ORDER_IDX = {t: i for i, t in enumerate(figpack.TIER_ORDER)}
MODEL_ID_ORDER = list(figpack.base.MODEL_ORDER)
MODEL_ID_ORDER_IDX = {m: i for i, m in enumerate(MODEL_ID_ORDER)}


def pct(value: float | int | None) -> float:
    if value is None or pd.isna(value):
        return np.nan
    return float(value) * 100.0


def count_label(full_pass: float | int | None, denominator: float | int | None) -> str:
    if full_pass is None or denominator is None or pd.isna(full_pass) or pd.isna(denominator):
        return ""
    rate = float(full_pass) / float(denominator) * 100.0 if float(denominator) else np.nan
    return f"{int(round(full_pass)):,}/{int(round(denominator)):,} ({rate:.1f}%)"


def row(**kwargs) -> dict:
    base = {
        "source_figure": "",
        "source_panel": "",
        "source_file": "",
        "grain": "",
        "plot_role": "",
        "row_order": np.nan,
        "metric_order": np.nan,
        "metric": "",
        "metric_label": "",
        "value": np.nan,
        "value_pct": np.nan,
        "ci95_low_pct": np.nan,
        "ci95_high_pct": np.nan,
        "ci95_halfwidth_pct": np.nan,
        "full_pass": np.nan,
        "denominator": np.nan,
        "count_label": "",
        "n_points": np.nan,
        "runs": np.nan,
        "suite": "",
        "suite_label": "",
        "family": "",
        "family_label": "",
        "tier": "",
        "tier_label": "",
        "model_tier": "",
        "model_group": "",
        "model": "",
        "model_label": "",
        "model_order": np.nan,
        "input_source": "",
        "denominator_policy": "",
        "data_scope": "",
        "notes": "",
    }
    base.update(kwargs)
    return base


def export_conformance_gap(tier: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    summary = figpack.report_family_summary(tier, missing_as_failed=True)
    row_labels = {
        "Clinical Command": "Clinical Cmd.",
        "Campus Registrar": "Campus Reg.",
        "Media Campaign": "Media Camp.",
    }
    for row_idx, rec in summary.reset_index(drop=True).iterrows():
        family = str(rec["family"])
        family_label = row_labels.get(family, family)
        for metric in ["full_pass_rate", "formal_mean", "stepwise_mean"]:
            full_pass = rec["full_pass"] if metric == "full_pass_rate" else np.nan
            denom = rec["full_total"] if metric == "full_pass_rate" else rec["runs"]
            rows.append(
                row(
                    source_figure="figure_conformance_gap_only",
                    source_panel="family conformance gap",
                    source_file="figures/main/figure_conformance_gap_only.pdf",
                    grain="overall_or_family",
                    plot_role="dot" if metric != "stepwise_mean" else "dot_and_gap_endpoint",
                    row_order=row_idx,
                    metric_order=METRIC_ORDER[metric],
                    metric=metric,
                    metric_label=METRIC_LABEL[metric],
                    value=float(rec[metric]),
                    value_pct=pct(rec[metric]),
                    full_pass=full_pass,
                    denominator=denom,
                    count_label=count_label(full_pass, denom) if metric == "full_pass_rate" else "",
                    runs=rec["runs"],
                    family="" if family == "Overall" else family,
                    family_label=family_label,
                    denominator_policy="planned denominator; missing planned runs counted as failures",
                    notes="Scenario and step metrics are run-weighted. Full pass uses planned denominators.",
                )
            )
    return rows


def model_tier_with_denominators(model_tier: pd.DataFrame) -> pd.DataFrame:
    df = model_tier.copy()
    expected_per_instance_group = 30.0
    df["_denom"] = df["full_total"].clip(lower=expected_per_instance_group)
    df["_formal_num"] = df["formal_mean"] * df["full_total"]
    df["_step_num"] = df["stepwise_mean"] * df["full_total"]
    df["model_group"] = df["model_tier"].map(figpack.MODEL_NAME)
    return df


def load_available_per_model_rollups(per_model_report: pd.DataFrame) -> pd.DataFrame:
    """Combine every per-model rollup available locally.

    The all-family aggregate rollups are model-group level. Per-model data are
    locally available from two sources: current raw run traces for the older
    trace-backed families, and explicit per-model report rows for Campus/Media.
    This function combines both while preserving the input source.
    """

    pieces: list[pd.DataFrame] = []
    raw_path = figpack.DATA_DIR / "raw_runs.csv"
    if raw_path.exists():
        raw = pd.read_csv(raw_path)
        if "view_current_raw" in raw.columns:
            raw = raw[raw["view_current_raw"] == True].copy()  # noqa: E712
        if not raw.empty:
            grouped = (
                raw.groupby(
                    ["suite", "suite_label", "tier", "model", "model_label", "model_tier", "model_tier_label"],
                    observed=True,
                    dropna=False,
                )
                .agg(
                    runs=("passed", "size"),
                    formal_mean=("formal_ratio", "mean"),
                    stepwise_mean=("stepwise_ratio", "mean"),
                    full_pass=("passed", "sum"),
                    full_total=("passed", "size"),
                )
                .reset_index()
            )
            grouped["full_pass_rate"] = grouped["full_pass"] / grouped["full_total"]
            grouped["report_view"] = "raw_current"
            grouped["source"] = "raw_runs.csv"
            pieces.append(grouped)

    if not per_model_report.empty:
        reported = per_model_report.copy()
        reported["source"] = reported.get("source", "report_per_model_rollups.csv")
        pieces.append(reported)

    if not pieces:
        return per_model_report

    combined = pd.concat(pieces, ignore_index=True, sort=False)
    combined["model_label"] = combined["model"].map(figpack.base.MODEL_LABELS).fillna(combined["model_label"])
    combined["model_tier"] = combined["model"].map(figpack.base.MODEL_TO_TIER).fillna(combined["model_tier"])
    combined["model_tier_label"] = combined["model_tier"].map({"M": "Mini", "T": "Turbo", "F": "Frontier"}).fillna(combined["model_tier_label"])
    combined = figpack.add_family_cols(combined)

    # If an explicit report row and a raw-derived row ever overlap, prefer the
    # explicit report row because it is the scope used in the paper report.
    combined["_source_priority"] = np.where(combined["source"].eq("raw_runs.csv"), 0, 1)
    combined = combined.sort_values(["suite", "tier", "model", "_source_priority"])
    combined = combined.drop_duplicates(["suite", "tier", "model"], keep="last")
    return combined.drop(columns=["_source_priority"])


def export_model_capability(model_tier: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    df = model_tier_with_denominators(model_tier)

    # Panel A: small points, one point per family-tier-model group.
    for _, rec in df.iterrows():
        for metric in ["formal_mean", "stepwise_mean"]:
            rows.append(
                row(
                    source_figure="figure_model_capability",
                    source_panel="progress by capability",
                    source_file="figures/main_or_appendix/figure_model_capability.pdf",
                    grain="family_tier_model_group",
                    plot_role="small_point",
                    row_order=MODEL_ORDER_IDX[str(rec["model_tier"])],
                    metric_order=METRIC_ORDER[metric],
                    metric=metric,
                    metric_label=METRIC_LABEL[metric],
                    value=float(rec[metric]),
                    value_pct=pct(rec[metric]),
                    denominator=rec["_denom"],
                    runs=rec["runs"],
                    suite=rec["suite"],
                    suite_label=rec["suite_label"],
                    family=str(rec["family"]),
                    family_label=str(rec["family"]),
                    tier=rec["tier"],
                    tier_label=f"Tier {rec['tier']} {figpack.TIER_NAME[str(rec['tier'])]}",
                    model_tier=rec["model_tier"],
                    model_group=figpack.MODEL_NAME[str(rec["model_tier"])],
                    model=rec.get("model", ""),
                    model_label=rec.get("model_label", ""),
                    model_order=MODEL_ID_ORDER_IDX.get(str(rec.get("model", "")), np.nan),
                    denominator_policy="planned denominator per family-tier-model group is at least 30",
                    data_scope="all latest family-tier model-group rollups",
                )
            )

    # Panel A: large run-weighted model-group means with the same interval logic as the figure.
    for mt in figpack.MODEL_ORDER:
        sub = df[df.model_tier == mt]
        for metric, numerator in [("formal_mean", "_formal_num"), ("stepwise_mean", "_step_num")]:
            vals = sub[metric].dropna().to_numpy() * 100
            mean_pct = 100.0 * sub[numerator].sum() / sub["_denom"].sum()
            se = vals.std(ddof=1) / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
            half = 1.96 * se
            rows.append(
                row(
                    source_figure="figure_model_capability",
                    source_panel="progress by capability",
                    source_file="figures/main_or_appendix/figure_model_capability.pdf",
                    grain="model_group",
                    plot_role="large_point_with_ci",
                    row_order=MODEL_ORDER_IDX[mt],
                    metric_order=METRIC_ORDER[metric],
                    metric=metric,
                    metric_label=METRIC_LABEL[metric],
                    value=mean_pct / 100.0,
                    value_pct=mean_pct,
                    ci95_low_pct=max(mean_pct - half, 0.0),
                    ci95_high_pct=min(mean_pct + half, 100.0),
                    ci95_halfwidth_pct=half,
                    denominator=sub["_denom"].sum(),
                    n_points=len(vals),
                    runs=sub["runs"].sum(),
                    model_tier=mt,
                    model_group=figpack.MODEL_NAME[mt],
                    data_scope="all latest family-tier model-group rollups",
                    denominator_policy="run-weighted mean; intervals computed over family-tier points",
                )
            )

    # Panel B: full-pass bar by capability.
    grp = (
        df.groupby("model_tier", observed=True)
        .agg(full_pass=("full_pass", "sum"), denominator=("_denom", "sum"), runs=("runs", "sum"))
        .reindex(figpack.MODEL_ORDER)
    )
    for mt, rec in grp.iterrows():
        value = float(rec["full_pass"] / rec["denominator"])
        rows.append(
            row(
                source_figure="figure_model_capability",
                source_panel="full pass by capability",
                source_file="figures/main_or_appendix/figure_model_capability.pdf",
                grain="model_group",
                plot_role="bar",
                row_order=MODEL_ORDER_IDX[mt],
                metric_order=METRIC_ORDER["full_pass_rate"],
                metric="full_pass_rate",
                metric_label=METRIC_LABEL["full_pass_rate"],
                value=value,
                value_pct=pct(value),
                full_pass=rec["full_pass"],
                denominator=rec["denominator"],
                count_label=count_label(rec["full_pass"], rec["denominator"]),
                runs=rec["runs"],
                model_tier=mt,
                model_group=figpack.MODEL_NAME[mt],
                data_scope="all latest family-tier model-group rollups",
                denominator_policy="planned denominator per family-tier-model group is at least 30",
            )
        )

    return rows


def per_model_with_denominators(per_model: pd.DataFrame) -> pd.DataFrame:
    df = per_model.copy()
    expected_per_instance_model = 10.0
    df["_denom"] = df["full_total"].clip(lower=expected_per_instance_model)
    df["_formal_num"] = df["formal_mean"] * df["full_total"]
    df["_step_num"] = df["stepwise_mean"] * df["full_total"]
    df["model_group"] = df["model_tier"].map(figpack.MODEL_NAME)
    df["model_order"] = df["model"].map(MODEL_ID_ORDER_IDX)
    return df


def export_conformance_gap_by_model(per_model: pd.DataFrame) -> list[dict]:
    """Per-model version of the conformance-gap table.

    This adds rows from the per-model rollup file. The available per-model
    rollup scope is recorded in data_scope because it is currently narrower
    than the model-tier aggregate table.
    """

    rows: list[dict] = []
    df = per_model_with_denominators(per_model)
    if df.empty:
        return rows

    def add_model_summary(sub: pd.DataFrame, model_rec: pd.Series, family: str, family_label: str, row_order: int) -> None:
        denom = sub["_denom"].sum()
        if denom <= 0:
            return
        values = {
            "full_pass_rate": float(sub["full_pass"].sum() / denom),
            "formal_mean": float(sub["_formal_num"].sum() / denom),
            "stepwise_mean": float(sub["_step_num"].sum() / denom),
        }
        for metric in ["full_pass_rate", "formal_mean", "stepwise_mean"]:
            full_pass = sub["full_pass"].sum() if metric == "full_pass_rate" else np.nan
            metric_denom = denom if metric == "full_pass_rate" else sub["runs"].sum()
            rows.append(
                row(
                    source_figure="figure_conformance_gap_only",
                    source_panel="family conformance gap",
                    source_file="figures/main/figure_conformance_gap_only.pdf",
                    grain="overall_or_family_model",
                    plot_role="model_specific_table_value",
                    row_order=row_order,
                    metric_order=METRIC_ORDER[metric],
                    metric=metric,
                    metric_label=METRIC_LABEL[metric],
                    value=values[metric],
                    value_pct=pct(values[metric]),
                    full_pass=full_pass,
                    denominator=metric_denom,
                    count_label=count_label(full_pass, metric_denom) if metric == "full_pass_rate" else "",
                    runs=sub["runs"].sum(),
                    family="" if family == "Overall" else family,
                    family_label=family_label,
                    model_tier=model_rec["model_tier"],
                    model_group=figpack.MODEL_NAME[str(model_rec["model_tier"])],
                    model=model_rec["model"],
                    model_label=model_rec["model_label"],
                    model_order=MODEL_ID_ORDER_IDX.get(str(model_rec["model"]), np.nan),
                    denominator_policy="planned denominator per family-tier-model is at least 10",
                    input_source=", ".join(sorted(map(str, sub["source"].dropna().unique()))),
                    data_scope="available per-model rollups from raw traces and explicit per-model reports",
                    notes="Per-model rollup file is narrower than the all-family model-tier aggregate; use data_scope before comparing totals.",
                )
            )

    for model_id in MODEL_ID_ORDER:
        sub_model = df[df["model"] == model_id]
        if sub_model.empty:
            continue
        model_rec = sub_model.iloc[0]
        add_model_summary(sub_model, model_rec, "Overall", "Overall", 0)
        for idx, fam in enumerate(figpack.FAMILY_ORDER, start=1):
            sub_fam = sub_model[sub_model["family"] == fam]
            if sub_fam.empty:
                continue
            add_model_summary(sub_fam, model_rec, fam, fam, idx)
    return rows


def export_model_capability_by_model(per_model: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    df = per_model_with_denominators(per_model)
    if df.empty:
        return rows

    # Per-family-tier small points for individual models.
    for _, rec in df.iterrows():
        for metric in ["formal_mean", "stepwise_mean"]:
            rows.append(
                row(
                    source_figure="figure_model_capability",
                    source_panel="progress by capability",
                    source_file="figures/main_or_appendix/figure_model_capability.pdf",
                    grain="family_tier_model",
                    plot_role="small_point",
                    row_order=MODEL_ID_ORDER_IDX.get(str(rec["model"]), np.nan),
                    metric_order=METRIC_ORDER[metric],
                    metric=metric,
                    metric_label=METRIC_LABEL[metric],
                    value=float(rec[metric]),
                    value_pct=pct(rec[metric]),
                    denominator=rec["_denom"],
                    runs=rec["runs"],
                    suite=rec["suite"],
                    suite_label=rec["suite_label"],
                    family=str(rec["family"]),
                    family_label=str(rec["family"]),
                    tier=rec["tier"],
                    tier_label=f"Tier {rec['tier']} {figpack.TIER_NAME[str(rec['tier'])]}",
                    model_tier=rec["model_tier"],
                    model_group=figpack.MODEL_NAME[str(rec["model_tier"])],
                    model=rec["model"],
                    model_label=rec["model_label"],
                    model_order=MODEL_ID_ORDER_IDX.get(str(rec["model"]), np.nan),
                    denominator_policy="planned denominator per family-tier-model is at least 10",
                    input_source=str(rec.get("source", "")),
                    data_scope="available per-model rollups from raw traces and explicit per-model reports",
                )
            )

    # Per-model aggregate points and full-pass bars.
    for model_id in MODEL_ID_ORDER:
        sub = df[df["model"] == model_id]
        if sub.empty:
            continue
        model_rec = sub.iloc[0]
        for metric, numerator in [("formal_mean", "_formal_num"), ("stepwise_mean", "_step_num")]:
            vals = sub[metric].dropna().to_numpy() * 100
            mean_pct = 100.0 * sub[numerator].sum() / sub["_denom"].sum()
            se = vals.std(ddof=1) / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
            half = 1.96 * se
            rows.append(
                row(
                    source_figure="figure_model_capability",
                    source_panel="progress by capability",
                    source_file="figures/main_or_appendix/figure_model_capability.pdf",
                    grain="model",
                    plot_role="large_point_with_ci",
                    row_order=MODEL_ID_ORDER_IDX[model_id],
                    metric_order=METRIC_ORDER[metric],
                    metric=metric,
                    metric_label=METRIC_LABEL[metric],
                    value=mean_pct / 100.0,
                    value_pct=mean_pct,
                    ci95_low_pct=max(mean_pct - half, 0.0),
                    ci95_high_pct=min(mean_pct + half, 100.0),
                    ci95_halfwidth_pct=half,
                    denominator=sub["_denom"].sum(),
                    n_points=len(vals),
                    runs=sub["runs"].sum(),
                    model_tier=model_rec["model_tier"],
                    model_group=figpack.MODEL_NAME[str(model_rec["model_tier"])],
                    model=model_id,
                    model_label=model_rec["model_label"],
                    model_order=MODEL_ID_ORDER_IDX[model_id],
                    denominator_policy="run-weighted mean over available per-model family-tier points",
                    input_source=", ".join(sorted(map(str, sub["source"].dropna().unique()))),
                    data_scope="available per-model rollups from raw traces and explicit per-model reports",
                )
            )

        full_pass = sub["full_pass"].sum()
        denom = sub["_denom"].sum()
        value = float(full_pass / denom)
        rows.append(
            row(
                source_figure="figure_model_capability",
                source_panel="full pass by capability",
                source_file="figures/main_or_appendix/figure_model_capability.pdf",
                grain="model",
                plot_role="bar",
                row_order=MODEL_ID_ORDER_IDX[model_id],
                metric_order=METRIC_ORDER["full_pass_rate"],
                metric="full_pass_rate",
                metric_label=METRIC_LABEL["full_pass_rate"],
                value=value,
                value_pct=pct(value),
                full_pass=full_pass,
                denominator=denom,
                count_label=count_label(full_pass, denom),
                runs=sub["runs"].sum(),
                model_tier=model_rec["model_tier"],
                model_group=figpack.MODEL_NAME[str(model_rec["model_tier"])],
                model=model_id,
                model_label=model_rec["model_label"],
                model_order=MODEL_ID_ORDER_IDX[model_id],
                denominator_policy="planned denominator per family-tier-model is at least 10",
                input_source=", ".join(sorted(map(str, sub["source"].dropna().unique()))),
                data_scope="available per-model rollups from raw traces and explicit per-model reports",
            )
        )
    return rows


def export_difficulty_scaling(model_tier: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    aggregates: list[dict] = []
    for (tier, mt), sub in model_tier.groupby(["tier", "model_tier"], observed=True):
        full_total = float(sub["full_total"].sum())
        aggregates.append(
            {
                "tier": tier,
                "model_tier": mt,
                "formal_mean": figpack.weighted_mean(sub, "formal_mean"),
                "stepwise_mean": figpack.weighted_mean(sub, "stepwise_mean"),
                "full_pass_rate": float(sub["full_pass"].sum() / full_total) if full_total > 0 else np.nan,
                "full_pass": float(sub["full_pass"].sum()),
                "full_total": full_total,
                "runs": float(sub["runs"].sum()),
                "n_points": int(len(sub)),
            }
        )
    df = pd.DataFrame(aggregates)
    for _, rec in df.iterrows():
        for panel, metric in [
            ("scenario-level by tier", "formal_mean"),
            ("step-level by tier", "stepwise_mean"),
            ("full-pass rate by tier", "full_pass_rate"),
        ]:
            full_pass = rec["full_pass"] if metric == "full_pass_rate" else np.nan
            denom = rec["full_total"] if metric == "full_pass_rate" else rec["runs"]
            rows.append(
                row(
                    source_figure="figure_difficulty_scaling_curve",
                    source_panel=panel,
                    source_file="figures/main_or_appendix/figure_difficulty_scaling_curve.pdf",
                    grain="tier_model_group",
                    plot_role="line_point",
                    row_order=TIER_ORDER_IDX[str(rec["tier"])],
                    metric_order=METRIC_ORDER[metric],
                    metric=metric,
                    metric_label=METRIC_LABEL[metric],
                    value=float(rec[metric]),
                    value_pct=pct(rec[metric]),
                    full_pass=full_pass,
                    denominator=denom,
                    count_label=count_label(full_pass, denom) if metric == "full_pass_rate" else "",
                    n_points=rec["n_points"],
                    runs=rec["runs"],
                    tier=rec["tier"],
                    tier_label=f"Tier {rec['tier']} {figpack.TIER_NAME[str(rec['tier'])]}",
                    model_tier=rec["model_tier"],
                    model_group=figpack.MODEL_NAME[str(rec["model_tier"])],
                    data_scope="all latest family-tier model-group rollups",
                    denominator_policy="observed run denominator, matching difficulty scaling curve",
                )
            )
    return rows


def export_difficulty_scaling_by_model(per_model: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    df = per_model_with_denominators(per_model)
    if df.empty:
        return rows

    aggregates: list[dict] = []
    for (tier, model), sub in df.groupby(["tier", "model"], observed=True):
        denom = float(sub["_denom"].sum())
        if denom <= 0:
            continue
        first = sub.iloc[0]
        aggregates.append(
            {
                "tier": tier,
                "model": model,
                "model_label": first["model_label"],
                "model_tier": first["model_tier"],
                "formal_mean": float(sub["_formal_num"].sum() / denom),
                "stepwise_mean": float(sub["_step_num"].sum() / denom),
                "full_pass_rate": float(sub["full_pass"].sum() / denom),
                "full_pass": float(sub["full_pass"].sum()),
                "full_total": denom,
                "runs": float(sub["runs"].sum()),
                "n_points": int(len(sub)),
            }
        )
    agg = pd.DataFrame(aggregates)
    for _, rec in agg.iterrows():
        for panel, metric in [
            ("scenario-level by tier", "formal_mean"),
            ("step-level by tier", "stepwise_mean"),
            ("full-pass rate by tier", "full_pass_rate"),
        ]:
            full_pass = rec["full_pass"] if metric == "full_pass_rate" else np.nan
            denom = rec["full_total"] if metric == "full_pass_rate" else rec["runs"]
            rows.append(
                row(
                    source_figure="figure_difficulty_scaling_curve",
                    source_panel=panel,
                    source_file="figures/main_or_appendix/figure_difficulty_scaling_curve.pdf",
                    grain="tier_model",
                    plot_role="line_point",
                    row_order=TIER_ORDER_IDX[str(rec["tier"])],
                    metric_order=METRIC_ORDER[metric],
                    metric=metric,
                    metric_label=METRIC_LABEL[metric],
                    value=float(rec[metric]),
                    value_pct=pct(rec[metric]),
                    full_pass=full_pass,
                    denominator=denom,
                    count_label=count_label(full_pass, denom) if metric == "full_pass_rate" else "",
                    n_points=rec["n_points"],
                    runs=rec["runs"],
                    tier=rec["tier"],
                    tier_label=f"Tier {rec['tier']} {figpack.TIER_NAME[str(rec['tier'])]}",
                    model_tier=rec["model_tier"],
                    model_group=figpack.MODEL_NAME[str(rec["model_tier"])],
                    model=rec["model"],
                    model_label=rec["model_label"],
                    model_order=MODEL_ID_ORDER_IDX.get(str(rec["model"]), np.nan),
                    denominator_policy="planned denominator per family-tier-model is at least 10",
                    input_source="aggregate of available per-model rollups",
                    data_scope="available per-model rollups from raw traces and explicit per-model reports",
                )
            )
    return rows


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    tier, model_tier, per_model_report = figpack.load_report()
    per_model = load_available_per_model_rollups(per_model_report)
    rows = []
    rows.extend(export_conformance_gap(tier))
    rows.extend(export_conformance_gap_by_model(per_model))
    rows.extend(export_model_capability(model_tier))
    rows.extend(export_model_capability_by_model(per_model))
    rows.extend(export_difficulty_scaling(model_tier))
    rows.extend(export_difficulty_scaling_by_model(per_model))
    out = pd.DataFrame(rows)
    out = out.sort_values(
        [
            "source_figure",
            "source_panel",
            "grain",
            "row_order",
            "model_tier",
            "tier",
            "family",
            "metric_order",
        ],
        kind="stable",
    )
    out.to_csv(OUT_CSV, index=False)
    print(OUT_CSV)
    print(f"rows={len(out)}")
    print(out.groupby(["source_figure", "source_panel", "grain"], dropna=False).size().to_string())


if __name__ == "__main__":
    main()
