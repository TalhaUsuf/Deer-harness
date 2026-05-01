"""
app_config.py — MINIMAL STUB of `deerflow.config.app_config`.

⚠ NOT a verbatim copy. The original AppConfig is a 400-line pydantic model
that aggregates 18 sub-config modules (models, sandbox, tools, skills, MCP,
guardrails, summarization, ...). Reproducing all of that here would balloon
the standalone folder and is not needed by the 17 middlewares.

What the middlewares actually need from `get_app_config()`:
    - LLMErrorHandlingMiddleware reads `cfg.circuit_breaker.failure_threshold`
      and `cfg.circuit_breaker.recovery_timeout_sec`.
    - file_conversion.extract_outline reads `cfg.uploads.pdf_converter` (only
      relevant if you adapt the original PDF-conversion path; the stripped
      version in `_internal/file_conversion.py` does NOT call get_app_config()
      at all).

So this stub exposes ONLY `circuit_breaker`. If you wire in another config
system, point `get_app_config` at it and surface whatever extra fields your
own middlewares need.
"""

from pydantic import BaseModel, ConfigDict, Field


class CircuitBreakerConfig(BaseModel):
    """LLM circuit-breaker thresholds.

    failure_threshold: consecutive failures before opening the breaker.
    recovery_timeout_sec: how long it stays open before allowing a probe call.
    """

    failure_threshold: int = Field(default=5)
    recovery_timeout_sec: int = Field(default=60)


class AppConfig(BaseModel):
    """Stripped-down container holding only the fields used by middlewares.

    `extra="allow"` lets you load richer configs without validation errors —
    handy if you copy in a real AppConfig dict and want to keep extra keys.
    """

    model_config = ConfigDict(extra="allow", frozen=False)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)


# Module-level singleton — defaults are sensible for development. Replace
# via `set_app_config()` from your own bootstrap code.
_app_config: AppConfig = AppConfig()


def get_app_config() -> AppConfig:
    return _app_config


def set_app_config(config: AppConfig) -> None:
    """Inject a custom AppConfig (e.g. loaded from YAML in your own app)."""
    global _app_config
    _app_config = config
