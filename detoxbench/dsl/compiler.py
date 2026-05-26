from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

from detoxbench.core.models import AssertionResult
from detoxbench.core.state import get_path
from detoxbench.core.templates import iter_state_template_paths
from detoxbench.core.templates import render_state_template


DSL_VERSION = "3.0.0"
SUPPORTED_DSL_VERSIONS = {
    "0.1",
    "0.2",
    "0.3",
    "0.4",
    "0.4.1",
    "0.4.2",
    "0.4.3",
    "0.4.4",
    "0.4.5",
    "0.4.6",
    "0.4.7",
    "0.4.8",
    "0.4.9",
    "0.5.0",
    "0.5.1",
    "0.5.2",
    "0.5.3",
    "0.5.4",
    "0.6.0",
    "0.6.1",
    "0.7.0",
    "0.7.1",
    "0.8.0",
    "0.8.1",
    "0.9.0",
    "1.0.0",
    "1.0.1",
    "1.0.2",
    "1.1.0",
    "1.1.1",
    "1.2.0",
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
    "1.6.1",
    "1.6.2",
    "1.7.0",
    "1.7.1",
    "1.7.2",
    "2.0.0",
    "2.0.1",
    "2.0.2",
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.1.0",
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
    "2.4.1",
    "2.4.2",
    "2.4.3",
    "2.4.4",
    "2.5.0",
    "2.5.1",
    "2.5.2",
    "2.5.3",
    "2.5.4",
    "2.6.0",
    "2.6.1",
    "2.6.2",
    "2.6.3",
    "2.6.4",
    "2.7.0",
    "2.7.1",
    "2.7.2",
    "2.7.3",
    "2.7.4",
    "2.8.0",
    "2.8.1",
    "2.8.2",
    "2.8.3",
    "2.8.4",
    "2.9.0",
    "2.9.1",
    "2.9.2",
    "2.9.3",
    "2.9.4",
    "3.0.0",
}
SUPPORTED_FIELD_TYPES = {"number", "string", "boolean", "array", "object", "any"}
SUPPORTED_ACTIONS = {"click", "fill", "select", "check", "uncheck", "toggle", "upload"}
SUPPORTED_SCENARIO_KINDS = {"scoring", "probe"}
SUPPORTED_SCENARIO_VISIBILITIES = {"public", "private"}
SUPPORTED_CHECKS_V01 = {
    "equals",
    "changed_by",
    "changed_by_path",
    "changed",
    "unchanged",
    "toggled",
    "truthy",
    "falsey",
    "relation",
}
SUPPORTED_CHECKS_BY_VERSION = {
    "0.1": SUPPORTED_CHECKS_V01,
    "0.2": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "length_changed_by",
        "matches",
        "not_contains",
    },
    "0.3": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "length_changed_by",
        "matches",
        "not_contains",
    },
    "0.4": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
    },
    "0.4.1": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_linear",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
    },
    "0.4.2": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
    },
    "0.4.3": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
        "removed_first",
    },
    "0.4.4": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_length",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
        "removed_first",
    },
    "0.4.5": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_count_where",
        "equals_length",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
        "removed_first",
    },
    "0.4.6": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_count_where",
        "equals_length",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_sum",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
        "removed_first",
    },
    "0.4.7": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_any_where",
        "equals_count_where",
        "equals_length",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_sum",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
        "removed_first",
    },
    "0.4.8": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_any_where",
        "equals_count_where",
        "equals_first_item_field",
        "equals_length",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_sum",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
        "removed_first",
    },
    "0.4.9": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_any_where",
        "equals_count_where",
        "equals_first_item_field",
        "equals_last_item_field",
        "equals_length",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_sum",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
        "removed_first",
    },
    "0.5.0": SUPPORTED_CHECKS_V01 | {
        "appended",
        "contains",
        "equals_any_where",
        "equals_count_where",
        "equals_first_item_field",
        "equals_last_item_field",
        "equals_length",
        "equals_linear",
        "equals_piecewise_linear",
        "equals_sum",
        "equals_template",
        "length_changed_by",
        "matches",
        "not_contains",
        "removed_first",
    },
}
SUPPORTED_CHECKS_BY_VERSION["0.5.1"] = SUPPORTED_CHECKS_BY_VERSION["0.5.0"] | {
    "removed_first_where",
}
SUPPORTED_CHECKS_BY_VERSION["0.5.2"] = SUPPORTED_CHECKS_BY_VERSION["0.5.1"] | {
    "updated_first_where",
}
SUPPORTED_CHECKS_BY_VERSION["0.5.3"] = SUPPORTED_CHECKS_BY_VERSION["0.5.2"] | {
    "moved_first_where",
}
SUPPORTED_CHECKS_BY_VERSION["0.5.4"] = SUPPORTED_CHECKS_BY_VERSION["0.5.3"] | {
    "appended_from_first_where",
}
SUPPORTED_CHECKS_BY_VERSION["0.6.0"] = SUPPORTED_CHECKS_BY_VERSION["0.5.4"]
SUPPORTED_CHECKS_BY_VERSION["0.6.1"] = SUPPORTED_CHECKS_BY_VERSION["0.6.0"] | {
    "appended_object",
}
SUPPORTED_CHECKS_BY_VERSION["0.7.0"] = SUPPORTED_CHECKS_BY_VERSION["0.6.1"]
SUPPORTED_CHECKS_BY_VERSION["0.7.1"] = SUPPORTED_CHECKS_BY_VERSION["0.7.0"] | {
    "equals_filter",
}
SUPPORTED_CHECKS_BY_VERSION["0.8.0"] = SUPPORTED_CHECKS_BY_VERSION["0.7.1"]
SUPPORTED_CHECKS_BY_VERSION["0.8.1"] = SUPPORTED_CHECKS_BY_VERSION["0.8.0"]
SUPPORTED_CHECKS_BY_VERSION["0.9.0"] = SUPPORTED_CHECKS_BY_VERSION["0.8.1"]
SUPPORTED_CHECKS_BY_VERSION["1.0.0"] = SUPPORTED_CHECKS_BY_VERSION["0.9.0"]
SUPPORTED_CHECKS_BY_VERSION["1.0.1"] = SUPPORTED_CHECKS_BY_VERSION["1.0.0"]
SUPPORTED_CHECKS_BY_VERSION["1.0.2"] = SUPPORTED_CHECKS_BY_VERSION["1.0.1"]
SUPPORTED_CHECKS_BY_VERSION["1.1.0"] = SUPPORTED_CHECKS_BY_VERSION["1.0.2"]
SUPPORTED_CHECKS_BY_VERSION["1.1.1"] = SUPPORTED_CHECKS_BY_VERSION["1.1.0"]
SUPPORTED_CHECKS_BY_VERSION["1.2.0"] = SUPPORTED_CHECKS_BY_VERSION["1.1.1"]
SUPPORTED_CHECKS_BY_VERSION["1.2.1"] = SUPPORTED_CHECKS_BY_VERSION["1.2.0"]
SUPPORTED_CHECKS_BY_VERSION["1.3.0"] = SUPPORTED_CHECKS_BY_VERSION["1.2.1"]
SUPPORTED_CHECKS_BY_VERSION["1.3.1"] = SUPPORTED_CHECKS_BY_VERSION["1.3.0"] | {
    "updated_all_where",
}
SUPPORTED_CHECKS_BY_VERSION["1.4.0"] = SUPPORTED_CHECKS_BY_VERSION["1.3.1"] | {
    "removed_all_where",
}
SUPPORTED_CHECKS_BY_VERSION["1.4.1"] = SUPPORTED_CHECKS_BY_VERSION["1.4.0"] | {
    "removed_object_fields",
    "updated_object_fields",
}
SUPPORTED_CHECKS_BY_VERSION["1.5.0"] = SUPPORTED_CHECKS_BY_VERSION["1.4.1"] | {
    "equals_object_key_count",
}
SUPPORTED_CHECKS_BY_VERSION["1.5.1"] = SUPPORTED_CHECKS_BY_VERSION["1.5.0"] | {
    "updated_first_child_where",
}
SUPPORTED_CHECKS_BY_VERSION["1.5.2"] = SUPPORTED_CHECKS_BY_VERSION["1.5.1"] | {
    "removed_first_child_where",
}
SUPPORTED_CHECKS_BY_VERSION["1.6.0"] = SUPPORTED_CHECKS_BY_VERSION["1.5.2"] | {
    "equals_nested_count_where",
    "equals_nested_sum",
}
SUPPORTED_CHECKS_BY_VERSION["1.6.1"] = SUPPORTED_CHECKS_BY_VERSION["1.6.0"] | {
    "advanced_time_by",
}
SUPPORTED_CHECKS_BY_VERSION["1.6.2"] = SUPPORTED_CHECKS_BY_VERSION["1.6.1"] | {
    "updated_all_where_after",
}
SUPPORTED_CHECKS_BY_VERSION["1.7.0"] = SUPPORTED_CHECKS_BY_VERSION["1.6.2"] | {
    "removed_all_where_after",
}
SUPPORTED_CHECKS_BY_VERSION["1.7.1"] = SUPPORTED_CHECKS_BY_VERSION["1.7.0"] | {
    "not_one_of",
    "one_of",
}
SUPPORTED_CHECKS_BY_VERSION["1.7.2"] = SUPPORTED_CHECKS_BY_VERSION["1.7.1"]
SUPPORTED_CHECKS_BY_VERSION["2.0.0"] = SUPPORTED_CHECKS_BY_VERSION["1.7.2"]
SUPPORTED_CHECKS_BY_VERSION["2.0.1"] = SUPPORTED_CHECKS_BY_VERSION["2.0.0"]
SUPPORTED_CHECKS_BY_VERSION["2.0.2"] = SUPPORTED_CHECKS_BY_VERSION["2.0.1"]
SUPPORTED_CHECKS_BY_VERSION["2.0.3"] = SUPPORTED_CHECKS_BY_VERSION["2.0.2"]
SUPPORTED_CHECKS_BY_VERSION["2.0.4"] = SUPPORTED_CHECKS_BY_VERSION["2.0.3"]
SUPPORTED_CHECKS_BY_VERSION["2.0.5"] = SUPPORTED_CHECKS_BY_VERSION["2.0.4"]
SUPPORTED_CHECKS_BY_VERSION["2.1.0"] = SUPPORTED_CHECKS_BY_VERSION["2.0.5"]
SUPPORTED_CHECKS_BY_VERSION["2.1.1"] = SUPPORTED_CHECKS_BY_VERSION["2.1.0"]
SUPPORTED_CHECKS_BY_VERSION["2.1.2"] = SUPPORTED_CHECKS_BY_VERSION["2.1.1"]
SUPPORTED_CHECKS_BY_VERSION["2.1.3"] = SUPPORTED_CHECKS_BY_VERSION["2.1.2"]
SUPPORTED_CHECKS_BY_VERSION["2.1.4"] = SUPPORTED_CHECKS_BY_VERSION["2.1.3"]
SUPPORTED_CHECKS_BY_VERSION["2.2.0"] = SUPPORTED_CHECKS_BY_VERSION["2.1.4"]
SUPPORTED_CHECKS_BY_VERSION["2.2.1"] = SUPPORTED_CHECKS_BY_VERSION["2.2.0"]
SUPPORTED_CHECKS_BY_VERSION["2.2.2"] = SUPPORTED_CHECKS_BY_VERSION["2.2.1"]
SUPPORTED_CHECKS_BY_VERSION["2.2.3"] = SUPPORTED_CHECKS_BY_VERSION["2.2.2"]
SUPPORTED_CHECKS_BY_VERSION["2.2.4"] = SUPPORTED_CHECKS_BY_VERSION["2.2.3"]
SUPPORTED_CHECKS_BY_VERSION["2.3.0"] = SUPPORTED_CHECKS_BY_VERSION["2.2.4"]
SUPPORTED_CHECKS_BY_VERSION["2.3.1"] = SUPPORTED_CHECKS_BY_VERSION["2.3.0"]
SUPPORTED_CHECKS_BY_VERSION["2.3.2"] = SUPPORTED_CHECKS_BY_VERSION["2.3.1"]
SUPPORTED_CHECKS_BY_VERSION["2.3.3"] = SUPPORTED_CHECKS_BY_VERSION["2.3.2"]
SUPPORTED_CHECKS_BY_VERSION["2.3.4"] = SUPPORTED_CHECKS_BY_VERSION["2.3.3"]
SUPPORTED_CHECKS_BY_VERSION["2.4.0"] = SUPPORTED_CHECKS_BY_VERSION["2.3.4"]
SUPPORTED_CHECKS_BY_VERSION["2.4.1"] = SUPPORTED_CHECKS_BY_VERSION["2.4.0"]
SUPPORTED_CHECKS_BY_VERSION["2.4.2"] = SUPPORTED_CHECKS_BY_VERSION["2.4.1"]
SUPPORTED_CHECKS_BY_VERSION["2.4.3"] = SUPPORTED_CHECKS_BY_VERSION["2.4.2"]
SUPPORTED_CHECKS_BY_VERSION["2.4.4"] = SUPPORTED_CHECKS_BY_VERSION["2.4.3"]
SUPPORTED_CHECKS_BY_VERSION["2.5.0"] = SUPPORTED_CHECKS_BY_VERSION["2.4.4"]
SUPPORTED_CHECKS_BY_VERSION["2.5.1"] = SUPPORTED_CHECKS_BY_VERSION["2.5.0"]
SUPPORTED_CHECKS_BY_VERSION["2.5.2"] = SUPPORTED_CHECKS_BY_VERSION["2.5.1"]
SUPPORTED_CHECKS_BY_VERSION["2.5.3"] = SUPPORTED_CHECKS_BY_VERSION["2.5.2"]
SUPPORTED_CHECKS_BY_VERSION["2.5.4"] = SUPPORTED_CHECKS_BY_VERSION["2.5.3"]
SUPPORTED_CHECKS_BY_VERSION["2.6.0"] = SUPPORTED_CHECKS_BY_VERSION["2.5.4"]
SUPPORTED_CHECKS_BY_VERSION["2.6.1"] = SUPPORTED_CHECKS_BY_VERSION["2.6.0"] | {
    "equals_normalized",
}
SUPPORTED_CHECKS_BY_VERSION["2.6.2"] = SUPPORTED_CHECKS_BY_VERSION["2.6.1"]
SUPPORTED_CHECKS_BY_VERSION["2.6.3"] = SUPPORTED_CHECKS_BY_VERSION["2.6.2"]
SUPPORTED_CHECKS_BY_VERSION["2.6.4"] = SUPPORTED_CHECKS_BY_VERSION["2.6.3"]
SUPPORTED_CHECKS_BY_VERSION["2.7.0"] = SUPPORTED_CHECKS_BY_VERSION["2.6.4"]
SUPPORTED_CHECKS_BY_VERSION["2.7.1"] = SUPPORTED_CHECKS_BY_VERSION["2.7.0"]
SUPPORTED_CHECKS_BY_VERSION["2.7.2"] = SUPPORTED_CHECKS_BY_VERSION["2.7.1"]
SUPPORTED_CHECKS_BY_VERSION["2.7.3"] = SUPPORTED_CHECKS_BY_VERSION["2.7.2"]
SUPPORTED_CHECKS_BY_VERSION["2.7.4"] = SUPPORTED_CHECKS_BY_VERSION["2.7.3"]
SUPPORTED_CHECKS_BY_VERSION["2.8.0"] = SUPPORTED_CHECKS_BY_VERSION["2.7.4"]
SUPPORTED_CHECKS_BY_VERSION["2.8.1"] = SUPPORTED_CHECKS_BY_VERSION["2.8.0"] | {
    "equals_join_projection",
}
SUPPORTED_CHECKS_BY_VERSION["2.8.2"] = SUPPORTED_CHECKS_BY_VERSION["2.8.1"]
SUPPORTED_CHECKS_BY_VERSION["2.8.3"] = SUPPORTED_CHECKS_BY_VERSION["2.8.2"]
SUPPORTED_CHECKS_BY_VERSION["2.8.4"] = SUPPORTED_CHECKS_BY_VERSION["2.8.3"]
SUPPORTED_CHECKS_BY_VERSION["2.9.0"] = SUPPORTED_CHECKS_BY_VERSION["2.8.4"]
SUPPORTED_CHECKS_BY_VERSION["2.9.1"] = SUPPORTED_CHECKS_BY_VERSION["2.9.0"]
SUPPORTED_CHECKS_BY_VERSION["2.9.2"] = SUPPORTED_CHECKS_BY_VERSION["2.9.1"]
SUPPORTED_CHECKS_BY_VERSION["2.9.3"] = SUPPORTED_CHECKS_BY_VERSION["2.9.2"]
SUPPORTED_CHECKS_BY_VERSION["2.9.4"] = SUPPORTED_CHECKS_BY_VERSION["2.9.3"]
SUPPORTED_CHECKS_BY_VERSION["3.0.0"] = SUPPORTED_CHECKS_BY_VERSION["2.9.4"]
SUPPORTED_STEP_MODES_BY_VERSION = {
    "0.1": {"normal"},
    "0.2": {"normal"},
    "0.3": {"normal", "blocked"},
    "0.4": {"normal", "blocked"},
    "0.4.1": {"normal", "blocked"},
    "0.4.2": {"normal", "blocked"},
    "0.4.3": {"normal", "blocked"},
    "0.4.4": {"normal", "blocked"},
    "0.4.5": {"normal", "blocked"},
    "0.4.6": {"normal", "blocked"},
    "0.4.7": {"normal", "blocked"},
    "0.4.8": {"normal", "blocked"},
    "0.4.9": {"normal", "blocked"},
    "0.5.0": {"normal", "blocked"},
}
for _dsl_version in (
    "0.5.1",
    "0.5.2",
    "0.5.3",
    "0.5.4",
    "0.6.0",
    "0.6.1",
    "0.7.0",
    "0.7.1",
    "0.8.0",
):
    SUPPORTED_STEP_MODES_BY_VERSION[_dsl_version] = {"normal", "blocked"}
