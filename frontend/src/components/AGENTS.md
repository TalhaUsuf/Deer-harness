<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# components

## Purpose

React component library for the DeerFlow frontend. Split into auto-generated registry components (`ui/`, `ai-elements/`) and hand-written feature components (`workspace/`, `landing/`).

## Key Files

| File | Description |
|------|-------------|
| `query-client-provider.tsx` | Wraps the app in TanStack Query's `QueryClientProvider` |
| `theme-provider.tsx` | Theme switcher (light/dark/system) using CSS variables defined in `styles/` |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `ui/` | **Auto-generated** Shadcn UI primitives (Button, Dialog, Input, etc.). ESLint-ignored. Do not hand-edit. |
| `ai-elements/` | **Auto-generated** Vercel AI SDK elements (Message, Thread, etc.). ESLint-ignored. Do not hand-edit. |
| `workspace/` | Chat workspace components: `agents/`, `chats/`, `messages/`, `artifacts/`, `settings/`, `citations/` |
| `landing/` | Landing page sections (`sections/`) |

## For AI Agents

### Working In This Directory

- `ui/` and `ai-elements/` are regenerated from upstream registries (Shadcn, MagicUI, React Bits, Vercel AI SDK) via the corresponding CLI. Manual edits will be overwritten.
- Custom workspace components belong in `workspace/<feature>/`. Each feature folder typically owns its own state via hooks under `@/core/<feature>/`.
- Use `cn()` from `@/lib/utils` for conditional class names. Prefer Tailwind utility classes over CSS modules.
- For DOM-exposing components, use `forwardRef` and a typed `Props` interface declared above the component.

### Testing Requirements

- Component tests live in `frontend/tests/unit/components/`. Use React Testing Library (`@testing-library/react`).
- E2E coverage exists in `frontend/tests/e2e/` for critical workspace flows.

### Common Patterns

- One component per file; co-locate styles in the same file via Tailwind utilities.
- Props typed inline with `interface ComponentNameProps { ... }`.
- Server Components by default; only add `"use client"` when interactivity is required.

## Dependencies

### Internal

- `@/core/*` for business logic and hooks
- `@/lib/utils` for `cn()`

### External

- Shadcn UI, MagicUI, React Bits, Vercel AI SDK, `lucide-react` (icons), `clsx`, `tailwind-merge`

<!-- MANUAL: -->
