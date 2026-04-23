<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# wizard

## Purpose

Implementation of the first-run setup wizard invoked by `scripts/setup_wizard.py`. Walks the operator through model provider selection, search tool configuration, and execution-environment choice, then writes a working `config.yaml` and `extensions_config.json`.

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | Package marker; exports the `run()` entry point |
| `providers.py` | Catalog of supported LLM providers (OpenAI, Anthropic, vLLM, Google, etc.) with required fields |
| `ui.py` | Terminal UI helpers (prompts, selects, validation) |
| `writer.py` | Renders the wizard answers into `config.yaml` / `extensions_config.json` |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `steps/` | Per-step modules (LLM, search, execution) that implement the wizard flow |

## For AI Agents

### Working In This Directory

- The wizard is **non-destructive**: it always writes to a temp file and prompts before overwriting an existing `config.yaml`.
- New providers are added by registering them in `providers.py` with their required env-var names; the renderer in `writer.py` reads from there.
- Step modules in `steps/` follow a uniform contract: each exposes `run(state) -> state` and is sequenced in `__init__.py`.

### Testing Requirements

- The wizard has no automated tests yet; smoke-test by running `python scripts/setup_wizard.py` against a clean directory.

### Common Patterns

- All user-visible strings live in `ui.py`; do not inline prompts inside step modules.
- Validation is done at the step level so the wizard can re-prompt without losing prior answers.

## Dependencies

### Internal

- `scripts/setup_wizard.py` — entry point
- `config.example.yaml` — template the writer extends from

### External

- `rich` / `prompt_toolkit` (terminal UI)

<!-- MANUAL: -->