for _dsl_version in (
    "0.8.1",
    "0.9.0",
    "1.0.0",
    "1.0.1",
    "1.0.2",
    "1.1.0",
    "1.1.1",
    "1.2.0",
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
    "1.6.1",
    "1.6.2",
    "1.7.0",
    "1.7.1",
    "1.7.2",
):
    SUPPORTED_STEP_MODES_BY_VERSION[_dsl_version] = {"normal", "blocked", "rejected"}
SUPPORTED_STEP_MODES_BY_VERSION["2.0.0"] = {"blocked", "normal", "rejected", "unauthorized"}
SUPPORTED_STEP_MODES_BY_VERSION["2.0.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.0.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.0.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.0.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.0.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.0.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.0.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.0.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.0.5"] = SUPPORTED_STEP_MODES_BY_VERSION["2.0.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.1.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.0.5"]
SUPPORTED_STEP_MODES_BY_VERSION["2.1.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.1.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.1.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.1.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.1.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.1.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.1.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.1.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.2.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.1.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.2.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.2.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.2.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.2.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.2.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.2.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.2.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.2.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.3.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.2.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.3.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.3.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.3.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.3.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.3.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.3.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.3.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.3.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.4.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.3.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.4.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.4.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.4.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.4.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.4.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.4.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.4.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.4.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.5.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.4.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.5.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.5.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.5.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.5.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.5.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.5.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.5.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.5.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.6.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.5.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.6.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.6.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.6.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.6.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.6.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.6.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.6.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.6.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.7.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.6.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.7.1"] = {*SUPPORTED_STEP_MODES_BY_VERSION["2.7.0"], "conflict"}
SUPPORTED_STEP_MODES_BY_VERSION["2.7.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.7.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.7.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.7.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.7.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.7.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.8.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.7.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.8.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.8.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.8.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.8.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.8.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.8.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.8.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.8.3"]
SUPPORTED_STEP_MODES_BY_VERSION["2.9.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.8.4"]
SUPPORTED_STEP_MODES_BY_VERSION["2.9.1"] = SUPPORTED_STEP_MODES_BY_VERSION["2.9.0"]
SUPPORTED_STEP_MODES_BY_VERSION["2.9.2"] = SUPPORTED_STEP_MODES_BY_VERSION["2.9.1"]
SUPPORTED_STEP_MODES_BY_VERSION["2.9.3"] = SUPPORTED_STEP_MODES_BY_VERSION["2.9.2"]
SUPPORTED_STEP_MODES_BY_VERSION["2.9.4"] = SUPPORTED_STEP_MODES_BY_VERSION["2.9.3"]
SUPPORTED_STEP_MODES_BY_VERSION["3.0.0"] = SUPPORTED_STEP_MODES_BY_VERSION["2.9.4"]
POST_160_DSL_VERSIONS = {
    "1.6.1",
    "1.6.2",
    "1.7.0",
    "1.7.1",
    "1.7.2",
    "2.0.0",
    "2.0.1",
    "2.0.2",
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.1.0",
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
SESSION_DSL_VERSIONS = {
    "1.7.2",
    "2.0.0",
    "2.0.1",
    "2.0.2",
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.1.0",
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
UNAUTHORIZED_ACTION_DSL_VERSIONS = {
    "2.0.0",
    "2.0.1",
    "2.0.2",
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.1.0",
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
BROWSER_ACTION_DSL_VERSIONS = {
    "2.0.1",
    "2.0.2",
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.1.0",
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
BROWSER_HISTORY_DSL_VERSIONS = {
    "2.0.2",
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.1.0",
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
BROWSER_GOTO_DSL_VERSIONS = {
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.1.0",
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
PERSISTENCE_DSL_VERSIONS = {
    "2.0.1",
    "2.0.2",
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.1.0",
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
ACTOR_DSL_VERSIONS = {
    "2.1.1",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.2.0",
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
SERVICE_DSL_VERSIONS = {
    "2.2.1",
    "2.2.2",
    "2.2.3",
    "2.2.4",
    "2.3.0",
    "2.3.1",
    "2.3.2",
    "2.3.3",
    "2.3.4",
    "2.4.0",
}
EVENT_DSL_VERSIONS = {"2.3.1", "2.3.2", "2.3.3", "2.3.4", "2.4.0"}
PAGE_AWARE_DSL_VERSIONS = {
    "1.0.1",
    "1.0.2",
    "1.1.0",
    "1.1.1",
    "1.2.0",
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
}
PAGE_AWARE_DSL_VERSIONS.update(POST_160_DSL_VERSIONS)
COMPONENT_PAGE_DSL_VERSIONS = {
    "1.0.2",
    "1.1.0",
    "1.1.1",
    "1.2.0",
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
}
COMPONENT_PAGE_DSL_VERSIONS.update(POST_160_DSL_VERSIONS)
ACTION_NAVIGATION_DSL_VERSIONS = {
    "1.1.0",
    "1.1.1",
    "1.2.0",
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
}
ACTION_NAVIGATION_DSL_VERSIONS.update(POST_160_DSL_VERSIONS)
WAIT_STEP_DSL_VERSIONS = {
    "1.1.1",
    "1.2.0",
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
}
WAIT_STEP_DSL_VERSIONS.update(POST_160_DSL_VERSIONS)
ASYNC_ACTION_DSL_VERSIONS = {
    "1.2.0",
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
}
ASYNC_ACTION_DSL_VERSIONS.update(POST_160_DSL_VERSIONS)
SELECTOR_TEMPLATE_DSL_VERSIONS = {
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
}
SELECTOR_TEMPLATE_DSL_VERSIONS.update(POST_160_DSL_VERSIONS)
ITEM_VALUE_FROM_DSL_VERSIONS = {
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
}
ITEM_VALUE_FROM_DSL_VERSIONS.update(POST_160_DSL_VERSIONS)
ITEM_VALUE_PATH_DSL_VERSIONS = {
    "0.9.0",
    "1.0.0",
    "1.0.1",
    "1.0.2",
    "1.1.0",
    "1.1.1",
    "1.2.0",
    "1.2.1",
    "1.3.0",
    "1.3.1",
    "1.4.0",
    "1.4.1",
    "1.5.0",
    "1.5.1",
    "1.5.2",
    "1.6.0",
}
ITEM_VALUE_PATH_DSL_VERSIONS.update(POST_160_DSL_VERSIONS)
DSL_25_PATCH_VERSIONS = {
    "2.4.1",
    "2.4.2",
    "2.4.3",
    "2.4.4",
    "2.5.0",
    "2.5.1",
    "2.5.2",
    "2.5.3",
    "2.5.4",
    "2.6.0",
    "2.6.1",
    "2.6.2",
    "2.6.3",
    "2.6.4",
    "2.7.0",
    "2.7.1",
    "2.7.2",
    "2.7.3",
    "2.7.4",
    "2.8.0",
    "2.8.1",
    "2.8.2",
    "2.8.3",
    "2.8.4",
    "2.9.0",
    "2.9.1",
    "2.9.2",
    "2.9.3",
    "2.9.4",
    "3.0.0",
}
TABLE_DSL_VERSIONS = DSL_25_PATCH_VERSIONS
FILE_INPUT_DSL_VERSIONS = {
    "2.5.1",
    "2.5.2",
    "2.5.3",
    "2.5.4",
} | {version for version in DSL_25_PATCH_VERSIONS if version >= "2.6.0"}
NORMALIZATION_DSL_VERSIONS = {
    version for version in DSL_25_PATCH_VERSIONS if version >= "2.6.1"
}
CONFLICT_DSL_VERSIONS = {
    version for version in DSL_25_PATCH_VERSIONS if version >= "2.7.1"
}
JOIN_PROJECTION_DSL_VERSIONS = {
    version for version in DSL_25_PATCH_VERSIONS if version >= "2.8.1"
}
FILE_SCHEMA_DSL_VERSIONS = {
    version for version in DSL_25_PATCH_VERSIONS if version >= "2.9.1"
}
SUPPORTED_FILE_COLUMN_TYPES = {"string", "number", "boolean"}
SUPPORTED_NORMALIZERS = {
    "trim",
    "collapse_whitespace",
    "lowercase",
    "uppercase",
    "digits_only",
    "currency_number",
}
for _versioned_set in (
    POST_160_DSL_VERSIONS,
    SESSION_DSL_VERSIONS,
    UNAUTHORIZED_ACTION_DSL_VERSIONS,
    BROWSER_ACTION_DSL_VERSIONS,
    BROWSER_HISTORY_DSL_VERSIONS,
    BROWSER_GOTO_DSL_VERSIONS,
    PERSISTENCE_DSL_VERSIONS,
    ACTOR_DSL_VERSIONS,
    SERVICE_DSL_VERSIONS,
    EVENT_DSL_VERSIONS,
    PAGE_AWARE_DSL_VERSIONS,
    COMPONENT_PAGE_DSL_VERSIONS,
    ACTION_NAVIGATION_DSL_VERSIONS,
    WAIT_STEP_DSL_VERSIONS,
    ASYNC_ACTION_DSL_VERSIONS,
    SELECTOR_TEMPLATE_DSL_VERSIONS,
    ITEM_VALUE_FROM_DSL_VERSIONS,
    ITEM_VALUE_PATH_DSL_VERSIONS,
):
    _versioned_set.update(DSL_25_PATCH_VERSIONS)
SELECTOR_INPUT_TOKEN_PATTERN = re.compile(r"\{(input\.[A-Za-z0-9_.-]+)\}")
SUPPORTED_PRECONDITIONS = {"equals", "truthy", "falsey", "not_one_of", "one_of", "relation"}
RELATION_OPERATORS = {
    "==": lambda left, right: left == right,
    "eq": lambda left, right: left == right,
    "!=": lambda left, right: left != right,
    "ne": lambda left, right: left != right,
    ">": lambda left, right: left > right,
    "gt": lambda left, right: left > right,
    ">=": lambda left, right: left >= right,
    "gte": lambda left, right: left >= right,
    "<": lambda left, right: left < right,
    "lt": lambda left, right: left < right,
    "<=": lambda left, right: left <= right,
    "lte": lambda left, right: left <= right,
}


class DslCompileError(ValueError):
    """Raised when a DSL bundle cannot be compiled."""


@dataclass(frozen=True)
class CompiledCheck:
    op: str
    path: str
    spec: dict[str, Any]
    source: str
    phase: str


@dataclass(frozen=True)
class CompiledStep:
    scenario_id: str
    index: int
    component: str
    action: str
    mode: str
    selector: str
    input: dict[str, Any]
    preconditions: list[CompiledCheck]
    checks: list[CompiledCheck]
    actor: str | None = None
    page: str | None = None
    navigates_to: str | None = None


@dataclass(frozen=True)
class CompiledScenario:
    id: str
    tier: str | None
    steps: list[CompiledStep]
    kind: str = "scoring"
    weight: float = 1.0
    visibility: str = "private"
    difficulty: str | None = None
    description: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class TraceStepReport:
    step: CompiledStep
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    assertions: list[AssertionResult]

    @property
    def passed(self) -> bool:
        return all(assertion.passed for assertion in self.assertions)


@dataclass(frozen=True)
class TraceScenarioReport:
    scenario: CompiledScenario
    steps: list[TraceStepReport]
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and all(step.passed for step in self.steps)

    @property
    def first_failure(self) -> AssertionResult | None:
        for step in self.steps:
            for assertion in step.assertions:
                if not assertion.passed:
                    return assertion
        return None


def load_dsl_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise DslCompileError(f"{path} must contain a YAML mapping")
    return data


def compile_bundle(contract: dict[str, Any], scenarios: dict[str, Any]) -> list[CompiledScenario]:
    dsl_version = _require_version(contract, "contract")
    scenario_version = _require_version(scenarios, "scenarios")
    if scenario_version != dsl_version:
        raise DslCompileError(
            f"contract.dsl_version {dsl_version!r} does not match scenarios.dsl_version {scenario_version!r}"
        )
    state_schema = _parse_state_schema(contract)
    initial_state = _parse_initial_state(contract, state_schema)
    pages = _parse_pages(contract, dsl_version)
    actors = _parse_actors(contract, dsl_version, pages)
    _parse_services(contract, dsl_version)
    events = _parse_events(contract, dsl_version, state_schema)
    tables = _parse_tables(contract, dsl_version, state_schema)
    session = _parse_session(contract, dsl_version, state_schema, initial_state)
    persistence = _parse_persistence(contract, dsl_version, state_schema)
    components = _parse_components(contract, state_schema, dsl_version, pages, session)
    tier_weights = _parse_tier_weights(scenarios)

    raw_scenarios = scenarios.get("scenarios")
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        raise DslCompileError("scenarios.scenarios must be a non-empty list")

    compiled: list[CompiledScenario] = []
    seen: set[str] = set()
    for raw_scenario in raw_scenarios:
        if not isinstance(raw_scenario, dict):
            raise DslCompileError("Every scenario must be a mapping")
        scenario_id = _required_string(raw_scenario, "id", "scenario")
        if scenario_id in seen:
            raise DslCompileError(f"Duplicate scenario id: {scenario_id}")
        seen.add(scenario_id)
        compiled.append(
            _compile_scenario(
                raw_scenario,
                components,
                state_schema,
                dsl_version,
                tier_weights,
                persistence,
                pages,
                actors,
                events,
                tables,
            )
        )
    return compiled


def evaluate_trace(
    scenario: CompiledScenario,
    trace_steps: list[dict[str, dict[str, Any]]],
) -> TraceScenarioReport:
    reports: list[TraceStepReport] = []
    error = None
    if len(trace_steps) != len(scenario.steps):
        error = (
            f"Trace step count {len(trace_steps)} does not match scenario "
            f"{scenario.id!r} step count {len(scenario.steps)}"
        )

    for step, trace_step in zip(scenario.steps, trace_steps, strict=False):
        before = trace_step.get("before")
        after = trace_step.get("after")
        if not isinstance(before, dict) or not isinstance(after, dict):
            assertions = [
                AssertionResult(
                    type="trace_shape",
                    passed=False,
                    message="Trace step must contain before and after state mappings",
                )
            ]
            reports.append(TraceStepReport(step, {}, {}, assertions))
            continue

        assertions = [
            _evaluate_check(check, before_state=before, after_state=after)
            for check in [*step.preconditions, *step.checks]
        ]
        reports.append(TraceStepReport(step, before, after, assertions))

    return TraceScenarioReport(scenario=scenario, steps=reports, error=error)


def _require_version(data: dict[str, Any], label: str) -> str:
    version = data.get("dsl_version")
    if version not in SUPPORTED_DSL_VERSIONS:
        supported = ", ".join(sorted(SUPPORTED_DSL_VERSIONS))
        raise DslCompileError(f"{label}.dsl_version must be one of {supported}; got {version!r}")
    return str(version)


def _parse_state_schema(contract: dict[str, Any]) -> dict[str, str]:
    raw_state = contract.get("state")
    if not isinstance(raw_state, dict):
        raise DslCompileError("contract.state must be a mapping")
    raw_schema = raw_state.get("schema")
    if not isinstance(raw_schema, dict) or not raw_schema:
        raise DslCompileError("contract.state.schema must be a non-empty mapping")

    schema: dict[str, str] = {}
    for path, declaration in raw_schema.items():
        if not isinstance(path, str) or not path:
            raise DslCompileError("Every state path must be a non-empty string")
        if isinstance(declaration, str):
            field_type = declaration
        elif isinstance(declaration, dict):
            field_type = declaration.get("type")
        else:
            raise DslCompileError(f"State path {path!r} must declare a type")
        if field_type not in SUPPORTED_FIELD_TYPES:
            raise DslCompileError(f"State path {path!r} has unsupported type {field_type!r}")
        if path in schema:
            raise DslCompileError(f"Duplicate state path: {path}")
        schema[path] = field_type
    return schema


def _parse_initial_state(contract: dict[str, Any], state_schema: dict[str, str]) -> dict[str, Any]:
    raw_state = contract.get("state")
    if not isinstance(raw_state, dict):
        raise DslCompileError("contract.state must be a mapping")
    raw_initial = raw_state.get("initial")
    if raw_initial is None:
        return {}
    if not isinstance(raw_initial, dict):
        raise DslCompileError("contract.state.initial must be a mapping")

    missing = sorted(set(state_schema) - set(raw_initial))
    if missing:
        raise DslCompileError(
            "contract.state.initial is missing declared paths: " + ", ".join(missing)
        )

    for path, value in raw_initial.items():
        if path not in state_schema:
            raise DslCompileError(f"contract.state.initial references undeclared state path {path!r}")
        field_type = state_schema[path]
        if not _value_matches_type(value, field_type):
            raise DslCompileError(
                f"contract.state.initial path {path!r} expected {field_type}, got {type(value).__name__}"
            )
    return dict(raw_initial)


def _value_matches_type(value: Any, field_type: str) -> bool:
    if field_type == "any":
        return True
    if field_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if field_type == "string":
        return isinstance(value, str)
    if field_type == "boolean":
        return isinstance(value, bool)
    if field_type == "array":
        return isinstance(value, list)
    if field_type == "object":
        return isinstance(value, dict)
    return False


def _parse_session(
    contract: dict[str, Any],
    dsl_version: str,
    state_schema: dict[str, str],
    initial_state: dict[str, Any],
) -> dict[str, Any] | None:
    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        raise DslCompileError("contract.runtime must be a mapping")
    raw_session = runtime.get("session")
    if raw_session in (None, {}):
        return None
    if dsl_version not in SESSION_DSL_VERSIONS:
        raise DslCompileError("runtime.session requires DSL 1.7.2 or newer")
    if not isinstance(raw_session, dict):
        raise DslCompileError("runtime.session must be a mapping")
    role_path = raw_session.get("role_path")
    if role_path not in state_schema:
        raise DslCompileError(f"runtime.session.role_path references undeclared state path {role_path!r}")
    if state_schema[role_path] != "string":
        raise DslCompileError("runtime.session.role_path must reference a string state path")
    roles = raw_session.get("roles")
    if not isinstance(roles, list) or not roles:
        raise DslCompileError("runtime.session.roles must be a non-empty list")
    normalized_roles: list[str] = []
    for role in roles:
        if not isinstance(role, str) or not role:
            raise DslCompileError("runtime.session.roles entries must be non-empty strings")
        if role in normalized_roles:
            raise DslCompileError(f"runtime.session.roles contains duplicate role {role!r}")
        normalized_roles.append(role)
    initial_role = get_path(initial_state, role_path)
    if initial_role not in normalized_roles:
        raise DslCompileError(
            f"runtime.session initial role {initial_role!r} is not declared in runtime.session.roles"
        )
    return {"role_path": role_path, "roles": normalized_roles}


def _parse_persistence(
    contract: dict[str, Any],
    dsl_version: str,
    state_schema: dict[str, str],
) -> dict[str, Any]:
    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        raise DslCompileError("contract.runtime must be a mapping")
    raw_persistence = runtime.get("persistence")
    if raw_persistence in (None, {}):
        return {}
    if dsl_version not in PERSISTENCE_DSL_VERSIONS:
        raise DslCompileError("runtime.persistence requires DSL 2.0.1 or newer")
    if not isinstance(raw_persistence, dict):
        raise DslCompileError("runtime.persistence must be a mapping")

    parsed: dict[str, Any] = {}
    raw_reload = raw_persistence.get("reload")
    if raw_reload not in (None, {}):
        if not isinstance(raw_reload, dict):
            raise DslCompileError("runtime.persistence.reload must be a mapping")
        scope = raw_reload.get("scope", "local_storage")
        if scope not in {"local_storage", "session_storage", "url"}:
            raise DslCompileError(
                "runtime.persistence.reload.scope must be one of local_storage, session_storage, url"
            )
        paths = raw_reload.get("paths")
        if not isinstance(paths, list) or not paths:
            raise DslCompileError("runtime.persistence.reload.paths must be a non-empty list")
        normalized_paths: list[str] = []
        for path in paths:
            if not isinstance(path, str) or not path:
                raise DslCompileError("runtime.persistence.reload.paths entries must be non-empty strings")
            if path not in state_schema:
                raise DslCompileError(
                    f"runtime.persistence.reload.paths references undeclared state path {path!r}"
                )
            if path in normalized_paths:
                raise DslCompileError(
                    f"runtime.persistence.reload.paths contains duplicate path {path!r}"
                )
            normalized_paths.append(path)
        parsed["reload"] = {
            "scope": scope,
            "paths": normalized_paths,
        }

    extra_keys = set(raw_persistence) - {"reload"}
    if extra_keys:
        raise DslCompileError(
            "runtime.persistence contains unsupported keys: " + ", ".join(sorted(extra_keys))
        )
    return parsed


def _parse_components(
    contract: dict[str, Any],
    state_schema: dict[str, str],
    dsl_version: str,
    pages: dict[str, str],
    session: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    raw_components = contract.get("components")
    if not isinstance(raw_components, dict) or not raw_components:
        raise DslCompileError("contract.components must be a non-empty mapping")

    components: dict[str, dict[str, Any]] = {}
    for component_id, component in raw_components.items():
        if not isinstance(component_id, str) or not component_id:
            raise DslCompileError("Every component id must be a non-empty string")
        if not isinstance(component, dict):
            raise DslCompileError(f"Component {component_id!r} must be a mapping")
        selector = component.get("selector")
        selector_template = component.get("selector_template")
        if selector is not None and (not isinstance(selector, str) or not selector):
            raise DslCompileError(f"Component {component_id!r} selector must be a non-empty string")
        if selector_template is not None:
            if dsl_version not in SELECTOR_TEMPLATE_DSL_VERSIONS:
                raise DslCompileError(
                    f"Component {component_id!r} uses selector_template, "
                    "which requires DSL 1.2.1 or newer"
                )
            if not isinstance(selector_template, str) or not selector_template:
                raise DslCompileError(
                    f"Component {component_id!r} selector_template must be a non-empty string"
                )
            _validate_selector_template(selector_template, component_id=component_id)
        if selector is None and selector_template is None:
            raise DslCompileError(f"Component {component_id!r} requires selector or selector_template")
        page = component.get("page")
        if page is not None:
            if dsl_version not in COMPONENT_PAGE_DSL_VERSIONS:
                raise DslCompileError(
                    f"Component {component_id!r} uses page, which requires DSL 1.0.2 or newer"
                )
            if not isinstance(page, str) or page not in pages:
                raise DslCompileError(
                    f"Component {component_id!r} references unknown page {page!r}"
                )
        raw_actions = component.get("actions")
        if not isinstance(raw_actions, dict) or not raw_actions:
            raise DslCompileError(f"Component {component_id!r} requires actions mapping")

        parsed_actions: dict[str, dict[str, Any]] = {}
        for action_name, action in raw_actions.items():
            if action_name not in SUPPORTED_ACTIONS:
                raise DslCompileError(
                    f"Component {component_id!r} uses unsupported action {action_name!r}"
                )
            if action_name == "upload" and dsl_version not in FILE_INPUT_DSL_VERSIONS:
                raise DslCompileError(
                    f"Component {component_id!r} action 'upload' requires DSL 2.5.1 or newer"
                )
            if action is None:
                action = {}
            if not isinstance(action, dict):
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} must be a mapping"
                )
            if "file_schema" in action:
                if action_name != "upload":
                    raise DslCompileError(
                        f"Component {component_id!r} action {action_name!r} file_schema is only supported on upload"
                    )
                _validate_file_schema(
                    action["file_schema"],
                    component_id=component_id,
                    action_name=action_name,
                    dsl_version=dsl_version,
                )
            allowed_roles = _parse_allowed_roles(
                action,
                component_id=component_id,
                action_name=action_name,
                dsl_version=dsl_version,
                session=session,
            )
            role_preconditions, unauthorized_when = _compile_role_checks(
                allowed_roles,
                session=session,
                component_id=component_id,
                action_name=action_name,
            )
            preconditions = _compile_raw_checks(
                action.get("preconditions", []),
                source=f"contract:{component_id}.{action_name}:precondition",
                phase="pre",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            if "blocked" not in SUPPORTED_STEP_MODES_BY_VERSION[dsl_version] and (
                "blocked_when" in action or "blocked_effects" in action
            ):
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} uses "
                    f"blocked semantics, which require DSL 0.3 or newer"
                )
            if "rejected" not in SUPPORTED_STEP_MODES_BY_VERSION[dsl_version] and (
                "rejected_when" in action or "rejected_effects" in action
            ):
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} uses "
                    f"rejected semantics, which require DSL 0.8.1 or newer"
                )
            if "conflict" not in SUPPORTED_STEP_MODES_BY_VERSION[dsl_version] and (
                "conflict_when" in action or "conflict_effects" in action
            ):
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} uses "
                    "conflict semantics, which require DSL 2.7.1 or newer"
                )
            blocked_when = _compile_raw_checks(
                action.get("blocked_when", []),
                source=f"contract:{component_id}.{action_name}:blocked_when",
                phase="pre",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            effects = _compile_raw_checks(
                action.get("effects", []),
                source=f"contract:{component_id}.{action_name}:effect",
                phase="post",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            blocked_effects = _compile_raw_checks(
                action.get("blocked_effects", []),
                source=f"contract:{component_id}.{action_name}:blocked_effect",
                phase="post",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            rejected_when = _compile_raw_checks(
                action.get("rejected_when", []),
                source=f"contract:{component_id}.{action_name}:rejected_when",
                phase="pre",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            rejected_effects = _compile_raw_checks(
                action.get("rejected_effects", []),
                source=f"contract:{component_id}.{action_name}:rejected_effect",
                phase="post",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            conflict_when = _compile_raw_checks(
                action.get("conflict_when", []),
                source=f"contract:{component_id}.{action_name}:conflict_when",
                phase="pre",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            conflict_effects = _compile_raw_checks(
                action.get("conflict_effects", []),
                source=f"contract:{component_id}.{action_name}:conflict_effect",
                phase="post",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            if "unauthorized_effects" in action and dsl_version not in UNAUTHORIZED_ACTION_DSL_VERSIONS:
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} uses "
                    "unauthorized_effects, which require DSL 2.0.0 or newer"
                )
            unauthorized_effects = _compile_raw_checks(
                action.get("unauthorized_effects", []),
                source=f"contract:{component_id}.{action_name}:unauthorized_effect",
                phase="post",
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            async_effects = _compile_async_effects(
                action.get("async_effects"),
                component_id=component_id,
                action_name=action_name,
                state_schema=state_schema,
                dsl_version=dsl_version,
            )
            navigates_to = action.get("navigate_to")
            if navigates_to is not None:
                if dsl_version not in ACTION_NAVIGATION_DSL_VERSIONS:
                    raise DslCompileError(
                        f"Component {component_id!r} action {action_name!r} uses "
                        "navigate_to, which requires DSL 1.1.0 or newer"
                    )
                if not isinstance(navigates_to, str) or navigates_to not in pages:
                    raise DslCompileError(
                        f"Component {component_id!r} action {action_name!r} "
                        f"references unknown navigate_to page {navigates_to!r}"
                    )
            if blocked_when and not blocked_effects:
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} declares "
                    "blocked_when without blocked_effects"
                )
            if blocked_effects and not blocked_when:
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} declares "
                    "blocked_effects without blocked_when"
                )
            if rejected_when and not rejected_effects:
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} declares "
                    "rejected_when without rejected_effects"
                )
            if rejected_effects and not rejected_when:
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} declares "
                    "rejected_effects without rejected_when"
                )
            if conflict_when and not conflict_effects:
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} declares "
                    "conflict_when without conflict_effects"
                )
            if conflict_effects and not conflict_when:
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} declares "
                    "conflict_effects without conflict_when"
                )
            if unauthorized_effects and not allowed_roles:
                raise DslCompileError(
                    f"Component {component_id!r} action {action_name!r} declares "
                    "unauthorized_effects without allowed_roles"
                )
            parsed_actions[action_name] = {
                "preconditions": preconditions,
                "effects": effects,
                "blocked_when": blocked_when,
                "blocked_effects": blocked_effects,
                "rejected_when": rejected_when,
                "rejected_effects": rejected_effects,
                "conflict_when": conflict_when,
                "conflict_effects": conflict_effects,
                "allowed_roles": allowed_roles,
                "role_preconditions": role_preconditions,
                "unauthorized_when": unauthorized_when,
                "unauthorized_effects": unauthorized_effects,
                "async_effects": async_effects,
                "navigates_to": navigates_to,
            }
        components[component_id] = {
            "selector": selector or selector_template,
            "selector_template": selector_template,
            "page": page,
            "actions": parsed_actions,
        }
    return components


