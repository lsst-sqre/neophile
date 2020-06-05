"""Update dependencies."""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from neophile.exceptions import DependencyNotFoundError

__all__ = ["HelmUpdater"]


class HelmUpdater:
    """Update the dependencies in a Helm chart."""

    def __init__(self) -> None:
        self._yaml = YAML()
        self._yaml.indent(mapping=2, sequence=4, offset=2)

    def update(self, path: str, name: str, version: str) -> None:
        """Update a Helm dependency.

        Parameters
        ----------
        path : `str`
            The file to change.
        name : `str`
            The name of the dependency to change.
        version : `str`
            The new version of that dependency.

        Raises
        ------
        neophile.exceptions.DependencyNotFoundError
            The specified file doesn't contain a dependency of that name.
        """
        dependency_file = Path(path)
        data = self._yaml.load(dependency_file)

        found = False
        for dependency in data.get("dependencies", []):
            if dependency["name"] == name:
                dependency["version"] = version
                found = True
        if not found:
            msg = f"Cannot find dependency for {name} in {path}"
            raise DependencyNotFoundError(msg)

        with dependency_file.open("w") as f:
            self._yaml.dump(data, f)
