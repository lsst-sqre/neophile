"""Analysis of a repository for needed Kustomize updates."""

from __future__ import annotations

from pathlib import Path

from ..inventory.github import GitHubInventory
from ..scanner.kustomize import KustomizeScanner
from ..update.base import Update
from ..update.kustomize import KustomizeUpdate
from .base import BaseAnalyzer

__all__ = ["KustomizeAnalyzer"]


class KustomizeAnalyzer(BaseAnalyzer):
    """Analyze a tree for needed Kustomize updates.

    Parameters
    ----------
    scanner
        Scanner for Kustomize dependencies.
    inventory
        Inventory for GitHub tags.
    """

    def __init__(
        self, scanner: KustomizeScanner, inventory: GitHubInventory
    ) -> None:
        self._scanner = scanner
        self._inventory = inventory

    async def analyze(
        self, root: Path, *, update: bool = False
    ) -> list[Update]:
        """Analyze a tree and return a list of needed Kustomize changes.

        Parameters
        ----------
        root
            Root of the path to analyze.
        update
            Ignored for this analyzer.

        Returns
        -------
        list of Update
            List of needed updates.
        """
        dependencies = self._scanner.scan(root)

        results: list[Update] = []
        for dependency in dependencies:
            latest = await self._inventory.inventory(
                dependency.owner, dependency.repo, semantic=True
            )
            if latest is not None and latest != dependency.version:
                kustomize_update = KustomizeUpdate(
                    path=dependency.path,
                    applied=False,
                    url=dependency.url,
                    owner=dependency.owner,
                    repo=dependency.repo,
                    current=dependency.version,
                    latest=latest,
                )
                results.append(kustomize_update)

        return results

    @property
    def name(self) -> str:
        return "kustomize"