def _validate_file_schema(
    raw_schema: Any,
    *,
    component_id: str,
    action_name: str,
    dsl_version: str,
) -> None:
    if dsl_version not in FILE_SCHEMA_DSL_VERSIONS:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} file_schema requires DSL 2.9.1 or newer"
        )
    if not isinstance(raw_schema, dict):
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} file_schema must be a mapping"
        )
    file_format = raw_schema.get("format", "csv")
    if file_format != "csv":
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} file_schema.format must be csv"
        )
    columns = raw_schema.get("columns")
    if not isinstance(columns, list) or not columns:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} file_schema.columns must be non-empty"
        )
    seen: set[str] = set()
    for index, column in enumerate(columns, start=1):
        if not isinstance(column, dict):
            raise DslCompileError(
                f"Component {component_id!r} action {action_name!r} file_schema column {index} must be a mapping"
            )
        name = column.get("name")
        if not isinstance(name, str) or not name:
            raise DslCompileError(
                f"Component {component_id!r} action {action_name!r} file_schema column {index} requires name"
            )
        if name in seen:
            raise DslCompileError(
                f"Component {component_id!r} action {action_name!r} file_schema duplicate column {name!r}"
            )
        seen.add(name)
        column_type = column.get("type")
        if column_type not in SUPPORTED_FILE_COLUMN_TYPES:
            supported = ", ".join(sorted(SUPPORTED_FILE_COLUMN_TYPES))
            raise DslCompileError(
                f"Component {component_id!r} action {action_name!r} file_schema column {name!r} "
                f"uses unsupported type {column_type!r}; supported: {supported}"
            )


def _parse_allowed_roles(
    action: dict[str, Any],
    *,
    component_id: str,
    action_name: str,
    dsl_version: str,
    session: dict[str, Any] | None,
) -> list[str]:
    raw_allowed_roles = action.get("allowed_roles")
    if raw_allowed_roles is None:
        return []
    if dsl_version not in SESSION_DSL_VERSIONS:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} uses allowed_roles, "
            "which require DSL 1.7.2 or newer"
        )
    if session is None:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} declares allowed_roles "
            "but contract.runtime.session is missing"
        )
    if not isinstance(raw_allowed_roles, list) or not raw_allowed_roles:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} allowed_roles "
            "must be a non-empty list"
        )
    allowed_roles: list[str] = []
    declared_roles = set(session["roles"])
    for role in raw_allowed_roles:
        if not isinstance(role, str) or not role:
            raise DslCompileError(
                f"Component {component_id!r} action {action_name!r} allowed_roles "
                "entries must be non-empty strings"
            )
        if role in allowed_roles:
            raise DslCompileError(
                f"Component {component_id!r} action {action_name!r} allowed_roles "
                f"contains duplicate role {role!r}"
            )
        if role not in declared_roles:
            raise DslCompileError(
                f"Component {component_id!r} action {action_name!r} allowed_roles "
                f"references undeclared runtime.session role {role!r}"
            )
        allowed_roles.append(role)
    return allowed_roles


def _compile_role_checks(
    allowed_roles: list[str],
    *,
    session: dict[str, Any] | None,
    component_id: str,
    action_name: str,
) -> tuple[list[CompiledCheck], list[CompiledCheck]]:
    if not allowed_roles:
        return [], []
    if session is None:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} role checks require runtime.session"
        )
    role_path = session["role_path"]
    role_spec = {
        "op": "one_of",
        "path": role_path,
        "values": list(allowed_roles),
    }
    unauthorized_spec = {
        "op": "not_one_of",
        "path": role_path,
        "values": list(allowed_roles),
    }
    return (
        [
            CompiledCheck(
                op="one_of",
                path=role_path,
                spec=role_spec,
                source=f"contract:{component_id}.{action_name}:allowed_roles",
                phase="pre",
            )
        ],
        [
            CompiledCheck(
                op="not_one_of",
                path=role_path,
                spec=unauthorized_spec,
                source=f"contract:{component_id}.{action_name}:unauthorized_role",
                phase="pre",
            )
        ],
    )


