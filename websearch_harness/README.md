# websearch_harness

Standalone, copy-pasteable web-search subsystem extracted from the
DeerFlow super-agent harness. No `deerflow.*` imports anywhere — all
required helpers, configs, and the relevant middleware are inlined
under `_internal/`.

## What's inside

```
websearch_harness/
├── __init__.py                           — re-exports providers + middleware
├── providers/
│   ├── ddg_search.py                     — web_search (DuckDuckGo, no key)
│   ├── tavily.py                         — web_search + web_fetch
│   ├── exa.py                            — web_search + web_fetch
│   ├── firecrawl.py                      — web_search + web_fetch
│   ├── jina_ai.py                        — web_fetch (async, optional key) + JinaClient
│   ├── infoquest.py                      — web_search + web_fetch + image_search + InfoQuestClient
│   └── image_search_ddg.py               — image_search (DuckDuckGo, no key)
├── middleware/
│   └── deferred_tool_filter_middleware.py — strips deferred tool schemas from bind_tools()
└── _internal/
    ├── app_config.py                     — STUB get_app_config().get_tool_config(name)
    ├── tool_config.py                    — ToolConfig + ToolGroupConfig (verbatim)
    ├── tool_search_config.py             — ToolSearchConfig (verbatim)
    ├── deferred_registry.py              — DeferredToolRegistry + tool_search (verbatim)
    ├── readability.py                    — Article + ReadabilityExtractor (verbatim)
    ├── search_filesystem.py              — find_glob_matches / find_grep_matches (verbatim)
    ├── reflection.py                     — resolve_variable("module:attr")
    └── tool_loader.py                    — trimmed get_available_tools(configs)
```

## Install

```bash
pip install \
  langchain>=1.0 langchain-core>=0.4 \
  pydantic>=2.0 \
  ddgs>=9.10.0 \
  tavily-python>=0.7.17 \
  exa-py>=1.0.0 \
  firecrawl-py>=1.15.0 \
  httpx>=0.28.0 \
  requests \
  readabilipy \
  markdownify
```

You only need the provider packages whose tools you actually plan to
use. Top-level `import websearch_harness` will tolerate missing
provider deps (the corresponding `*_tool` aliases will be `None`).

## Quick start

### Programmatic configuration

```python
from websearch_harness import (
    ToolConfig,
    set_tool_configs,
    tavily_web_search_tool,
    tavily_web_fetch_tool,
)

set_tool_configs([
    ToolConfig(
        name="web_search", group="search",
        use="websearch_harness.providers.tavily:web_search_tool",
        api_key="$TAVILY_API_KEY",   # resolved from os.environ at lookup time
        max_results=5,
    ),
    ToolConfig(
        name="web_fetch", group="search",
        use="websearch_harness.providers.tavily:web_fetch_tool",
        api_key="$TAVILY_API_KEY",
    ),
])

# Now bind to a LangChain agent:
from langchain.agents import create_agent
agent = create_agent(model=..., tools=[tavily_web_search_tool, tavily_web_fetch_tool])
```

### Env-var-only configuration

If you skip `set_tool_configs`, the providers fall back to reading API
keys directly from environment variables:

| Provider  | Env var             | Required? |
|-----------|---------------------|-----------|
| ddg_search| —                   | no key    |
| tavily    | `TAVILY_API_KEY`    | yes       |
| exa       | `EXA_API_KEY`       | yes       |
| firecrawl | `FIRECRAWL_API_KEY` | yes       |
| jina_ai   | `JINA_API_KEY`      | optional (raises rate limit) |
| infoquest | `INFOQUEST_API_KEY` | yes       |
| image_search_ddg | —            | no key    |

## Deferred-tool flow (optional)

When you bind many providers at once, the LLM's context bloats with
tool schemas. The deferred-tool flow advertises tool names only and
lets the LLM fetch full schemas on demand via the `tool_search`
builtin:

```python
from websearch_harness import (
    DeferredToolRegistry,
    set_deferred_registry,
    tool_search,
    DeferredToolFilterMiddleware,
    tavily_web_search_tool,
    exa_web_search_tool,
    firecrawl_web_search_tool,
)

registry = DeferredToolRegistry()
for t in (tavily_web_search_tool, exa_web_search_tool, firecrawl_web_search_tool):
    registry.register(t)
set_deferred_registry(registry)

agent = create_agent(
    model=...,
    tools=[tavily_web_search_tool, exa_web_search_tool, firecrawl_web_search_tool, tool_search],
    middleware=[DeferredToolFilterMiddleware()],
)
```

`DeferredToolFilterMiddleware` runs in `wrap_model_call` and strips
deferred-tool schemas from `request.tools` before
`model.bind_tools(...)`. The `tool_search` tool returns OpenAI-function
schemas for matching tools and "promotes" them out of the registry, so
on the next turn the middleware lets their schemas through.

## What's NOT carried over

- The full deerflow agent factory (`make_lead_agent`, middleware chain
  assembly, model factory, sandbox, subagents, MCP integration, …) —
  only the slice that web-search needs is here.
- Other middlewares (sandbox, summarization, todo list, memory,
  uploads, etc.) — see the sibling `standalone_middlewares/` folder
  for those.

## Source mapping

Every file in this folder includes a header comment that names its
original source path under
`backend/packages/harness/deerflow/...`. Use those headers as the
ground-truth reference when porting upstream changes.

## Testing in isolation

```bash
python -c "import websearch_harness; print('OK', [
    n for n in dir(websearch_harness) if n.endswith('_tool')
])"
```
