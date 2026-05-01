"""Standalone web-search / web-fetch / image-search provider tools.

Each module exposes one or more `@tool`-decorated callables ready to bind
to a LangChain agent. Provider modules:

  - ddg_search:       web_search_tool (DuckDuckGo, no API key required)
  - tavily:           web_search_tool, web_fetch_tool ($TAVILY_API_KEY)
  - exa:              web_search_tool, web_fetch_tool ($EXA_API_KEY)
  - firecrawl:        web_search_tool, web_fetch_tool ($FIRECRAWL_API_KEY)
  - jina_ai:          web_fetch_tool (async; optional $JINA_API_KEY)
  - infoquest:        web_search_tool, web_fetch_tool, image_search_tool ($INFOQUEST_API_KEY)
  - image_search_ddg: image_search_tool (DuckDuckGo, no API key required)
"""