def _parse_pages(contract: dict[str, Any], dsl_version: str) -> dict[str, str]:
    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        raise DslCompileError("contract.runtime must be a mapping")
    raw_pages = runtime.get("pages", {})
    if raw_pages in (None, {}):
        return {}
    if dsl_version not in PAGE_AWARE_DSL_VERSIONS:
        raise DslCompileError("runtime.pages requires DSL 1.0.1 or newer")
    if not isinstance(raw_pages, dict):
        raise DslCompileError("runtime.pages must be a mapping")

    pages: dict[str, str] = {}
    for page_id, page in raw_pages.items():
        if not isinstance(page_id, str) or not page_id:
            raise DslCompileError("Every runtime.pages id must be a non-empty string")
        if isinstance(page, str):
            path = page
        elif isinstance(page, dict):
            path = page.get("path")
        else:
            raise DslCompileError(f"runtime.pages.{page_id} must be a string or mapping")
        if not isinstance(path, str) or not path.startswith("/"):
            raise DslCompileError(f"runtime.pages.{page_id}.path must start with '/'")
        if path in pages.values():
            raise DslCompileError(f"runtime.pages path {path!r} is duplicated")
        pages[page_id] = path
    return pages


def _parse_actors(
    contract: dict[str, Any],
    dsl_version: str,
    pages: dict[str, str],
) -> dict[str, dict[str, str | None]]:
    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        raise DslCompileError("contract.runtime must be a mapping")
    raw_actors = runtime.get("actors", {})
    if raw_actors in (None, {}):
        return {}
    if dsl_version not in ACTOR_DSL_VERSIONS:
        raise DslCompileError("runtime.actors requires DSL 2.1.1 or newer")
    if not isinstance(raw_actors, dict):
        raise DslCompileError("runtime.actors must be a mapping")

    actors: dict[str, dict[str, str | None]] = {}
    for actor_id, actor in raw_actors.items():
        if not isinstance(actor_id, str) or not actor_id:
            raise DslCompileError("Every runtime.actors id must be a non-empty string")
        if actor is None:
            actor = {}
        if not isinstance(actor, dict):
            raise DslCompileError(f"runtime.actors.{actor_id} must be a mapping")
        start_page = actor.get("start_page")
        start_path = actor.get("start_path")
        if start_page is not None and start_path is not None:
            raise DslCompileError(
                f"runtime.actors.{actor_id} must not declare both start_page and start_path"
            )
        if start_page is not None:
            if not isinstance(start_page, str) or start_page not in pages:
                raise DslCompileError(
                    f"runtime.actors.{actor_id}.start_page references unknown page {start_page!r}"
                )
        if start_path is not None:
            if not isinstance(start_path, str) or not start_path.startswith("/"):
                raise DslCompileError(
                    f"runtime.actors.{actor_id}.start_path must start with '/'"
                )
        label = actor.get("label")
        if label is not None and not isinstance(label, str):
            raise DslCompileError(f"runtime.actors.{actor_id}.label must be a string")
        actors[actor_id] = {
            "label": label,
            "start_page": start_page,
            "start_path": start_path,
        }
    return actors


def _parse_services(contract: dict[str, Any], dsl_version: str) -> dict[str, dict[str, Any]]:
    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        raise DslCompileError("contract.runtime must be a mapping")
    raw_services = runtime.get("services", {})
    if raw_services in (None, {}):
        return {}
    if dsl_version not in SERVICE_DSL_VERSIONS:
        raise DslCompileError("runtime.services requires DSL 2.2.1 or newer")
    if not isinstance(raw_services, dict):
        raise DslCompileError("runtime.services must be a mapping")

    services: dict[str, dict[str, Any]] = {}
    for service_id, service in raw_services.items():
        if not isinstance(service_id, str) or not service_id:
            raise DslCompileError("Every runtime.services id must be a non-empty string")
        if not isinstance(service, dict):
            raise DslCompileError(f"runtime.services.{service_id} must be a mapping")
        endpoint = service.get("endpoint")
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise DslCompileError(f"runtime.services.{service_id}.endpoint must start with '/'")
        method = service.get("method", "GET")
        if not isinstance(method, str) or method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise DslCompileError(
                f"runtime.services.{service_id}.method must be GET, POST, PUT, PATCH, or DELETE"
            )
        responses = service.get("responses")
        if not isinstance(responses, list) or not responses:
            raise DslCompileError(
                f"runtime.services.{service_id}.responses must be a non-empty list"
            )
        parsed_responses: list[dict[str, Any]] = []
        for response_index, response in enumerate(responses, start=1):
            if not isinstance(response, dict):
                raise DslCompileError(
                    f"runtime.services.{service_id}.responses[{response_index}] must be a mapping"
                )
            match = response.get("match", {})
            if match is None:
                match = {}
            if not isinstance(match, dict):
                raise DslCompileError(
                    f"runtime.services.{service_id}.responses[{response_index}].match must be a mapping"
                )
            query = match.get("query", {})
            if query is None:
                query = {}
            if not isinstance(query, dict):
                raise DslCompileError(
                    f"runtime.services.{service_id}.responses[{response_index}].match.query must be a mapping"
                )
            body_json = match.get("body_json", {})
            if body_json is None:
                body_json = {}
            if not isinstance(body_json, dict):
                raise DslCompileError(
                    f"runtime.services.{service_id}.responses[{response_index}].match.body_json must be a mapping"
                )
            status = response.get("status", 200)
            if not isinstance(status, int) or isinstance(status, bool) or status < 100 or status > 599:
                raise DslCompileError(
                    f"runtime.services.{service_id}.responses[{response_index}].status must be an HTTP status code"
                )
            if "json" not in response and "text" not in response:
                raise DslCompileError(
                    f"runtime.services.{service_id}.responses[{response_index}] requires json or text"
                )
            parsed_responses.append(
                {
                    "id": response.get("id", f"response_{response_index}"),
                    "match": {"query": dict(query), "body_json": dict(body_json)},
                    "status": status,
                    "json": response.get("json"),
                    "text": response.get("text"),
                }
            )
        services[service_id] = {
            "endpoint": endpoint,
            "method": method.upper(),
            "responses": parsed_responses,
            "default_status": service.get("default_status", 404),
        }
        default_status = services[service_id]["default_status"]
        if (
            not isinstance(default_status, int)
            or isinstance(default_status, bool)
            or default_status < 100
            or default_status > 599
        ):
            raise DslCompileError(
                f"runtime.services.{service_id}.default_status must be an HTTP status code"
            )
    return services


def _parse_events(
    contract: dict[str, Any],
    dsl_version: str,
    state_schema: dict[str, str],
) -> dict[str, dict[str, Any]]:
    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        raise DslCompileError("contract.runtime must be a mapping")
    raw_events = runtime.get("events", {})
    if raw_events in (None, {}):
        return {}
    if dsl_version not in EVENT_DSL_VERSIONS:
        raise DslCompileError("runtime.events requires DSL 2.3.1 or newer")
    if not isinstance(raw_events, dict):
        raise DslCompileError("runtime.events must be a mapping")

    events: dict[str, dict[str, Any]] = {}
    for event_id, event in raw_events.items():
        if not isinstance(event_id, str) or not event_id:
            raise DslCompileError("Every runtime.events id must be a non-empty string")
        if event is None:
            event = {}
        if not isinstance(event, dict):
            raise DslCompileError(f"runtime.events.{event_id} must be a mapping")
        payload = event.get("payload", {})
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise DslCompileError(f"runtime.events.{event_id}.payload must be a mapping")
        preconditions = _compile_raw_checks(
            event.get("preconditions", []),
            source=f"runtime.events.{event_id}:precondition",
            phase="pre",
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        effects = _compile_raw_checks(
            event.get("effects", []),
            source=f"runtime.events.{event_id}:effect",
            phase="post",
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        if not effects:
            raise DslCompileError(f"runtime.events.{event_id}.effects must be a non-empty list")
        events[event_id] = {
            "payload": dict(payload),
            "preconditions": preconditions,
            "effects": effects,
        }
    return events


def _parse_tables(
    contract: dict[str, Any],
    dsl_version: str,
    state_schema: dict[str, str],
) -> dict[str, dict[str, Any]]:
    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        raise DslCompileError("contract.runtime must be a mapping")
    raw_tables = runtime.get("tables", {})
    if raw_tables in (None, {}):
        return {}
    if dsl_version not in TABLE_DSL_VERSIONS:
        raise DslCompileError("runtime.tables requires DSL 2.4.1 or newer")
    if not isinstance(raw_tables, dict):
        raise DslCompileError("runtime.tables must be a mapping")

    tables: dict[str, dict[str, Any]] = {}
    for table_id, table in raw_tables.items():
        if not isinstance(table_id, str) or not table_id:
            raise DslCompileError("Every runtime.tables id must be a non-empty string")
        if not isinstance(table, dict):
            raise DslCompileError(f"runtime.tables.{table_id} must be a mapping")
        selector = table.get("selector")
        row_selector = table.get("row_selector")
        if not isinstance(selector, str) or not selector:
            raise DslCompileError(f"runtime.tables.{table_id}.selector must be a non-empty string")
        if not isinstance(row_selector, str) or not row_selector:
            raise DslCompileError(f"runtime.tables.{table_id}.row_selector must be a non-empty string")
        row_id_attribute = table.get("row_id_attribute", "data-row-id")
        if not isinstance(row_id_attribute, str) or not row_id_attribute:
            raise DslCompileError(
                f"runtime.tables.{table_id}.row_id_attribute must be a non-empty string"
            )
        source_path = table.get("source_path")
        if source_path is not None:
            if source_path not in state_schema:
                raise DslCompileError(
                    f"runtime.tables.{table_id}.source_path references undeclared state path {source_path!r}"
                )
            if state_schema[source_path] != "array":
                raise DslCompileError(
                    f"runtime.tables.{table_id}.source_path must reference an array state path"
                )
        row_id_field = table.get("row_id_field")
        if row_id_field is not None and (not isinstance(row_id_field, str) or not row_id_field):
            raise DslCompileError(f"runtime.tables.{table_id}.row_id_field must be a non-empty string")

        raw_columns = table.get("columns")
        if not isinstance(raw_columns, dict) or not raw_columns:
            raise DslCompileError(f"runtime.tables.{table_id}.columns must be a non-empty mapping")
        columns: dict[str, dict[str, str | None]] = {}
        for column_id, column in raw_columns.items():
            if not isinstance(column_id, str) or not column_id:
                raise DslCompileError(f"runtime.tables.{table_id}.columns ids must be non-empty strings")
            if isinstance(column, str):
                cell_selector = column
                state_field = None
            elif isinstance(column, dict):
                cell_selector = column.get("selector")
                state_field = column.get("state_field")
            else:
                raise DslCompileError(
                    f"runtime.tables.{table_id}.columns.{column_id} must be a selector string or mapping"
                )
            if not isinstance(cell_selector, str) or not cell_selector:
                raise DslCompileError(
                    f"runtime.tables.{table_id}.columns.{column_id}.selector must be a non-empty string"
                )
            if state_field is not None and (not isinstance(state_field, str) or not state_field):
                raise DslCompileError(
                    f"runtime.tables.{table_id}.columns.{column_id}.state_field must be a non-empty string"
                )
            columns[column_id] = {"selector": cell_selector, "state_field": state_field}
        tables[table_id] = {
            "selector": selector,
            "row_selector": row_selector,
            "row_id_attribute": row_id_attribute,
            "source_path": source_path,
            "row_id_field": row_id_field,
            "columns": columns,
        }
    return tables


def _validate_selector_template(template: str, *, component_id: str) -> None:
    tokens = SELECTOR_INPUT_TOKEN_PATTERN.findall(template)
    if not tokens:
        raise DslCompileError(
            f"Component {component_id!r} selector_template must contain at least one "
            "{{input.*}} token"
        )
    rendered_probe = SELECTOR_INPUT_TOKEN_PATTERN.sub("x", template)
    if "{" in rendered_probe or "}" in rendered_probe:
        raise DslCompileError(
            f"Component {component_id!r} selector_template contains unsupported token syntax"
        )


def _compile_async_effects(
    raw_async_effects: Any,
    *,
    component_id: str,
    action_name: str,
    state_schema: dict[str, str],
    dsl_version: str,
) -> dict[str, Any] | None:
    if raw_async_effects is None:
        return None
    if dsl_version not in ASYNC_ACTION_DSL_VERSIONS:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} uses async_effects, "
            "which requires DSL 1.2.0 or newer"
        )
    if not isinstance(raw_async_effects, dict):
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} async_effects must be a mapping"
        )
    after_ms = raw_async_effects.get("after_ms")
    if not isinstance(after_ms, int) or after_ms <= 0:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} async_effects.after_ms "
            "must be a positive integer"
        )
    effects = _compile_raw_checks(
        raw_async_effects.get("effects", []),
        source=f"contract:{component_id}.{action_name}:async_effect",
        phase="post",
        state_schema=state_schema,
        dsl_version=dsl_version,
    )
    if not effects:
        raise DslCompileError(
            f"Component {component_id!r} action {action_name!r} async_effects.effects "
            "must be a non-empty check list"
        )
    return {"after_ms": after_ms, "effects": effects}


