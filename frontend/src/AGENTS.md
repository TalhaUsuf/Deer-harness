<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# src

## Purpose

Source root for the DeerFlow Next.js 16 frontend. Contains the App Router pages, React components, business logic in `core/`, custom hooks, shared library helpers, server-side stubs, content (MDX), and global styles. Path alias `@/*` maps to `src/*`.

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `app/` | Next.js App Router pages, route groups (`[lang]`), API routes, mock pages (see `app/AGENTS.md`) |
| `components/` | React components: `ui/` (Shadcn primitives), `ai-elements/` (Vercel AI SDK), `workspace/`, `landing/` (see `components/AGENTS.md`) |
| `core/` | Business logic: threads, api client, artifacts, i18n, settings, memory, skills, messages, MCP, models, agents, tasks, todos, tools, uploads, utils, streamdown, rehype, blog, notification, config (see `core/AGENTS.md`) |
| `hooks/` | Shared React hooks (e.g. `usePoseStream` — passive store selector) |
| `lib/` | Utilities (`cn()` from `clsx` + `tailwind-merge`) |
| `server/` | Server-side code (`better-auth/`) — not yet active |
| `content/` | MDX content for `blog/` and localized harness/intro/tutorials/reference/application/posts under `en/` and `zh/` |
| `styles/` | Global CSS with Tailwind v4 `@import` syntax and CSS variables for theming |
| `typings/` | Ambient TypeScript declarations |

## For AI Agents

### Working In This Directory

- **Server Components by default**; add `"use client"` only for interactive components.
- **Thread hooks** (`useThreadStream`, `useSubmitThread`, `useThreads` in `core/threads/`) are the primary API surface for chat features.
- The LangGraph client is a singleton — get it via `getAPIClient()` from `core/api/`.
- `components/ui/` and `components/ai-elements/` are auto-generated from registries (Shadcn, MagicUI, React Bits, Vercel AI SDK). They are ESLint-ignored — **do not hand-edit**.
- Environment validation uses `@t3-oss/env-nextjs` with Zod (`src/env.js`); skip with `SKIP_ENV_VALIDATION=1`.

### Testing Requirements

- Unit tests live in `frontend/tests/unit/` and mirror this layout. E2E tests in `frontend/tests/e2e/` use Playwright with mocked backend.
- Run `pnpm check` before committing (lint + typecheck).

### Common Patterns

- Imports are ordered (builtin → external → internal → parent → sibling), alphabetized, with newlines between groups.
- Inline type imports: `import { type Foo } from "..."`.
- Unused variables prefixed with `_`.
- Conditional Tailwind classes via `cn()` from `@/lib/utils`.

## Dependencies

### Internal

- Backend Gateway API (`/api/*`) and LangGraph server (`/api/langgraph/*`) via Nginx proxy

### External

- Next.js 16, React 19, TypeScript 5.8, Tailwind CSS 4
- `@langchain/langgraph-sdk`, `@langchain/core`, `@tanstack/react-query`
- Shadcn UI, MagicUI, React Bits, Vercel AI SDK

<!-- MANUAL: -->
