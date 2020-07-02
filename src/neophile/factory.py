"""Factory for neophile components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.analysis.helm import HelmAnalyzer
from neophile.analysis.kustomize import KustomizeAnalyzer
from neophile.analysis.pre_commit import PreCommitAnalyzer
from neophile.analysis.python import PythonAnalyzer
from neophile.config import Configuration
from neophile.inventory.github import GitHubInventory
from neophile.inventory.helm import CachedHelmInventory
from neophile.pr import PullRequester
from neophile.scanner.helm import HelmScanner
from neophile.scanner.kustomize import KustomizeScanner
from neophile.scanner.pre_commit import PreCommitScanner

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from neophile.analysis.base import BaseAnalyzer
    from typing import List

__all__ = ["Factory"]


class Factory:
    """Factory to create neophile components.

    Parameters
    ----------
    config : `neophile.config.Configuration`
        neophile configuration.
    session : `aiohttp.ClientSession`
        The client session to use for requests.
    """

    def __init__(self, session: ClientSession) -> None:
        self._config = Configuration()
        self._session = session

    def create_all_analyzers(
        self, path: str, *, allow_expressions: bool = False
    ) -> List[BaseAnalyzer]:
        """Create a new Helm analyzer.

        Parameters
        ----------
        path : `str`
            Path to the Git repository.
        allow_expressions : `bool`, optional
            If set, allow dependencies to be expressed as expressions, and
            only report a needed update if the latest version is outside the
            range of the expression.  Defaults to false.

        Returns
        -------
        analyzers : List[`neophile.analysis.base.BaseAnalyzer`]
            List of all available analyzers.
        """
        return [
            self.create_helm_analyzer(
                path, allow_expressions=allow_expressions
            ),
            self.create_kustomize_analyzer(path),
            self.create_pre_commit_analyzer(path),
            self.create_python_analyzer(path),
        ]

    def create_helm_analyzer(
        self, path: str, *, allow_expressions: bool = False
    ) -> HelmAnalyzer:
        """Create a new Helm analyzer.

        Parameters
        ----------
        path : `str`
            Path to the Git repository.
        allow_expressions : `bool`, optional
            If set, allow dependencies to be expressed as expressions, and
            only report a needed update if the latest version is outside the
            range of the expression.  Defaults to false.

        Returns
        -------
        analyzer : `neophile.analysis.helm.HelmAnalyzer`
            New analyzer.
        """
        scanner = HelmScanner(path)
        inventory = CachedHelmInventory(self._session)
        return HelmAnalyzer(path, scanner, inventory)

    def create_kustomize_analyzer(self, path: str) -> KustomizeAnalyzer:
        """Create a new Helm analyzer.

        Parameters
        ----------
        path : `str`
            Path to the Git repository.

        Returns
        -------
        analyzer : `neophile.analysis.kustomize.KustomizeAnalyzer`
            New analyzer.
        """
        scanner = KustomizeScanner(path)
        inventory = GitHubInventory(self._config, self._session)
        return KustomizeAnalyzer(path, scanner, inventory)

    def create_pre_commit_analyzer(self, path: str) -> PreCommitAnalyzer:
        """Create a new pre-commit hook analyzer.

        Parameters
        ----------
        path : `str`
            Path to the Git repository.

        Returns
        -------
        analyzer : `neophile.analysis.pre_commit.PreCommitAnalyzer`
            New analyzer.
        """
        scanner = PreCommitScanner(path)
        inventory = GitHubInventory(self._config, self._session)
        return PreCommitAnalyzer(path, scanner, inventory)

    def create_python_analyzer(self, path: str) -> PythonAnalyzer:
        """Create a new Python frozen dependency analyzer.

        Parameters
        ----------
        path : `str`
            Path to the Git repository.

        Returns
        -------
        analyzer : `neophile.analysis.python.PythonAnalyzer`
            New analyzer.
        """
        return PythonAnalyzer(path)

    def create_pull_requester(self, path: str) -> PullRequester:
        """Create a new pull requester.

        Parameters
        ----------
        path : `str`
            Path to the Git repository.

        Returns
        -------
        pull_requester : `neophile.pr.PullRequester`
            New pull requester.
        """
        return PullRequester(path, self._config, self._session)
