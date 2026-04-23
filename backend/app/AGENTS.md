<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# app

## Purpose

Application layer for the DeerFlow backend (import prefix `app.*`). Contains the FastAPI Gateway API and IM platform channel integrations. **Unpublished** code that depends on the publishable harness package (`packages/harness/deerflow/`) but is never imported by it.

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | Package marker |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `gateway/` | FastAPI Gateway API on port 8001 — REST endpoints for models, MCP, skills, memory, uploads, threads, artifacts, agents (see `gateway/AGENTS.md`) |
| `channels/` | IM platform bridges (Feishu, Slack, Telegram, Discord, WeChat, WeCom) using `langgraph-sdk` HTTP client (see `channels/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- **Harness boundary**: code here MAY import `from deerflow.*` but `deerflow/*` MUST NOT import `from app.*`. Enforced by `tests/test_harness_boundary.py` in CI.
- New modules belong here only if they require FastAPI, channel SDKs, or other deployment-tier concerns. Reusable agent logic belongs in the harness.
- Use `from app.gateway.deps import ...` for dependency-injected services (config, sandbox provider, etc.).

### Testing Requirements

- Run `make test` from `backend/`. Boundary check (`tests/test_harness_boundary.py`) MUST pass.
- Gateway router changes need a corresponding test in `tests/test_*_router.py`.

### Common Patterns

- Routers live in `gateway/routers/<resource>.py` and are registered via `gateway/app.py`.
- Channels follow the abstract `Channel` base class in `channels/base.py`.

## Dependencies

### Internal

- `packages/harness/deerflow/` — agent runtime, sandbox, models, MCP, skills, config (allowed direction)

### External

- FastAPI, Uvicorn, `langgraph-sdk`, channel-specific SDKs (`slack-sdk`, `python-telegram-bot`, etc.)

<!-- MANUAL: -->
