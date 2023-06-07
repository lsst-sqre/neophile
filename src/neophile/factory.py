"""Factory for neophile components."""

from __future__ import annotations

from aiohttp import ClientSession

from .analysis.base import BaseAnalyzer
from .analysis.helm import HelmAnalyzer
from .analysis.kustomize import KustomizeAnalyzer
from .analysis.pre_commit import PreCommitAnalyzer
from .analysis.python import PythonAnalyzer
from .config import Config
from .inventory.github import GitHubInventory
from .inventory.helm import CachedHelmInventory, HelmInventory
from .pr import PullRequester
from .processor import Processor
from .scanner.base import BaseScanner
from .scanner.helm import HelmScanner
from .scanner.kustomize import KustomizeScanner
from .scanner.pre_commit import PreCommitScanner
from .virtualenv import VirtualEnv

__all__ = ["Factory"]


class Factory:
    """Factory to create neophile components.

    Parameters
    ----------
    config
        neophile configuration.
    session
        The client session to use for requests.
    """

    def __init__(self, config: Config, session: ClientSession) -> None:
        self._config = config
        self._session = session

    def create_all_analyzers(
        self, *, use_venv: bool = False
    ) -> list[BaseAnalyzer]:
        """Create all analyzers.

        Parameters
        ----------
        use_venv
            Whether to use a virtualenv to isolate analysis.

        Returns
        -------
        list of BaseAnalyzer
            List of all available analyzers.

        Notes
        -----
        The Python analyzer requires a clean Git tree in order to determine if
        any changes were necessary, and therefore must run first if the
        analyzers are run in update mode (which means they will make changes
        to the working tree).
        """
        return [
            self.create_python_analyzer(use_venv=use_venv),
            self.create_helm_analyzer(),
            self.create_kustomize_analyzer(),
            self.create_pre_commit_analyzer(),
        ]

    def create_all_scanners(self) -> list[BaseScanner]:
        """Create all scanners.

        Returns
        -------
        list of BaseScanner
            List of all available scanners.
        """
        return [
            HelmScanner(),
            KustomizeScanner(),
            PreCommitScanner(),
        ]

    def create_helm_analyzer(self) -> HelmAnalyzer:
        """Create a new Helm analyzer.

        Returns
        -------
        HelmAnalyzer
            New analyzer.
        """
        return HelmAnalyzer(
            HelmScanner(),
            self.create_helm_inventory(),
            allow_expressions=self._config.allow_expressions,
        )

    def create_helm_inventory(self) -> HelmInventory:
        """Create a new Helm inventory.

        Uses the configuration to determine whether this should be a cached
        inventory and, if so, where to put the cache.

        Returns
        -------
        HelmInventory
            New inventory.
        """
        if not self._config.cache_enabled:
            return HelmInventory(self._session)
        else:
            cache_path = self._config.cache_path / "helm.yaml"
            return CachedHelmInventory(self._session, cache_path)

    def create_kustomize_analyzer(self) -> KustomizeAnalyzer:
        """Create a new Helm analyzer.

        Returns
        -------
        KustomizeAnalyzer
            New analyzer.
        """
        scanner = KustomizeScanner()
        inventory = GitHubInventory(self._config, self._session)
        return KustomizeAnalyzer(scanner, inventory)

    def create_pre_commit_analyzer(self) -> PreCommitAnalyzer:
        """Create a new pre-commit hook analyzer.

        Returns
        -------
        PreCommitAnalyzer
            New analyzer.
        """
        scanner = PreCommitScanner()
        inventory = GitHubInventory(self._config, self._session)
        return PreCommitAnalyzer(scanner, inventory)

    def create_python_analyzer(
        self, *, use_venv: bool = False
    ) -> PythonAnalyzer:
        """Create a new Python frozen dependency analyzer.

        Parameters
        ----------
        use_venv
            Whether to use a virtualenv to isolate analysis.

        Returns
        -------
        PythonAnalyzer
            New analyzer.
        """
        if use_venv:
            virtualenv = VirtualEnv(self._config.work_area / "venv")
            return PythonAnalyzer(virtualenv)
        else:
            return PythonAnalyzer()

    def create_processor(self) -> Processor:
        """Create a new repository processor.

        Parameters
        ----------
        use_venv
            Whether to use a virtualenv to isolate analysis.

        Returns
        -------
        Processor
            New processor.
        """
        return Processor(
            self._config,
            self.create_all_analyzers(use_venv=True),
            self.create_pull_requester(),
        )

    def create_pull_requester(self) -> PullRequester:
        """Create a new pull requester.

        Returns
        -------
        PullRequester
            New pull requester.
        """
        return PullRequester(self._config, self._session)
