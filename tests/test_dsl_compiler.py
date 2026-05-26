from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from detoxbench.dsl.compiler import DslCompileError
from detoxbench.dsl.compiler import compile_bundle
from detoxbench.dsl.compiler import evaluate_trace
from detoxbench.dsl.compiler import load_dsl_yaml
from detoxbench.dsl.web_bridge import compile_dsl_to_web_suite


def test_compiles_contract_effects_and_evaluates_positive_trace() -> None:
    compiled = compile_bundle(_contract(), _scenario())[0]

    assert compiled.id == "increment_and_label"
    assert compiled.steps[0].selector == '[data-testid="increment"]'
    assert compiled.steps[0].mode == "normal"
    assert [check.op for check in compiled.steps[0].preconditions] == ["equals"]
    assert [check.op for check in compiled.steps[0].checks] == [
        "changed_by_path",
        "equals",
        "unchanged",
        "relation",
    ]

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {"value": 0, "step_size": 2, "locked": False, "last_action": "", "label": ""},
                "after": {"value": 2, "step_size": 2, "locked": False, "last_action": "increment", "label": ""},
            },
            {
                "before": {"value": 2, "step_size": 2, "locked": False, "last_action": "increment", "label": ""},
                "after": {
                    "value": 2,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "edit_label",
                    "label": "Apollo",
                },
            },
        ],
    )

    assert report.passed
    assert report.first_failure is None


def test_trace_failure_reports_the_failed_compiled_check() -> None:
    compiled = compile_bundle(_contract(), _scenario())[0]

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {"value": 0, "step_size": 2, "locked": False, "last_action": "", "label": ""},
                "after": {"value": 0, "step_size": 2, "locked": False, "last_action": "increment", "label": ""},
            },
            {
                "before": {"value": 0, "step_size": 2, "locked": False, "last_action": "increment", "label": ""},
                "after": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "edit_label",
                    "label": "Apollo",
                },
            },
        ],
    )

    assert not report.passed
    failure = report.first_failure
    assert failure is not None
    assert failure.type == "dsl_post_changed_by_path"
    assert failure.actual == 0
    assert failure.expected == 2


def test_precondition_failure_is_a_step_assertion_failure() -> None:
    compiled = compile_bundle(_contract(), _scenario())[0]

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {"value": 0, "step_size": 1, "locked": True, "last_action": "", "label": ""},
                "after": {"value": 1, "step_size": 1, "locked": True, "last_action": "increment", "label": ""},
            },
            {
                "before": {"value": 1, "step_size": 1, "locked": True, "last_action": "increment", "label": ""},
                "after": {
                    "value": 1,
                    "step_size": 1,
                    "locked": True,
                    "last_action": "edit_label",
                    "label": "Apollo",
                },
            },
        ],
    )

    assert not report.passed
    assert report.first_failure is not None
    assert report.first_failure.type == "dsl_pre_equals"
    assert report.first_failure.actual is True
    assert report.first_failure.expected is False


def test_unknown_component_is_rejected_at_compile_time() -> None:
    scenarios = {
        "dsl_version": "0.1",
        "scenarios": [
            {
                "id": "bad_component",
                "steps": [{"do": "missing_button.click"}],
            }
        ],
    }

    with pytest.raises(DslCompileError, match="unknown component"):
        compile_bundle(_contract(), scenarios)


def test_undeclared_state_path_is_rejected_at_compile_time() -> None:
    contract = _contract()
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {"op": "equals", "path": "missing.path", "value": 1}
    )

    with pytest.raises(DslCompileError, match="undeclared state path"):
        compile_bundle(contract, _scenario())


def test_numeric_checks_require_numeric_state_paths() -> None:
    contract = _contract()
    contract["components"]["label_input"]["actions"]["fill"]["effects"].append(
        {"op": "changed_by", "path": "label", "by": 1}
    )

    with pytest.raises(DslCompileError, match="requires number path"):
        compile_bundle(contract, _scenario())


def test_changed_by_path_requires_declared_numeric_delta_path() -> None:
    contract = _contract()
    contract["components"]["increment_button"]["actions"]["click"]["effects"][0] = {
        "op": "changed_by_path",
        "path": "value",
        "by_path": "label",
    }

    with pytest.raises(DslCompileError, match="requires number by_path"):
        compile_bundle(contract, _scenario())


def test_value_from_must_resolve_from_step_input() -> None:
    scenarios = {
        "dsl_version": "0.1",
        "scenarios": [
            {
                "id": "missing_input",
                "steps": [{"do": "label_input.fill"}],
            }
        ],
    }

    with pytest.raises(DslCompileError, match="cannot be resolved"):
        compile_bundle(_contract(), scenarios)


def test_v02_collection_checks_compile_evaluate_and_lower() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.2"
    contract["state"]["initial"]["history"] = []
    contract["state"]["initial"]["status"] = ""
    contract["state"]["schema"]["history"] = {"type": "array"}
    contract["state"]["schema"]["status"] = {"type": "string"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].extend(
        [
            {"op": "appended", "path": "history", "value": "increment"},
            {"op": "length_changed_by", "path": "history", "by": 1},
            {"op": "contains", "path": "history", "value": "increment"},
            {"op": "matches", "path": "status", "pattern": "^value:"},
        ]
    )

    scenarios = {
        "dsl_version": "0.2",
        "scenarios": [
            {
                "id": "collection_ops",
                "steps": [
                    {
                        "do": "increment_button.click",
                        "expect": [
                            {"op": "not_contains", "path": "history", "value": "decrement"}
                        ],
                    }
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    assert [check.op for check in compiled.steps[0].checks][-5:] == [
        "appended",
        "length_changed_by",
        "contains",
        "matches",
        "not_contains",
    ]

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 0,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "history": [],
                    "status": "value:0",
                },
                "after": {
                    "value": 1,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "increment",
                    "label": "",
                    "history": ["increment"],
                    "status": "value:1",
                },
            }
        ],
    )
    assert report.passed

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)
    action_step = lowered.scenarios[0]["steps"][1]
    assert action_step["expect"][-5:] == [
        {
            "type": "state_appended",
            "path": "history",
            "from": "dsl_before_1",
            "expected": "increment",
        },
        {"type": "state_length_delta", "path": "history", "from": "dsl_before_1", "by": 1},
        {"type": "state_contains", "path": "history", "expected": "increment"},
        {"type": "state_matches", "path": "status", "pattern": "^value:"},
        {"type": "state_not_contains", "path": "history", "expected": "decrement"},
    ]


def test_v01_rejects_v02_only_checks() -> None:
    contract = _contract()
    contract["state"]["initial"]["history"] = []
    contract["state"]["schema"]["history"] = {"type": "array"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {"op": "length_changed_by", "path": "history", "by": 1}
    )

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, _scenario())


def test_contract_and_scenario_versions_must_match() -> None:
    scenarios = _scenario()
    scenarios["dsl_version"] = "0.2"

    with pytest.raises(DslCompileError, match="does not match"):
        compile_bundle(_contract(), scenarios)


def test_v03_blocked_mode_compiles_evaluates_and_lowers() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.3"
    contract["components"]["increment_button"]["actions"]["click"]["blocked_when"] = [
        {"op": "equals", "path": "locked", "value": True}
    ]
    contract["components"]["increment_button"]["actions"]["click"]["blocked_effects"] = [
        {"op": "unchanged", "path": "value"},
        {"op": "unchanged", "path": "last_action"},
    ]
    scenarios = {
        "dsl_version": "0.3",
        "scenarios": [
            {
                "id": "blocked_increment",
                "steps": [
                    {
                        "do": "increment_button.click",
                        "mode": "blocked",
                        "expect": [
                            {"op": "equals", "path": "locked", "value": True}
                        ],
                    }
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    step = compiled.steps[0]
    assert step.mode == "blocked"
    assert [check.op for check in step.preconditions] == ["equals"]
    assert [check.op for check in step.checks] == ["unchanged", "unchanged", "equals"]

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 9,
                    "step_size": 1,
                    "locked": True,
                    "last_action": "toggle_lock",
                    "label": "",
                },
                "after": {
                    "value": 9,
                    "step_size": 1,
                    "locked": True,
                    "last_action": "toggle_lock",
                    "label": "",
                },
            }
        ],
    )
    assert report.passed

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)
    action_step = lowered.scenarios[0]["steps"][1]
    assert action_step["dsl_mode"] == "blocked"
    assert action_step["expect"][:2] == [
        {"type": "state_unchanged", "path": "value", "from": "dsl_before_1"},
        {"type": "state_unchanged", "path": "last_action", "from": "dsl_before_1"},
    ]


def test_v02_rejects_blocked_mode_and_blocked_contract_semantics() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.2"
    contract["components"]["increment_button"]["actions"]["click"]["blocked_when"] = [
        {"op": "equals", "path": "locked", "value": True}
    ]
    contract["components"]["increment_button"]["actions"]["click"]["blocked_effects"] = [
        {"op": "unchanged", "path": "value"}
    ]
    scenarios = _scenario()
    scenarios["dsl_version"] = "0.2"

    with pytest.raises(DslCompileError, match="require DSL 0.3"):
        compile_bundle(contract, scenarios)

    contract = _contract()
    contract["dsl_version"] = "0.2"
    scenarios = {
        "dsl_version": "0.2",
        "scenarios": [
            {
                "id": "blocked_increment",
                "steps": [{"do": "increment_button.click", "mode": "blocked"}],
            }
        ],
    }

    with pytest.raises(DslCompileError, match="unsupported mode"):
        compile_bundle(contract, scenarios)


def test_v04_template_checks_compile_evaluate_and_lower() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.4"
    contract["state"]["initial"]["history"] = []
    contract["state"]["initial"]["status"] = "value:0 | last:none | history:0"
    contract["state"]["schema"]["history"] = {"type": "array"}
    contract["state"]["schema"]["status"] = {"type": "string"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {
            "op": "equals_template",
            "path": "status",
            "template": "value:{value} | last:{last_action|default:none} | history:{history.length}",
        }
    )
    scenarios = {
        "dsl_version": "0.4",
        "scenarios": [
            {
                "id": "status_template",
                "steps": [{"do": "increment_button.click"}],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    assert compiled.steps[0].checks[-1].op == "equals_template"

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "history": [],
                    "status": "value:0 | last:none | history:0",
                },
                "after": {
                    "value": 2,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "increment",
                    "label": "",
                    "history": ["increment"],
                    "status": "value:2 | last:increment | history:1",
                },
            }
        ],
    )
    assert report.passed

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)
    assert lowered.scenarios[0]["steps"][1]["expect"][-1] == {
        "type": "state_template_equals",
        "path": "status",
        "template": "value:{value} | last:{last_action|default:none} | history:{history.length}",
    }


def test_v03_rejects_template_checks() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.3"
    contract["state"]["initial"]["status"] = ""
    contract["state"]["schema"]["status"] = {"type": "string"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {
            "op": "equals_template",
            "path": "status",
            "template": "value:{value}",
        }
    )
    scenarios = _scenario()
    scenarios["dsl_version"] = "0.3"

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_v041_linear_checks_compile_evaluate_and_lower() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.4.1"
    contract["state"]["initial"]["subtotal"] = 0
    contract["state"]["initial"]["shipping_fee"] = 6
    contract["state"]["initial"]["coupon_credit"] = 0
    contract["state"]["initial"]["grand_total"] = 6
    contract["state"]["schema"]["subtotal"] = {"type": "number"}
    contract["state"]["schema"]["shipping_fee"] = {"type": "number"}
    contract["state"]["schema"]["coupon_credit"] = {"type": "number"}
    contract["state"]["schema"]["grand_total"] = {"type": "number"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {
            "op": "equals_linear",
            "path": "grand_total",
            "terms": [
                {"path": "subtotal", "multiplier": 1.08},
                {"path": "shipping_fee"},
                {"path": "coupon_credit", "multiplier": -1},
            ],
            "round": 2,
        }
    )
    scenarios = {
        "dsl_version": "0.4.1",
        "scenarios": [
            {
                "id": "cart_total_formula",
                "steps": [{"do": "increment_button.click"}],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    assert compiled.steps[0].checks[-1].op == "equals_linear"

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 0,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "subtotal": 0,
                    "shipping_fee": 6,
                    "coupon_credit": 0,
                    "grand_total": 6,
                },
                "after": {
                    "value": 1,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "increment",
                    "label": "",
                    "subtotal": 45,
                    "shipping_fee": 6,
                    "coupon_credit": 5,
                    "grand_total": 49.6,
                },
            }
        ],
    )
    assert report.passed

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)
    assert lowered.scenarios[0]["steps"][1]["expect"][-1] == {
        "type": "state_linear_equals",
        "path": "grand_total",
        "terms": [
            {"path": "subtotal", "multiplier": 1.08},
            {"path": "shipping_fee"},
            {"path": "coupon_credit", "multiplier": -1},
        ],
        "constant": 0,
        "round": 2,
    }


