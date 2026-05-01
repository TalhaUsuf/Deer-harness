"""
title_config.py — VERBATIM copy of `deerflow.config.title_config`.

Used by:
    TitleMiddleware — reads `enabled`, `max_words`, `max_chars`,
                      `model_name`, `prompt_template`.

External deps: pydantic only.
"""

from pydantic import BaseModel, Field


class TitleConfig(BaseModel):
    """Configuration for automatic thread title generation."""

    enabled: bool = Field(default=True)
    max_words: int = Field(default=6, ge=1, le=20)
    max_chars: int = Field(default=60, ge=10, le=200)
    model_name: str | None = Field(
        default=None,
        description="LLM name for title generation. None -> use the agent's default model.",
    )
    prompt_template: str = Field(
        default=(
            "Generate a concise title (max {max_words} words) for this conversation.\n"
            "User: {user_msg}\n"
            "Assistant: {assistant_msg}\n\n"
            "Return ONLY the title, no quotes, no explanation."
        ),
        description="Format string fed to the title LLM.",
    )


_title_config: TitleConfig = TitleConfig()


def get_title_config() -> TitleConfig:
    return _title_config


def set_title_config(config: TitleConfig) -> None:
    global _title_config
    _title_config = config


def load_title_config_from_dict(config_dict: dict) -> None:
    global _title_config
    _title_config = TitleConfig(**config_dict)
