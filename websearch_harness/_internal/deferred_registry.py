"""
deferred_registry.py — Verbatim copy of `deerflow.tools.builtins.tool_search`.

What it provides
----------------
1. `DeferredToolRegistry` — keeps a list of `BaseTool`s whose schemas are
   intentionally hidden from the LLM until the LLM looks them up. This is
   how DeerFlow's "tool_search" deferral pattern saves context tokens
   when there are many community tools (web_search providers, MCP tools,
   …).
2. `tool_search(query)` — the LangChain `@tool`-decorated function the
   LLM calls to fetch the full OpenAI-function schema for a deferred
   tool. Once a schema is fetched the tool is "promoted" out of the
   registry so subsequent `bind_tools()` passes include it.
3. `get_deferred_registry`, `set_deferred_registry`,
   `reset_deferred_registry` — ContextVar accessors. Per-async-context
   isolation prevents concurrent agent runs from clobbering each
   other's registry.

How this fits the web-search story
----------------------------------
When a harness wires up multiple search providers (ddg, tavily, exa,
firecrawl, jina, infoquest, image_search) the LLM doesn't necessarily
need every schema in its system prompt. With deferred-tool mode the
provider names alone are listed and the LLM calls `tool_search("web
search")` to fetch full schemas for the providers it actually wants to
use. `DeferredToolFilterMiddleware` (see `../middleware/`) is what
strips the schemas at `bind_tools()` time.

Original source
---------------
backend/packages/harness/deerflow/tools/builtins/tool_search.py

External deps
-------------
- langchain.tools.BaseTool
- langchain_core.tools.tool
- langchain_core.utils.function_calling.convert_to_openai_function
- stdlib (contextvars, json, logging, re, dataclasses)
"""

import contextvars
import json
import logging
import re
from dataclasses import dataclass

from langchain.tools import BaseTool
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function

logger = logging.getLogger(__name__)

MAX_RESULTS = 5  # Max tools returned per search


@dataclass
class DeferredToolEntry:
    """Lightweight metadata for a deferred tool (no full schema in context)."""

    name: str
    description: str
    tool: BaseTool


class DeferredToolRegistry:
    """Registry of deferred tools, searchable by regex pattern."""

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
        """Remove tools from the deferred registry so they pass through the filter.

        Called after tool_search returns a tool's schema — the LLM now knows
        the full definition, so the DeferredToolFilterMiddleware should stop
        stripping it from bind_tools on subsequent calls.
        """
        if not names:
            return
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.name not in names]
        promoted = before - len(self._entries)
        if promoted:
            logger.debug(f"Promoted {promoted} tool(s) from deferred to active: {names}")

    def search(self, query: str) -> list[BaseTool]:
        """Search deferred tools by regex pattern against name + description.

        Three query forms (aligned with Claude Code):
          - "select:name1,name2"  — exact name match
          - "+keyword rest"       — name must contain keyword, rank by rest
          - "keyword query"       — regex match against name + description
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
                    key=lambda e: _regex_score(parts[1], e),
                    reverse=True,
                )
            return [e.tool for e in candidates][:MAX_RESULTS]

        try:
            regex = re.compile(query, re.IGNORECASE)
        except re.error:
            regex = re.compile(re.escape(query), re.IGNORECASE)

        scored = []
        for entry in self._entries:
            searchable = f"{entry.name} {entry.description}"
            if regex.search(searchable):
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


# ── Per-request registry (ContextVar) ──
#
# A ContextVar (not a module global) so concurrent agent runs do not clobber
# each other's registry. Each LangGraph run executes inside its own asyncio
# context, and `loop.run_in_executor` propagates the active context to worker
# threads — so sync tools also see the right registry value.

_registry_var: contextvars.ContextVar[DeferredToolRegistry | None] = contextvars.ContextVar("deferred_tool_registry", default=None)


def get_deferred_registry() -> DeferredToolRegistry | None:
    return _registry_var.get()


def set_deferred_registry(registry: DeferredToolRegistry) -> None:
    _registry_var.set(registry)


def reset_deferred_registry() -> None:
    """Reset the deferred registry for the current async context."""
    _registry_var.set(None)


# ── Tool ──


@tool
def tool_search(query: str) -> str:
    """Fetches full schema definitions for deferred tools so they can be called.

    Deferred tools appear by name in <available-deferred-tools> in the system
    prompt. Until fetched, only the name is known — there is no parameter
    schema, so the tool cannot be invoked. This tool takes a query, matches
    it against the deferred tool list, and returns the matched tools' complete
    definitions. Once a tool's schema appears in that result, it is callable.

    Query forms:
      - "select:Read,Edit,Grep" — fetch these exact tools by name
      - "notebook jupyter" — keyword search, up to max_results best matches
      - "+slack send" — require "slack" in the name, rank by remaining terms

    Args:
        query: Query to find deferred tools. Use "select:<tool_name>" for
               direct selection, or keywords to search.

    Returns:
        Matched tool definitions as JSON array.
    """
    registry = get_deferred_registry()
    if not registry:
        return "No deferred tools available."

    matched_tools = registry.search(query)
    if not matched_tools:
        return f"No tools found matching: {query}"

    tool_defs = [convert_to_openai_function(t) for t in matched_tools[:MAX_RESULTS]]
    registry.promote({t.name for t in matched_tools[:MAX_RESULTS]})

    return json.dumps(tool_defs, indent=2, ensure_ascii=False)