def test_v042_piecewise_linear_checks_compile_evaluate_and_lower() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.4.2"
    contract["state"]["initial"]["subtotal"] = 0
    contract["state"]["initial"]["item_count"] = 0
    contract["state"]["initial"]["shipping_fee"] = 6
    contract["state"]["schema"]["subtotal"] = {"type": "number"}
    contract["state"]["schema"]["item_count"] = {"type": "number"}
    contract["state"]["schema"]["shipping_fee"] = {"type": "number"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {
            "op": "equals_piecewise_linear",
            "path": "shipping_fee",
            "cases": [
                {
                    "when": [
                        {
                            "op": "relation",
                            "path": "subtotal",
                            "operator": ">=",
                            "value": 75,
                        }
                    ],
                    "formula": {"constant": 0},
                },
                {
                    "when": [
                        {
                            "op": "relation",
                            "path": "item_count",
                            "operator": ">=",
                            "value": 4,
                        }
                    ],
                    "formula": {"constant": 2},
                },
            ],
            "default": {"constant": 6},
        }
    )
    scenarios = {
        "dsl_version": "0.4.2",
        "scenarios": [
            {
                "id": "shipping_piecewise_formula",
                "steps": [{"do": "increment_button.click"}],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    assert compiled.steps[0].checks[-1].op == "equals_piecewise_linear"

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 0,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "subtotal": 0,
                    "item_count": 0,
                    "shipping_fee": 6,
                },
                "after": {
                    "value": 1,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "increment",
                    "label": "",
                    "subtotal": 72,
                    "item_count": 4,
                    "shipping_fee": 2,
                },
            }
        ],
    )
    assert report.passed

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)
    assert lowered.scenarios[0]["steps"][1]["expect"][-1] == {
        "type": "state_piecewise_linear_equals",
        "path": "shipping_fee",
        "cases": [
            {
                "when": [
                    {
                        "op": "relation",
                        "path": "subtotal",
                        "operator": ">=",
                        "value": 75,
                    }
                ],
                "formula": {"constant": 0},
            },
            {
                "when": [
                    {
                        "op": "relation",
                        "path": "item_count",
                        "operator": ">=",
                        "value": 4,
                    }
                ],
                "formula": {"constant": 2},
            },
        ],
        "default": {"constant": 6},
    }


def test_v04_rejects_linear_checks() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.4"
    contract["state"]["initial"]["grand_total"] = 0
    contract["state"]["schema"]["grand_total"] = {"type": "number"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {
            "op": "equals_linear",
            "path": "grand_total",
            "terms": [{"path": "value"}],
        }
    )
    scenarios = _scenario()
    scenarios["dsl_version"] = "0.4"

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_v041_rejects_piecewise_linear_checks() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.4.1"
    contract["state"]["initial"]["shipping_fee"] = 0
    contract["state"]["schema"]["shipping_fee"] = {"type": "number"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {
            "op": "equals_piecewise_linear",
            "path": "shipping_fee",
            "cases": [
                {
                    "when": [{"op": "truthy", "path": "locked"}],
                    "formula": {"constant": 0},
                }
            ],
            "default": {"constant": 6},
        }
    )
    scenarios = _scenario()
    scenarios["dsl_version"] = "0.4.1"

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_v050_collection_checks_compile_evaluate_and_lower() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.5.0"
    contract["state"]["initial"].update(
        {
            "cases": [],
            "queue_count": 0,
            "urgent_count": 0,
            "acuity_total": 0,
            "has_urgent": False,
            "next_case_type": "none",
            "last_case_type": "none",
        }
    )
    contract["state"]["schema"].update(
        {
            "cases": {"type": "array"},
            "queue_count": {"type": "number"},
            "urgent_count": {"type": "number"},
            "acuity_total": {"type": "number"},
            "has_urgent": {"type": "boolean"},
            "next_case_type": {"type": "string"},
            "last_case_type": {"type": "string"},
        }
    )
    collection_effects = [
        {"op": "equals_length", "path": "queue_count", "source_path": "cases"},
        {
            "op": "equals_count_where",
            "path": "urgent_count",
            "source_path": "cases",
            "where": [{"op": "truthy", "field": "urgent"}],
        },
        {"op": "equals_sum", "path": "acuity_total", "source_path": "cases", "field": "acuity"},
        {
            "op": "equals_any_where",
            "path": "has_urgent",
            "source_path": "cases",
            "where": [{"op": "truthy", "field": "urgent"}],
        },
        {
            "op": "equals_first_item_field",
            "path": "next_case_type",
            "source_path": "cases",
            "field": "type",
            "default": "none",
        },
        {
            "op": "equals_last_item_field",
            "path": "last_case_type",
            "source_path": "cases",
            "field": "type",
            "default": "none",
        },
    ]
    contract["components"]["add_urgent_button"] = {
        "kind": "button",
        "selector": '[data-testid="add-urgent"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "appended",
                        "path": "cases",
                        "value": {
                            "type": "urgent",
                            "acuity": 5,
                            "urgent": True,
                        },
                    },
                    *collection_effects,
                ]
            }
        },
    }
    contract["components"]["process_next_button"] = {
        "kind": "button",
        "selector": '[data-testid="process-next"]',
        "actions": {
            "click": {
                "preconditions": [
                    {"op": "relation", "path": "queue_count", "operator": ">", "value": 0}
                ],
                "effects": [
                    {"op": "removed_first", "path": "cases"},
                    *collection_effects,
                ],
            }
        },
    }
    scenarios = {
        "dsl_version": "0.5.0",
        "scenarios": [
            {
                "id": "collection_queue_projection",
                "steps": [
                    {"do": "add_urgent_button.click"},
                    {"do": "process_next_button.click"},
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    assert [check.op for check in compiled.steps[0].checks][-6:] == [
        "equals_length",
        "equals_count_where",
        "equals_sum",
        "equals_any_where",
        "equals_first_item_field",
        "equals_last_item_field",
    ]
    assert compiled.steps[1].checks[0].op == "removed_first"

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 0,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "cases": [],
                    "queue_count": 0,
                    "urgent_count": 0,
                    "acuity_total": 0,
                    "has_urgent": False,
                    "next_case_type": "none",
                    "last_case_type": "none",
                },
                "after": {
                    "value": 0,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "cases": [{"type": "urgent", "acuity": 5, "urgent": True}],
                    "queue_count": 1,
                    "urgent_count": 1,
                    "acuity_total": 5,
                    "has_urgent": True,
                    "next_case_type": "urgent",
                    "last_case_type": "urgent",
                },
            },
            {
                "before": {
                    "value": 0,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "cases": [{"type": "urgent", "acuity": 5, "urgent": True}],
                    "queue_count": 1,
                    "urgent_count": 1,
                    "acuity_total": 5,
                    "has_urgent": True,
                    "next_case_type": "urgent",
                    "last_case_type": "urgent",
                },
                "after": {
                    "value": 0,
                    "step_size": 1,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "cases": [],
                    "queue_count": 0,
                    "urgent_count": 0,
                    "acuity_total": 0,
                    "has_urgent": False,
                    "next_case_type": "none",
                    "last_case_type": "none",
                },
            },
        ],
    )
    assert report.passed

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)
    process_step = lowered.scenarios[0]["steps"][3]
    assert process_step["expect"][:7] == [
        {"type": "state_removed_first", "path": "cases", "from": "dsl_before_2"},
        {"type": "state_length_equals", "path": "queue_count", "source_path": "cases"},
        {
            "type": "state_count_where_equals",
            "path": "urgent_count",
            "source_path": "cases",
            "where": [{"op": "truthy", "field": "urgent"}],
        },
        {
            "type": "state_sum_equals",
            "path": "acuity_total",
            "source_path": "cases",
            "field": "acuity",
            "where": [],
            "constant": 0,
            "multiplier": 1,
        },
        {
            "type": "state_any_where_equals",
            "path": "has_urgent",
            "source_path": "cases",
            "where": [{"op": "truthy", "field": "urgent"}],
        },
        {
            "type": "state_first_item_field_equals",
            "path": "next_case_type",
            "source_path": "cases",
            "field": "type",
            "default": "none",
        },
        {
            "type": "state_last_item_field_equals",
            "path": "last_case_type",
            "source_path": "cases",
            "field": "type",
            "default": "none",
        },
    ]


