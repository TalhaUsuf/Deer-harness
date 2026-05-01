"""
tool_search_registry.py — Trimmed copy of `deerflow.tools.builtins.tool_search`.

Carried over: `DeferredToolRegistry`, `get_deferred_registry()`,
`set_deferred_registry()`, `reset_deferred_registry()`.

Dropped: the `@tool tool_search(query)` LangChain tool function, because it
is not referenced by any middleware — only the registry accessor is needed
by `DeferredToolFilterMiddleware._filter_tools()`.

How the system fits together
----------------------------
1. At agent setup, deferred tools are registered with the registry stored
   in a ContextVar.
2. The system prompt advertises their NAMES only (no schema), saving tokens.
3. `DeferredToolFilterMiddleware` strips deferred tool definitions from
   `bind_tools()` so the LLM cannot call them blind.
4. The user-facing `tool_search` tool (NOT carried into this folder) lets
   the LLM look up a tool's full schema by name; once promoted, the
   middleware stops filtering and the LLM can call it.

External deps: `langchain.tools.BaseTool`, stdlib (`contextvars`, `re`,
`dataclasses`).
"""

import contextvars
import logging
import re
from dataclasses import dataclass

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

MAX_RESULTS = 5  # Max tools returned per search


@dataclass
class DeferredToolEntry:
    """Lightweight metadata for one deferred tool — full BaseTool kept for promotion."""

    name: str
    description: str
    tool: BaseTool


class DeferredToolRegistry:
    """Registry of deferred tools, searchable by regex / select: / +keyword forms."""

    def __init__(self):
        self._entries: list[DeferredToolEntry] = []

    def register(self, tool: BaseTool) -> None:
        self._entries.append(
            DeferredToolEntry(
                name=tool.name,
                description=tool.description or "",
                tool=tool,
            )
        )

    def promote(self, names: set[str]) -> None:
        """Remove tools from the deferred set so they pass through the filter again."""
        if not names:
            return
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.name not in names]
        promoted = before - len(self._entries)
        if promoted:
            logger.debug(
                f"Promoted {promoted} tool(s) from deferred to active: {names}"
            )

    def search(self, query: str) -> list[BaseTool]:
        """Three query forms aligned with Claude Code:

        - `"select:name1,name2"` — exact-name fetch
        - `"+keyword rest"`      — name must contain `keyword`, rank by `rest`
        - `"keyword query"`      — regex match against name + description
        """
        if query.startswith("select:"):
            names = {n.strip() for n in query[7:].split(",")}
            return [e.tool for e in self._entries if e.name in names][:MAX_RESULTS]

        if query.startswith("+"):
            parts = query[1:].split(None, 1)
            required = parts[0].lower()
            candidates = [e for e in self._entries if required in e.name.lower()]
            if len(parts) > 1:
                candidates.sort(
                    key=lambda e: _regex_score(parts[1], e), reverse=True
                )
            return [e.tool for e in candidates][:MAX_RESULTS]

        # General regex search; fall back to literal match on bad regex input.
        try:
            regex = re.compile(query, re.IGNORECASE)
        except re.error:
            regex = re.compile(re.escape(query), re.IGNORECASE)

        scored = []
        for entry in self._entries:
            searchable = f"{entry.name} {entry.description}"
            if regex.search(searchable):
                # Name match outweighs description match — score 2 vs 1.
                score = 2 if regex.search(entry.name) else 1
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry.tool for _, entry in scored][:MAX_RESULTS]

    @property
    def entries(self) -> list[DeferredToolEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


def _regex_score(pattern: str, entry: DeferredToolEntry) -> int:
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        regex = re.compile(re.escape(pattern), re.IGNORECASE)
    return len(regex.findall(f"{entry.name} {entry.description}"))


# ── Per-request registry (ContextVar) ─────────────────────────────────────
#
# A ContextVar (not a module global) so concurrent agent runs do not clobber
# each other's registry. Each LangGraph run executes inside its own asyncio
# context, and `loop.run_in_executor` propagates the active context to worker
# threads — so sync tools also see the right registry value.

_registry_var: contextvars.ContextVar[DeferredToolRegistry | None] = (
    contextvars.ContextVar("deferred_tool_registry", default=None)
)


def get_deferred_registry() -> DeferredToolRegistry | None:
    """Return the registry for the current async context, or None if unset."""
    return _registry_var.get()


def set_deferred_registry(registry: DeferredToolRegistry) -> None:
    _registry_var.set(registry)


def reset_deferred_registry() -> None:
    _registry_var.set(None)
