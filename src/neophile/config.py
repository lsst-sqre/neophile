"""Configuration for neophile."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, BaseSettings, Field, SecretStr
from ruamel.yaml import YAML
from xdg import XDG_CACHE_HOME

__all__ = ["Configuration"]


class GitHubRepository(BaseModel):
    """An individual GitHub repository."""

    owner: str
    """The owner of the repository."""

    repo: str
    """The name of the repository."""


class Configuration(BaseSettings):
    """Configuration for neophile."""

    allow_expressions: bool = Field(
        False,
        description="Whether to allow version expressions in dependencies",
    )

    cache_enabled: bool = Field(
        True, description="Whether to cache inventory information"
    )

    cache_path: Path = Field(
        XDG_CACHE_HOME / "neophile", description="Path to the cache directory"
    )

    github_email: str | None = Field(
        None, description="Email address to use for GitHub commits"
    )

    github_token: SecretStr = Field(
        SecretStr(""), description="GitHub token for creating pull requests"
    )

    github_user: str = Field(
        "", description="GitHub user for creating pull requests"
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
    def from_file(cls, path: Path) -> Configuration:
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
        with path.open("r") as f:
            settings = yaml.load(f)
        return Configuration.parse_obj(settings)
