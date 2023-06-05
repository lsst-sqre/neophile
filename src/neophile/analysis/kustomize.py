"""Analysis of a repository for needed Kustomize updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.analysis.base import BaseAnalyzer
from neophile.update.kustomize import KustomizeUpdate

if TYPE_CHECKING:
    from neophile.inventory.github import GitHubInventory
    from neophile.scanner.kustomize import KustomizeScanner
    from neophile.update.base import Update

__all__ = ["KustomizeAnalyzer"]


class KustomizeAnalyzer(BaseAnalyzer):
    """Analyze a tree for needed Kustomize updates.

    Parameters
    ----------
    scanner : `neophile.scanner.kustomize.KustomizeScanner`
        Scanner for Kustomize dependencies.
    inventory : `neophile.inventory.github.GitHubInventory`
        Inventory for GitHub tags.
    """

    def __init__(
        self, scanner: KustomizeScanner, inventory: GitHubInventory
    ) -> None:
        self._scanner = scanner
        self._inventory = inventory

    async def analyze(self, *, update: bool = False) -> list[Update]:
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