def _compile_scenario(
    scenario: dict[str, Any],
    components: dict[str, dict[str, Any]],
    state_schema: dict[str, str],
    dsl_version: str,
    tier_weights: dict[str, float],
    persistence: dict[str, Any],
    pages: dict[str, str],
    actors: dict[str, dict[str, str | None]],
    events: dict[str, dict[str, Any]],
    tables: dict[str, dict[str, Any]],
) -> CompiledScenario:
    scenario_id = _required_string(scenario, "id", "scenario")
    raw_steps = scenario.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise DslCompileError(f"Scenario {scenario_id!r} requires non-empty steps")

    steps: list[CompiledStep] = []
    for index, raw_step in enumerate(raw_steps, start=1):
        if not isinstance(raw_step, dict):
            raise DslCompileError(f"Scenario {scenario_id!r} step {index} must be a mapping")
        wait_step = _compile_wait_like_step(
            raw_step,
            scenario_id=scenario_id,
            index=index,
            components=components,
            state_schema=state_schema,
            dsl_version=dsl_version,
            persistence=persistence,
            pages=pages,
            actors=actors,
            events=events,
            tables=tables,
        )
        if wait_step is not None:
            steps.append(wait_step)
            continue
        actor_id = _parse_step_actor(
            raw_step,
            scenario_id=scenario_id,
            index=index,
            dsl_version=dsl_version,
            actors=actors,
        )
        component_id, action_name = _parse_step_action(raw_step, scenario_id, index)
        try:
            component = components[component_id]
        except KeyError as exc:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} references unknown component "
                f"{component_id!r}"
            ) from exc
        try:
            action = component["actions"][action_name]
        except KeyError as exc:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} references unsupported action "
                f"{component_id}.{action_name}"
            ) from exc

        step_input = raw_step.get("input", {})
        if step_input is None:
            step_input = {}
        if not isinstance(step_input, dict):
            raise DslCompileError(f"Scenario {scenario_id!r} step {index} input must be a mapping")
        if action_name == "upload":
            _validate_upload_step_input(
                step_input,
                scenario_id=scenario_id,
                index=index,
                dsl_version=dsl_version,
            )
        selector = _resolve_component_selector(component, step_input)

        mode = raw_step.get("mode", "normal")
        if not isinstance(mode, str) or mode not in SUPPORTED_STEP_MODES_BY_VERSION[dsl_version]:
            supported = ", ".join(sorted(SUPPORTED_STEP_MODES_BY_VERSION[dsl_version]))
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses unsupported mode "
                f"{mode!r} for DSL {dsl_version}; supported: {supported}"
            )
        if mode == "blocked" and not action["blocked_when"]:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses blocked mode for "
                f"{component_id}.{action_name}, but the action declares no blocked semantics"
            )
        if mode == "rejected" and not action["rejected_when"]:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses rejected mode for "
                f"{component_id}.{action_name}, but the action declares no rejected semantics"
            )
        if mode == "conflict" and not action["conflict_when"]:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses conflict mode for "
                f"{component_id}.{action_name}, but the action declares no conflict semantics"
            )
        if mode == "unauthorized" and not action["allowed_roles"]:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses unauthorized mode for "
                f"{component_id}.{action_name}, but the action declares no allowed_roles"
            )
        if mode == "unauthorized" and not action["unauthorized_effects"]:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses unauthorized mode for "
                f"{component_id}.{action_name}, but the action declares no unauthorized_effects"
            )

        if mode == "blocked":
            action_preconditions = [*action["role_preconditions"], *action["blocked_when"]]
            action_effects = action["blocked_effects"]
            navigates_to = None
        elif mode == "rejected":
            action_preconditions = [*action["role_preconditions"], *action["rejected_when"]]
            action_effects = action["rejected_effects"]
            navigates_to = None
        elif mode == "conflict":
            action_preconditions = [*action["role_preconditions"], *action["conflict_when"]]
            action_effects = action["conflict_effects"]
            navigates_to = None
        elif mode == "unauthorized":
            action_preconditions = action["unauthorized_when"]
            action_effects = action["unauthorized_effects"]
            navigates_to = None
        else:
            action_preconditions = [*action["role_preconditions"], *action["preconditions"]]
            action_effects = action["effects"]
            navigates_to = action.get("navigates_to")
        preconditions = [
            _resolve_check_inputs(check, step_input)
            for check in action_preconditions
        ]
        checks = [
            _resolve_check_inputs(check, step_input)
            for check in action_effects
        ]
        extra_checks = _compile_raw_checks(
            raw_step.get("expect", []),
            source=f"scenario:{scenario_id}:step:{index}:expect",
            phase="post",
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        checks.extend(_resolve_check_inputs(check, step_input) for check in extra_checks)
        _reject_detectable_conflicts([*preconditions, *checks], scenario_id, index)

        steps.append(
            CompiledStep(
                scenario_id=scenario_id,
                index=index,
                component=component_id,
                action=action_name,
                mode=mode,
                selector=selector,
                input=step_input,
                preconditions=preconditions,
                checks=checks,
                actor=actor_id,
                page=component.get("page"),
                navigates_to=navigates_to,
            )
        )

    tier = scenario.get("tier")
    tier_name = str(tier) if tier is not None else None
    kind = _parse_scenario_kind(scenario, scenario_id)
    weight = _parse_scenario_weight(scenario, scenario_id, kind, tier_name, tier_weights)
    visibility = _parse_scenario_visibility(scenario, scenario_id)
    difficulty = scenario.get("difficulty")
    if difficulty is not None and (not isinstance(difficulty, str) or not difficulty):
        raise DslCompileError(f"Scenario {scenario_id!r} difficulty must be a non-empty string")
    description = scenario.get("description")
    if description is not None and not isinstance(description, str):
        raise DslCompileError(f"Scenario {scenario_id!r} description must be a string")
    source = scenario.get("_source_path") or scenario.get("_source")
    if source is not None and not isinstance(source, str):
        raise DslCompileError(f"Scenario {scenario_id!r} _source must be a string")
    return CompiledScenario(
        id=scenario_id,
        tier=tier_name,
        steps=steps,
        kind=kind,
        weight=weight,
        visibility=visibility,
        difficulty=difficulty,
        description=description,
        source=source,
    )


def _parse_tier_weights(scenarios: dict[str, Any]) -> dict[str, float]:
    raw = scenarios.get("tier_weights", {})
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise DslCompileError("scenarios.tier_weights must be a mapping")
    weights: dict[str, float] = {}
    for tier, value in raw.items():
        if not isinstance(tier, str) or not tier:
            raise DslCompileError("scenarios.tier_weights keys must be non-empty strings")
        weights[tier] = _parse_positive_weight(value, f"scenarios.tier_weights.{tier}")
    return weights


def _parse_scenario_kind(scenario: dict[str, Any], scenario_id: str) -> str:
    kind = scenario.get("kind", "scoring")
    if not isinstance(kind, str) or kind not in SUPPORTED_SCENARIO_KINDS:
        supported = ", ".join(sorted(SUPPORTED_SCENARIO_KINDS))
        raise DslCompileError(
            f"Scenario {scenario_id!r} kind must be one of {supported}; got {kind!r}"
        )
    return kind


def _parse_scenario_weight(
    scenario: dict[str, Any],
    scenario_id: str,
    kind: str,
    tier: str | None,
    tier_weights: dict[str, float],
) -> float:
    if "weight" in scenario:
        value = scenario["weight"]
        if kind == "probe":
            return _parse_nonnegative_weight(value, f"Scenario {scenario_id!r} weight")
        return _parse_positive_weight(value, f"Scenario {scenario_id!r} weight")
    if tier and tier in tier_weights:
        return tier_weights[tier]
    return 1.0


def _parse_scenario_visibility(scenario: dict[str, Any], scenario_id: str) -> str:
    visibility = scenario.get("visibility", "private")
    if not isinstance(visibility, str) or visibility not in SUPPORTED_SCENARIO_VISIBILITIES:
        supported = ", ".join(sorted(SUPPORTED_SCENARIO_VISIBILITIES))
        raise DslCompileError(
            f"Scenario {scenario_id!r} visibility must be one of {supported}; "
            f"got {visibility!r}"
        )
    return visibility


def _parse_positive_weight(value: Any, source: str) -> float:
    parsed = _parse_nonnegative_weight(value, source)
    if parsed <= 0:
        raise DslCompileError(f"{source} must be greater than 0")
    return parsed


def _parse_nonnegative_weight(value: Any, source: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise DslCompileError(f"{source} must be numeric")
    parsed = float(value)
    if parsed < 0:
        raise DslCompileError(f"{source} must be greater than or equal to 0")
    return parsed


def _compile_wait_like_step(
    raw_step: dict[str, Any],
    *,
    scenario_id: str,
    index: int,
    components: dict[str, dict[str, Any]],
    state_schema: dict[str, str],
    dsl_version: str,
    persistence: dict[str, Any],
    pages: dict[str, str],
    actors: dict[str, dict[str, str | None]],
    events: dict[str, dict[str, Any]],
    tables: dict[str, dict[str, Any]],
) -> CompiledStep | None:
    actor_id = _parse_step_actor(
        raw_step,
        scenario_id=scenario_id,
        index=index,
        dsl_version=dsl_version,
        actors=actors,
    )
    if "browser" in raw_step:
        if dsl_version not in BROWSER_ACTION_DSL_VERSIONS:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses browser actions, "
                "which require DSL 2.0.1 or newer"
            )
        browser_action, browser_page, browser_path = _parse_browser_step(
            raw_step,
            scenario_id=scenario_id,
            index=index,
        )
        if browser_action == "reload":
            if "reload" not in persistence:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} uses browser reload, "
                    "but contract.runtime.persistence.reload is missing"
                )
        elif browser_action in {"back", "forward"}:
            if dsl_version not in BROWSER_HISTORY_DSL_VERSIONS:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} uses browser {browser_action}, "
                    "which requires DSL 2.0.2 or newer"
                )
            if not browser_page:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} browser {browser_action} "
                    "requires expect_page"
                )
        elif browser_action == "goto":
            if dsl_version not in BROWSER_GOTO_DSL_VERSIONS:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} uses browser goto, "
                    "which requires DSL 2.0.3 or newer"
                )
            if browser_page and browser_page not in pages:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} browser goto references "
                    f"unknown page {browser_page!r}"
                )
            if not browser_path and not browser_page:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} browser goto requires page or path"
                )
        else:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} browser must be reload, back, forward, or goto"
            )
        if browser_page and browser_page not in pages:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} expect_page references "
                f"unknown page {browser_page!r}"
            )
        if browser_action == "goto" and browser_page and not browser_path:
            browser_path = pages[browser_page]
        checks = _compile_step_expect(raw_step, scenario_id, index, state_schema, dsl_version)
        _reject_detectable_conflicts(checks, scenario_id, index)
        return CompiledStep(
            scenario_id=scenario_id,
            index=index,
            component="",
            action=browser_action,
            mode="normal",
            selector="",
            input={"path": browser_path} if browser_path else {},
            preconditions=[],
            checks=checks,
            actor=actor_id,
            navigates_to=browser_page,
        )

    if "event" in raw_step:
        if dsl_version not in EVENT_DSL_VERSIONS:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses event, "
                "which requires DSL 2.3.1 or newer"
            )
        raw_event = raw_step.get("event")
        event_id = raw_event.get("id") if isinstance(raw_event, dict) else raw_event
        if not isinstance(event_id, str) or not event_id:
            raise DslCompileError(f"Scenario {scenario_id!r} step {index} event must be a string or mapping id")
        try:
            event = events[event_id]
        except KeyError as exc:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} references unknown event {event_id!r}"
            ) from exc
        extra_checks = _compile_step_expect(raw_step, scenario_id, index, state_schema, dsl_version)
        checks = [*event["effects"], *extra_checks]
        _reject_detectable_conflicts([*event["preconditions"], *checks], scenario_id, index)
        return CompiledStep(
            scenario_id=scenario_id,
            index=index,
            component="",
            action="event",
            mode="normal",
            selector="",
            input={"event": event_id, "payload": event["payload"]},
            preconditions=event["preconditions"],
            checks=checks,
            actor=actor_id,
        )

    if "table" in raw_step:
        if dsl_version not in TABLE_DSL_VERSIONS:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses table inspection, "
                "which requires DSL 2.4.1 or newer"
            )
        table_id = raw_step.get("table")
        if not isinstance(table_id, str) or not table_id:
            raise DslCompileError(f"Scenario {scenario_id!r} step {index} table must be a string")
        if table_id not in tables:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} references unknown table {table_id!r}"
            )
        checks: list[CompiledCheck] = []
        if "expect_order" in raw_step:
            order = raw_step["expect_order"]
            if not isinstance(order, list) or not all(isinstance(item, str) for item in order):
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} expect_order must be a list of strings"
                )
            checks.append(
                CompiledCheck(
                    op="table_order_equals",
                    path=f"__tables.{table_id}.order",
                    spec={"table": table_id, "expected": list(order)},
                    source=f"scenario:{scenario_id}:step:{index}:table_order",
                    phase="post",
                )
            )
        if "expect_row_count" in raw_step:
            row_count = raw_step["expect_row_count"]
            if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 0:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} expect_row_count must be a non-negative integer"
                )
            checks.append(
                CompiledCheck(
                    op="table_row_count_equals",
                    path=f"__tables.{table_id}.count",
                    spec={"table": table_id, "expected": row_count},
                    source=f"scenario:{scenario_id}:step:{index}:table_row_count",
                    phase="post",
                )
            )
        raw_rows = raw_step.get("expect_rows", [])
        if raw_rows is None:
            raw_rows = []
        if not isinstance(raw_rows, list):
            raise DslCompileError(f"Scenario {scenario_id!r} step {index} expect_rows must be a list")
        declared_columns = set(tables[table_id]["columns"])
        for row_index, row in enumerate(raw_rows, start=1):
            if not isinstance(row, dict):
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} expect_rows[{row_index}] must be a mapping"
                )
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} expect_rows[{row_index}].id must be a string"
                )
            cells = row.get("cells")
            if not isinstance(cells, dict) or not cells:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {index} expect_rows[{row_index}].cells must be a mapping"
                )
            for column_id, expected in cells.items():
                if column_id not in declared_columns:
                    raise DslCompileError(
                        f"Scenario {scenario_id!r} step {index} expect_rows[{row_index}] "
                        f"references unknown table column {column_id!r}"
                    )
                if not isinstance(expected, (str, int, float, bool)) or isinstance(expected, bool):
                    if not isinstance(expected, str):
                        raise DslCompileError(
                            f"Scenario {scenario_id!r} step {index} table cell expectations must be scalar"
                        )
                checks.append(
                    CompiledCheck(
                        op="table_cell_equals",
                        path=f"__tables.{table_id}.rows.{row_id}.{column_id}",
                        spec={
                            "table": table_id,
                            "row_id": row_id,
                            "column": column_id,
                            "expected": expected,
                        },
                        source=f"scenario:{scenario_id}:step:{index}:table_cell",
                        phase="post",
                    )
                )
        return CompiledStep(
            scenario_id=scenario_id,
            index=index,
            component="",
            action="snapshot",
            mode="normal",
            selector="",
            input={},
            preconditions=[],
            checks=checks,
            actor=actor_id,
        )

    if "wait_ms" in raw_step:
        if dsl_version not in WAIT_STEP_DSL_VERSIONS:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} uses wait_ms, "
                "which requires DSL 1.1.1 or newer"
            )
        wait_ms = raw_step.get("wait_ms")
        if not isinstance(wait_ms, int) or wait_ms <= 0:
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} wait_ms must be a positive integer"
            )
        checks = _compile_step_expect(raw_step, scenario_id, index, state_schema, dsl_version)
        _reject_detectable_conflicts(checks, scenario_id, index)
        return CompiledStep(
            scenario_id=scenario_id,
            index=index,
            component="",
            action="wait",
            mode="normal",
            selector="",
            input={"ms": wait_ms},
            preconditions=[],
            checks=checks,
            actor=actor_id,
        )

    if "await" not in raw_step:
        return None
    if dsl_version not in ASYNC_ACTION_DSL_VERSIONS:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} uses await, "
            "which requires DSL 1.2.0 or newer"
        )
    raw_await = raw_step.get("await")
    if not isinstance(raw_await, str):
        raise DslCompileError(f"Scenario {scenario_id!r} step {index} await must be a string")
    component_id, action_name = _parse_action_ref(raw_await, scenario_id, index, field="await")
    try:
        action = components[component_id]["actions"][action_name]
    except KeyError as exc:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} awaits unknown action {raw_await!r}"
        ) from exc
    async_effects = action.get("async_effects")
    if not async_effects:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} awaits {raw_await!r}, "
            "but that action declares no async_effects"
        )
    extra_checks = _compile_step_expect(raw_step, scenario_id, index, state_schema, dsl_version)
    checks = [*async_effects["effects"], *extra_checks]
    _reject_detectable_conflicts(checks, scenario_id, index)
    return CompiledStep(
        scenario_id=scenario_id,
        index=index,
        component="",
        action="wait",
        mode="normal",
        selector="",
        input={"ms": async_effects["after_ms"]},
        preconditions=[],
        checks=checks,
        actor=actor_id,
    )


def _parse_step_actor(
    raw_step: dict[str, Any],
    *,
    scenario_id: str,
    index: int,
    dsl_version: str,
    actors: dict[str, dict[str, str | None]],
) -> str | None:
    raw_actor = raw_step.get("actor")
    if raw_actor is None:
        return None
    if dsl_version not in ACTOR_DSL_VERSIONS:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} uses actor, "
            "which requires DSL 2.1.1 or newer"
        )
    if not actors:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} uses actor, "
            "but contract.runtime.actors is missing"
        )
    if not isinstance(raw_actor, str) or not raw_actor:
        raise DslCompileError(f"Scenario {scenario_id!r} step {index} actor must be a non-empty string")
    if raw_actor not in actors:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} references unknown actor {raw_actor!r}"
        )
    return raw_actor


def _parse_browser_step(
    raw_step: dict[str, Any],
    *,
    scenario_id: str,
    index: int,
) -> tuple[str, str | None, str | None]:
    raw_browser = raw_step.get("browser")
    page = raw_step.get("page")
    path = raw_step.get("path")
    expect_page = raw_step.get("expect_page")
    if isinstance(raw_browser, str):
        action = raw_browser
    elif isinstance(raw_browser, dict):
        action = raw_browser.get("action")
        page = raw_browser.get("page", page)
        path = raw_browser.get("path", path)
        expect_page = raw_browser.get("expect_page", expect_page)
    else:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} browser must be a string or mapping"
        )
    if action not in {"reload", "back", "forward", "goto"}:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} browser action is unsupported: {action!r}"
        )

    target_page = page if action == "goto" else None
    expected_page = expect_page or target_page
    if expected_page is not None and (not isinstance(expected_page, str) or not expected_page):
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} expect_page must be a non-empty string"
        )
    if target_page is not None and (not isinstance(target_page, str) or not target_page):
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} browser goto page must be a non-empty string"
        )
    if path is not None:
        if not isinstance(path, str) or not path.startswith("/"):
            raise DslCompileError(
                f"Scenario {scenario_id!r} step {index} browser path must start with '/'"
            )
    if action == "goto" and target_page and path:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} browser goto must use page or path, not both"
        )
    if action != "goto" and (page is not None or path is not None):
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} browser {action} does not accept page/path"
        )
    return str(action), str(expected_page) if expected_page else None, str(path) if path else None


def _compile_step_expect(
    raw_step: dict[str, Any],
    scenario_id: str,
    index: int,
    state_schema: dict[str, str],
    dsl_version: str,
) -> list[CompiledCheck]:
    return _compile_raw_checks(
        raw_step.get("expect", []),
        source=f"scenario:{scenario_id}:step:{index}:expect",
        phase="post",
        state_schema=state_schema,
        dsl_version=dsl_version,
    )


def _resolve_component_selector(component: dict[str, Any], step_input: dict[str, Any]) -> str:
    selector_template = component.get("selector_template")
    if not selector_template:
        return str(component["selector"])

    def replace(match: re.Match[str]) -> str:
        value = _resolve_input_ref(match.group(1), step_input)
        return _escape_selector_template_value(value)

    return SELECTOR_INPUT_TOKEN_PATTERN.sub(replace, str(selector_template))


def _escape_selector_template_value(value: Any) -> str:
    text = str(value)
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _parse_step_action(raw_step: dict[str, Any], scenario_id: str, index: int) -> tuple[str, str]:
    if "do" in raw_step:
        action_ref = raw_step["do"]
        if not isinstance(action_ref, str):
            raise DslCompileError(f"Scenario {scenario_id!r} step {index} do must be a string")
        return _parse_action_ref(action_ref, scenario_id, index, field="do")

    component_id = raw_step.get("component")
    action_name = raw_step.get("action")
    if not isinstance(component_id, str) or not isinstance(action_name, str):
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} requires do or component/action"
        )
    return component_id, action_name


