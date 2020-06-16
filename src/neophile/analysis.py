"""Analysis of a repository for needed updates."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import TYPE_CHECKING

from git import Repo
from semver import VersionInfo

from neophile.exceptions import UncommittedChangesError
from neophile.inventory import CachedHelmInventory
from neophile.scanner import Scanner
from neophile.update import HelmUpdate, PythonFrozenUpdate

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from neophile.update import Update
    from typing import List

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
        self._root = root
        self._scanner = Scanner(root)
        self._helm_inventory = CachedHelmInventory(session)
        self._allow_expressions = allow_expressions

    async def analyze(self) -> List[Update]:
        """Analyze a tree and return a list of needed Helm changes.

        Returns
        -------
        results : List[`neophile.update.Update`]
            A list of updates.
        """
        results = await self._analyze_helm_dependencies()
        results.extend(self._analyze_python())
        return results

    async def _analyze_helm_dependencies(self) -> List[Update]:
        """Analyze a tree and return a list of needed Helm changes.

        Returns
        -------
        results : List[`neophile.update.Update`]
            A list of updates.
        """
        helm_dependencies = self._scanner.scan()
        helm_repositories = {d.repository for d in helm_dependencies}
        latest = {}
        for repo in helm_repositories:
            latest[repo] = await self._helm_inventory.inventory(repo)

        results: List[Update] = []
        for dependency in helm_dependencies:
            repo = dependency.repository
            name = dependency.name
            if name not in latest[repo]:
                logging.warning(
                    "Helm chart %s not found in repository %s", name, repo
                )
                continue
            if self._needs_update(dependency.version, latest[repo][name]):
                update = HelmUpdate(
                    name=name,
                    current=dependency.version,
                    latest=latest[repo][name],
                    path=dependency.path,
                )
                results.append(update)

        return results

    def _analyze_python(self) -> List[Update]:
        """Determine if a tree needs an update to Python frozen dependencies.

        Returns
        -------
        results : List[`neophile.update.Update`]
            Will contain either no elements (no updates needed) or a single
            element (an update needed).

        Raises
        ------
        neophile.exceptions.UncommittedChangesError
            The repository being analyzed has uncommitted changes and
            therefore cannot be checked for updates.
        subprocess.CalledProcessError
            Running ``make update-deps`` failed.
        """
        for name in ("Makefile", "requirements/main.in"):
            if not os.path.exists(os.path.join(self._root, name)):
                return []
        repo = Repo(self._root)

        if repo.is_dirty():
            msg = "Working tree contains uncommitted changes"
            raise UncommittedChangesError(msg)

        subprocess.run(
            ["make", "update-deps"],
            cwd=self._root,
            check=True,
            capture_output=True,
        )

        if repo.is_dirty():
            repo.git.restore(".")
            return [
                PythonFrozenUpdate(
                    name="python-deps",
                    path=os.path.join(self._root, "requirements"),
                )
            ]
        else:
            return []

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
        if latest_str.startswith("v"):
            latest = VersionInfo.parse(latest_str[1:])
        else:
            latest = VersionInfo.parse(latest_str)
        if VersionInfo.isvalid(current):
            return latest > current
        elif self._allow_expressions:
            return not latest.match(current)
        else:
            return True
