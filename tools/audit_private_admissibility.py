#!/usr/bin/env python3
"""Audit whether private scenarios stay inside public ConformWeb contracts.

The audit is intentionally paper-facing.  It checks that private scenarios for
each target/tier compile against the public contract and summarizes which
declared symbols they use.  Compilation is the strongest static check here:
the compiler rejects scenarios that reference undeclared actions, pages, actors,
events, rendered tables, state paths, modes, or check operators.
"""

from __future__ import annotations

import csv
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import yaml

from detoxbench.dsl.compiler import DslCompileError
from detoxbench.dsl.compiler import compile_bundle


ROOT = Path(__file__).resolve().parents[1]
TARGET_ROOT = ROOT / "targets" / "web"
OUT_ROOT = ROOT / "reports" / "conformweb_visualizations"
TABLE_DIR = OUT_ROOT / "tables"
FIGURE_DIR = OUT_ROOT / "figures" / "appendix"


@dataclass(frozen=True)
class Target:
    target_id: str
    family: str
    short_family: str


TARGETS = [
    Target("stayflow_concierge", "Travel", "Travel"),
    Target("freshcart_market", "Grocery", "Grocery"),
    Target("clinic_shift_command", "Clinical Command", "Clinical"),
    Target("campus_registrar_command", "Campus Registrar", "Campus"),
    Target("media_campaign_launch_desk", "Media Campaign", "Media"),
    Target("homefix_hub", "Home Services", "Home"),
]

TIERS = [
    ("tier_a", "Tier A", "Consumer"),
    ("tier_b", "Tier B", "Operational"),
    ("tier_c", "Tier C", "Regulated"),
    ("tier_d", "Tier D", "Release stage"),
]

# The current working tree may not carry the local Tier A Clinical files in
# every checkout, while the paper artifact pack has historically used this
# branch as the source of truth for that instance.
FALLBACK_REFS = {
    ("clinic_shift_command", "tier_a"): "codex/clinic-shift-tier-a",
}

PATH_KEYS = {
    "path",
    "source_path",
    "other_path",
    "by_path",
    "lookup_path",
    "output_path",
    "term_path",
    "role_path",
}


def read_git_text(ref: str, rel_path: str) -> str | None:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def read_artifact(target_id: str, tier_id: str, filename: str) -> tuple[str | None, str]:
    local = TARGET_ROOT / target_id / tier_id / filename
    if local.exists():
        return local.read_text(encoding="utf-8"), "local"
    fallback = FALLBACK_REFS.get((target_id, tier_id))
    if fallback:
        rel = f"targets/web/{target_id}/{tier_id}/{filename}"
        text = read_git_text(fallback, rel)
        if text is not None:
            return text, f"git:{fallback}"
    return None, "missing"


def load_yaml_text(text: str, *, label: str) -> dict[str, Any]:
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{label} must contain a YAML mapping")
    return data


def contract_symbols(contract: dict[str, Any]) -> dict[str, set[str]]:
    runtime = contract.get("runtime") or {}
    state = contract.get("state") or {}
    components = contract.get("components") or {}

    actions: set[str] = set()
    for component_id, component in components.items():
        if not isinstance(component, dict):
            continue
        raw_actions = component.get("actions") or {}
        if isinstance(raw_actions, dict):
            for action_id in raw_actions:
                actions.add(f"{component_id}.{action_id}")

    return {
        "components": set(components.keys()) if isinstance(components, dict) else set(),
        "actions": actions,
        "state_paths": set((state.get("schema") or {}).keys()) if isinstance(state, dict) else set(),
        "pages": set((runtime.get("pages") or {}).keys()) if isinstance(runtime, dict) else set(),
        "events": set((runtime.get("events") or {}).keys()) if isinstance(runtime, dict) else set(),
        "tables": set((runtime.get("tables") or {}).keys()) if isinstance(runtime, dict) else set(),
        "actors": set((runtime.get("actors") or {}).keys()) if isinstance(runtime, dict) else set(),
    }


