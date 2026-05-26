from __future__ import annotations

import re
from typing import Any

from detoxbench.core.state import get_path


TEMPLATE_TOKEN_RE = re.compile(r"\{([^{}]+)\}")


def iter_state_template_paths(template: str) -> list[tuple[str, str]]:
    paths: list[tuple[str, str]] = []
    for match in TEMPLATE_TOKEN_RE.finditer(template):
        expression = match.group(1).strip()
        path_expression = expression.split("|default:", 1)[0].strip()
        if path_expression.endswith(".length"):
            paths.append((path_expression.removesuffix(".length"), "length"))
        else:
            paths.append((path_expression, "value"))
    return paths


def render_state_template(template: str, state: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        expression = match.group(1).strip()
        default: str | None = None
        if "|default:" in expression:
            expression, default = expression.split("|default:", 1)
            expression = expression.strip()
            default = default.strip()

        if expression.endswith(".length"):
            value = get_path(state, expression.removesuffix(".length"))
            rendered: Any = len(value)
        else:
            rendered = get_path(state, expression)

        if default is not None and (rendered is None or rendered == ""):
            rendered = default
        return str(rendered)

    return TEMPLATE_TOKEN_RE.sub(replace, template)
