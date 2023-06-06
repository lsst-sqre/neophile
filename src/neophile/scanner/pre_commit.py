"""pre-commit hook dependency scanning."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from ruamel.yaml import YAML

from ..models.dependencies import PreCommitDependency
from .base import BaseScanner

__all__ = ["PreCommitScanner"]


class PreCommitScanner(BaseScanner):
    """Scan a source tree for pre-commit hook version references.

    Parameters
    ----------
    root : `pathlib.Path`
        The root of the source tree.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._yaml = YAML()

    @property
    def name(self) -> str:
        return "pre-commit"

    def scan(self) -> list[PreCommitDependency]:
        """Scan a source tree for pre-commit hook version references.

        Returns
        -------
        list of PreCommitDependency
            A list of all discovered pre-commit dependencies.
        """
        path = self._root / ".pre-commit-config.yaml"
        if not path.exists():
            return []
        results = []

        with path.open() as f:
            config = self._yaml.load(f)
        for hook in config.get("repos", []):
            path_components = urlparse(hook["repo"]).path[1:].split("/")
            dependency = PreCommitDependency(
                repository=hook["repo"],
                owner=path_components[0],
                repo=path_components[1],
                version=hook["rev"],
                path=path,
            )
            results.append(dependency)

        return results
