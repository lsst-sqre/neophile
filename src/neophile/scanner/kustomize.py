"""Kustomize dependency scanning."""

from __future__ import annotations

import re
from pathlib import Path

from ruamel.yaml import YAML

from ..models.dependencies import KustomizeDependency
from .base import BaseScanner
from .util import find_files

__all__ = ["KustomizeScanner"]


class KustomizeScanner(BaseScanner):
    """Scan a source tree for Kustomize version references.

    This recognizes external resources in the formats::

       github.com/<owner>/<repo>(.git)?//<path>?ref=<version>
       https://github.com/<owner>/<repo>/<path>?ref=<version>

    Parameters
    ----------
    root
        The root of the source tree.
    """

    RESOURCE_REGEXES = [
        re.compile(r"github\.com/([^/]+)/([^/.]+).*?ref=(.*)"),
        re.compile(r"https://github\.com/([^/]+)/([^/.]+).*?ref=(.*)"),
    ]
    """The regexes to match external resources and extract data from them.

    The first match group will be the repository owner, the second match group
    will be the repository name, and the third match group will be the tag.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._yaml = YAML()

    @property
    def name(self) -> str:
        return "kustomize"

    def scan(self) -> list[KustomizeDependency]:
        """Scan a source tree for version references.

        Returns
        -------
        list of KustomizeDependency
            A list of all discovered dependencies.
        """
        dependency_paths = find_files(self._root, {"kustomization.yaml"})

        results = []
        for path in dependency_paths:
            results.extend(self._build_kustomize_dependencies(path))

        return results

    def _build_kustomize_dependencies(
        self, path: Path
    ) -> list[KustomizeDependency]:
        """Build Kustomize dependencies from a ``kustomization.yaml`` file.

        Given the path to a ``kustomization.yaml`` file, construct a list of
        all external GitHub dependencies present.

        Parameters
        ----------
        path
            Path to the ``kustomization.yaml`` file.

        Returns
        -------
        list of KustomizeDependency
            A list of all discovered Helm chart dependencies.
        """
        results = []

        with path.open() as f:
            kustomization = self._yaml.load(f)
        for resource in kustomization.get("resources", []):
            for regex in self.RESOURCE_REGEXES:
                match = regex.match(resource)
                if match:
                    break
            if not match:
                continue
            dependency = KustomizeDependency(
                url=resource,
                owner=match.group(1),
                repo=match.group(2),
                version=match.group(3),
                path=path,
            )
            results.append(dependency)

        return results
