"""Factory for neophile components."""

from __future__ import annotations

from httpx import AsyncClient

from .analysis.base import BaseAnalyzer
from .analysis.pre_commit import PreCommitAnalyzer
from .analysis.python import PythonAnalyzer
from .config import Config
from .inventory.github import GitHubInventory
from .pr import PullRequester
from .processor import Processor
from .scanner.base import BaseScanner
from .scanner.pre_commit import PreCommitScanner
from .virtualenv import VirtualEnv

__all__ = ["Factory"]


class Factory:
    """Factory to create neophile components.

    Parameters
    ----------
    config
        neophile configuration.
    http_client
        HTTP client to use for requests.
    """

    def __init__(self, config: Config, http_client: AsyncClient) -> None:
        self._config = config
        self._http_client = http_client

    def create_analyzers(
        self, types: list[str] | None = None, *, use_venv: bool = False
    ) -> list[BaseAnalyzer]:
        """Create all analyzers.

        Parameters
        ----------
        types
            If given, only create analyzers of the given types.
        use_venv
            Whether to use a virtualenv to isolate analysis.

        Returns
        -------
        list of BaseAnalyzer
            List of analyzers.

        Notes
        -----
        The Python analyzer requires a clean Git tree in order to determine if
        any changes were necessary, and therefore must run first if the
        analyzers are run in update mode (which means they will make changes
        to the working tree).
        """
        if not types:
            types = ["python", "pre-commit"]

        analyzers: list[BaseAnalyzer] = []
        if "python" in types:
            analyzers.append(self.create_python_analyzer(use_venv=use_venv))
        if "pre-commit" in types:
            analyzers.append(self.create_pre_commit_analyzer())
        return analyzers

    def create_all_scanners(self) -> list[BaseScanner]:
        """Create all scanners.

        Returns
        -------
        list of BaseScanner
            List of all available scanners.
        """
        return [PreCommitScanner()]

    def create_pre_commit_analyzer(self) -> PreCommitAnalyzer:
        """Create a new pre-commit hook analyzer.

        Returns
        -------
        PreCommitAnalyzer
            New analyzer.
        """
        scanner = PreCommitScanner()
        inventory = GitHubInventory(self._config, self._http_client)
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

    def create_processor(self, types: list[str] | None = None) -> Processor:
        """Create a new repository processor.

        Parameters
        ----------
        types
            If given, only process dependencies of the given types.

        Returns
        -------
        Processor
            New processor.
        """
        return Processor(
            self._config,
            self.create_analyzers(types, use_venv=True),
            self.create_pull_requester(),
        )

    def create_pull_requester(self) -> PullRequester:
        """Create a new pull requester.

        Returns
        -------
        PullRequester
            New pull requester.
        """
        return PullRequester(self._config, self._http_client)
