"""Wrapper around a Git repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from git import Repo

if TYPE_CHECKING:
    from pathlib import Path


class Repository:
    """Wrapper around a Git repository to add some convenience functions.

    Parameters
    ----------
    path : `str`
        Root path of the Git repository.
    """

    @classmethod
    def clone_or_update(cls, path: Path, url: str) -> Repository:
        """Clone a repository or update an existing repository.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to where the clone should be kept (and may already exist).
        url : `str`
            URL of the remote repository.

        Returns
        -------
        repo : `Repository`
            Newly-created repository object.
        """
        if path.is_dir():
            repo = cls(path)
            repo.update()
            return repo

        Repo.clone_from(url, str(path))
        return cls(path)

    def __init__(self, path: Path) -> None:
        self._repo = Repo(str(path))
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

    def update(self) -> None:
        """Update an existing checkout to its current upstream."""
        self._repo.remotes.origin.pull(ff_only=True)