def test_v049_rejects_v050_version_and_v048_rejects_last_item_projection() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.4.8"
    contract["state"]["initial"]["cases"] = []
    contract["state"]["initial"]["last_case_type"] = "none"
    contract["state"]["schema"]["cases"] = {"type": "array"}
    contract["state"]["schema"]["last_case_type"] = {"type": "string"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {
            "op": "equals_last_item_field",
            "path": "last_case_type",
            "source_path": "cases",
            "field": "type",
            "default": "none",
        }
    )
    scenarios = _scenario()
    scenarios["dsl_version"] = "0.4.8"

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_v060_collection_identity_checks_compile_evaluate_and_lower() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.6.0"
    contract["state"]["initial"].update(
        {
            "backlog": [
                {"id": "alpha", "lane": "backlog", "priority": "normal", "points": 2},
                {"id": "beta", "lane": "backlog", "priority": "normal", "points": 5},
                {"id": "gamma", "lane": "backlog", "priority": "low", "points": 1},
            ],
            "active": [],
            "done": [],
        }
    )
    contract["state"]["schema"].update(
        {
            "backlog": {"type": "array"},
            "active": {"type": "array"},
            "done": {"type": "array"},
        }
    )
    contract["components"]["start_beta_button"] = {
        "kind": "button",
        "selector": '[data-testid="start-beta"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "removed_first_where",
                        "path": "backlog",
                        "where": [{"op": "equals", "field": "id", "value": "beta"}],
                    },
                    {
                        "op": "appended_from_first_where",
                        "path": "active",
                        "source_path": "backlog",
                        "where": [{"op": "equals", "field": "id", "value": "beta"}],
                        "updates": {"lane": "active"},
                    },
                ]
            }
        },
    }
    contract["components"]["escalate_gamma_button"] = {
        "kind": "button",
        "selector": '[data-testid="escalate-gamma"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_first_where",
                        "path": "backlog",
                        "where": [{"op": "equals", "field": "id", "value": "gamma"}],
                        "updates": {"priority": "urgent", "points": 8},
                    }
                ]
            }
        },
    }
    contract["components"]["move_gamma_front_button"] = {
        "kind": "button",
        "selector": '[data-testid="move-gamma-front"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "moved_first_where",
                        "path": "backlog",
                        "where": [{"op": "equals", "field": "id", "value": "gamma"}],
                        "to_index": 0,
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "0.6.0",
        "scenarios": [
            {
                "id": "identity_transfer_update_move",
                "steps": [
                    {"do": "start_beta_button.click"},
                    {"do": "escalate_gamma_button.click"},
                    {"do": "move_gamma_front_button.click"},
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    assert [check.op for check in compiled.steps[0].checks] == [
        "removed_first_where",
        "appended_from_first_where",
    ]
    assert compiled.steps[1].checks[0].op == "updated_first_where"
    assert compiled.steps[2].checks[0].op == "moved_first_where"

    beta_started = {
        "backlog": [
            {"id": "alpha", "lane": "backlog", "priority": "normal", "points": 2},
            {"id": "gamma", "lane": "backlog", "priority": "low", "points": 1},
        ],
        "active": [
            {"id": "beta", "lane": "active", "priority": "normal", "points": 5},
        ],
        "done": [],
        "value": 0,
        "step_size": 1,
        "locked": False,
        "last_action": "",
        "label": "",
    }
    gamma_escalated = {
        **beta_started,
        "backlog": [
            {"id": "alpha", "lane": "backlog", "priority": "normal", "points": 2},
            {"id": "gamma", "lane": "backlog", "priority": "urgent", "points": 8},
        ],
    }
    gamma_front = {
        **gamma_escalated,
        "backlog": [
            {"id": "gamma", "lane": "backlog", "priority": "urgent", "points": 8},
            {"id": "alpha", "lane": "backlog", "priority": "normal", "points": 2},
        ],
    }

    report = evaluate_trace(
        compiled,
        [
            {
                "before": contract["state"]["initial"],
                "after": beta_started,
            },
            {
                "before": beta_started,
                "after": gamma_escalated,
            },
            {
                "before": gamma_escalated,
                "after": gamma_front,
            },
        ],
    )
    assert report.passed

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)
    first_action = lowered.scenarios[0]["steps"][1]
    assert {
        "type": "state_removed_first_where",
        "path": "backlog",
        "from": "dsl_before_1",
        "where": [{"op": "equals", "field": "id", "value": "beta"}],
    } in first_action["expect"]
    assert {
        "type": "state_appended_from_first_where",
        "path": "active",
        "from": "dsl_before_1",
        "source_path": "backlog",
        "where": [{"op": "equals", "field": "id", "value": "beta"}],
        "updates": {"lane": "active"},
    } in first_action["expect"]


def test_v052_rejects_later_reorder_op() -> None:
    contract = _contract()
    contract["dsl_version"] = "0.5.2"
    contract["state"]["initial"]["items"] = []
    contract["state"]["schema"]["items"] = {"type": "array"}
    contract["components"]["increment_button"]["actions"]["click"]["effects"].append(
        {
            "op": "moved_first_where",
            "path": "items",
            "where": [{"op": "equals", "field": "id", "value": "alpha"}],
            "to_index": 0,
        }
    )
    scenarios = _scenario()
    scenarios["dsl_version"] = "0.5.2"

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_detectable_conflicting_step_expectations_are_rejected() -> None:
    scenarios = {
        "dsl_version": "0.1",
        "scenarios": [
            {
                "id": "conflict",
                "steps": [
                    {
                        "do": "increment_button.click",
                        "expect": [
                            {"op": "equals", "path": "last_action", "value": "not_increment"}
                        ],
                    }
                ],
            }
        ],
    }

    with pytest.raises(DslCompileError, match="conflicting equals"):
        compile_bundle(_contract(), scenarios)


def test_initial_state_must_match_declared_schema() -> None:
    contract = _contract()
    contract["state"]["initial"]["step_size"] = "large"

    with pytest.raises(DslCompileError, match="expected number"):
        compile_bundle(contract, _scenario())


def test_v100_dynamic_item_filter_and_rejected_mode_compile_evaluate_and_lower() -> None:
    contract = {
        "dsl_version": "1.0.0",
        "app": {"id": "work_orders", "name": "Work Orders", "capability": "dynamic_items"},
        "runtime": {
            "target": "web",
            "state_probe": {"kind": "javascript", "expression": "window.__DETOX_STATE__"},
        },
        "state": {
            "initial": {
                "orders": [],
                "visible_orders": [],
                "draft_title": "",
                "draft_priority": "normal",
                "next_id": "wo-1",
                "selected_id": "",
                "error": "",
            },
            "schema": {
                "orders": {"type": "array"},
                "visible_orders": {"type": "array"},
                "draft_title": {"type": "string"},
                "draft_priority": {"type": "string"},
                "next_id": {"type": "string"},
                "selected_id": {"type": "string"},
                "error": {"type": "string"},
            },
        },
        "components": {
            "title_input": {
                "kind": "input",
                "selector": "[data-testid='title']",
                "actions": {
                    "fill": {
                        "effects": [
                            {"op": "equals", "path": "draft_title", "value_from": "input.value"},
                            {"op": "equals_filter", "path": "visible_orders", "source_path": "orders"},
                        ]
                    }
                },
            },
            "select_id_input": {
                "kind": "input",
                "selector": "[data-testid='select-id']",
                "actions": {
                    "fill": {
                        "effects": [
                            {"op": "equals", "path": "selected_id", "value_from": "input.value"}
                        ]
                    }
                },
            },
            "submit_button": {
                "kind": "button",
                "selector": "[data-testid='submit']",
                "actions": {
                    "click": {
                        "preconditions": [
                            {"op": "relation", "path": "draft_title", "operator": "!=", "value": ""}
                        ],
                        "effects": [
                            {
                                "op": "appended_object",
                                "path": "orders",
                                "value": {
                                    "id": {"from_path": "next_id"},
                                    "title": {"from_path": "draft_title"},
                                    "priority": {"from_path": "draft_priority"},
                                },
                            },
                            {"op": "equals_filter", "path": "visible_orders", "source_path": "orders"},
                            {"op": "equals", "path": "error", "value": ""},
                        ],
                        "rejected_when": [
                            {"op": "equals", "path": "draft_title", "value": ""}
                        ],
                        "rejected_effects": [
                            {"op": "unchanged", "path": "orders"},
                            {"op": "unchanged", "path": "visible_orders"},
                            {"op": "equals", "path": "error", "value": "Title required"},
                        ],
                    }
                },
            },
            "escalate_button": {
                "kind": "button",
                "selector": "[data-testid='escalate']",
                "actions": {
                    "click": {
                        "preconditions": [
                            {"op": "relation", "path": "selected_id", "operator": "!=", "value": ""}
                        ],
                        "effects": [
                            {
                                "op": "updated_first_where",
                                "path": "orders",
                                "where": [{"op": "equals", "field": "id", "value_path": "selected_id"}],
                                "updates": {"priority": "urgent"},
                            },
                            {
                                "op": "equals_filter",
                                "path": "visible_orders",
                                "source_path": "orders",
                            },
                        ],
                    }
                },
            },
        },
    }
    scenarios = {
        "dsl_version": "1.0.0",
        "scenarios": [
            {
                "id": "create_then_reject",
                "steps": [
                    {"do": "title_input.fill", "input": {"value": "Replace router"}},
                    {"do": "submit_button.click"},
                ],
            },
            {
                "id": "reject_empty",
                "steps": [
                    {"do": "submit_button.click", "mode": "rejected"},
                ],
            },
        ],
    }

    compiled = compile_bundle(contract, scenarios)
    report = evaluate_trace(
        compiled[0],
        [
            {
                "before": {
                    "orders": [],
                    "visible_orders": [],
                    "draft_title": "",
                    "draft_priority": "normal",
                    "next_id": "wo-1",
                    "selected_id": "",
                    "error": "",
                },
                "after": {
                    "orders": [],
                    "visible_orders": [],
                    "draft_title": "Replace router",
                    "draft_priority": "normal",
                    "next_id": "wo-1",
                    "selected_id": "",
                    "error": "",
                },
            },
            {
                "before": {
                    "orders": [],
                    "visible_orders": [],
                    "draft_title": "Replace router",
                    "draft_priority": "normal",
                    "next_id": "wo-1",
                    "selected_id": "",
                    "error": "",
                },
                "after": {
                    "orders": [
                        {"id": "wo-1", "title": "Replace router", "priority": "normal"}
                    ],
                    "visible_orders": [
                        {"id": "wo-1", "title": "Replace router", "priority": "normal"}
                    ],
                    "draft_title": "Replace router",
                    "draft_priority": "normal",
                    "next_id": "wo-1",
                    "selected_id": "",
                    "error": "",
                },
            },
        ],
    )
    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert report.passed
    assert compiled[1].steps[0].mode == "rejected"
    assert any(
        assertion["type"] == "state_appended_object"
        for step in web_scenarios.scenarios[0]["steps"]
        for assertion in step.get("expect", [])
    )
    assert any(
        assertion["type"] == "state_filter_equals"
        for step in web_scenarios.scenarios[0]["steps"]
        for assertion in step.get("expect", [])
    )


def test_v110_pages_component_page_and_navigation_lower_to_browser_assertions() -> None:
    contract = {
        "dsl_version": "1.1.0",
        "app": {"id": "portal", "name": "Portal", "capability": "multipage"},
        "runtime": {
            "target": "web",
            "start_url": "/#/home",
            "state_probe": {"kind": "javascript", "expression": "window.__DETOX_STATE__"},
            "pages": {
                "home": {"path": "/#/home"},
                "intake": {"path": "/#/intake"},
            },
        },
        "state": {
            "initial": {"current_page": "home", "action_count": 0},
            "schema": {
                "current_page": {"type": "string"},
                "action_count": {"type": "number"},
            },
        },
        "components": {
            "go_intake": {
                "kind": "link",
                "selector": "[data-testid='go-intake']",
                "page": "home",
                "actions": {
                    "click": {
                        "navigate_to": "intake",
                        "effects": [
                            {"op": "equals", "path": "current_page", "value": "intake"},
                            {"op": "changed_by", "path": "action_count", "by": 1},
                        ],
                    }
                },
            }
        },
    }
    scenarios = {
        "dsl_version": "1.1.0",
        "scenarios": [{"id": "go_to_intake", "steps": [{"do": "go_intake.click"}]}],
    }

    compiled = compile_bundle(contract, scenarios)
    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert compiled[0].steps[0].page == "home"
    assert compiled[0].steps[0].navigates_to == "intake"
    snapshot_step, action_step = web_scenarios.scenarios[0]["steps"]
    assert {"type": "browser_page_equals", "expected": "home"} in snapshot_step["expect"]
    assert {"type": "browser_page_equals", "expected": "intake"} in action_step["expect"]


def test_component_page_requires_declared_page() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.0.2"
    contract["runtime"]["pages"] = {"home": {"path": "/#/home"}}
    contract["components"]["increment_button"]["page"] = "missing"
    scenarios = _scenario()
    scenarios["dsl_version"] = "1.0.2"

    with pytest.raises(DslCompileError, match="unknown page"):
        compile_bundle(contract, scenarios)


def test_v111_wait_step_lowers_to_web_wait() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.1.1"
    scenarios = {
        "dsl_version": "1.1.1",
        "scenarios": [
            {
                "id": "wait_for_label",
                "steps": [
                    {"do": "label_input.fill", "input": {"value": "queued"}},
                    {
                        "wait_ms": 125,
                        "expect": [
                            {"op": "equals", "path": "label", "value": "queued"}
                        ],
                    },
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert compiled.steps[1].action == "wait"
    assert compiled.steps[1].input == {"ms": 125}
    assert web_scenarios.scenarios[0]["steps"][3]["action"] == "wait"
    assert web_scenarios.scenarios[0]["steps"][3]["ms"] == 125


def test_v120_async_await_uses_declared_async_effects() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.2.0"
    contract["state"]["initial"]["request_status"] = "idle"
    contract["state"]["schema"]["request_status"] = {"type": "string"}
    contract["components"]["submit_button"] = {
        "kind": "button",
        "selector": "[data-testid='submit']",
        "actions": {
            "click": {
                "effects": [
                    {"op": "equals", "path": "request_status", "value": "submitting"}
                ],
                "async_effects": {
                    "after_ms": 180,
                    "effects": [
                        {"op": "equals", "path": "request_status", "value": "accepted"},
                        {"op": "equals", "path": "last_action", "value": "submit_done"},
                    ],
                },
            }
        },
    }
    scenarios = {
        "dsl_version": "1.2.0",
        "scenarios": [
            {
                "id": "submit_and_await",
                "steps": [
                    {"do": "submit_button.click"},
                    {"await": "submit_button.click"},
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert [step.action for step in compiled.steps] == ["click", "wait"]
    assert [check.source for check in compiled.steps[1].checks] == [
        "contract:submit_button.click:async_effect",
        "contract:submit_button.click:async_effect",
    ]
    wait_action = web_scenarios.scenarios[0]["steps"][3]
    assert wait_action["action"] == "wait"
    assert wait_action["ms"] == 180
    assert wait_action["expect"] == [
        {
            "type": "state_equals",
            "path": "request_status",
            "expected": "accepted",
        },
        {
            "type": "state_equals",
            "path": "last_action",
            "expected": "submit_done",
        },
    ]


def test_async_effects_requires_v120() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.1.1"
    contract["components"]["increment_button"]["actions"]["click"]["async_effects"] = {
        "after_ms": 100,
        "effects": [{"op": "equals", "path": "last_action", "value": "done"}],
    }
    scenarios = _scenario()
    scenarios["dsl_version"] = "1.1.1"

    with pytest.raises(DslCompileError, match="requires DSL 1.2.0"):
        compile_bundle(contract, scenarios)


def test_await_requires_action_with_async_effects() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.2.0"
    scenarios = {
        "dsl_version": "1.2.0",
        "scenarios": [{"id": "bad_await", "steps": [{"await": "increment_button.click"}]}],
    }

    with pytest.raises(DslCompileError, match="declares no async_effects"):
        compile_bundle(contract, scenarios)


def test_v130_selector_template_and_item_value_from_compile_lower_and_evaluate() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.3.0"
    contract["state"]["initial"]["tasks"] = [
        {"id": "T-1", "status": "open"},
        {"id": "T-2", "status": "open"},
    ]
    contract["state"]["schema"]["tasks"] = {"type": "array"}
    contract["components"]["complete_row_button"] = {
        "kind": "button",
        "selector_template": '[data-row-id="{input.row_id}"] [data-testid="complete-row"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_first_where",
                        "path": "tasks",
                        "where": [
                            {"op": "equals", "field": "id", "value_from": "input.row_id"}
                        ],
                        "updates": {"status": "done"},
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.3.0",
        "scenarios": [
            {
                "id": "complete_dynamic_row",
                "steps": [
                    {
                        "do": "complete_row_button.click",
                        "input": {"row_id": "T-2"},
                    }
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert compiled.steps[0].selector == '[data-row-id="T-2"] [data-testid="complete-row"]'
    assert compiled.steps[0].checks[0].spec["where"][0]["value"] == "T-2"
    assert web_scenarios.scenarios[0]["steps"][1]["selector"] == (
        '[data-row-id="T-2"] [data-testid="complete-row"]'
    )

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "tasks": [
                        {"id": "T-1", "status": "open"},
                        {"id": "T-2", "status": "open"},
                    ],
                },
                "after": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "tasks": [
                        {"id": "T-1", "status": "open"},
                        {"id": "T-2", "status": "done"},
                    ],
                },
            }
        ],
    )
    assert report.passed


def test_selector_template_requires_v121() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.2.0"
    contract["components"]["row_button"] = {
        "kind": "button",
        "selector_template": '[data-row-id="{input.row_id}"] button',
        "actions": {"click": {"effects": [{"op": "equals", "path": "last_action", "value": "row"}]}},
    }
    scenarios = {"dsl_version": "1.2.0", "scenarios": [{"id": "row", "steps": [{"do": "row_button.click"}]}]}

    with pytest.raises(DslCompileError, match="selector_template"):
        compile_bundle(contract, scenarios)


def test_item_condition_value_from_requires_v130() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.2.1"
    contract["state"]["initial"]["tasks"] = [{"id": "T-1"}]
    contract["state"]["schema"]["tasks"] = {"type": "array"}
    contract["components"]["row_button"] = {
        "kind": "button",
        "selector": "[data-testid='row']",
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_first_where",
                        "path": "tasks",
                        "where": [{"op": "equals", "field": "id", "value_from": "input.row_id"}],
                        "updates": {"status": "done"},
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.2.1",
        "scenarios": [{"id": "row", "steps": [{"do": "row_button.click", "input": {"row_id": "T-1"}}]}],
    }

    with pytest.raises(DslCompileError, match="value_from requires DSL 1.3.0"):
        compile_bundle(contract, scenarios)


def test_v140_bulk_where_operations_compile_lower_and_evaluate() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.4.0"
    contract["state"]["initial"]["items"] = [
        {"id": "A", "selected": True, "status": "queued"},
        {"id": "B", "selected": False, "status": "queued"},
        {"id": "C", "selected": True, "status": "queued"},
    ]
    contract["state"]["schema"]["items"] = {"type": "array"}
    contract["components"]["bulk_approve_button"] = {
        "kind": "button",
        "selector": '[data-testid="bulk-approve"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_all_where",
                        "path": "items",
                        "where": [{"op": "equals", "field": "selected", "value": True}],
                        "updates": {"status": "approved", "selected": False},
                    }
                ]
            }
        },
    }
    contract["components"]["remove_approved_button"] = {
        "kind": "button",
        "selector": '[data-testid="remove-approved"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "removed_all_where",
                        "path": "items",
                        "where": [{"op": "equals", "field": "status", "value": "approved"}],
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.4.0",
        "scenarios": [
            {
                "id": "bulk_approve_then_remove",
                "steps": [
                    {"do": "bulk_approve_button.click"},
                    {"do": "remove_approved_button.click"},
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert [check.op for step in compiled.steps for check in step.checks] == [
        "updated_all_where",
        "removed_all_where",
    ]
    assert web_scenarios.scenarios[0]["steps"][1]["expect"][0]["type"] == "state_updated_all_where"
    assert web_scenarios.scenarios[0]["steps"][3]["expect"][0]["type"] == "state_removed_all_where"

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "items": [
                        {"id": "A", "selected": True, "status": "queued"},
                        {"id": "B", "selected": False, "status": "queued"},
                        {"id": "C", "selected": True, "status": "queued"},
                    ],
                },
                "after": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "items": [
                        {"id": "A", "selected": False, "status": "approved"},
                        {"id": "B", "selected": False, "status": "queued"},
                        {"id": "C", "selected": False, "status": "approved"},
                    ],
                },
            },
            {
                "before": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "items": [
                        {"id": "A", "selected": False, "status": "approved"},
                        {"id": "B", "selected": False, "status": "queued"},
                        {"id": "C", "selected": False, "status": "approved"},
                    ],
                },
                "after": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "items": [
                        {"id": "B", "selected": False, "status": "queued"},
                    ],
                },
            },
        ],
    )
    assert report.passed


def test_updated_all_where_requires_v131() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.3.0"
    contract["state"]["initial"]["items"] = [{"selected": True}]
    contract["state"]["schema"]["items"] = {"type": "array"}
    contract["components"]["bulk_button"] = {
        "kind": "button",
        "selector": '[data-testid="bulk"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_all_where",
                        "path": "items",
                        "where": [{"op": "equals", "field": "selected", "value": True}],
                        "updates": {"status": "done"},
                    }
                ]
            }
        },
    }
    scenarios = {"dsl_version": "1.3.0", "scenarios": [{"id": "bulk", "steps": [{"do": "bulk_button.click"}]}]}

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_removed_all_where_requires_v140() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.3.1"
    contract["state"]["initial"]["items"] = [{"selected": True}]
    contract["state"]["schema"]["items"] = {"type": "array"}
    contract["components"]["bulk_button"] = {
        "kind": "button",
        "selector": '[data-testid="bulk"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "removed_all_where",
                        "path": "items",
                        "where": [{"op": "equals", "field": "selected", "value": True}],
                    }
                ]
            }
        },
    }
    scenarios = {"dsl_version": "1.3.1", "scenarios": [{"id": "bulk", "steps": [{"do": "bulk_button.click"}]}]}

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_v150_field_error_object_operations_compile_lower_and_evaluate() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.5.0"
    contract["state"]["initial"]["field_errors"] = {}
    contract["state"]["initial"]["error_count"] = 0
    contract["state"]["schema"]["field_errors"] = {"type": "object"}
    contract["state"]["schema"]["error_count"] = {"type": "number"}
    contract["components"]["mark_name_error_button"] = {
        "kind": "button",
        "selector": '[data-testid="mark-name-error"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_object_fields",
                        "path": "field_errors",
                        "updates": {"name": "Name is required"},
                    },
                    {
                        "op": "equals_object_key_count",
                        "path": "error_count",
                        "source_path": "field_errors",
                    },
                ]
            }
        },
    }
    contract["components"]["clear_name_error_button"] = {
        "kind": "button",
        "selector": '[data-testid="clear-name-error"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "removed_object_fields",
                        "path": "field_errors",
                        "fields": ["name"],
                    },
                    {
                        "op": "equals_object_key_count",
                        "path": "error_count",
                        "source_path": "field_errors",
                    },
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.5.0",
        "scenarios": [
            {
                "id": "mark_and_clear",
                "steps": [
                    {"do": "mark_name_error_button.click"},
                    {"do": "clear_name_error_button.click"},
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert [check.op for step in compiled.steps for check in step.checks] == [
        "updated_object_fields",
        "equals_object_key_count",
        "removed_object_fields",
        "equals_object_key_count",
    ]
    assert web_scenarios.scenarios[0]["steps"][1]["expect"][0]["type"] == "state_updated_object_fields"
    assert web_scenarios.scenarios[0]["steps"][1]["expect"][1]["type"] == "state_object_key_count_equals"
    assert web_scenarios.scenarios[0]["steps"][3]["expect"][0]["type"] == "state_removed_object_fields"

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "field_errors": {},
                    "error_count": 0,
                },
                "after": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "field_errors": {"name": "Name is required"},
                    "error_count": 1,
                },
            },
            {
                "before": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "field_errors": {"name": "Name is required", "tax": "Tax ID is required"},
                    "error_count": 2,
                },
                "after": {
                    "value": 0,
                    "step_size": 2,
                    "locked": False,
                    "last_action": "",
                    "label": "",
                    "field_errors": {"tax": "Tax ID is required"},
                    "error_count": 1,
                },
            },
        ],
    )
    assert report.passed


