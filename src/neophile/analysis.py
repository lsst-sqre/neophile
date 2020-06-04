"""Analysis of a repository for needed updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from semver import VersionInfo

from neophile.inventory import HelmInventory
from neophile.scanner import Scanner

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from typing import Dict, List

__all__ = ["Analyzer"]


class Analyzer:
    """Analyze a tree for needed updates.

    Parameters
    ----------
    root : `str`
        Root of the directory tree to analyze.
    session : `aiohttp.ClientSession`
        The aiohttp client session to use to make requests for external
        information, such as Helm repository indices.
    allow_expressions : `bool`, optional
        If set, allow dependencies to be expressed as expressions, and only
        report a needed update if the latest version is outside the range of
        the expression.  Defaults to false.
    """

    def __init__(
        self,
        root: str,
        session: ClientSession,
        *,
        allow_expressions: bool = False,
    ) -> None:
        self._scanner = Scanner(root)
        self._helm_inventory = HelmInventory(session)
        self._allow_expressions = allow_expressions

    async def analyze(self) -> List[Dict[str, str]]:
        """Analyze a tree and return a list of needed changes.

        Returns
        -------
        results : List[Dict[`str`, `str`]]
            A list of change sets.  Each change set will specify a path, a
            type of dependency, the name of the dependency, the old version,
            and the new version.
        """
        helm_dependencies = self._scanner.scan()
        helm_repositories = {d["repository"] for d in helm_dependencies}
        latest = {}
        for repo in helm_repositories:
            latest[repo] = await self._helm_inventory.inventory(repo)

        results = []
        for dependency in helm_dependencies:
            repo = dependency["repository"]
            name = dependency["name"]
            if self._needs_update(dependency["version"], latest[repo][name]):
                update = {
                    "path": dependency["path"],
                    "name": name,
                    "type": dependency["type"],
                    "current": dependency["version"],
                    "latest": latest[repo][name],
                }
                results.append(update)

        return results

    def _needs_update(self, current: str, latest_str: str) -> bool:
        """Determine if a dependency needs to be updated.

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
        latest = VersionInfo.parse(latest_str)
        if VersionInfo.isvalid(current):
            return latest > current
        elif self._allow_expressions:
            return not latest.match(current)
        else:
            return True
