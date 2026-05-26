from detoxbench.core.assertions import evaluate_assertions


def test_state_delta_uses_snapshot_baseline() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "state_delta",
                "path": "counter.value",
                "from": "initial",
                "by": 1,
            }
        ],
        after_state={"counter": {"value": 42}},
        snapshots={"initial": {"counter": {"value": 41}}},
    )

    assert results[0].passed


def test_browser_page_assertion_uses_public_browser_probe() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "browser_page_equals",
                "expected": "review",
            }
        ],
        after_state={"__browser": {"page_id": "review", "path": "/#/review"}},
        snapshots={},
    )

    assert results[0].passed
    assert results[0].actual == "review"


def test_state_delta_from_path_uses_snapshot_delta_path() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "state_delta_from_path",
                "path": "counter.value",
                "from": "initial",
                "by_path": "counter.stepSize",
                "multiplier": -1,
            }
        ],
        after_state={"counter": {"value": 38, "stepSize": 99}},
        snapshots={"initial": {"counter": {"value": 41, "stepSize": 3}}},
    )

    assert results[0].passed
    assert results[0].actual == 38
    assert results[0].expected == 38


def test_state_length_delta_uses_snapshot_baseline() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "state_length_delta",
                "path": "todos.items",
                "from": "initial",
                "by": 1,
            }
        ],
        after_state={"todos": {"items": ["a", "b", "c"]}},
        snapshots={"initial": {"todos": {"items": ["a", "b"]}}},
    )

    assert results[0].passed


def test_state_appended_uses_snapshot_baseline() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "state_appended",
                "path": "todos.events",
                "from": "initial",
                "expected": "archive",
            }
        ],
        after_state={"todos": {"events": ["create", "archive"]}},
        snapshots={"initial": {"todos": {"events": ["create"]}}},
    )

    assert results[0].passed
    assert results[0].expected == ["create", "archive"]


def test_state_unchanged_compares_deep_values() -> None:
    items = [{"text": "Draft", "done": False}]
    results = evaluate_assertions(
        [
            {
                "type": "state_unchanged",
                "path": "todos.items",
                "from": "initial",
            }
        ],
        after_state={"todos": {"items": [{"text": "Draft", "done": False}]}},
        snapshots={"initial": {"todos": {"items": items}}},
    )

    assert results[0].passed


def test_state_relation_compares_against_snapshot_path() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "state_relation",
                "path": "cart.itemCount",
                "operator": ">",
                "from": "initial",
            }
        ],
        after_state={"cart": {"itemCount": 3}},
        snapshots={"initial": {"cart": {"itemCount": 1}}},
    )

    assert results[0].passed


def test_state_relation_compares_two_after_state_paths() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "state_relation",
                "path": "analytics.checkoutTotal",
                "operator": "==",
                "other_path": "checkout.total",
            }
        ],
        after_state={"analytics": {"checkoutTotal": 128}, "checkout": {"total": 128}},
        snapshots={},
    )

    assert results[0].passed


def test_state_template_equals_renders_after_state_paths() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "state_template_equals",
                "path": "status",
                "template": "value:{value} | last:{last_action|default:none} | history:{history.length}",
            }
        ],
        after_state={
            "value": 4,
            "last_action": "increment",
            "history": ["set_step_3", "increment"],
            "status": "value:4 | last:increment | history:2",
        },
        snapshots={},
    )

    assert results[0].passed


def test_state_linear_equals_uses_after_state_terms() -> None:
    results = evaluate_assertions(
        [
            {
                "type": "state_linear_equals",
                "path": "grand_total",
                "terms": [
                    {"path": "subtotal", "multiplier": 1.08},
                    {"path": "shipping_fee"},
                    {"path": "coupon_credit", "multiplier": -1},
                ],
                "constant": 4,
                "round": 2,
            }
        ],
        after_state={
            "subtotal": 45,
            "shipping_fee": 6,
            "coupon_credit": 5,
            "grand_total": 53.6,
        },
        snapshots={},
    )

    assert results[0].passed
    assert results[0].expected == 53.6


