"""
infoquest.py — BytePlus InfoQuest ``web_search`` + ``web_fetch`` +
``image_search`` tools.

Provider summary
----------------
- ``web_search_tool(query)``  → JSON list with ``{type,title,url,...}``
  entries cleaned from InfoQuest's organic + top-stories results.
- ``web_fetch_tool(url)``     → ``article.to_markdown()[:4096]`` after
  passing the InfoQuest reader-result HTML through ``ReadabilityExtractor``.
- ``image_search_tool(query)``→ JSON list of ``{image_url,title}``
  built from InfoQuest's image-search response.

Authentication
--------------
``INFOQUEST_API_KEY`` is read directly from ``os.environ`` by
``InfoQuestClient._prepare_headers()`` (not through the AppConfig
stub). See https://docs.byteplus.com/en/docs/InfoQuest/What_is_Info_Quest
for setup.

Configuration
-------------
- ``ToolConfig(name="web_search",  search_time_range=-1)``
- ``ToolConfig(name="web_fetch",   fetch_time=-1, timeout=-1, navigation_timeout=-1)``
- ``ToolConfig(name="image_search", image_search_time_range=-1, image_size="i")``

A value of ``-1`` means "use InfoQuest defaults" (no client-side filter).

External pip dep: ``requests`` (sync HTTP).

Internal-import rewrites
------------------------
Original                                                       | Rewritten
---------------------------------------------------------------|---------------------------
from deerflow.config import get_app_config                     | from .._internal.app_config import get_app_config
from deerflow.utils.readability import ReadabilityExtractor    | from .._internal.readability import ReadabilityExtractor
from .infoquest_client import InfoQuestClient                  | (InfoQuestClient inlined below)

Original source
---------------
backend/packages/harness/deerflow/community/infoquest/tools.py
backend/packages/harness/deerflow/community/infoquest/infoquest_client.py
"""

import json
import logging
import os
from typing import Any

import requests
from langchain.tools import tool

from .._internal.app_config import get_app_config
from .._internal.readability import ReadabilityExtractor

logger = logging.getLogger(__name__)


