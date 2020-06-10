"""Tests for the PullRequester class."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import call, patch

import aiohttp
import pytest
from aioresponses import aioresponses
from git import Actor, PushInfo, Remote, Repo

from neophile.config import Configuration
from neophile.pr import GitHubRepo, PullRequester
from neophile.update import HelmUpdate


@pytest.mark.asyncio
async def test_pr(tmp_path: Path) -> None:
    repo = Repo.init(str(tmp_path))
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    helm_path = Path(__file__).parent / "data" / "helm"
    chart_path = helm_path / "gafaelfawr" / "Chart.yaml"
    update_path = tmp_path / "Chart.yaml"
    shutil.copy(str(chart_path), str(update_path))
    repo.index.add(str(update_path))
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)
    config = Configuration(github_user="someone", github_token="some-token")

    update = HelmUpdate(
        name="gafaelfawr",
        current="1.0.0",
        latest="2.0.0",
        path=str(update_path),
    )
    payload = {"name": "Someone", "email": "someone@example.com"}
    with aioresponses() as mock_responses:
        mock_responses.get("https://api.github.com/user", payload=payload)
        mock_responses.post(
            "https://api.github.com/repos/foo/bar/pulls",
            payload={},
            status=201,
        )
        async with aiohttp.ClientSession() as session:
            pr = PullRequester(str(tmp_path), config, session)
            with patch.object(Remote, "push") as mock:
                mock.return_value = [
                    PushInfo(PushInfo.NEW_HEAD, None, "", None)
                ]
                await pr.make_pull_request([update])
                for head in repo.heads:
                    if head.name.startswith("u/neophile/"):
                        branch = head.name
                        break
                assert mock.call_args_list == [call(f"{branch}:{branch}")]

    assert not repo.is_dirty()
    assert repo.head.ref.name == "master"
    repo.heads[branch].checkout()
    commit = repo.head.commit
    assert commit.author.name == "Someone"
    assert commit.author.email == "someone@example.com"
    assert commit.committer.name == "Someone"
    assert commit.committer.email == "someone@example.com"
    change = "Update gafaelfawr Helm chart from 1.0.0 to 2.0.0"
    assert commit.message == f"Update dependencies\n\n- {change}\n"
    expected_url = "https://someone:some-token@github.com/foo/bar"
    assert repo.remotes["tmp-neophile"].url == expected_url


@pytest.mark.asyncio
async def test_get_authenticated_remote(tmp_path: Path) -> None:
    repo = Repo.init(str(tmp_path))

    config = Configuration(github_user="test", github_token="some-token")
    async with aiohttp.ClientSession() as session:
        pr = PullRequester(str(tmp_path), config, session)

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
async def test_get_github_repo(tmp_path: Path) -> None:
    repo = Repo.init(str(tmp_path))

    config = Configuration(github_user="test", github_token="some-token")
    async with aiohttp.ClientSession() as session:
        pr = PullRequester(str(tmp_path), config, session)

        remote = Remote.create(repo, "origin", "git@github.com:foo/bar.git")
        assert pr._get_github_repo() == GitHubRepo(owner="foo", repo="bar")

        remote.set_url("https://github.com/foo/bar.git")
        assert pr._get_github_repo() == GitHubRepo(owner="foo", repo="bar")

        remote.set_url("ssh://git@github.com/foo/bar")
        assert pr._get_github_repo() == GitHubRepo(owner="foo", repo="bar")