def _parse_action_ref(
    value: str,
    scenario_id: str,
    index: int,
    *,
    field: str,
) -> tuple[str, str]:
    if "." not in value:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} {field} must look like component.action"
        )
    component_id, action_name = value.rsplit(".", 1)
    if not component_id or not action_name:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} {field} must look like component.action"
        )
    return component_id, action_name


def _validate_upload_step_input(
    step_input: dict[str, Any],
    *,
    scenario_id: str,
    index: int,
    dsl_version: str,
) -> None:
    if dsl_version not in FILE_INPUT_DSL_VERSIONS:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} upload requires DSL 2.5.1 or newer"
        )
    file_payload = step_input.get("file")
    if not isinstance(file_payload, dict):
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} upload input requires file mapping"
        )
    name = file_payload.get("name")
    content = file_payload.get("content")
    if not isinstance(name, str) or not name:
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} upload file.name must be a non-empty string"
        )
    if not isinstance(content, str):
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} upload file.content must be a string"
        )
    mime_type = file_payload.get("mime_type")
    if mime_type is not None and (not isinstance(mime_type, str) or not mime_type):
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {index} upload file.mime_type must be a non-empty string"
        )


def _validate_normalizers(raw_normalizers: Any, *, source: str) -> None:
    normalizers = _parse_normalizers(raw_normalizers)
    if not normalizers:
        raise DslCompileError(f"{source} equals_normalized requires non-empty normalizers")


def _compile_raw_checks(
    raw_checks: Any,
    *,
    source: str,
    phase: str,
    state_schema: dict[str, str],
    dsl_version: str,
) -> list[CompiledCheck]:
    if raw_checks is None:
        return []
    if not isinstance(raw_checks, list):
        raise DslCompileError(f"{source} must be a list")

    checks: list[CompiledCheck] = []
    for raw in _flatten_raw_checks(raw_checks):
        if not isinstance(raw, dict):
            raise DslCompileError(f"{source} checks must be mappings")
        op = raw.get("op")
        path = raw.get("path")
        supported_checks = SUPPORTED_CHECKS_BY_VERSION[dsl_version]
        if not isinstance(op, str) or op not in supported_checks:
            raise DslCompileError(
                f"{source} uses unsupported check op {op!r} for DSL {dsl_version}"
            )
        if phase == "pre" and op not in SUPPORTED_PRECONDITIONS:
            raise DslCompileError(f"{source} uses unsupported precondition op {op!r}")
        if not isinstance(path, str) or not path:
            raise DslCompileError(f"{source} check {op!r} requires path")
        _validate_check(raw, op, path, source, state_schema, dsl_version=dsl_version)
        checks.append(
            CompiledCheck(
                op=op,
                path=path,
                spec=dict(raw),
                source=source,
                phase=phase,
            )
        )
    return checks


def _flatten_raw_checks(raw_checks: list[Any]) -> list[Any]:
    flattened: list[Any] = []
    for raw in raw_checks:
        if isinstance(raw, list):
            flattened.extend(_flatten_raw_checks(raw))
        else:
            flattened.append(raw)
    return flattened


