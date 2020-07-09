"""pre-commit hook dependency scanning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from typing import List

__all__ = [
    "PreCommitDependency",
    "PreCommitScanner",
]


@dataclass(frozen=True)
class PreCommitDependency:
    """Represents a single pre-commit dependency."""

    repository: str
    """The URL of the GitHub repository providing this pre-commit hook."""

    owner: str
    """The GitHub repository owner of the pre-commit hook."""

    repo: str
    """The GitHub repository name of the pre-commit hook."""

    version: str
    """The version of the dependency (may be a match pattern)."""

    path: str
    """The file that contains the dependency declaration."""


class PreCommitScanner:
    """Scan a source tree for pre-commit hook version references.

    Parameters
    ----------
    root : `str`
        The root of the source tree.
    """

    def __init__(self, root: str) -> None:
        self._root = root
        self._yaml = YAML()

    def scan(self) -> List[PreCommitDependency]:
        """Scan a source tree for pre-commit hook version references.

        Returns
        -------
        results : List[`PreCommitDependency`]
            A list of all discovered pre-commit dependencies.
        """
        path = Path(self._root) / ".pre-commit-config.yaml"
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
                path=str(path),
            )
            results.append(dependency)

        return results
