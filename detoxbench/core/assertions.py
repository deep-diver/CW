from __future__ import annotations

import re
from collections.abc import Callable
from collections.abc import Sized
from typing import Any

from detoxbench.core.models import AssertionResult
from detoxbench.core.state import get_path
from detoxbench.core.templates import render_state_template


RELATION_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "==": lambda left, right: left == right,
    "eq": lambda left, right: left == right,
    "!=": lambda left, right: left != right,
    "ne": lambda left, right: left != right,
    ">": lambda left, right: left > right,
    "gt": lambda left, right: left > right,
    ">=": lambda left, right: left >= right,
    "gte": lambda left, right: left >= right,
    "ge": lambda left, right: left >= right,
    "<": lambda left, right: left < right,
    "lt": lambda left, right: left < right,
    "<=": lambda left, right: left <= right,
    "lte": lambda left, right: left <= right,
    "le": lambda left, right: left <= right,
}


def evaluate_assertions(
    assertion_specs: list[dict[str, Any]],
    *,
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> list[AssertionResult]:
    return [
        evaluate_assertion(spec, after_state=after_state, snapshots=snapshots)
        for spec in assertion_specs
    ]


def evaluate_assertion(
    spec: dict[str, Any],
    *,
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    assertion_type = spec.get("type")
    if not assertion_type:
        return AssertionResult(
            type="unknown",
            passed=False,
            message="Assertion is missing type",
        )

    try:
        if assertion_type == "state_equals":
            return _state_equals(spec, after_state)
        if assertion_type == "state_normalized_equals":
            return _state_normalized_equals(spec, after_state)
        if assertion_type == "state_not_equals":
            return _state_not_equals(spec, after_state)
        if assertion_type == "state_delta":
            return _state_delta(spec, after_state, snapshots)
        if assertion_type == "state_time_advanced_by":
            return _state_time_advanced_by(spec, after_state, snapshots)
        if assertion_type == "state_delta_from_path":
            return _state_delta_from_path(spec, after_state, snapshots)
        if assertion_type == "state_length_delta":
            return _state_length_delta(spec, after_state, snapshots)
        if assertion_type == "state_appended":
            return _state_appended(spec, after_state, snapshots)
        if assertion_type == "state_appended_object":
            return _state_appended_object(spec, after_state, snapshots)
        if assertion_type == "state_removed_first":
            return _state_removed_first(spec, after_state, snapshots)
        if assertion_type == "state_removed_first_where":
            return _state_removed_first_where(spec, after_state, snapshots)
        if assertion_type == "state_removed_all_where":
            return _state_removed_all_where(spec, after_state, snapshots)
        if assertion_type == "state_removed_all_where_after":
            return _state_removed_all_where_after(spec, after_state, snapshots)
        if assertion_type == "state_updated_first_where":
            return _state_updated_first_where(spec, after_state, snapshots)
        if assertion_type == "state_updated_all_where":
            return _state_updated_all_where(spec, after_state, snapshots)
        if assertion_type == "state_updated_all_where_after":
            return _state_updated_all_where_after(spec, after_state, snapshots)
        if assertion_type == "state_updated_first_child_where":
            return _state_updated_first_child_where(spec, after_state, snapshots)
        if assertion_type == "state_updated_object_fields":
            return _state_updated_object_fields(spec, after_state, snapshots)
        if assertion_type == "state_removed_object_fields":
            return _state_removed_object_fields(spec, after_state, snapshots)
        if assertion_type == "state_removed_first_child_where":
            return _state_removed_first_child_where(spec, after_state, snapshots)
        if assertion_type == "state_moved_first_where":
            return _state_moved_first_where(spec, after_state, snapshots)
        if assertion_type == "state_appended_from_first_where":
            return _state_appended_from_first_where(spec, after_state, snapshots)
        if assertion_type == "state_contains":
            return _state_contains(spec, after_state)
        if assertion_type == "state_not_contains":
            return _state_not_contains(spec, after_state)
        if assertion_type == "state_matches":
            return _state_matches(spec, after_state)
        if assertion_type == "state_template_equals":
            return _state_template_equals(spec, after_state)
        if assertion_type == "state_linear_equals":
            return _state_linear_equals(spec, after_state)
        if assertion_type == "state_piecewise_linear_equals":
            return _state_piecewise_linear_equals(spec, after_state)
        if assertion_type == "state_length_equals":
            return _state_length_equals(spec, after_state)
        if assertion_type == "state_count_where_equals":
            return _state_count_where_equals(spec, after_state)
        if assertion_type == "state_sum_equals":
            return _state_sum_equals(spec, after_state)
        if assertion_type == "state_any_where_equals":
            return _state_any_where_equals(spec, after_state)
        if assertion_type == "state_first_item_field_equals":
            return _state_first_item_field_equals(spec, after_state)
        if assertion_type == "state_last_item_field_equals":
            return _state_last_item_field_equals(spec, after_state)
        if assertion_type == "state_filter_equals":
            return _state_filter_equals(spec, after_state)
        if assertion_type == "state_join_projection_equals":
            return _state_join_projection_equals(spec, after_state)
        if assertion_type == "state_object_key_count_equals":
            return _state_object_key_count_equals(spec, after_state)
        if assertion_type == "state_nested_count_where_equals":
            return _state_nested_count_where_equals(spec, after_state)
        if assertion_type == "state_nested_sum_equals":
            return _state_nested_sum_equals(spec, after_state)
        if assertion_type == "state_truthy":
            return _state_truthy(spec, after_state)
        if assertion_type == "state_falsey":
            return _state_falsey(spec, after_state)
        if assertion_type == "state_one_of":
            return _state_one_of(spec, after_state)
        if assertion_type == "state_not_one_of":
            return _state_not_one_of(spec, after_state)
        if assertion_type == "state_relation":
            return _state_relation(spec, after_state, snapshots)
        if assertion_type == "state_changed":
            return _state_changed(spec, after_state, snapshots)
        if assertion_type == "state_unchanged":
            return _state_unchanged(spec, after_state, snapshots)
        if assertion_type == "browser_page_equals":
            return _browser_page_equals(spec, after_state)
        if assertion_type == "browser_path_equals":
            return _browser_path_equals(spec, after_state)
        if assertion_type == "table_order_equals":
            return _table_order_equals(spec, after_state)
        if assertion_type == "table_row_count_equals":
            return _table_row_count_equals(spec, after_state)
        if assertion_type == "table_cell_equals":
            return _table_cell_equals(spec, after_state)
    except Exception as exc:  # noqa: BLE001 - assertion failures should be data, not crashes.
        return AssertionResult(
            type=assertion_type,
            passed=False,
            message=f"Assertion raised {exc.__class__.__name__}: {exc}",
        )

    return AssertionResult(
        type=assertion_type,
        passed=False,
        message=f"Unsupported assertion type: {assertion_type}",
    )


def _state_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    expected = spec.get("expected", spec.get("value"))
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_equals",
        passed=actual == expected,
        message=f"{path} should equal {expected!r}",
        actual=actual,
        expected=expected,
    )


def _state_normalized_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    normalizers = _parse_normalizers(spec.get("normalizers", spec.get("normalizer")))
    actual = _normalize_value(get_path(after_state, path), normalizers)
    expected = _normalize_value(spec.get("expected", spec.get("value")), normalizers)
    return AssertionResult(
        type="state_normalized_equals",
        passed=actual == expected,
        message=f"{path} normalized by {normalizers!r} should equal {expected!r}",
        actual=actual,
        expected=expected,
    )


def _browser_page_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    expected = spec.get("expected", spec.get("page"))
    actual = get_path(after_state, "__browser.page_id")
    return AssertionResult(
        type="browser_page_equals",
        passed=actual == expected,
        message=f"browser page should equal {expected!r}",
        actual=actual,
        expected=expected,
    )


def _browser_path_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    expected = spec.get("expected", spec.get("path"))
    actual = get_path(after_state, "__browser.path")
    return AssertionResult(
        type="browser_path_equals",
        passed=actual == expected,
        message=f"browser path should equal {expected!r}",
        actual=actual,
        expected=expected,
    )


def _table_order_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    table = _table_state(spec, after_state)
    expected = list(spec.get("expected", []))
    actual = table.get("order")
    return AssertionResult(
        type="table_order_equals",
        passed=actual == expected,
        message=f"table {spec.get('table')!r} row order should equal {expected!r}",
        actual=actual,
        expected=expected,
    )


def _table_row_count_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    table = _table_state(spec, after_state)
    expected = spec.get("expected")
    actual = table.get("count")
    return AssertionResult(
        type="table_row_count_equals",
        passed=actual == expected,
        message=f"table {spec.get('table')!r} row count should equal {expected!r}",
        actual=actual,
        expected=expected,
    )


def _table_cell_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    table = _table_state(spec, after_state)
    row_id = str(_required(spec, "row_id"))
    column = str(_required(spec, "column"))
    rows = table.get("rows")
    if not isinstance(rows, dict):
        raise TypeError(f"table {spec.get('table')!r} rows must be an object")
    row = rows.get(row_id)
    if not isinstance(row, dict):
        actual = None
    else:
        actual = row.get(column)
    expected = str(spec.get("expected", ""))
    return AssertionResult(
        type="table_cell_equals",
        passed=actual == expected,
        message=f"table {spec.get('table')!r} row {row_id!r} column {column!r} should equal {expected!r}",
        actual=actual,
        expected=expected,
    )


def _table_state(spec: dict[str, Any], after_state: dict[str, Any]) -> dict[str, Any]:
    table_id = _required(spec, "table")
    tables = after_state.get("__tables")
    if not isinstance(tables, dict):
        raise KeyError("__tables")
    table = tables.get(table_id)
    if not isinstance(table, dict):
        raise KeyError(str(table_id))
    return table


def _state_not_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    expected = spec.get("expected", spec.get("value"))
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_not_equals",
        passed=actual != expected,
        message=f"{path} should not equal {expected!r}",
        actual=actual,
        expected=f"not {expected!r}",
    )


