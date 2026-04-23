<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# packages

## Purpose

Container directory for publishable Python packages. Currently hosts a single package — `deerflow-harness` — which contains the entire reusable agent framework (agents, sandbox, models, MCP, skills, config, runtime).

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `harness/` | The `deerflow-harness` package; import prefix `deerflow.*` (see `harness/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- This directory is a thin namespace wrapper. Do not add code at this level — add new packages as siblings of `harness/`.
- The harness is the **only** part of the backend that may be published; `app/` depends on it but is unpublished.
- Adding a new package requires updating root `Makefile`, `backend/Makefile`, and the `pyproject.toml` workspace configuration.

## Dependencies

### Internal

- Consumed by `backend/app/`, `scripts/`, and external integrators

<!-- MANUAL: -->
