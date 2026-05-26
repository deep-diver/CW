#!/usr/bin/env python3
"""Build main-paper model rollups and audit tables for ConformWeb.

This script deliberately refuses to infer per-model values from model-group
aggregates. It exports the available per-model rollup and a report that states
whether the complete 24-instance x 9-model grid is present locally.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from typing import Any

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


figpack = load_module("conformweb_figpack_main_table", ROOT / "tools" / "build_conformweb_figure_pack.py")

DATA_DIR = ROOT / "reports" / "conformweb_visualizations" / "data"
REPORT_DIR = ROOT / "reports" / "conformweb_visualizations"
ROOT_TABLE_DIR = ROOT / "tables"

MODEL_GROUPS = {
    "M": "Mini",
    "T": "Turbo",
    "F": "Frontier",
}
MODEL_ORDER = list(figpack.base.MODEL_ORDER)
MODEL_LABELS = dict(figpack.base.MODEL_LABELS)
MODEL_TO_TIER = dict(figpack.base.MODEL_TO_TIER)
TIER_NAMES = figpack.TIER_NAME
FAMILY_BY_SUITE = {
    "stayflow_concierge": "Travel",
    "freshcart_market": "Grocery",
    "clinic_shift_command": "Clinical Command",
    "campus_registrar_command": "Campus Registrar",
    "media_campaign_launch_desk": "Media Campaign",
    "homefix_hub": "Home Services",
}
SUITE_ORDER = list(figpack.SUITE_TO_FAMILY.keys())
TIER_ORDER = list(figpack.TIER_ORDER)
REPS = [f"r{i:02d}" for i in range(1, 11)]

EXPECTED = {
    "overall": {
        "planned": 2160,
        "reportable": 2157,
        "full": 244,
        "formal": 0.363,
        "step": 0.491,
    },
    "groups": {
        "M": {"reportable": 719, "full": 5, "rate": 0.007},
        "T": {"reportable": 720, "full": 65, "rate": 0.090},
        "F": {"reportable": 718, "full": 174, "rate": 0.242},
    },
    "tiers": {
        "A": {"reportable": 539, "full": 116},
        "B": {"reportable": 540, "full": 82},
        "C": {"reportable": 539, "full": 38},
        "D": {"reportable": 539, "full": 8},
    },
    "families": {
        "Travel": {"reportable": 359, "full": 6, "formal": 0.285, "step": 0.460},
        "Grocery": {"reportable": 359, "full": 20, "formal": 0.247, "step": 0.402},
        "Clinical Command": {"reportable": 360, "full": 43, "formal": 0.429, "step": 0.529},
        "Campus Registrar": {"reportable": 360, "full": 70, "formal": 0.424, "step": 0.525},
        "Media Campaign": {"reportable": 359, "full": 86, "formal": 0.453, "step": 0.542},
        "Home Services": {"reportable": 360, "full": 19, "formal": 0.338, "step": 0.485},
    },
}


def pct(x: float | int | None, digits: int = 1) -> str:
    if x is None or pd.isna(x):
        return "N/A"
    return f"{100 * float(x):.{digits}f}\\%"


def pct_plain(x: float | int | None, digits: int = 1) -> str:
    if x is None or pd.isna(x):
        return "N/A"
    return f"{100 * float(x):.{digits}f}%"


def weighted_mean(df: pd.DataFrame, value_col: str, weight_col: str = "reportable_runs") -> float:
    ok = df[[value_col, weight_col]].dropna()
    denom = ok[weight_col].sum()
    if denom <= 0:
        return np.nan
    return float((ok[value_col] * ok[weight_col]).sum() / denom)


def format_count(full: float | int | None, total: float | int | None) -> str:
    if full is None or total is None or pd.isna(full) or pd.isna(total) or int(total) == 0:
        return "N/A"
    rate = float(full) / float(total)
    return f"{int(round(full))}/{int(round(total))} ({100 * rate:.1f}\\%)"


def load_latest_aggregate() -> tuple[pd.DataFrame, pd.DataFrame]:
    tier, model_tier, _ = figpack.load_report()
    return tier.copy(), model_tier.copy()


def per_model_from_raw() -> pd.DataFrame:
    raw_path = DATA_DIR / "raw_runs.csv"
    if not raw_path.exists():
        return pd.DataFrame()
    raw = pd.read_csv(raw_path)
    if "view_current_raw" in raw.columns:
        raw = raw[raw["view_current_raw"] == True].copy()  # noqa: E712
    if raw.empty:
        return pd.DataFrame()
    g = (
        raw.groupby(["suite", "tier", "model_tier", "model", "model_label"], observed=True, dropna=False)
        .agg(
            reportable_runs=("passed", "size"),
            full_pass_count=("passed", "sum"),
            S_scen=("formal_ratio", "mean"),
            S_step=("stepwise_ratio", "mean"),
            source_file=("summary_path", lambda x: "; ".join(sorted(set(map(str, x)))[:3])),
            observed_reps=("rep", lambda x: "|".join(sorted(set(map(str, x))))),
        )
        .reset_index()
    )
    g["input_source"] = "reports/conformweb_visualizations/data/raw_runs.csv"
    return g


def per_model_from_report() -> pd.DataFrame:
    p = DATA_DIR / "report_per_model_rollups.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    if df.empty:
        return pd.DataFrame()
    out = df.rename(
        columns={
            "runs": "reportable_runs",
            "formal_mean": "S_scen",
            "stepwise_mean": "S_step",
            "full_pass": "full_pass_count",
        }
    )
    out["input_source"] = "reports/conformweb_visualizations/data/report_per_model_rollups.csv"
    out["source_file"] = out["source"].fillna("report_per_model_rollups.csv")
    out["observed_reps"] = "|".join(REPS)
    return out[[
        "suite",
        "tier",
        "model_tier",
        "model",
        "model_label",
        "reportable_runs",
        "full_pass_count",
        "S_scen",
        "S_step",
        "source_file",
        "observed_reps",
        "input_source",
    ]]


def load_available_per_model() -> pd.DataFrame:
    parts = [per_model_from_raw(), per_model_from_report()]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts, ignore_index=True, sort=False)
    df["model"] = df["model"].astype(str)
    df["model_label"] = df["model"].map(MODEL_LABELS).fillna(df["model_label"])
    df["model_tier"] = df["model"].map(MODEL_TO_TIER).fillna(df["model_tier"])
    # Prefer explicit report rows when both a raw-derived and report row exist.
    df["_priority"] = np.where(df["input_source"].str.contains("report_per_model", regex=False), 1, 0)
    df = df.sort_values(["suite", "tier", "model", "_priority"])
    df = df.drop_duplicates(["suite", "tier", "model"], keep="last")
    return df.drop(columns=["_priority"])


def expected_grid() -> pd.DataFrame:
    rows = []
    for suite in SUITE_ORDER:
        for tier in TIER_ORDER:
            for model in MODEL_ORDER:
                rows.append(
                    {
                        "suite": suite,
                        "family": FAMILY_BY_SUITE[suite],
                        "target_id": suite,
                        "tier": tier,
                        "tier_name": TIER_NAMES[tier],
                        "model": model,
                        "model_label": MODEL_LABELS[model],
                        "model_tier": MODEL_TO_TIER[model],
                        "model_group": MODEL_GROUPS[MODEL_TO_TIER[model]],
                        "planned_runs": 10,
                    }
                )
    return pd.DataFrame(rows)


def build_instance_model_grid() -> pd.DataFrame:
    avail = load_available_per_model()
    grid = expected_grid()
    if avail.empty:
        for col in ["reportable_runs", "full_pass_count", "S_scen", "S_step", "source_file", "observed_reps", "input_source"]:
            grid[col] = np.nan
        return grid
    merged = grid.merge(
        avail,
        on=["suite", "tier", "model", "model_label", "model_tier"],
        how="left",
        suffixes=("", "_src"),
    )
    merged["reportable_runs"] = merged["reportable_runs"].fillna(0).astype(int)
    merged["full_pass_count"] = merged["full_pass_count"].fillna(0)
    merged["missing_or_excluded_runs"] = merged["planned_runs"] - merged["reportable_runs"]
    merged["source_status"] = np.where(
        merged["input_source"].isna(),
        "model_level_source_unavailable",
        np.where(merged["reportable_runs"] < merged["planned_runs"], "missing_or_excluded_evaluation", "available"),
    )
    return merged


def aggregate_model_tier(grid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model_tier, model, model_label, tier), sub in grid.groupby(["model_tier", "model", "model_label", "tier"], observed=True):
        planned = int(sub["planned_runs"].sum())
        reportable = int(sub["reportable_runs"].sum())
        full = int(round(sub["full_pass_count"].sum()))
        rows.append(
            {
                "model_group": MODEL_GROUPS[model_tier],
                "model": model_label,
                "tier": tier,
                "tier_name": TIER_NAMES[tier],
                "planned_runs": planned,
                "reportable_runs": reportable,
                "missing_or_excluded_runs": planned - reportable,
                "full_pass_count": full,
                "full_pass_rate_reportable": full / reportable if reportable else np.nan,
                "full_pass_rate_planned": full / planned if planned else np.nan,
                "S_scen": weighted_mean(sub, "S_scen"),
                "S_step": weighted_mean(sub, "S_step"),
                "available_instance_model_cells": int((sub["source_status"] != "model_level_source_unavailable").sum()),
                "missing_instance_model_cells": int((sub["source_status"] == "model_level_source_unavailable").sum()),
            }
        )
    out = pd.DataFrame(rows)
    out["model_order"] = out["model"].map({MODEL_LABELS[m]: i for i, m in enumerate(MODEL_ORDER)})
    out["tier_order"] = out["tier"].map({t: i for i, t in enumerate(TIER_ORDER)})
    return out.sort_values(["model_order", "tier_order"]).drop(columns=["model_order", "tier_order"])


def aggregate_model(model_tier_rollup: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (group, model), sub in model_tier_rollup.groupby(["model_group", "model"], observed=True, sort=False):
        planned = int(sub["planned_runs"].sum())
        reportable = int(sub["reportable_runs"].sum())
        full = int(sub["full_pass_count"].sum())
        rec: dict[str, Any] = {
            "model_group": group,
            "model": model,
            "planned_runs": planned,
            "reportable_runs": reportable,
            "missing_or_excluded_runs": planned - reportable,
            "full_pass_count": full,
            "full_pass_rate_reportable": full / reportable if reportable else np.nan,
            "full_pass_rate_planned": full / planned if planned else np.nan,
            "S_scen": weighted_mean(sub, "S_scen"),
            "S_step": weighted_mean(sub, "S_step"),
        }
        for tier in TIER_ORDER:
            tsub = sub[sub["tier"] == tier]
            if tsub.empty:
                planned_t = reportable_t = full_t = 0
                s_scen = s_step = np.nan
            else:
                r = tsub.iloc[0]
                planned_t = int(r["planned_runs"])
                reportable_t = int(r["reportable_runs"])
                full_t = int(r["full_pass_count"])
                s_scen = r["S_scen"]
                s_step = r["S_step"]
            rec.update(
                {
                    f"{tier}_planned_runs": planned_t,
                    f"{tier}_reportable_runs": reportable_t,
                    f"{tier}_full_pass_count": full_t,
                    f"{tier}_full_pass_rate_reportable": full_t / reportable_t if reportable_t else np.nan,
                    f"{tier}_S_scen": s_scen,
                    f"{tier}_S_step": s_step,
                }
            )
        rows.append(rec)
    out = pd.DataFrame(rows)
    out["model_order"] = out["model"].map({MODEL_LABELS[m]: i for i, m in enumerate(MODEL_ORDER)})
    return out.sort_values("model_order").drop(columns=["model_order"])


def build_missing_rows(grid: pd.DataFrame, latest_model_tier: pd.DataFrame) -> pd.DataFrame:
    rows = []
    mt_index = latest_model_tier.set_index(["suite", "tier", "model_tier"])
    for _, rec in grid.iterrows():
        if int(rec["missing_or_excluded_runs"]) <= 0:
            continue
        observed = set(str(rec.get("observed_reps") or "").split("|")) if pd.notna(rec.get("observed_reps")) else set()
        missing_reps = [r for r in REPS if r not in observed]
        if rec["source_status"] == "model_level_source_unavailable":
            missing_reps = REPS
        key = (rec["suite"], rec["tier"], rec["model_tier"])
        group_reportable = int(mt_index.loc[key]["runs"]) if key in mt_index.index else 0
        group_has_actual_missing = group_reportable < 30
        for idx, rep in enumerate(missing_reps[: int(rec["missing_or_excluded_runs"])]):
            if rec["source_status"] == "model_level_source_unavailable":
                reason = "model-level artifact unavailable in local workspace"
                notes = "Latest model-group aggregate exists, but the corresponding per-model run artifact was not available locally; value was not inferred."
                source_file = "reports/conformweb_visualizations/data/report_model_tier_rollups.csv"
            else:
                if group_has_actual_missing:
                    reason = "missing or excluded evaluation result"
                    notes = "Latest model-group aggregate reports fewer than 30 reportable runs for this instance and model group."
                    source_file = str(rec.get("source_file") or rec.get("input_source") or "")
                else:
                    reason = "model-level artifact incomplete in local workspace"
                    notes = "The latest model-group aggregate reports the full 30-run cohort, so this is source coverage missing at per-model granularity, not a missing paper-scope run."
                    source_file = str(rec.get("source_file") or rec.get("input_source") or "")
            if (
                rec["suite"] == "media_campaign_launch_desk"
                and rec["tier"] == "D"
                and rec["model"] == "gemini31_pro_preview"
                and idx == 0
            ):
                reason = "generation hung or was excluded from scoring"
                notes = "Media Campaign Tier D evaluation report notes one Gemini Pro generation hung during the final cohort."
                source_file = "targets/web/media_campaign_launch_desk/evaluation_report.md"
            rows.append(
                {
                    "family": rec["family"],
                    "target_id": rec["target_id"],
                    "instance_id": f"{rec['suite']}_tier_{str(rec['tier']).lower()}",
                    "tier": rec["tier"],
                    "model_group": rec["model_group"],
                    "model": rec["model_label"],
                    "generation_index": rep,
                    "reason": reason,
                    "source_file": source_file,
                    "notes": notes,
                }
            )
    return pd.DataFrame(rows)


def validate_latest_aggregates(tier: pd.DataFrame, model_tier: pd.DataFrame) -> tuple[bool, list[str]]:
    messages: list[str] = []
    ok = True
    overall_runs = int(tier["runs"].sum())
    overall_full = int(tier["full_pass"].sum())
    formal = figpack.weighted_mean(tier, "formal_mean")
    step = figpack.weighted_mean(tier, "stepwise_mean")
    checks = [
        ("overall reportable", overall_runs, EXPECTED["overall"]["reportable"]),
        ("overall full pass", overall_full, EXPECTED["overall"]["full"]),
    ]
    for name, got, exp in checks:
        if got != exp:
            ok = False
            messages.append(f"FAIL {name}: got {got}, expected {exp}")
        else:
            messages.append(f"PASS {name}: {got}")
    for name, got, exp in [("overall S_scen", formal, EXPECTED["overall"]["formal"]), ("overall S_step", step, EXPECTED["overall"]["step"])]:
        if not math.isclose(got, exp, abs_tol=0.0025):
            ok = False
            messages.append(f"FAIL {name}: got {got:.4f}, expected approx {exp:.4f}")
        else:
            messages.append(f"PASS {name}: {got:.4f}")
    grp = model_tier.groupby("model_tier", observed=True).agg(reportable=("runs", "sum"), full=("full_pass", "sum"))
    for mt, exp in EXPECTED["groups"].items():
        got = grp.loc[mt]
        if int(got["reportable"]) != exp["reportable"] or int(got["full"]) != exp["full"]:
            ok = False
            messages.append(f"FAIL group {mt}: got {int(got['full'])}/{int(got['reportable'])}, expected {exp['full']}/{exp['reportable']}")
        else:
            messages.append(f"PASS group {mt}: {int(got['full'])}/{int(got['reportable'])}")
    tiers = tier.groupby("tier", observed=True).agg(reportable=("runs", "sum"), full=("full_pass", "sum"))
    for t, exp in EXPECTED["tiers"].items():
        got = tiers.loc[t]
        if int(got["reportable"]) != exp["reportable"] or int(got["full"]) != exp["full"]:
            ok = False
            messages.append(f"FAIL tier {t}: got {int(got['full'])}/{int(got['reportable'])}, expected {exp['full']}/{exp['reportable']}")
        else:
            messages.append(f"PASS tier {t}: {int(got['full'])}/{int(got['reportable'])}")
    fam = tier.groupby("family", observed=True).agg(reportable=("runs", "sum"), full=("full_pass", "sum"), S_scen=("formal_mean", lambda x: np.nan), S_step=("stepwise_mean", lambda x: np.nan))
    for family, exp in EXPECTED["families"].items():
        sub = tier[tier["family"] == family]
        reportable = int(sub["runs"].sum())
        full = int(sub["full_pass"].sum())
        fmean = figpack.weighted_mean(sub, "formal_mean")
        smean = figpack.weighted_mean(sub, "stepwise_mean")
        if reportable != exp["reportable"] or full != exp["full"] or not math.isclose(fmean, exp["formal"], abs_tol=0.0035) or not math.isclose(smean, exp["step"], abs_tol=0.0035):
            ok = False
            messages.append(f"FAIL family {family}: got {full}/{reportable}, S_scen={fmean:.3f}, S_step={smean:.3f}; expected {exp['full']}/{exp['reportable']}, {exp['formal']:.3f}, {exp['step']:.3f}")
        else:
            messages.append(f"PASS family {family}: {full}/{reportable}, S_scen={fmean:.3f}, S_step={smean:.3f}")
    return ok, messages


def write_latex_table(model_rollup: pd.DataFrame, complete: bool) -> None:
    ROOT_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append(r"\begin{table*}[t]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\setlength{\tabcolsep}{4pt}")
    lines.append(r"\caption{Model-level behavioral conformance. Overall columns report conformance across all benchmark instances; tier columns report full-pass rates by complexity tier. Denominators are reportable runs when available. Missing planned runs and unavailable per-model source artifacts are audited separately.}")
    lines.append(r"\label{tab:model-tier-conformance}")
    lines.append(r"\begin{tabular}{llrrrrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Group & Model & Full pass & $S_{\mathrm{scen}}$ & $S_{\mathrm{step}}$ & A & B & C & D \\")
    lines.append(r"\midrule")
    last_group = None
    for _, rec in model_rollup.iterrows():
        group = rec["model_group"]
        if last_group is not None and group != last_group:
            lines.append(r"\addlinespace[2pt]")
        last_group = group
        cells = [
            str(group),
            str(rec["model"]),
            format_count(rec["full_pass_count"], rec["reportable_runs"]),
            pct(rec["S_scen"]),
            pct(rec["S_step"]),
        ]
        for tier in TIER_ORDER:
            cells.append(format_count(rec[f"{tier}_full_pass_count"], rec[f"{tier}_reportable_runs"]))
        lines.append(" & ".join(cells) + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    if not complete:
        lines.append(r"\vspace{2pt}")
        lines.append(r"\footnotesize{\emph{Audit note:} The local workspace does not contain complete per-model artifacts for every planned instance-model cell, so this table should not be used as the final main-paper table until the missing source artifacts are restored.}")
    lines.append(r"\end{table*}")
    (ROOT_TABLE_DIR / "main_model_tier_conformance.tex").write_text("\n".join(lines) + "\n")


def write_report(
    tier: pd.DataFrame,
    model_tier: pd.DataFrame,
    model_rollup: pd.DataFrame,
    model_tier_rollup: pd.DataFrame,
    missing: pd.DataFrame,
    invariant_ok: bool,
    invariant_messages: list[str],
    complete: bool,
) -> None:
    overall_runs = int(tier["runs"].sum())
    overall_full = int(tier["full_pass"].sum())
    formal = figpack.weighted_mean(tier, "formal_mean")
    step = figpack.weighted_mean(tier, "stepwise_mean")
    group = model_tier.groupby("model_tier", observed=True).agg(reportable=("runs", "sum"), full=("full_pass", "sum"))
    tiers = tier.groupby("tier", observed=True).agg(reportable=("runs", "sum"), full=("full_pass", "sum"))
    fam_rows = []
    for family in figpack.FAMILY_ORDER:
        sub = tier[tier["family"] == family]
        fam_rows.append(
            {
                "family": family,
                "reportable": int(sub["runs"].sum()),
                "full": int(sub["full_pass"].sum()),
                "S_scen": figpack.weighted_mean(sub, "formal_mean"),
                "S_step": figpack.weighted_mean(sub, "stepwise_mean"),
            }
        )
    fam = pd.DataFrame(fam_rows)
    md = []
    md.append("# Main Model Rollup Audit\n")
    md.append("## Status\n")
    md.append(f"- Latest aggregate invariants: {'PASS' if invariant_ok else 'FAIL'}")
    md.append(f"- Complete per-model 24-instance grid available locally: {'PASS' if complete else 'FAIL'}")
    if not complete:
        md.append("- Per-model values were **not inferred** from model-group aggregates. CSV/LaTeX outputs contain only available per-model source values and explicitly mark missing source coverage.")
    md.append("\n## Source Files Used\n")
    md.extend(
        [
            "- `reports/conformweb_visualizations/data/report_tier_rollups.csv`",
            "- `reports/conformweb_visualizations/data/report_model_tier_rollups.csv`",
            "- `reports/conformweb_visualizations/data/report_per_model_rollups.csv`",
            "- `reports/conformweb_visualizations/data/raw_runs.csv`",
            "- `tools/build_main_model_experiment_table.py`",
        ]
    )
    md.append("\n## Command\n")
    md.append("```bash\npython tools/build_main_model_experiment_table.py\n```")
    md.append("\n## Invariant Check\n")
    md.extend(f"- {m}" for m in invariant_messages)
    md.append("\n## Overall Aggregate Reproduced\n")
    md.append(f"- Reportable generations: {overall_runs:,}")
    md.append(f"- Full pass: {overall_full:,}")
    md.append(f"- Full-pass rate: {overall_full / overall_runs:.3%}")
    md.append(f"- S_scen: {formal:.3%}")
    md.append(f"- S_step: {step:.3%}")
    md.append("\n## Group Aggregate Reproduced\n")
    for mt in figpack.MODEL_ORDER:
        r = group.loc[mt]
        md.append(f"- {MODEL_GROUPS[mt]}: {int(r['full'])}/{int(r['reportable'])} ({int(r['full']) / int(r['reportable']):.1%})")
    md.append("\n## Tier Aggregate Reproduced\n")
    for t in TIER_ORDER:
        r = tiers.loc[t]
        md.append(f"- Tier {t} ({TIER_NAMES[t]}): {int(r['full'])}/{int(r['reportable'])} ({int(r['full']) / int(r['reportable']):.1%})")
    md.append("\n## Family Aggregate Reproduced\n")
    for _, r in fam.iterrows():
        md.append(f"- {r['family']}: {r['full']}/{r['reportable']}, S_scen={r['S_scen']:.1%}, S_step={r['S_step']:.1%}")
    md.append("\n## Per-model Planned/Reportable Counts\n")
    md.append(model_rollup[["model_group", "model", "planned_runs", "reportable_runs", "missing_or_excluded_runs", "full_pass_count", "full_pass_rate_reportable", "S_scen", "S_step"]].to_markdown(index=False, floatfmt=".4f"))
    md.append("\n## Missing / Excluded / Unavailable Rows\n")
    reason_counts = missing["reason"].value_counts(dropna=False) if not missing.empty else pd.Series(dtype=int)
    if reason_counts.empty:
        md.append("- None.")
    else:
        for reason, count in reason_counts.items():
            md.append(f"- {reason}: {count}")
    actual_missing = int(missing["reason"].isin(["missing or excluded evaluation result", "generation hung or was excluded from scoring"]).sum()) if not missing.empty else 0
    md.append(f"\nActual latest-aggregate missing/excluded planned runs identified from model-group accounting: {actual_missing}.")
    md.append("\n## Warnings\n")
    md.append("- `raw_runs.csv` is a partial raw-trace artifact and is not sufficient by itself for the 6-family model-level table.")
    md.append("- `report_per_model_rollups.csv` is also partial: it contains explicit per-model rows for Campus/Media A/B and Campus C/D Frontier, but not all 24 instances.")
    md.append("- The latest paper aggregate is complete at model-group level, not complete at per-model level in the local workspace.")
    (REPORT_DIR / "main_model_rollup_report.md").write_text("\n".join(md) + "\n")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ROOT_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    tier, latest_model_tier = load_latest_aggregate()
    invariant_ok, invariant_messages = validate_latest_aggregates(tier, latest_model_tier)
    grid = build_instance_model_grid()
    model_tier_rollup = aggregate_model_tier(grid)
    model_rollup = aggregate_model(model_tier_rollup)
    complete = bool((grid["source_status"] != "model_level_source_unavailable").all() and (model_rollup["planned_runs"].eq(240)).all() and (model_rollup["reportable_runs"].sum() == EXPECTED["overall"]["reportable"]))
    missing = build_missing_rows(grid, latest_model_tier)

    model_rollup.to_csv(DATA_DIR / "main_model_rollup_complete.csv", index=False)
    model_tier_rollup.to_csv(DATA_DIR / "main_model_tier_rollup_complete.csv", index=False)
    missing.to_csv(DATA_DIR / "main_missing_or_excluded_runs.csv", index=False)
    write_latex_table(model_rollup, complete)
    write_report(tier, latest_model_tier, model_rollup, model_tier_rollup, missing, invariant_ok, invariant_messages, complete)

    print(DATA_DIR / "main_model_rollup_complete.csv")
    print(DATA_DIR / "main_model_tier_rollup_complete.csv")
    print(DATA_DIR / "main_missing_or_excluded_runs.csv")
    print(REPORT_DIR / "main_model_rollup_report.md")
    print(ROOT_TABLE_DIR / "main_model_tier_conformance.tex")
    print(f"invariant_ok={invariant_ok}")
    print(f"complete_per_model_grid={complete}")
    print(model_rollup[["model_group", "model", "planned_runs", "reportable_runs", "missing_or_excluded_runs", "full_pass_count", "full_pass_rate_reportable", "S_scen", "S_step"]].to_markdown(index=False, floatfmt=".4f"))


if __name__ == "__main__":
    main()
