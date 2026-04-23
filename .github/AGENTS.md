<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# .github

## Purpose

GitHub-specific configuration: CI workflows, issue templates, and Copilot guidance.

## Key Files

| File | Description |
|------|-------------|
| `copilot-instructions.md` | Repository-wide instructions surfaced to GitHub Copilot |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `workflows/` | GitHub Actions CI: backend unit tests, frontend unit tests, e2e, lint |
| `ISSUE_TEMPLATE/` | Structured issue forms (currently `runtime-information.yml`) |

## For AI Agents

### Working In This Directory

- CI workflows in `workflows/`:
  - `backend-unit-tests.yml` — runs `make test` against the backend, including the harness/app boundary check
  - `frontend-unit-tests.yml` — runs `pnpm test` (Vitest)
  - `e2e-tests.yml` — Playwright/Chromium e2e against a mocked backend
  - `lint-check.yml` — ruff (backend) + ESLint/Prettier (frontend)
- Workflows pin tool versions (Python, Node, pnpm, uv); update both root `Makefile` requirements and these pins together.
- Issue templates use the GitHub Forms YAML schema; validate locally with the [GitHub schema linter](https://github.com/github/github-issue-form-schemas) before committing.

### Common Patterns

- Use `paths-filter` style triggers so backend changes do not run frontend CI and vice versa (where applicable).
- Cache keys include lockfile hashes (`uv.lock`, `pnpm-lock.yaml`).

## Dependencies

### Internal

- `backend/Makefile`, `frontend/package.json` — invoked by workflows
- `backend/tests/test_harness_boundary.py` — boundary check enforced in CI

### External

- GitHub Actions runners (`ubuntu-latest`)

<!-- MANUAL: -->
