<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# docker

## Purpose

Container orchestration assets for DeerFlow: production and dev Compose stacks, Nginx reverse-proxy configs, and the optional sandbox provisioner image. Used by `make docker-start`, `make up`, `scripts/docker.sh`, and `scripts/deploy.sh`.

## Key Files

| File | Description |
|------|-------------|
| `docker-compose.yaml` | Production stack (nginx + frontend + gateway + langgraph + optional provisioner) |
| `docker-compose-dev.yaml` | Dev stack with bind mounts for live reload |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `nginx/` | Reverse-proxy config (local + container variants) (see `nginx/AGENTS.md`) |
| `provisioner/` | FastAPI service that provisions per-thread sandboxes via Docker or Kubernetes (see `provisioner/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- The Compose stacks are launched from the project root via `scripts/docker.sh` / `scripts/deploy.sh`, not by raw `docker compose` calls. The scripts inject env vars (e.g. `DEER_FLOW_CHANNELS_LANGGRAPH_URL=http://langgraph:2024`) so service-to-service URLs work inside the network.
- IM channels run **inside the gateway container**, so localhost URLs do not work — use the service names (`langgraph`, `gateway`).
- Provisioner is started only when `sandbox.use` in `config.yaml` selects the provisioner/Kubernetes provider.
- Nginx routes differ between standard mode (`/api/langgraph/*` → langgraph:2024) and gateway mode (`/api/langgraph/*` → gateway:8001 via envsubst).

### Testing Requirements

- After modifying `docker-compose*.yaml`, validate with `docker compose -f <file> config`.
- Smoke test with `make docker-start` and `curl http://localhost:2026/health` (gateway health) and `/api/langgraph/ok` (langgraph health).

### Common Patterns

- Builds use multi-stage Dockerfiles defined in `backend/` and `frontend/` (not in this directory).
- Nginx config is rendered with `envsubst` on container start to swap routing per mode.

## Dependencies

### Internal

- `backend/Dockerfile`, `frontend/Dockerfile` — image builds
- `scripts/docker.sh`, `scripts/deploy.sh` — entrypoints
- `config.yaml`, `extensions_config.json` — bind-mounted into containers

### External

- Docker 24+, Docker Compose v2

<!-- MANUAL: -->
