"""Configuration for neophile."""

from __future__ import annotations

from pydantic import BaseSettings, Field, SecretStr
from ruamel.yaml import YAML

__all__ = ["Configuration"]


class Configuration(BaseSettings):
    """Configuration for neophile."""

    github_user: str = Field(
        "", description="GitHub user for creating pull requests"
    )

    github_token: SecretStr = Field(
        "", description="GitHub token for creating pull requests"
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
