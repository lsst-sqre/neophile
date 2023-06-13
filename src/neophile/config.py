"""Configuration for neophile."""

from __future__ import annotations

from pathlib import Path
from typing import Self

from pydantic import BaseModel, BaseSettings, Field, SecretStr
from ruamel.yaml import YAML

__all__ = [
    "Config",
    "GitHubRepository",
]


class GitHubRepository(BaseModel):
    """An individual GitHub repository."""

    owner: str
    """The owner of the repository."""

    repo: str
    """The name of the repository."""


class Config(BaseSettings):
    """Configuration for neophile."""

    github_email: str | None = Field(
        None, description="Email address to use for GitHub commits"
    )

    github_token: SecretStr = Field(
        SecretStr(""),
        description="GitHub token for creating pull requests",
        env="GITHUB_TOKEN",
    )

    github_user: str = Field(
        "neophile", description="GitHub user for creating pull requests"
    )

    repositories: list[GitHubRepository] = Field(
        default_factory=list, description="List of repositories to check"
    )

    work_area: Path = Field(
        default_factory=Path.cwd,
        description="Path to a writable working directory",
    )

    class Config:
        env_prefix = "neophile_"

    @classmethod
    def from_file(cls, path: Path) -> Self:
        """Initialize the configuration from a file.

        Parameters
        ----------
        path
            Path to a configuration file in YAML format.

        Returns
        -------
        Config
            The configuration.
        """
        yaml = YAML()
        with path.open("r") as f:
            settings = yaml.load(f)
        return cls.parse_obj(settings)
