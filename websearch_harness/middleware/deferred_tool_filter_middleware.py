"""
deferred_tool_filter_middleware.py — Strip deferred-tool schemas from
``bind_tools()`` so the LLM only sees active tools.

Hook
----
``wrap_model_call`` / ``awrap_model_call``.

How the deferred-tool flow works
--------------------------------
1. The harness builds the agent with ALL tools (including deferred
   web-search providers + MCP tools) registered in the LangGraph
   ``ToolNode`` for execution routing.
2. Before each model call, this middleware reads the per-async-context
   ``DeferredToolRegistry`` (set by the harness assembly code, see
   ``websearch_harness._internal.deferred_registry``) and removes any
   tool whose name appears in the registry from ``request.tools``.
3. The model thus only sees the schemas for tools that are NOT deferred
   plus the ``tool_search`` builtin, saving context tokens.
4. When the LLM calls ``tool_search("web_search")``, the registry's
   ``promote()`` removes those tools from the deferred set, so on the
   next turn this middleware lets their schemas through.

Why a ContextVar registry
-------------------------
Concurrent agent runs each have their own asyncio context, so each gets
its own registry value without locking. Sync tools dispatched via
``loop.run_in_executor`` inherit the calling context too.

Internal-import rewrites
------------------------
Original                                                          | Rewritten
------------------------------------------------------------------|---------------------------
from deerflow.tools.builtins.tool_search import get_deferred_registry | from .._internal.deferred_registry import get_deferred_registry

Original source
---------------
backend/packages/harness/deerflow/agents/middlewares/deferred_tool_filter_middleware.py
"""

import logging
from collections.abc import Awaitable, Callable
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelCallResult, ModelRequest, ModelResponse

from .._internal.deferred_registry import get_deferred_registry

logger = logging.getLogger(__name__)


class DeferredToolFilterMiddleware(AgentMiddleware[AgentState]):
    """Remove deferred tools from ``request.tools`` before model binding.

    ToolNode still holds all tools (including deferred) for execution
    routing; the LLM only sees active tool schemas — deferred tools are
    discoverable via the ``tool_search`` builtin at runtime.
    """

    def _filter_tools(self, request: ModelRequest) -> ModelRequest:
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
