"""Analysis of a repository for needed updates."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import TYPE_CHECKING

from git import Repo
from semver import VersionInfo

from neophile.exceptions import UncommittedChangesError
from neophile.inventory.github import GitHubInventory
from neophile.inventory.helm import CachedHelmInventory
from neophile.scanner.helm import HelmScanner
from neophile.scanner.kustomize import KustomizeScanner
from neophile.scanner.pre_commit import PreCommitScanner
from neophile.update.helm import HelmUpdate
from neophile.update.kustomize import KustomizeUpdate
from neophile.update.pre_commit import PreCommitUpdate
from neophile.update.python import PythonFrozenUpdate

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from neophile.config import Configuration
    from neophile.update.base import Update
    from typing import List

__all__ = ["Analyzer"]


class Analyzer:
    """Analyze a tree for needed updates.

    Parameters
    ----------
    root : `str`
        Root of the directory tree to analyze.
    config : `neophile.config.Configuration`
        neophile configuration.
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
        config: Configuration,
        session: ClientSession,
        *,
        allow_expressions: bool = False,
    ) -> None:
        self._root = root
        self._config = config
        self._session = session
        self._allow_expressions = allow_expressions

    async def analyze(self) -> List[Update]:
        """Analyze a tree and return a list of needed Helm changes.

        Returns
        -------
        results : List[`neophile.update.Update`]
            A list of updates.
        """
        results = await self._analyze_helm_dependencies()
        results.extend(await self._analyze_kustomize_dependencies())
        results.extend(await self._analyze_pre_commit_dependencies())
        results.extend(self._analyze_python())
        return results

    async def _analyze_helm_dependencies(self) -> List[Update]:
        """Analyze a tree and return a list of needed Helm changes.

        Returns
        -------
        results : List[`neophile.update.base.Update`]
            A list of updates.
        """
        scanner = HelmScanner(self._root)
        dependencies = scanner.scan()
        repositories = {d.repository for d in dependencies}
        inventory = CachedHelmInventory(self._session)
        latest = {}
        for repo in repositories:
            latest[repo] = await inventory.inventory(repo)

        results: List[Update] = []
        for dependency in dependencies:
            repo = dependency.repository
            name = dependency.name
            if name not in latest[repo]:
                logging.warning(
                    "Helm chart %s not found in repository %s", name, repo
                )
                continue
            if self._helm_needs_update(dependency.version, latest[repo][name]):
                update = HelmUpdate(
                    name=name,
                    current=dependency.version,
                    latest=latest[repo][name],
                    path=dependency.path,
                )
                results.append(update)

        return results

    async def _analyze_kustomize_dependencies(self) -> List[Update]:
        """Analyze a tree and return a list of needed Kustomize changes.

        Returns
        -------
        results : List[`neophile.update.base.Update`]
            A list of updates.
        """
        scanner = KustomizeScanner(self._root)
        dependencies = scanner.scan()
        inventory = GitHubInventory(self._config, self._session)

        results: List[Update] = []
        for dependency in dependencies:
            latest = await inventory.inventory(
                dependency.owner, dependency.repo
            )
            if latest != dependency.version:
                update = KustomizeUpdate(
                    path=dependency.path,
                    url=dependency.url,
                    current=dependency.version,
                    latest=latest,
                )
                results.append(update)

        return results

    async def _analyze_pre_commit_dependencies(self) -> List[Update]:
        """Analyze pre-commit configuration.

        Returns
        -------
        results : List[`neophile.update.base.Update`]
            A list of updates.
        """
        scanner = PreCommitScanner(self._root)
        dependencies = scanner.scan()
        inventory = GitHubInventory(self._config, self._session)

        results: List[Update] = []
        for dependency in dependencies:
            latest = await inventory.inventory(
                dependency.owner, dependency.repo
            )
            if latest != dependency.version:
                update = PreCommitUpdate(
                    path=dependency.path,
                    repository=dependency.repository,
                    current=dependency.version,
                    latest=latest,
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
                    path=os.path.join(self._root, "requirements")
                )
            ]
        else:
            return []

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
