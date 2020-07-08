"""Analysis of a repository for needed pre-commit hook updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.analysis.base import BaseAnalyzer
from neophile.update.pre_commit import PreCommitUpdate

if TYPE_CHECKING:
    from neophile.inventory.github import GitHubInventory
    from neophile.scanner.pre_commit import PreCommitScanner
    from neophile.update.base import Update
    from typing import List

__all__ = ["PreCommitAnalyzer"]


class PreCommitAnalyzer(BaseAnalyzer):
    """Analyze a tree for needed pre-commit hook updates.

    Parameters
    ----------
    root : `str`
        Root of the directory tree to analyze.
    scanner : `neophile.scanner.PreCommitScanner`
        Scanner for pre-commit hook dependencies.
    inventory : `neophile.inventory.GitHubInventory`
        Inventory for GitHub tags.
    """

    def __init__(
        self, root: str, scanner: PreCommitScanner, inventory: GitHubInventory,
    ) -> None:
        self._root = root
        self._scanner = scanner
        self._inventory = inventory

    async def analyze(self, update: bool = False) -> List[Update]:
        """Analyze a tree and return a list of needed pre-commit hook changes.

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
                dependency.owner, dependency.repo
            )
            if latest is not None and latest != dependency.version:
                pre_commit_update = PreCommitUpdate(
                    path=dependency.path,
                    applied=False,
                    repository=dependency.repository,
                    current=dependency.version,
                    latest=latest,
                )
                results.append(pre_commit_update)

        return results

    def name(self) -> str:
        return "pre-commit"
