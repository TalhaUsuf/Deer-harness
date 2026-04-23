<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# tests

## Purpose

Backend test suite (~111 modules). Covers the harness (agents, sandbox, subagents, MCP, models, skills, config, runtime), the app layer (Gateway routers, channels), and critical regression checks (harness/app boundary, sandbox mode detection, provisioner kubeconfig handling).

## Key Files

| File | Description |
|------|-------------|
| `conftest.py` | Shared fixtures and `sys.modules` mocks for circular-import-prone modules |
| `test_harness_boundary.py` | Enforces that `packages/harness/deerflow/` does not import from `app.*` |
| `test_docker_sandbox_mode_detection.py` | Regression: sandbox mode resolved correctly from `config.yaml` |
| `test_provisioner_kubeconfig.py` | Regression: provisioner accepts kubeconfig file or directory |
| `test_client.py` | `DeerFlowClient` unit tests including `TestGatewayConformance` (validates client output against Gateway Pydantic models) |
| `test_client_live.py` | Live integration tests (require a running stack and `config.yaml`) |
| `test_memory_updater.py` | Memory subsystem regression (fact dedup, atomic writes) |

## For AI Agents

### Working In This Directory

- **TDD is mandatory** for backend changes. Every feature or bug fix must include a test here.
- Naming convention: `test_<feature>.py`. Mirror the source layout when reasonable (e.g. `test_skills.py` for `deerflow.skills`).
- Run the full suite via `make test` from `backend/`. For one file: `PYTHONPATH=. uv run pytest tests/test_<feature>.py -v`.
- The harness boundary test runs in CI on every PR (`.github/workflows/backend-unit-tests.yml`); never bypass it.
- Live tests (`*_live.py`) are excluded from the default run; gate them on a marker or environment variable.

### Testing Requirements

- Prefer pure unit tests with no external dependencies for utility / config modules.
- For modules that cause circular imports under test, add a `sys.modules` mock in `conftest.py` rather than restructuring import order.
- Gateway response models must round-trip through `TestGatewayConformance` whenever new dict fields are added to either side.

### Common Patterns

- Use the `tmp_path` fixture for file-IO tests; never write into the real `.deer-flow/` directory.
- Mock LLM calls — never hit a real provider in unit tests.
- For middleware tests, build minimal `ThreadState` instances rather than full agent runs.

## Dependencies

### Internal

- `packages/harness/deerflow/*` (subject under test)
- `app/*` (subject under test for router and channel tests)

### External

- `pytest`, `pytest-asyncio`, `httpx` (for FastAPI test client), `freezegun` (for time-sensitive tests)

<!-- MANUAL: -->
