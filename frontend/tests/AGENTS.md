<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# tests

## Purpose

Frontend test suite. Two layers: Vitest unit tests under `unit/` (mirrors `src/` layout) and Playwright end-to-end tests under `e2e/` (Chromium, mocked backend via `page.route()`).

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `unit/` | Vitest unit tests; mirror the `src/` layout (e.g. `unit/core/api/stream-mode.test.ts` covers `src/core/api/stream-mode.ts`) |
| `e2e/` | Playwright tests; `utils/` holds shared fixtures (page setup, mock route helpers, common selectors) |

## For AI Agents

### Working In This Directory

- **Unit tests** import source modules via the `@/` path alias. Mock external services; never hit a real backend.
- **E2E tests** use Playwright with Chromium. Mock all backend APIs via `page.route()` — see `playwright.config.ts` (`frontend/playwright.config.ts`).
- Add a unit test for every new `core/` module and a Vitest test for every new component with non-trivial behavior.
- For new e2e flows, add a single happy-path scenario plus the most likely error path.

### Testing Requirements

- Run unit tests: `pnpm test`
- Run e2e tests: `pnpm test:e2e`
- Both must pass before merging; CI enforces this via `.github/workflows/frontend-unit-tests.yml` and `e2e-tests.yml`.

### Common Patterns

- One file per `src/` module under test; filename ends in `.test.ts` or `.test.tsx`.
- Use `describe(...)` blocks per public function or component.
- For streaming tests, push events via a `MockReadableStream` helper rather than real SSE.

## Dependencies

### Internal

- `src/*` (subject under test)

### External

- Vitest, `@testing-library/react`, `@testing-library/user-event`, Playwright

<!-- MANUAL: -->
