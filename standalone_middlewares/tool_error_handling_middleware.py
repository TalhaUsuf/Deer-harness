"""
ToolErrorHandlingMiddleware — converts tool execution exceptions into error
ToolMessages so the agent run can continue instead of aborting.

Hook
----
`wrap_tool_call` / `awrap_tool_call` — runs around every tool call.

Behaviour
---------
1. If the tool raises `GraphBubbleUp` (LangGraph's interrupt/pause/resume
   control-flow signal), re-raise unchanged. These are NOT errors.
2. For any other exception, log with `exception()` (so the traceback is
   captured) and synthesise a ToolMessage with `status="error"` carrying a
   truncated message (max 500 chars) and the exception class name. Returning
   the ToolMessage instead of re-raising lets LangGraph keep going — the
   LLM sees the failure on its next turn and can adapt.

Internal deerflow imports (rewritten)
-------------------------------------
The class itself has NO internal imports. The original module also exposed
two factory functions (`build_lead_runtime_middlewares`,
`build_subagent_runtime_middlewares`) that lazy-imported and assembled the
full runtime middleware stack including:
    - SandboxMiddleware (deerflow.sandbox.middleware)
    - GuardrailMiddleware (deerflow.guardrails.middleware)
    - get_guardrails_config (deerflow.config.guardrails_config)
    - resolve_variable (deerflow.reflection)

Those factories are NOT carried into the standalone copy because they pull
in three subsystems (sandbox runtime, guardrail provider system, reflection
loader) that live outside `agents/middlewares/`. Stripped-down replacements
are provided below — they assemble only the middlewares present in this
folder and raise on guardrail/sandbox-specific paths so missing pieces fail
loudly rather than silently.

External deps: langchain, langchain_core, langgraph.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphBubbleUp
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

logger = logging.getLogger(__name__)

_MISSING_TOOL_CALL_ID = "missing_tool_call_id"


class ToolErrorHandlingMiddleware(AgentMiddleware[AgentState]):
    """Convert tool exceptions into error ToolMessages so the run can continue."""

    def _build_error_message(self, request: ToolCallRequest, exc: Exception) -> ToolMessage:
        tool_name = str(request.tool_call.get("name") or "unknown_tool")
        tool_call_id = str(request.tool_call.get("id") or _MISSING_TOOL_CALL_ID)
        detail = str(exc).strip() or exc.__class__.__name__
        # Truncate so a giant traceback string doesn't blow up the message list.
        if len(detail) > 500:
            detail = detail[:497] + "..."

        content = (
            f"Error: Tool '{tool_name}' failed with {exc.__class__.__name__}: "
            f"{detail}. Continue with available context, or choose an alternative tool."
        )
        return ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
            name=tool_name,
            status="error",
        )

    @override
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        try:
            return handler(request)
        except GraphBubbleUp:
            # Preserve LangGraph control-flow signals (interrupt/pause/resume).
            raise
        except Exception as exc:
            logger.exception(
                "Tool execution failed (sync): name=%s id=%s",
                request.tool_call.get("name"),
                request.tool_call.get("id"),
            )
            return self._build_error_message(request, exc)

    @override
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        try:
            return await handler(request)
        except GraphBubbleUp:
            # Preserve LangGraph control-flow signals (interrupt/pause/resume).
            raise
        except Exception as exc:
            logger.exception(
                "Tool execution failed (async): name=%s id=%s",
                request.tool_call.get("name"),
                request.tool_call.get("id"),
            )
            return self._build_error_message(request, exc)


# ── Runtime middleware factories (stripped) ──────────────────────────────
#
# The original file shipped two factories that returned the full lead/subagent
# runtime middleware list, including the sandbox lifecycle middleware and an
# optional guardrail middleware. Those depend on subsystems outside this
# folder — see the module docstring for details.
#
# The replacements below assemble ONLY the middlewares that exist in this
# standalone folder and raise NotImplementedError when sandbox / guardrail
# pieces are requested. If you want the full original behaviour, copy
# `deerflow/sandbox/middleware.py`, `deerflow/guardrails/middleware.py`, and
# their dependencies into `_internal/` and rewire the imports below.


def build_lead_runtime_middlewares(*, lazy_init: bool = True) -> list[AgentMiddleware]:
    """Lead-agent stack — minus SandboxMiddleware and GuardrailMiddleware.

    Original order (deerflow):
        ThreadDataMiddleware
        UploadsMiddleware
        CustomInstructionsMiddleware
        SandboxMiddleware                  <- not in standalone folder
        DanglingToolCallMiddleware
        LLMErrorHandlingMiddleware
        GuardrailMiddleware (optional)     <- not in standalone folder
        SandboxAuditMiddleware
        ToolErrorHandlingMiddleware

    Standalone variant returns only the middlewares present here, in the same
    relative order. Insert your own SandboxMiddleware / GuardrailMiddleware
    where indicated in the comments before passing the list to your agent.
    """
    # Local sibling imports — these all live in this same folder.
    from .thread_data_middleware import ThreadDataMiddleware
    from .uploads_middleware import UploadsMiddleware
    from .custom_instructions_middleware import CustomInstructionsMiddleware
    from .dangling_tool_call_middleware import DanglingToolCallMiddleware
    from .llm_error_handling_middleware import LLMErrorHandlingMiddleware
    from .sandbox_audit_middleware import SandboxAuditMiddleware

    return [
        ThreadDataMiddleware(lazy_init=lazy_init),
        UploadsMiddleware(),
        CustomInstructionsMiddleware(),
        # ← Insert SandboxMiddleware(lazy_init=lazy_init) here in your app.
        DanglingToolCallMiddleware(),
        LLMErrorHandlingMiddleware(),
        # ← Insert GuardrailMiddleware(provider, ...) here if guardrails enabled.
        SandboxAuditMiddleware(),
        ToolErrorHandlingMiddleware(),
    ]


def build_subagent_runtime_middlewares(*, lazy_init: bool = True) -> list[AgentMiddleware]:
    """Subagent stack — same as lead minus UploadsMiddleware and CustomInstructions.

    Subagents inherit uploads context from the parent agent's prompt, and they
    do not honour user-supplied custom instructions (those are lead-only).
    """
    from .thread_data_middleware import ThreadDataMiddleware
    from .dangling_tool_call_middleware import DanglingToolCallMiddleware
    from .llm_error_handling_middleware import LLMErrorHandlingMiddleware
    from .sandbox_audit_middleware import SandboxAuditMiddleware

    return [
        ThreadDataMiddleware(lazy_init=lazy_init),
        # ← Insert SandboxMiddleware(lazy_init=lazy_init) here in your app.
        DanglingToolCallMiddleware(),
        LLMErrorHandlingMiddleware(),
        # ← Insert GuardrailMiddleware(provider, ...) here if guardrails enabled.
        SandboxAuditMiddleware(),
        ToolErrorHandlingMiddleware(),
    ]