def test_state_piecewise_linear_equals_uses_first_matching_case() -> None:
    results = evaluate_assertions(
        [
            {
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
        ],
        after_state={
            "subtotal": 72,
            "item_count": 4,
            "shipping_fee": 2,
        },
        snapshots={},
    )

    assert results[0].passed
    assert results[0].expected == 2


def test_collection_assertions_use_after_state_arrays_and_snapshots() -> None:
    before_cases = [
        {"type": "walkin", "acuity": 1, "urgent": False, "coverage": 80},
        {"type": "urgent", "acuity": 5, "urgent": True, "coverage": 200},
        {"type": "followup", "acuity": 2, "urgent": False, "coverage": 120},
    ]
    after_state = {
        "cases": [
            {"type": "urgent", "acuity": 5, "urgent": True, "coverage": 200},
            {"type": "followup", "acuity": 2, "urgent": False, "coverage": 120},
        ],
        "queue_count": 2,
        "urgent_count": 1,
        "acuity_total": 7,
        "urgent_coverage_total": 200,
        "has_urgent": True,
        "next_case_type": "urgent",
        "last_case_type": "followup",
    }

    results = evaluate_assertions(
        [
            {
                "type": "state_removed_first",
                "path": "cases",
                "from": "before_process",
            },
            {
                "type": "state_length_equals",
                "path": "queue_count",
                "source_path": "cases",
            },
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
            },
            {
                "type": "state_sum_equals",
                "path": "urgent_coverage_total",
                "source_path": "cases",
                "field": "coverage",
                "where": [{"op": "truthy", "field": "urgent"}],
            },
            {
                "type": "state_any_where_equals",
                "path": "has_urgent",
                "source_path": "cases",
                "where": [{"op": "relation", "field": "acuity", "operator": ">=", "value": 5}],
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
        ],
        after_state=after_state,
        snapshots={
            "before_process": {
                "cases": before_cases,
            }
        },
    )

    assert all(result.passed for result in results)
    assert results[0].expected == before_cases[1:]
    assert results[2].expected == 1
    assert results[3].expected == 7
    assert results[4].expected == 200
    assert results[6].expected == "urgent"
    assert results[7].expected == "followup"


def test_collection_identity_assertions_use_before_state_items() -> None:
    before_state = {
        "backlog": [
            {"id": "alpha", "lane": "backlog", "priority": "normal", "points": 2},
            {"id": "beta", "lane": "backlog", "priority": "normal", "points": 5},
            {"id": "gamma", "lane": "backlog", "priority": "low", "points": 1},
        ],
        "active": [
            {"id": "delta", "lane": "active", "priority": "normal", "points": 3},
        ],
        "done": [],
    }
    move_results = evaluate_assertions(
        [
            {
                "type": "state_moved_first_where",
                "path": "backlog",
                "from": "before",
                "where": [{"op": "equals", "field": "id", "value": "gamma"}],
                "to_index": 0,
            }
        ],
        after_state={
            "backlog": [
                {"id": "gamma", "lane": "backlog", "priority": "low", "points": 1},
                {"id": "alpha", "lane": "backlog", "priority": "normal", "points": 2},
                {"id": "beta", "lane": "backlog", "priority": "normal", "points": 5},
            ]
        },
        snapshots={"before": before_state},
    )
    update_results = evaluate_assertions(
        [
            {
                "type": "state_updated_first_where",
                "path": "backlog",
                "from": "after_move",
                "where": [{"op": "equals", "field": "id", "value": "beta"}],
                "updates": {"priority": "urgent", "points": 8},
            }
        ],
        after_state={
            "backlog": [
                {"id": "gamma", "lane": "backlog", "priority": "low", "points": 1},
                {"id": "alpha", "lane": "backlog", "priority": "normal", "points": 2},
                {"id": "beta", "lane": "backlog", "priority": "urgent", "points": 8},
            ]
        },
        snapshots={
            "after_move": {
                "backlog": [
                    {"id": "gamma", "lane": "backlog", "priority": "low", "points": 1},
                    {"id": "alpha", "lane": "backlog", "priority": "normal", "points": 2},
                    {"id": "beta", "lane": "backlog", "priority": "normal", "points": 5},
                ]
            },
        },
    )
    remove_results = evaluate_assertions(
        [
            {
                "type": "state_removed_first_where",
                "path": "backlog",
                "from": "before",
                "where": [{"op": "equals", "field": "id", "value": "alpha"}],
            }
        ],
        after_state={
            "backlog": [
                {"id": "beta", "lane": "backlog", "priority": "normal", "points": 5},
                {"id": "gamma", "lane": "backlog", "priority": "low", "points": 1},
            ]
        },
        snapshots={"before": before_state},
    )
    append_results = evaluate_assertions(
        [
            {
                "type": "state_appended_from_first_where",
                "path": "active",
                "from": "before",
                "source_path": "backlog",
                "where": [{"op": "equals", "field": "id", "value": "beta"}],
                "updates": {"lane": "active"},
            },
            {
                "type": "state_appended_from_first_where",
                "path": "done",
                "from": "before",
                "source_path": "backlog",
                "where": [{"op": "equals", "field": "id", "value": "alpha"}],
                "updates": {"lane": "done"},
            },
        ],
        after_state={
            "active": [
                {"id": "delta", "lane": "active", "priority": "normal", "points": 3},
                {"id": "beta", "lane": "active", "priority": "normal", "points": 5},
            ],
            "done": [
                {"id": "alpha", "lane": "done", "priority": "normal", "points": 2},
            ],
        },
        snapshots={"before": before_state},
    )

    assert move_results[0].passed
    assert update_results[0].passed
    assert remove_results[0].passed
    assert append_results[0].passed
    assert append_results[1].passed
    assert remove_results[0].expected == before_state["backlog"][1:]


def test_collection_identity_assertions_can_match_state_value_path() -> None:
    before_state = {
        "selected_id": "beta",
        "backlog": [
            {"id": "alpha", "points": 2},
            {"id": "beta", "points": 5},
        ],
    }
    results = evaluate_assertions(
        [
            {
                "type": "state_updated_first_where",
                "path": "backlog",
                "from": "before",
                "where": [{"op": "equals", "field": "id", "value_path": "selected_id"}],
                "updates": {"points": 8},
            }
        ],
        after_state={
            "backlog": [
                {"id": "alpha", "points": 2},
                {"id": "beta", "points": 8},
            ],
        },
        snapshots={"before": before_state},
    )

    assert results[0].passed


def test_dynamic_object_and_filtered_view_assertions() -> None:
    before_state = {
        "draft_title": "Replace router",
        "draft_priority": "high",
        "next_id": "wo-42",
        "orders": [
            {"id": "wo-1", "title": "Low battery", "priority": "low", "score": 1},
        ],
    }
    after_state = {
        **before_state,
        "orders": [
            {"id": "wo-1", "title": "Low battery", "priority": "low", "score": 1},
            {"id": "wo-42", "title": "Replace router", "priority": "high", "score": 5},
        ],
        "visible_orders": [
            {"id": "wo-42", "title": "Replace router", "priority": "high", "score": 5},
        ],
    }

    results = evaluate_assertions(
        [
            {
                "type": "state_appended_object",
                "path": "orders",
                "from": "before_submit",
                "value": {
                    "id": {"from_path": "next_id"},
                    "title": {"from_path": "draft_title"},
                    "priority": {"from_path": "draft_priority"},
                    "score": 5,
                },
            },
            {
                "type": "state_filter_equals",
                "path": "visible_orders",
                "source_path": "orders",
                "where": [{"op": "equals", "field": "priority", "value": "high"}],
                "order_by": [{"field": "score", "direction": "desc"}],
            },
        ],
        after_state=after_state,
        snapshots={"before_submit": before_state},
    )

    assert results[0].passed
    assert results[1].passed
