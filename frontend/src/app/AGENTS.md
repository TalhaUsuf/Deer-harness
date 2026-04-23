<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# app

## Purpose

Next.js App Router root. Hosts the landing page, the workspace (chat, agents, memory, auth), the public blog, the localized routes (`[lang]/docs`), API routes, and a `mock/` route group used for offline/demo scenarios.

## Key Files

| File | Description |
|------|-------------|
| `layout.tsx` | Root layout: HTML shell, providers (theme, query client), global styles |
| `page.tsx` | Landing page entry |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `[lang]/docs/` | Localized documentation routes (en, zh) |
| `api/` | Next.js Route Handlers — `auth/` (better-auth, not yet active), `memory/` |
| `blog/` | Public blog: `posts/`, `tags/`, `[[...mdxPath]]` catch-all |
| `mock/` | Mock/demo pages with `mock/api/` for stubbed responses |
| `workspace/` | Authenticated app surface: `chats/[thread_id]`, `agents/`, `memory/`, `auth/` |

## For AI Agents

### Working In This Directory

- The composer busy-state for the chat is wired in `workspace/chats/[thread_id]/page.tsx` (see `frontend/AGENTS.md` "Interaction Ownership").
- Pre-submit upload state and thread submission are owned by `core/threads/hooks.ts` — page components should consume rather than re-implement.
- API routes here are thin shims (auth callback, memory mock); business logic lives in `core/`.
- The `[lang]` segment uses Next.js dynamic route with the locale list defined in `core/i18n/`.

### Testing Requirements

- E2E coverage lives in `frontend/tests/e2e/`. Tests mock backend via `page.route()` so changes to API contracts must be reflected in the mocks.

### Common Patterns

- Server Components by default; mark interactive components with `"use client"`.
- Use `loading.tsx` and `error.tsx` files for streaming + error boundaries.

## Dependencies

### Internal

- `@/components/*`, `@/core/*`, `@/hooks/*`

### External

- Next.js 16 App Router, `next-mdx-remote` (for blog/docs), `better-auth` (planned)

<!-- MANUAL: -->