def _validate_check(
    raw: dict[str, Any],
    op: str,
    path: str,
    source: str,
    state_schema: dict[str, str],
    *,
    dsl_version: str,
) -> None:
    if path not in state_schema:
        raise DslCompileError(f"{source} references undeclared state path {path!r}")
    if op == "changed_by" and state_schema[path] != "number":
        raise DslCompileError(f"{source} changed_by requires number path; {path!r} is {state_schema[path]!r}")
    if op == "changed_by" and "by" not in raw:
        raise DslCompileError(f"{source} changed_by requires by")
    if op == "advanced_time_by":
        if state_schema[path] != "number":
            raise DslCompileError(
                f"{source} advanced_time_by requires number path; {path!r} is {state_schema[path]!r}"
            )
        by = raw.get("by")
        if not isinstance(by, (int, float)) or isinstance(by, bool):
            raise DslCompileError(f"{source} advanced_time_by requires numeric by")
    if op == "changed_by_path":
        if state_schema[path] != "number":
            raise DslCompileError(
                f"{source} changed_by_path requires number path; {path!r} is {state_schema[path]!r}"
            )
        by_path = raw.get("by_path")
        if by_path not in state_schema:
            raise DslCompileError(f"{source} changed_by_path references undeclared by_path {by_path!r}")
        if state_schema[by_path] != "number":
            raise DslCompileError(
                f"{source} changed_by_path requires number by_path; {by_path!r} is {state_schema[by_path]!r}"
            )
        multiplier = raw.get("multiplier", 1)
        if not isinstance(multiplier, (int, float)):
            raise DslCompileError(f"{source} changed_by_path multiplier must be numeric")
    if op == "toggled" and state_schema[path] != "boolean":
        raise DslCompileError(f"{source} toggled requires boolean path; {path!r} is {state_schema[path]!r}")
    if op == "relation":
        operator = raw.get("operator", raw.get("relation"))
        if operator not in RELATION_OPERATORS:
            raise DslCompileError(f"{source} relation uses unsupported operator {operator!r}")
        if "other_path" not in raw and "value" not in raw and "value_from" not in raw:
            raise DslCompileError(f"{source} relation requires other_path, value, or value_from")
        other_path = raw.get("other_path")
        if other_path is not None and other_path not in state_schema:
            raise DslCompileError(f"{source} relation references undeclared other_path {other_path!r}")
    if op == "equals" and "value" not in raw and "value_from" not in raw:
        raise DslCompileError(f"{source} equals requires value or value_from")
    if op == "equals_normalized":
        if dsl_version not in NORMALIZATION_DSL_VERSIONS:
            raise DslCompileError(f"{source} equals_normalized requires DSL 2.6.1 or newer")
        if state_schema[path] not in {"string", "number", "any"}:
            raise DslCompileError(
                f"{source} equals_normalized requires string, number, or any path; "
                f"{path!r} is {state_schema[path]!r}"
            )
        if "value" not in raw and "value_from" not in raw:
            raise DslCompileError(f"{source} equals_normalized requires value or value_from")
        _validate_normalizers(raw.get("normalizers", raw.get("normalizer")), source=source)
    if op in {"one_of", "not_one_of"}:
        values = raw.get("values")
        if not isinstance(values, list) or not values:
            raise DslCompileError(f"{source} {op} requires non-empty values list")
        for index, value in enumerate(values, start=1):
            if state_schema[path] != "any" and not _value_matches_type(value, state_schema[path]):
                raise DslCompileError(
                    f"{source} {op} values item {index} must match path type "
                    f"{state_schema[path]!r}"
                )
    if op in {"contains", "not_contains"}:
        if state_schema[path] not in {"array", "string"}:
            raise DslCompileError(
                f"{source} {op} requires array or string path; {path!r} is {state_schema[path]!r}"
            )
        if "value" not in raw and "value_from" not in raw:
            raise DslCompileError(f"{source} {op} requires value or value_from")
    if op == "appended":
        if state_schema[path] != "array":
            raise DslCompileError(f"{source} appended requires array path; {path!r} is {state_schema[path]!r}")
        if "value" not in raw and "value_from" not in raw:
            raise DslCompileError(f"{source} appended requires value or value_from")
    if op == "appended_object":
        if state_schema[path] != "array":
            raise DslCompileError(
                f"{source} appended_object requires array path; {path!r} is {state_schema[path]!r}"
            )
        if "value" not in raw:
            raise DslCompileError(f"{source} appended_object requires value template")
        _validate_value_template(raw["value"], source=source, state_schema=state_schema)
    if op == "matches":
        if state_schema[path] != "string":
            raise DslCompileError(f"{source} matches requires string path; {path!r} is {state_schema[path]!r}")
        if not isinstance(raw.get("pattern"), str):
            raise DslCompileError(f"{source} matches requires string pattern")
    if op == "equals_template":
        if state_schema[path] != "string":
            raise DslCompileError(
                f"{source} equals_template requires string path; {path!r} is {state_schema[path]!r}"
            )
        template = raw.get("template")
        if not isinstance(template, str):
            raise DslCompileError(f"{source} equals_template requires string template")
        for template_path, template_kind in iter_state_template_paths(template):
            if template_path not in state_schema:
                raise DslCompileError(
                    f"{source} equals_template references undeclared template path {template_path!r}"
                )
            if template_kind == "length" and state_schema[template_path] not in {"array", "string"}:
                raise DslCompileError(
                    f"{source} equals_template .length requires array or string path; "
                    f"{template_path!r} is {state_schema[template_path]!r}"
                )
    if op == "equals_linear":
        if state_schema[path] != "number":
            raise DslCompileError(
                f"{source} equals_linear requires number path; {path!r} is {state_schema[path]!r}"
            )
        _validate_linear_formula(
            raw,
            source=source,
            state_schema=state_schema,
            output_path=path,
            op="equals_linear",
            allow_empty_terms=False,
        )
    if op == "equals_piecewise_linear":
        if state_schema[path] != "number":
            raise DslCompileError(
                f"{source} equals_piecewise_linear requires number path; {path!r} is {state_schema[path]!r}"
            )
        cases = raw.get("cases")
        if not isinstance(cases, list) or not cases:
            raise DslCompileError(f"{source} equals_piecewise_linear requires non-empty cases")
        for case_index, case in enumerate(cases, start=1):
            if not isinstance(case, dict):
                raise DslCompileError(f"{source} equals_piecewise_linear case {case_index} must be a mapping")
            conditions = case.get("when")
            if not isinstance(conditions, list) or not conditions:
                raise DslCompileError(
                    f"{source} equals_piecewise_linear case {case_index} requires non-empty when"
                )
            for condition_index, condition in enumerate(conditions, start=1):
                _validate_piecewise_condition(
                    condition,
                    source=f"{source} equals_piecewise_linear case {case_index} condition {condition_index}",
                    state_schema=state_schema,
                    dsl_version=dsl_version,
                )
            formula = case.get("formula")
            if not isinstance(formula, dict):
                raise DslCompileError(
                    f"{source} equals_piecewise_linear case {case_index} requires formula mapping"
                )
            _validate_linear_formula(
                formula,
                source=f"{source} equals_piecewise_linear case {case_index}",
                state_schema=state_schema,
                output_path=path,
                op="equals_piecewise_linear",
                allow_empty_terms=True,
            )
        default = raw.get("default")
        if not isinstance(default, dict):
            raise DslCompileError(f"{source} equals_piecewise_linear requires default formula mapping")
        _validate_linear_formula(
            default,
            source=f"{source} equals_piecewise_linear default",
            state_schema=state_schema,
            output_path=path,
            op="equals_piecewise_linear",
            allow_empty_terms=True,
        )
    if op == "length_changed_by":
        if state_schema[path] not in {"array", "string"}:
            raise DslCompileError(
                f"{source} length_changed_by requires array or string path; {path!r} is {state_schema[path]!r}"
            )
        if not isinstance(raw.get("by"), int):
            raise DslCompileError(f"{source} length_changed_by requires integer by")
    if op == "removed_first" and state_schema[path] != "array":
        raise DslCompileError(f"{source} removed_first requires array path; {path!r} is {state_schema[path]!r}")
    if op in {
        "removed_all_where",
        "removed_all_where_after",
        "removed_first_where",
        "updated_all_where_after",
        "updated_all_where",
        "updated_first_where",
        "moved_first_where",
    }:
        if state_schema[path] != "array":
            raise DslCompileError(f"{source} {op} requires array path; {path!r} is {state_schema[path]!r}")
        where = raw.get("where")
        if not where:
            raise DslCompileError(f"{source} {op} requires non-empty where")
        _validate_item_conditions(
            where,
            source=source,
            op=op,
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        if op in {"updated_first_where", "updated_all_where", "updated_all_where_after"}:
            _validate_item_updates(raw.get("updates"), source=source, op=op, required=True)
        if op == "moved_first_where":
            to_index = raw.get("to_index")
            if not isinstance(to_index, int) or isinstance(to_index, bool) or to_index < 0:
                raise DslCompileError(f"{source} moved_first_where requires non-negative integer to_index")
    if op == "updated_object_fields":
        if state_schema[path] != "object":
            raise DslCompileError(
                f"{source} updated_object_fields requires object path; {path!r} is {state_schema[path]!r}"
            )
        updates = raw.get("updates")
        if not isinstance(updates, dict) or not updates:
            raise DslCompileError(f"{source} updated_object_fields requires non-empty updates mapping")
        for field in updates:
            if not isinstance(field, str) or not field:
                raise DslCompileError(f"{source} updated_object_fields update keys must be non-empty strings")
    if op == "removed_object_fields":
        if state_schema[path] != "object":
            raise DslCompileError(
                f"{source} removed_object_fields requires object path; {path!r} is {state_schema[path]!r}"
            )
        fields = raw.get("fields")
        if not isinstance(fields, list) or not fields:
            raise DslCompileError(f"{source} removed_object_fields requires non-empty fields list")
        for field in fields:
            if not isinstance(field, str) or not field:
                raise DslCompileError(f"{source} removed_object_fields fields must be non-empty strings")
    if op == "equals_object_key_count":
        if state_schema[path] != "number":
            raise DslCompileError(
                f"{source} equals_object_key_count requires number path; {path!r} is {state_schema[path]!r}"
            )
        source_path = raw.get("source_path")
        if source_path not in state_schema:
            raise DslCompileError(
                f"{source} equals_object_key_count references undeclared source_path {source_path!r}"
            )
        if state_schema[source_path] != "object":
            raise DslCompileError(
                f"{source} equals_object_key_count requires object source_path; "
                f"{source_path!r} is {state_schema[source_path]!r}"
            )
    if op in {"updated_first_child_where", "removed_first_child_where"}:
        if state_schema[path] != "array":
            raise DslCompileError(f"{source} {op} requires array path; {path!r} is {state_schema[path]!r}")
        _validate_nested_collection_shape(raw, source=source, op=op)
        _validate_item_conditions(
            raw.get("parent_where", []),
            source=f"{source} {op} parent_where",
            op=op,
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        child_where = raw.get("child_where")
        if not child_where:
            raise DslCompileError(f"{source} {op} requires non-empty child_where")
        _validate_item_conditions(
            child_where,
            source=f"{source} {op} child_where",
            op=op,
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        if op == "updated_first_child_where":
            _validate_item_updates(raw.get("updates"), source=source, op=op, required=True)
    if op in {"equals_nested_count_where", "equals_nested_sum"}:
        if state_schema[path] != "number":
            raise DslCompileError(
                f"{source} {op} requires number path; {path!r} is {state_schema[path]!r}"
            )
        _validate_collection_source(raw, source=source, state_schema=state_schema, op=op)
        _validate_nested_collection_shape(raw, source=source, op=op)
        _validate_item_conditions(
            raw.get("parent_where", []),
            source=f"{source} {op} parent_where",
            op=op,
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        child_where = raw.get("child_where", [])
        if op == "equals_nested_count_where" and not child_where:
            raise DslCompileError(f"{source} equals_nested_count_where requires non-empty child_where")
        _validate_item_conditions(
            child_where,
            source=f"{source} {op} child_where",
            op=op,
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        if op == "equals_nested_sum":
            field = raw.get("field")
            if not isinstance(field, str) or not field:
                raise DslCompileError(f"{source} equals_nested_sum requires field")
            multiplier = raw.get("multiplier", 1)
            if not isinstance(multiplier, (int, float)) or isinstance(multiplier, bool):
                raise DslCompileError(f"{source} equals_nested_sum multiplier must be numeric")
            constant = raw.get("constant", 0)
            if not isinstance(constant, (int, float)) or isinstance(constant, bool):
                raise DslCompileError(f"{source} equals_nested_sum constant must be numeric")
            precision = raw.get("round")
            if precision is not None and (
                not isinstance(precision, int) or isinstance(precision, bool) or precision < 0
            ):
                raise DslCompileError(f"{source} equals_nested_sum round must be a non-negative integer")
    if op == "appended_from_first_where":
        if state_schema[path] != "array":
            raise DslCompileError(
                f"{source} appended_from_first_where requires array path; {path!r} is {state_schema[path]!r}"
            )
        _validate_collection_source(raw, source=source, state_schema=state_schema, op=op)
        where = raw.get("where")
        if not where:
            raise DslCompileError(f"{source} appended_from_first_where requires non-empty where")
        _validate_item_conditions(
            where,
            source=source,
            op=op,
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        _validate_item_updates(raw.get("updates", {}), source=source, op=op, required=False)
    if op == "equals_length":
        if state_schema[path] != "number":
            raise DslCompileError(
                f"{source} equals_length requires number path; {path!r} is {state_schema[path]!r}"
            )
        source_path = raw.get("source_path")
        if source_path not in state_schema:
            raise DslCompileError(f"{source} equals_length references undeclared source_path {source_path!r}")
        if state_schema[source_path] not in {"array", "string"}:
            raise DslCompileError(
                f"{source} equals_length requires array or string source_path; "
                f"{source_path!r} is {state_schema[source_path]!r}"
            )
    if op in {"equals_count_where", "equals_sum", "equals_any_where"}:
        expected_type = "boolean" if op == "equals_any_where" else "number"
        if state_schema[path] != expected_type:
            raise DslCompileError(
                f"{source} {op} requires {expected_type} path; {path!r} is {state_schema[path]!r}"
            )
        _validate_collection_source(raw, source=source, state_schema=state_schema, op=op)
        where = raw.get("where", [])
        if op in {"equals_count_where", "equals_any_where"} and not where:
            raise DslCompileError(f"{source} {op} requires non-empty where")
        _validate_item_conditions(
            where,
            source=source,
            op=op,
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        if op == "equals_sum":
            field = raw.get("field")
            if not isinstance(field, str) or not field:
                raise DslCompileError(f"{source} equals_sum requires field")
            multiplier = raw.get("multiplier", 1)
            if not isinstance(multiplier, (int, float)) or isinstance(multiplier, bool):
                raise DslCompileError(f"{source} equals_sum multiplier must be numeric")
            constant = raw.get("constant", 0)
            if not isinstance(constant, (int, float)) or isinstance(constant, bool):
                raise DslCompileError(f"{source} equals_sum constant must be numeric")
            precision = raw.get("round")
            if precision is not None and (
                not isinstance(precision, int) or isinstance(precision, bool) or precision < 0
            ):
                raise DslCompileError(f"{source} equals_sum round must be a non-negative integer")
    if op in {"equals_first_item_field", "equals_last_item_field"}:
        if state_schema[path] == "array":
            raise DslCompileError(f"{source} {op} output path must be scalar; {path!r} is array")
        _validate_collection_source(raw, source=source, state_schema=state_schema, op=op)
        field = raw.get("field")
        if not isinstance(field, str) or not field:
            raise DslCompileError(f"{source} {op} requires field")
        if "default" not in raw:
            raise DslCompileError(f"{source} {op} requires default")
        default = raw["default"]
        if state_schema[path] != "any" and not _value_matches_type(default, state_schema[path]):
            raise DslCompileError(
                f"{source} {op} default must match output path type {state_schema[path]!r}"
            )
    if op == "equals_filter":
        if state_schema[path] != "array":
            raise DslCompileError(
                f"{source} equals_filter requires array path; {path!r} is {state_schema[path]!r}"
            )
        _validate_collection_source(raw, source=source, state_schema=state_schema, op=op)
        _validate_item_conditions(
            raw.get("where", []),
            source=source,
            op=op,
            state_schema=state_schema,
            dsl_version=dsl_version,
        )
        order_by = raw.get("order_by", [])
        if not isinstance(order_by, list):
            raise DslCompileError(f"{source} equals_filter order_by must be a list")
        for index, order in enumerate(order_by, start=1):
            if not isinstance(order, dict):
                raise DslCompileError(f"{source} equals_filter order_by {index} must be a mapping")
            field = order.get("field")
            if not isinstance(field, str) or not field:
                raise DslCompileError(f"{source} equals_filter order_by {index} requires field")
            direction = order.get("direction", "asc")
            if direction not in {"asc", "desc"}:
                raise DslCompileError(
                    f"{source} equals_filter order_by {index} direction must be asc or desc"
                )
    if op == "equals_join_projection":
        if dsl_version not in JOIN_PROJECTION_DSL_VERSIONS:
            raise DslCompileError(f"{source} equals_join_projection requires DSL 2.8.1 or newer")
        if state_schema[path] != "array":
            raise DslCompileError(
                f"{source} equals_join_projection requires array path; {path!r} is {state_schema[path]!r}"
            )
        _validate_join_projection(raw, source=source, state_schema=state_schema, dsl_version=dsl_version)


def _validate_value_template(template: Any, *, source: str, state_schema: dict[str, str]) -> None:
    if isinstance(template, dict):
        if set(template) == {"from_path"}:
            path = template["from_path"]
            if path not in state_schema:
                raise DslCompileError(f"{source} value template references undeclared from_path {path!r}")
            return
        if set(template) == {"after_path"}:
            path = template["after_path"]
            if path not in state_schema:
                raise DslCompileError(f"{source} value template references undeclared after_path {path!r}")
            return
        if set(template) == {"from_input"}:
            ref = template["from_input"]
            if not isinstance(ref, str) or not ref.startswith("input."):
                raise DslCompileError(f"{source} value template from_input must be an input.* reference")
            return
        for value in template.values():
            _validate_value_template(value, source=source, state_schema=state_schema)
        return
    if isinstance(template, list):
        for value in template:
            _validate_value_template(value, source=source, state_schema=state_schema)


def _validate_linear_formula(
    formula: dict[str, Any],
    *,
    source: str,
    state_schema: dict[str, str],
    output_path: str,
    op: str,
    allow_empty_terms: bool,
) -> None:
    terms = formula.get("terms", [])
    if not isinstance(terms, list) or (not terms and not allow_empty_terms):
        raise DslCompileError(f"{source} {op} requires non-empty terms")
    for index, term in enumerate(terms, start=1):
        if not isinstance(term, dict):
            raise DslCompileError(f"{source} {op} term {index} must be a mapping")
        term_path = term.get("path")
        if term_path not in state_schema:
            raise DslCompileError(
                f"{source} {op} references undeclared term path {term_path!r}"
            )
        if state_schema[term_path] != "number":
            raise DslCompileError(
                f"{source} {op} requires number term path; "
                f"{term_path!r} is {state_schema[term_path]!r}"
            )
        if term_path == output_path:
            raise DslCompileError(f"{source} {op} term path must not equal output path")
        multiplier = term.get("multiplier", 1)
        if not isinstance(multiplier, (int, float)) or isinstance(multiplier, bool):
            raise DslCompileError(f"{source} {op} term {index} multiplier must be numeric")
    constant = formula.get("constant", 0)
    if not isinstance(constant, (int, float)) or isinstance(constant, bool):
        raise DslCompileError(f"{source} {op} constant must be numeric")
    precision = formula.get("round")
    if precision is not None and (
        not isinstance(precision, int) or isinstance(precision, bool) or precision < 0
    ):
        raise DslCompileError(f"{source} {op} round must be a non-negative integer")


def _validate_piecewise_condition(
    condition: Any,
    *,
    source: str,
    state_schema: dict[str, str],
    dsl_version: str,
) -> None:
    if not isinstance(condition, dict):
        raise DslCompileError(f"{source} must be a mapping")
    op = condition.get("op")
    path = condition.get("path")
    if not isinstance(op, str) or op not in SUPPORTED_PRECONDITIONS:
        raise DslCompileError(f"{source} uses unsupported condition op {op!r}")
    if not isinstance(path, str) or not path:
        raise DslCompileError(f"{source} condition {op!r} requires path")
    if "value_from" in condition:
        raise DslCompileError(f"{source} does not support value_from")
    _validate_check(condition, op, path, source, state_schema, dsl_version=dsl_version)


def _validate_collection_source(
    raw: dict[str, Any],
    *,
    source: str,
    state_schema: dict[str, str],
    op: str,
) -> None:
    source_path = raw.get("source_path")
    if source_path not in state_schema:
        raise DslCompileError(f"{source} {op} references undeclared source_path {source_path!r}")
    if state_schema[source_path] != "array":
        raise DslCompileError(
            f"{source} {op} requires array source_path; {source_path!r} is {state_schema[source_path]!r}"
        )


def _validate_nested_collection_shape(raw: dict[str, Any], *, source: str, op: str) -> None:
    child_path = raw.get("child_path")
    if not isinstance(child_path, str) or not child_path:
        raise DslCompileError(f"{source} {op} requires child_path")
    parent_where = raw.get("parent_where", [])
    if parent_where is not None and not isinstance(parent_where, list):
        raise DslCompileError(f"{source} {op} parent_where must be a list")
    child_where = raw.get("child_where", [])
    if child_where is not None and not isinstance(child_where, list):
        raise DslCompileError(f"{source} {op} child_where must be a list")


def _validate_item_conditions(
    conditions: Any,
    *,
    source: str,
    op: str,
    state_schema: dict[str, str],
    dsl_version: str,
) -> None:
    if conditions is None:
        return
    if not isinstance(conditions, list):
        raise DslCompileError(f"{source} {op} where must be a list")
    for index, condition in enumerate(conditions, start=1):
        if not isinstance(condition, dict):
            raise DslCompileError(f"{source} {op} where condition {index} must be a mapping")
        condition_op = condition.get("op")
        field = condition.get("field")
        if not isinstance(condition_op, str) or condition_op not in SUPPORTED_PRECONDITIONS:
            raise DslCompileError(f"{source} {op} where condition {index} uses unsupported op {condition_op!r}")
        if not isinstance(field, str) or not field:
            raise DslCompileError(f"{source} {op} where condition {index} requires field")
        if "value_from" in condition and dsl_version not in ITEM_VALUE_FROM_DSL_VERSIONS:
            raise DslCompileError(
                f"{source} {op} where condition {index} value_from requires DSL 1.3.0 or newer"
            )
        value_from = condition.get("value_from")
        if value_from is not None and (not isinstance(value_from, str) or not value_from.startswith("input.")):
            raise DslCompileError(
                f"{source} {op} where condition {index} value_from must be an input.* reference"
            )
        value_path = condition.get("value_path")
        if value_path is not None and dsl_version not in ITEM_VALUE_PATH_DSL_VERSIONS:
            raise DslCompileError(
                f"{source} {op} where condition {index} value_path requires DSL 0.9.0 or newer"
            )
        if value_path is not None and value_path not in state_schema:
            raise DslCompileError(
                f"{source} {op} where condition {index} references undeclared value_path {value_path!r}"
            )
        if (
            condition_op == "equals"
            and "value" not in condition
            and "value_path" not in condition
            and "value_from" not in condition
        ):
            raise DslCompileError(
                f"{source} {op} where condition {index} equals requires value, value_path, or value_from"
            )
        if condition_op in {"one_of", "not_one_of"}:
            values = condition.get("values")
            if not isinstance(values, list) or not values:
                raise DslCompileError(
                    f"{source} {op} where condition {index} {condition_op} "
                    "requires non-empty values list"
                )
        if condition_op == "relation":
            operator = condition.get("operator", condition.get("relation"))
            if operator not in RELATION_OPERATORS:
                raise DslCompileError(
                    f"{source} {op} where condition {index} uses unsupported operator {operator!r}"
                )
            if (
                "value" not in condition
                and "other_field" not in condition
                and "value_path" not in condition
                and "value_from" not in condition
            ):
                raise DslCompileError(
                    f"{source} {op} where condition {index} relation requires value, "
                    "value_path, value_from, or other_field"
                )
            other_field = condition.get("other_field")
            if other_field is not None and (not isinstance(other_field, str) or not other_field):
                raise DslCompileError(f"{source} {op} where condition {index} other_field must be a string")


def _validate_item_updates(updates: Any, *, source: str, op: str, required: bool) -> None:
    if updates is None:
        if required:
            raise DslCompileError(f"{source} {op} requires updates mapping")
        return
    if not isinstance(updates, dict):
        raise DslCompileError(f"{source} {op} updates must be a mapping")
    if required and not updates:
        raise DslCompileError(f"{source} {op} updates must not be empty")
    for field in updates:
        if not isinstance(field, str) or not field:
            raise DslCompileError(f"{source} {op} updates fields must be non-empty strings")


def _validate_join_projection(
    raw: dict[str, Any],
    *,
    source: str,
    state_schema: dict[str, str],
    dsl_version: str,
) -> None:
    _validate_collection_source(raw, source=source, state_schema=state_schema, op="equals_join_projection")
    lookup_path = raw.get("lookup_path")
    if lookup_path not in state_schema:
        raise DslCompileError(f"{source} equals_join_projection references undeclared lookup_path {lookup_path!r}")
    if state_schema[lookup_path] != "array":
        raise DslCompileError(
            f"{source} equals_join_projection requires array lookup_path; {lookup_path!r} is {state_schema[lookup_path]!r}"
        )
    for key_name in ("source_key", "lookup_key"):
        key_value = raw.get(key_name)
        if not isinstance(key_value, str) or not key_value:
            raise DslCompileError(f"{source} equals_join_projection requires non-empty {key_name}")
    _validate_item_conditions(
        raw.get("where", []),
        source=source,
        op="equals_join_projection",
        state_schema=state_schema,
        dsl_version=dsl_version,
    )
    fields = raw.get("fields")
    if not isinstance(fields, list) or not fields:
        raise DslCompileError(f"{source} equals_join_projection requires non-empty fields list")
    for index, field_spec in enumerate(fields, start=1):
        if not isinstance(field_spec, dict):
            raise DslCompileError(f"{source} equals_join_projection field {index} must be a mapping")
        output_name = field_spec.get("name")
        if not isinstance(output_name, str) or not output_name:
            raise DslCompileError(f"{source} equals_join_projection field {index} requires non-empty name")
        sources = [key for key in ("source_field", "lookup_field", "value") if key in field_spec]
        if len(sources) != 1:
            raise DslCompileError(
                f"{source} equals_join_projection field {index} requires exactly one of "
                "source_field, lookup_field, or value"
            )
        for key in ("source_field", "lookup_field"):
            if key in field_spec and (not isinstance(field_spec[key], str) or not field_spec[key]):
                raise DslCompileError(f"{source} equals_join_projection field {index} {key} must be a string")


def _resolve_check_inputs(check: CompiledCheck, step_input: dict[str, Any]) -> CompiledCheck:
    spec = _resolve_spec_input_refs(dict(check.spec), step_input)
    if check.op == "appended_object" and "value" in spec:
        spec["value"] = _resolve_value_template_inputs(spec["value"], step_input)
    return CompiledCheck(
        op=check.op,
        path=check.path,
        spec=spec,
        source=check.source,
        phase=check.phase,
    )


def _resolve_spec_input_refs(value: Any, step_input: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        resolved = {
            key: _resolve_spec_input_refs(nested, step_input)
            for key, nested in value.items()
        }
        if "value_from" in resolved:
            resolved["value"] = _resolve_input_ref(resolved.pop("value_from"), step_input)
        return resolved
    if isinstance(value, list):
        return [_resolve_spec_input_refs(item, step_input) for item in value]
    return value


def _resolve_value_template_inputs(template: Any, step_input: dict[str, Any]) -> Any:
    if isinstance(template, dict):
        if set(template) == {"from_input"}:
            return _resolve_input_ref(template["from_input"], step_input)
        return {
            key: _resolve_value_template_inputs(value, step_input)
            for key, value in template.items()
        }
    if isinstance(template, list):
        return [_resolve_value_template_inputs(value, step_input) for value in template]
    return template


def _resolve_input_ref(ref: Any, step_input: dict[str, Any]) -> Any:
    if not isinstance(ref, str):
        raise DslCompileError("value_from must be a string")
    if not ref.startswith("input."):
        raise DslCompileError(f"value_from only supports input.* refs in v0.1; got {ref!r}")
    current: Any = step_input
    for part in ref.removeprefix("input.").split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise DslCompileError(f"value_from {ref!r} cannot be resolved from step input")
    return current


def _parse_normalizers(raw_normalizers: Any) -> list[str]:
    if isinstance(raw_normalizers, str):
        normalizers = [raw_normalizers]
    elif isinstance(raw_normalizers, list):
        normalizers = raw_normalizers
    else:
        raise DslCompileError("normalizers must be a string or non-empty list of strings")
    if not normalizers:
        raise DslCompileError("normalizers must not be empty")
    parsed: list[str] = []
    for normalizer in normalizers:
        if not isinstance(normalizer, str) or normalizer not in SUPPORTED_NORMALIZERS:
            supported = ", ".join(sorted(SUPPORTED_NORMALIZERS))
            raise DslCompileError(f"unsupported normalizer {normalizer!r}; supported: {supported}")
        parsed.append(normalizer)
    return parsed


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
            raise DslCompileError(f"unsupported normalizer {normalizer!r}")
    return text


def _normalize_currency_number(value: str) -> str:
    cleaned = re.sub(r"[^0-9.\-]+", "", value)
    if cleaned in {"", "-", ".", "-."}:
        return "0"
    number = float(cleaned)
    if number.is_integer():
        return str(int(number))
    return f"{number:.6f}".rstrip("0").rstrip(".")


def _reject_detectable_conflicts(
    checks: list[CompiledCheck],
    scenario_id: str,
    step_index: int,
) -> None:
    equals_by_path: dict[tuple[str, str], Any] = {}
    changed_paths: set[tuple[str, str]] = set()
    unchanged_paths: set[tuple[str, str]] = set()

    for check in checks:
        key = (check.phase, check.path)
        if check.op == "equals":
            value = check.spec.get("value")
            if key in equals_by_path and equals_by_path[key] != value:
                raise DslCompileError(
                    f"Scenario {scenario_id!r} step {step_index} has conflicting equals "
                    f"checks for {check.path!r}"
                )
            equals_by_path[key] = value
        if check.op in {
            "advanced_time_by",
            "appended",
            "appended_object",
            "appended_from_first_where",
            "changed",
            "changed_by",
            "changed_by_path",
            "length_changed_by",
            "moved_first_where",
            "removed_object_fields",
            "removed_first",
            "removed_all_where",
            "removed_all_where_after",
            "removed_first_child_where",
            "removed_first_where",
            "toggled",
            "updated_all_where",
            "updated_all_where_after",
            "updated_first_child_where",
            "updated_first_where",
            "updated_object_fields",
        }:
            changed_paths.add(key)
        if check.op == "unchanged":
            unchanged_paths.add(key)

    conflict_paths = changed_paths & unchanged_paths
    if conflict_paths:
        path = sorted(conflict_paths)[0][1]
        raise DslCompileError(
            f"Scenario {scenario_id!r} step {step_index} requires {path!r} to both "
            "change and stay unchanged"
        )


def _evaluate_check(
    check: CompiledCheck,
    *,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
) -> AssertionResult:
    try:
        if check.phase == "pre":
            return _evaluate_state_check(check, before_state, label="pre")
        return _evaluate_transition_check(check, before_state, after_state)
    except Exception as exc:  # noqa: BLE001 - malformed app states should be assertion data.
        return AssertionResult(
            type=f"dsl_{check.phase}_{check.op}",
            passed=False,
            message=f"{check.source} raised {exc.__class__.__name__}: {exc}",
        )


def _evaluate_transition_check(
    check: CompiledCheck,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
) -> AssertionResult:
    if check.op == "table_order_equals":
        actual = get_path(after_state, check.path)
        expected = check.spec["expected"]
        return _result(check, actual == expected, actual=actual, expected=expected)
    if check.op == "table_row_count_equals":
        actual = get_path(after_state, check.path)
        expected = check.spec["expected"]
        return _result(check, actual == expected, actual=actual, expected=expected)
    if check.op == "table_cell_equals":
        actual = get_path(after_state, check.path)
        expected = str(check.spec["expected"])
        return _result(check, actual == expected, actual=actual, expected=expected)

    before = get_path(before_state, check.path)
    after = get_path(after_state, check.path)
    spec = check.spec

    if check.op == "equals":
        expected = spec["value"]
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_normalized":
        normalizers = _parse_normalizers(spec.get("normalizers", spec.get("normalizer")))
        actual = _normalize_value(after, normalizers)
        expected = _normalize_value(spec["value"], normalizers)
        return _result(check, actual == expected, actual=actual, expected=expected)
    if check.op == "changed_by":
        expected = before + spec["by"]
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "advanced_time_by":
        expected = before + spec["by"]
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "changed_by_path":
        delta = get_path(before_state, spec["by_path"]) * spec.get("multiplier", 1)
        expected = before + delta
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "changed":
        return _result(check, after != before, actual=after, expected=f"not {before!r}")
    if check.op == "unchanged":
        return _result(check, after == before, actual=after, expected=before)
    if check.op == "toggled":
        expected = not before
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "truthy":
        return _result(check, bool(after), actual=after, expected=True)
    if check.op == "falsey":
        return _result(check, not bool(after), actual=after, expected=False)
    if check.op == "one_of":
        expected = spec["values"]
        return _result(check, after in expected, actual=after, expected=f"one of {expected!r}")
    if check.op == "not_one_of":
        expected = spec["values"]
        return _result(check, after not in expected, actual=after, expected=f"not one of {expected!r}")
    if check.op == "relation":
        return _evaluate_relation(check, after_state, label="post")
    if check.op == "length_changed_by":
        expected = len(before) + spec["by"]
        return _result(check, len(after) == expected, actual=len(after), expected=expected)
    if check.op == "appended":
        expected = [*before, spec["value"]]
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "appended_object":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected_item = _render_value_template(spec["value"], before_state, after_state)
        expected = [*before, expected_item]
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "removed_first":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = before[1:]
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "removed_first_where":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _remove_first_where(before, spec["where"], before_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "removed_all_where":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _remove_all_where(before, spec["where"], before_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "removed_all_where_after":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _remove_all_where(before, spec["where"], after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "updated_first_where":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _update_first_where(before, spec["where"], spec["updates"], before_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "updated_all_where":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _update_all_where(before, spec["where"], spec["updates"], before_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "updated_all_where_after":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _update_all_where(before, spec["where"], spec["updates"], after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "updated_first_child_where":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _update_first_child_where(before, spec, before_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "removed_first_child_where":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _remove_first_child_where(before, spec, before_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "moved_first_where":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        expected = _move_first_where(before, spec["where"], spec["to_index"], before_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "appended_from_first_where":
        if not isinstance(before, list) or not isinstance(after, list):
            raise TypeError(f"{check.path} must be an array")
        source_items = get_path(before_state, spec["source_path"])
        if not isinstance(source_items, list):
            raise TypeError(f"{spec['source_path']} must be an array")
        expected = _append_from_first_where(
            before,
            source_items,
            spec["where"],
            spec.get("updates", {}),
            before_state,
        )
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "updated_object_fields":
        if not isinstance(before, dict) or not isinstance(after, dict):
            raise TypeError(f"{check.path} must be an object")
        expected = {**before, **spec["updates"]}
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "removed_object_fields":
        if not isinstance(before, dict) or not isinstance(after, dict):
            raise TypeError(f"{check.path} must be an object")
        expected = {key: value for key, value in before.items() if key not in spec["fields"]}
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "contains":
        expected = spec["value"]
        return _result(check, expected in after, actual=after, expected=f"contains {expected!r}")
    if check.op == "not_contains":
        expected = spec["value"]
        return _result(check, expected not in after, actual=after, expected=f"not contains {expected!r}")
    if check.op == "matches":
        import re

        pattern = spec["pattern"]
        return _result(check, re.search(pattern, str(after)) is not None, actual=after, expected=pattern)
    if check.op == "equals_template":
        expected = render_state_template(spec["template"], after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_linear":
        expected = _evaluate_linear(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_piecewise_linear":
        expected = _evaluate_piecewise_linear(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_length":
        source_value = get_path(after_state, spec["source_path"])
        expected = len(source_value)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_count_where":
        expected = _count_where(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_sum":
        expected = _sum_items(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_any_where":
        expected = _any_where(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_first_item_field":
        expected = _edge_item_field(spec, after_state, first=True)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_last_item_field":
        expected = _edge_item_field(spec, after_state, first=False)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_filter":
        expected = _filter_items(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_join_projection":
        expected = _join_projection(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_object_key_count":
        source_value = get_path(after_state, spec["source_path"])
        if not isinstance(source_value, dict):
            raise TypeError(f"{spec['source_path']} must be an object")
        expected = len(source_value)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_nested_count_where":
        expected = _nested_count_where(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)
    if check.op == "equals_nested_sum":
        expected = _nested_sum(spec, after_state)
        return _result(check, after == expected, actual=after, expected=expected)

    return AssertionResult(
        type=f"dsl_post_{check.op}",
        passed=False,
        message=f"Unsupported check op: {check.op}",
    )


def _evaluate_state_check(
    check: CompiledCheck,
    state: dict[str, Any],
    *,
    label: str,
) -> AssertionResult:
    actual = get_path(state, check.path)
    spec = check.spec
    if check.op == "equals":
        expected = spec["value"]
        return _result(check, actual == expected, actual=actual, expected=expected)
    if check.op == "equals_normalized":
        normalizers = _parse_normalizers(spec.get("normalizers", spec.get("normalizer")))
        normalized_actual = _normalize_value(actual, normalizers)
        expected = _normalize_value(spec["value"], normalizers)
        return _result(check, normalized_actual == expected, actual=normalized_actual, expected=expected)
    if check.op == "truthy":
        return _result(check, bool(actual), actual=actual, expected=True)
    if check.op == "falsey":
        return _result(check, not bool(actual), actual=actual, expected=False)
    if check.op == "one_of":
        expected = spec["values"]
        return _result(check, actual in expected, actual=actual, expected=f"one of {expected!r}")
    if check.op == "not_one_of":
        expected = spec["values"]
        return _result(check, actual not in expected, actual=actual, expected=f"not one of {expected!r}")
    if check.op == "relation":
        return _evaluate_relation(check, state, label=label)
    return AssertionResult(
        type=f"dsl_{label}_{check.op}",
        passed=False,
        message=f"Unsupported {label} check op: {check.op}",
    )


def _evaluate_relation(
    check: CompiledCheck,
    state: dict[str, Any],
    *,
    label: str,
) -> AssertionResult:
    spec = check.spec
    operator = spec.get("operator", spec.get("relation"))
    left = get_path(state, check.path)
    if "other_path" in spec:
        right = get_path(state, spec["other_path"])
    else:
        right = spec["value"]
    passed = RELATION_OPERATORS[operator](left, right)
    return AssertionResult(
        type=f"dsl_{label}_relation",
        passed=passed,
        message=f"{check.source}: {check.path} should satisfy {operator} {right!r}",
        actual=left,
        expected=f"{operator} {right!r}",
    )


def _evaluate_linear(spec: dict[str, Any], state: dict[str, Any]) -> float:
    expected = float(spec.get("constant", 0))
    for term in spec.get("terms", []):
        expected += get_path(state, term["path"]) * term.get("multiplier", 1)
    if "round" in spec:
        return round(expected, spec["round"])
    return expected


def _evaluate_piecewise_linear(spec: dict[str, Any], state: dict[str, Any]) -> float:
    for case in spec["cases"]:
        if all(_state_condition_passes(condition, state) for condition in case["when"]):
            return _evaluate_linear(case["formula"], state)
    return _evaluate_linear(spec["default"], state)


def _collection_items(spec: dict[str, Any], state: dict[str, Any]) -> list[Any]:
    items = get_path(state, spec["source_path"])
    if not isinstance(items, list):
        raise TypeError(f"{spec['source_path']} must be an array")
    return items


def _count_where(spec: dict[str, Any], state: dict[str, Any]) -> int:
    return sum(
        1
        for item in _collection_items(spec, state)
        if _item_matches(item, spec.get("where", []), state)
    )


def _sum_items(spec: dict[str, Any], state: dict[str, Any]) -> float:
    total = float(spec.get("constant", 0))
    multiplier = spec.get("multiplier", 1)
    field = spec["field"]
    for item in _collection_items(spec, state):
        if _item_matches(item, spec.get("where", []), state):
            value = get_path(item, field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"Collection field {field!r} must be numeric")
            total += value * multiplier
    if "round" in spec:
        total = round(total, int(spec["round"]))
    return total


def _nested_count_where(spec: dict[str, Any], state: dict[str, Any]) -> int:
    count = 0
    for child in _matching_nested_children(spec, state):
        if _item_matches(child, spec.get("child_where", []), state):
            count += 1
    return count


def _nested_sum(spec: dict[str, Any], state: dict[str, Any]) -> float:
    total = float(spec.get("constant", 0))
    multiplier = spec.get("multiplier", 1)
    field = spec["field"]
    for child in _matching_nested_children(spec, state):
        if not _item_matches(child, spec.get("child_where", []), state):
            continue
        value = get_path(child, field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"Nested collection field {field!r} must be numeric")
        total += value * multiplier
    if "round" in spec:
        total = round(total, int(spec["round"]))
    return total


def _matching_nested_children(spec: dict[str, Any], state: dict[str, Any]) -> list[Any]:
    children: list[Any] = []
    for parent in _collection_items(spec, state):
        if not _item_matches(parent, spec.get("parent_where", []), state):
            continue
        child_items = get_path(parent, spec["child_path"])
        if not isinstance(child_items, list):
            raise TypeError(f"child_path {spec['child_path']!r} must resolve to an array")
        children.extend(child_items)
    return children


def _any_where(spec: dict[str, Any], state: dict[str, Any]) -> bool:
    return any(
        _item_matches(item, spec.get("where", []), state)
        for item in _collection_items(spec, state)
    )


def _edge_item_field(spec: dict[str, Any], state: dict[str, Any], *, first: bool) -> Any:
    items = _collection_items(spec, state)
    if not items:
        return spec["default"]
    item = items[0] if first else items[-1]
    return get_path(item, spec["field"])


def _filter_items(spec: dict[str, Any], state: dict[str, Any]) -> list[Any]:
    items = [
        item
        for item in _collection_items(spec, state)
        if _item_matches(item, spec.get("where", []), state)
    ]
    for order in reversed(spec.get("order_by", [])):
        field = order["field"]
        reverse = order.get("direction", "asc") == "desc"
        items.sort(key=lambda item: get_path(item, field), reverse=reverse)
    return items


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
    children = get_path(parent, spec["child_path"])
    if not isinstance(children, list):
        raise TypeError(f"child_path {spec['child_path']!r} must resolve to an array")
    child_index = _first_matching_index(children, spec["child_where"], state)
    if child_index is None:
        return list(items)
    child = children[child_index]
    if not isinstance(child, dict):
        raise TypeError("nested child item must be an object")
    updated_child = {**child, **spec["updates"]}
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
    children = get_path(parent, spec["child_path"])
    if not isinstance(children, list):
        raise TypeError(f"child_path {spec['child_path']!r} must resolve to an array")
    child_index = _first_matching_index(children, spec["child_where"], state)
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


def _join_projection(spec: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    source_items = get_path(state, spec["source_path"])
    lookup_items = get_path(state, spec["lookup_path"])
    if not isinstance(source_items, list):
        raise TypeError(f"{spec['source_path']} must be an array")
    if not isinstance(lookup_items, list):
        raise TypeError(f"{spec['lookup_path']} must be an array")
    lookup_by_key: dict[Any, dict[str, Any]] = {}
    for lookup_item in lookup_items:
        if not isinstance(lookup_item, dict):
            raise TypeError("lookup projection item must be an object")
        lookup_by_key[get_path(lookup_item, spec["lookup_key"])] = lookup_item

    output: list[dict[str, Any]] = []
    for source_item in source_items:
        if not isinstance(source_item, dict):
            raise TypeError("source projection item must be an object")
        if not _item_matches(source_item, spec.get("where", []), state):
            continue
        lookup_item = lookup_by_key.get(get_path(source_item, spec["source_key"]))
        if lookup_item is None:
            raise KeyError(f"missing lookup item for source key {spec['source_key']!r}")
        output.append(_project_join_item(source_item, lookup_item, spec["fields"]))
    return output


def _project_join_item(
    source_item: dict[str, Any],
    lookup_item: dict[str, Any],
    fields: list[dict[str, Any]],
) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    for field_spec in fields:
        name = field_spec["name"]
        if "source_field" in field_spec:
            projected[name] = get_path(source_item, field_spec["source_field"])
        elif "lookup_field" in field_spec:
            projected[name] = get_path(lookup_item, field_spec["lookup_field"])
        else:
            projected[name] = field_spec.get("value")
    return projected


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
    op = condition["op"]
    actual = get_path(item, condition["field"])
    if op == "equals":
        right = get_path(state, condition["value_path"]) if "value_path" in condition else condition["value"]
        return actual == right
    if op == "truthy":
        return bool(actual)
    if op == "falsey":
        return not bool(actual)
    if op == "one_of":
        return actual in condition["values"]
    if op == "not_one_of":
        return actual not in condition["values"]
    if op == "relation":
        operator = condition.get("operator", condition.get("relation"))
        if "other_field" in condition:
            right = get_path(item, condition["other_field"])
        elif "value_path" in condition:
            right = get_path(state, condition["value_path"])
        else:
            right = condition["value"]
        return RELATION_OPERATORS[operator](actual, right)
    raise ValueError(f"Unsupported collection condition op: {op}")


def _state_condition_passes(condition: dict[str, Any], state: dict[str, Any]) -> bool:
    op = condition["op"]
    actual = get_path(state, condition["path"])
    if op == "equals":
        return actual == condition["value"]
    if op == "truthy":
        return bool(actual)
    if op == "falsey":
        return not bool(actual)
    if op == "one_of":
        return actual in condition["values"]
    if op == "not_one_of":
        return actual not in condition["values"]
    if op == "relation":
        operator = condition.get("operator", condition.get("relation"))
        if "other_path" in condition:
            right = get_path(state, condition["other_path"])
        else:
            right = condition["value"]
        return RELATION_OPERATORS[operator](actual, right)
    raise ValueError(f"Unsupported piecewise condition op: {op}")


def _result(check: CompiledCheck, passed: bool, *, actual: Any, expected: Any) -> AssertionResult:
    return AssertionResult(
        type=f"dsl_{check.phase}_{check.op}",
        passed=passed,
        message=f"{check.source}: {check.path} should satisfy {check.op}",
        actual=actual,
        expected=expected,
    )


def _required_string(data: dict[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise DslCompileError(f"{label}.{key} must be a non-empty string")
    return value