def test_field_error_object_operations_are_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.4.0"
    contract["state"]["initial"]["field_errors"] = {}
    contract["state"]["schema"]["field_errors"] = {"type": "object"}
    contract["components"]["mark_error_button"] = {
        "kind": "button",
        "selector": '[data-testid="mark-error"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_object_fields",
                        "path": "field_errors",
                        "updates": {"name": "Name is required"},
                    }
                ]
            }
        },
    }
    scenarios = {"dsl_version": "1.4.0", "scenarios": [{"id": "error", "steps": [{"do": "mark_error_button.click"}]}]}

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_object_key_count_requires_v150() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.4.1"
    contract["state"]["initial"]["field_errors"] = {}
    contract["state"]["initial"]["error_count"] = 0
    contract["state"]["schema"]["field_errors"] = {"type": "object"}
    contract["state"]["schema"]["error_count"] = {"type": "number"}
    contract["components"]["count_error_button"] = {
        "kind": "button",
        "selector": '[data-testid="count-error"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "equals_object_key_count",
                        "path": "error_count",
                        "source_path": "field_errors",
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.4.1",
        "scenarios": [{"id": "count", "steps": [{"do": "count_error_button.click"}]}],
    }

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_v160_nested_child_operations_compile_lower_and_evaluate() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.6.0"
    contract["state"]["initial"].update(
        {
            "shipments": [
                {
                    "id": "north",
                    "lane": "north",
                    "stops": [
                        {"id": "n1", "status": "queued", "weight": 5},
                        {"id": "n2", "status": "queued", "weight": 3},
                    ],
                },
                {
                    "id": "south",
                    "lane": "south",
                    "stops": [{"id": "s1", "status": "queued", "weight": 7}],
                },
            ],
            "queued": 3,
            "assigned": 0,
            "queued_weight": 15,
        }
    )
    contract["state"]["schema"].update(
        {
            "shipments": {"type": "array"},
            "queued": {"type": "number"},
            "assigned": {"type": "number"},
            "queued_weight": {"type": "number"},
        }
    )
    contract["components"]["assign_north_button"] = {
        "kind": "button",
        "selector": '[data-testid="assign-north"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_first_child_where",
                        "path": "shipments",
                        "parent_where": [{"op": "equals", "field": "lane", "value": "north"}],
                        "child_path": "stops",
                        "child_where": [{"op": "equals", "field": "status", "value": "queued"}],
                        "updates": {"status": "assigned"},
                    },
                    {
                        "op": "equals_nested_count_where",
                        "path": "queued",
                        "source_path": "shipments",
                        "child_path": "stops",
                        "child_where": [{"op": "equals", "field": "status", "value": "queued"}],
                    },
                    {
                        "op": "equals_nested_count_where",
                        "path": "assigned",
                        "source_path": "shipments",
                        "child_path": "stops",
                        "child_where": [{"op": "equals", "field": "status", "value": "assigned"}],
                    },
                    {
                        "op": "equals_nested_sum",
                        "path": "queued_weight",
                        "source_path": "shipments",
                        "child_path": "stops",
                        "child_where": [{"op": "equals", "field": "status", "value": "queued"}],
                        "field": "weight",
                    },
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.6.0",
        "scenarios": [{"id": "nested", "steps": [{"do": "assign_north_button.click"}]}],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    web_contract, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert web_contract.id == "tiny_counter"
    assert compiled.steps[0].checks[0].op == "updated_first_child_where"
    assert web_scenarios.scenarios[0]["steps"][1]["expect"][0]["type"] == "state_updated_first_child_where"

    report = evaluate_trace(
        compiled,
        [
            {
                "before": contract["state"]["initial"],
                "after": {
                    **contract["state"]["initial"],
                    "shipments": [
                        {
                            "id": "north",
                            "lane": "north",
                            "stops": [
                                {"id": "n1", "status": "assigned", "weight": 5},
                                {"id": "n2", "status": "queued", "weight": 3},
                            ],
                        },
                        {
                            "id": "south",
                            "lane": "south",
                            "stops": [{"id": "s1", "status": "queued", "weight": 7}],
                        },
                    ],
                    "queued": 2,
                    "assigned": 1,
                    "queued_weight": 10,
                },
            }
        ],
    )
    assert report.passed


