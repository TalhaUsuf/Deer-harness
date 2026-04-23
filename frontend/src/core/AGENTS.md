<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# core

## Purpose

Business logic for the DeerFlow frontend — the heart of the app. Each subdirectory owns one concern (threads, api, artifacts, memory, etc.) and exposes hooks + helpers consumed by `app/` pages and `components/` features. No UI lives here; this is pure logic + types.

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `api/` | LangGraph SDK client singleton (`getAPIClient()`), low-level HTTP helpers |
| `threads/` | Thread creation, streaming, state management; `useThreadStream`, `useSubmitThread`, `useThreads` (primary chat API) |
| `messages/` | Message processing, transformation, and streaming-event normalization |
| `artifacts/` | Artifact loading, caching, type-aware rendering helpers |
| `todos/` | Todo list state for plan-mode tasks |
| `tasks/` | Subagent task tracking (mirrors backend SSE `task_started/running/completed/failed/timed_out`) |
| `agents/` | Agent metadata, listing, selection state |
| `tools/` | Tool catalog + invocation helpers exposed to the chat surface |
| `skills/` | Skills installation and management (calls Gateway `/api/skills`) |
| `mcp/` | MCP server config viewer/editor (calls Gateway `/api/mcp/config`) |
| `models/` | TypeScript types and data-model definitions (matches Gateway response models) |
| `memory/` | Persistent user memory state (calls Gateway `/api/memory`) |
| `settings/` | User preferences in localStorage |
| `uploads/` | File upload state and conversion progress tracking |
| `notification/` | In-app toast / notification helpers |
| `i18n/` | Internationalization: `locales/` for en-US, zh-CN |
| `config/` | Frontend configuration constants |
| `streamdown/` | Custom streaming markdown renderer |
| `rehype/` | Rehype plugins (syntax highlighting, links, etc.) |
| `blog/` | Blog post loader + metadata helpers |
| `utils/` | Pure utility functions |

## For AI Agents

### Working In This Directory

- **No JSX** in this directory. UI components consume these hooks; if you find yourself needing JSX, the file belongs in `components/`.
- All API access goes through `core/api/`. Do not call `fetch()` directly from features — use the typed client.
- Thread streaming uses the LangGraph SDK's `stream(["messages-tuple", "values", "custom"])` mode; deltas are accumulated per `id` to rebuild full messages. See backend `STREAMING.md` for the wire-level invariants.
- Settings are persisted in `localStorage`; never store secrets there.
- Type-only imports use `import { type Foo }` per the lint config.

### Testing Requirements

- Unit tests live at `frontend/tests/unit/core/<feature>/<file>.test.ts`. Use Vitest with the `@/` path alias.
- For hooks, prefer `@testing-library/react`'s `renderHook`.

### Common Patterns

- One folder per feature; folder name matches the agent-facing concept (e.g. `threads/`, `skills/`).
- Public exports via a per-folder `index.ts` (barrel).
- Types co-located with their implementation; shared types in `core/models/`.

## Dependencies

### Internal

- Backend Gateway API (`/api/*`) — see `backend/app/gateway/AGENTS.md`
- Backend LangGraph server (`/api/langgraph/*`) — see `backend/CLAUDE.md`

### External

- `@langchain/langgraph-sdk`, `@langchain/core`, `@tanstack/react-query`, `zod`

<!-- MANUAL: -->
