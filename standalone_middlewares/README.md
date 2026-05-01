# standalone_middlewares

Copy-pasteable rewrite of the 17 LangGraph middlewares that live in
`backend/packages/harness/deerflow/agents/middlewares/`.

The point: drop this folder into any other project — it will import cleanly
without dragging the rest of the `deerflow` package along, as long as the
external pip deps are installed.

## Install

```bash
pip install "langchain>=1.0" "langchain-core>=0.4" "langgraph>=1.0" "pydantic>=2.0"
```

Then `cp -r standalone_middlewares /path/to/your/project/`.

## Usage

```python
from standalone_middlewares import (
    ClarificationMiddleware,
    LLMErrorHandlingMiddleware,
    LoopDetectionMiddleware,
    SubagentLimitMiddleware,
    # ... 13 more
)

agent = create_agent(
    model=...,
    tools=[...],
    middleware=[
        ClarificationMiddleware(),
        LLMErrorHandlingMiddleware(),
        LoopDetectionMiddleware(),
        # ... etc
    ],
)
```

Or use the prebuilt stack helper:

```python
from standalone_middlewares import build_lead_runtime_middlewares

middlewares = build_lead_runtime_middlewares(lazy_init=True)
# Splice in your own SandboxMiddleware / GuardrailMiddleware where
# the source code comments indicate.
```

## Layout

```
standalone_middlewares/
├── __init__.py                  Re-exports all 17 middleware classes.
├── README.md                    This file.
├── _internal/                   Inlined helpers (was: deerflow.*).
│   ├── thread_state.py          ThreadState, ThreadDataState (verbatim).
│   ├── paths.py                 Paths, get_paths (verbatim).
│   ├── memory_config.py         MemoryConfig (verbatim).
│   ├── title_config.py          TitleConfig (verbatim).
│   ├── app_config.py            ★ STUB — only carries `circuit_breaker`.
│   ├── memory_message_processing.py   filter / detect helpers (verbatim).
│   ├── memory_queue.py          MemoryUpdateQueue + ★ STUB updater.
│   ├── file_conversion.py       extract_outline (verbatim, trimmed).
│   ├── tool_search_registry.py  DeferredToolRegistry (verbatim, trimmed).
│   ├── models_factory.py        ★ STUB — create_chat_model raises.
│   └── subagent_const.py        MAX_CONCURRENT_SUBAGENTS = 3.
├── clarification_middleware.py
├── custom_instructions_middleware.py
├── dangling_tool_call_middleware.py
├── deferred_tool_filter_middleware.py
├── llm_error_handling_middleware.py
├── loop_detection_middleware.py
├── memory_middleware.py
├── sandbox_audit_middleware.py
├── subagent_limit_middleware.py
├── summarization_middleware.py
├── thread_data_middleware.py
├── title_middleware.py
├── todo_middleware.py
├── token_usage_middleware.py
├── tool_error_handling_middleware.py
├── uploads_middleware.py
└── view_image_middleware.py
```

## Stubs you may want to wire up

★ Three internal helpers are stubs in this standalone build — the
middlewares still import cleanly, but the affected behaviour is degraded
until you replace the stub with a real implementation.

| Stub | Affected middleware | What it does in stub mode | What it should do |
|---|---|---|---|
| `_internal/models_factory.py::create_chat_model` | `TitleMiddleware` | Raises `NotImplementedError`; the middleware catches and uses a truncation-based fallback title. | Return a `BaseChatModel` instance so titles are LLM-generated. |
| `_internal/memory_queue.py::_StubMemoryUpdater` | `MemoryMiddleware` | Logs that an update would have happened, persists nothing. | Run an LLM prompt to extract facts from the conversation and write them to your memory store. |
| `_internal/app_config.py::AppConfig` | `LLMErrorHandlingMiddleware` (reads `circuit_breaker`) | Defaults: 5 failures, 60 s recovery. | Replace with your own config-loading code if you want runtime tuning. |

The two factory functions in `tool_error_handling_middleware.py`
(`build_lead_runtime_middlewares`, `build_subagent_runtime_middlewares`) also
return a *stripped* stack — they leave gaps where `SandboxMiddleware` and
`GuardrailMiddleware` would normally sit. Comments in the function bodies
mark the splice points.

## Per-middleware reference

Every middleware file starts with a heavy header comment block explaining:
* what the middleware does
* which lifecycle hook(s) it overrides
* what state it reads / mutates
* which internal `deerflow.*` imports were rewritten and where they now
  point.

Read the headers — they're the user-facing documentation.

## Origin

This folder was generated from
`backend/packages/harness/deerflow/agents/middlewares/` at the time of the
commit that added `standalone_middlewares/` to the repo. If the upstream
middlewares change, regenerate by re-running the same parallel-investigation
process and re-applying the import rewrites.
