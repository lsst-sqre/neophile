"""Analysis of a repository for needed Helm updates."""

from __future__ import annotations

import logging

from ..inventory.helm import HelmInventory
from ..inventory.version import SemanticVersion
from ..scanner.helm import HelmScanner
from ..update.base import Update
from ..update.helm import HelmUpdate
from .base import BaseAnalyzer

__all__ = ["HelmAnalyzer"]


class HelmAnalyzer(BaseAnalyzer):
    """Analyze a tree for needed Helm updates.

    Parameters
    ----------
    scanner : `neophile.scanner.helm.HelmScanner`
        Scanner for Helm dependencies.
    inventory : `neophile.inventory.helm.HelmInventory`
        Inventory for Helm repositories.
    allow_expressions : `bool`, optional
        If set, allow dependencies to be expressed as expressions, and only
        report a needed update if the latest version is outside the range of
        the expression.  Defaults to false.
    """

    def __init__(
        self,
        scanner: HelmScanner,
        inventory: HelmInventory,
        *,
        allow_expressions: bool = False,
    ) -> None:
        self._allow_expressions = allow_expressions
        self._scanner = scanner
        self._inventory = inventory

    async def analyze(self, *, update: bool = False) -> list[Update]:
        """Analyze a tree and return a list of needed Helm changes.

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
        repositories = {d.repository for d in dependencies}
        latest = {}
        for repo in repositories:
            latest[repo] = await self._inventory.inventory(repo)

        results: list[Update] = []
        for dependency in dependencies:
            repo = dependency.repository
            name = dependency.name
            if name not in latest[repo]:
                logging.warning(
                    "Helm chart %s not found in repository %s", name, repo
                )
                continue
            if self._helm_needs_update(dependency.version, latest[repo][name]):
                helm_update = HelmUpdate(
                    path=dependency.path,
                    applied=False,
                    name=name,
                    current=dependency.version,
                    latest=latest[repo][name],
                )
                results.append(helm_update)

        return results

    @property
    def name(self) -> str:
        return "helm"

    def _helm_needs_update(self, current: str, latest_str: str) -> bool:
        """Determine if a Helm dependency needs to be updated.

        Parameters
        ----------
        current : `str`
            The current version number.  If this is not a valid version number,
            it is assumed to be a match pattern.
        latest_str : `str`
            The version number of the latest release.

        Returns
        -------
        result : `bool`
            Whether this dependency should be updated.  Returns true if the
            current version is invalid or if it is older than the latest
            version.
        """
        latest = SemanticVersion.from_str(latest_str)
        if SemanticVersion.is_valid(current):
            return latest.parsed_version > current
        elif self._allow_expressions:
            return not latest.parsed_version.match(current)
        else:
            return True
