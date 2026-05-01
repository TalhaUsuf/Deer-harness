"""
DeferredToolFilterMiddleware — strips deferred tool schemas from
`request.tools` so the LLM never sees them via `bind_tools()`.

The point of deferral
---------------------
DeerFlow registers some tools (typically MCP tools) as "deferred" — their
names are advertised in the system prompt under `<available-deferred-tools>`,
but their schemas are NOT bound to the model. Instead the LLM uses a single
`tool_search` tool to look up specific deferred tools by name when it needs
them. This keeps the bound-tool schema small even when hundreds of MCP tools
are available.

This middleware is the enforcer of that separation: it intercepts every model
call, queries the per-context `DeferredToolRegistry`, and removes any tool
whose name is currently deferred. ToolNode still has all tools (so once the
LLM does call a deferred tool, execution works), but the LLM cannot call
deferred tools blindly because their schemas are absent.

Hook
----
`wrap_model_call` / `awrap_model_call` — runs immediately before the model.

Internal deerflow imports (rewritten in this standalone copy)
------------------------------------------------------------
    deerflow.tools.builtins.tool_search.get_deferred_registry
        → ._internal.tool_search_registry.get_deferred_registry
    (lazy import inside `_filter_tools` to avoid a hard dependency)

External deps: langchain.

──────────────────────────────────────────────────────────────────────────
Original module docstring follows:

Middleware to filter deferred tool schemas from model binding.

When tool_search is enabled, MCP tools are registered in the DeferredToolRegistry
and passed to ToolNode for execution, but their schemas should NOT be sent to the
LLM via bind_tools (that's the whole point of deferral — saving context tokens).

This middleware intercepts wrap_model_call and removes deferred tools from
request.tools so that model.bind_tools only receives active tool schemas.
The agent discovers deferred tools at runtime via the tool_search tool.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelCallResult, ModelRequest, ModelResponse

logger = logging.getLogger(__name__)


class DeferredToolFilterMiddleware(AgentMiddleware[AgentState]):
    """Remove deferred tools from request.tools before model binding.

    ToolNode still holds all tools (including deferred) for execution routing,
    but the LLM only sees active tool schemas — deferred tools are discoverable
    via tool_search at runtime.
    """

    def _filter_tools(self, request: ModelRequest) -> ModelRequest:
        # Was: from deerflow.tools.builtins.tool_search import get_deferred_registry
        from ._internal.tool_search_registry import get_deferred_registry

        registry = get_deferred_registry()
        if not registry:
            return request

        deferred_names = {e.name for e in registry.entries}
        active_tools = [t for t in request.tools if getattr(t, "name", None) not in deferred_names]

        if len(active_tools) < len(request.tools):
            logger.debug(f"Filtered {len(request.tools) - len(active_tools)} deferred tool schema(s) from model binding")

        return request.override(tools=active_tools)

    @override
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        return handler(self._filter_tools(request))

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        return await handler(self._filter_tools(request))
