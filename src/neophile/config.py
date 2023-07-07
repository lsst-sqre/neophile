"""Configuration for neophile."""

from __future__ import annotations

from pydantic import BaseSettings, Field, SecretStr

__all__ = ["Config"]


class Config(BaseSettings):
    """Configuration for neophile."""

    github_app_id: str = Field("", description="GitHub App ID")

    github_private_key: SecretStr = Field(
        SecretStr(""), description="GitHub App private key"
    )

    username: str = Field(
        "neophile-square[bot]",
        description=(
            "Username, used as the name for GitHub commits and as part of"
            " the email address if `commit_email` is not set. In the latter"
            " case, must be the same as the login attribute in the GitHub"
            " users API."
        ),
    )

    commit_email: str | None = Field(
        None,
        description=(
            "Email address to use for GitHub commits. If `None`, a GitHub"
            " bot email address will be constructed using `github_app_id`."
        ),
    )

    class Config:
        env_prefix = "neophile_"
