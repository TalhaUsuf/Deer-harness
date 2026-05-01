"""
TokenUsageMiddleware — emits structured logs of input/output token usage
after every model call. Pure side-effect middleware (no state mutation).

Hook
----
`after_model` / `aafter_model` — fires after every model response. Reads
the standard `usage_metadata` field on the latest AIMessage and logs:
    input_tokens=…, output_tokens=…, total_tokens=…

If `usage_metadata` is missing (some custom models do not populate it) the
middleware silently does nothing.

Use this as a starting point if you need richer observability — push to
Prometheus, Datadog, or a SQL audit table from the same hook.

Internal deerflow imports: NONE.
External deps: langchain, langgraph.
"""

import logging
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)


class TokenUsageMiddleware(AgentMiddleware):
    """Logs token usage from model response usage_metadata."""

    @override
    def after_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return self._log_usage(state)

    @override
    async def aafter_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return self._log_usage(state)

    def _log_usage(self, state: AgentState) -> None:
        messages = state.get("messages", [])
        if not messages:
            return None
        last = messages[-1]
        usage = getattr(last, "usage_metadata", None)
        if usage:
            logger.info(
                "LLM token usage: input=%s output=%s total=%s",
                usage.get("input_tokens", "?"),
                usage.get("output_tokens", "?"),
                usage.get("total_tokens", "?"),
            )
        return None
