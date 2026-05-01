"""
SubagentLimitMiddleware — truncates excess `task` tool calls in a single LLM
response to enforce a hard cap on parallel subagent delegation.

Hook
----
`after_model` / `aafter_model` — runs after every model response. Inspects
the latest AIMessage; if more than N `task` tool_calls are present, drops
the extras (keeping only the first N). N is read from runtime context
(`max_concurrent_subagents`), clamped to `[MIN_SUBAGENT_LIMIT,
MAX_SUBAGENT_LIMIT]` = `[2, 4]`. Default fallback is `MAX_CONCURRENT_SUBAGENTS`.

The truncation is necessary because LangGraph executes all tool_calls in a
single AIMessage in parallel — without this guard, an unbounded LLM could
spawn dozens of concurrent subagents and exhaust the executor pool.

Internal deerflow imports (rewritten)
-------------------------------------
    deerflow.subagents.executor.MAX_CONCURRENT_SUBAGENTS
        → ._internal.subagent_const.MAX_CONCURRENT_SUBAGENTS

External deps: langchain, langgraph.
"""

import logging
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

# Was: from deerflow.subagents.executor import MAX_CONCURRENT_SUBAGENTS
from ._internal.subagent_const import MAX_CONCURRENT_SUBAGENTS

logger = logging.getLogger(__name__)

# Valid range for max_concurrent_subagents
MIN_SUBAGENT_LIMIT = 2
MAX_SUBAGENT_LIMIT = 4


def _clamp_subagent_limit(value: int) -> int:
    """Clamp subagent limit to valid range [2, 4]."""
    return max(MIN_SUBAGENT_LIMIT, min(MAX_SUBAGENT_LIMIT, value))


class SubagentLimitMiddleware(AgentMiddleware[AgentState]):
    """Truncates excess 'task' tool calls from a single model response.

    When an LLM generates more than max_concurrent parallel task tool calls
    in one response, this middleware keeps only the first max_concurrent and
    discards the rest. This is more reliable than prompt-based limits.

    Args:
        max_concurrent: Maximum number of concurrent subagent calls allowed.
            Defaults to MAX_CONCURRENT_SUBAGENTS (3). Clamped to [2, 4].
    """

    def __init__(self, max_concurrent: int = MAX_CONCURRENT_SUBAGENTS):
        super().__init__()
        self.max_concurrent = _clamp_subagent_limit(max_concurrent)

    def _truncate_task_calls(self, state: AgentState) -> dict | None:
        messages = state.get("messages", [])
        if not messages:
            return None

        last_msg = messages[-1]
        if getattr(last_msg, "type", None) != "ai":
            return None

        tool_calls = getattr(last_msg, "tool_calls", None)
        if not tool_calls:
            return None

        # Count task tool calls
        task_indices = [i for i, tc in enumerate(tool_calls) if tc.get("name") == "task"]
        if len(task_indices) <= self.max_concurrent:
            return None

        # Build set of indices to drop (excess task calls beyond the limit)
        indices_to_drop = set(task_indices[self.max_concurrent :])
        truncated_tool_calls = [tc for i, tc in enumerate(tool_calls) if i not in indices_to_drop]

        dropped_count = len(indices_to_drop)
        logger.warning(f"Truncated {dropped_count} excess task tool call(s) from model response (limit: {self.max_concurrent})")

        # Replace the AIMessage with truncated tool_calls (same id triggers replacement)
        updated_msg = last_msg.model_copy(update={"tool_calls": truncated_tool_calls})
        return {"messages": [updated_msg]}

    @override
    def after_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return self._truncate_task_calls(state)

    @override
    async def aafter_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return self._truncate_task_calls(state)
