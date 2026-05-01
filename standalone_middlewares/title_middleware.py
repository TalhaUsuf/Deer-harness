"""
TitleMiddleware — auto-generates a concise thread title after the first
complete user→assistant exchange, then stops.

Hook
----
`after_model` / `aafter_model` — runs after every model response. Bails
early unless:
    1. `state.title` is empty,
    2. `_should_generate_title()` says yes (typically: at least 1 user
       message + 1 final assistant message present, no tool calls pending,
       config enabled).

If eligible, builds a small prompt from the first user/assistant exchange,
calls `create_chat_model(config.model_name)`, parses + truncates the
response, and writes the title to `state.title`.

Robustness
----------
- Strips `<think>...</think>` blocks (reasoning models like DeepSeek).
- Falls back to a truncated user message if the LLM call raises (this is
  the path used in the standalone copy because `_internal/models_factory`
  is a stub — see below).

Internal deerflow imports (rewritten)
-------------------------------------
    deerflow.config.title_config.get_title_config
        → ._internal.title_config.get_title_config
    deerflow.models.create_chat_model
        → ._internal.models_factory.create_chat_model  (STUB — raises;
          the middleware catches and uses the truncation fallback)

External deps: langchain, langgraph.
"""

import logging
import re
from typing import NotRequired, override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

# Original imports (rewritten for standalone build):
#   from deerflow.config.title_config import get_title_config
#   from deerflow.models import create_chat_model
from ._internal.title_config import get_title_config
from ._internal.models_factory import create_chat_model  # STUB; see _internal/models_factory.py

logger = logging.getLogger(__name__)


class TitleMiddlewareState(AgentState):
    """Compatible with the `ThreadState` schema."""

    title: NotRequired[str | None]


class TitleMiddleware(AgentMiddleware[TitleMiddlewareState]):
    """Automatically generate a title for the thread after the first user message."""

    state_schema = TitleMiddlewareState

    def _normalize_content(self, content: object) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = [self._normalize_content(item) for item in content]
            return "\n".join(part for part in parts if part)

        if isinstance(content, dict):
            text_value = content.get("text")
            if isinstance(text_value, str):
                return text_value

            nested_content = content.get("content")
            if nested_content is not None:
                return self._normalize_content(nested_content)

        return ""

    def _should_generate_title(self, state: TitleMiddlewareState) -> bool:
        """Check if we should generate a title for this thread."""
        config = get_title_config()
        if not config.enabled:
            return False

        # Check if thread already has a title in state
        if state.get("title"):
            return False

        # Check if this is the first turn (has at least one user message and one assistant response)
        messages = state.get("messages", [])
        if len(messages) < 2:
            return False

        # Count user and assistant messages
        user_messages = [m for m in messages if m.type == "human"]
        assistant_messages = [m for m in messages if m.type == "ai"]

        # Generate title after first complete exchange
        return len(user_messages) == 1 and len(assistant_messages) >= 1

    def _build_title_prompt(self, state: TitleMiddlewareState) -> tuple[str, str]:
        """Extract user/assistant messages and build the title prompt.

        Returns (prompt_string, user_msg) so callers can use user_msg as fallback.
        """
        config = get_title_config()
        messages = state.get("messages", [])

        user_msg_content = next((m.content for m in messages if m.type == "human"), "")
        assistant_msg_content = next((m.content for m in messages if m.type == "ai"), "")

        user_msg = self._normalize_content(user_msg_content)
        assistant_msg = self._strip_think_tags(self._normalize_content(assistant_msg_content))

        prompt = config.prompt_template.format(
            max_words=config.max_words,
            user_msg=user_msg[:500],
            assistant_msg=assistant_msg[:500],
        )
        return prompt, user_msg

    def _strip_think_tags(self, text: str) -> str:
        """Remove <think>...</think> blocks emitted by reasoning models (e.g. minimax, DeepSeek-R1)."""
        return re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()

    def _parse_title(self, content: object) -> str:
        """Normalize model output into a clean title string."""
        config = get_title_config()
        title_content = self._normalize_content(content)
        title_content = self._strip_think_tags(title_content)
        title = title_content.strip().strip('"').strip("'")
        return title[: config.max_chars] if len(title) > config.max_chars else title

    def _fallback_title(self, user_msg: str) -> str:
        config = get_title_config()
        fallback_chars = min(config.max_chars, 50)
        if len(user_msg) > fallback_chars:
            return user_msg[:fallback_chars].rstrip() + "..."
        return user_msg if user_msg else "New Conversation"

    def _generate_title_result(self, state: TitleMiddlewareState) -> dict | None:
        """Generate a local fallback title without blocking on an LLM call."""
        if not self._should_generate_title(state):
            return None

        _, user_msg = self._build_title_prompt(state)
        return {"title": self._fallback_title(user_msg)}

    async def _agenerate_title_result(self, state: TitleMiddlewareState) -> dict | None:
        """Generate a title asynchronously and fall back locally on failure."""
        if not self._should_generate_title(state):
            return None

        config = get_title_config()
        prompt, user_msg = self._build_title_prompt(state)

        try:
            if config.model_name:
                model = create_chat_model(name=config.model_name, thinking_enabled=False)
            else:
                model = create_chat_model(thinking_enabled=False)
            response = await model.ainvoke(prompt)
            title = self._parse_title(response.content)
            if title:
                return {"title": title}
        except Exception:
            logger.debug("Failed to generate async title; falling back to local title", exc_info=True)
        return {"title": self._fallback_title(user_msg)}

    @override
    def after_model(self, state: TitleMiddlewareState, runtime: Runtime) -> dict | None:
        return self._generate_title_result(state)

    @override
    async def aafter_model(self, state: TitleMiddlewareState, runtime: Runtime) -> dict | None:
        return await self._agenerate_title_result(state)
