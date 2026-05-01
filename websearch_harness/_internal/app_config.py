"""
app_config.py — Minimal stub of `deerflow.config.get_app_config`.

Why a stub
----------
Deerflow's real `AppConfig` is a 397-line Pydantic aggregate that imports
17+ sub-config modules (memory, sandbox, subagents, skills, channels, ...).
The web-search providers in this harness only need ONE method on it:

    get_app_config().get_tool_config(tool_name) -> ToolConfig | None

…which the providers consult to read their `api_key`, `max_results`,
`timeout`, etc. via `.model_extra`. Pulling in the full AppConfig would
defeat the goal of being copy-pasteable, so we ship a tiny replacement
that satisfies the same surface contract.

Two configuration pathways
--------------------------
1. **Programmatic** (preferred for embedding):

       from websearch_harness._internal.app_config import set_tool_configs
       from websearch_harness._internal.tool_config import ToolConfig
       set_tool_configs([
           ToolConfig(name="web_search", group="search",
                      use="websearch_harness.providers.tavily:web_search_tool",
                      api_key="$TAVILY_API_KEY", max_results=5),
       ])

2. **Environment-variable fallback**: if no `ToolConfig` is registered for
   *tool_name*, providers fall back to reading their API key from the
   provider-specific env var (e.g. `TAVILY_API_KEY`, `EXA_API_KEY`,
   `FIRECRAWL_API_KEY`, `JINA_API_KEY`, `INFOQUEST_API_KEY`).
   This is handled by each provider directly via `os.getenv` — this stub
   only needs to return `None` to trigger that fallback.

Env-var placeholder substitution
--------------------------------
If a registered `ToolConfig` carries a value like `"$TAVILY_API_KEY"`, the
stub resolves it to `os.environ["TAVILY_API_KEY"]` on lookup. This mirrors
deerflow's behaviour where config values starting with `$` are treated as
environment-variable references.

Original source
---------------
backend/packages/harness/deerflow/config/app_config.py (full impl, ~397 LOC)
backend/packages/harness/deerflow/config/__init__.py (which re-exports
``get_app_config``)

External deps: stdlib only.
"""

from __future__ import annotations

import os
from typing import Any

from .tool_config import ToolConfig


class _StubAppConfig:
    """Minimal AppConfig surface used by web-search provider tools."""

    def __init__(self) -> None:
        self._tool_configs: dict[str, ToolConfig] = {}

    # Public surface used by providers ─────────────────────────────────
    def get_tool_config(self, name: str) -> ToolConfig | None:
        cfg = self._tool_configs.get(name)
        if cfg is None:
            return None
        return _resolve_env_vars(cfg)

    # Mutators (programmatic configuration) ────────────────────────────
    def set_tool_configs(self, configs: list[ToolConfig]) -> None:
        self._tool_configs = {c.name: c for c in configs}

    def add_tool_config(self, cfg: ToolConfig) -> None:
        self._tool_configs[cfg.name] = cfg

    def clear_tool_configs(self) -> None:
        self._tool_configs.clear()


def _resolve_env_vars(cfg: ToolConfig) -> ToolConfig:
    """Return a copy of *cfg* with `$VAR` strings resolved from os.environ.

    Mirrors deerflow's behaviour: any extra-field whose value is a string
    starting with ``$`` is replaced with `os.environ.get(VAR)`. Missing
    env vars become None so providers can detect "not configured".
    """
    if not cfg.model_extra:
        return cfg
    resolved: dict[str, Any] = {}
    for key, value in cfg.model_extra.items():
        if isinstance(value, str) and value.startswith("$"):
            resolved[key] = os.environ.get(value[1:])
        else:
            resolved[key] = value
    return cfg.model_copy(update=resolved)


_singleton: _StubAppConfig | None = None


def get_app_config() -> _StubAppConfig:
    """Return the process-wide stub AppConfig (lazy singleton)."""
    global _singleton
    if _singleton is None:
        _singleton = _StubAppConfig()
    return _singleton


def set_tool_configs(configs: list[ToolConfig]) -> None:
    """Convenience wrapper around `get_app_config().set_tool_configs(...)`."""
    get_app_config().set_tool_configs(configs)


def reset_app_config() -> None:
    """Drop the singleton — primarily a test-isolation helper."""
    global _singleton
    _singleton = None
