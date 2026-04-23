<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# deerflow

## Purpose

The Python implementation of the DeerFlow harness. Contains the lead agent, middleware chain, sandbox abstraction, subagent system, MCP integration, model factory, skills loader, configuration system, runtime (for embedded gateway mode), reflection helpers, and the `DeerFlowClient` embedded API. **Never imports from `app.*`**.

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | Package marker; re-exports the most-used surface |
| `client.py` | `DeerFlowClient` — embedded in-process API mirroring the Gateway response schemas |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `agents/` | Lead agent factory, middleware chain (18 components), memory subsystem, checkpointer, `ThreadState` schema |
| `sandbox/` | Abstract `Sandbox` interface, `SandboxProvider` lifecycle, sandbox tools (`bash`, `ls`, `read_file`, `write_file`, `str_replace`), local provider |
| `subagents/` | Subagent registry + executor (dual thread pool, `MAX_CONCURRENT_SUBAGENTS=3`), built-in agents (`general-purpose`, `bash`) |
| `tools/` | `get_available_tools()` aggregator and built-in tools (`present_files`, `ask_clarification`, `view_image`) |
| `mcp/` | `MultiServerMCPClient` integration with lazy load + mtime-based cache invalidation; supports stdio, SSE, HTTP, OAuth |
| `models/` | Model factory (reflection-based instantiation), thinking/vision flag handling, vLLM provider for Qwen reasoning models |
| `skills/` | Skills discovery and loading (parses `SKILL.md` frontmatter, merges enable-state from `extensions_config.json`) |
| `config/` | Layered configuration system: `AppConfig`, `ModelConfig`, `ToolConfig`, `SandboxConfig`, version-drift warnings, env-var resolution |
| `community/` | Optional third-party tools: `tavily/`, `jina_ai/`, `firecrawl/`, `image_search/`, `ddg_search/`, `exa/`, `infoquest/`, `aio_sandbox/` (Docker isolation) |
| `runtime/` | Embedded agent runtime for gateway mode: `RunManager`, `run_agent()`, `StreamBridge`, runs/store packages |
| `tracing/` | Observability hooks (e.g. Langfuse integration — see `docs/plans/2026-04-01-langfuse-tracing.md`) |
| `guardrails/` | Pre-tool-call authorization providers (`AllowlistProvider` built-in; OAP / custom via the `GuardrailProvider` protocol) |
| `uploads/` | File upload handling and document conversion helpers |
| `reflection/` | `resolve_variable()` and `resolve_class()` for dynamic module loading from config |
| `utils/` | Shared utilities (network, readability) |

## For AI Agents

### Working In This Directory

- **Hard rule**: no imports from `app.*`. The boundary test (`backend/tests/test_harness_boundary.py`) will fail CI on violation.
- Middleware ordering matters — see `backend/CLAUDE.md` for the full 18-step chain. `ClarificationMiddleware` must remain last because it interrupts via `Command(goto=END)`.
- New tools register through `tools/__init__.py::get_available_tools(...)` and via config `tools[]` entries; do not bypass the aggregator.
- Optional providers (Tavily, Firecrawl, vLLM, etc.) must lazy-import their SDKs inside the module so missing extras don't break the base install — surface actionable hints (e.g. `uv add langchain-google-genai`) in the resolver.
- All state lives in `ThreadState` (see `agents/thread_state.py`) with custom reducers `merge_artifacts` and `merge_viewed_images`.

### Testing Requirements

- New code requires unit tests in `backend/tests/test_<feature>.py` (TDD is **mandatory** per `backend/CLAUDE.md`).
- For circular-import-prone modules, add a `sys.modules` mock in `backend/tests/conftest.py` (see existing `deerflow.subagents.executor` example).

### Common Patterns

- Reflection-based wiring: `models[]`, `tools[]`, `sandbox.use`, etc. specify `module.path:VariableOrClass`. The `reflection/` helpers do the import + validation.
- Config caching with mtime invalidation: `get_app_config()` reloads when the file changes; MCP and skills caches do the same.
- Path translation: agent sees `/mnt/user-data/{workspace,uploads,outputs}` and `/mnt/skills`; the local provider rewrites to host paths via `replace_virtual_path()`.

## Dependencies

### External

- `langgraph`, `langchain-core`, `langchain-openai`, `langchain-anthropic`, `langchain-mcp-adapters`, Pydantic v2
- Provider-specific SDKs are optional (lazy-imported)

<!-- MANUAL: -->
