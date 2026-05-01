"""
tool_loader.py — Stripped copy of `deerflow.tools.tools.get_available_tools`.

What it does
------------
Given a list of `ToolConfig` entries, resolves each `cfg.use` string via
`resolve_variable()` and returns a list of `BaseTool` instances ready to
hand to a LangChain agent.

What we DROPPED from the original
---------------------------------
The deerflow original also wires up:
  - sandbox bash gating (`is_host_bash_allowed`)
  - built-in tools (`present_files`, `ask_clarification`, `view_image`)
  - subagent tools (`task`)
  - MCP tools via `get_cached_mcp_tools` + extensions config
  - ACP agent tools
  - skill-evolution tool
  - tool-name-mismatch warning

None of those are part of the web-search story, so this trimmed loader
only handles config-defined tools (and optional registration of all
loaded tools into a `DeferredToolRegistry`).

If the caller wants the deferred-tool flow:

    from websearch_harness._internal.deferred_registry import (
        DeferredToolRegistry, set_deferred_registry, tool_search,
    )
    tools = get_available_tools(configs)
    registry = DeferredToolRegistry()
    for t in tools:
        registry.register(t)
    set_deferred_registry(registry)
    # Now hand `tools + [tool_search]` to the agent and add
    # DeferredToolFilterMiddleware so deferred schemas stay hidden.

External deps: langchain.tools.BaseTool.

Original source
---------------
backend/packages/harness/deerflow/tools/tools.py (full impl, ~169 LOC)
"""

from __future__ import annotations

import logging

from langchain.tools import BaseTool

from .reflection import resolve_variable
from .tool_config import ToolConfig

logger = logging.getLogger(__name__)


def get_available_tools(
    configs: list[ToolConfig],
    groups: list[str] | None = None,
) -> list[BaseTool]:
    """Resolve `cfg.use` strings to `BaseTool` instances.

    Args:
        configs: List of `ToolConfig` entries (typically registered via
                 `_internal.app_config.set_tool_configs`).
        groups:  Optional filter — only configs whose `group` is in this
                 list will be loaded. ``None`` means "all groups".

    Returns:
        A list of unique `BaseTool` objects (deduplicated by `.name`).
    """
    selected = [cfg for cfg in configs if groups is None or cfg.group in groups]

    loaded_raw = [(cfg, resolve_variable(cfg.use, BaseTool)) for cfg in selected]

    for cfg, loaded in loaded_raw:
        if cfg.name != loaded.name:
            logger.warning(
                "Tool name mismatch: config name %r does not match tool .name %r (use: %s). The tool's own .name will be used for binding.",
                cfg.name,
                loaded.name,
                cfg.use,
            )

    seen: set[str] = set()
    unique: list[BaseTool] = []
    for _, t in loaded_raw:
        if t.name in seen:
            logger.warning("Duplicate tool name %r detected and skipped.", t.name)
            continue
        unique.append(t)
        seen.add(t.name)
    return unique
