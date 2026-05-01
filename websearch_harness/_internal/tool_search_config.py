"""
tool_search_config.py — Verbatim copy of `deerflow.config.tool_search_config`.

What it does
------------
Defines `ToolSearchConfig.enabled` — a master switch for the deferred-tool
flow. When True, the agent factory should:

1. Register all MCP / community tools in a `DeferredToolRegistry`.
2. Add the `tool_search` builtin so the LLM can fetch full schemas on demand.
3. Plug `DeferredToolFilterMiddleware` into the middleware chain so deferred
   tool schemas are stripped from `bind_tools()` until promoted.

The flag is consulted by the harness assembly code, not by the providers
themselves — providers don't care whether they are deferred or not.

Original source
---------------
backend/packages/harness/deerflow/config/tool_search_config.py

External deps: pydantic.
"""

from pydantic import BaseModel, Field


class ToolSearchConfig(BaseModel):
    """Configuration for deferred tool loading via tool_search.

    When enabled, MCP/community tools are not loaded into the agent's
    context directly. Instead, they are listed by name in the system
    prompt and discoverable via the `tool_search` tool at runtime.
    """

    enabled: bool = Field(
        default=False,
        description="Defer tools and enable tool_search",
    )


_tool_search_config: ToolSearchConfig | None = None


def get_tool_search_config() -> ToolSearchConfig:
    """Return the cached ToolSearchConfig, lazily initializing on first call."""
    global _tool_search_config
    if _tool_search_config is None:
        _tool_search_config = ToolSearchConfig()
    return _tool_search_config


def load_tool_search_config_from_dict(data: dict) -> ToolSearchConfig:
    """Replace the cached config with one validated from *data*."""
    global _tool_search_config
    _tool_search_config = ToolSearchConfig.model_validate(data)
    return _tool_search_config
