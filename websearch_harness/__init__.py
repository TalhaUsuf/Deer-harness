"""
websearch_harness — Standalone web-search subsystem extracted from DeerFlow.

Layout
------
- providers/         — one module per search/fetch provider (langchain @tool)
- middleware/        — DeferredToolFilterMiddleware (web-search-related)
- _internal/         — config stubs, readability, deferred registry, helpers

Drop this folder into any project that has a working
``langchain >= 1.0`` install and the relevant provider pip package
(see README.md). Nothing in this package imports from ``deerflow.*`` —
all deerflow internals have been inlined or stubbed under ``_internal/``.

Public API
----------
Each provider exports its raw langchain tool under its original name
(``web_search_tool`` / ``web_fetch_tool`` / ``image_search_tool``). To
distinguish providers when several are imported together, the top-level
package re-exports them under provider-prefixed aliases:

    from websearch_harness import (
        ddg_web_search_tool,
        tavily_web_search_tool, tavily_web_fetch_tool,
        exa_web_search_tool, exa_web_fetch_tool,
        firecrawl_web_search_tool, firecrawl_web_fetch_tool,
        jina_web_fetch_tool,
        infoquest_web_search_tool, infoquest_web_fetch_tool,
        infoquest_image_search_tool,
        ddg_image_search_tool,
    )

Configuration
-------------
Either set provider env vars (TAVILY_API_KEY, EXA_API_KEY, FIRECRAWL_API_KEY,
JINA_API_KEY, INFOQUEST_API_KEY) or call:

    from websearch_harness import set_tool_configs, ToolConfig
    set_tool_configs([
        ToolConfig(name="web_search", group="search",
                   use="websearch_harness.providers.tavily:web_search_tool",
                   api_key="$TAVILY_API_KEY", max_results=5),
    ])

Deferred-tool flow (optional)
-----------------------------
    from websearch_harness import (
        DeferredToolRegistry, set_deferred_registry, tool_search,
        DeferredToolFilterMiddleware,
    )

Each provider import below is wrapped in try/except so that missing
provider pip packages (tavily, exa, firecrawl, ddgs, requests, httpx)
do NOT break ``import websearch_harness`` for users who only want one
provider.
"""

from __future__ import annotations

import logging as _logging

from ._internal.app_config import (
    get_app_config,
    reset_app_config,
    set_tool_configs,
)
from ._internal.deferred_registry import (
    DeferredToolEntry,
    DeferredToolRegistry,
    get_deferred_registry,
    reset_deferred_registry,
    set_deferred_registry,
    tool_search,
)
from ._internal.tool_config import ToolConfig, ToolGroupConfig
from ._internal.tool_loader import get_available_tools
from ._internal.tool_search_config import ToolSearchConfig, get_tool_search_config
from .middleware import DeferredToolFilterMiddleware

_logger = _logging.getLogger(__name__)


# Provider aliases — wrapped so missing pip pkgs don't break package import.
def _safe_import(import_path: str, attr: str):
    """Try to import ``attr`` from ``import_path``; return None on failure.

    Logs a debug-level note so users see why a provider is unavailable.
    """
    try:
        module = __import__(import_path, fromlist=[attr])
        return getattr(module, attr)
    except Exception as exc:  # noqa: BLE001 — provider deps are optional
        _logger.debug("websearch_harness: provider %s.%s unavailable (%s)", import_path, attr, exc)
        return None


ddg_web_search_tool = _safe_import("websearch_harness.providers.ddg_search", "web_search_tool")

tavily_web_search_tool = _safe_import("websearch_harness.providers.tavily", "web_search_tool")
tavily_web_fetch_tool = _safe_import("websearch_harness.providers.tavily", "web_fetch_tool")

exa_web_search_tool = _safe_import("websearch_harness.providers.exa", "web_search_tool")
exa_web_fetch_tool = _safe_import("websearch_harness.providers.exa", "web_fetch_tool")

firecrawl_web_search_tool = _safe_import("websearch_harness.providers.firecrawl", "web_search_tool")
firecrawl_web_fetch_tool = _safe_import("websearch_harness.providers.firecrawl", "web_fetch_tool")

jina_web_fetch_tool = _safe_import("websearch_harness.providers.jina_ai", "web_fetch_tool")

infoquest_web_search_tool = _safe_import("websearch_harness.providers.infoquest", "web_search_tool")
infoquest_web_fetch_tool = _safe_import("websearch_harness.providers.infoquest", "web_fetch_tool")
infoquest_image_search_tool = _safe_import("websearch_harness.providers.infoquest", "image_search_tool")

ddg_image_search_tool = _safe_import("websearch_harness.providers.image_search_ddg", "image_search_tool")


__all__ = [
    # Config / loader
    "ToolConfig",
    "ToolGroupConfig",
    "ToolSearchConfig",
    "get_app_config",
    "set_tool_configs",
    "reset_app_config",
    "get_tool_search_config",
    "get_available_tools",
    # Deferred-tool registry
    "DeferredToolEntry",
    "DeferredToolRegistry",
    "get_deferred_registry",
    "set_deferred_registry",
    "reset_deferred_registry",
    "tool_search",
    # Middleware
    "DeferredToolFilterMiddleware",
    # Provider tools
    "ddg_web_search_tool",
    "tavily_web_search_tool",
    "tavily_web_fetch_tool",
    "exa_web_search_tool",
    "exa_web_fetch_tool",
    "firecrawl_web_search_tool",
    "firecrawl_web_fetch_tool",
    "jina_web_fetch_tool",
    "infoquest_web_search_tool",
    "infoquest_web_fetch_tool",
    "infoquest_image_search_tool",
    "ddg_image_search_tool",
]
