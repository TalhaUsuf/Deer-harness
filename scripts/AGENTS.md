<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# scripts

## Purpose

Operator and developer entry points for installing, running, deploying, diagnosing, and configuring DeerFlow. Most root `Makefile` targets shell out to scripts here.

## Key Files

| File | Description |
|------|-------------|
| `serve.sh` | Local foreground / daemon launcher for dev and prod modes (drives `make dev`, `make start`) |
| `docker.sh` | Docker dev stack lifecycle (`start`, `stop`, `restart`) |
| `deploy.sh` | Production Docker deploy (`make up`, `make down`) |
| `start-daemon.sh` | Background process launcher used by `serve.sh --daemon` |
| `check.sh` / `check.py` | System-requirement preflight (Node, Python, uv, pnpm, Docker) |
| `doctor.py` | Deeper diagnostic for a misconfigured installation |
| `configure.py` | Interactive config helper |
| `setup_wizard.py` | First-run setup wizard entry point (delegates to `wizard/`) |
| `config-upgrade.sh` | Merges new fields from `config.example.yaml` into `config.yaml` (`make config-upgrade`) |
| `cleanup-containers.sh` | Removes orphaned dev sandboxes |
| `wait-for-port.sh` | Block until TCP port is listening (used by other scripts) |
| `tool-error-degradation-detection.sh` | Heuristic for detecting LLM tool-error regressions |
| `export_claude_code_oauth.py` | Export Claude Code OAuth credentials for embedded use |
| `load_memory_sample.py` | Seed `memory.json` with sample data for development |
| `run-with-git-bash.cmd` | Windows entry shim that re-execs under Git Bash |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `wizard/` | Setup wizard implementation: providers, UI, writer, step modules (see `wizard/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- Shell scripts are POSIX-compatible where possible; Windows users go through `run-with-git-bash.cmd`.
- `serve.sh` accepts flags `--dev`, `--prod`, `--gateway`, `--daemon`, `--restart`, `--stop`. Read its case statement before adding new options.
- `doctor.py` is intentionally noisy — it prints what it checked and what it found, even on success. Preserve that behavior.
- Long-running scripts must respect `wait-for-port.sh` for service readiness instead of `sleep`.

### Testing Requirements

- After modifying a script, run it end-to-end at least once (`bash -n` for syntax is not sufficient).
- For Python helpers, type-check with `ruff check` from `backend/`.

### Common Patterns

- All daemon scripts write a PID file under `.deer-flow/pids/` so `serve.sh --stop` can clean up.
- Scripts that touch `config.yaml` always make a `.bak` copy first.

## Dependencies

### Internal

- `Makefile` (root) — most targets call into here
- `docker/docker-compose*.yaml` — referenced by `docker.sh` / `deploy.sh`
- `backend/Makefile`, `frontend/package.json` — invoked from `serve.sh`

### External

- Bash 4+, Python 3.12+, `uv`, `pnpm`, `docker`

<!-- MANUAL: -->
