"""Tests for the PullRequester class."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import call, patch

import pytest
from aioresponses import CallbackResult, aioresponses
from git import Actor, PushInfo, Remote, Repo

from neophile.config import Configuration
from neophile.exceptions import PushError
from neophile.pr import CommitMessage, GitHubRepo, PullRequester
from neophile.repository import Repository
from neophile.update.helm import HelmUpdate

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from typing import Any
    from unittest.mock import Mock


def setup_repo(tmp_path: Path) -> Repo:
    """Set up a repository with the Gafaelfawr Helm chart."""
    repo = Repo.init(str(tmp_path))
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    helm_path = Path(__file__).parent / "data" / "kubernetes"
    chart_path = helm_path / "gafaelfawr" / "Chart.yaml"
    update_path = tmp_path / "Chart.yaml"
    shutil.copy(str(chart_path), str(update_path))
    repo.index.add(str(update_path))
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)
    return repo


@pytest.mark.asyncio
async def test_pr(
    tmp_path: Path, session: ClientSession, mock_push: Mock
) -> None:
    repo = setup_repo(tmp_path)
    config = Configuration(github_user="someone", github_token="some-token")
    update = HelmUpdate(
        path=tmp_path / "Chart.yaml",
        applied=False,
        name="gafaelfawr",
        current="1.0.0",
        latest="2.0.0",
    )
    payload = {"name": "Someone", "email": "someone@example.com"}

    with aioresponses() as mock_responses:
        mock_responses.get("https://api.github.com/user", payload=payload)
        pattern = re.compile(r"https://api.github.com/repos/foo/bar/pulls\?.*")
        mock_responses.get(pattern, payload=[])
        mock_responses.post(
            "https://api.github.com/repos/foo/bar/pulls",
            payload={},
            status=201,
        )
        repository = Repository(tmp_path)
        repository.switch_branch()
        update.apply()
        pr = PullRequester(tmp_path, config, session)
        await pr.make_pull_request([update])

    assert mock_push.call_args_list == [call("u/neophile:u/neophile")]
    assert not repo.is_dirty()
    assert repo.head.ref.name == "u/neophile"
    commit = repo.head.commit
    assert commit.author.name == "Someone"
    assert commit.author.email == "someone@example.com"
    assert commit.committer.name == "Someone"
    assert commit.committer.email == "someone@example.com"
    change = "Update gafaelfawr Helm chart from 1.0.0 to 2.0.0"
    assert commit.message == f"{CommitMessage.title}\n\n- {change}\n"
    assert "tmp-neophile" not in [r.name for r in repo.remotes]


@pytest.mark.asyncio
async def test_pr_push_failure(tmp_path: Path, session: ClientSession) -> None:
    setup_repo(tmp_path)
    config = Configuration(github_user="someone", github_token="some-token")
    update = HelmUpdate(
        path=tmp_path / "Chart.yaml",
        applied=False,
        name="gafaelfawr",
        current="1.0.0",
        latest="2.0.0",
    )
    push_error = PushInfo(PushInfo.ERROR, None, "", None, summary="Some error")
    user = {"name": "Someone", "email": "someone@example.com"}

    with aioresponses() as mock_responses:
        mock_responses.get("https://api.github.com/user", payload=user)
        pattern = re.compile(r"https://api.github.com/repos/foo/bar/pulls\?.*")
        mock_responses.get(pattern, payload=[])
        pr = PullRequester(tmp_path, config, session)
        with patch.object(Remote, "push") as mock:
            mock.return_value = [push_error]
            with pytest.raises(PushError) as excinfo:
                await pr.make_pull_request([update])

    assert "Some error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_pr_update(
    tmp_path: Path, session: ClientSession, mock_push: Mock
) -> None:
    """Test updating an existing PR."""
    repo = setup_repo(tmp_path)
    config = Configuration(github_user="someone", github_token="some-token")
    update = HelmUpdate(
        path=tmp_path / "Chart.yaml",
        applied=False,
        name="gafaelfawr",
        current="1.0.0",
        latest="2.0.0",
    )
    user = {"name": "Someone", "email": "someone@example.com"}
    updated_pr = False

    def check_pr_update(url: str, **kwargs: Any) -> CallbackResult:
        change = "Update gafaelfawr Helm chart from 1.0.0 to 2.0.0"
        assert json.loads(kwargs["data"]) == {
            "title": CommitMessage.title,
            "body": f"- {change}\n",
        }

        nonlocal updated_pr
        updated_pr = True
        return CallbackResult(status=200)

    with aioresponses() as mock_responses:
        mock_responses.get("https://api.github.com/user", payload=user)
        pattern = re.compile(r"https://api.github.com/repos/foo/bar/pulls\?.*")
        mock_responses.get(pattern, payload=[{"number": "1234"}])
        mock_responses.patch(
            "https://api.github.com/repos/foo/bar/pulls/1234",
            callback=check_pr_update,
        )
        repository = Repository(tmp_path)
        repository.switch_branch()
        update.apply()
        pr = PullRequester(tmp_path, config, session)
        await pr.make_pull_request([update])

    assert mock_push.call_args_list == [call("u/neophile:u/neophile")]
    assert not repo.is_dirty()
    assert repo.head.ref.name == "u/neophile"


@pytest.mark.asyncio
async def test_get_authenticated_remote(
    tmp_path: Path, session: ClientSession
) -> None:
    repo = Repo.init(str(tmp_path))

    config = Configuration(github_user="test", github_token="some-token")
    pr = PullRequester(tmp_path, config, session)

    remote = Remote.create(repo, "origin", "https://github.com/foo/bar")
    url = pr._get_authenticated_remote()
    assert url == "https://test:some-token@github.com/foo/bar"

    remote.set_url("https://foo@github.com:8080/foo/bar")
    url = pr._get_authenticated_remote()
    assert url == "https://test:some-token@github.com:8080/foo/bar"

    remote.set_url("git@github.com:bar/foo")
    url = pr._get_authenticated_remote()
    assert url == "https://test:some-token@github.com/bar/foo"

    remote.set_url("ssh://git:blahblah@github.com/baz/stuff")
    url = pr._get_authenticated_remote()
    assert url == "https://test:some-token@github.com/baz/stuff"


@pytest.mark.asyncio
async def test_get_github_repo(tmp_path: Path, session: ClientSession) -> None:
    repo = Repo.init(str(tmp_path))

    config = Configuration(github_user="test", github_token="some-token")
    pr = PullRequester(tmp_path, config, session)

    remote = Remote.create(repo, "origin", "git@github.com:foo/bar.git")
    assert pr._get_github_repo() == GitHubRepo(owner="foo", repo="bar")

    remote.set_url("https://github.com/foo/bar.git")
    assert pr._get_github_repo() == GitHubRepo(owner="foo", repo="bar")

    remote.set_url("ssh://git@github.com/foo/bar")
    assert pr._get_github_repo() == GitHubRepo(owner="foo", repo="bar")
