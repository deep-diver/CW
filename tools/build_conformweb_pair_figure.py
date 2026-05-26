#!/usr/bin/env python3
"""Build the two-panel square-derived figure for the ConformWeb paper."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


figpack = load_module("conformweb_figpack", ROOT / "tools" / "build_conformweb_figure_pack.py")
audit = load_module("conformweb_private_audit", ROOT / "tools" / "audit_private_admissibility.py")


OUT_DIR = ROOT / "reports" / "conformweb_visualizations" / "figures" / "main_or_appendix"
MAIN_DIR = ROOT / "reports" / "conformweb_visualizations" / "figures" / "main"

FONT = {
    # These sizes are chosen for a figure* inserted near full text width.
    # Keeping the canvas close to paper size avoids LaTeX downscaling tiny text.
    "legend": 8.1,
    "axis_label": 8.8,
    "tick": 8.4,
    "row": 8.9,
    "value": 8.0,
    "panel_title": 8.2,
}

REFERENCE_COLORS = {
    # Palette family adapted from the supplied basic/intermediate/complex/edge example.
    # These exact colors are kept for contract-reference semantics only, so they are not
    # reused for unrelated failure categories.
    "public_private": "#F6C344",
    "private_only": "#35C3CC",
    "unused": "#DADCE0",
}


def pct_axis(x: float, _pos: int | None = None) -> str:
    return f"{int(round(x))}%"


def reference_legend_handles(*, standalone: bool = False) -> list[Patch]:
    labels = (
        ("Public + Private", "Private Only", "Declared, but unused")
        if standalone
        else ("Public + private", "Private only", "Declared, not scored")
    )
    return [
        Patch(color=REFERENCE_COLORS["public_private"], label=labels[0]),
        Patch(color=REFERENCE_COLORS["private_only"], label=labels[1]),
        Patch(color=REFERENCE_COLORS["unused"], label=labels[2]),
    ]


def gap_legend_handles() -> list[Line2D]:
    return [
        Line2D([0], [0], marker="D", color="none", markerfacecolor=figpack.COL["full"], markeredgecolor=figpack.COL["full"], markersize=5.6, label="Full pass"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=figpack.COL["scenario"], markeredgecolor="white", markeredgewidth=0.6, markersize=5.8, label="Scenario"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=figpack.COL["step"], markeredgecolor="white", markeredgewidth=0.6, markersize=5.8, label="Step"),
    ]


def draw_reference_coverage(
    ax,
    coverage_rows: list[dict],
    show_panel_title: bool = True,
    show_grid: bool = True,
    show_legend: bool = True,
    ytick_rotation: float = 0.0,
    compact_ylabels: bool = False,
) -> None:
    categories = [
        "Actions",
        "State / observation paths",
        "Routes/pages",
        "Rendered tables",
        "Events",
    ]
    labels = {
        "Actions": "Actions",
        "State / observation paths": "State paths",
        "Routes/pages": "Routes",
        "Rendered tables": "Rendered tables",
        "Events": "Events",
    }
    if compact_ylabels:
        labels["Rendered tables"] = "Rendered\ntables"
    totals = {}
    for category in categories:
        subset = [row for row in coverage_rows if row["category"] == category]
        totals[category] = {
            "declared": sum(int(row["declared_in_public_contract"]) for row in subset),
            "seen": sum(int(row["private_seen_in_public_examples"]) for row in subset),
            "private_only": sum(int(row["private_only_but_declared"]) for row in subset),
            "undeclared": sum(int(row["private_undeclared"]) for row in subset),
        }

    declared = [totals[c]["declared"] for c in categories]
    seen = [totals[c]["seen"] for c in categories]
    private_only = [totals[c]["private_only"] for c in categories]
    undeclared = [totals[c]["undeclared"] for c in categories]
    unused = [
        max(declared_i - seen_i - private_i - undeclared_i, 0)
        for declared_i, seen_i, private_i, undeclared_i in zip(declared, seen, private_only, undeclared, strict=True)
    ]

    def share(values: list[int]) -> list[float]:
        return [
            (100 * value / total) if total else 0.0
            for value, total in zip(values, declared, strict=True)
        ]

    seen_share = share(seen)
    private_share = share(private_only)
    unused_share = share(unused)
    orange = REFERENCE_COLORS["public_private"]
    purple = REFERENCE_COLORS["private_only"]
    gray = REFERENCE_COLORS["unused"]
    ink = figpack.COL["ink"]
    y = np.arange(len(categories))

    ax.set_axisbelow(True)
    if show_grid:
        for x in [0, 25, 50, 75, 100]:
            ax.axvline(x, color="#EEF1F4", lw=0.8, zorder=0)
    ax.barh(y, seen_share, height=0.66, color=orange, edgecolor="white", linewidth=0.8)
    ax.barh(y, private_share, left=seen_share, height=0.66, color=purple, edgecolor="white", linewidth=0.8)
    ax.barh(
        y,
        unused_share,
        left=[seen_i + private_i for seen_i, private_i in zip(seen_share, private_share, strict=True)],
        height=0.66,
        color=gray,
        edgecolor="white",
        linewidth=0.8,
    )

    for idx in range(len(categories)):
        if seen[idx] > 0:
            ax.text(seen_share[idx] / 2, idx, f"{seen[idx]}", ha="center", va="center", fontsize=FONT["value"], fontweight="bold", color=ink)
        if private_only[idx] > 0:
            ax.text(
                seen_share[idx] + private_share[idx] / 2,
                idx,
                f"{private_only[idx]}",
                ha="center",
                va="center",
                fontsize=FONT["value"],
                fontweight="bold",
                color="white",
            )
        if unused[idx] > 0:
            ax.text(
                seen_share[idx] + private_share[idx] + unused_share[idx] / 2,
                idx,
                f"{unused[idx]}",
                ha="center",
                va="center",
                fontsize=FONT["value"],
                fontweight="bold",
                color=ink,
            )

    ax.set_yticks(y)
    ax.set_yticklabels(
        [labels[category] for category in categories],
        fontsize=FONT["row"],
        fontweight="bold",
        rotation=ytick_rotation,
        ha="right",
        va="center",
        rotation_mode="anchor",
    )
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.set_xlabel("Share of declared contract references (%)", fontsize=FONT["axis_label"], fontweight="bold")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=FONT["tick"])
    for tick in ax.get_xticklabels():
        tick.set_fontweight("bold")
    if show_legend:
        ax.legend(
            handles=reference_legend_handles(),
            loc="upper center",
            bbox_to_anchor=(0.5, 1.105),
            ncol=3,
            frameon=False,
            handletextpad=0.3,
            columnspacing=0.72,
            prop={"weight": "bold", "size": FONT["legend"]},
        )
    if show_panel_title:
        ax.text(
            0.5,
            -0.20,
            "(a) Private scenarios reuse declared references",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=FONT["panel_title"],
            fontweight="bold",
            color=ink,
        )


def draw_reference_coverage_vertical(
    ax,
    coverage_rows: list[dict],
    show_legend: bool = True,
) -> None:
    vertical_font = {
        "legend": 10.0,
        "axis_label": 11.2,
        "tick": 10.6,
        "row": 11.2,
        "value": 11.0,
    }
    categories = [
        "Actions",
        "State / observation paths",
        "Routes/pages",
        "Rendered tables",
        "Events",
    ]
    labels = {
        "Actions": "Actions",
        "State / observation paths": "State\npaths",
        "Routes/pages": "Routes",
        "Rendered tables": "Rendered\ntables",
        "Events": "Events",
    }
    totals = {}
    for category in categories:
        subset = [row for row in coverage_rows if row["category"] == category]
        totals[category] = {
            "declared": sum(int(row["declared_in_public_contract"]) for row in subset),
            "seen": sum(int(row["private_seen_in_public_examples"]) for row in subset),
            "private_only": sum(int(row["private_only_but_declared"]) for row in subset),
            "undeclared": sum(int(row["private_undeclared"]) for row in subset),
        }

    declared = [totals[c]["declared"] for c in categories]
    seen = [totals[c]["seen"] for c in categories]
    private_only = [totals[c]["private_only"] for c in categories]
    undeclared = [totals[c]["undeclared"] for c in categories]
    unused = [
        max(declared_i - seen_i - private_i - undeclared_i, 0)
        for declared_i, seen_i, private_i, undeclared_i in zip(declared, seen, private_only, undeclared, strict=True)
    ]

    def share(values: list[int]) -> list[float]:
        return [
            (100 * value / total) if total else 0.0
            for value, total in zip(values, declared, strict=True)
        ]

    seen_share = share(seen)
    private_share = share(private_only)
    unused_share = share(unused)
    x = np.arange(len(categories)) * 1.62
    orange = REFERENCE_COLORS["public_private"]
    purple = REFERENCE_COLORS["private_only"]
    gray = REFERENCE_COLORS["unused"]
    ink = figpack.COL["ink"]

    ax.set_axisbelow(True)
    for y in [0, 25, 50, 75, 100]:
        ax.axhline(y, color="#EEF1F4", lw=0.8, zorder=0)
    ax.bar(x, seen_share, width=0.82, color=orange, edgecolor="white", linewidth=0.8)
    ax.bar(x, private_share, bottom=seen_share, width=0.82, color=purple, edgecolor="white", linewidth=0.8)
    ax.bar(
        x,
        unused_share,
        bottom=[s + p for s, p in zip(seen_share, private_share, strict=True)],
        width=0.82,
        color=gray,
        edgecolor="white",
        linewidth=0.8,
    )

    for idx in range(len(categories)):
        if seen_share[idx] >= 7:
            ax.text(
                x[idx],
                seen_share[idx] / 2,
                f"{seen[idx]}",
                ha="center",
                va="center",
                fontsize=vertical_font["value"],
                fontweight="bold",
                color=ink,
            )
        if private_share[idx] >= 7:
            ax.text(
                x[idx],
                seen_share[idx] + private_share[idx] / 2,
                f"{private_only[idx]}",
                ha="center",
                va="center",
                fontsize=vertical_font["value"],
                fontweight="bold",
                color="white",
            )
        if unused_share[idx] >= 7:
            ax.text(
                x[idx],
                seen_share[idx] + private_share[idx] + unused_share[idx] / 2,
                f"{unused[idx]}",
                ha="center",
                va="center",
                fontsize=vertical_font["value"],
                fontweight="bold",
                color=ink,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [labels[category] for category in categories],
        fontsize=vertical_font["row"],
        fontweight="bold",
    )
    ax.set_ylim(0, 100)
    ax.set_xlim(x[0] - 0.82, x[-1] + 0.82)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.set_ylabel("Declared references (%)", fontsize=vertical_font["axis_label"], fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.tick_params(axis="y", labelsize=vertical_font["tick"])
    for tick in ax.get_yticklabels():
        tick.set_fontweight("bold")
    if show_legend:
        ax.legend(
            handles=reference_legend_handles(standalone=True),
            loc="upper center",
            bbox_to_anchor=(0.43, 1.16),
            ncol=3,
            frameon=False,
            handletextpad=0.35,
            columnspacing=0.72,
            prop={"weight": "bold", "size": vertical_font["legend"]},
        )


def draw_conformance_gap(
    ax,
    tier,
    show_panel_title: bool = True,
    show_grid: bool = True,
    show_legend: bool = True,
    show_xlabel: bool = True,
) -> None:
    df = figpack.report_family_summary(tier, missing_as_failed=True)
    short_family = {
        "Clinical Command": "Clinical Cmd.",
        "Campus Registrar": "Campus Reg.",
        "Media Campaign": "Media Camp.",
        "Home Services": "Home Services",
    }
    y = np.arange(len(df), dtype=float)
    if len(y) > 1:
        y[1:] += 0.35

    if show_grid:
        for x in [0, 20, 40, 60]:
            ax.axvline(x, color=figpack.COL["grid"], lw=0.8, zorder=0)

    scenario = df["formal_mean"] * 100
    step = df["stepwise_mean"] * 100
    full = df["full_pass_rate"] * 100
    for idx in range(len(df)):
        ax.plot(
            [scenario.iloc[idx], step.iloc[idx]],
            [y[idx], y[idx]],
            color="#AAB7C4",
            lw=2.0,
            solid_capstyle="round",
            zorder=1,
        )

    ax.scatter(full, y, s=34, color=figpack.COL["full"], marker="D", zorder=3)
    ax.scatter(scenario, y, s=42, color=figpack.COL["scenario"], edgecolor="white", lw=0.6, zorder=4)
    ax.scatter(step, y, s=42, color=figpack.COL["step"], edgecolor="white", lw=0.6, zorder=4)

    for idx, row in df.iterrows():
        ax.text(
            min(full.iloc[idx] + 2.35, 58.2),
            y[idx],
            figpack.fmt_count(row.full_pass, row.full_total),
            va="center",
            ha="left",
            fontsize=FONT["value"],
            fontweight="bold",
            color=figpack.COL["ink"],
        )

    ax.axhline((y[0] + y[1]) / 2, color="#C9CDD3", lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([short_family.get(name, name) for name in df["family"]], fontsize=FONT["row"], fontweight="bold")
    ax.set_xlim(0, 62)
    ax.set_ylim(y[-1] + 0.6, y[0] - 0.95)
    ax.set_xticks([0, 20, 40, 60])
    ax.xaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.set_xlabel("Score (%)" if show_xlabel else "", fontsize=FONT["axis_label"], fontweight="bold")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=FONT["tick"])
    for tick in ax.get_xticklabels():
        tick.set_fontweight("bold")
    if show_legend:
        ax.legend(
            handles=gap_legend_handles(),
            loc="upper center",
            bbox_to_anchor=(0.5, 1.105),
            ncol=3,
            frameon=False,
            handletextpad=0.35,
            columnspacing=1.05,
            prop={"weight": "bold", "size": FONT["legend"]},
        )
    if show_panel_title:
        ax.text(
            0.5,
            -0.20,
            "(b) Conformance gap",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=FONT["panel_title"],
            fontweight="bold",
            color=figpack.COL["ink"],
        )


def _model_tier_denominators(model_tier):
    df = model_tier.copy()
    expected_per_instance_group = 30.0
    df["_denom"] = df["full_total"].clip(lower=expected_per_instance_group)
    df["_formal_num"] = df["formal_mean"] * df["full_total"]
    df["_step_num"] = df["stepwise_mean"] * df["full_total"]
    df["x"] = df["model_tier"].map({m: i for i, m in enumerate(figpack.MODEL_ORDER)})
    return df


def draw_model_progress(ax, model_tier, show_legend: bool = False) -> None:
    df = _model_tier_denominators(model_tier)
    offsets = {"formal_mean": -0.13, "stepwise_mean": 0.13}
    colors = {"formal_mean": figpack.COL["scenario"], "stepwise_mean": figpack.COL["step"]}
    labels = {"formal_mean": "Scenario", "stepwise_mean": "Step"}

    for metric in ["formal_mean", "stepwise_mean"]:
        for mt in figpack.MODEL_ORDER:
            sub = df[df.model_tier == mt]
            x = figpack.MODEL_ORDER.index(mt) + offsets[metric]
            vals = sub[metric].dropna().to_numpy() * 100
            if len(vals) == 0:
                continue
            jitter = np.linspace(-0.033, 0.033, len(vals))
            ax.scatter(
                np.full(len(vals), x) + jitter,
                vals,
                s=13,
                color=colors[metric],
                alpha=0.34,
                linewidth=0,
                zorder=2,
            )
            numerator = "_formal_num" if metric == "formal_mean" else "_step_num"
            mean = 100 * sub[numerator].sum() / sub["_denom"].sum()
            se = vals.std(ddof=1) / math.sqrt(len(vals)) if len(vals) > 1 else 0
            ax.errorbar(
                [x],
                [mean],
                yerr=[1.96 * se],
                fmt="o",
                color=colors[metric],
                markersize=6.6,
                capsize=3.0,
                lw=1.25,
                zorder=5,
                label=labels[metric] if mt == "M" else None,
            )

    ax.set_xticks(range(3))
    ax.set_xticklabels([figpack.MODEL_NAME[m] for m in figpack.MODEL_ORDER], fontsize=FONT["tick"], fontweight="bold")
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.set_ylabel("Score", fontsize=FONT["axis_label"], fontweight="bold")
    ax.grid(axis="y", color=figpack.COL["grid"], lw=0.8)
    ax.tick_params(axis="both", labelsize=FONT["tick"])
    for tick in ax.get_yticklabels():
        tick.set_fontweight("bold")
    if show_legend:
        ax.legend(
            loc="upper left",
            frameon=False,
            ncol=1,
            handletextpad=0.35,
            prop={"weight": "bold", "size": FONT["legend"]},
        )


def draw_model_full_pass(ax, model_tier) -> None:
    df = _model_tier_denominators(model_tier)
    grp = (
        df.groupby("model_tier", observed=True)
        .agg(full_pass=("full_pass", "sum"), full_total=("_denom", "sum"))
        .reindex(figpack.MODEL_ORDER)
    )
    rates = grp["full_pass"] / grp["full_total"] * 100
    bars = ax.bar(
        range(3),
        rates,
        width=0.58,
        color=figpack.COL["full"],
        alpha=0.9,
        edgecolor="white",
        linewidth=0.7,
    )
    for bar, mt in zip(bars, figpack.MODEL_ORDER, strict=True):
        rate = 100 * grp.loc[mt, "full_pass"] / grp.loc[mt, "full_total"]
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.25,
            f"{figpack.fmt_count(grp.loc[mt, 'full_pass'], grp.loc[mt, 'full_total'])}\n({rate:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=7.45,
            fontweight="bold",
            linespacing=0.95,
            color=figpack.COL["ink"],
        )
    ax.set_xticks(range(3))
    ax.set_xticklabels([figpack.MODEL_NAME[m] for m in figpack.MODEL_ORDER], fontsize=FONT["tick"], fontweight="bold")
    ax.set_ylim(0, max(32, float(rates.max()) + 10))
    ax.set_yticks([0, 10, 20, 30])
    ax.set_ylabel("Full-pass rate", fontsize=FONT["axis_label"], fontweight="bold")
    ax.yaxis.set_major_formatter(FuncFormatter(pct_axis))
    ax.grid(axis="y", color=figpack.COL["grid"], lw=0.8)
    ax.tick_params(axis="both", labelsize=FONT["tick"])
    for tick in ax.get_yticklabels():
        tick.set_fontweight("bold")


def make_gap_model_capability_figure(tier, model_tier) -> None:
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(7.75, 3.15),
        dpi=300,
        gridspec_kw={"width_ratios": [1.23, 1.0, 0.82], "wspace": 0.52},
    )
    fig.patch.set_facecolor("white")
    draw_conformance_gap(
        axes[0],
        tier,
        show_panel_title=False,
        show_legend=False,
        show_xlabel=True,
    )
    draw_model_progress(axes[1], model_tier)
    draw_model_full_pass(axes[2], model_tier)

    titles = [
        "(a) Family conformance gap",
        "(b) Progress by capability",
        "(c) Completion by capability",
    ]
    for ax, title in zip(axes, titles, strict=True):
        ax.set_title(title, loc="left", fontsize=9.0, fontweight="bold", color=figpack.COL["ink"], pad=7)

    fig.legend(
        handles=gap_legend_handles(),
        loc="upper center",
        bbox_to_anchor=(0.49, 0.985),
        ncol=3,
        frameon=False,
        handletextpad=0.35,
        columnspacing=1.2,
        prop={"weight": "bold", "size": FONT["legend"]},
    )
    fig.subplots_adjust(left=0.095, right=0.988, top=0.79, bottom=0.18)
    stem = OUT_DIR / "figure_conformance_gap_model_capability"
    stem_main = MAIN_DIR / "figure_conformance_gap_model_capability"
    for out_stem in [stem, stem_main]:
        out_stem.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_stem.with_suffix(".pdf"), bbox_inches="tight")
        fig.savefig(out_stem.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    for out_stem in [stem, stem_main]:
        print(out_stem.with_suffix(".pdf"))
        print(out_stem.with_suffix(".png"))

def save_individual_panel(
    name: str,
    draw_fn,
    *args,
    width: float = 3.55,
    height: float = 3.35,
    left: float = 0.25,
    right: float = 0.985,
    bottom: float = 0.19,
    legend_handles: list | None = None,
    legend_rows: list[list] | None = None,
    legend_columnspacing: float = 0.9,
    draw_kwargs: dict | None = None,
    subplot_top: float = 0.82,
) -> None:
    fig, ax = plt.subplots(figsize=(width, height), dpi=300)
    fig.patch.set_facecolor("white")
    kwargs = {
        "show_panel_title": False,
        "show_grid": False,
        "show_legend": False,
    }
    if draw_kwargs:
        kwargs.update(draw_kwargs)
    draw_fn(ax, *args, **kwargs)
    if legend_rows:
        row_anchors = [0.93, 0.875]
        for row_handles, y_anchor in zip(legend_rows, row_anchors, strict=True):
            fig.legend(
                handles=row_handles,
                loc="upper center",
                bbox_to_anchor=(0.5, y_anchor),
                ncol=len(row_handles),
                frameon=False,
                handletextpad=0.35,
                columnspacing=legend_columnspacing,
                prop={"weight": "bold", "size": FONT["legend"]},
            )
    elif legend_handles:
        fig.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.875),
            ncol=3,
            frameon=False,
            handletextpad=0.35,
            columnspacing=legend_columnspacing,
            prop={"weight": "bold", "size": FONT["legend"]},
        )
    fig.subplots_adjust(left=left, right=right, top=subplot_top, bottom=bottom)
    stem = MAIN_DIR / name
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(stem.with_suffix(".pdf"))
    print(stem.with_suffix(".png"))


def main() -> None:
    figpack.setup_style()
    tier, model_tier, _ = figpack.load_report()
    coverage_rows = audit.make_reference_coverage_rows()

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.35, 3.95),
        dpi=300,
        gridspec_kw={"width_ratios": [1.02, 1.0], "wspace": 0.62},
    )
    fig.patch.set_facecolor("white")
    draw_reference_coverage(axes[0], coverage_rows)
    draw_conformance_gap(axes[1], tier)
    fig.subplots_adjust(left=0.095, right=0.985, top=0.80, bottom=0.22)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MAIN_DIR.mkdir(parents=True, exist_ok=True)
    stems = [
        OUT_DIR / "figure_conformance_gap_reference_pair",
        MAIN_DIR / "figure_admissibility_conformance_gap",
    ]
    for stem in stems:
        fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
        fig.savefig(stem.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    for stem in stems:
        print(stem.with_suffix(".pdf"))
        print(stem.with_suffix(".png"))

    standalone_reference_handles = reference_legend_handles(standalone=True)
    save_individual_panel(
        "figure_private_scenario_reference_reuse",
        draw_reference_coverage,
        coverage_rows,
        width=4.95,
        height=3.28,
        left=0.18,
        right=0.985,
        bottom=0.18,
        legend_handles=standalone_reference_handles,
        legend_columnspacing=0.65,
        draw_kwargs={"ytick_rotation": 0, "compact_ylabels": True},
        subplot_top=0.765,
    )
    fig, ax = plt.subplots(figsize=(5.9, 4.35), dpi=300)
    fig.patch.set_facecolor("white")
    draw_reference_coverage_vertical(ax, coverage_rows)
    fig.subplots_adjust(left=0.14, right=0.985, top=0.82, bottom=0.12)
    vertical_stem = MAIN_DIR / "figure_private_scenario_reference_reuse_vertical"
    fig.savefig(vertical_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(vertical_stem.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(vertical_stem.with_suffix(".pdf"))
    print(vertical_stem.with_suffix(".png"))
    save_individual_panel(
        "figure_conformance_gap_only",
        draw_conformance_gap,
        tier,
        width=3.6,
        legend_handles=gap_legend_handles(),
        legend_columnspacing=1.05,
        draw_kwargs={"show_xlabel": False},
    )
    make_gap_model_capability_figure(tier, model_tier)


if __name__ == "__main__":
    main()
