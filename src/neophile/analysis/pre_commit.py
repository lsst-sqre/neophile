"""Analysis of a repository for needed pre-commit hook updates."""

from __future__ import annotations

from pathlib import Path

from ..inventory.github import GitHubInventory
from ..scanner.pre_commit import PreCommitScanner
from ..update.base import Update
from ..update.pre_commit import PreCommitUpdate
from .base import BaseAnalyzer

__all__ = ["PreCommitAnalyzer"]


class PreCommitAnalyzer(BaseAnalyzer):
    """Analyze a tree for needed pre-commit hook updates.

    Parameters
    ----------
    scanner
        Scanner for pre-commit hook dependencies.
    inventory
        Inventory for GitHub tags.
    """

    def __init__(
        self, scanner: PreCommitScanner, inventory: GitHubInventory
    ) -> None:
        self._scanner = scanner
        self._inventory = inventory

    async def analyze(
        self, root: Path, *, update: bool = False
    ) -> list[Update]:
        """Analyze a tree and return needed pre-commit hook changes.

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

    @property
    def name(self) -> str:
        return "pre-commit"
