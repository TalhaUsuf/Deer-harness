<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# nginx

## Purpose

Nginx reverse-proxy configurations for DeerFlow's unified entry point on port 2026. Routes traffic to the frontend (`:3000`), Gateway API (`:8001`), and LangGraph server (`:2024`).

## Key Files

| File | Description |
|------|-------------|
| `nginx.conf` | Container-mode config used inside the docker stack (service-name upstreams: `frontend`, `gateway`, `langgraph`) |
| `nginx.local.conf` | Local-mode config used by `scripts/serve.sh` (localhost upstreams) |

## For AI Agents

### Working In This Directory

- Both files use `envsubst` placeholders (e.g. `${LANGGRAPH_UPSTREAM}`) so the same template works for standard mode (`langgraph:2024`) and gateway mode (`gateway:8001`).
- Routing rules:
  - `/api/langgraph/*` → LangGraph or embedded gateway runtime (mode-dependent)
  - `/api/*` → Gateway API
  - `/` → Frontend (Next.js)
- Streaming endpoints (SSE) need `proxy_buffering off` and long timeouts — preserve these directives when editing.

### Testing Requirements

- Validate syntax: `nginx -t -c $(pwd)/nginx.conf` (mount paths must resolve).
- After changes, restart with `make docker-start` (or `scripts/docker.sh restart`) and exercise streaming via the chat UI.

### Common Patterns

- Keep upstream blocks at the top of each file for easy diffing.
- Do not hard-code ports inside `location` blocks; use the upstream name.

## Dependencies

### Internal

- `docker/docker-compose.yaml`, `docker/docker-compose-dev.yaml` — mount these configs

### External

- Nginx 1.25+ (with `envsubst` available in the official image)

<!-- MANUAL: -->
