"""
models_factory.py — STUB for `deerflow.models.create_chat_model`.

The original factory dynamically resolves a chat-model class from `config.yaml`
via `deerflow.reflection.resolve_class`, attaches tracing callbacks via
`deerflow.tracing.build_tracing_callbacks`, and supports vLLM-style thinking
toggles for Qwen reasoning models. Re-implementing all of that would pull
the entire deerflow runtime in.

This stub raises NotImplementedError so that any code path that actually
needs an LLM fails loudly. TitleMiddleware (the only consumer in the 17
middlewares) catches the exception and falls back to a truncated user-message
title — so the middleware still works end-to-end without an LLM, just with a
simpler title.

To enable real LLM-driven titles, replace `create_chat_model` here with a
function that returns a `langchain_core.language_models.BaseChatModel`
instance configured for your environment.
"""

from typing import Any


def create_chat_model(name: str | None = None, thinking_enabled: bool = False) -> Any:
    """Stub — raises so callers fall back to non-LLM logic.

    Args:
        name: Model name from config; ignored by stub.
        thinking_enabled: Per-call thinking toggle; ignored by stub.

    Raises:
        NotImplementedError: always.
    """
    raise NotImplementedError(
        "standalone_middlewares._internal.models_factory.create_chat_model is a stub. "
        "Replace it with a function that returns a BaseChatModel configured for your env. "
        "TitleMiddleware will fall back to a simple truncation-based title until you do."
    )