def test_nested_child_operations_are_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.5.0"
    contract["state"]["initial"]["shipments"] = [{"lane": "north", "stops": []}]
    contract["state"]["schema"]["shipments"] = {"type": "array"}
    contract["components"]["assign_child_button"] = {
        "kind": "button",
        "selector": '[data-testid="assign-child"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_first_child_where",
                        "path": "shipments",
                        "parent_where": [{"op": "equals", "field": "lane", "value": "north"}],
                        "child_path": "stops",
                        "child_where": [{"op": "equals", "field": "status", "value": "queued"}],
                        "updates": {"status": "assigned"},
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.5.0",
        "scenarios": [{"id": "nested_gate", "steps": [{"do": "assign_child_button.click"}]}],
    }

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_v170_time_scheduled_after_state_operations_compile_lower_and_evaluate() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.7.0"
    contract["state"]["initial"].update(
        {
            "clock": 0,
            "tasks": [
                {"id": "a", "stage": "queued", "due_at": 30, "expires_at": 120},
                {"id": "b", "stage": "queued", "due_at": 90, "expires_at": 120},
                {"id": "c", "stage": "done", "due_at": 0, "expires_at": 60},
            ],
            "due_count": 0,
            "active_count": 3,
        }
    )
    contract["state"]["schema"].update(
        {
            "clock": {"type": "number"},
            "tasks": {"type": "array"},
            "due_count": {"type": "number"},
            "active_count": {"type": "number"},
        }
    )
    contract["components"]["advance_button"] = {
        "kind": "button",
        "selector": '[data-testid="advance"]',
        "actions": {
            "click": {
                "effects": [
                    {"op": "advanced_time_by", "path": "clock", "by": 90},
                    {
                        "op": "updated_all_where_after",
                        "path": "tasks",
                        "where": [
                            {"op": "equals", "field": "stage", "value": "queued"},
                            {"op": "relation", "field": "due_at", "operator": "<=", "value_path": "clock"},
                        ],
                        "updates": {"stage": "due"},
                    },
                    {
                        "op": "equals_count_where",
                        "path": "due_count",
                        "source_path": "tasks",
                        "where": [{"op": "equals", "field": "stage", "value": "due"}],
                    },
                    {"op": "equals_length", "path": "active_count", "source_path": "tasks"},
                ]
            }
        },
    }
    contract["components"]["archive_button"] = {
        "kind": "button",
        "selector": '[data-testid="archive"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "removed_all_where_after",
                        "path": "tasks",
                        "where": [
                            {"op": "equals", "field": "stage", "value": "done"},
                            {"op": "relation", "field": "expires_at", "operator": "<=", "value_path": "clock"},
                        ],
                    },
                    {
                        "op": "equals_count_where",
                        "path": "due_count",
                        "source_path": "tasks",
                        "where": [{"op": "equals", "field": "stage", "value": "due"}],
                    },
                    {"op": "equals_length", "path": "active_count", "source_path": "tasks"},
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.7.0",
        "scenarios": [
            {
                "id": "time_due",
                "steps": [{"do": "advance_button.click"}, {"do": "archive_button.click"}],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)

    assert [check.op for check in compiled.steps[0].checks[:3]] == [
        "advanced_time_by",
        "updated_all_where_after",
        "equals_count_where",
    ]
    expect = web_scenarios.scenarios[0]["steps"][1]["expect"]
    assert expect[0]["type"] == "state_time_advanced_by"
    assert expect[1]["type"] == "state_updated_all_where_after"
    second_expect = web_scenarios.scenarios[0]["steps"][3]["expect"]
    assert second_expect[0]["type"] == "state_removed_all_where_after"

    report = evaluate_trace(
        compiled,
        [
            {
                "before": contract["state"]["initial"],
                "after": {
                    **contract["state"]["initial"],
                    "clock": 90,
                    "tasks": [
                        {"id": "a", "stage": "due", "due_at": 30, "expires_at": 120},
                        {"id": "b", "stage": "due", "due_at": 90, "expires_at": 120},
                        {"id": "c", "stage": "done", "due_at": 0, "expires_at": 60},
                    ],
                    "due_count": 2,
                    "active_count": 3,
                },
            },
            {
                "before": {
                    **contract["state"]["initial"],
                    "clock": 90,
                    "tasks": [
                        {"id": "a", "stage": "due", "due_at": 30, "expires_at": 120},
                        {"id": "b", "stage": "due", "due_at": 90, "expires_at": 120},
                        {"id": "c", "stage": "done", "due_at": 0, "expires_at": 60},
                    ],
                    "due_count": 2,
                    "active_count": 3,
                },
                "after": {
                    **contract["state"]["initial"],
                    "clock": 90,
                    "tasks": [
                        {"id": "a", "stage": "due", "due_at": 30, "expires_at": 120},
                        {"id": "b", "stage": "due", "due_at": 90, "expires_at": 120},
                    ],
                    "due_count": 2,
                    "active_count": 2,
                },
            }
        ],
    )
    assert report.passed


def test_after_state_scheduled_operations_are_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "1.6.1"
    contract["state"]["initial"]["tasks"] = [{"stage": "queued", "due_at": 1}]
    contract["state"]["schema"]["tasks"] = {"type": "array"}
    contract["components"]["advance_button"] = {
        "kind": "button",
        "selector": '[data-testid="advance"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "updated_all_where_after",
                        "path": "tasks",
                        "where": [
                            {"op": "relation", "field": "due_at", "operator": "<=", "value_path": "value"}
                        ],
                        "updates": {"stage": "due"},
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "1.6.1",
        "scenarios": [{"id": "time_gate", "steps": [{"do": "advance_button.click"}]}],
    }

    with pytest.raises(DslCompileError, match="unsupported check op"):
        compile_bundle(contract, scenarios)


def test_value_path_requires_v090_or_newer() -> None:
    contract = {
        "dsl_version": "0.8.0",
        "app": {"id": "selected_view", "name": "Selected View", "capability": "filter"},
        "runtime": {
            "target": "web",
            "state_probe": {"kind": "javascript", "expression": "window.__DETOX_STATE__"},
        },
        "state": {
            "initial": {
                "items": [{"id": "a"}],
                "visible_items": [],
                "selected_id": "a",
            },
            "schema": {
                "items": {"type": "array"},
                "visible_items": {"type": "array"},
                "selected_id": {"type": "string"},
            },
        },
        "components": {
            "filter_selected_button": {
                "kind": "button",
                "selector": "[data-testid='filter-selected']",
                "actions": {
                    "click": {
                        "effects": [
                            {
                                "op": "equals_filter",
                                "path": "visible_items",
                                "source_path": "items",
                                "where": [
                                    {
                                        "op": "equals",
                                        "field": "id",
                                        "value_path": "selected_id",
                                    }
                                ],
                            }
                        ]
                    }
                },
            }
        },
    }
    scenarios = {
        "dsl_version": "0.8.0",
        "scenarios": [{"id": "filter_selected", "steps": [{"do": "filter_selected_button.click"}]}],
    }

    with pytest.raises(DslCompileError, match="value_path requires DSL 0.9.0"):
        compile_bundle(contract, scenarios)


def test_v200_roles_session_allowed_and_unauthorized_compile_lower_and_evaluate() -> None:
    contract = _role_contract()
    scenarios = {
        "dsl_version": "2.0.0",
        "scenarios": [
            {
                "id": "analyst_denied_then_supervisor_approves",
                "steps": [
                    {"do": "approve_button.click", "mode": "unauthorized"},
                    {"do": "supervisor_role_button.click"},
                    {"do": "approve_button.click"},
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    assert compiled.steps[0].mode == "unauthorized"
    assert [check.op for check in compiled.steps[0].preconditions] == ["not_one_of"]
    assert [check.op for check in compiled.steps[2].preconditions] == ["one_of"]

    report = evaluate_trace(
        compiled,
        [
            {
                "before": {
                    "active_role": "analyst",
                    "access_notice": "",
                    "approved_count": 0,
                    "last_action": "none",
                },
                "after": {
                    "active_role": "analyst",
                    "access_notice": "supervisor required",
                    "approved_count": 0,
                    "last_action": "unauthorized_approve",
                },
            },
            {
                "before": {
                    "active_role": "analyst",
                    "access_notice": "supervisor required",
                    "approved_count": 0,
                    "last_action": "unauthorized_approve",
                },
                "after": {
                    "active_role": "supervisor",
                    "access_notice": "",
                    "approved_count": 0,
                    "last_action": "switch_supervisor",
                },
            },
            {
                "before": {
                    "active_role": "supervisor",
                    "access_notice": "",
                    "approved_count": 0,
                    "last_action": "switch_supervisor",
                },
                "after": {
                    "active_role": "supervisor",
                    "access_notice": "",
                    "approved_count": 1,
                    "last_action": "approve",
                },
            },
        ],
    )
    assert report.passed

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)
    unauthorized_snapshot = lowered.scenarios[0]["steps"][0]
    normal_snapshot = lowered.scenarios[0]["steps"][4]
    assert unauthorized_snapshot["expect"][0] == {
        "type": "state_not_one_of",
        "path": "active_role",
        "values": ["supervisor"],
    }
    assert normal_snapshot["expect"][0] == {
        "type": "state_one_of",
        "path": "active_role",
        "values": ["supervisor"],
    }
    assert lowered.scenarios[0]["steps"][1]["dsl_mode"] == "unauthorized"


def test_roles_session_and_unauthorized_semantics_are_version_gated() -> None:
    contract = _role_contract()
    contract["dsl_version"] = "1.7.1"
    scenarios = {"dsl_version": "1.7.1", "scenarios": [{"id": "gate", "steps": []}]}
    with pytest.raises(DslCompileError, match="runtime.session requires DSL 1.7.2"):
        compile_bundle(contract, scenarios)

    contract = _role_contract()
    contract["dsl_version"] = "1.7.2"
    contract.pop("runtime")
    scenarios = {"dsl_version": "1.7.2", "scenarios": [{"id": "gate", "steps": [{"do": "approve_button.click"}]}]}
    with pytest.raises(DslCompileError, match="contract.runtime.session is missing"):
        compile_bundle(contract, scenarios)

    contract = _role_contract()
    contract["dsl_version"] = "1.7.2"
    scenarios = {"dsl_version": "1.7.2", "scenarios": [{"id": "gate", "steps": [{"do": "approve_button.click"}]}]}
    with pytest.raises(DslCompileError, match="unauthorized_effects.*require DSL 2.0.0"):
        compile_bundle(contract, scenarios)


def test_scenario_metadata_weight_visibility_and_kind_are_preserved() -> None:
    scenarios = _scenario()
    scenarios["tier_weights"] = {"smoke": 3}
    scenarios["scenarios"][0]["visibility"] = "public"
    scenarios["scenarios"][0]["kind"] = "probe"
    scenarios["scenarios"][0]["weight"] = 0
    scenarios["scenarios"][0]["description"] = "Public diagnostic example"
    scenarios["scenarios"][0]["difficulty"] = "d1_smoke"
    scenarios["scenarios"][0]["_source_path"] = "/tmp/scenarios.public.dsl.yaml"

    compiled = compile_bundle(_contract(), scenarios)[0]
    assert compiled.visibility == "public"
    assert compiled.kind == "probe"
    assert compiled.weight == 0
    assert compiled.description == "Public diagnostic example"
    assert compiled.difficulty == "d1_smoke"
    assert compiled.source == "/tmp/scenarios.public.dsl.yaml"

    _, lowered = compile_dsl_to_web_suite(_contract(), scenarios)
    assert lowered.scenarios[0]["visibility"] == "public"
    assert lowered.scenarios[0]["kind"] == "probe"
    assert lowered.scenarios[0]["weight"] == 0
    assert lowered.scenarios[0]["description"] == "Public diagnostic example"
    assert lowered.scenarios[0]["difficulty"] == "d1_smoke"
    assert lowered.scenarios[0]["_source"] == "/tmp/scenarios.public.dsl.yaml"


def test_scenario_weight_defaults_to_tier_weight() -> None:
    scenarios = _scenario()
    scenarios["tier_weights"] = {"smoke": 4}

    compiled = compile_bundle(_contract(), scenarios)[0]

    assert compiled.weight == 4
    assert compiled.visibility == "private"


def test_invalid_scenario_weight_is_rejected() -> None:
    scenarios = _scenario()
    scenarios["scenarios"][0]["weight"] = 0

    with pytest.raises(DslCompileError, match="greater than 0"):
        compile_bundle(_contract(), scenarios)


def test_dsl_201_browser_reload_requires_declared_persistence() -> None:
    scenarios = _persistence_scenario()

    with pytest.raises(DslCompileError, match="persistence.reload is missing"):
        compile_bundle(_contract_201(), scenarios)


def test_dsl_201_browser_reload_lowers_to_web_action() -> None:
    contract, scenarios = compile_dsl_to_web_suite(
        _persistence_contract(),
        _persistence_scenario(),
    )

    assert contract.version == "dsl-2.0.1"
    lowered_steps = scenarios.scenarios[0]["steps"]
    assert lowered_steps[3]["action"] == "reload"
    assert "component" not in lowered_steps[3]
    assert lowered_steps[3]["expect"] == [
        {
            "type": "state_unchanged",
            "path": "label",
            "from": "dsl_before_2",
        },
        {
            "type": "state_unchanged",
            "path": "last_action",
            "from": "dsl_before_2",
        },
    ]


def test_dsl_201_rejects_reload_persistence_unknown_paths() -> None:
    contract = _persistence_contract()
    contract["runtime"]["persistence"]["reload"]["paths"].append("missing")

    with pytest.raises(DslCompileError, match="undeclared state path 'missing'"):
        compile_bundle(contract, _persistence_scenario())


def test_browser_actions_require_dsl_201() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.0.0"
    scenarios = _persistence_scenario()
    scenarios["dsl_version"] = "2.0.0"

    with pytest.raises(DslCompileError, match="browser actions.*require DSL 2.0.1"):
        compile_bundle(contract, scenarios)


def test_dsl_202_browser_history_lowers_to_componentless_actions() -> None:
    contract = _browser_lifecycle_contract("2.0.2")
    scenarios = {
        "dsl_version": "2.0.2",
        "scenarios": [
            {
                "id": "browser_history_round_trip",
                "steps": [
                    {"do": "to_intake_button.click"},
                    {"do": "to_review_button.click"},
                    {"browser": "back", "expect_page": "intake"},
                    {"browser": "forward", "expect_page": "review"},
                ],
            }
        ],
    }

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)

    lowered_steps = lowered.scenarios[0]["steps"]
    assert lowered_steps[5]["action"] == "back"
    assert "component" not in lowered_steps[5]
    assert lowered_steps[5]["expect"] == [
        {"type": "browser_page_equals", "expected": "intake"}
    ]
    assert lowered_steps[7]["action"] == "forward"
    assert lowered_steps[7]["expect"] == [
        {"type": "browser_page_equals", "expected": "review"}
    ]


def test_dsl_202_browser_history_requires_expected_page() -> None:
    contract = _browser_lifecycle_contract("2.0.2")
    scenarios = {
        "dsl_version": "2.0.2",
        "scenarios": [{"id": "missing_expected_page", "steps": [{"browser": "back"}]}],
    }

    with pytest.raises(DslCompileError, match="browser back requires expect_page"):
        compile_bundle(contract, scenarios)


def test_dsl_202_browser_history_is_version_gated() -> None:
    contract = _browser_lifecycle_contract("2.0.1")
    scenarios = {
        "dsl_version": "2.0.1",
        "scenarios": [
            {
                "id": "history_too_early",
                "steps": [{"browser": "back", "expect_page": "home"}],
            }
        ],
    }

    with pytest.raises(DslCompileError, match="browser back.*requires DSL 2.0.2"):
        compile_bundle(contract, scenarios)


def test_dsl_203_browser_goto_page_lowers_to_path_and_page_assertion() -> None:
    contract = _browser_lifecycle_contract("2.0.3")
    scenarios = {
        "dsl_version": "2.0.3",
        "scenarios": [
            {
                "id": "goto_review_directly",
                "steps": [
                    {
                        "browser": {
                            "action": "goto",
                            "page": "review",
                        },
                    }
                ],
            }
        ],
    }

    _, lowered = compile_dsl_to_web_suite(contract, scenarios)

    action_step = lowered.scenarios[0]["steps"][1]
    assert action_step["action"] == "goto"
    assert action_step["path"] == "/#/review"
    assert action_step["expect"] == [
        {"type": "browser_page_equals", "expected": "review"}
    ]


def test_dsl_203_browser_goto_is_version_gated() -> None:
    contract = _browser_lifecycle_contract("2.0.2")
    scenarios = {
        "dsl_version": "2.0.2",
        "scenarios": [
            {
                "id": "goto_too_early",
                "steps": [{"browser": {"action": "goto", "page": "review"}}],
            }
        ],
    }

    with pytest.raises(DslCompileError, match="browser goto.*requires DSL 2.0.3"):
        compile_bundle(contract, scenarios)


def test_dsl_203_browser_goto_rejects_unknown_page() -> None:
    contract = _browser_lifecycle_contract("2.0.3")
    scenarios = {
        "dsl_version": "2.0.3",
        "scenarios": [
            {
                "id": "goto_unknown",
                "steps": [{"browser": {"action": "goto", "page": "missing"}}],
            }
        ],
    }

    with pytest.raises(DslCompileError, match="unknown page 'missing'"):
        compile_bundle(contract, scenarios)


def test_dsl_220_actor_scoped_steps_lower_to_web_steps() -> None:
    contract = _browser_lifecycle_contract("2.2.0")
    contract["runtime"]["actors"] = {
        "clerk": {"label": "Clerk", "start_page": "home"},
        "reviewer": {"label": "Reviewer", "start_page": "intake"},
    }
    scenarios = {
        "dsl_version": "2.2.0",
        "scenarios": [
            {
                "id": "actor_handoff",
                "steps": [
                    {"actor": "clerk", "do": "to_intake_button.click"},
                    {"actor": "reviewer", "do": "to_review_button.click"},
                    {"actor": "reviewer", "browser": "back", "expect_page": "intake"},
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    web_contract, lowered = compile_dsl_to_web_suite(contract, scenarios)

    assert [step.actor for step in compiled.steps] == ["clerk", "reviewer", "reviewer"]
    assert web_contract.runtime["web"]["actors"]["reviewer"]["start_page"] == "intake"
    assert lowered.scenarios[0]["steps"][0]["actor"] == "clerk"
    assert lowered.scenarios[0]["steps"][1]["actor"] == "clerk"
    assert lowered.scenarios[0]["steps"][2]["actor"] == "reviewer"
    assert lowered.scenarios[0]["steps"][3]["actor"] == "reviewer"
    assert lowered.scenarios[0]["steps"][5]["action"] == "back"
    assert lowered.scenarios[0]["steps"][5]["actor"] == "reviewer"


def test_dsl_220_actor_steps_require_declared_actors() -> None:
    contract = _browser_lifecycle_contract("2.2.0")
    scenarios = {
        "dsl_version": "2.2.0",
        "scenarios": [
            {"id": "missing_actor_runtime", "steps": [{"actor": "clerk", "browser": "reload"}]}
        ],
    }

    with pytest.raises(DslCompileError, match="runtime.actors is missing"):
        compile_bundle(contract, scenarios)


def test_dsl_211_runtime_actors_are_version_gated() -> None:
    contract = _browser_lifecycle_contract("2.1.0")
    contract["runtime"]["actors"] = {"clerk": {"start_page": "home"}}
    scenarios = {"dsl_version": "2.1.0", "scenarios": [{"id": "actor_gate", "steps": [{"browser": "reload"}]}]}

    with pytest.raises(DslCompileError, match="runtime.actors requires DSL 2.1.1"):
        compile_bundle(contract, scenarios)


def test_dsl_230_service_fixtures_lower_to_web_contract() -> None:
    contract = _browser_lifecycle_contract("2.3.0")
    contract["state"]["initial"]["__services.calls"] = []
    contract["state"]["initial"]["service_call_count"] = 0
    contract["state"]["schema"]["__services.calls"] = {"type": "array"}
    contract["state"]["schema"]["service_call_count"] = {"type": "number"}
    contract["runtime"]["services"] = {
        "formulary_lookup": {
            "endpoint": "/api/formulary",
            "method": "GET",
            "responses": [
                {
                    "id": "covered_specialty",
                    "match": {"query": {"drug": "Revaxa"}},
                    "status": 200,
                    "json": {"tier": "specialty", "requires_pa": True},
                }
            ],
        }
    }
    scenarios = {
        "dsl_version": "2.3.0",
        "scenarios": [
            {
                "id": "service_call_is_observable",
                "steps": [
                    {
                        "do": "to_intake_button.click",
                        "expect": [
                            {
                                "op": "equals_count_where",
                                "path": "service_call_count",
                                "source_path": "__services.calls",
                                "where": [
                                    {
                                        "op": "equals",
                                        "field": "service",
                                        "value": "formulary_lookup",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }

    web_contract, lowered = compile_dsl_to_web_suite(contract, scenarios)

    assert web_contract.runtime["web"]["services"]["formulary_lookup"]["endpoint"] == "/api/formulary"
    assert lowered.version == "2.3.0"


def test_dsl_221_runtime_services_are_version_gated() -> None:
    contract = _browser_lifecycle_contract("2.2.0")
    contract["runtime"]["services"] = {
        "lookup": {
            "endpoint": "/api/lookup",
            "responses": [{"json": {"ok": True}}],
        }
    }
    scenarios = {"dsl_version": "2.2.0", "scenarios": [{"id": "service_gate", "steps": [{"browser": "reload"}]}]}

    with pytest.raises(DslCompileError, match="runtime.services requires DSL 2.2.1"):
        compile_bundle(contract, scenarios)


def test_dsl_240_event_steps_lower_to_web_events() -> None:
    contract = _browser_lifecycle_contract("2.4.0")
    contract["state"]["initial"]["alert_count"] = 0
    contract["state"]["schema"]["alert_count"] = {"type": "number"}
    contract["runtime"]["events"] = {
        "sensor_spike": {
            "payload": {"sensor": "cold-room-7"},
            "effects": [
                {"op": "changed_by", "path": "alert_count", "by": 1},
                {"op": "equals", "path": "last_action", "value": "sensor_spike"},
            ],
        }
    }
    scenarios = {
        "dsl_version": "2.4.0",
        "scenarios": [{"id": "event_step", "steps": [{"event": "sensor_spike"}]}],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    web_contract, lowered = compile_dsl_to_web_suite(contract, scenarios)

    assert compiled.steps[0].action == "event"
    assert compiled.steps[0].input["payload"] == {"sensor": "cold-room-7"}
    assert web_contract.runtime["web"]["events"]["sensor_spike"]["payload"]["sensor"] == "cold-room-7"
    assert lowered.scenarios[0]["steps"][1]["action"] == "event"
    assert lowered.scenarios[0]["steps"][1]["event"] == "sensor_spike"


def test_dsl_231_runtime_events_are_version_gated() -> None:
    contract = _browser_lifecycle_contract("2.3.0")
    contract["runtime"]["events"] = {
        "tick": {"effects": [{"op": "equals", "path": "last_action", "value": "tick"}]}
    }
    scenarios = {"dsl_version": "2.3.0", "scenarios": [{"id": "event_gate", "steps": [{"event": "tick"}]}]}

    with pytest.raises(DslCompileError, match="runtime.events requires DSL 2.3.1"):
        compile_bundle(contract, scenarios)


def _role_contract() -> dict:
    return {
        "dsl_version": "2.0.0",
        "app": {
            "id": "role_review",
            "name": "Role Review",
            "capability": "role_gated_workflow",
        },
        "runtime": {
            "target": "web",
            "state_probe": {
                "kind": "javascript",
                "expression": "window.__DETOX_STATE__",
            },
            "session": {
                "role_path": "active_role",
                "roles": ["analyst", "supervisor", "auditor"],
            },
        },
        "state": {
            "initial": {
                "active_role": "analyst",
                "access_notice": "",
                "approved_count": 0,
                "last_action": "none",
            },
            "schema": {
                "active_role": {"type": "string"},
                "access_notice": {"type": "string"},
                "approved_count": {"type": "number"},
                "last_action": {"type": "string"},
            },
        },
        "components": {
            "supervisor_role_button": {
                "kind": "button",
                "selector": '[data-testid="role-supervisor"]',
                "actions": {
                    "click": {
                        "effects": [
                            {"op": "equals", "path": "active_role", "value": "supervisor"},
                            {"op": "equals", "path": "access_notice", "value": ""},
                            {"op": "equals", "path": "last_action", "value": "switch_supervisor"},
                        ]
                    }
                },
            },
            "approve_button": {
                "kind": "button",
                "selector": '[data-testid="approve"]',
                "actions": {
                    "click": {
                        "allowed_roles": ["supervisor"],
                        "effects": [
                            {"op": "changed_by", "path": "approved_count", "by": 1},
                            {"op": "equals", "path": "access_notice", "value": ""},
                            {"op": "equals", "path": "last_action", "value": "approve"},
                        ],
                        "unauthorized_effects": [
                            {"op": "unchanged", "path": "approved_count"},
                            {
                                "op": "equals",
                                "path": "access_notice",
                                "value": "supervisor required",
                            },
                            {
                                "op": "equals",
                                "path": "last_action",
                                "value": "unauthorized_approve",
                            },
                        ],
                    }
                },
            },
        },
    }


def _contract_201() -> dict:
    contract = _contract()
    contract["dsl_version"] = "2.0.1"
    return contract


def _persistence_contract() -> dict:
    contract = _contract_201()
    contract["runtime"]["persistence"] = {
        "reload": {
            "scope": "local_storage",
            "paths": ["label", "last_action"],
        }
    }
    return contract


def _persistence_scenario() -> dict:
    return {
        "dsl_version": "2.0.1",
        "scenarios": [
            {
                "id": "reload_keeps_public_state",
                "steps": [
                    {
                        "do": "label_input.fill",
                        "input": {"value": "Apollo"},
                    },
                    {
                        "browser": "reload",
                        "expect": [
                            {"op": "unchanged", "path": "label"},
                            {"op": "unchanged", "path": "last_action"},
                        ],
                    },
                ],
            }
        ],
    }


def _browser_lifecycle_contract(version: str) -> dict:
    return {
        "dsl_version": version,
        "app": {
            "id": "browser_lifecycle",
            "name": "Browser Lifecycle",
            "capability": "browser_lifecycle",
        },
        "runtime": {
            "target": "web",
            "start_url": "/#/home",
            "state_probe": {
                "kind": "javascript",
                "expression": "window.__DETOX_STATE__",
            },
            "pages": {
                "home": {"path": "/#/home"},
                "intake": {"path": "/#/intake"},
                "review": {"path": "/#/review"},
            },
            "persistence": {
                "reload": {
                    "scope": "local_storage",
                    "paths": ["current_page", "last_action"],
                }
            },
        },
        "state": {
            "initial": {
                "current_page": "home",
                "last_action": "",
            },
            "schema": {
                "current_page": {"type": "string"},
                "last_action": {"type": "string"},
            },
        },
        "components": {
            "to_intake_button": {
                "kind": "button",
                "page": "home",
                "selector": '[data-testid="to-intake"]',
                "actions": {
                    "click": {
                        "navigate_to": "intake",
                        "effects": [
                            {"op": "equals", "path": "current_page", "value": "intake"},
                            {"op": "equals", "path": "last_action", "value": "to_intake"},
                        ],
                    }
                },
            },
            "to_review_button": {
                "kind": "button",
                "page": "intake",
                "selector": '[data-testid="to-review"]',
                "actions": {
                    "click": {
                        "navigate_to": "review",
                        "effects": [
                            {"op": "equals", "path": "current_page", "value": "review"},
                            {"op": "equals", "path": "last_action", "value": "to_review"},
                        ],
                    }
                },
            },
        },
    }


def _contract() -> dict:
    return {
        "dsl_version": "0.1",
        "app": {
            "id": "tiny_counter",
            "name": "Tiny Counter",
            "capability": "basic_stateful_web",
        },
        "runtime": {
            "target": "web",
            "state_probe": {
                "kind": "javascript",
                "expression": "window.__DETOX_STATE__",
            },
        },
        "state": {
            "initial": {
                "value": 0,
                "step_size": 1,
                "locked": False,
                "last_action": "",
                "label": "",
            },
            "schema": {
                "value": {"type": "number"},
                "step_size": {"type": "number"},
                "locked": {"type": "boolean"},
                "last_action": {"type": "string"},
                "label": {"type": "string"},
            }
        },
        "components": {
            "increment_button": {
                "kind": "button",
                "selector": '[data-testid="increment"]',
                "actions": {
                    "click": {
                        "preconditions": [
                            {"op": "equals", "path": "locked", "value": False}
                        ],
                        "effects": [
                            {"op": "changed_by_path", "path": "value", "by_path": "step_size"},
                            {"op": "equals", "path": "last_action", "value": "increment"},
                            {"op": "unchanged", "path": "locked"},
                        ],
                    }
                },
            },
            "label_input": {
                "kind": "input",
                "selector": '[data-testid="label"]',
                "actions": {
                    "fill": {
                        "effects": [
                            {
                                "op": "equals",
                                "path": "label",
                                "value_from": "input.value",
                            },
                            {
                                "op": "equals",
                                "path": "last_action",
                                "value": "edit_label",
                            },
                        ]
                    }
                },
            },
        },
    }


def test_dsl_250_table_inspection_steps_lower_to_web_assertions() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.5.0"
    contract["state"]["initial"]["items"] = [
        {"id": "A-1", "status": "open"},
        {"id": "B-2", "status": "closed"},
    ]
    contract["state"]["schema"]["items"] = {"type": "array"}
    contract["runtime"]["tables"] = {
        "items_grid": {
            "selector": '[data-testid="items-grid"]',
            "row_selector": "[data-row-id]",
            "row_id_attribute": "data-row-id",
            "source_path": "items",
            "row_id_field": "id",
            "columns": {
                "status": {"selector": '[data-col="status"]', "state_field": "status"}
            },
        }
    }
    scenarios = {
        "dsl_version": "2.5.0",
        "scenarios": [
            {
                "id": "inspect_grid",
                "steps": [
                    {
                        "table": "items_grid",
                        "expect_order": ["A-1", "B-2"],
                        "expect_row_count": 2,
                        "expect_rows": [
                            {"id": "A-1", "cells": {"status": "open"}},
                            {"id": "B-2", "cells": {"status": "closed"}},
                        ],
                    }
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)
    assert compiled[0].steps[0].action == "snapshot"
    assert [check.op for check in compiled[0].steps[0].checks] == [
        "table_order_equals",
        "table_row_count_equals",
        "table_cell_equals",
        "table_cell_equals",
    ]

    web_contract, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)
    assert web_contract.runtime["web"]["tables"]["items_grid"]["selector"] == '[data-testid="items-grid"]'
    expect = web_scenarios.scenarios[0]["steps"][1]["expect"]
    assert expect[0]["type"] == "table_order_equals"
    assert expect[1]["type"] == "table_row_count_equals"
    assert expect[2]["type"] == "table_cell_equals"


def test_dsl_241_tables_are_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.4.0"
    contract["runtime"]["tables"] = {
        "items_grid": {
            "selector": '[data-testid="items-grid"]',
            "row_selector": "[data-row-id]",
            "columns": {"status": '[data-col="status"]'},
        }
    }
    scenarios = {"dsl_version": "2.4.0", "scenarios": [{"id": "inspect_grid", "steps": [{"table": "items_grid"}]}]}

    with pytest.raises(DslCompileError, match="runtime.tables requires DSL 2.4.1"):
        compile_bundle(contract, scenarios)


def test_dsl_260_upload_action_lowers_file_payload() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.6.0"
    contract["state"]["schema"]["rows"] = {"type": "array"}
    contract["state"]["initial"]["rows"] = []
    contract["components"]["csv_input"] = {
        "kind": "file_input",
        "selector": '[data-testid="csv"]',
        "actions": {
            "upload": {
                "effects": [
                    {"op": "equals", "path": "rows", "value_from": "input.rows"}
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "2.6.0",
        "scenarios": [
            {
                "id": "upload_csv",
                "steps": [
                    {
                        "do": "csv_input.upload",
                        "input": {
                            "file": {
                                "name": "rows.csv",
                                "mime_type": "text/csv",
                                "content": "id,status\nA,open\n",
                            },
                            "rows": [{"id": "A", "status": "open"}],
                        },
                    }
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)
    assert compiled[0].steps[0].action == "upload"
    assert compiled[0].steps[0].checks[0].spec["value"] == [{"id": "A", "status": "open"}]

    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)
    action_step = web_scenarios.scenarios[0]["steps"][1]
    assert action_step["action"] == "upload"
    assert action_step["file"]["name"] == "rows.csv"
    assert action_step["expect"][0]["expected"] == [{"id": "A", "status": "open"}]


def test_dsl_251_upload_requires_file_payload() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.6.0"
    contract["components"]["csv_input"] = {
        "kind": "file_input",
        "selector": '[data-testid="csv"]',
        "actions": {"upload": {"effects": [{"op": "unchanged", "path": "value"}]}},
    }
    scenarios = {"dsl_version": "2.6.0", "scenarios": [{"id": "bad_upload", "steps": [{"do": "csv_input.upload"}]}]}

    with pytest.raises(DslCompileError, match="upload input requires file mapping"):
        compile_bundle(contract, scenarios)


def test_dsl_251_upload_is_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.5.0"
    contract["components"]["csv_input"] = {
        "kind": "file_input",
        "selector": '[data-testid="csv"]',
        "actions": {"upload": {"effects": [{"op": "unchanged", "path": "value"}]}},
    }
    scenarios = {"dsl_version": "2.5.0", "scenarios": [{"id": "upload", "steps": [{"do": "csv_input.upload"}]}]}

    with pytest.raises(DslCompileError, match="requires DSL 2.5.1"):
        compile_bundle(contract, scenarios)


def test_dsl_270_equals_normalized_lowers_to_assertion() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.7.0"
    contract["state"]["schema"]["match_key"] = {"type": "string"}
    contract["state"]["initial"]["match_key"] = ""
    contract["components"]["name_input"] = {
        "kind": "input",
        "selector": '[data-testid="name"]',
        "actions": {
            "fill": {
                "effects": [
                    {
                        "op": "equals_normalized",
                        "path": "match_key",
                        "value_from": "input.value",
                        "normalizers": ["trim", "collapse_whitespace", "lowercase"],
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "2.7.0",
        "scenarios": [
            {
                "id": "normalized_name",
                "steps": [
                    {"do": "name_input.fill", "input": {"value": "  ACME    Logistics  "}}
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)
    check = compiled[0].steps[0].checks[0]
    assert check.op == "equals_normalized"
    assert check.spec["value"] == "  ACME    Logistics  "

    _, web_scenarios = compile_dsl_to_web_suite(contract, scenarios)
    assertion = web_scenarios.scenarios[0]["steps"][1]["expect"][0]
    assert assertion == {
        "type": "state_normalized_equals",
        "path": "match_key",
        "expected": "  ACME    Logistics  ",
        "normalizers": ["trim", "collapse_whitespace", "lowercase"],
    }


def test_dsl_261_equals_normalized_is_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.6.0"
    contract["components"]["label_input"]["actions"]["fill"]["effects"] = [
        {
            "op": "equals_normalized",
            "path": "label",
            "value_from": "input.value",
            "normalizers": ["trim"],
        }
    ]
    scenarios = {
        "dsl_version": "2.6.0",
        "scenarios": [{"id": "normalized", "steps": [{"do": "label_input.fill", "input": {"value": "x"}}]}],
    }

    with pytest.raises(DslCompileError, match="unsupported check op 'equals_normalized'"):
        compile_bundle(contract, scenarios)


def test_dsl_280_conflict_mode_uses_conflict_branch() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.8.0"
    contract["state"]["schema"]["draft_version"] = {"type": "number"}
    contract["state"]["schema"]["server_version"] = {"type": "number"}
    contract["state"]["initial"]["draft_version"] = 1
    contract["state"]["initial"]["server_version"] = 2
    contract["components"]["commit_button"] = {
        "kind": "button",
        "selector": '[data-testid="commit"]',
        "actions": {
            "click": {
                "preconditions": [
                    {"op": "relation", "path": "draft_version", "operator": "==", "other_path": "server_version"}
                ],
                "effects": [{"op": "changed_by", "path": "server_version", "by": 1}],
                "conflict_when": [
                    {"op": "relation", "path": "draft_version", "operator": "!=", "other_path": "server_version"}
                ],
                "conflict_effects": [{"op": "unchanged", "path": "server_version"}],
            }
        },
    }
    scenarios = {
        "dsl_version": "2.8.0",
        "scenarios": [{"id": "conflict", "steps": [{"do": "commit_button.click", "mode": "conflict"}]}],
    }

    compiled = compile_bundle(contract, scenarios)
    step = compiled[0].steps[0]
    assert step.mode == "conflict"
    assert step.preconditions[0].op == "relation"
    assert step.checks[0].op == "unchanged"


def test_dsl_271_conflict_mode_is_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.7.0"
    contract["components"]["commit_button"] = {
        "kind": "button",
        "selector": '[data-testid="commit"]',
        "actions": {
            "click": {
                "conflict_when": [{"op": "truthy", "path": "is_locked"}],
                "conflict_effects": [{"op": "unchanged", "path": "value"}],
            }
        },
    }
    scenarios = {"dsl_version": "2.7.0", "scenarios": [{"id": "conflict", "steps": [{"do": "commit_button.click", "mode": "conflict"}]}]}

    with pytest.raises(DslCompileError, match="conflict semantics"):
        compile_bundle(contract, scenarios)


def test_dsl_290_join_projection_evaluates_and_lowers_to_web_assertion() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.9.0"
    contract["state"]["initial"].update(
        {
            "cases": [
                {"id": "C-1", "patient_id": "P-1", "status": "open", "priority": 2},
                {"id": "C-2", "patient_id": "P-2", "status": "closed", "priority": 1},
            ],
            "patients": [
                {"id": "P-1", "name": "Ada", "ward": "Blue"},
                {"id": "P-2", "name": "Byron", "ward": "Green"},
            ],
            "visible_rows": [],
        }
    )
    contract["state"]["schema"].update(
        {
            "cases": {"type": "array"},
            "patients": {"type": "array"},
            "visible_rows": {"type": "array"},
        }
    )
    contract["components"]["project_button"] = {
        "kind": "button",
        "selector": '[data-testid="project"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "equals_join_projection",
                        "path": "visible_rows",
                        "source_path": "cases",
                        "lookup_path": "patients",
                        "source_key": "patient_id",
                        "lookup_key": "id",
                        "where": [{"op": "equals", "field": "status", "value": "open"}],
                        "fields": [
                            {"name": "case_id", "source_field": "id"},
                            {"name": "patient_name", "lookup_field": "name"},
                            {"name": "ward", "lookup_field": "ward"},
                            {"name": "priority", "source_field": "priority"},
                            {"name": "source", "value": "joined"},
                        ],
                    }
                ]
            }
        },
    }
    scenarios = {
        "dsl_version": "2.9.0",
        "scenarios": [{"id": "project", "steps": [{"do": "project_button.click"}]}],
    }

    compiled = compile_bundle(contract, scenarios)[0]
    report = evaluate_trace(
        compiled,
        [
            {
                "before": contract["state"]["initial"],
                "after": {
                    **contract["state"]["initial"],
                    "visible_rows": [
                        {
                            "case_id": "C-1",
                            "patient_name": "Ada",
                            "ward": "Blue",
                            "priority": 2,
                            "source": "joined",
                        }
                    ],
                },
            }
        ],
    )
    _, lowered = compile_dsl_to_web_suite(contract, scenarios)

    assert report.passed
    assert compiled.steps[0].checks[0].op == "equals_join_projection"
    assert lowered.scenarios[0]["steps"][1]["expect"][0]["type"] == "state_join_projection_equals"


def test_dsl_280_join_projection_is_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.8.0"
    contract["state"]["schema"]["rows"] = {"type": "array"}
    contract["state"]["schema"]["source"] = {"type": "array"}
    contract["state"]["schema"]["lookup"] = {"type": "array"}
    contract["state"]["initial"]["rows"] = []
    contract["state"]["initial"]["source"] = []
    contract["state"]["initial"]["lookup"] = []
    contract["components"]["project_button"] = {
        "kind": "button",
        "selector": '[data-testid="project"]',
        "actions": {
            "click": {
                "effects": [
                    {
                        "op": "equals_join_projection",
                        "path": "rows",
                        "source_path": "source",
                        "lookup_path": "lookup",
                        "source_key": "lookup_id",
                        "lookup_key": "id",
                        "fields": [{"name": "id", "source_field": "id"}],
                    }
                ]
            }
        },
    }
    scenarios = {"dsl_version": "2.8.0", "scenarios": [{"id": "project", "steps": [{"do": "project_button.click"}]}]}

    with pytest.raises(DslCompileError, match="unsupported check op 'equals_join_projection'"):
        compile_bundle(contract, scenarios)


def test_dsl_300_upload_file_schema_is_validated() -> None:
    contract = _contract()
    contract["dsl_version"] = "3.0.0"
    contract["state"]["schema"]["rows"] = {"type": "array"}
    contract["state"]["initial"]["rows"] = []
    contract["components"]["csv_input"] = {
        "kind": "input",
        "selector": '[data-testid="csv"]',
        "actions": {
            "upload": {
                "file_schema": {
                    "format": "csv",
                    "columns": [
                        {"name": "id", "type": "string"},
                        {"name": "amount", "type": "number"},
                    ],
                },
                "effects": [{"op": "equals", "path": "rows", "value_from": "input.rows"}],
            }
        },
    }
    scenarios = {
        "dsl_version": "3.0.0",
        "scenarios": [
            {
                "id": "upload",
                "steps": [
                    {
                        "do": "csv_input.upload",
                        "input": {
                            "file": {
                                "name": "rows.csv",
                                "mime_type": "text/csv",
                                "content": "id,amount\nA,1\n",
                            },
                            "rows": [{"id": "A", "amount": 1}],
                        },
                    }
                ],
            }
        ],
    }

    compiled = compile_bundle(contract, scenarios)
    assert compiled[0].steps[0].input["file"]["name"] == "rows.csv"


def test_dsl_290_upload_file_schema_is_version_gated() -> None:
    contract = _contract()
    contract["dsl_version"] = "2.9.0"
    contract["state"]["schema"]["rows"] = {"type": "array"}
    contract["state"]["initial"]["rows"] = []
    contract["components"]["csv_input"] = {
        "kind": "input",
        "selector": '[data-testid="csv"]',
        "actions": {
            "upload": {
                "file_schema": {
                    "format": "csv",
                    "columns": [{"name": "amount", "type": "number"}],
                },
                "effects": [{"op": "equals", "path": "rows", "value_from": "input.rows"}],
            }
        },
    }
    scenarios = {
        "dsl_version": "2.9.0",
        "scenarios": [
            {
                "id": "upload",
                "steps": [
                    {
                        "do": "csv_input.upload",
                        "input": {
                            "file": {
                                "name": "rows.csv",
                                "mime_type": "text/csv",
                                "content": "amount\n1\n",
                            },
                            "rows": [{"amount": 1}],
                        },
                    }
                ],
            }
        ],
    }

    with pytest.raises(DslCompileError, match="file_schema requires DSL 2.9.1"):
        compile_bundle(contract, scenarios)


def _scenario() -> dict:
    return {
        "dsl_version": "0.1",
        "scenarios": [
            {
                "id": "increment_and_label",
                "tier": "smoke",
                "steps": [
                    {
                        "do": "increment_button.click",
                        "expect": [
                            {"op": "relation", "path": "value", "operator": ">", "value": 0}
                        ],
                    },
                    {
                        "do": "label_input.fill",
                        "input": {"value": "Apollo"},
                    },
                ],
            }
        ],
    }
