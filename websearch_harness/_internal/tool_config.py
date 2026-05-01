"""
tool_config.py — Verbatim copy of `deerflow.config.tool_config`.

Why this file exists
--------------------
Every web-search provider (ddg_search, tavily, exa, firecrawl, jina_ai,
infoquest, image_search) calls `get_app_config().get_tool_config(name)`
to look up its API key, max_results, timeouts, etc. The returned object
is a `ToolConfig` instance whose extra fields land in `.model_extra`.

This module supplies that schema. No deerflow internals are referenced.

Original source
---------------
backend/packages/harness/deerflow/config/tool_config.py

External deps: pydantic.
"""

from pydantic import BaseModel, ConfigDict, Field


class ToolGroupConfig(BaseModel):
    """Logical grouping for a tool (e.g. 'search', 'bash')."""

    name: str = Field(..., description="Unique name for the tool group")
    model_config = ConfigDict(extra="allow")


class ToolConfig(BaseModel):
    """Per-tool configuration entry from the user's config.yaml.

    Provider-specific keys (api_key, max_results, timeout, etc.) flow
    through `model_config = extra='allow'` and are read off `.model_extra`.
    """

    name: str = Field(..., description="Unique name for the tool")
    group: str = Field(..., description="Group name for the tool")
    use: str = Field(
        ...,
        description="Variable name of the tool provider (e.g. websearch_harness.providers.ddg_search:web_search_tool)",
    )
    model_config = ConfigDict(extra="allow")
