<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# harness

## Purpose

The `deerflow-harness` package — a publishable agent framework that bundles everything needed to build and run a DeerFlow-style agent: orchestration, tools, sandbox, models, MCP, skills, config, runtime, and the embedded `DeerFlowClient`. Import prefix: `deerflow.*`.

## Key Files

| File | Description |
|------|-------------|
| `pyproject.toml` | Package metadata, dependencies, build configuration |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `deerflow/` | The Python package itself — all importable modules (see `deerflow/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- The harness is **standalone**: it must work without `app.*` being installed. Boundary is enforced by `backend/tests/test_harness_boundary.py`.
- Public API surface should remain stable across versions — anything imported by `app/` or external consumers needs deprecation cycles before removal.
- Optional dependencies (Tavily, Jina, Firecrawl, image search, AIO sandbox, vLLM) should be lazily imported inside their modules so the base install stays light.

### Testing Requirements

- All harness tests live in `backend/tests/`. Run via `make test` from `backend/`.
- The boundary test ensures no `from app.*` imports leak into this package.

## Dependencies

### External

- `langgraph`, `langchain-core`, `langchain-openai`, `langchain-mcp-adapters`, Pydantic v2

<!-- MANUAL: -->
