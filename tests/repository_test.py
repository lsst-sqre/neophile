"""Tests for the Repository class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from git import Actor, Repo

from neophile.repository import Repository

if TYPE_CHECKING:
    from pathlib import Path


def test_clone_or_update(tmp_path: Path) -> None:
    one_path = tmp_path / "one"
    two_path = tmp_path / "two"
    upstream_path = tmp_path / "upstream"
    one_repo = Repo.init(str(one_path))
    Repo.init(str(upstream_path), bare=True)
    actor = Actor("Someone", "someone@example.com")

    (one_path / "foo").write_text("initial contents\n")
    one_repo.index.add("foo")
    one_repo.index.commit("Initial commit", author=actor, committer=actor)
    origin = one_repo.create_remote("origin", str(upstream_path))
    origin.push(all=True)
    one_repo.heads.master.set_tracking_branch(origin.refs.master)

    Repository.clone_or_update(two_path, str(upstream_path))
    assert (two_path / "foo").read_text() == "initial contents\n"

    (one_path / "foo").write_text("new contents\n")
    one_repo.index.add("foo")
    one_repo.index.commit("New commit", author=actor, committer=actor)
    one_repo.remotes.origin.push()

    Repository.clone_or_update(two_path, str(upstream_path))
    assert (two_path / "foo").read_text() == "new contents\n"
