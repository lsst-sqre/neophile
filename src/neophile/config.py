"""Configuration for neophile."""

from __future__ import annotations

from pydantic import BaseSettings, Field, SecretStr

__all__ = ["Configuration"]


class Configuration(BaseSettings):
    """Configuration for neophile."""

    github_user: str = Field(
        "",
        env="NEOPHILE_GITHUB_USER",
        description="GitHub user for creating pull requests.",
    )

    github_token: SecretStr = Field(
        "",
        env="NEOPHILE_GITHUB_TOKEN",
        description="GitHub token for creating pull requests.",
    )
