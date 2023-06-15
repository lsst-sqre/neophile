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

__all__ = ["Factory"]


class Factory:
    """Factory to create neophile components.

    Parameters
    ----------
    http_client
        HTTP client to use for requests.
    """

    def __init__(self, http_client: AsyncClient) -> None:
        self._http_client = http_client
        self._config = Config()

    def create_analyzers(
        self, types: list[str] | None = None
    ) -> list[BaseAnalyzer]:
        """Create all analyzers.

        Parameters
        ----------
        types
            If given, only create analyzers of the given types.

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
            analyzers.append(self.create_python_analyzer())
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
        inventory = GitHubInventory(self._http_client)
        return PreCommitAnalyzer(scanner, inventory)

    def create_python_analyzer(self) -> PythonAnalyzer:
        """Create a new Python frozen dependency analyzer.

        Returns
        -------
        PythonAnalyzer
            New analyzer.
        """
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
            self.create_analyzers(types),
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
