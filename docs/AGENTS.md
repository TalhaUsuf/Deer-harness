<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# docs

## Purpose

Project-wide documentation that lives outside the per-subtree `backend/docs/` and inline READMEs. Hosts cross-cutting summaries, design plans, and screenshot evidence attached to PRs.

## Key Files

| File | Description |
|------|-------------|
| `CODE_CHANGE_SUMMARY_BY_FILE.md` | Aggregated change log keyed by file path |
| `SKILL_NAME_CONFLICT_FIX.md` | Post-mortem / design note on the skill name collision fix |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `plans/` | Forward-looking design docs (e.g. tracing, observability rollouts) |
| `pr-evidence/` | Screenshots and artifacts attached as evidence in pull-request descriptions |

## For AI Agents

### Working In This Directory

- This directory is for **cross-cutting** docs only. Backend-specific docs (`API.md`, `ARCHITECTURE.md`, `CONFIGURATION.md`, `STREAMING.md`, etc.) live in `backend/docs/`.
- When adding a new design doc to `plans/`, use the date-prefixed convention `YYYY-MM-DD-short-name.md`.
- PR evidence images are kept here so PR descriptions can reference stable paths; do not delete without checking the linked PR.

### Common Patterns

- Markdown is the only supported format.
- Reference code locations as `path:line` so `AGENTS.md`-aware tooling can navigate.

## Dependencies

### Internal

- `backend/docs/` — backend-specific reference docs (architecture, API, streaming, etc.)
- `frontend/AGENTS.md` — frontend architecture overview

<!-- MANUAL: -->
