<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# docs

## Purpose

Backend reference documentation. Architecture, API surface, configuration, subsystem deep-dives, RFCs, and implementation summaries. Cross-cutting docs (PR evidence, project-wide plans) live in the root `docs/` directory; everything backend-specific lives here.

## Key Files

| File | Description |
|------|-------------|
| `README.md` | Index of backend docs |
| `ARCHITECTURE.md` | High-level architecture overview |
| `API.md` | Gateway REST API reference |
| `SETUP.md` | Backend setup walkthrough |
| `CONFIGURATION.md` | `config.yaml` and `extensions_config.json` reference |
| `STREAMING.md` | LangGraph streaming design (per-id dedup, modes, parallel paths between Gateway and `DeerFlowClient`) |
| `HARNESS_APP_SPLIT.md` | The harness/app dependency boundary, rationale, enforcement |
| `MCP_SERVER.md` | MCP integration: transports, OAuth, lazy loading, cache invalidation |
| `GUARDRAILS.md` | Pre-tool-call authorization providers and how to implement custom ones |
| `FILE_UPLOAD.md` | Multi-file upload + automatic conversion (PDF/PPT/Excel/Word via markitdown) |
| `MEMORY_IMPROVEMENTS.md` / `MEMORY_IMPROVEMENTS_SUMMARY.md` / `MEMORY_SETTINGS_REVIEW.md` | Memory subsystem design and tuning notes |
| `memory-settings-sample.json` | Reference memory configuration |
| `summarization.md` | Context summarization configuration and triggers |
| `plan_mode_usage.md` | TodoList middleware (`is_plan_mode`) usage |
| `AUTO_TITLE_GENERATION.md` / `TITLE_GENERATION_IMPLEMENTATION.md` | Auto-title middleware design and implementation |
| `PATH_EXAMPLES.md` | Virtual-path / host-path translation examples |
| `APPLE_CONTAINER.md` | macOS container runtime notes |
| `middleware-execution-flow.md` | Middleware ordering and runtime flow |
| `task_tool_improvements.md` | Subagent `task` tool design notes |
| `TODO.md` | Open work items |
| `rfc-create-deerflow-agent.md` | RFC: agent-creation API |
| `rfc-extract-shared-modules.md` | RFC: shared module extraction |
| `rfc-grep-glob-tools.md` | RFC: grep/glob sandbox tools |

## For AI Agents

### Working In This Directory

- **Documentation update policy** (per `backend/CLAUDE.md`): when changing backend code, update the relevant doc here. Keep `CLAUDE.md` synchronized.
- New design proposals go in `rfc-*.md` files; once accepted, fold the canonical content into `ARCHITECTURE.md` or a dedicated subsystem doc.
- Do not move user-facing setup docs here — those belong in the root `README.md` / `Install.md`.

### Common Patterns

- Markdown only; reference code as `path:line`.
- Long-form designs use a Status header (Draft / Accepted / Implemented / Superseded).

## Dependencies

### Internal

- All backend subsystems (this directory documents them)
- Root `docs/` for cross-cutting plans and PR evidence

<!-- MANUAL: -->
