"""Kustomize dependency update."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path  # noqa: F401

from ruamel.yaml import YAML

from ..exceptions import DependencyNotFoundError
from .base import Update

__all__ = ["KustomizeUpdate"]


@dataclass(order=True)
class KustomizeUpdate(Update):
    """An update to a Helm chart dependency."""

    url: str
    """Original URL of the resource to update."""

    owner: str
    """The owner of the referenced GitHub repository."""

    repo: str
    """The name of the referenced GitHub repository."""

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
        return (
            f"Update {self.owner}/{self.repo} Kustomize resource from"
            f" {self.current} to {self.latest}"
        )