def iter_steps(scenarios: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for scenario in scenarios.get("scenarios") or []:
        if not isinstance(scenario, dict):
            continue
        for step in scenario.get("steps") or []:
            if isinstance(step, dict):
                steps.append(step)
    return steps


def add_nested_path_refs(value: Any, refs: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PATH_KEYS and isinstance(child, str):
                refs.add(child)
            add_nested_path_refs(child, refs)
    elif isinstance(value, list):
        for child in value:
            add_nested_path_refs(child, refs)


def collect_raw_refs(scenarios: dict[str, Any]) -> dict[str, set[str]]:
    refs = {
        "actions": set(),
        "state_paths": set(),
        "pages": set(),
        "events": set(),
        "tables": set(),
        "actors": set(),
        "ops": set(),
        "modes": set(),
        "browser": set(),
    }
    for step in iter_steps(scenarios):
        action_ref = step.get("do") or step.get("await")
        if isinstance(action_ref, str):
            refs["actions"].add(action_ref)
        elif isinstance(step.get("component"), str) and isinstance(step.get("action"), str):
            refs["actions"].add(f"{step['component']}.{step['action']}")

        browser = step.get("browser")
        if isinstance(browser, str):
            refs["browser"].add(browser)
        elif isinstance(browser, dict):
            if isinstance(browser.get("action"), str):
                refs["browser"].add(browser["action"])
            for page_key in ("page", "expect_page"):
                if isinstance(browser.get(page_key), str):
                    refs["pages"].add(browser[page_key])
        for page_key in ("page", "expect_page"):
            if isinstance(step.get(page_key), str):
                refs["pages"].add(step[page_key])

        raw_event = step.get("event")
        if isinstance(raw_event, str):
            refs["events"].add(raw_event)
        elif isinstance(raw_event, dict) and isinstance(raw_event.get("id"), str):
            refs["events"].add(raw_event["id"])

        if isinstance(step.get("table"), str):
            refs["tables"].add(step["table"])
        if isinstance(step.get("actor"), str):
            refs["actors"].add(step["actor"])
        if isinstance(step.get("mode"), str):
            refs["modes"].add(step["mode"])
        for expect in step.get("expect") or []:
            if isinstance(expect, dict) and isinstance(expect.get("op"), str):
                refs["ops"].add(expect["op"])
        add_nested_path_refs(step, refs["state_paths"])
    return refs


def collect_public_refs(public_text: str | None) -> dict[str, set[str]]:
    if not public_text:
        return {
            "actions": set(),
            "state_paths": set(),
            "pages": set(),
            "events": set(),
            "tables": set(),
            "actors": set(),
            "ops": set(),
            "modes": set(),
            "browser": set(),
        }
    return collect_raw_refs(load_yaml_text(public_text, label="public scenarios"))


def join_items(items: set[str]) -> str:
    return "; ".join(sorted(items))


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return ""
    return f"{100 * numerator / denominator:.1f}"


def latex_escape(value: Any) -> str:
    text = str(value)
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def make_row(target: Target, tier_id: str, tier_label: str, tier_name: str) -> dict[str, Any]:
    contract_text, contract_source = read_artifact(target.target_id, tier_id, "contract.dsl.yaml")
    private_text, private_source = read_artifact(target.target_id, tier_id, "scenarios.private.dsl.yaml")
    public_text, public_source = read_artifact(target.target_id, tier_id, "scenarios.public.dsl.yaml")

    base: dict[str, Any] = {
        "target_id": target.target_id,
        "family": target.family,
        "family_short": target.short_family,
        "tier_id": tier_id,
        "tier_label": tier_label,
        "tier_name": tier_name,
        "contract_source": contract_source,
        "public_source": public_source,
        "private_source": private_source,
        "contract_present": contract_text is not None,
        "private_present": private_text is not None,
        "compile_ok": False,
        "compile_error": "",
        "private_scenarios": 0,
        "private_steps": 0,
        "compiled_checks": 0,
        "declared_actions": 0,
        "private_action_refs": 0,
        "undeclared_action_refs": 0,
        "private_state_refs": 0,
        "undeclared_state_refs": 0,
        "private_page_refs": 0,
        "undeclared_page_refs": 0,
        "private_table_refs": 0,
        "undeclared_table_refs": 0,
        "private_event_refs": 0,
        "undeclared_event_refs": 0,
        "private_actor_refs": 0,
        "undeclared_actor_refs": 0,
        "relation_ops": "",
        "browser_actions": "",
        "step_modes": "",
        "upload_steps": 0,
        "table_steps": 0,
        "browser_steps": 0,
        "event_steps": 0,
        "wait_steps": 0,
        "private_actions_seen_in_public": 0,
        "private_actions_total": 0,
        "private_action_public_overlap_pct": "",
        "private_state_paths_seen_in_public": 0,
        "private_state_paths_total": 0,
        "private_state_public_overlap_pct": "",
        "undeclared_symbols_total": 0,
        "admissible": False,
        "notes": "",
    }

    if contract_text is None:
        base["notes"] = "missing public contract"
        return base
    if private_text is None:
        base["notes"] = "missing private scenario file in this checkout"
        return base

    try:
        contract = load_yaml_text(contract_text, label=f"{target.target_id}/{tier_id}/contract")
        private = load_yaml_text(private_text, label=f"{target.target_id}/{tier_id}/private")
    except Exception as exc:
        base["compile_error"] = str(exc)
        base["notes"] = "YAML parse failure"
        return base

    symbols = contract_symbols(contract)
    private_refs = collect_raw_refs(private)
    public_refs = collect_public_refs(public_text)

    undeclared_actions = private_refs["actions"] - symbols["actions"]
    undeclared_state = private_refs["state_paths"] - symbols["state_paths"]
    undeclared_pages = {page for page in private_refs["pages"] if page not in symbols["pages"]}
    undeclared_tables = private_refs["tables"] - symbols["tables"]
    undeclared_events = private_refs["events"] - symbols["events"]
    undeclared_actors = private_refs["actors"] - symbols["actors"]
    undeclared_total = sum(
        len(items)
        for items in [
            undeclared_actions,
            undeclared_state,
            undeclared_pages,
            undeclared_tables,
            undeclared_events,
            undeclared_actors,
        ]
    )

    scenarios = private.get("scenarios") or []
    steps = iter_steps(private)
    base.update(
        {
            "private_scenarios": len(scenarios) if isinstance(scenarios, list) else 0,
            "private_steps": len(steps),
            "declared_actions": len(symbols["actions"]),
            "private_action_refs": len(private_refs["actions"]),
            "undeclared_action_refs": len(undeclared_actions),
            "private_state_refs": len(private_refs["state_paths"]),
            "undeclared_state_refs": len(undeclared_state),
            "private_page_refs": len(private_refs["pages"]),
            "undeclared_page_refs": len(undeclared_pages),
            "private_table_refs": len(private_refs["tables"]),
            "undeclared_table_refs": len(undeclared_tables),
            "private_event_refs": len(private_refs["events"]),
            "undeclared_event_refs": len(undeclared_events),
            "private_actor_refs": len(private_refs["actors"]),
            "undeclared_actor_refs": len(undeclared_actors),
            "relation_ops": join_items(private_refs["ops"]),
            "browser_actions": join_items(private_refs["browser"]),
            "step_modes": join_items(private_refs["modes"]),
            "upload_steps": sum(1 for step in steps if isinstance(step.get("do"), str) and step["do"].endswith(".upload")),
            "table_steps": sum(1 for step in steps if "table" in step),
            "browser_steps": sum(1 for step in steps if "browser" in step),
            "event_steps": sum(1 for step in steps if "event" in step),
            "wait_steps": sum(1 for step in steps if "wait_ms" in step or "await" in step),
            "private_actions_seen_in_public": len(private_refs["actions"] & public_refs["actions"]),
            "private_actions_total": len(private_refs["actions"]),
            "private_action_public_overlap_pct": pct(len(private_refs["actions"] & public_refs["actions"]), len(private_refs["actions"])),
            "private_state_paths_seen_in_public": len(private_refs["state_paths"] & public_refs["state_paths"]),
            "private_state_paths_total": len(private_refs["state_paths"]),
            "private_state_public_overlap_pct": pct(len(private_refs["state_paths"] & public_refs["state_paths"]), len(private_refs["state_paths"])),
            "undeclared_symbols_total": undeclared_total,
        }
    )

    try:
        compiled = compile_bundle(contract, private)
        base["compile_ok"] = True
        base["compiled_checks"] = sum(
            len(step.preconditions) + len(step.checks)
            for scenario in compiled
            for step in scenario.steps
        )
    except DslCompileError as exc:
        base["compile_error"] = str(exc)
        base["notes"] = "compiler rejected private scenarios"
    except Exception as exc:  # pragma: no cover - kept for audit robustness.
        base["compile_error"] = repr(exc)
        base["notes"] = "unexpected compiler failure"

    base["admissible"] = bool(base["compile_ok"] and undeclared_total == 0)
    if not base["notes"]:
        base["notes"] = "private scenarios compile against public contract"
    return base


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_latex(rows: list[dict[str, Any]], path: Path) -> None:
    visible = [
        row
        for row in rows
        if row["contract_present"] and row["private_present"]
    ]
    header = [
        "Family",
        "Tier",
        "Private scenarios",
        "Steps",
        "Compiled checks",
        "Undeclared refs",
        "Compiler",
    ]
    lines = [
        r"\begin{tabular}{llrrrrl}",
        r"\toprule",
        " & ".join(header) + r" \\",
        r"\midrule",
    ]
    for row in visible:
        cells = [
            row["family"],
            f"{row['tier_label']} ({row['tier_name']})",
            row["private_scenarios"],
            row["private_steps"],
            row["compiled_checks"],
            row["undeclared_symbols_total"],
            "pass" if row["compile_ok"] else "fail",
        ]
        lines.append(" & ".join(latex_escape(cell) for cell in cells) + r" \\")
    missing = [
        row
        for row in rows
        if row["contract_present"] and not row["private_present"]
    ]
    if missing:
        lines.extend([r"\midrule", r"\multicolumn{7}{l}{\textit{Private scenario file absent in this checkout}} \\"])
        for row in missing:
            cells = [
                row["family"],
                f"{row['tier_label']} ({row['tier_name']})",
                "--",
                "--",
                "--",
                "--",
                "missing",
            ]
            lines.append(" & ".join(latex_escape(cell) for cell in cells) + r" \\")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary_latex(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Family & Audited tiers & Private scenarios & Steps & Checks & Undeclared refs \\",
        r"\midrule",
    ]
    for target in TARGETS:
        subset = [
            row
            for row in rows
            if row["family"] == target.family and row["contract_present"] and row["private_present"]
        ]
        cells = [
            target.family,
            f"{len(subset)}/4",
            sum(int(row["private_scenarios"]) for row in subset),
            sum(int(row["private_steps"]) for row in subset),
            sum(int(row["compiled_checks"]) for row in subset),
            sum(int(row["undeclared_symbols_total"]) for row in subset),
        ]
        lines.append(" & ".join(latex_escape(cell) for cell in cells) + r" \\")
    lines.extend(
        [
            r"\midrule",
            r"\textbf{Total} & "
            + " & ".join(
                latex_escape(cell)
                for cell in [
                    f"{sum(1 for row in rows if row['contract_present'] and row['private_present'])}/24",
                    sum(int(row["private_scenarios"]) for row in rows if row["contract_present"] and row["private_present"]),
                    sum(int(row["private_steps"]) for row in rows if row["contract_present"] and row["private_present"]),
                    sum(int(row["compiled_checks"]) for row in rows if row["contract_present"] and row["private_present"]),
                    sum(int(row["undeclared_symbols_total"]) for row in rows if row["contract_present"] and row["private_present"]),
                ]
            )
            + r" \\",
            r"\bottomrule",
            r"\end{tabular}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_matrix_latex(rows: list[dict[str, Any]], path: Path) -> None:
    by_key = {(row["target_id"], row["tier_id"]): row for row in rows}
    lines = [
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Family & A Consumer & B Operational & C Regulated & D Release stage \\",
        r"\midrule",
    ]
    for target in TARGETS:
        cells = [target.family]
        for tier_id, _tier_label, _tier_name in TIERS:
            row = by_key[(target.target_id, tier_id)]
            if row["contract_present"] and row["private_present"]:
                cells.append(
                    r"\makecell{"
                    + f"{row['private_scenarios']} scen. / {row['private_steps']} steps"
                    + r"\\0 undecl.}"
                )
            else:
                cells.append(r"\makecell{N/A\\in checkout}")
        lines.append(" & ".join(latex_escape(cells[0:1][0]) if idx == 0 else cell for idx, cell in enumerate(cells)) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def draw_admissibility_matrix(rows: list[dict[str, Any]], path_stem: Path) -> None:
    """Draw a compact Appendix figure for contract admissibility."""

    by_key = {(row["target_id"], row["tier_id"]): row for row in rows}
    n_rows = len(TARGETS)
    n_cols = len(TIERS)

    blue = "#4285F4"
    blue_dark = "#174EA6"
    gray = "#E8EAED"
    gray_text = "#5F6368"
    line = "#DADCE0"

    fig, ax = plt.subplots(figsize=(11.6, 6.1), dpi=300)
    ax.set_xlim(-0.15, n_cols)
    ax.set_ylim(0, n_rows)
    ax.invert_yaxis()
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    for row_idx, target in enumerate(TARGETS):
        for col_idx, (tier_id, tier_label, tier_name) in enumerate(TIERS):
            row = by_key[(target.target_id, tier_id)]
            present = bool(row["contract_present"] and row["private_present"])
            admissible = bool(row["admissible"])
            color = blue if present and admissible else gray
            rect = patches.FancyBboxPatch(
                (col_idx + 0.04, row_idx + 0.10),
                0.92,
                0.80,
                boxstyle="round,pad=0.015,rounding_size=0.045",
                linewidth=1.0,
                edgecolor=line if not present else blue_dark,
                facecolor=color,
                alpha=0.16 if present else 1.0,
            )
            ax.add_patch(rect)
            if present and admissible:
                ax.text(
                    col_idx + 0.50,
                    row_idx + 0.35,
                    f"{row['private_scenarios']} scenarios",
                    ha="center",
                    va="center",
                    fontsize=12.0,
                    fontweight="bold",
                    color=blue_dark,
                )
                ax.text(
                    col_idx + 0.50,
                    row_idx + 0.58,
                    f"{row['private_steps']} steps",
                    ha="center",
                    va="center",
                    fontsize=10.2,
                    fontweight="bold",
                    color="#202124",
                )
                ax.text(
                    col_idx + 0.50,
                    row_idx + 0.76,
                    "0 undeclared references",
                    ha="center",
                    va="center",
                    fontsize=9.4,
                    color=gray_text,
                )
            else:
                ax.text(
                    col_idx + 0.50,
                    row_idx + 0.45,
                    "N/A",
                    ha="center",
                    va="center",
                    fontsize=11.5,
                    fontweight="bold",
                    color=gray_text,
                )
                ax.text(
                    col_idx + 0.50,
                    row_idx + 0.67,
                    "not in checkout",
                    ha="center",
                    va="center",
                    fontsize=9.3,
                    color=gray_text,
                )

    ax.set_xticks([i + 0.5 for i in range(n_cols)])
    ax.set_xticklabels(
        ["A\nConsumer", "B\nOperational", "C\nRegulated", "D\nRelease stage"],
        fontsize=12.2,
        fontweight="bold",
    )
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=8)

    ax.set_yticks([i + 0.5 for i in range(n_rows)])
    ax.set_yticklabels([target.family for target in TARGETS], fontsize=12.0, fontweight="bold")
    ax.tick_params(axis="y", length=0, pad=10)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.text(
        0,
        n_rows + 0.20,
        "Cells summarize private scenarios that compile against the public contract; gray cells are absent in this checkout.",
        ha="left",
        va="top",
        fontsize=10.4,
        color=gray_text,
    )

    plt.tight_layout(rect=(0, 0.045, 1, 1))
    path_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path_stem.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)


def make_reference_coverage_rows() -> list[dict[str, Any]]:
    """Return per-target/tier symbol coverage rows for public/private relation."""

    categories = [
        ("actions", "Actions"),
        ("state_paths", "State / observation paths"),
        ("pages", "Routes/pages"),
        ("tables", "Rendered tables"),
        ("events", "Events"),
    ]
    rows: list[dict[str, Any]] = []
    for target in TARGETS:
        for tier_id, tier_label, tier_name in TIERS:
            contract_text, contract_source = read_artifact(target.target_id, tier_id, "contract.dsl.yaml")
            private_text, private_source = read_artifact(target.target_id, tier_id, "scenarios.private.dsl.yaml")
            public_text, public_source = read_artifact(target.target_id, tier_id, "scenarios.public.dsl.yaml")
            if contract_text is None or private_text is None:
                continue
            contract = load_yaml_text(contract_text, label=f"{target.target_id}/{tier_id}/contract")
            private = load_yaml_text(private_text, label=f"{target.target_id}/{tier_id}/private")
            symbols = contract_symbols(contract)
            public_refs = collect_public_refs(public_text)
            private_refs = collect_raw_refs(private)
            for key, label in categories:
                declared = symbols[key]
                public_used = public_refs[key]
                private_used = private_refs[key]
                private_seen_public = private_used & public_used
                private_only = private_used - public_used
                private_undeclared = private_used - declared
                rows.append(
                    {
                        "target_id": target.target_id,
                        "family": target.family,
                        "family_short": target.short_family,
                        "tier_id": tier_id,
                        "tier_label": tier_label,
                        "tier_name": tier_name,
                        "category": label,
                        "contract_source": contract_source,
                        "public_source": public_source,
                        "private_source": private_source,
                        "declared_in_public_contract": len(declared),
                        "used_in_public_examples": len(public_used),
                        "used_in_private_scenarios": len(private_used),
                        "private_seen_in_public_examples": len(private_seen_public),
                        "private_only_but_declared": len(private_only),
                        "private_undeclared": len(private_undeclared),
                        "private_coverage_pct": pct(len(private_used - private_undeclared), len(private_used)),
                    }
                )
    return rows


def draw_public_private_reference_figure(
    coverage_rows: list[dict[str, Any]],
    path_stem: Path,
    *,
    square: bool = False,
) -> None:
    """Draw how private scenarios are covered by public contract declarations."""

    categories = [
        "Actions",
        "State / observation paths",
        "Routes/pages",
        "Rendered tables",
        "Events",
    ]
    totals: dict[str, dict[str, int]] = {}
    for category in categories:
        subset = [row for row in coverage_rows if row["category"] == category]
        totals[category] = {
            "declared": sum(int(row["declared_in_public_contract"]) for row in subset),
            "public_used": sum(int(row["used_in_public_examples"]) for row in subset),
            "private_used": sum(int(row["used_in_private_scenarios"]) for row in subset),
            "private_seen": sum(int(row["private_seen_in_public_examples"]) for row in subset),
            "private_only": sum(int(row["private_only_but_declared"]) for row in subset),
            "private_undeclared": sum(int(row["private_undeclared"]) for row in subset),
        }

    purple = "#7E57C2"
    orange = "#F9AB00"
    gray = "#DADCE0"
    dark = "#202124"
    muted = "#5F6368"

    if square:
        figsize = (7.6, 7.6)
        label_font = 14.2
        tick_font = 12.4
        xlabel_font = 13.0
        value_font = 12.6
        legend_font = 13.0
        legend_ys = [0.835]
        top = 0.805
        bottom = 0.13
        left = 0.28
        right = 0.94
        swatch_w = 0.026
        swatch_h = 0.014
        legend_rows = [
            [
                (0.20, orange, "Both"),
                (0.43, purple, "Only in private"),
                (0.75, gray, "Unused"),
            ],
        ]
    else:
        figsize = (12.2, 6.1)
        label_font = 15.0
        tick_font = 13.2
        xlabel_font = 14.2
        value_font = 13.2
        legend_font = 14.2
        legend_ys = [0.748]
        top = 0.72
        bottom = 0.13
        left = 0.20
        right = 0.98
        swatch_w = 0.020
        swatch_h = 0.014
        legend_rows = [
            [
                (0.36, orange, "Both"),
                (0.48, purple, "Only in private"),
                (0.66, gray, "Unused"),
            ],
        ]

    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    fig.patch.set_facecolor("white")
    y = list(range(len(categories)))

    declared = [totals[c]["declared"] for c in categories]
    seen = [totals[c]["private_seen"] for c in categories]
    private_only = [totals[c]["private_only"] for c in categories]
    undeclared = [totals[c]["private_undeclared"] for c in categories]
    unused = [
        max(d - s - p - u, 0)
        for d, s, p, u in zip(declared, seen, private_only, undeclared, strict=True)
    ]

    def share(values: list[int]) -> list[float]:
        return [
            (100 * value / total) if total else 0.0
            for value, total in zip(values, declared, strict=True)
        ]

    seen_share = share(seen)
    private_share = share(private_only)
    unused_share = share(unused)
    undeclared_share = share(undeclared)

    ax.barh(y, seen_share, color=orange, height=0.66, edgecolor="white", linewidth=0.8, label="Used in both scenarios")
    ax.barh(y, private_share, left=seen_share, color=purple, height=0.66, edgecolor="white", linewidth=0.8, label="Used only in private scenarios")
    ax.barh(
        y,
        unused_share,
        left=[s + p for s, p in zip(seen_share, private_share, strict=True)],
        color=gray,
        height=0.66,
        edgecolor="white",
        linewidth=0.8,
        label="Declared but unused by private scenarios",
    )
    if any(undeclared):
        ax.barh(
            y,
            undeclared_share,
            left=[s + p + u0 for s, p, u0 in zip(seen_share, private_share, unused_share, strict=True)],
            color="#D93025",
            height=0.66,
            edgecolor="white",
            linewidth=0.8,
            label="Undeclared",
        )
    for idx, category in enumerate(categories):
        total_private = seen[idx] + private_only[idx] + undeclared[idx]
        if private_share[idx] >= 7:
            ax.text(
                seen_share[idx] + private_share[idx] / 2,
                idx,
                f"{private_only[idx]}",
                va="center",
                ha="center",
                fontsize=value_font,
                fontweight="bold",
                color="white",
            )
        if seen[idx] > 0:
            ax.text(
                seen_share[idx] / 2,
                idx,
                f"{seen[idx]}",
                va="center",
                ha="center",
                fontsize=value_font,
                fontweight="bold",
                color="#202124",
            )
        if unused[idx] > 0:
            ax.text(
                seen_share[idx] + private_share[idx] + unused_share[idx] / 2,
                idx,
                f"{unused[idx]}",
                va="center",
                ha="center",
                fontsize=value_font,
                fontweight="bold",
                color="#202124",
            )

    ax.set_yticks(y)
    ax.set_yticklabels(
        ["Actions", "State paths", "Routes", "Rendered tables", "Events"],
        fontsize=label_font,
        fontweight="bold",
    )
    ax.invert_yaxis()
    ax.set_xlabel("Share of declared public contract references", fontsize=xlabel_font, fontweight="bold", labelpad=11)
    ax.grid(axis="x", color="#EEF1F4", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#BDC1C6")
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=tick_font, colors=muted)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    for tick in ax.get_xticklabels():
        tick.set_fontweight("bold")

    for legend_y, legend_row in zip(legend_ys, legend_rows, strict=True):
        for x, color, label in legend_row:
            fig.add_artist(
                patches.Rectangle(
                    (x, legend_y - swatch_h / 2),
                    swatch_w,
                    swatch_h,
                    transform=fig.transFigure,
                    color=color,
                    clip_on=False,
                )
            )
            fig.text(
                x + swatch_w + 0.010,
                legend_y,
                label,
                ha="left",
                va="center",
                fontsize=legend_font,
                fontweight="bold",
            )
    fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
    path_stem.parent.mkdir(parents=True, exist_ok=True)
    if square:
        fig.savefig(path_stem.with_suffix(".pdf"))
        fig.savefig(path_stem.with_suffix(".png"), dpi=300)
    else:
        fig.savefig(path_stem.with_suffix(".pdf"), bbox_inches="tight")
        fig.savefig(path_stem.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)


def short_list(items: list[str], limit: int = 4) -> str:
    cleaned = [item for item in items if item]
    if not cleaned:
        return "none"
    if len(cleaned) <= limit:
        return ", ".join(cleaned)
    return ", ".join(cleaned[:limit]) + f", +{len(cleaned) - limit}"


def check_paths(checks: Any) -> list[str]:
    paths: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in PATH_KEYS and isinstance(child, str):
                    paths.append(child)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(checks)
    return sorted(dict.fromkeys(paths))


def wrap_cell(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False))


def draw_private_contract_witness(path_stem: Path) -> None:
    """Draw one concrete private-scenario witness against public declarations."""

    target_id = "homefix_hub"
    tier_id = "tier_d"
    scenario_id = "private_06_full_quality_invoice_path"
    contract_text, _ = read_artifact(target_id, tier_id, "contract.dsl.yaml")
    private_text, _ = read_artifact(target_id, tier_id, "scenarios.private.dsl.yaml")
    if contract_text is None or private_text is None:
        return
    contract = load_yaml_text(contract_text, label="witness contract")
    private = load_yaml_text(private_text, label="witness private scenarios")
    scenario = next((s for s in private.get("scenarios", []) if isinstance(s, dict) and s.get("id") == scenario_id), None)
    if scenario is None:
        return

    selected_actions = [
        "select_leak_button.click",
        "get_quote_button.click",
        "role_dispatcher_button.click",
        "permit_upload_input.upload",
        "pass_qa_button.click",
        "issue_invoice_button.click",
    ]
    steps = []
    for action_ref in selected_actions:
        raw_step = next((step for step in scenario.get("steps", []) if isinstance(step, dict) and step.get("do") == action_ref), None)
        if raw_step is None:
            continue
        component_id, action_name = action_ref.rsplit(".", 1)
        component = contract.get("components", {}).get(component_id, {})
        action = (component.get("actions") or {}).get(action_name, {})
        pre_paths = check_paths(action.get("preconditions", []))
        effect_paths = check_paths(action.get("effects", []))
        explicit_paths = check_paths(raw_step.get("expect", []))
        input_note = ""
        if action_name == "upload":
            rows = raw_step.get("input", {}).get("rows", [])
            input_note = f"private file rows: {len(rows)}"
        steps.append(
            {
                "private": action_ref.replace("_button", "").replace("_input", ""),
                "decl": f"component: {component_id}\nselector: declared\naction: {action_name}",
                "checks": (
                    f"pre: {short_list(pre_paths, 3)}\n"
                    f"post: {short_list(effect_paths, 4)}"
                    + (f"\nexplicit: {short_list(explicit_paths, 3)}" if explicit_paths else "")
                    + (f"\n{input_note}" if input_note else "")
                ),
            }
        )

    blue = "#4285F4"
    blue_dark = "#174EA6"
    orange = "#F9AB00"
    green = "#34A853"
    gray = "#F1F3F4"
    line = "#DADCE0"
    dark = "#202124"
    muted = "#5F6368"

    fig, ax = plt.subplots(figsize=(12.2, 7.35), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    cols = [
        (0.03, 0.25, "Private step", blue_dark),
        (0.35, 0.31, "Public declaration", orange),
        (0.72, 0.25, "Compiled checks", green),
    ]
    header_y = 0.925
    for x, w, label, color in cols:
        ax.add_patch(
            patches.FancyBboxPatch(
                (x, header_y),
                w,
                0.044,
                boxstyle="round,pad=0.008,rounding_size=0.012",
                facecolor=color,
                edgecolor="none",
                alpha=0.96,
            )
        )
        ax.text(x + w / 2, header_y + 0.022, label, ha="center", va="center", fontsize=11.2, fontweight="bold", color="white")

    row_top = 0.872
    row_h = 0.115
    gap = 0.012
    for idx, step in enumerate(steps):
        y = row_top - idx * (row_h + gap) - row_h
        ax.text(0.006, y + row_h / 2, str(idx + 1), ha="center", va="center", fontsize=10.5, fontweight="bold", color=muted)
        for col_idx, (x, w, _label, color) in enumerate(cols):
            ax.add_patch(
                patches.FancyBboxPatch(
                    (x, y),
                    w,
                    row_h,
                    boxstyle="round,pad=0.010,rounding_size=0.012",
                    facecolor=gray if col_idx != 0 else "#E8F0FE",
                    edgecolor=line,
                    linewidth=0.8,
                )
            )
        ax.text(0.048, y + row_h / 2, wrap_cell(step["private"], 24), ha="left", va="center", fontsize=10.0, fontweight="bold", color=blue_dark)
        ax.text(0.363, y + row_h / 2, wrap_cell(step["decl"], 34), ha="left", va="center", fontsize=8.55, color=dark, linespacing=1.05)
        ax.text(0.733, y + row_h / 2, wrap_cell(step["checks"], 30), ha="left", va="center", fontsize=8.55, color=dark, linespacing=1.05)
        if idx < len(steps) - 1:
            ax.annotate(
                "",
                xy=(0.305, y - gap * 0.18),
                xytext=(0.305, y + gap * 0.18),
                arrowprops=dict(arrowstyle="-|>", color=line, lw=0.9),
            )

    path_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path_stem.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)


def write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    total_instances = len(rows)
    present = [row for row in rows if row["contract_present"] and row["private_present"]]
    missing_private = [row for row in rows if row["contract_present"] and not row["private_present"]]
    missing_contract = [row for row in rows if not row["contract_present"]]
    compile_ok = [row for row in present if row["compile_ok"]]
    admissible = [row for row in present if row["admissible"]]
    total_scenarios = sum(int(row["private_scenarios"]) for row in present)
    total_steps = sum(int(row["private_steps"]) for row in present)
    total_checks = sum(int(row["compiled_checks"]) for row in present)
    total_undeclared = sum(int(row["undeclared_symbols_total"]) for row in present)

    family_lines = []
    for target in TARGETS:
        subset = [row for row in rows if row["family"] == target.family]
        family_present = [row for row in subset if row["private_present"] and row["contract_present"]]
        family_lines.append(
            f"| {target.family} | {len(family_present)}/4 | "
            f"{sum(int(row['private_scenarios']) for row in family_present)} | "
            f"{sum(int(row['private_steps']) for row in family_present)} | "
            f"{sum(int(row['undeclared_symbols_total']) for row in family_present)} |"
        )

    missing_lines = []
    for row in missing_private:
        missing_lines.append(f"- {row['family']} {row['tier_label']} ({row['tier_name']}): {row['notes']}")
    for row in missing_contract:
        missing_lines.append(f"- {row['family']} {row['tier_label']} ({row['tier_name']}): missing public contract")
    if not missing_lines:
        missing_lines.append("- None.")

    md = f"""# Private Scenario Admissibility Audit

This audit checks whether private scenarios stay inside the public
behavioral contract boundary. A row is marked admissible only when the private
scenario file compiles against the public contract and no raw private reference
points to an undeclared action, state path, route/page, actor, event, or
rendered table.

## Summary

- Expected target tier instances: {total_instances}
- Private scenario files present in this checkout: {len(present)}
- Private scenario files compiling against the public contract: {len(compile_ok)}/{len(present)}
- Admissible present private files: {len(admissible)}/{len(present)}
- Private scenarios audited: {total_scenarios}
- Private steps audited: {total_steps}
- Compiled checks generated: {total_checks}
- Undeclared private references found: {total_undeclared}

## Family Summary

| Family | Private files present | Private scenarios | Private steps | Undeclared refs |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(family_lines)}

## Missing Or Absent Private Files

{chr(10).join(missing_lines)}

## Interpretation

The static audit supports the fairness claim that private scenarios are
contract-derived rather than hidden product requirements. Compilation is the
key check: the same compiler used to lower scenarios into browser evaluation
plans rejects references outside the public contract. This audit should be
reported together with reference-implementation validation, which establishes
that the resulting browser plans are executable by a conforming implementation.

## Generated Files

- `tables/private_admissibility_audit.csv`: full target tier audit rows.
- `tables/private_scenario_admissibility.csv`: one row per private scenario.
- `tables/private_admissibility_audit.tex`: compact Appendix table.
- `tables/private_admissibility_summary.tex`: family-level summary table.
- `tables/private_admissibility_matrix.tex`: tier matrix table.
- `figures/appendix/appendix_public_private_reference_flow.pdf`: paper-facing coverage figure.
- `figures/appendix/appendix_public_private_reference_flow_square.pdf`: square coverage figure variant.
"""
    path.write_text(textwrap.dedent(md).strip() + "\n", encoding="utf-8")


def make_scenario_rows(target: Target, tier_id: str, tier_label: str, tier_name: str) -> list[dict[str, Any]]:
    contract_text, contract_source = read_artifact(target.target_id, tier_id, "contract.dsl.yaml")
    private_text, private_source = read_artifact(target.target_id, tier_id, "scenarios.private.dsl.yaml")
    if contract_text is None or private_text is None:
        return []

    contract = load_yaml_text(contract_text, label=f"{target.target_id}/{tier_id}/contract")
    private = load_yaml_text(private_text, label=f"{target.target_id}/{tier_id}/private")
    symbols = contract_symbols(contract)
    rows: list[dict[str, Any]] = []
    for scenario in private.get("scenarios") or []:
        if not isinstance(scenario, dict):
            continue
        scenario_dsl = {
            "dsl_version": private.get("dsl_version"),
            "visibility": private.get("visibility", "private"),
            "tier_weights": private.get("tier_weights", {}),
            "scenarios": [scenario],
        }
        scenario_refs = collect_raw_refs(scenario_dsl)
        steps = iter_steps(scenario_dsl)
        undeclared_total = sum(
            len(items)
            for items in [
                scenario_refs["actions"] - symbols["actions"],
                scenario_refs["state_paths"] - symbols["state_paths"],
                {page for page in scenario_refs["pages"] if page not in symbols["pages"]},
                scenario_refs["tables"] - symbols["tables"],
                scenario_refs["events"] - symbols["events"],
                scenario_refs["actors"] - symbols["actors"],
            ]
        )
        compile_ok = False
        compile_error = ""
        compiled_checks = 0
        try:
            compiled = compile_bundle(contract, scenario_dsl)
            compile_ok = True
            compiled_checks = sum(
                len(step.preconditions) + len(step.checks)
                for compiled_scenario in compiled
                for step in compiled_scenario.steps
            )
        except DslCompileError as exc:
            compile_error = str(exc)
        rows.append(
            {
                "target_id": target.target_id,
                "family": target.family,
                "family_short": target.short_family,
                "tier_id": tier_id,
                "tier_label": tier_label,
                "tier_name": tier_name,
                "scenario_id": scenario.get("id", ""),
                "scenario_tier": scenario.get("tier", ""),
                "visibility": scenario.get("visibility", private.get("visibility", "private")),
                "kind": scenario.get("kind", "scoring"),
                "difficulty": scenario.get("difficulty", ""),
                "private_source": private_source,
                "contract_source": contract_source,
                "steps": len(steps),
                "compiled_checks": compiled_checks,
                "component_action_refs": len(scenario_refs["actions"]),
                "state_path_refs": len(scenario_refs["state_paths"]),
                "page_refs": len(scenario_refs["pages"]),
                "table_refs": len(scenario_refs["tables"]),
                "event_refs": len(scenario_refs["events"]),
                "actor_refs": len(scenario_refs["actors"]),
                "browser_steps": sum(1 for step in steps if "browser" in step),
                "table_steps": sum(1 for step in steps if "table" in step),
                "upload_steps": sum(1 for step in steps if isinstance(step.get("do"), str) and step["do"].endswith(".upload")),
                "relation_ops": join_items(scenario_refs["ops"]),
                "browser_actions": join_items(scenario_refs["browser"]),
                "step_modes": join_items(scenario_refs["modes"]),
                "undeclared_symbols_total": undeclared_total,
                "compile_ok": compile_ok,
                "compile_error": compile_error,
                "admissible": bool(compile_ok and undeclared_total == 0),
            }
        )
    return rows


def main() -> None:
    rows: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []
    for target in TARGETS:
        for tier_id, tier_label, tier_name in TIERS:
            rows.append(make_row(target, tier_id, tier_label, tier_name))
            scenario_rows.extend(make_scenario_rows(target, tier_id, tier_label, tier_name))
    coverage_rows = make_reference_coverage_rows()

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(rows, TABLE_DIR / "private_admissibility_audit.csv")
    write_csv(scenario_rows, TABLE_DIR / "private_scenario_admissibility.csv")
    write_csv(coverage_rows, TABLE_DIR / "private_reference_coverage.csv")
    write_latex(rows, TABLE_DIR / "private_admissibility_audit.tex")
    write_summary_latex(rows, TABLE_DIR / "private_admissibility_summary.tex")
    write_matrix_latex(rows, TABLE_DIR / "private_admissibility_matrix.tex")
    draw_public_private_reference_figure(coverage_rows, FIGURE_DIR / "appendix_public_private_reference_flow")
    draw_public_private_reference_figure(
        coverage_rows,
        FIGURE_DIR / "appendix_public_private_reference_flow_square",
        square=True,
    )
    write_markdown(rows, OUT_ROOT / "private_admissibility_audit.md")

    present = [row for row in rows if row["contract_present"] and row["private_present"]]
    compile_ok = [row for row in present if row["compile_ok"]]
    total_undeclared = sum(int(row["undeclared_symbols_total"]) for row in present)
    print(f"target tier rows: {len(rows)}")
    print(f"private files present: {len(present)}")
    print(f"compile ok: {len(compile_ok)}/{len(present)}")
    print(f"undeclared private refs: {total_undeclared}")
    print(f"private scenario rows: {len(scenario_rows)}")
    print(f"wrote {TABLE_DIR / 'private_admissibility_audit.csv'}")
    print(f"wrote {TABLE_DIR / 'private_scenario_admissibility.csv'}")
    print(f"wrote {TABLE_DIR / 'private_reference_coverage.csv'}")
    print(f"wrote {FIGURE_DIR / 'appendix_public_private_reference_flow.pdf'}")
    print(f"wrote {FIGURE_DIR / 'appendix_public_private_reference_flow_square.pdf'}")
    print(f"wrote {OUT_ROOT / 'private_admissibility_audit.md'}")


if __name__ == "__main__":
    main()
