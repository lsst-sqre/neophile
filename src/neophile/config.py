"""Configuration for neophile."""

from __future__ import annotations

from git.util import Actor
from pydantic import BaseSettings, Field, SecretStr

__all__ = ["Config"]


class Config(BaseSettings):
    """Configuration for neophile."""

    commit_name: str = Field(
        "neophile", description="Name to use for GitHub commits"
    )

    commit_email: str | None = Field(
        None, description="Email address to use for GitHub commits"
    )

    github_app_id: str = Field("", description="GitHub App ID")

    github_private_key: SecretStr = Field(
        SecretStr(""), description="GitHub App private key"
    )

    class Config:
        env_prefix = "neophile_"

    @property
    def actor(self) -> Actor:
        """Git actor to use for commits."""
        return Actor(self.commit_name, self.commit_email)
