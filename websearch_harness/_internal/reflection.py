"""
reflection.py — Trimmed copy of `deerflow.reflection.resolve_variable`.

What it does
------------
Imports a module by dotted path and returns a named attribute. Format:

    "module.submodule:variable_name"

Raises clear `ImportError` / `AttributeError` so the caller can surface
"missing dependency" errors with actionable install hints.

Used by `_internal/tool_loader.py` to resolve `ToolConfig.use` strings
into the actual `@tool`-decorated callable.

External deps: stdlib (importlib).

Original source
---------------
backend/packages/harness/deerflow/reflection/__init__.py
backend/packages/harness/deerflow/reflection/resolvers.py
"""

from __future__ import annotations

import importlib
from typing import Any


def resolve_variable(path: str, expected_type: type | None = None) -> Any:
    """Import *module* and return *variable*.

    Args:
        path: ``"module.submodule:variable"`` — colon separates the import
              path from the attribute name.
        expected_type: Optional runtime check; raises TypeError if the
              resolved attribute is not an instance of this type.

    Returns:
        The resolved attribute.
    """
    if ":" not in path:
        raise ValueError(f"resolve_variable() requires 'module:attr' format, got: {path!r}")
    module_path, attr_name = path.split(":", 1)
    if not module_path or not attr_name:
        raise ValueError(f"resolve_variable() requires non-empty module and attribute, got: {path!r}")

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(f"resolve_variable: cannot import module {module_path!r} (referenced as {path!r}): {exc}") from exc

    try:
        attr = getattr(module, attr_name)
    except AttributeError as exc:
        raise AttributeError(f"resolve_variable: module {module_path!r} has no attribute {attr_name!r}") from exc

    if expected_type is not None and not isinstance(attr, expected_type):
        raise TypeError(f"resolve_variable: expected {expected_type.__name__}, got {type(attr).__name__} at {path!r}")
    return attr
