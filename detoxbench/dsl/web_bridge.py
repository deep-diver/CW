from __future__ import annotations

from typing import Any

from detoxbench.core.models import Component
from detoxbench.core.models import Contract
from detoxbench.core.models import ScenarioSet
from detoxbench.dsl.compiler import CompiledCheck
from detoxbench.dsl.compiler import CompiledScenario
from detoxbench.dsl.compiler import compile_bundle


def compile_dsl_to_web_suite(
    contract_dsl: dict[str, Any],
    scenarios_dsl: dict[str, Any],
) -> tuple[Contract, ScenarioSet]:
    compiled = compile_bundle(contract_dsl, scenarios_dsl)
    return build_web_contract(contract_dsl), build_web_scenarios(scenarios_dsl, compiled)


def build_web_contract(contract_dsl: dict[str, Any]) -> Contract:
    app = contract_dsl.get("app", {})
    runtime = contract_dsl.get("runtime", {})
    state_probe = runtime.get("state_probe", {})
    expression = state_probe.get("expression")
    if not expression:
        raise ValueError("DSL runtime.state_probe.expression is required")

    components: dict[str, Component] = {}
    for component_id, raw_component in contract_dsl.get("components", {}).items():
        raw_actions = raw_component.get("actions", {})
        actions = sorted({_web_action(action) for action in raw_actions})
        selector = raw_component.get("selector", raw_component.get("selector_template"))
        components[str(component_id)] = Component(
            id=str(component_id),
            selector=str(selector),
            type=str(raw_component.get("kind", "generic")),
            actions=actions,
            attributes={
                "dsl_actions": sorted(raw_actions.keys()),
                "page": raw_component.get("page"),
                "selector_template": raw_component.get("selector_template"),
            },
        )

    pages = runtime.get("pages", {})
    if pages is None:
        pages = {}
    actors = runtime.get("actors", {})
    if actors is None:
        actors = {}
    services = runtime.get("services", {})
    if services is None:
        services = {}
    events = runtime.get("events", {})
    if events is None:
        events = {}
    tables = runtime.get("tables", {})
    if tables is None:
        tables = {}
    return Contract(
        id=str(app.get("id", "dsl_target")),
        name=str(app.get("name", app.get("id", "DSL Target"))),
        version=f"dsl-{contract_dsl.get('dsl_version', 'unknown')}",
        target="web",
        runtime={
            "kind": "web",
            "web": {
                "start_url": str(runtime.get("start_url", "/")),
                "state_expression": str(expression),
                "pages": pages,
                "actors": actors,
                "services": services,
                "events": events,
                "tables": tables,
            },
        },
        components=components,
        constraints=[],
        raw=contract_dsl,
    )


