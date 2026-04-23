<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# provisioner

## Purpose

Optional FastAPI sandbox provisioner (port 8002) that allocates per-thread isolated execution environments for the agent. Selected via `sandbox.use` in `config.yaml` when running in Docker or Kubernetes mode. Skipped entirely for `LocalSandboxProvider`.

## Key Files

| File | Description |
|------|-------------|
| `app.py` | FastAPI service exposing acquire/get/release endpoints for sandbox lifecycle |
| `Dockerfile` | Image build (Python + Docker SDK / kubernetes client) |
| `README.md` | Operator notes and config examples |

## For AI Agents

### Working In This Directory

- Provisioner is a peer service to Gateway, not embedded. The harness `AioSandboxProvider` (in `backend/packages/harness/deerflow/community/aio_sandbox/`) talks to it over HTTP.
- Two backends supported: Docker (default) and Kubernetes (kubeconfig file or directory). Mode is detected at startup; see `backend/tests/test_docker_sandbox_mode_detection.py` and `backend/tests/test_provisioner_kubeconfig.py`.
- Each acquired sandbox lives for the duration of one thread; `release` is idempotent.

### Testing Requirements

- Regression tests live in `backend/tests/test_provisioner_kubeconfig.py` and `backend/tests/test_docker_sandbox_mode_detection.py`. CI runs them on every PR.
- Manual smoke: `curl -X POST http://localhost:8002/sandboxes -d '{"thread_id":"smoke"}'`.

### Common Patterns

- Long-lived state (allocated containers, namespaces) is tracked in process memory; the service is single-replica.
- Errors are translated to actionable messages (e.g. missing `kubeconfig`, Docker daemon unreachable) rather than raw exceptions.

## Dependencies

### Internal

- `backend/packages/harness/deerflow/community/aio_sandbox/` — the client side
- `config.yaml` `sandbox` section — selects provider and provisioner URL

### External

- Docker SDK for Python (Docker mode), `kubernetes` (Kubernetes mode), FastAPI, Uvicorn

<!-- MANUAL: -->
