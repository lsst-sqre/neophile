"""Kustomize dependency update."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ruamel.yaml import YAML

from neophile.exceptions import DependencyNotFoundError
from neophile.update.base import Update

__all__ = ["KustomizeUpdate"]


@dataclass(order=True)
class KustomizeUpdate(Update):
    """An update to a Helm chart dependency."""

    url: str
    """Original URL of the resource to update."""

    current: str
    """The current version."""

    latest: str
    """The latest available version."""

    def apply(self) -> None:
        """Apply an update to a ``kustomization.yaml`` file.

        Raises
        ------
        neophile.exceptions.DependencyNotFoundError
            The specified file doesn't contain a dependency of that name.
        """
        if self.applied:
            return

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        data = yaml.load(self.path)

        resource_to_replace = None
        for index, resource in enumerate(data.get("resources", [])):
            if resource == self.url:
                old_ref_regex = f"\\?ref={self.current}$"
                new_ref = f"?ref={self.latest}"
                new_resource = re.sub(old_ref_regex, new_ref, resource)
                resource_to_replace = index
                break
        if resource_to_replace is not None:
            data["resources"][index] = new_resource
        else:
            msg = f"Cannot find resource {self.url} in {self.path}"
            raise DependencyNotFoundError(msg)

        with self.path.open("w") as f:
            yaml.dump(data, f)

        self.applied = True

    def description(self) -> str:
        """Build a description of this update.

        Returns
        -------
        description : `str`
            Short text description of the update.
        """
        match = re.match("github.com/([^/]+/[^/.]+)", self.url)
        assert match
        name = match.group(1)
        return (
            f"Update {name} Kustomize resource from {self.current} to"
            f" {self.latest}"
        )