def build_web_scenarios(
    scenarios_dsl: dict[str, Any],
    compiled: list[CompiledScenario],
) -> ScenarioSet:
    scenarios: list[dict[str, Any]] = []
    for scenario in compiled:
        web_steps: list[dict[str, Any]] = []
        for step in scenario.steps:
            snapshot_name = f"dsl_before_{step.index}"
            snapshot_expect = [
                _precondition_to_assertion(check)
                for check in step.preconditions
            ]
            if step.page:
                snapshot_expect.append(
                    {
                        "type": "browser_page_equals",
                        "expected": step.page,
                    }
                )
            if step.preconditions:
                snapshot_step = {
                    "action": "snapshot",
                    "save_as": snapshot_name,
                    "expect": snapshot_expect,
                    "contract_refs": [check.source for check in step.preconditions],
                }
                if step.actor:
                    snapshot_step["actor"] = step.actor
                web_steps.append(snapshot_step)
            else:
                snapshot_step = {
                    "action": "snapshot",
                    "save_as": snapshot_name,
                }
                if snapshot_expect:
                    snapshot_step["expect"] = snapshot_expect
                if step.actor:
                    snapshot_step["actor"] = step.actor
                web_steps.append(snapshot_step)

            action_step: dict[str, Any] = {
                "action": _web_action(step.action),
                "dsl_mode": step.mode,
                "expect": [
                    _effect_to_assertion(check, snapshot_name)
                    for check in step.checks
                ],
                "contract_refs": [check.source for check in step.checks],
            }
            if step.component:
                action_step["component"] = step.component
                if step.selector:
                    action_step["selector"] = step.selector
            if step.actor:
                action_step["actor"] = step.actor
            if step.action == "wait":
                action_step["ms"] = step.input.get("ms", 100)
            if step.action == "goto":
                action_step["path"] = step.input.get("path", "")
            if step.action == "event":
                action_step["event"] = step.input.get("event", "")
                action_step["payload"] = step.input.get("payload", {})
            if step.action == "upload":
                action_step["file"] = step.input.get("file", {})
            if step.action in {"fill", "select"}:
                action_step["value"] = step.input.get("value", "")
            if step.navigates_to:
                action_step["expect"].append(
                    {
                        "type": "browser_page_equals",
                        "expected": step.navigates_to,
                    }
                )
            web_steps.append(action_step)

        scenarios.append(
            {
                "id": scenario.id,
                "kind": scenario.kind,
                "tier": scenario.tier,
                "weight": scenario.weight,
                "visibility": scenario.visibility,
                "difficulty": scenario.difficulty,
                "description": scenario.description,
                "steps": web_steps,
                "contract_refs": [f"dsl:{scenario.id}"],
                "_source": scenario.source or "compiled-dsl",
                "dsl_step_count": len(scenario.steps),
            }
        )

    return ScenarioSet(
        version=str(scenarios_dsl.get("dsl_version", "0.1")),
        scenarios=scenarios,
        raw={"compiled_from": "dsl", "source": scenarios_dsl},
        sources=list(scenarios_dsl.get("_sources", ["compiled-dsl"])),
    )


def _web_action(action: str) -> str:
    if action == "toggle":
        return "click"
    return action


def _precondition_to_assertion(check: CompiledCheck) -> dict[str, Any]:
    return _state_check_to_assertion(check, phase="pre")


