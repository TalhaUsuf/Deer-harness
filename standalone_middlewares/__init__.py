"""
standalone_middlewares — copy-pasteable rewrite of the 17 LangGraph middlewares
that live in `deerflow.agents.middlewares`.

Goal
----
Drop this folder into ANY project that has the same external pip
dependencies (langchain, langgraph, langchain_core, pydantic) and the
middleware classes will import cleanly without needing the rest of the
deerflow codebase. Internal `deerflow.*` imports have been carried over
into the private `_internal/` subpackage; the middleware files have been
rewritten to import from there.

External deps (your `pyproject.toml` / `requirements.txt` must include)
-----------------------------------------------------------------------
    langchain >= 1.0          # AgentMiddleware, AgentState, builtin middlewares
    langchain-core >= 0.4     # message types
    langgraph >= 1.0          # Runtime, Command, prebuilt.tool_node
    pydantic >= 2.0           # config models
    python-dotenv             # only if you call _internal.app_config setters
                              # that read .env (the stub here does not)

Stubs you may want to wire up
-----------------------------
A few helpers in `_internal/` are STUBS — they preserve the public surface
the middlewares import, but with placeholder behaviour:

    _internal/models_factory.py
        `create_chat_model()` raises NotImplementedError. TitleMiddleware
        catches it and falls back to a truncation-based title, so the
        middleware works without an LLM. Replace with your own factory if
        you want LLM-driven titles.

    _internal/memory_queue.py — `_StubMemoryUpdater`
        Logs but doesn't persist. Replace with your own
        `update_memory(messages, thread_id, agent_name, ...)` -> bool
        implementation if you want the memory system to actually do work.

    _internal/app_config.py
        Minimal AppConfig with only `circuit_breaker`. Wire up your own
        config loading if you need more fields exposed.

    tool_error_handling_middleware.build_{lead,subagent}_runtime_middlewares
        Return a stripped middleware stack (no SandboxMiddleware,
        no GuardrailMiddleware) — those subsystems live outside
        `agents/middlewares/` in the original codebase. Comments in the
        function bodies show where to splice them in.

The 17 middleware classes (re-exported below)
---------------------------------------------
"""

# Re-export every middleware class so callers can simply do:
#     from standalone_middlewares import LLMErrorHandlingMiddleware

from .clarification_middleware import ClarificationMiddleware
from .custom_instructions_middleware import CustomInstructionsMiddleware
from .dangling_tool_call_middleware import DanglingToolCallMiddleware
from .deferred_tool_filter_middleware import DeferredToolFilterMiddleware
from .llm_error_handling_middleware import LLMErrorHandlingMiddleware
from .loop_detection_middleware import LoopDetectionMiddleware
from .memory_middleware import MemoryMiddleware
from .sandbox_audit_middleware import SandboxAuditMiddleware
from .subagent_limit_middleware import SubagentLimitMiddleware
from .summarization_middleware import DeerFlowSummarizationMiddleware
from .thread_data_middleware import ThreadDataMiddleware
from .title_middleware import TitleMiddleware
from .todo_middleware import TodoMiddleware
from .token_usage_middleware import TokenUsageMiddleware
from .tool_error_handling_middleware import (
    ToolErrorHandlingMiddleware,
    build_lead_runtime_middlewares,
    build_subagent_runtime_middlewares,
)
from .uploads_middleware import UploadsMiddleware
from .view_image_middleware import ViewImageMiddleware

__all__ = [
    "ClarificationMiddleware",
    "CustomInstructionsMiddleware",
    "DanglingToolCallMiddleware",
    "DeferredToolFilterMiddleware",
    "DeerFlowSummarizationMiddleware",
    "TodoMiddleware",
    "LLMErrorHandlingMiddleware",
    "LoopDetectionMiddleware",
    "MemoryMiddleware",
    "SandboxAuditMiddleware",
    "SubagentLimitMiddleware",
    "ThreadDataMiddleware",
    "TitleMiddleware",
    "TokenUsageMiddleware",
    "ToolErrorHandlingMiddleware",
    "UploadsMiddleware",
    "ViewImageMiddleware",
    "build_lead_runtime_middlewares",
    "build_subagent_runtime_middlewares",
]
