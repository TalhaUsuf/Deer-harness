"""
CustomInstructionsMiddleware — injects user-supplied instructions as a
SystemMessage on the FIRST turn of a thread only.

Hook
----
`before_agent` — fires once per agent invocation, before any model call.
Reads `custom_instructions` from `runtime.context` first, then falls back
to `langgraph.config.get_config()['configurable']`.

How "first turn" is detected
----------------------------
The middleware checks `not any(m.type == "ai" for m in state["messages"])`
— i.e. "first turn = no AIMessage has been produced on this thread yet".
This is intentionally NOT a length check (`len(messages) > 1` would be
wrong) because state may legitimately contain a SystemMessage or multiple
HumanMessages before the agent has ever replied:

    [HumanMessage]                       -> first turn (inject)
    [HumanMessage, AIMessage, ...]       -> NOT first turn (skip)
    [SystemMessage, HumanMessage]        -> first turn (inject)
    [HumanMessage, HumanMessage]         -> first turn (inject; e.g. resumed
                                             after a cancelled turn that
                                             never produced an AI reply)
    [AIMessage(tool_calls=..., content="")] -> NOT first turn (tool-only
                                             AI turns still count as a reply)

Once the agent has replied at least once, the checkpointer carries the
injected SystemMessage forward across turns automatically, so re-injecting
would just duplicate it. Re-sending `custom_instructions` on an already-
established thread is logged and silently ignored.

The injected SystemMessage is wrapped in
`<custom_instructions>...</custom_instructions>` XML tags so the agent can
clearly distinguish user-supplied directives from its own system prompt.
The middleware writes back to `state["messages"]` — the only AgentState
key that LangChain's agent node serialises into the LLM context window
(see langchain.agents.middleware.types.AgentState; `jump_to` and
`structured_response` are control/output, not prompt input).

Internal deerflow imports: NONE.
External deps: langchain, langchain_core, langgraph.

──────────────────────────────────────────────────────────────────────────
Original module docstring follows:

Middleware for thread-scoped user-supplied custom instructions.

Captures ``custom_instructions`` from the runtime config on the very first turn
of a thread and persists them as a ``SystemMessage`` prepended to
``state.messages``. The LangGraph checkpointer carries the message forward
automatically, so on subsequent turns the model continues to see the
instructions without the client needing to re-send them.

If the client re-sends ``custom_instructions`` on a thread that already has
prior turns, the value is logged and silently ignored — the original
instructions stay in effect.
"""

import logging
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import SystemMessage
from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)


_TAG_OPEN = "<custom_instructions>"
_TAG_CLOSE = "</custom_instructions>"


class CustomInstructionsMiddleware(AgentMiddleware[AgentState]):
    """Inject user-supplied custom instructions on the first turn of a thread."""

    def _read_incoming(self, runtime: Runtime) -> str | None:
        """Read ``custom_instructions`` from runtime context, falling back to RunnableConfig."""
        ctx = getattr(runtime, "context", None)
        if isinstance(ctx, dict):
            value = ctx.get("custom_instructions")
            if isinstance(value, str) and value.strip():
                return value

        try:
            from langgraph.config import get_config

            value = get_config().get("configurable", {}).get("custom_instructions")
        except RuntimeError:
            # get_config() raises outside a runnable context (e.g. unit tests)
            value = None

        if isinstance(value, str) and value.strip():
            return value
        return None

    def _thread_id(self, runtime: Runtime) -> str | None:
        ctx = getattr(runtime, "context", None)
        if isinstance(ctx, dict) and ctx.get("thread_id"):
            return ctx["thread_id"]
        try:
            from langgraph.config import get_config

            return get_config().get("configurable", {}).get("thread_id")
        except RuntimeError:
            return None

    @override
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict | None:
        messages = list(state.get("messages", []))
        # First turn = the thread has not yet produced any AI responses.
        is_first_turn = not any(getattr(m, "type", None) == "ai" for m in messages)

        incoming = self._read_incoming(runtime)

        if not is_first_turn:
            if incoming is not None:
                logger.warning(
                    "custom_instructions ignored on existing thread (thread_id=%s); "
                    "instructions can only be set when starting a new conversation.",
                    self._thread_id(runtime),
                )
            return None

        if incoming is None:
            return None

        system_msg = SystemMessage(content=f"{_TAG_OPEN}\n{incoming.strip()}\n{_TAG_CLOSE}")
        return {"messages": [system_msg, *messages]}