def _effect_to_assertion(check: CompiledCheck, snapshot_name: str) -> dict[str, Any]:
    spec = check.spec
    if check.op == "changed_by":
        return {
            "type": "state_delta",
            "path": check.path,
            "from": snapshot_name,
            "by": spec["by"],
        }
    if check.op == "advanced_time_by":
        return {
            "type": "state_time_advanced_by",
            "path": check.path,
            "from": snapshot_name,
            "by": spec["by"],
        }
    if check.op == "changed_by_path":
        return {
            "type": "state_delta_from_path",
            "path": check.path,
            "from": snapshot_name,
            "by_path": spec["by_path"],
            "multiplier": spec.get("multiplier", 1),
        }
    if check.op == "changed":
        return {
            "type": "state_changed",
            "path": check.path,
            "from": snapshot_name,
        }
    if check.op == "unchanged":
        return {
            "type": "state_unchanged",
            "path": check.path,
            "from": snapshot_name,
        }
    if check.op == "length_changed_by":
        return {
            "type": "state_length_delta",
            "path": check.path,
            "from": snapshot_name,
            "by": spec["by"],
        }
    if check.op == "appended":
        return {
            "type": "state_appended",
            "path": check.path,
            "from": snapshot_name,
            "expected": spec["value"],
        }
    if check.op == "appended_object":
        return {
            "type": "state_appended_object",
            "path": check.path,
            "from": snapshot_name,
            "value": spec["value"],
        }
    if check.op == "removed_first":
        return {
            "type": "state_removed_first",
            "path": check.path,
            "from": snapshot_name,
        }
    if check.op == "removed_first_where":
        return {
            "type": "state_removed_first_where",
            "path": check.path,
            "from": snapshot_name,
            "where": spec["where"],
        }
    if check.op == "removed_all_where":
        return {
            "type": "state_removed_all_where",
            "path": check.path,
            "from": snapshot_name,
            "where": spec["where"],
        }
    if check.op == "removed_all_where_after":
        return {
            "type": "state_removed_all_where_after",
            "path": check.path,
            "from": snapshot_name,
            "where": spec["where"],
        }
    if check.op == "updated_first_where":
        return {
            "type": "state_updated_first_where",
            "path": check.path,
            "from": snapshot_name,
            "where": spec["where"],
            "updates": spec["updates"],
        }
    if check.op == "updated_all_where":
        return {
            "type": "state_updated_all_where",
            "path": check.path,
            "from": snapshot_name,
            "where": spec["where"],
            "updates": spec["updates"],
        }
    if check.op == "updated_all_where_after":
        return {
            "type": "state_updated_all_where_after",
            "path": check.path,
            "from": snapshot_name,
            "where": spec["where"],
            "updates": spec["updates"],
        }
    if check.op == "updated_first_child_where":
        return {
            "type": "state_updated_first_child_where",
            "path": check.path,
            "from": snapshot_name,
            "parent_where": spec.get("parent_where", []),
            "child_path": spec["child_path"],
            "child_where": spec["child_where"],
            "updates": spec["updates"],
        }
    if check.op == "removed_first_child_where":
        return {
            "type": "state_removed_first_child_where",
            "path": check.path,
            "from": snapshot_name,
            "parent_where": spec.get("parent_where", []),
            "child_path": spec["child_path"],
            "child_where": spec["child_where"],
        }
    if check.op == "updated_object_fields":
        return {
            "type": "state_updated_object_fields",
            "path": check.path,
            "from": snapshot_name,
            "updates": spec["updates"],
        }
    if check.op == "removed_object_fields":
        return {
            "type": "state_removed_object_fields",
            "path": check.path,
            "from": snapshot_name,
            "fields": spec["fields"],
        }
    if check.op == "moved_first_where":
        return {
            "type": "state_moved_first_where",
            "path": check.path,
            "from": snapshot_name,
            "where": spec["where"],
            "to_index": spec["to_index"],
        }
    if check.op == "appended_from_first_where":
        return {
            "type": "state_appended_from_first_where",
            "path": check.path,
            "from": snapshot_name,
            "source_path": spec["source_path"],
            "where": spec["where"],
            "updates": spec.get("updates", {}),
        }
    if check.op == "toggled":
        return {
            "type": "state_relation",
            "path": check.path,
            "operator": "!=",
            "from": snapshot_name,
        }
    return _state_check_to_assertion(check, phase="post")


