<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# gateway

## Purpose

FastAPI Gateway API on port 8001. Health check at `GET /health`. Provides REST access to models, MCP servers, skills, memory, file uploads, thread cleanup, artifact serving, agent invocation, and follow-up question generation. Frontend talks to it via Nginx proxy under `/api/*`.

## Key Files

| File | Description |
|------|-------------|
| `app.py` | FastAPI application; registers routers, CORS, exception handlers |
| `config.py` | Gateway-specific config (CORS origins, log level, etc.) |
| `services.py` | Shared service singletons (sandbox provider, MCP cache, memory) |
| `deps.py` | FastAPI dependency providers (`Depends(...)`) |
| `path_utils.py` | Helpers for resolving thread-scoped paths and translating virtual paths |
| `__init__.py` | Package marker |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `routers/` | One module per resource: `models`, `mcp`, `skills`, `memory`, `uploads`, `threads`, `thread_runs`, `artifacts`, `agents`, `runs`, `suggestions`, `channels`, `assistants_compat` |

## For AI Agents

### Working In This Directory

- Gateway-mode (`make dev-pro`) embeds the agent runtime in this process via `RunManager` + `run_agent()` + `StreamBridge` from `deerflow.runtime`. Standard mode keeps Gateway as a peer to the LangGraph server.
- Active content types (`text/html`, `application/xhtml+xml`, `image/svg+xml`) served from `routers/artifacts.py` are **always** forced as download attachments to mitigate XSS.
- Thread cleanup endpoint (`DELETE /api/threads/{id}`) deletes `.deer-flow/threads/{thread_id}` after LangGraph has removed the thread; failures are logged server-side and return a generic 500 detail.
- All dict responses must conform to the matching Gateway Pydantic response model — this is checked against `DeerFlowClient` outputs by `tests/test_client.py::TestGatewayConformance`.

### Testing Requirements

- Per-router tests live at `backend/tests/test_<resource>_router.py`.
- Gateway-conformance tests catch any drift between Gateway models and the embedded `DeerFlowClient` API.

### Common Patterns

- One file per router resource; no nested router packages.
- Inject services via `Depends(get_<service>)` from `deps.py`; do not instantiate inside routes.
- Use `path_utils.translate_virtual_path()` whenever the agent-facing virtual path needs to map to a host path.

## Dependencies

### Internal

- `deerflow.config`, `deerflow.runtime`, `deerflow.sandbox`, `deerflow.skills`, `deerflow.mcp`, `deerflow.client` — harness modules

### External

- FastAPI, Uvicorn, Pydantic v2, `markitdown` (for upload conversion)

<!-- MANUAL: -->
