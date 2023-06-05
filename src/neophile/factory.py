"""Factory for neophile components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.analysis.helm import HelmAnalyzer
from neophile.analysis.kustomize import KustomizeAnalyzer
from neophile.analysis.pre_commit import PreCommitAnalyzer
from neophile.analysis.python import PythonAnalyzer
from neophile.inventory.github import GitHubInventory
from neophile.inventory.helm import CachedHelmInventory, HelmInventory
from neophile.pr import PullRequester
from neophile.processor import Processor
from neophile.scanner.helm import HelmScanner
from neophile.scanner.kustomize import KustomizeScanner
from neophile.scanner.pre_commit import PreCommitScanner
from neophile.virtualenv import VirtualEnv

if TYPE_CHECKING:
    from pathlib import Path

    from aiohttp import ClientSession

    from neophile.analysis.base import BaseAnalyzer
    from neophile.config import Configuration
    from neophile.scanner.base import BaseScanner

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
        self, path: Path, *, use_venv: bool = False
    ) -> list[BaseAnalyzer]:
        """Create all analyzers.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository.
        use_venv : `bool`, optional
            Whether to use a virtualenv to isolate analysis.  Default is
            false.

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
            self.create_python_analyzer(path, use_venv=use_venv),
            self.create_helm_analyzer(path),
            self.create_kustomize_analyzer(path),
            self.create_pre_commit_analyzer(path),
        ]

    def create_all_scanners(self, path: Path) -> list[BaseScanner]:
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

    def create_helm_analyzer(self, path: Path) -> HelmAnalyzer:
        """Create a new Helm analyzer.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository.

        Returns
        -------
        analyzer : `neophile.analysis.helm.HelmAnalyzer`
            New analyzer.
        """
        scanner = HelmScanner(path)
        inventory = self.create_helm_inventory()
        return HelmAnalyzer(
            scanner,
            inventory,
            allow_expressions=self._config.allow_expressions,
        )

    def create_helm_inventory(self) -> HelmInventory:
        """Create a new Helm inventory.

        Uses the configuration to determine whether this should be a cached
        inventory and, if so, where to put the cache.

        Returns
        -------
        inventory : `neophile.inventory.helm.HelmInventory`
            New inventory.
        """
        if not self._config.cache_enabled:
            return HelmInventory(self._session)
        else:
            cache_path = self._config.cache_path / "helm.yaml"
            return CachedHelmInventory(self._session, cache_path)

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

    def create_python_analyzer(
        self, path: Path, *, use_venv: bool = False
    ) -> PythonAnalyzer:
        """Create a new Python frozen dependency analyzer.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the Git repository.
        use_venv : `bool`, optional
            Whether to use a virtualenv to isolate analysis.  Default is
            false.

        Returns
        -------
        analyzer : `neophile.analysis.python.PythonAnalyzer`
            New analyzer.
        """
        if use_venv:
            virtualenv = VirtualEnv(self._config.work_area / "venv")
            return PythonAnalyzer(path, virtualenv)
        else:
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