def _state_check_to_assertion(check: CompiledCheck, *, phase: str) -> dict[str, Any]:
    spec = check.spec
    if check.op == "table_order_equals":
        return {
            "type": "table_order_equals",
            "table": spec["table"],
            "expected": spec["expected"],
        }
    if check.op == "table_row_count_equals":
        return {
            "type": "table_row_count_equals",
            "table": spec["table"],
            "expected": spec["expected"],
        }
    if check.op == "table_cell_equals":
        return {
            "type": "table_cell_equals",
            "table": spec["table"],
            "row_id": spec["row_id"],
            "column": spec["column"],
            "expected": spec["expected"],
        }
    if check.op == "equals":
        return {
            "type": "state_equals",
            "path": check.path,
            "expected": spec["value"],
        }
    if check.op == "equals_normalized":
        return {
            "type": "state_normalized_equals",
            "path": check.path,
            "expected": spec["value"],
            "normalizers": spec.get("normalizers", spec.get("normalizer")),
        }
    if check.op == "truthy":
        return {
            "type": "state_truthy",
            "path": check.path,
        }
    if check.op == "falsey":
        return {
            "type": "state_falsey",
            "path": check.path,
        }
    if check.op == "one_of":
        return {
            "type": "state_one_of",
            "path": check.path,
            "values": spec["values"],
        }
    if check.op == "not_one_of":
        return {
            "type": "state_not_one_of",
            "path": check.path,
            "values": spec["values"],
        }
    if check.op == "contains":
        return {
            "type": "state_contains",
            "path": check.path,
            "expected": spec["value"],
        }
    if check.op == "not_contains":
        return {
            "type": "state_not_contains",
            "path": check.path,
            "expected": spec["value"],
        }
    if check.op == "matches":
        return {
            "type": "state_matches",
            "path": check.path,
            "pattern": spec["pattern"],
        }
    if check.op == "equals_template":
        return {
            "type": "state_template_equals",
            "path": check.path,
            "template": spec["template"],
        }
    if check.op == "equals_linear":
        assertion = {
            "type": "state_linear_equals",
            "path": check.path,
            "terms": spec["terms"],
            "constant": spec.get("constant", 0),
        }
        if "round" in spec:
            assertion["round"] = spec["round"]
        return assertion
    if check.op == "equals_piecewise_linear":
        return {
            "type": "state_piecewise_linear_equals",
            "path": check.path,
            "cases": spec["cases"],
            "default": spec["default"],
        }
    if check.op == "equals_length":
        return {
            "type": "state_length_equals",
            "path": check.path,
            "source_path": spec["source_path"],
        }
    if check.op == "equals_count_where":
        return {
            "type": "state_count_where_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "where": spec["where"],
        }
    if check.op == "equals_sum":
        assertion = {
            "type": "state_sum_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "field": spec["field"],
            "where": spec.get("where", []),
            "constant": spec.get("constant", 0),
            "multiplier": spec.get("multiplier", 1),
        }
        if "round" in spec:
            assertion["round"] = spec["round"]
        return assertion
    if check.op == "equals_any_where":
        return {
            "type": "state_any_where_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "where": spec["where"],
        }
    if check.op == "equals_first_item_field":
        return {
            "type": "state_first_item_field_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "field": spec["field"],
            "default": spec["default"],
        }
    if check.op == "equals_last_item_field":
        return {
            "type": "state_last_item_field_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "field": spec["field"],
            "default": spec["default"],
        }
    if check.op == "equals_filter":
        return {
            "type": "state_filter_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "where": spec.get("where", []),
            "order_by": spec.get("order_by", []),
        }
    if check.op == "equals_join_projection":
        return {
            "type": "state_join_projection_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "lookup_path": spec["lookup_path"],
            "source_key": spec["source_key"],
            "lookup_key": spec["lookup_key"],
            "where": spec.get("where", []),
            "fields": spec["fields"],
        }
    if check.op == "equals_object_key_count":
        return {
            "type": "state_object_key_count_equals",
            "path": check.path,
            "source_path": spec["source_path"],
        }
    if check.op == "equals_nested_count_where":
        return {
            "type": "state_nested_count_where_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "parent_where": spec.get("parent_where", []),
            "child_path": spec["child_path"],
            "child_where": spec["child_where"],
        }
    if check.op == "equals_nested_sum":
        assertion = {
            "type": "state_nested_sum_equals",
            "path": check.path,
            "source_path": spec["source_path"],
            "parent_where": spec.get("parent_where", []),
            "child_path": spec["child_path"],
            "child_where": spec.get("child_where", []),
            "field": spec["field"],
            "constant": spec.get("constant", 0),
            "multiplier": spec.get("multiplier", 1),
        }
        if "round" in spec:
            assertion["round"] = spec["round"]
        return assertion
    if check.op == "relation":
        assertion = {
            "type": "state_relation",
            "path": check.path,
            "operator": spec.get("operator", spec.get("relation")),
        }
        if "other_path" in spec:
            assertion["other_path"] = spec["other_path"]
        elif "value" in spec:
            assertion["value"] = spec["value"]
        else:
            raise ValueError(f"{phase} relation check requires other_path or value")
        return assertion
    raise ValueError(f"Cannot convert DSL {phase} check {check.op!r} to web assertion")
