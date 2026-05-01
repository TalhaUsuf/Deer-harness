"""
memory_config.py — VERBATIM copy of `deerflow.config.memory_config`.

Used by:
    MemoryMiddleware           — checks `enabled` before queuing updates
    memory_queue.MemoryUpdateQueue — reads `debounce_seconds`

This is a tiny pydantic model with sensible defaults. Tweak fields here or
load them from your own config system by calling `set_memory_config()`.
External deps: pydantic only.
"""

from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """Configuration for the global memory mechanism."""

    enabled: bool = Field(
        default=True, description="Master switch for the memory subsystem."
    )
    storage_path: str = Field(
        default="",
        description=(
            "Path to memory.json. Empty -> defaults to {base_dir}/memory.json. "
            "Absolute paths used as-is; relative paths resolved against Paths.base_dir."
        ),
    )
    storage_class: str = Field(
        default="deerflow.agents.memory.storage.FileMemoryStorage",
        description=(
            "Class path for memory storage provider. The standalone folder does "
            "NOT inline the original FileMemoryStorage; replace with your own."
        ),
    )
    debounce_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="How long the queue waits before flushing — coalesces bursts.",
    )
    model_name: str | None = Field(
        default=None,
        description="LLM name for memory extraction. None means use the agent's default model.",
    )
    max_facts: int = Field(default=100, ge=10, le=500)
    fact_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    injection_enabled: bool = Field(
        default=True, description="Inject memory into the system prompt at turn start."
    )
    max_injection_tokens: int = Field(default=2000, ge=100, le=8000)


# Module-level singleton — start with defaults, replace via setters below.
_memory_config: MemoryConfig = MemoryConfig()


def get_memory_config() -> MemoryConfig:
    return _memory_config


def set_memory_config(config: MemoryConfig) -> None:
    global _memory_config
    _memory_config = config


def load_memory_config_from_dict(config_dict: dict) -> None:
    """Replace the singleton from a plain dict (typically loaded from YAML)."""
    global _memory_config
    _memory_config = MemoryConfig(**config_dict)
