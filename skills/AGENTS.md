<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# skills

## Purpose

Agent skills directory consumed by the harness `Skills` subsystem (`backend/packages/harness/deerflow/skills/`). Each subdirectory is a self-contained skill bundle with its own `SKILL.md` (YAML frontmatter: `name`, `description`, `license`, `allowed-tools`). Enabled skills are surfaced in the agent's system prompt and made addressable via `/mnt/skills/...` inside the sandbox.

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `public/` | Committed, redistributable skills (21 bundles: research, design, generation, analysis) |
| `custom/` | User-installed skills, gitignored — populated by `POST /api/skills/install` |

## For AI Agents

### Working In This Directory

- **Do not** create per-skill `AGENTS.md` files. Each skill already documents itself via `SKILL.md`. Only this top-level `AGENTS.md` is needed.
- New skills should land in `public/` only if they are general-purpose, MIT-licensable, and have no proprietary dependencies. Otherwise they belong in `custom/` (or a private overlay).
- The skill name (frontmatter `name`) must be unique across `public/` and `custom/` — collisions surface in the Gateway `/api/skills` listing. See `docs/SKILL_NAME_CONFLICT_FIX.md` for the resolution strategy.
- Enabled state is **not** stored here — it lives in `extensions_config.json` under `skills.{name}.enabled`. The harness loader reads metadata from `SKILL.md` and merges enable-state from config.

### Testing Requirements

- After adding a skill, run `pytest backend/tests/test_skills.py` (if present) and verify it appears in `GET /api/skills`.
- For installable `.skill` archives (zip), validate via `POST /api/skills/install` against a dev Gateway.

### Common Patterns

- A skill bundle layout: `<name>/SKILL.md`, optional `scripts/`, `templates/`, `references/` subdirectories.
- Skills use container paths (e.g. `/mnt/skills/<name>/scripts/foo.sh`) — never absolute host paths.

## Dependencies

### Internal

- `backend/packages/harness/deerflow/skills/` — discovery and loading
- `extensions_config.json` — per-skill enable state
- `config.yaml` `skills.path` / `skills.container_path` — host vs container paths

<!-- MANUAL: -->
