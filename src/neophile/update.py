"""Update dependencies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML

from neophile.exceptions import DependencyNotFoundError

__all__ = [
    "HelmUpdate",
    "Update",
]


class ApplyMixin(ABC):
    """Add the abstract apply method.

    Workaround for https://github.com/python/mypy/issues/5374.
    """

    @abstractmethod
    def apply(self) -> None:
        """Apply an update.

        Raises
        ------
        neophile.exceptions.DependencyNotFoundError
            The specified file doesn't contain a dependency of that name.
        """


@dataclass(frozen=True, eq=True)
class UpdateMixin:
    """Add the base data elements for `Update`.

    Workaround for https://github.com/python/mypy/issues/5374.
    """

    name: str
    """Name of the dependency."""

    current: str
    """The current version."""

    latest: str
    """The latest available version."""

    path: str
    """The file that contains the dependency."""


class Update(UpdateMixin, ApplyMixin):
    """Base class for a needed dependency version update."""


@dataclass(frozen=True, eq=True)
class HelmUpdate(Update):
    """An update to a Helm chart dependency."""

    def apply(self) -> None:
        """Apply an update to a Helm chart.

        Raises
        ------
        neophile.exceptions.DependencyNotFoundError
            The specified file doesn't contain a dependency of that name.
        """
        dependency_file = Path(self.path)
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        data = yaml.load(dependency_file)

        found = False
        for dependency in data.get("dependencies", []):
            if dependency["name"] == self.name:
                dependency["version"] = self.latest
                found = True
        if not found:
            msg = f"Cannot find dependency for {self.name} in {self.path}"
            raise DependencyNotFoundError(msg)

        with dependency_file.open("w") as f:
            yaml.dump(data, f)
