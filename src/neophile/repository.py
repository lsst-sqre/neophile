"""Wrapper around a Git repository."""

from __future__ import annotations

from pathlib import Path
from typing import Self

from git.repo import Repo

__all__ = ["Repository"]


class Repository:
    """Wrapper around a Git repository to add some convenience functions.

    Parameters
    ----------
    path
        Root path of the Git repository.
    """

    @classmethod
    def clone_or_update(cls, path: Path, url: str) -> Self:
        """Clone a repository or update an existing repository.

        Parameters
        ----------
        path
            Path to where the clone should be kept (and may already exist).
        url
            URL of the remote repository.

        Returns
        -------
        Repository
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
        """Switch back to the branch before switch_branch was called.

        Also deletes the neophile branch to clean up.
        """
        self._branch.checkout()
        self._repo.delete_head("u/neophile", force=True)

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
        if "main" in self._repo.heads:
            self._repo.heads["main"].checkout()
        else:
            self._repo.heads["master"].checkout()
        if "u/neophile" in (h.name for h in self._repo.heads):
            self._repo.delete_head("u/neophile", force=True)
        self._repo.git.restore(".")
        self._repo.remotes.origin.pull(ff_only=True)
