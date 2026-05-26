#!/usr/bin/env python3
"""Export ConformWeb evidence PDFs into editable PNG assets.

Outputs:
  - one representative screenshot PNG for every family x tier target
  - one before/after evidence PNG for every selected target-tier failure pair
  - contact sheets for quick human review
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import fitz
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "reports" / "conformweb_visualizations"
EVIDENCE_ROOT = OUT_ROOT / "evidence"
FIG_ROOT = OUT_ROOT / "figures"

REP_SRC = EVIDENCE_ROOT / "representative_screenshots"
FAIL_SRC = EVIDENCE_ROOT / "failure_pairs" / "current_raw"

REP_OUT = FIG_ROOT / "appendix" / "representative_screenshots"
FAIL_OUT = FIG_ROOT / "appendix" / "failure_evidence_by_tier"
REVIEW_OUT = FIG_ROOT / "review"
REP_ROW_OUT = REVIEW_OUT / "representative_rows"
FAIL_ROW_OUT = REVIEW_OUT / "failure_evidence_rows"
FAIL_COLUMN_OUT = REVIEW_OUT / "failure_evidence_columns"

FAMILY_ORDER = [
    "StayFlow Concierge",
    "FreshCart Market",
    "Clinic Shift Command",
    "Campus Registrar Command",
    "Media Campaign Launch Desk",
    "HomeFix Hub",
]
TIER_ORDER = ["A", "B", "C", "D"]
TIER_NAMES = {
    "A": "Consumer",
    "B": "Operational",
    "C": "Regulated",
    "D": "Release-stage",
}
FAILURE_ORDER = [
    "wrong state transition",
    "route / persistence drift",
    "rendered-projection mismatch",
]
FAILURE_SHORT = {
    "wrong state transition": "Wrong transition",
    "route / persistence drift": "Route / persistence drift",
    "rendered-projection mismatch": "Projection mismatch",
}
RELATION_LABELS = {
    "assertion_state_equals": "state value mismatch",
    "assertion_state_one_of": "state value outside allowed set",
    "assertion_state_delta": "state delta mismatch",
    "assertion_state_unchanged": "state changed unexpectedly",
    "assertion_state_normalized_equals": "normalized state value mismatch",
    "assertion_state_appended_object": "missing appended state object",
    "assertion_browser_page_equals": "browser route mismatch",
    "assertion_table_cell_equals": "rendered table cell mismatch",
    "assertion_table_order_equals": "rendered table order mismatch",
    "assertion_table_rows_equal": "rendered table rows mismatch",
    "assertion_table_row_count": "rendered table row-count mismatch",
    "assertion_table_row_count_equals": "rendered table row-count mismatch",
}


def slugify(s: str) -> str:
    s = str(s).strip().lower()
    s = s.replace("/", " ")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def is_missing(value: object) -> bool:
    return pd.isna(value) or str(value).strip().lower() in {"", "nan", "none", "null"}


def humanize_identifier(value: object) -> str:
    if is_missing(value):
        return "not recorded"
    text = re.sub(r"^(public|private)_\d+_", "", str(value))
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1].upper() + text[1:]


def model_group_label(value: object) -> str:
    mapping = {"M": "Mini", "T": "Turbo", "F": "Frontier"}
    return mapping.get(str(value), str(value))


def relation_label(value: object) -> str:
    if is_missing(value):
        return "contract assertion failed"
    raw = str(value)
    return RELATION_LABELS.get(raw, humanize_identifier(raw).lower())


def action_label(row: pd.Series) -> str:
    action = humanize_identifier(row.get("first_failed_action", "action")).lower()
    component = humanize_identifier(row.get("first_failed_component", ""))
    if action == "snapshot":
        return "Observe rendered state"
    if is_missing(row.get("first_failed_component", "")):
        return action.capitalize()
    return f"{action.capitalize()} {component}"


def display_value(value: object, max_len: int = 86) -> str:
    if value is None:
        text = "not found"
    elif isinstance(value, str):
        text = "empty string" if value == "" else value
    elif isinstance(value, (list, tuple)):
        text = ", ".join(display_value(v, 40) for v in value)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= max_len else text[: max_len - 1] + "..."


def parse_failed_item(assertion_type: object, message: object) -> str:
    msg = "" if is_missing(message) else str(message)
    typ = "" if is_missing(assertion_type) else str(assertion_type)
    if "table_" in typ or msg.startswith("table "):
        table = re.search(r"table '([^']+)'", msg)
        row = re.search(r"row '([^']+)'", msg)
        col = re.search(r"column '([^']+)'", msg)
        parts = []
        if table:
            parts.append(f"table {table.group(1)}")
        if row:
            parts.append(f"row {row.group(1)}")
        if col:
            parts.append(f"column {col.group(1)}")
        return " / ".join(parts) if parts else "rendered table"
    if "browser_page" in typ or msg.startswith("browser page"):
        return "browser page"
    m = re.match(r"^([A-Za-z0-9_.\\[\\]-]+)\s+(?:should|normalized|contains|is|must)", msg)
    if m:
        return m.group(1)
    if msg:
        return humanize_identifier(msg.split(" should ")[0])
    return "contract field"


@lru_cache(maxsize=1)
def summary_paths_by_run() -> dict[str, str]:
    csv_path = OUT_ROOT / "data" / "raw_runs.csv"
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path, usecols=["run_id", "summary_path"])
    return dict(df.drop_duplicates("run_id")[["run_id", "summary_path"]].itertuples(index=False, name=None))


@lru_cache(maxsize=512)
def load_summary(summary_path: str) -> dict:
    try:
        with open(summary_path) as f:
            return json.load(f)
    except Exception:
        return {}


def failure_detail(row: pd.Series) -> dict[str, str]:
    summary_path = summary_paths_by_run().get(str(row.get("run_id", "")))
    result = {
        "failed_item": "not recorded",
        "expected": "not recorded",
        "observed": "not recorded",
        "assertion_message": "",
        "additional_failed_checks": "",
    }
    if not summary_path:
        return result
    summary = load_summary(summary_path)
    scenarios = summary.get("scenarios", [])
    scenario = next((s for s in scenarios if s.get("id") == row.get("scenario_id")), None)
    if not scenario:
        return result

    first = scenario.get("first_failure") or {}
    step_index = int(float(row.get("first_failed_step", first.get("step_index", 0)) or 0))
    step = next((s for s in scenario.get("steps", []) if int(s.get("step_index", -1)) == step_index), {})
    failed_assertions = [a for a in step.get("assertions", []) if not a.get("passed", False)]
    if not first and failed_assertions:
        first = failed_assertions[0]

    assertion_type = first.get("assertion_type") or first.get("type") or row.get("first_failure_raw")
    message = first.get("message", "")
    result["failed_item"] = parse_failed_item(assertion_type, message)
    result["expected"] = display_value(first.get("expected"))
    result["observed"] = display_value(first.get("actual"))
    result["assertion_message"] = str(message)

    extras = []
    seen_extras = set()
    for assertion in failed_assertions:
        if assertion.get("message") == message:
            continue
        item = parse_failed_item(assertion.get("type"), assertion.get("message"))
        expected = display_value(assertion.get("expected"), 52)
        observed = display_value(assertion.get("actual"), 52)
        extra = f"{item}: expected {expected}, observed {observed}"
        if extra in seen_extras:
            continue
        seen_extras.add(extra)
        extras.append(extra)
        if len(extras) >= 2:
            break
    result["additional_failed_checks"] = "; ".join(extras)
    return result


def failure_explanation(category: str) -> str:
    if category == "wrong state transition":
        return (
            "The interaction surface was usable and the action ran, but the public state "
            "after the action did not satisfy the contract."
        )
    if category == "route / persistence drift":
        return (
            "The trace crossed a route, reload, or persistence boundary and the browser-visible "
            "state no longer matched the required workflow state."
        )
    if category == "rendered-projection mismatch":
        return (
            "The rendered interface diverged from the contract-visible state, so the user-facing "
            "view became stale or inconsistent."
        )
    return "The evaluator reached a contract violation at this step."


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join([*current, word])
        box = draw.textbbox((0, 0), trial, font=font_obj)
        if current and box[2] - box[0] > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font_obj: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int = 8,
) -> int:
    x, y = xy
    for line in wrap_text(draw, text, font_obj, max_width):
        draw.text((x, y), line, font=font_obj, fill=fill)
        box = draw.textbbox((0, 0), line, font=font_obj)
        y += (box[3] - box[1]) + line_gap
    return y


def wrapped_height(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_obj: ImageFont.ImageFont,
    max_width: int,
    line_gap: int = 8,
) -> int:
    lines = wrap_text(draw, text, font_obj, max_width)
    if not lines:
        return 0
    total = 0
    for i, line in enumerate(lines):
        box = draw.textbbox((0, 0), line, font=font_obj)
        total += box[3] - box[1]
        if i < len(lines) - 1:
            total += line_gap
    return total


def render_pdf(pdf: Path, out: Path, dpi: int = 300) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    try:
        page = doc.load_page(0)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(out)
    finally:
        doc.close()


def fit_image(path: Path, box: tuple[int, int], bg: str = "#FFFFFF", margin: int = 0) -> Image.Image:
    canvas = Image.new("RGB", box, bg)
    im = Image.open(path).convert("RGB")
    im.thumbnail((box[0] - 2 * margin, box[1] - 2 * margin), Image.LANCZOS)
    canvas.paste(im, ((box[0] - im.width) // 2, (box[1] - im.height) // 2))
    return canvas


def draw_info_chip(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    accent: str,
    label_font: ImageFont.ImageFont,
    value_font: ImageFont.ImageFont,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill="#F8FAFD", outline="#DADCE0", width=2)
    draw.text((x0 + 22, y0 + 18), label, fill=accent, font=label_font)
    draw_wrapped(draw, (x0 + 22, y0 + 62), value, value_font, "#202124", x1 - x0 - 44, line_gap=6)


def compose_failure_card(row: pd.Series, out: Path) -> dict[str, str]:
    width = 2600
    margin = 70
    gap = 44
    header_h = 160
    shot_label_h = 54
    shot_w = (width - 2 * margin - gap) // 2
    shot_h = 820
    evidence_y = margin + header_h + shot_label_h + shot_h + 46

    category = str(row["first_failure_group"])
    title = f"{row['target_label']} (Tier {row['tier']}): {FAILURE_SHORT.get(category, humanize_identifier(category))}"
    scenario = humanize_identifier(row.get("scenario_id", "scenario"))
    check = relation_label(row.get("first_failure_raw", ""))
    model = f"{row.get('model_label', 'model')} ({model_group_label(row.get('model_tier'))})"
    progress = float(row.get("step_progress_until_failure", 0.0))
    failed_step = row.get("first_failed_step", "")
    total_step = row.get("expected_step_count", "")
    visibility = humanize_identifier(row.get("visibility", ""))
    action = action_label(row)
    detail = failure_detail(row)

    summary = failure_explanation(category)
    step_value = (
        f"{int(float(failed_step)) if not is_missing(failed_step) else '?'}"
        f"/{int(float(total_step)) if not is_missing(total_step) else '?'} "
        f"({progress:.0%})"
    )
    meta_line = f"Scenario: {scenario} ({visibility}) · Model: {model}"

    out.parent.mkdir(parents=True, exist_ok=True)
    measure = Image.new("RGB", (width, 1000), "white")
    measure_draw = ImageDraw.Draw(measure)

    title_font = font(48, bold=True)
    subtitle_font = font(30)
    label_font = font(34, bold=True)
    chip_label_font = font(25, bold=True)
    chip_value_font = font(33, bold=True)
    body_font = font(31)
    meta_font = font(27)

    card_inner_w = width - 2 * margin - 76
    chip_gap = 20
    chip_w = (card_inner_w - 2 * chip_gap) // 3
    chip_h = 152
    value_chip_h = 142
    summary_h = wrapped_height(measure_draw, summary, body_font, card_inner_w, line_gap=10)
    extra_line = ""
    if detail["additional_failed_checks"]:
        extra_line = f"Additional failed checks: {detail['additional_failed_checks']}"
    extra_h = wrapped_height(measure_draw, extra_line, meta_font, card_inner_w, line_gap=8) if extra_line else 0
    meta = (
        f"Scenario id: {str(row.get('scenario_id', ''))} · "
        f"Component: {humanize_identifier(row.get('first_failed_component', ''))} · "
        f"Run: {str(row.get('run_id', ''))}"
    )
    meta_h = wrapped_height(measure_draw, meta, meta_font, card_inner_w, line_gap=8)
    evidence_h = (
        34
        + 42
        + 24
        + chip_h
        + 18
        + value_chip_h
        + 24
        + summary_h
        + (18 + extra_h if extra_line else 0)
        + 22
        + meta_h
        + 34
    )
    height = evidence_y + evidence_h + margin

    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)

    draw.text((margin, margin), title, fill="#202124", font=title_font)
    draw.text((margin, margin + 68), meta_line, fill="#5F6368", font=subtitle_font)

    before_x = margin
    after_x = margin + shot_w + gap
    shot_y = margin + header_h + shot_label_h
    for x, label, color in [(before_x, "Before", "#1A73E8"), (after_x, "After", "#E8710A")]:
        draw.rounded_rectangle(
            [x, margin + header_h, x + shot_w, margin + header_h + shot_label_h + shot_h],
            radius=18,
            fill="#F8FAFD",
            outline="#DADCE0",
            width=3,
        )
        draw.text((x + 28, margin + header_h + 14), label, fill=color, font=label_font)

    before_img = fit_image(Path(str(row["first_failure_before_screenshot"])), (shot_w - 42, shot_h - 36), margin=0)
    after_img = fit_image(Path(str(row["first_failure_after_screenshot"])), (shot_w - 42, shot_h - 36), margin=0)
    canvas.paste(before_img, (before_x + 21, shot_y + 18))
    canvas.paste(after_img, (after_x + 21, shot_y + 18))

    arrow_x = margin + shot_w + gap // 2
    arrow_y = shot_y + shot_h // 2
    draw.polygon(
        [(arrow_x - 12, arrow_y - 24), (arrow_x + 24, arrow_y), (arrow_x - 12, arrow_y + 24)],
        fill="#202124",
    )

    draw.rounded_rectangle(
        [margin, evidence_y, width - margin, evidence_y + evidence_h],
        radius=20,
        fill="#FFF8F2",
        outline="#E7CFC4",
        width=3,
    )
    x = margin + 38
    y = evidence_y + 32
    draw.text((x, y), "Failure evidence", fill="#202124", font=label_font)
    y += 66
    chips = [
        ("Action", action, "#1A73E8"),
        ("Check", check, "#E8710A"),
        ("First failing step", step_value, "#D93025"),
    ]
    for i, (chip_label, chip_value, accent) in enumerate(chips):
        chip_x = x + i * (chip_w + chip_gap)
        draw_info_chip(
            draw,
            (chip_x, y, chip_x + chip_w, y + chip_h),
            chip_label,
            chip_value,
            accent,
            chip_label_font,
            chip_value_font,
        )
    y += chip_h + 18
    value_chips = [
        ("Failed item", detail["failed_item"], "#5F6368"),
        ("Expected", detail["expected"], "#188038"),
        ("Observed", detail["observed"], "#D93025"),
    ]
    for i, (chip_label, chip_value, accent) in enumerate(value_chips):
        chip_x = x + i * (chip_w + chip_gap)
        draw_info_chip(
            draw,
            (chip_x, y, chip_x + chip_w, y + value_chip_h),
            chip_label,
            chip_value,
            accent,
            chip_label_font,
            font(30, bold=True),
        )
    y += value_chip_h + 24
    y = draw_wrapped(draw, (x, y), summary, body_font, "#202124", width - 2 * margin - 76, line_gap=10)
    if extra_line:
        y += 18
        y = draw_wrapped(draw, (x, y), extra_line, meta_font, "#5F6368", width - 2 * margin - 76, line_gap=8)
    y += 22
    draw_wrapped(draw, (x, y), meta, meta_font, "#5F6368", width - 2 * margin - 76, line_gap=8)

    canvas.save(out, dpi=(300, 300))
    return {
        "human_title": title,
        "human_summary": summary,
        "human_action": action,
        "human_check": check,
        "human_first_failing_step": step_value,
        "human_failed_item": detail["failed_item"],
        "human_expected": detail["expected"],
        "human_observed": detail["observed"],
        "human_assertion_message": detail["assertion_message"],
        "human_additional_failed_checks": detail["additional_failed_checks"],
        "human_metadata": meta_line,
    }


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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


def trim_outer_whitespace(im: Image.Image, tolerance: int = 248, pad: int = 18) -> Image.Image:
    """Trim near-white export margins while preserving a small breathing room."""
    rgb = im.convert("RGB")
    pixels = rgb.load()
    width, height = rgb.size
    min_x, min_y = width, height
    max_x, max_y = -1, -1
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if min(r, g, b) < tolerance:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < min_x or max_y < min_y:
        return im
    min_x = max(0, min_x - pad)
    min_y = max(0, min_y - pad)
    max_x = min(width, max_x + pad)
    max_y = min(height, max_y + pad)
    if max_x - min_x < width * 0.35 or max_y - min_y < height * 0.35:
        return im
    return rgb.crop((min_x, min_y, max_x + 1, max_y + 1))


def thumbnail(
    path: Path,
    box: tuple[int, int],
    bg: str = "white",
    top_pad: int = 92,
    margin: int = 36,
    crop_outer: bool = False,
    fill_width: bool = False,
) -> Image.Image:
    canvas = Image.new("RGB", box, bg)
    if path.exists():
        im = Image.open(path).convert("RGB")
        if crop_outer:
            im = trim_outer_whitespace(im)
        avail_w = box[0] - 2 * margin
        avail_h = box[1] - top_pad - margin
        if fill_width:
            scale = avail_w / im.width
            resized = im.resize((avail_w, max(1, int(im.height * scale))), Image.LANCZOS)
            crop = resized.crop((0, 0, avail_w, min(avail_h, resized.height)))
            canvas.paste(crop, (margin, top_pad))
        else:
            im.thumbnail((avail_w, avail_h), Image.LANCZOS)
            canvas.paste(im, ((box[0] - im.width) // 2, top_pad + (avail_h - im.height) // 2))
    else:
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([margin, top_pad, box[0] - margin, box[1] - margin], outline="#BDC1C6")
        draw.text((margin + 20, box[1] // 2), "missing", fill="#5F6368", font=font(34))
    return canvas


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, max_chars: int = 44, size: int = 34) -> None:
    if len(text) > max_chars:
        text = text[: max_chars - 1] + "..."
    draw.text(xy, text, fill="#202124", font=font(size))


def export_representatives() -> pd.DataFrame:
    meta = pd.read_csv(REP_SRC / "representative_screenshots_metadata.csv")
    rows = []
    for r in meta.itertuples(index=False):
        pdf = OUT_ROOT / r.output_pdf
        out = REP_OUT / f"{r.suite}_tier_{str(r.tier).lower()}_representative.png"
        render_pdf(pdf, out)
        row = r._asdict()
        row["output_png"] = str(out.relative_to(OUT_ROOT))
        rows.append(row)
    out_meta = pd.DataFrame(rows)
    REP_OUT.mkdir(parents=True, exist_ok=True)
    out_meta.to_csv(REP_OUT / "representative_screenshots_metadata.csv", index=False)
    return out_meta


def export_failure_evidence() -> pd.DataFrame:
    meta = pd.read_csv(FAIL_SRC / "current_raw_failure_evidence_selected.csv")
    rows = []
    for r in meta.itertuples(index=False):
        failure_slug = slugify(r.first_failure_group)
        base = f"{r.suite}_tier_{str(r.tier).lower()}_{failure_slug}"
        before_pdf = OUT_ROOT / r.before_pdf
        after_pdf = OUT_ROOT / r.after_pdf
        pair_png = FAIL_OUT / f"{base}_before_after.png"
        before_png = FAIL_OUT / f"{base}_before.png"
        after_png = FAIL_OUT / f"{base}_after.png"
        render_pdf(before_pdf, before_png)
        render_pdf(after_pdf, after_png)
        row = r._asdict()
        human = compose_failure_card(pd.Series(row), pair_png)
        row["before_after_png"] = str(pair_png.relative_to(OUT_ROOT))
        row["before_png"] = str(before_png.relative_to(OUT_ROOT))
        row["after_png"] = str(after_png.relative_to(OUT_ROOT))
        row.update(human)
        rows.append(row)
    out_meta = pd.DataFrame(rows)
    FAIL_OUT.mkdir(parents=True, exist_ok=True)
    out_meta.to_csv(FAIL_OUT / "failure_evidence_by_tier_metadata.csv", index=False)
    return out_meta


def representative_contact_sheet(meta: pd.DataFrame) -> None:
    cell_w, cell_h = 1780, 1060
    header_h = 22
    panel_header_h = 96
    REP_ROW_OUT.mkdir(parents=True, exist_ok=True)
    for old in REP_ROW_OUT.glob("*.png"):
        old.unlink()

    for i, fam in enumerate(FAMILY_ORDER):
        sheet = Image.new("RGB", (2 * cell_w, header_h + 2 * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for j, tier in enumerate(TIER_ORDER):
            row = meta[(meta["suite_label"] == fam) & (meta["tier"].astype(str) == tier)]
            x = (j % 2) * cell_w
            y = header_h + (j // 2) * cell_h
            draw.rectangle([x, y, x + cell_w, y + cell_h], outline="#E0E3E7")
            if not row.empty:
                target_label = str(row.iloc[0].get("target_label", f"{fam} {tier}"))
                label = f"{target_label} (Tier {tier})"
                label_font = font(39, bold=True)
                path = OUT_ROOT / row.iloc[0]["output_png"]
                im = thumbnail(
                    path,
                    (cell_w, cell_h),
                    top_pad=panel_header_h + 14,
                    margin=18,
                    crop_outer=True,
                    fill_width=True,
                )
                sheet.paste(im, (x, y))
                draw.rectangle([x, y, x + cell_w, y + panel_header_h], fill="#F7F9FC", outline="#E0E3E7")
                box = draw.textbbox((0, 0), label, font=label_font)
                draw.text(
                    (x + (cell_w - (box[2] - box[0])) // 2, y + 25),
                    label,
                    fill="#202124",
                    font=label_font,
                )
        sheet.save(REP_ROW_OUT / f"{i + 1:02d}_{slugify(fam)}.png", dpi=(300, 300))


def failure_evidence_contact_sheet(meta: pd.DataFrame) -> None:
    families = [
        ("StayFlow Concierge", "A"),
        ("StayFlow Concierge", "B"),
        ("StayFlow Concierge", "C"),
        ("FreshCart Market", "A"),
        ("FreshCart Market", "B"),
        ("FreshCart Market", "C"),
        ("Clinic Shift Command", "A"),
        ("Clinic Shift Command", "B"),
        ("Clinic Shift Command", "C"),
        ("HomeFix Hub", "A"),
        ("HomeFix Hub", "B"),
        ("HomeFix Hub", "C"),
        ("HomeFix Hub", "D"),
    ]
    cell_w, cell_h = 1900, 1240
    left_w = 420
    header_h = 140
    headers = ["Wrong transition", "Route / persistence", "Projection mismatch"]
    FAIL_ROW_OUT.mkdir(parents=True, exist_ok=True)
    FAIL_COLUMN_OUT.mkdir(parents=True, exist_ok=True)
    for old in FAIL_ROW_OUT.glob("*.png"):
        old.unlink()
    for old in FAIL_COLUMN_OUT.glob("*.png"):
        old.unlink()

    column_rows = []
    idx = 1
    for fam, tier in families:
        for failure in FAILURE_ORDER:
            row_df = meta[
                (meta["suite_label"] == fam)
                & (meta["tier"].astype(str) == tier)
                & (meta["first_failure_group"] == failure)
            ]
            if row_df.empty:
                continue
            row = row_df.iloc[0]
            src = OUT_ROOT / row["before_after_png"]
            out = FAIL_COLUMN_OUT / (
                f"{idx:02d}_{slugify(fam)}_tier_{str(tier).lower()}_"
                f"{slugify(failure)}.png"
            )
            out.write_bytes(src.read_bytes())
            row_dict = row.to_dict()
            row_dict["review_column_png"] = str(out.relative_to(OUT_ROOT))
            column_rows.append(row_dict)
            idx += 1

    for i, (fam, tier) in enumerate(families):
        sheet = Image.new("RGB", (left_w + 3 * cell_w, header_h + cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for j, h in enumerate(headers):
            draw.text((left_w + j * cell_w + 44, 40), h, fill="#202124", font=font(40, bold=True))
        draw.text((28, header_h + 56), f"{fam}\nTier {tier}", fill="#202124", font=font(34, bold=True))
        for j, failure in enumerate(FAILURE_ORDER):
            x = left_w + j * cell_w
            y = header_h
            draw.rectangle([x, y, x + cell_w, y + cell_h], outline="#E0E3E7")
            row = meta[
                (meta["suite_label"] == fam)
                & (meta["tier"].astype(str) == tier)
                & (meta["first_failure_group"] == failure)
            ]
            if not row.empty:
                path = OUT_ROOT / row.iloc[0]["before_after_png"]
                im = thumbnail(path, (cell_w, cell_h), top_pad=122, margin=44)
                sheet.paste(im, (x, y))
                progress = row.iloc[0]["step_progress_until_failure"]
                draw_label(draw, (x + 44, y + 32), f"{progress:.0%} into trace", size=34)
            else:
                draw.text((x + 64, y + 420), "no selected raw evidence", fill="#5F6368", font=font(34))
        sheet.save(FAIL_ROW_OUT / f"{i + 1:02d}_{slugify(fam)}_tier_{tier.lower()}.png", dpi=(300, 300))

    pd.DataFrame(column_rows).to_csv(FAIL_COLUMN_OUT / "failure_evidence_columns_metadata.csv", index=False)


def write_readmes(rep_meta: pd.DataFrame, fail_meta: pd.DataFrame) -> None:
    (REP_OUT / "README.md").write_text(
        "# Representative Tier Screenshots\n\n"
        "One editable PNG is exported for each product family and Tier A-D target. "
        "These are representative screenshots for paper editing, not model judgments.\n\n"
        f"Total PNGs: {len(rep_meta)}\n"
    )
    (FAIL_OUT / "README.md").write_text(
        "# Failure Evidence By Target Tier\n\n"
        "Each row in `failure_evidence_by_tier_metadata.csv` links a selected target-tier "
        "failure to before, after, and human-readable before/after evidence panels. These "
        "are audit evidence paired with structured evaluator metadata, not aesthetic judgments.\n\n"
        f"Total selected evidence rows: {len(fail_meta)}\n\n"
        "The review folder also contains `failure_evidence_columns/`, where each selected "
        "failure category is exported as its own standalone image for manual paper editing.\n"
    )


def main() -> None:
    REP_OUT.mkdir(parents=True, exist_ok=True)
    FAIL_OUT.mkdir(parents=True, exist_ok=True)
    REVIEW_OUT.mkdir(parents=True, exist_ok=True)
    for obsolete in [
        REVIEW_OUT / "representative_tier_screenshots_sheet.png",
        REVIEW_OUT / "failure_evidence_by_tier_sheet.png",
    ]:
        if obsolete.exists():
            obsolete.unlink()
    rep_meta = export_representatives()
    fail_meta = export_failure_evidence()
    representative_contact_sheet(rep_meta)
    failure_evidence_contact_sheet(fail_meta)
    write_readmes(rep_meta, fail_meta)


if __name__ == "__main__":
    main()