def _state_delta(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    delta = _required(spec, "by")
    baseline = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    expected = baseline + delta
    return AssertionResult(
        type="state_delta",
        passed=actual == expected,
        message=f"{path} should change by {delta!r} from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_time_advanced_by(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    delta = _required(spec, "by")
    baseline = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    expected = baseline + delta
    return AssertionResult(
        type="state_time_advanced_by",
        passed=actual == expected,
        message=f"{path} should advance by {delta!r} from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_delta_from_path(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    by_path = _required(spec, "by_path")
    multiplier = spec.get("multiplier", 1)
    baseline = _snapshot_value(snapshots, baseline_name, path)
    delta_value = _snapshot_value(snapshots, baseline_name, by_path)
    actual = get_path(after_state, path)
    expected = baseline + (delta_value * multiplier)
    return AssertionResult(
        type="state_delta_from_path",
        passed=actual == expected,
        message=(
            f"{path} should change by {by_path} * {multiplier!r} "
            f"from snapshot {baseline_name!r}"
        ),
        actual=actual,
        expected=expected,
    )


def _state_length_delta(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    delta = _required(spec, "by")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual_value = get_path(after_state, path)
    if not isinstance(baseline_value, Sized) or not isinstance(actual_value, Sized):
        raise TypeError(f"{path} values must have length")
    actual = len(actual_value)
    expected = len(baseline_value) + delta
    return AssertionResult(
        type="state_length_delta",
        passed=actual == expected,
        message=f"len({path}) should change by {delta!r} from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_appended(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    expected_item = spec.get("expected", spec.get("value"))
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = [*baseline_value, expected_item]
    return AssertionResult(
        type="state_appended",
        passed=actual == expected,
        message=f"{path} should append {expected_item!r} to snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_appended_object(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    baseline_state = snapshots[baseline_name]
    expected_item = _render_value_template(_required(spec, "value"), baseline_state, after_state)
    expected = [*baseline_value, expected_item]
    return AssertionResult(
        type="state_appended_object",
        passed=actual == expected,
        message=f"{path} should append a rendered object to snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_removed_first(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = baseline_value[1:]
    return AssertionResult(
        type="state_removed_first",
        passed=actual == expected,
        message=f"{path} should remove the first item from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_removed_first_where(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _remove_first_where(baseline_value, spec.get("where", []), snapshots[baseline_name])
    return AssertionResult(
        type="state_removed_first_where",
        passed=actual == expected,
        message=f"{path} should remove the first matching item from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_removed_all_where(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _remove_all_where(baseline_value, spec.get("where", []), snapshots[baseline_name])
    return AssertionResult(
        type="state_removed_all_where",
        passed=actual == expected,
        message=f"{path} should remove every matching item from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_removed_all_where_after(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _remove_all_where(baseline_value, spec.get("where", []), after_state)
    return AssertionResult(
        type="state_removed_all_where_after",
        passed=actual == expected,
        message=f"{path} should remove every item matching after-state predicates from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_updated_first_where(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _update_first_where(
        baseline_value,
        spec.get("where", []),
        _required(spec, "updates"),
        snapshots[baseline_name],
    )
    return AssertionResult(
        type="state_updated_first_where",
        passed=actual == expected,
        message=f"{path} should update the first matching item from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_updated_all_where(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _update_all_where(
        baseline_value,
        spec.get("where", []),
        _required(spec, "updates"),
        snapshots[baseline_name],
    )
    return AssertionResult(
        type="state_updated_all_where",
        passed=actual == expected,
        message=f"{path} should update every matching item from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_updated_all_where_after(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _update_all_where(
        baseline_value,
        spec.get("where", []),
        _required(spec, "updates"),
        after_state,
    )
    return AssertionResult(
        type="state_updated_all_where_after",
        passed=actual == expected,
        message=f"{path} should update every item matching after-state predicates from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_updated_first_child_where(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _update_first_child_where(baseline_value, spec, snapshots[baseline_name])
    return AssertionResult(
        type="state_updated_first_child_where",
        passed=actual == expected,
        message=f"{path} should update the first matching child item from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_updated_object_fields(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, dict) or not isinstance(actual, dict):
        raise TypeError(f"{path} values must be objects")
    expected = {**baseline_value, **_required(spec, "updates")}
    return AssertionResult(
        type="state_updated_object_fields",
        passed=actual == expected,
        message=f"{path} should update object fields from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_removed_object_fields(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, dict) or not isinstance(actual, dict):
        raise TypeError(f"{path} values must be objects")
    fields = set(_required(spec, "fields"))
    expected = {key: value for key, value in baseline_value.items() if key not in fields}
    return AssertionResult(
        type="state_removed_object_fields",
        passed=actual == expected,
        message=f"{path} should remove object fields from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_removed_first_child_where(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _remove_first_child_where(baseline_value, spec, snapshots[baseline_name])
    return AssertionResult(
        type="state_removed_first_child_where",
        passed=actual == expected,
        message=f"{path} should remove the first matching child item from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_moved_first_where(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_value = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    if not isinstance(baseline_value, list) or not isinstance(actual, list):
        raise TypeError(f"{path} values must be arrays")
    expected = _move_first_where(
        baseline_value,
        spec.get("where", []),
        _required(spec, "to_index"),
        snapshots[baseline_name],
    )
    return AssertionResult(
        type="state_moved_first_where",
        passed=actual == expected,
        message=f"{path} should move the first matching item from snapshot {baseline_name!r}",
        actual=actual,
        expected=expected,
    )


def _state_appended_from_first_where(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline_destination = _snapshot_value(snapshots, baseline_name, path)
    source_path = _required(spec, "source_path")
    source_items = _snapshot_value(snapshots, baseline_name, source_path)
    actual = get_path(after_state, path)
    if (
        not isinstance(baseline_destination, list)
        or not isinstance(source_items, list)
        or not isinstance(actual, list)
    ):
        raise TypeError(f"{path} and {source_path} values must be arrays")
    expected = _append_from_first_where(
        baseline_destination,
        source_items,
        spec.get("where", []),
        spec.get("updates", {}),
        snapshots[baseline_name],
    )
    return AssertionResult(
        type="state_appended_from_first_where",
        passed=actual == expected,
        message=f"{path} should append the first matching item from {source_path}",
        actual=actual,
        expected=expected,
    )


def _state_contains(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    expected = spec.get("expected", spec.get("value"))
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_contains",
        passed=expected in actual,
        message=f"{path} should contain {expected!r}",
        actual=actual,
        expected=f"contains {expected!r}",
    )


def _state_not_contains(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    expected = spec.get("expected", spec.get("value"))
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_not_contains",
        passed=expected not in actual,
        message=f"{path} should not contain {expected!r}",
        actual=actual,
        expected=f"does not contain {expected!r}",
    )


def _state_matches(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    pattern = _required(spec, "pattern")
    actual = get_path(after_state, path)
    passed = re.search(pattern, str(actual)) is not None
    return AssertionResult(
        type="state_matches",
        passed=passed,
        message=f"{path} should match /{pattern}/",
        actual=actual,
        expected=pattern,
    )


def _state_template_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    template = _required(spec, "template")
    actual = get_path(after_state, path)
    expected = render_state_template(str(template), after_state)
    return AssertionResult(
        type="state_template_equals",
        passed=actual == expected,
        message=f"{path} should equal rendered state template",
        actual=actual,
        expected=expected,
    )


def _state_linear_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _evaluate_linear_formula(spec, after_state)
    return AssertionResult(
        type="state_linear_equals",
        passed=actual == expected,
        message=f"{path} should equal rendered linear state formula",
        actual=actual,
        expected=expected,
    )


def _state_piecewise_linear_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _evaluate_piecewise_linear_formula(spec, after_state)
    return AssertionResult(
        type="state_piecewise_linear_equals",
        passed=actual == expected,
        message=f"{path} should equal rendered piecewise linear state formula",
        actual=actual,
        expected=expected,
    )


def _state_length_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    source_path = _required(spec, "source_path")
    actual = get_path(after_state, path)
    source_value = get_path(after_state, source_path)
    expected = len(source_value)
    return AssertionResult(
        type="state_length_equals",
        passed=actual == expected,
        message=f"{path} should equal len({source_path})",
        actual=actual,
        expected=expected,
    )


def _state_count_where_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _count_where(spec, after_state)
    return AssertionResult(
        type="state_count_where_equals",
        passed=actual == expected,
        message=f"{path} should equal count of matching collection items",
        actual=actual,
        expected=expected,
    )


def _state_sum_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _sum_items(spec, after_state)
    return AssertionResult(
        type="state_sum_equals",
        passed=actual == expected,
        message=f"{path} should equal sum of matching collection items",
        actual=actual,
        expected=expected,
    )


def _state_any_where_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _any_where(spec, after_state)
    return AssertionResult(
        type="state_any_where_equals",
        passed=actual == expected,
        message=f"{path} should equal whether any collection item matches",
        actual=actual,
        expected=expected,
    )


def _state_first_item_field_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _edge_item_field(spec, after_state, first=True)
    return AssertionResult(
        type="state_first_item_field_equals",
        passed=actual == expected,
        message=f"{path} should equal the first collection item's field",
        actual=actual,
        expected=expected,
    )


def _state_last_item_field_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _edge_item_field(spec, after_state, first=False)
    return AssertionResult(
        type="state_last_item_field_equals",
        passed=actual == expected,
        message=f"{path} should equal the last collection item's field",
        actual=actual,
        expected=expected,
    )


def _state_filter_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _filter_items(spec, after_state)
    return AssertionResult(
        type="state_filter_equals",
        passed=actual == expected,
        message=f"{path} should equal the filtered collection view",
        actual=actual,
        expected=expected,
    )


def _state_join_projection_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _join_projection(spec, after_state)
    return AssertionResult(
        type="state_join_projection_equals",
        passed=actual == expected,
        message=f"{path} should equal the declared joined projection",
        actual=actual,
        expected=expected,
    )


def _state_object_key_count_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    source_path = _required(spec, "source_path")
    source_value = get_path(after_state, source_path)
    if not isinstance(source_value, dict):
        raise TypeError(f"{source_path} value must be an object")
    actual = get_path(after_state, path)
    expected = len(source_value)
    return AssertionResult(
        type="state_object_key_count_equals",
        passed=actual == expected,
        message=f"{path} should equal number of keys in {source_path}",
        actual=actual,
        expected=expected,
    )


def _state_nested_count_where_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _nested_count_where(spec, after_state)
    return AssertionResult(
        type="state_nested_count_where_equals",
        passed=actual == expected,
        message=f"{path} should equal count of matching nested collection items",
        actual=actual,
        expected=expected,
    )


def _state_nested_sum_equals(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    expected = _nested_sum(spec, after_state)
    return AssertionResult(
        type="state_nested_sum_equals",
        passed=actual == expected,
        message=f"{path} should equal sum of matching nested collection items",
        actual=actual,
        expected=expected,
    )


def _evaluate_linear_formula(spec: dict[str, Any], after_state: dict[str, Any]) -> float:
    expected = float(spec.get("constant", 0))
    terms = spec.get("terms", [])
    if not isinstance(terms, list):
        raise TypeError("state_linear_equals terms must be a non-empty array")
    for term in terms:
        if not isinstance(term, dict):
            raise TypeError("state_linear_equals terms must be mappings")
        term_path = _required(term, "path")
        expected += get_path(after_state, term_path) * term.get("multiplier", 1)
    if "round" in spec:
        expected = round(expected, int(spec["round"]))
    return expected


def _evaluate_piecewise_linear_formula(spec: dict[str, Any], after_state: dict[str, Any]) -> float:
    cases = _required(spec, "cases")
    if not isinstance(cases, list) or not cases:
        raise TypeError("state_piecewise_linear_equals cases must be a non-empty array")
    for case in cases:
        if not isinstance(case, dict):
            raise TypeError("state_piecewise_linear_equals cases must be mappings")
        conditions = case.get("when")
        if not isinstance(conditions, list) or not conditions:
            raise TypeError("state_piecewise_linear_equals case.when must be a non-empty array")
        if all(_state_condition_passes(condition, after_state) for condition in conditions):
            formula = case.get("formula")
            if not isinstance(formula, dict):
                raise TypeError("state_piecewise_linear_equals case.formula must be a mapping")
            return _evaluate_linear_formula(formula, after_state)
    default = spec.get("default")
    if not isinstance(default, dict):
        raise TypeError("state_piecewise_linear_equals default must be a mapping")
    return _evaluate_linear_formula(default, after_state)


def _collection_items(spec: dict[str, Any], after_state: dict[str, Any]) -> list[Any]:
    source_path = _required(spec, "source_path")
    items = get_path(after_state, source_path)
    if not isinstance(items, list):
        raise TypeError(f"{source_path} must be an array")
    return items


def _count_where(spec: dict[str, Any], after_state: dict[str, Any]) -> int:
    return sum(
        1
        for item in _collection_items(spec, after_state)
        if _item_matches(item, spec.get("where", []), after_state)
    )


def _sum_items(spec: dict[str, Any], after_state: dict[str, Any]) -> float:
    total = float(spec.get("constant", 0))
    multiplier = spec.get("multiplier", 1)
    field = _required(spec, "field")
    for item in _collection_items(spec, after_state):
        if _item_matches(item, spec.get("where", []), after_state):
            value = get_path(item, field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"Collection field {field!r} must be numeric")
            total += value * multiplier
    if "round" in spec:
        total = round(total, int(spec["round"]))
    return total


def _nested_count_where(spec: dict[str, Any], after_state: dict[str, Any]) -> int:
    count = 0
    for child in _matching_nested_children(spec, after_state):
        if _item_matches(child, spec.get("child_where", []), after_state):
            count += 1
    return count


def _nested_sum(spec: dict[str, Any], after_state: dict[str, Any]) -> float:
    total = float(spec.get("constant", 0))
    multiplier = spec.get("multiplier", 1)
    field = _required(spec, "field")
    for child in _matching_nested_children(spec, after_state):
        if not _item_matches(child, spec.get("child_where", []), after_state):
            continue
        value = get_path(child, field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"Nested collection field {field!r} must be numeric")
        total += value * multiplier
    if "round" in spec:
        total = round(total, int(spec["round"]))
    return total


def _matching_nested_children(spec: dict[str, Any], after_state: dict[str, Any]) -> list[Any]:
    children: list[Any] = []
    for parent in _collection_items(spec, after_state):
        if not _item_matches(parent, spec.get("parent_where", []), after_state):
            continue
        child_items = get_path(parent, _required(spec, "child_path"))
        if not isinstance(child_items, list):
            raise TypeError(f"child_path {spec['child_path']!r} must resolve to an array")
        children.extend(child_items)
    return children


def _any_where(spec: dict[str, Any], after_state: dict[str, Any]) -> bool:
    return any(
        _item_matches(item, spec.get("where", []), after_state)
        for item in _collection_items(spec, after_state)
    )


def _edge_item_field(spec: dict[str, Any], after_state: dict[str, Any], *, first: bool) -> Any:
    items = _collection_items(spec, after_state)
    if not items:
        return _required(spec, "default")
    item = items[0] if first else items[-1]
    return get_path(item, _required(spec, "field"))


def _filter_items(spec: dict[str, Any], after_state: dict[str, Any]) -> list[Any]:
    items = [
        item
        for item in _collection_items(spec, after_state)
        if _item_matches(item, spec.get("where", []), after_state)
    ]
    for order in reversed(spec.get("order_by", [])):
        field = _required(order, "field")
        reverse = order.get("direction", "asc") == "desc"
        items.sort(key=lambda item: get_path(item, field), reverse=reverse)
    return items


def _join_projection(spec: dict[str, Any], after_state: dict[str, Any]) -> list[dict[str, Any]]:
    source_items = get_path(after_state, _required(spec, "source_path"))
    lookup_items = get_path(after_state, _required(spec, "lookup_path"))
    if not isinstance(source_items, list):
        raise TypeError(f"{spec['source_path']} value must be an array")
    if not isinstance(lookup_items, list):
        raise TypeError(f"{spec['lookup_path']} value must be an array")
    lookup_by_key: dict[Any, dict[str, Any]] = {}
    for lookup_item in lookup_items:
        if not isinstance(lookup_item, dict):
            raise TypeError("lookup projection item must be an object")
        lookup_by_key[get_path(lookup_item, _required(spec, "lookup_key"))] = lookup_item

    output: list[dict[str, Any]] = []
    for source_item in source_items:
        if not isinstance(source_item, dict):
            raise TypeError("source projection item must be an object")
        if not _item_matches(source_item, spec.get("where", []), after_state):
            continue
        lookup_item = lookup_by_key.get(get_path(source_item, _required(spec, "source_key")))
        if lookup_item is None:
            raise KeyError(f"missing lookup item for source key {spec['source_key']!r}")
        output.append(_project_join_item(source_item, lookup_item, _required(spec, "fields")))
    return output


def _project_join_item(
    source_item: dict[str, Any],
    lookup_item: dict[str, Any],
    fields: list[dict[str, Any]],
) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    for field_spec in fields:
        name = _required(field_spec, "name")
        if "source_field" in field_spec:
            projected[name] = get_path(source_item, field_spec["source_field"])
        elif "lookup_field" in field_spec:
            projected[name] = get_path(lookup_item, field_spec["lookup_field"])
        else:
            projected[name] = field_spec.get("value")
    return projected


def _render_value_template(template: Any, before_state: dict[str, Any], after_state: dict[str, Any]) -> Any:
    if isinstance(template, dict):
        if set(template) == {"from_path"}:
            return get_path(before_state, template["from_path"])
        if set(template) == {"after_path"}:
            return get_path(after_state, template["after_path"])
        return {
            key: _render_value_template(value, before_state, after_state)
            for key, value in template.items()
        }
    if isinstance(template, list):
        return [_render_value_template(value, before_state, after_state) for value in template]
    return template


def _remove_first_where(
    items: list[Any],
    conditions: list[dict[str, Any]],
    state: dict[str, Any],
) -> list[Any]:
    index = _first_matching_index(items, conditions, state)
    if index is None:
        return list(items)
    return [*items[:index], *items[index + 1:]]


def _remove_all_where(
    items: list[Any],
    conditions: list[dict[str, Any]],
    state: dict[str, Any],
) -> list[Any]:
    return [item for item in items if not _item_matches(item, conditions, state)]


def _update_first_where(
    items: list[Any],
    conditions: list[dict[str, Any]],
    updates: dict[str, Any],
    state: dict[str, Any],
) -> list[Any]:
    index = _first_matching_index(items, conditions, state)
    if index is None:
        return list(items)
    item = items[index]
    if not isinstance(item, dict):
        raise TypeError("updated collection item must be an object")
    updated = {**item, **updates}
    return [*items[:index], updated, *items[index + 1:]]


def _update_all_where(
    items: list[Any],
    conditions: list[dict[str, Any]],
    updates: dict[str, Any],
    state: dict[str, Any],
) -> list[Any]:
    updated_items: list[Any] = []
    for item in items:
        if not _item_matches(item, conditions, state):
            updated_items.append(item)
            continue
        if not isinstance(item, dict):
            raise TypeError("updated collection item must be an object")
        updated_items.append({**item, **updates})
    return updated_items


def _update_first_child_where(
    items: list[Any],
    spec: dict[str, Any],
    state: dict[str, Any],
) -> list[Any]:
    parent_index = _first_matching_index(items, spec.get("parent_where", []), state)
    if parent_index is None:
        return list(items)
    parent = items[parent_index]
    if not isinstance(parent, dict):
        raise TypeError("nested parent item must be an object")
    children = get_path(parent, _required(spec, "child_path"))
    if not isinstance(children, list):
        raise TypeError(f"child_path {spec['child_path']!r} must resolve to an array")
    child_index = _first_matching_index(children, _required(spec, "child_where"), state)
    if child_index is None:
        return list(items)
    child = children[child_index]
    if not isinstance(child, dict):
        raise TypeError("nested child item must be an object")
    updated_child = {**child, **_required(spec, "updates")}
    updated_children = [*children[:child_index], updated_child, *children[child_index + 1:]]
    updated_parent = _copy_with_path(parent, spec["child_path"], updated_children)
    return [*items[:parent_index], updated_parent, *items[parent_index + 1:]]


def _remove_first_child_where(
    items: list[Any],
    spec: dict[str, Any],
    state: dict[str, Any],
) -> list[Any]:
    parent_index = _first_matching_index(items, spec.get("parent_where", []), state)
    if parent_index is None:
        return list(items)
    parent = items[parent_index]
    if not isinstance(parent, dict):
        raise TypeError("nested parent item must be an object")
    children = get_path(parent, _required(spec, "child_path"))
    if not isinstance(children, list):
        raise TypeError(f"child_path {spec['child_path']!r} must resolve to an array")
    child_index = _first_matching_index(children, _required(spec, "child_where"), state)
    if child_index is None:
        return list(items)
    updated_children = [*children[:child_index], *children[child_index + 1:]]
    updated_parent = _copy_with_path(parent, spec["child_path"], updated_children)
    return [*items[:parent_index], updated_parent, *items[parent_index + 1:]]


def _copy_with_path(item: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    parts = path.split(".")
    root = dict(item)
    output_cursor = root
    input_cursor: Any = item
    for part in parts[:-1]:
        if not isinstance(input_cursor, dict):
            raise TypeError(f"Cannot set nested path {path!r}")
        nested = input_cursor.get(part)
        if not isinstance(nested, dict):
            raise TypeError(f"Nested path {path!r} must traverse objects")
        cloned = dict(nested)
        output_cursor[part] = cloned
        output_cursor = cloned
        input_cursor = nested
    output_cursor[parts[-1]] = value
    return root


def _move_first_where(
    items: list[Any],
    conditions: list[dict[str, Any]],
    to_index: int,
    state: dict[str, Any],
) -> list[Any]:
    index = _first_matching_index(items, conditions, state)
    if index is None:
        return list(items)
    moved = items[index]
    remaining = [*items[:index], *items[index + 1:]]
    destination = min(to_index, len(remaining))
    return [*remaining[:destination], moved, *remaining[destination:]]


def _append_from_first_where(
    destination: list[Any],
    source_items: list[Any],
    conditions: list[dict[str, Any]],
    updates: dict[str, Any],
    state: dict[str, Any],
) -> list[Any]:
    index = _first_matching_index(source_items, conditions, state)
    if index is None:
        return list(destination)
    item = source_items[index]
    if updates:
        if not isinstance(item, dict):
            raise TypeError("appended source item must be an object when updates are used")
        item = {**item, **updates}
    return [*destination, item]


def _first_matching_index(
    items: list[Any],
    conditions: list[dict[str, Any]],
    state: dict[str, Any],
) -> int | None:
    for index, item in enumerate(items):
        if _item_matches(item, conditions, state):
            return index
    return None


def _item_matches(item: Any, conditions: list[dict[str, Any]], state: dict[str, Any]) -> bool:
    return all(_item_condition_passes(item, condition, state) for condition in conditions)


def _item_condition_passes(item: Any, condition: dict[str, Any], state: dict[str, Any]) -> bool:
    if not isinstance(condition, dict):
        raise TypeError("collection condition must be a mapping")
    op = condition.get("op")
    actual = get_path(item, _required(condition, "field"))
    if op == "equals":
        right = get_path(state, condition["value_path"]) if "value_path" in condition else condition.get("value")
        return actual == right
    if op == "truthy":
        return bool(actual)
    if op == "falsey":
        return not bool(actual)
    if op == "one_of":
        return actual in _required(condition, "values")
    if op == "not_one_of":
        return actual not in _required(condition, "values")
    if op == "relation":
        operator = str(condition.get("operator", condition.get("relation", "")))
        if operator not in RELATION_OPERATORS:
            raise ValueError(f"Unsupported collection relation operator: {operator!r}")
        if "other_field" in condition:
            right = get_path(item, condition["other_field"])
        elif "value_path" in condition:
            right = get_path(state, condition["value_path"])
        else:
            right = condition.get("value")
        return RELATION_OPERATORS[operator](actual, right)
    raise ValueError(f"Unsupported collection condition op: {op!r}")


def _state_condition_passes(condition: dict[str, Any], after_state: dict[str, Any]) -> bool:
    if not isinstance(condition, dict):
        raise TypeError("piecewise condition must be a mapping")
    op = condition.get("op")
    path = _required(condition, "path")
    actual = get_path(after_state, path)
    if op == "equals":
        return actual == condition.get("value")
    if op == "truthy":
        return bool(actual)
    if op == "falsey":
        return not bool(actual)
    if op == "one_of":
        return actual in _required(condition, "values")
    if op == "not_one_of":
        return actual not in _required(condition, "values")
    if op == "relation":
        operator = str(condition.get("operator", condition.get("relation", "")))
        if operator not in RELATION_OPERATORS:
            raise ValueError(f"Unsupported piecewise relation operator: {operator!r}")
        if "other_path" in condition:
            right = get_path(after_state, condition["other_path"])
        else:
            right = condition.get("value")
        return RELATION_OPERATORS[operator](actual, right)
    raise ValueError(f"Unsupported piecewise condition op: {op!r}")


def _state_truthy(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_truthy",
        passed=bool(actual),
        message=f"{path} should be truthy",
        actual=actual,
        expected=True,
    )


def _state_falsey(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_falsey",
        passed=not actual,
        message=f"{path} should be falsey",
        actual=actual,
        expected=False,
    )


def _state_one_of(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    values = _required(spec, "values")
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_one_of",
        passed=actual in values,
        message=f"{path} should be one of {values!r}",
        actual=actual,
        expected=f"one of {values!r}",
    )


def _state_not_one_of(spec: dict[str, Any], after_state: dict[str, Any]) -> AssertionResult:
    path = _required(spec, "path")
    values = _required(spec, "values")
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_not_one_of",
        passed=actual not in values,
        message=f"{path} should not be one of {values!r}",
        actual=actual,
        expected=f"not one of {values!r}",
    )


def _state_relation(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    operator = str(spec.get("operator", spec.get("op", "")))
    if operator not in RELATION_OPERATORS:
        raise ValueError(f"Unsupported relation operator: {operator!r}")

    actual = get_path(after_state, path)
    expected, expected_label = _relation_rhs(spec, after_state, snapshots, path)
    return AssertionResult(
        type="state_relation",
        passed=RELATION_OPERATORS[operator](actual, expected),
        message=f"{path} should be {operator} {expected_label}",
        actual=actual,
        expected=f"{operator} {expected!r}",
    )


def _relation_rhs(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
    path: str,
) -> tuple[Any, str]:
    if "other_path" in spec:
        other_path = str(spec["other_path"])
        if "from" in spec:
            snapshot_name = str(spec["from"])
            return (
                _snapshot_value(snapshots, snapshot_name, other_path),
                f"{other_path} from snapshot {snapshot_name!r}",
            )
        return get_path(after_state, other_path), other_path

    if "expected" in spec or "value" in spec:
        expected = spec.get("expected", spec.get("value"))
        return expected, repr(expected)

    if "from" in spec:
        snapshot_name = str(spec["from"])
        return (
            _snapshot_value(snapshots, snapshot_name, path),
            f"{path} from snapshot {snapshot_name!r}",
        )

    raise KeyError("Missing assertion field: one of other_path, expected, value, or from")


def _state_changed(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_changed",
        passed=actual != baseline,
        message=f"{path} should differ from snapshot {baseline_name!r}",
        actual=actual,
        expected=f"not {baseline!r}",
    )


def _state_unchanged(
    spec: dict[str, Any],
    after_state: dict[str, Any],
    snapshots: dict[str, dict[str, Any]],
) -> AssertionResult:
    path = _required(spec, "path")
    baseline_name = _required(spec, "from")
    baseline = _snapshot_value(snapshots, baseline_name, path)
    actual = get_path(after_state, path)
    return AssertionResult(
        type="state_unchanged",
        passed=actual == baseline,
        message=f"{path} should equal snapshot {baseline_name!r}",
        actual=actual,
        expected=baseline,
    )


def _snapshot_value(
    snapshots: dict[str, dict[str, Any]],
    name: str,
    path: str,
) -> Any:
    if name not in snapshots:
        raise KeyError(f"Unknown snapshot: {name}")
    return get_path(snapshots[name], path)


def _parse_normalizers(raw_normalizers: Any) -> list[str]:
    if isinstance(raw_normalizers, str):
        normalizers = [raw_normalizers]
    elif isinstance(raw_normalizers, list):
        normalizers = raw_normalizers
    else:
        raise TypeError("normalizers must be a string or list")
    if not normalizers:
        raise ValueError("normalizers must not be empty")
    return [str(normalizer) for normalizer in normalizers]


def _normalize_value(value: Any, normalizers: list[str]) -> str:
    text = "" if value is None else str(value)
    for normalizer in normalizers:
        if normalizer == "trim":
            text = text.strip()
        elif normalizer == "collapse_whitespace":
            text = re.sub(r"\s+", " ", text)
        elif normalizer == "lowercase":
            text = text.lower()
        elif normalizer == "uppercase":
            text = text.upper()
        elif normalizer == "digits_only":
            text = re.sub(r"\D+", "", text)
        elif normalizer == "currency_number":
            text = _normalize_currency_number(text)
        else:
            raise ValueError(f"unsupported normalizer {normalizer!r}")
    return text


def _normalize_currency_number(value: str) -> str:
    cleaned = re.sub(r"[^0-9.\-]+", "", value)
    if cleaned in {"", "-", ".", "-."}:
        return "0"
    number = float(cleaned)
    if number.is_integer():
        return str(int(number))
    return f"{number:.6f}".rstrip("0").rstrip(".")


def _required(spec: dict[str, Any], key: str) -> Any:
    if key not in spec:
        raise KeyError(f"Missing assertion field: {key}")
    return spec[key]
