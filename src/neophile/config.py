"""Configuration for neophile."""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import BaseModel, BaseSettings, Field, SecretStr
from ruamel.yaml import YAML

__all__ = ["Configuration"]


class GitHubRepository(BaseModel):
    """An individual GitHub repository."""

    owner: str
    """The owner of the repository."""

    repo: str
    """The name of the repository."""


class Configuration(BaseSettings):
    """Configuration for neophile."""

    github_user: str = Field(
        "", description="GitHub user for creating pull requests"
    )

    github_token: SecretStr = Field(
        "", description="GitHub token for creating pull requests"
    )

    repositories: List[GitHubRepository] = Field(
        default_factory=list, description="List of repositories to check"
    )

    work_area: Path = Field(
        default_factory=Path.cwd,
        description="Path to a writable working directory",
    )

    class Config:
        env_prefix = "neophile_"

    @classmethod
    def from_file(cls, path: str) -> Configuration:
        """Initialize the configuration from a file.

        Parameters
        ----------
        path : `str`
            Path to a configuration file in YAML format.

        Returns
        -------
        config : `Configuration`
            The configuration.
        """
        yaml = YAML()
        with open(path, "r") as f:
            settings = yaml.load(f)
        return Configuration.parse_obj(settings)