class InfoQuestClient:
    """Sync HTTP client for the BytePlus InfoQuest search/reader APIs.

    Inlined from ``deerflow.community.infoquest.infoquest_client`` so the
    harness folder has no cross-package imports.

    Endpoints
    ---------
    - https://search.infoquest.bytepluses.com (web + image search)
    - https://reader.infoquest.bytepluses.com (page fetch / readability)
    """

    def __init__(
        self,
        fetch_time: int = -1,
        fetch_timeout: int = -1,
        fetch_navigation_timeout: int = -1,
        search_time_range: int = -1,
        image_search_time_range: int = -1,
        image_size: str = "i",
    ):
        logger.info("BytePlus InfoQuest Client Initialized")
        self.fetch_time = fetch_time
        self.fetch_timeout = fetch_timeout
        self.fetch_navigation_timeout = fetch_navigation_timeout
        self.search_time_range = search_time_range
        self.image_search_time_range = image_search_time_range
        self.image_size = image_size
        self.api_key_set = bool(os.getenv("INFOQUEST_API_KEY"))

    def fetch(self, url: str, return_format: str = "html") -> str:
        headers = self._prepare_headers()
        data = self._prepare_crawl_request_data(url, return_format)
        try:
            response = requests.post("https://reader.infoquest.bytepluses.com", headers=headers, json=data)
            if response.status_code != 200:
                return f"Error: fetch API returned status {response.status_code}: {response.text}"
            if not response.text or not response.text.strip():
                return "Error: no result found"
            try:
                response_data = json.loads(response.text)
                if "reader_result" in response_data:
                    return response_data["reader_result"]
                elif "content" in response_data:
                    return response_data["content"]
                else:
                    logger.warning("Neither reader_result nor content field found in JSON response")
            except json.JSONDecodeError:
                return response.text
            return response.text
        except Exception as e:
            return f"Error: fetch API failed: {str(e)}"

    @staticmethod
    def _prepare_headers() -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if os.getenv("INFOQUEST_API_KEY"):
            headers["Authorization"] = f"Bearer {os.getenv('INFOQUEST_API_KEY')}"
        else:
            logger.warning("InfoQuest API key is not set. Provide your own key for authentication.")
        return headers

    def _prepare_crawl_request_data(self, url: str, return_format: str) -> dict[str, Any]:
        normalized_format = "HTML" if return_format and return_format.lower() == "html" else return_format
        data: dict[str, Any] = {"url": url, "format": normalized_format}
        timeout_params: dict[str, Any] = {}
        if self.fetch_time > 0:
            timeout_params["fetch_time"] = self.fetch_time
        if self.fetch_timeout > 0:
            timeout_params["timeout"] = self.fetch_timeout
        if self.fetch_navigation_timeout > 0:
            timeout_params["navi_timeout"] = self.fetch_navigation_timeout
        if timeout_params:
            data.update(timeout_params)
        return data

    def web_search_raw_results(self, query: str, site: str, output_format: str = "JSON") -> dict:
        headers = self._prepare_headers()
        params: dict[str, Any] = {"format": output_format, "query": query}
        if self.search_time_range > 0:
            params["time_range"] = self.search_time_range
        if site != "":
            params["site"] = site
        response = requests.post("https://search.infoquest.bytepluses.com", headers=headers, json=params)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def clean_results(raw_results: list[dict[str, dict[str, dict[str, Any]]]]) -> list[dict]:
        seen_urls: set[str] = set()
        clean: list[dict] = []
        for content_list in raw_results:
            content = content_list["content"]
            results = content["results"]
            if results.get("organic"):
                for result in results["organic"]:
                    cr: dict[str, Any] = {"type": "page"}
                    if "title" in result:
                        cr["title"] = result["title"]
                    if "desc" in result:
                        cr["desc"] = result["desc"]
                        cr["snippet"] = result["desc"]
                    if "url" in result:
                        cr["url"] = result["url"]
                        url = cr["url"]
                        if isinstance(url, str) and url and url not in seen_urls:
                            seen_urls.add(url)
                            clean.append(cr)
            if results.get("top_stories"):
                news = results["top_stories"]
                for obj in news["items"]:
                    cr = {"type": "news"}
                    if "time_frame" in obj:
                        cr["time_frame"] = obj["time_frame"]
                    if "source" in obj:
                        cr["source"] = obj["source"]
                    title = obj.get("title")
                    url = obj.get("url")
                    if title:
                        cr["title"] = title
                    if url:
                        cr["url"] = url
                    if title and isinstance(url, str) and url and url not in seen_urls:
                        seen_urls.add(url)
                        clean.append(cr)
        return clean

    def web_search(self, query: str, site: str = "", output_format: str = "JSON") -> str:
        try:
            raw_results = self.web_search_raw_results(query, site, output_format)
            if "search_result" in raw_results:
                results = raw_results["search_result"]
                cleaned = self.clean_results(results["results"])
                return json.dumps(cleaned, indent=2, ensure_ascii=False)
            elif "content" in raw_results:
                return "Error: web search API return wrong format"
            else:
                return json.dumps(raw_results, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error: InfoQuest Web-Search failed: {str(e)}"

    @staticmethod
    def clean_results_with_image_search(raw_results: list[dict[str, dict[str, dict[str, Any]]]]) -> list[dict]:
        seen_urls: set[str] = set()
        clean: list[dict] = []
        for content_list in raw_results:
            content = content_list["content"]
            results = content["results"]
            if results.get("images_results"):
                for result in results["images_results"]:
                    cr: dict[str, Any] = {}
                    if "original" in result:
                        cr["image_url"] = result["original"]
                        url = cr["image_url"]
                        if isinstance(url, str) and url and url not in seen_urls:
                            seen_urls.add(url)
                            clean.append(cr)
                    if "title" in result:
                        cr["title"] = result["title"]
        return clean

    def image_search_raw_results(self, query: str, site: str = "", output_format: str = "JSON") -> dict:
        headers = self._prepare_headers()
        params: dict[str, Any] = {"format": output_format, "query": query, "search_type": "Images"}
        if 1 <= self.image_search_time_range <= 365:
            params["time_range"] = self.image_search_time_range
        if site:
            params["site"] = site
        if self.image_size and self.image_size in ["l", "m", "i"]:
            params["image_size"] = self.image_size
        response = requests.post("https://search.infoquest.bytepluses.com", headers=headers, json=params)
        response.raise_for_status()
        return response.json()

    def image_search(self, query: str, site: str = "", output_format: str = "JSON") -> str:
        try:
            raw_results = self.image_search_raw_results(query, site, output_format)
            if "search_result" in raw_results:
                results = raw_results["search_result"]
                cleaned = self.clean_results_with_image_search(results["results"])
                return json.dumps(cleaned, indent=2, ensure_ascii=False)
            elif "content" in raw_results:
                return "Error: image search API return wrong format"
            else:
                return json.dumps(raw_results, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error: InfoQuest Image Search failed: {str(e)}"


readability_extractor = ReadabilityExtractor()


def _get_infoquest_client() -> InfoQuestClient:
    """Build an InfoQuestClient from registered ToolConfig entries."""
    search_config = get_app_config().get_tool_config("web_search")
    search_time_range = -1
    if search_config is not None and "search_time_range" in search_config.model_extra:
        search_time_range = search_config.model_extra.get("search_time_range")

    fetch_config = get_app_config().get_tool_config("web_fetch")
    fetch_time = -1
    if fetch_config is not None and "fetch_time" in fetch_config.model_extra:
        fetch_time = fetch_config.model_extra.get("fetch_time")
    fetch_timeout = -1
    if fetch_config is not None and "timeout" in fetch_config.model_extra:
        fetch_timeout = fetch_config.model_extra.get("timeout")
    navigation_timeout = -1
    if fetch_config is not None and "navigation_timeout" in fetch_config.model_extra:
        navigation_timeout = fetch_config.model_extra.get("navigation_timeout")

    image_search_config = get_app_config().get_tool_config("image_search")
    image_search_time_range = -1
    if image_search_config is not None and "image_search_time_range" in image_search_config.model_extra:
        image_search_time_range = image_search_config.model_extra.get("image_search_time_range")
    image_size = "i"
    if image_search_config is not None and "image_size" in image_search_config.model_extra:
        image_size = image_search_config.model_extra.get("image_size")

    return InfoQuestClient(
        search_time_range=search_time_range,
        fetch_timeout=fetch_timeout,
        fetch_navigation_timeout=navigation_timeout,
        fetch_time=fetch_time,
        image_search_time_range=image_search_time_range,
        image_size=image_size,
    )


@tool("web_search", parse_docstring=True)
def web_search_tool(query: str) -> str:
    """Search the web.

    Args:
        query: The query to search for.
    """
    client = _get_infoquest_client()
    return client.web_search(query)


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
    client = _get_infoquest_client()
    result = client.fetch(url)
    if result.startswith("Error: "):
        return result
    article = readability_extractor.extract_article(result)
    return article.to_markdown()[:4096]


@tool("image_search", parse_docstring=True)
def image_search_tool(query: str) -> str:
    """Search for images online. Use this tool BEFORE image generation to find reference images for characters, portraits, objects, scenes, or any content requiring visual accuracy.

    **When to use:**
    - Before generating character/portrait images: search for similar poses, expressions, styles
    - Before generating specific objects/products: search for accurate visual references
    - Before generating scenes/locations: search for architectural or environmental references
    - Before generating fashion/clothing: search for style and detail references

    The returned image URLs can be used as reference images in image generation to significantly improve quality.

    Args:
        query: The query to search for images.
    """
    client = _get_infoquest_client()
    return client.image_search(query)
