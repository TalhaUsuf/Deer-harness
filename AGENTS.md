<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# deer-flow

## Purpose

DeerFlow is a LangGraph-based AI super-agent platform with a Next.js frontend, FastAPI Gateway, sandboxed execution, persistent memory, subagent delegation, MCP integration, and IM channel bridges. The repo is a monorepo: Python backend (`backend/`), TypeScript frontend (`frontend/`), shared skills (`skills/`), Docker deployment assets (`docker/`), and operator scripts (`scripts/`).

## Key Files

| File | Description |
|------|-------------|
| `Makefile` | Top-level orchestration (`make check`, `install`, `dev`, `dev-pro`, `start`, `stop`, `docker-start`) |
| `README.md` | User-facing project overview (English; localized variants `README_{fr,ja,ru,zh}.md`) |
| `Install.md` | Installation walkthrough |
| `CONTRIBUTING.md` | Contribution workflow and PR rules |
| `CODE_OF_CONDUCT.md` | Community guidelines |
| `SECURITY.md` | Security disclosure policy |
| `LICENSE` | MIT license |
| `config.example.yaml` | Reference application configuration; copy to `config.yaml` |
| `extensions_config.example.json` | Reference MCP servers + skills config; copy to `extensions_config.json` |
| `deer-flow.code-workspace` | VS Code multi-root workspace |
| `.dockerignore` / `.gitattributes` / `.gitignore` | VCS / Docker hygiene |
| `.env.example` | Environment variable template |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `backend/` | Python backend: LangGraph agent, FastAPI Gateway, IM channels, harness library (see `backend/AGENTS.md`) |
| `frontend/` | Next.js 16 web UI for thread-based AI conversations (see `frontend/AGENTS.md`) |
| `skills/` | Agent skills tree (`public/` committed, `custom/` gitignored) (see `skills/AGENTS.md`) |
| `docker/` | Compose files, Nginx config, provisioner (see `docker/AGENTS.md`) |
| `scripts/` | Operator scripts: serve, deploy, doctor, setup wizard (see `scripts/AGENTS.md`) |
| `docs/` | Project-wide documentation, plans, PR evidence (see `docs/AGENTS.md`) |
| `.github/` | GitHub Actions workflows and issue templates (see `.github/AGENTS.md`) |
| `.agent/` | Bundled smoke-test skill used by the harness (self-contained `SKILL.md`) |
| `pr-build/` | Transient screenshots attached to PRs |

## For AI Agents

### Working In This Directory

- The repo has two layers of CLAUDE.md guidance: `backend/CLAUDE.md` (architecture, middleware chain, harness/app boundary) and `frontend/CLAUDE.md` (Next.js layout, data flow, code style). Both are loaded automatically when the corresponding `AGENTS.md` is opened.
- **Documentation policy**: when changing code, update `README.md` for user-facing changes and `CLAUDE.md` (in the relevant subtree) for architecture / dev workflow changes.
- **Harness → App firewall**: `backend/packages/harness/deerflow/` must NOT import from `app.*`. Enforced by `backend/tests/test_harness_boundary.py` in CI.
- Configuration files (`config.yaml`, `extensions_config.json`) are resolved from project root by default; `config_version` drift triggers a warning at startup — bump it whenever the schema changes.
- The dev branch in active use is documented in `.github/` and per-feature instructions; never push directly to `main`.

### Testing Requirements

| Area | Command | Where |
|------|---------|-------|
| Full app | `make check` | root |
| Backend tests | `make test` (or `cd backend && make test`) | backend |
| Backend lint | `make lint` / `make format` (ruff) | backend |
| Frontend lint + types | `pnpm check` | frontend |
| Frontend unit | `pnpm test` (Vitest) | frontend |
| Frontend e2e | `pnpm test:e2e` (Playwright/Chromium) | frontend |

CI runs backend regression tests via `.github/workflows/backend-unit-tests.yml`.

### Common Patterns

- Two runtime modes: **standard** (`make dev`, separate LangGraph server on :2024) and **gateway** (`make dev-pro`, agent embedded in Gateway via `RunManager`/`StreamBridge`).
- Nginx reverse-proxies `:2026` → frontend, gateway, langgraph in both modes.
- Channels (Feishu, Slack, Telegram) and skills are configured in `config.yaml` / `extensions_config.json` and hot-reload via mtime checks.

## Dependencies

### External

- Python 3.12+, `uv` package manager, `ruff` for linting
- Node.js 22+, `pnpm` 10.26.2+
- Docker / Docker Compose for `make docker-start` and production deploys
- Optional: Kubernetes (for provisioner sandbox mode)

<!-- MANUAL: Notes added below this line are preserved on regeneration -->
