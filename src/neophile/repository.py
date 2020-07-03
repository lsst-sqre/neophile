"""Wrapper around a Git repository."""

from __future__ import annotations

from git import Repo


class Repository:
    """Wrapper around a Git repository to add some convenience functions.

    Parameters
    ----------
    path : `str`
        Root path of the Git repository.
    """

    def __init__(self, path: str) -> None:
        self._repo = Repo(path)
        self._branch = self._repo.head.ref

    def restore_branch(self) -> None:
        """Switch back to the branch before switch_branch was called."""
        self._branch.checkout()

    def switch_branch(self) -> None:
        """Switch to the neophile working branch.

        Notes
        -----
        Currently this unconditionally creates the branch and fails if it
        already exists.  Eventually this will be smarter about updating the
        neophile branch as appropriate.
        """
        branch = self._repo.create_head("u/neophile")
        branch.checkout()
