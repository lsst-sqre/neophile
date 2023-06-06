"""pre-commit dependency update."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: F401
from urllib.parse import urlparse

from ruamel.yaml import YAML

from ..exceptions import DependencyNotFoundError
from .base import Update

__all__ = ["PreCommitUpdate"]


@dataclass(order=True)
class PreCommitUpdate(Update):
    """An update to a Helm chart dependency."""

    repository: str
    """The URL of the GitHub repository providing this pre-commit hook."""

    current: str
    """The current version."""

    latest: str
    """The latest available version."""

    def apply(self) -> None:
        """Apply an update to a Helm chart.

        Raises
        ------
        DependencyNotFoundError
            Raised if the specified file doesn't contain a dependency of that
            name.
        """
        if self.applied:
            return

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        data = yaml.load(self.path)

        found = False
        for hook in data.get("repos", []):
            if hook["repo"] == self.repository:
                hook["rev"] = self.latest
                found = True
        if not found:
            raise DependencyNotFoundError(
                f"Cannot find dependency for {self.repository} in {self.path}"
            )

        with self.path.open("w") as f:
            yaml.dump(data, f)

        self.applied = True

    def description(self) -> str:
        short_repo = urlparse(self.repository).path[1:]
        return (
            f"Update {short_repo} pre-commit hook from {self.current} to"
            f" {self.latest}"
        )
