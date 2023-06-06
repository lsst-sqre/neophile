"""Helm dependency update."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: F401

from ruamel.yaml import YAML

from ..exceptions import DependencyNotFoundError
from .base import Update

__all__ = ["HelmUpdate"]


@dataclass(order=True)
class HelmUpdate(Update):
    """An update to a Helm chart dependency."""

    name: str
    """Name of the dependency."""

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
        for dependency in data.get("dependencies", []):
            if dependency["name"] == self.name:
                dependency["version"] = self.latest
                found = True
        if not found:
            msg = f"Cannot find dependency for {self.name} in {self.path}"
            raise DependencyNotFoundError(msg)

        with self.path.open("w") as f:
            yaml.dump(data, f)

        self.applied = True

    def description(self) -> str:
        return (
            f"Update {self.name} Helm chart from {self.current}"
            f" to {self.latest}"
        )
