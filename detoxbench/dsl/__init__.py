"""Compiler-style DSL helpers for small DetoxBench targets."""

from detoxbench.dsl.compiler import CompiledScenario
from detoxbench.dsl.compiler import CompiledStep
from detoxbench.dsl.compiler import DslCompileError
from detoxbench.dsl.compiler import TraceScenarioReport
from detoxbench.dsl.compiler import compile_bundle
from detoxbench.dsl.compiler import evaluate_trace
from detoxbench.dsl.compiler import load_dsl_yaml
from detoxbench.dsl.scenario_sets import discover_scenario_paths
from detoxbench.dsl.scenario_sets import load_scenario_bundles
from detoxbench.dsl.web_bridge import compile_dsl_to_web_suite

__all__ = [
    "CompiledScenario",
    "CompiledStep",
    "DslCompileError",
    "TraceScenarioReport",
    "compile_bundle",
    "compile_dsl_to_web_suite",
    "evaluate_trace",
    "discover_scenario_paths",
    "load_scenario_bundles",
    "load_dsl_yaml",
]
