"""
firecrawl.py — Firecrawl ``web_search`` + ``web_fetch`` tools.

Provider summary
----------------
- ``web_search_tool(query)`` → JSON list of ``{title, url, snippet}``
  built from ``client.search(query, limit=...).web``.
- ``web_fetch_tool(url)``    → ``# {title}\\n\\n{markdown[:4096]}`` via
  ``client.scrape(url, formats=["markdown"])``.

Configuration
-------------
- ``ToolConfig(name="web_search", api_key="$FIRECRAWL_API_KEY", max_results=5)``.
- ``ToolConfig(name="web_fetch",  api_key="$FIRECRAWL_API_KEY")``.

External pip dep: ``firecrawl-py>=1.15.0``.

Internal-import rewrites
------------------------
Original                                | Rewritten
----------------------------------------|------------------------------------
from deerflow.config import get_app_config | from .._internal.app_config import get_app_config

Original source
---------------
backend/packages/harness/deerflow/community/firecrawl/tools.py
"""

import json

from firecrawl import FirecrawlApp
from langchain.tools import tool

from .._internal.app_config import get_app_config


def _get_firecrawl_client(tool_name: str = "web_search") -> FirecrawlApp:
    config = get_app_config().get_tool_config(tool_name)
    api_key = None
    if config is not None and "api_key" in config.model_extra:
        api_key = config.model_extra.get("api_key")
    return FirecrawlApp(api_key=api_key)  # type: ignore[arg-type]


@tool("web_search", parse_docstring=True)
def web_search_tool(query: str) -> str:
    """Search the web.

    Args:
        query: The query to search for.
    """
    try:
        config = get_app_config().get_tool_config("web_search")
        max_results = 5
        if config is not None:
            max_results = config.model_extra.get("max_results", max_results)

        client = _get_firecrawl_client("web_search")
        result = client.search(query, limit=max_results)

        web_results = result.web or []
        normalized_results = [
            {
                "title": getattr(item, "title", "") or "",
                "url": getattr(item, "url", "") or "",
                "snippet": getattr(item, "description", "") or "",
            }
            for item in web_results
        ]
        return json.dumps(normalized_results, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"


@tool("web_fetch", parse_docstring=True)
def web_fetch_tool(url: str) -> str:
    """Fetch the contents of a web page at a given URL.
    Only fetch EXACT URLs that have been provided directly by the user or have been returned in results from the web_search and web_fetch tools.
    This tool can NOT access content that requires authentication, such as private Google Docs or pages behind login walls.
    Do NOT add www. to URLs that do NOT have them.
    URLs must include the schema: https://example.com is a valid URL while example.com is an invalid URL.

    Args:
        url: The URL to fetch the contents of.
    """
    try:
        client = _get_firecrawl_client("web_fetch")
        result = client.scrape(url, formats=["markdown"])

        markdown_content = result.markdown or ""
        metadata = result.metadata
        title = metadata.title if metadata and metadata.title else "Untitled"

        if not markdown_content:
            return "Error: No content found"
    except Exception as e:
        return f"Error: {str(e)}"

    return f"# {title}\n\n{markdown_content[:4096]}"
