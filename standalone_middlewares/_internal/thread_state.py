"""
thread_state.py — VERBATIM copy of `deerflow.agents.thread_state`.

This module defines the `ThreadState` schema that several middlewares extend
(SandboxAuditMiddleware, ViewImageMiddleware, ThreadDataMiddleware). It is a
LangChain `AgentState` subclass with a handful of NotRequired keys plus two
custom reducers (`merge_artifacts`, `merge_viewed_images`) that LangGraph uses
to combine state updates from concurrent middleware steps.

Why the reducers matter
-----------------------
LangGraph applies state updates by calling each `Annotated[..., reducer]`
function with `(existing, new)` — without these reducers, list/dict updates
from middleware would simply overwrite each other. `merge_artifacts` keeps
the union (deduplicated, order-preserving), and `merge_viewed_images` merges
dicts but treats an empty `{}` as an explicit "clear" signal so a middleware
can wipe the slot after consuming it.

External dependencies: `langchain.agents.AgentState` only.
"""

from typing import Annotated, NotRequired, TypedDict

from langchain.agents import AgentState


# Sandbox handle stored in state by SandboxMiddleware (the upstream middleware
# that allocates an isolated execution sandbox per-thread). The id is later
# read by SandboxAuditMiddleware and the bash/file tools.
class SandboxState(TypedDict):
    sandbox_id: NotRequired[str | None]


# Per-thread directory paths injected by ThreadDataMiddleware. These are the
# host-side absolute paths corresponding to the sandbox's virtual `/mnt/user-data`.
class ThreadDataState(TypedDict):
    workspace_path: NotRequired[str | None]
    uploads_path: NotRequired[str | None]
    outputs_path: NotRequired[str | None]


# Image data injected by view_image tool calls; consumed by ViewImageMiddleware
# which converts entries into multimodal HumanMessages before the LLM call.
class ViewedImageData(TypedDict):
    base64: str
    mime_type: str


def merge_artifacts(existing: list[str] | None, new: list[str] | None) -> list[str]:
    """Reducer for `artifacts` — order-preserving deduplicated union.

    `dict.fromkeys` is the standard Python idiom for stable-order dedup.
    """
    if existing is None:
        return new or []
    if new is None:
        return existing
    return list(dict.fromkeys(existing + new))


def merge_viewed_images(
    existing: dict[str, ViewedImageData] | None,
    new: dict[str, ViewedImageData] | None,
) -> dict[str, ViewedImageData]:
    """Reducer for `viewed_images` — merges, but empty dict means CLEAR.

    The clear-via-empty-dict semantics let ViewImageMiddleware reset the slot
    after rendering images into the message stream, preventing the same image
    from being re-injected on every subsequent model call.
    """
    if existing is None:
        return new or {}
    if new is None:
        return existing
    if len(new) == 0:  # explicit clear sentinel
        return {}
    return {**existing, **new}


class ThreadState(AgentState):
    """The full per-thread state schema used by the lead agent.

    Only `artifacts` and `viewed_images` use Annotated reducers; the rest are
    plain NotRequired keys, meaning later updates simply replace earlier ones.
    """

    sandbox: NotRequired[SandboxState | None]
    thread_data: NotRequired[ThreadDataState | None]
    title: NotRequired[str | None]
    artifacts: Annotated[list[str], merge_artifacts]
    todos: NotRequired[list | None]
    uploaded_files: NotRequired[list[dict] | None]
    viewed_images: Annotated[dict[str, ViewedImageData], merge_viewed_images]
