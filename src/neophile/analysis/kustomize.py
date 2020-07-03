"""Analysis of a repository for needed Kustomize updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.analysis.base import BaseAnalyzer
from neophile.update.kustomize import KustomizeUpdate

if TYPE_CHECKING:
    from neophile.inventory.github import GitHubInventory
    from neophile.scanner.kustomize import KustomizeScanner
    from neophile.update.base import Update
    from typing import List

__all__ = ["KustomizeAnalyzer"]


class KustomizeAnalyzer(BaseAnalyzer):
    """Analyze a tree for needed Kustomize updates.

    Parameters
    ----------
    root : `str`
        Root of the directory tree to analyze.
    scanner : `neophile.scanner.KustomizeScanner`
        Scanner for Kustomize dependencies.
    inventory : `neophile.inventory.GitHubInventory`
        Inventory for GitHub tags.
    """

    def __init__(
        self, root: str, scanner: KustomizeScanner, inventory: GitHubInventory,
    ) -> None:
        self._root = root
        self._scanner = scanner
        self._inventory = inventory

    async def analyze(self, update: bool = False) -> List[Update]:
        """Analyze a tree and return a list of needed Kustomize changes.

        Parameters
        ----------
        update : `bool`, optional
            Ignored for this analyzer.

        Returns
        -------
        results : List[`neophile.update.base.Update`]
            A list of updates.
        """
        dependencies = self._scanner.scan()

        results: List[Update] = []
        for dependency in dependencies:
            latest = await self._inventory.inventory(
                dependency.owner, dependency.repo, semantic=True
            )
            if latest != dependency.version:
                kustomize_update = KustomizeUpdate(
                    path=dependency.path,
                    url=dependency.url,
                    current=dependency.version,
                    latest=latest,
                )
                results.append(kustomize_update)

        return results

    def name(self) -> str:
        return "kustomize"