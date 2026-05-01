"""
ddg_search.py — DuckDuckGo `web_search` tool (no API key required).

Provider summary
----------------
Calls `ddgs.DDGS().text(query, ...)` and returns up to ``max_results``
hits as a JSON-encoded list of ``{title, url, content}`` dicts. Region
defaults to ``wt-wt`` (worldwide) and safesearch to ``moderate``.

Configuration
-------------
- Programmatic: register a ``ToolConfig(name="web_search", ..., max_results=N)``
  via ``websearch_harness._internal.app_config.set_tool_configs``.
- Otherwise the function-arg ``max_results`` (default 5) is used.

External pip dep: ``ddgs>=9.10.0`` (the ``ddgs`` package, not the older
``duckduckgo-search`` package).

Internal-import rewrites
------------------------
Original                                | Rewritten
----------------------------------------|------------------------------------
from deerflow.config import get_app_config | from .._internal.app_config import get_app_config

Original source
---------------
backend/packages/harness/deerflow/community/ddg_search/tools.py
"""

import json
import logging

from langchain.tools import tool

from .._internal.app_config import get_app_config

logger = logging.getLogger(__name__)


def _search_text(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
    safesearch: str = "moderate",
) -> list[dict]:
    """Execute text search using DuckDuckGo.

    Returns an empty list (and logs the error) on any failure so the
    tool wrapper can return a structured "no results" message instead
    of crashing the agent.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        logger.error("ddgs library not installed. Run: pip install ddgs")
        return []

    ddgs = DDGS(timeout=30)

    try:
        results = ddgs.text(
            query,
            region=region,
            safesearch=safesearch,
            max_results=max_results,
        )
        return list(results) if results else []

    except Exception as e:
        logger.error(f"Failed to search web: {e}")
        return []


@tool("web_search", parse_docstring=True)
def web_search_tool(
    query: str,
    max_results: int = 5,
) -> str:
    """Search the web for information. Use this tool to find current information, news, articles, and facts from the internet.

    Args:
        query: Search keywords describing what you want to find. Be specific for better results.
        max_results: Maximum number of results to return. Default is 5.
    """
    config = get_app_config().get_tool_config("web_search")

    if config is not None and "max_results" in config.model_extra:
        max_results = config.model_extra.get("max_results", max_results)

    results = _search_text(
        query=query,
        max_results=max_results,
    )

    if not results:
        return json.dumps({"error": "No results found", "query": query}, ensure_ascii=False)

    normalized_results = [
        {
            "title": r.get("title", ""),
            "url": r.get("href", r.get("link", "")),
            "content": r.get("body", r.get("snippet", "")),
        }
        for r in results
    ]

    output = {
        "query": query,
        "total_results": len(normalized_results),
        "results": normalized_results,
    }

    return json.dumps(output, indent=2, ensure_ascii=False)
