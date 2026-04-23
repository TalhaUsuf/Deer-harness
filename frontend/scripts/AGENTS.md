<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# scripts

## Purpose

Frontend-only build / utility scripts invoked outside the standard `pnpm` lifecycle.

## Key Files

| File | Description |
|------|-------------|
| `save-demo.js` | Captures demo screenshots / artifacts used by the marketing landing page (writes into `public/demo/`) |

## For AI Agents

### Working In This Directory

- Scripts here are Node ESM modules; run via `node frontend/scripts/<name>.js` from the repo root or `pnpm node scripts/<name>.js` from `frontend/`.
- New scripts should be referenced from `frontend/package.json` (`"scripts": { ... }`) so they are discoverable via `pnpm run`.

### Common Patterns

- Side-effecting writes go into `frontend/public/`, never into `src/`.

## Dependencies

### Internal

- `frontend/public/demo/` (output target)

### External

- Node 22+

<!-- MANUAL: -->
