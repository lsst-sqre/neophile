"""Configuration for neophile."""

from __future__ import annotations

from pydantic import BaseSettings, Field, SecretStr

__all__ = ["Config"]


class Config(BaseSettings):
    """Configuration for neophile."""

    github_email: str | None = Field(
        None, description="Email address to use for GitHub commits"
    )

    github_token: SecretStr = Field(
        SecretStr(""), description="GitHub token for creating pull requests"
    )

    github_user: str = Field(
        "neophile", description="GitHub user for creating pull requests"
    )

    class Config:
        env_prefix = "neophile_"
