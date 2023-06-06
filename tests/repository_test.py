"""Tests for the Repository class."""

from __future__ import annotations

from pathlib import Path

from git.repo import Repo
from git.util import Actor

from neophile.repository import Repository


def create_repo(upstream_path: Path, checkout_path: Path) -> Repo:
    """Create an upstream and downstream repository.

    Parameters
    ----------
    upstream_path : `pathlib.Path`
        Path to the upstream bare repository.
    checkout_path : `pathlib.Path`
        Path to the downstream checkout.

    Returns
    -------
    repo : `git.Repo`
        The repository for the downstream checkout.
    """
    repo = Repo.init(str(checkout_path), initial_branch="main")
    Repo.init(str(upstream_path), bare=True, initial_branch="main")
    actor = Actor("Someone", "someone@example.com")

    (checkout_path / "foo").write_text("initial contents\n")
    repo.index.add("foo")
    repo.index.commit("Initial commit", author=actor, committer=actor)
    origin = repo.create_remote("origin", str(upstream_path))
    origin.push(all=True)
    repo.heads.main.set_tracking_branch(origin.refs.main)

    return repo


def test_clone_or_update(tmp_path: Path) -> None:
    one_path = tmp_path / "one"
    two_path = tmp_path / "two"
    upstream_path = tmp_path / "upstream"
    one_repo = create_repo(upstream_path, one_path)
    actor = Actor("Someone", "someone@example.com")

    Repository.clone_or_update(two_path, str(upstream_path))
    assert (two_path / "foo").read_text() == "initial contents\n"

    (one_path / "foo").write_text("new contents\n")
    one_repo.index.add("foo")
    one_repo.index.commit("New commit", author=actor, committer=actor)
    one_repo.remotes.origin.push()

    Repository.clone_or_update(two_path, str(upstream_path))
    assert (two_path / "foo").read_text() == "new contents\n"


def test_update_dirty_repo(tmp_path: Path) -> None:
    upstream_path = tmp_path / "upstream"
    checkout_path = tmp_path / "checkout"
    repo = create_repo(upstream_path, checkout_path)

    repository = Repository(checkout_path)
    repository.switch_branch()
    (checkout_path / "foo").write_text("other garbage\n")

    # After a clone or update, the branch should not exist and the changes
    # should be unwound.
    repository = Repository.clone_or_update(checkout_path, str(upstream_path))
    assert "u/neophile" not in (h.name for h in repo.heads)
    assert (checkout_path / "foo").read_text() == "initial contents\n"
