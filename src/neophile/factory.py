"""Factory for neophile components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.analysis.helm import HelmAnalyzer
from neophile.analysis.kustomize import KustomizeAnalyzer
from neophile.analysis.pre_commit import PreCommitAnalyzer
from neophile.analysis.python import PythonAnalyzer
from neophile.inventory.github import GitHubInventory
from neophile.inventory.helm import CachedHelmInventory
from neophile.pr import PullRequester
from neophile.processor import Processor
from neophile.scanner.helm import HelmScanner
from neophile.scanner.kustomize import KustomizeScanner
from neophile.scanner.pre_commit import PreCommitScanner

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from neophile.analysis.base import BaseAnalyzer
    from neophile.config import Configuration
    from neophile.scanner.base import BaseScanner
    from pathlib import Path
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

    def __init__(self, config: Configuration, session: ClientSession) -> None:
        self._config = config
        self._session = session

    def create_all_analyzers(
        self, path: Path, *, allow_expressions: bool = False
    ) -> List[BaseAnalyzer]:
        """Create all analyzers.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository.
        allow_expressions : `bool`, optional
            If set, allow dependencies to be expressed as expressions, and
            only report a needed update if the latest version is outside the
            range of the expression.  Defaults to false.

        Returns
        -------
        analyzers : List[`neophile.analysis.base.BaseAnalyzer`]
            List of all available analyzers.

        Notes
        -----
        The Python analyzer requires a clean Git tree in order to determine if
        any changes were necessary, and therefore must run first if the
        analyzers are run in update mode (which means they will make changes
        to the working tree).
        """
        return [
            self.create_python_analyzer(path),
            self.create_helm_analyzer(
                path, allow_expressions=allow_expressions
            ),
            self.create_kustomize_analyzer(path),
            self.create_pre_commit_analyzer(path),
        ]

    def create_all_scanners(self, path: Path) -> List[BaseScanner]:
        """Create all scanners.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository to scan.

        Returns
        -------
        scanners : List[`neophile.scanner.base.BaseScanner`]
            List of all available scanners.
        """
        return [
            HelmScanner(path),
            KustomizeScanner(path),
            PreCommitScanner(path),
        ]

    def create_helm_analyzer(
        self, path: Path, *, allow_expressions: bool = False
    ) -> HelmAnalyzer:
        """Create a new Helm analyzer.

        Parameters
        ----------
        path : `pathlib.Path`
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
        return HelmAnalyzer(scanner, inventory)

    def create_kustomize_analyzer(self, path: Path) -> KustomizeAnalyzer:
        """Create a new Helm analyzer.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository.

        Returns
        -------
        analyzer : `neophile.analysis.kustomize.KustomizeAnalyzer`
            New analyzer.
        """
        scanner = KustomizeScanner(path)
        inventory = GitHubInventory(self._config, self._session)
        return KustomizeAnalyzer(scanner, inventory)

    def create_pre_commit_analyzer(self, path: Path) -> PreCommitAnalyzer:
        """Create a new pre-commit hook analyzer.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository.

        Returns
        -------
        analyzer : `neophile.analysis.pre_commit.PreCommitAnalyzer`
            New analyzer.
        """
        scanner = PreCommitScanner(path)
        inventory = GitHubInventory(self._config, self._session)
        return PreCommitAnalyzer(scanner, inventory)

    def create_python_analyzer(self, path: Path) -> PythonAnalyzer:
        """Create a new Python frozen dependency analyzer.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository.

        Returns
        -------
        analyzer : `neophile.analysis.python.PythonAnalyzer`
            New analyzer.
        """
        return PythonAnalyzer(path)

    def create_processor(self) -> Processor:
        """Create a new repository processor."""
        return Processor(self._config, self)

    def create_pull_requester(self, path: Path) -> PullRequester:
        """Create a new pull requester.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository.

        Returns
        -------
        pull_requester : `neophile.pr.PullRequester`
            New pull requester.
        """
        return PullRequester(path, self._config, self._session)
