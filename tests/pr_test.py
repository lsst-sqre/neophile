"""Tests for the PullRequester class."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from unittest.mock import Mock, call, patch

import pytest
from aiohttp import ClientSession
from aioresponses import CallbackResult, aioresponses
from git import PushInfo, Remote
from git.repo import Repo
from pydantic import SecretStr

from neophile.config import Config, GitHubRepository
from neophile.exceptions import PushError
from neophile.pr import CommitMessage, PullRequester
from neophile.repository import Repository
from neophile.update.pre_commit import PreCommitUpdate

from .util import mock_enable_auto_merge, setup_python_repo


@pytest.mark.asyncio
async def test_pr(
    tmp_path: Path, session: ClientSession, mock_push: Mock
) -> None:
    repo = setup_python_repo(tmp_path)
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    config = Config(
        github_user="someone", github_token=SecretStr("some-token")
    )
    update = PreCommitUpdate(
        path=tmp_path / ".pre-commit-config.yaml",
        applied=False,
        repository="https://github.com/ambv/black",
        current="19.10b0",
        latest="23.3.0",
    )
    payload = {"name": "Someone", "email": "someone@example.com"}

    with aioresponses() as mock_responses:
        mock_responses.get("https://api.github.com/user", payload=payload)
        mock_responses.get(
            "https://api.github.com/repos/foo/bar",
            payload={"default_branch": "main"},
        )
        pattern = re.compile(
            r"https://api.github.com/repos/foo/bar/pulls\?.*base=main.*"
        )
        mock_responses.get(pattern, payload=[])
        mock_responses.post(
            "https://api.github.com/repos/foo/bar/pulls",
            payload={"number": 1},
            status=201,
        )
        mock_enable_auto_merge(mock_responses, "foo", "bar", "1")
        repository = Repository(tmp_path)
        repository.switch_branch()
        update.apply()
        pr = PullRequester(config, session)
        await pr.make_pull_request(tmp_path, [update])

    assert mock_push.call_args_list == [
        call("u/neophile:u/neophile", force=True)
    ]
    assert not repo.is_dirty()
    assert repo.head.ref.name == "u/neophile"
    commit = repo.head.commit
    assert commit.author.name == "Someone"
    assert commit.author.email == "someone@example.com"
    assert commit.committer.name == "Someone"
    assert commit.committer.email == "someone@example.com"
    change = "Update ambv/black pre-commit hook from 19.10b0 to 23.3.0"
    assert commit.message == f"{CommitMessage.title}\n\n- {change}\n"
    assert "tmp-neophile" not in [r.name for r in repo.remotes]


@pytest.mark.asyncio
async def test_pr_push_failure(tmp_path: Path, session: ClientSession) -> None:
    repo = setup_python_repo(tmp_path)
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    config = Config(
        github_user="someone", github_token=SecretStr("some-token")
    )
    update = PreCommitUpdate(
        path=tmp_path / ".pre-commit-config.yaml",
        applied=False,
        repository="https://github.com/ambv/black",
        current="19.10b0",
        latest="23.3.0",
    )
    remote = Mock(spec=Remote)
    push_error = PushInfo(
        PushInfo.ERROR, None, "", remote, summary="Some error"
    )
    user = {"name": "Someone", "email": "someone@example.com"}

    with aioresponses() as mock_responses:
        mock_responses.get("https://api.github.com/user", payload=user)
        mock_responses.get(
            "https://api.github.com/repos/foo/bar",
            payload={"default_branch": "main"},
        )
        pattern = re.compile(
            r"https://api.github.com/repos/foo/bar/pulls\?.*base=main.*"
        )
        mock_responses.get(pattern, payload=[])
        pr = PullRequester(config, session)
        with patch.object(Remote, "push") as mock:
            mock.return_value = [push_error]
            with pytest.raises(PushError) as excinfo:
                await pr.make_pull_request(tmp_path, [update])

    assert "Some error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_pr_no_automerge(
    tmp_path: Path, session: ClientSession, mock_push: Mock
) -> None:
    repo = setup_python_repo(tmp_path)
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    config = Config(
        github_user="someone", github_token=SecretStr("some-token")
    )
    update = PreCommitUpdate(
        path=tmp_path / ".pre-commit-config.yaml",
        applied=False,
        repository="https://github.com/ambv/black",
        current="19.10b0",
        latest="23.3.0",
    )
    payload = {"name": "Someone", "email": "someone@example.com"}

    with aioresponses() as mock_responses:
        mock_responses.get("https://api.github.com/user", payload=payload)
        mock_responses.get(
            "https://api.github.com/repos/foo/bar",
            payload={"default_branch": "main"},
        )
        pattern = re.compile(
            r"https://api.github.com/repos/foo/bar/pulls\?.*base=main.*"
        )
        mock_responses.get(pattern, payload=[])
        mock_responses.post(
            "https://api.github.com/repos/foo/bar/pulls",
            payload={"number": 1},
            status=201,
        )
        mock_enable_auto_merge(mock_responses, "foo", "bar", "1", fail=True)
        repository = Repository(tmp_path)
        repository.switch_branch()
        update.apply()
        pr = PullRequester(config, session)
        await pr.make_pull_request(tmp_path, [update])

    assert mock_push.call_args_list == [
        call("u/neophile:u/neophile", force=True)
    ]
    assert not repo.is_dirty()
    assert repo.head.ref.name == "u/neophile"
    commit = repo.head.commit
    assert commit.author.name == "Someone"
    assert commit.author.email == "someone@example.com"
    assert commit.committer.name == "Someone"
    assert commit.committer.email == "someone@example.com"
    change = "Update ambv/black pre-commit hook from 19.10b0 to 23.3.0"
    assert commit.message == f"{CommitMessage.title}\n\n- {change}\n"
    assert "tmp-neophile" not in [r.name for r in repo.remotes]


@pytest.mark.asyncio
async def test_pr_update(
    tmp_path: Path, session: ClientSession, mock_push: Mock
) -> None:
    """Test updating an existing PR."""
    repo = setup_python_repo(tmp_path)
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    config = Config(
        github_email="otheremail@example.com",
        github_token=SecretStr("some-token"),
        github_user="someone",
    )
    update = PreCommitUpdate(
        path=tmp_path / ".pre-commit-config.yaml",
        applied=False,
        repository="https://github.com/ambv/black",
        current="19.10b0",
        latest="23.3.0",
    )
    user = {"name": "Someone", "email": "someone@example.com"}
    updated_pr = False

    def check_pr_update(url: str, **kwargs: Any) -> CallbackResult:
        change = "Update ambv/black pre-commit hook from 19.10b0 to 23.3.0"
        assert json.loads(kwargs["data"]) == {
            "title": CommitMessage.title,
            "body": f"- {change}\n",
        }

        nonlocal updated_pr
        updated_pr = True
        return CallbackResult(status=200)

    with aioresponses() as mock_responses:
        mock_responses.get("https://api.github.com/user", payload=user)
        mock_responses.get("https://api.github.com/repos/foo/bar", payload={})
        pattern = re.compile(
            r"https://api.github.com/repos/foo/bar/pulls\?.*base=main.*"
        )
        mock_responses.get(pattern, payload=[{"number": 1234}])
        mock_responses.patch(
            "https://api.github.com/repos/foo/bar/pulls/1234",
            callback=check_pr_update,
        )
        mock_enable_auto_merge(mock_responses, "foo", "bar", "1234")

        repository = Repository(tmp_path)
        repository.switch_branch()
        update.apply()
        pr = PullRequester(config, session)
        await pr.make_pull_request(tmp_path, [update])

    assert mock_push.call_args_list == [
        call("u/neophile:u/neophile", force=True)
    ]
    assert not repo.is_dirty()
    assert repo.head.ref.name == "u/neophile"
    commit = repo.head.commit
    assert commit.author.name == "Someone"
    assert commit.author.email == "otheremail@example.com"
    assert commit.committer.name == "Someone"
    assert commit.committer.email == "otheremail@example.com"


@pytest.mark.asyncio
async def test_get_authenticated_remote(
    tmp_path: Path, session: ClientSession
) -> None:
    repo = Repo.init(str(tmp_path), initial_branch="main")

    config = Config(github_user="test", github_token=SecretStr("some-token"))
    pr = PullRequester(config, session)

    remote = Remote.create(repo, "origin", "https://github.com/foo/bar")
    url = pr._get_authenticated_remote(repo)
    assert url == "https://test:some-token@github.com/foo/bar"

    remote.set_url("https://foo@github.com:8080/foo/bar")
    url = pr._get_authenticated_remote(repo)
    assert url == "https://test:some-token@github.com:8080/foo/bar"

    remote.set_url("git@github.com:bar/foo")
    url = pr._get_authenticated_remote(repo)
    assert url == "https://test:some-token@github.com/bar/foo"

    remote.set_url("ssh://git:blahblah@github.com/baz/stuff")
    url = pr._get_authenticated_remote(repo)
    assert url == "https://test:some-token@github.com/baz/stuff"


@pytest.mark.asyncio
async def test_get_github_repo(tmp_path: Path, session: ClientSession) -> None:
    repo = Repo.init(str(tmp_path), initial_branch="main")

    config = Config(github_user="test", github_token=SecretStr("some-token"))
    pr = PullRequester(config, session)

    remote = Remote.create(repo, "origin", "git@github.com:foo/bar.git")
    github_repo = pr._get_github_repo(repo)
    assert github_repo == GitHubRepository(owner="foo", repo="bar")

    remote.set_url("https://github.com/foo/bar.git")
    github_repo = pr._get_github_repo(repo)
    assert github_repo == GitHubRepository(owner="foo", repo="bar")

    remote.set_url("ssh://git@github.com/foo/bar")
    github_repo = pr._get_github_repo(repo)
    assert github_repo == GitHubRepository(owner="foo", repo="bar")
