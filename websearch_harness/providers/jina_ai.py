"""
jina_ai.py — Jina Reader ``web_fetch`` tool (async).

Provider summary
----------------
``web_fetch_tool(url)`` (async) calls Jina's reader API at
``https://r.jina.ai/`` to obtain the full HTML of *url*, then runs the
result through the local ``ReadabilityExtractor`` and returns
``article.to_markdown()[:4096]``.

This is the most "polite" of the fetch providers — Jina handles
JS-rendered pages, anti-bot mitigations, and PDF extraction
server-side, returning clean HTML that Readability can parse without
fuss.

Authentication
--------------
``JINA_API_KEY`` is **optional** — without it Jina applies a free-tier
rate limit. With it the request adds an ``Authorization: Bearer …``
header and lifts the limit. The key is read from ``os.environ`` at
request time by ``JinaClient``, NOT through the AppConfig stub.

Configuration
-------------
- ``ToolConfig(name="web_fetch", timeout=10)`` — only the timeout is
  read from config. Default 10 seconds.

External pip dep: ``httpx>=0.28.0`` (no Jina SDK).

Internal-import rewrites
------------------------
Original                                                  | Rewritten
----------------------------------------------------------|---------------------------
from deerflow.community.jina_ai.jina_client import JinaClient | from .jina_ai_client import JinaClient
from deerflow.config import get_app_config                | from .._internal.app_config import get_app_config
from deerflow.utils.readability import ReadabilityExtractor | from .._internal.readability import ReadabilityExtractor

Original source
---------------
backend/packages/harness/deerflow/community/jina_ai/tools.py
backend/packages/harness/deerflow/community/jina_ai/jina_client.py
"""

import asyncio
import logging
import os

import httpx
from langchain.tools import tool

from .._internal.app_config import get_app_config
from .._internal.readability import ReadabilityExtractor

logger = logging.getLogger(__name__)

_api_key_warned = False


class JinaClient:
    """Thin async wrapper around the Jina reader API at https://r.jina.ai/.

    Inlined from ``deerflow.community.jina_ai.jina_client`` so the harness
    folder is fully self-contained.
    """

    async def crawl(self, url: str, return_format: str = "html", timeout: int = 10) -> str:
        global _api_key_warned
        headers = {
            "Content-Type": "application/json",
            "X-Return-Format": return_format,
            "X-Timeout": str(timeout),
        }
        if os.getenv("JINA_API_KEY"):
            headers["Authorization"] = f"Bearer {os.getenv('JINA_API_KEY')}"
        elif not _api_key_warned:
            _api_key_warned = True
            logger.warning("Jina API key is not set. Provide your own key to access a higher rate limit. See https://jina.ai/reader for more information.")
        data = {"url": url}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("https://r.jina.ai/", headers=headers, json=data, timeout=timeout)

            if response.status_code != 200:
                error_message = f"Jina API returned status {response.status_code}: {response.text}"
                logger.error(error_message)
                return f"Error: {error_message}"

            if not response.text or not response.text.strip():
                error_message = "Jina API returned empty response"
                logger.error(error_message)
                return f"Error: {error_message}"

            return response.text
        except Exception as e:
            error_message = f"Request to Jina API failed: {str(e)}"
            logger.exception(error_message)
            return f"Error: {error_message}"


readability_extractor = ReadabilityExtractor()


@tool("web_fetch", parse_docstring=True)
async def web_fetch_tool(url: str) -> str:
    """Fetch the contents of a web page at a given URL.
    Only fetch EXACT URLs that have been provided directly by the user or have been returned in results from the web_search and web_fetch tools.
    This tool can NOT access content that requires authentication, such as private Google Docs or pages behind login walls.
    Do NOT add www. to URLs that do NOT have them.
    URLs must include the schema: https://example.com is a valid URL while example.com is an invalid URL.

    Args:
        url: The URL to fetch the contents of.
    """
    jina_client = JinaClient()
    timeout = 10
    config = get_app_config().get_tool_config("web_fetch")
    if config is not None and "timeout" in config.model_extra:
        timeout = config.model_extra.get("timeout")
    html_content = await jina_client.crawl(url, return_format="html", timeout=timeout)
    if isinstance(html_content, str) and html_content.startswith("Error:"):
        return html_content
    article = await asyncio.to_thread(readability_extractor.extract_article, html_content)
    return article.to_markdown()[:4096]
