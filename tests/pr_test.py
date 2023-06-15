"""Tests for the PullRequester class."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest
import respx
from git import PushInfo, Remote
from git.repo import Repo
from httpx import AsyncClient, Request, Response
from pydantic import SecretStr

from neophile.config import Config
from neophile.exceptions import PushError
from neophile.pr import CommitMessage, GitHubRepository, PullRequester
from neophile.repository import Repository
from neophile.update.pre_commit import PreCommitUpdate

from .support.github import mock_app_authenticate, mock_enable_auto_merge
from .util import setup_python_repo


@pytest.mark.asyncio
async def test_pr(
    tmp_path: Path,
    client: AsyncClient,
    respx_mock: respx.Router,
    github_key: str,
    mock_push: Mock,
) -> None:
    repo = setup_python_repo(tmp_path)
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    config = Config(
        commit_name="Someone",
        commit_email="someone@example.com",
        github_private_key=SecretStr(github_key),
    )
    update = PreCommitUpdate(
        path=tmp_path / ".pre-commit-config.yaml",
        applied=False,
        repository="https://github.com/ambv/black",
        current="19.10b0",
        latest="23.3.0",
    )
    mock_app_authenticate(respx_mock, "foo/bar")
    respx_mock.get("https://api.github.com/repos/foo/bar").mock(
        return_value=Response(200, json={"default_branch": "main"})
    )
    pattern = r"https://api.github.com/repos/foo/bar/pulls\?.*base=main.*"
    respx_mock.get(url__regex=pattern).mock(
        return_value=Response(200, json=[])
    )
    respx_mock.post("https://api.github.com/repos/foo/bar/pulls").mock(
        return_value=Response(201, json={"number": 1})
    )
    mock_enable_auto_merge(respx_mock, "foo", "bar", "1")

    repository = Repository(tmp_path)
    repository.switch_branch()
    update.apply()
    pr = PullRequester(config, client)
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


@pytest.mark.asyncio
async def test_pr_push_failure(
    tmp_path: Path,
    client: AsyncClient,
    respx_mock: respx.Router,
    github_key: str,
) -> None:
    repo = setup_python_repo(tmp_path)
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    config = Config(github_private_key=SecretStr(github_key))
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
    mock_app_authenticate(respx_mock, "foo/bar")
    respx_mock.get("https://api.github.com/repos/foo/bar").mock(
        return_value=Response(200, json={"default_branch": "main"})
    )
    pattern = r"https://api.github.com/repos/foo/bar/pulls\?.*base=main.*"
    respx_mock.get(url__regex=pattern).mock(
        return_value=Response(200, json=[])
    )

    pr = PullRequester(config, client)
    with patch.object(Remote, "push") as mock:
        mock.return_value = [push_error]
        with pytest.raises(PushError) as excinfo:
            await pr.make_pull_request(tmp_path, [update])

    assert "Some error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_pr_no_automerge(
    tmp_path: Path,
    client: AsyncClient,
    respx_mock: respx.Router,
    github_key: str,
    mock_push: Mock,
) -> None:
    repo = setup_python_repo(tmp_path)
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    config = Config(
        commit_name="Someone",
        commit_email="someone@example.com",
        github_private_key=SecretStr(github_key),
    )
    update = PreCommitUpdate(
        path=tmp_path / ".pre-commit-config.yaml",
        applied=False,
        repository="https://github.com/ambv/black",
        current="19.10b0",
        latest="23.3.0",
    )
    mock_app_authenticate(respx_mock, "foo/bar")
    respx_mock.get("https://api.github.com/repos/foo/bar").mock(
        return_value=Response(200, json={"default_branch": "main"})
    )
    pattern = r"https://api.github.com/repos/foo/bar/pulls\?.*base=main.*"
    respx_mock.get(url__regex=pattern).mock(
        return_value=Response(200, json=[])
    )
    respx_mock.post("https://api.github.com/repos/foo/bar/pulls").mock(
        return_value=Response(201, json={"number": 1})
    )
    mock_enable_auto_merge(respx_mock, "foo", "bar", "1", fail=True)

    repository = Repository(tmp_path)
    repository.switch_branch()
    update.apply()
    pr = PullRequester(config, client)
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


@pytest.mark.asyncio
async def test_pr_update(
    tmp_path: Path,
    client: AsyncClient,
    respx_mock: respx.Router,
    github_key: str,
    mock_push: Mock,
) -> None:
    """Test updating an existing PR."""
    repo = setup_python_repo(tmp_path)
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    config = Config(
        commit_name="Someone",
        commit_email="otheremail@example.com",
        github_private_key=SecretStr(github_key),
    )
    update = PreCommitUpdate(
        path=tmp_path / ".pre-commit-config.yaml",
        applied=False,
        repository="https://github.com/ambv/black",
        current="19.10b0",
        latest="23.3.0",
    )
    updated_pr = False

    def check_pr_update(request: Request) -> Response:
        change = "Update ambv/black pre-commit hook from 19.10b0 to 23.3.0"
        assert json.loads(request.content) == {
            "title": CommitMessage.title,
            "body": f"- {change}\n",
        }

        nonlocal updated_pr
        updated_pr = True
        return Response(200)

    mock_app_authenticate(respx_mock, "foo/bar")
    respx_mock.get("https://api.github.com/repos/foo/bar").mock(
        return_value=Response(200, json={})
    )
    pattern = r"https://api.github.com/repos/foo/bar/pulls\?.*base=main.*"
    respx_mock.get(url__regex=pattern).mock(
        return_value=Response(200, json=[{"number": 1234}])
    )
    respx_mock.patch("https://api.github.com/repos/foo/bar/pulls/1234").mock(
        side_effect=check_pr_update
    )
    mock_enable_auto_merge(respx_mock, "foo", "bar", "1234")

    repository = Repository(tmp_path)
    repository.switch_branch()
    update.apply()
    pr = PullRequester(config, client)
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
async def test_get_github_repo(tmp_path: Path, client: AsyncClient) -> None:
    repo = Repo.init(str(tmp_path), initial_branch="main")
    pr = PullRequester(Config(), client)

    remote = Remote.create(repo, "origin", "git@github.com:foo/bar.git")
    github_repo = pr._get_github_repo(repo)
    assert github_repo == GitHubRepository(owner="foo", repo="bar")

    remote.set_url("https://github.com/foo/bar.git")
    github_repo = pr._get_github_repo(repo)
    assert github_repo == GitHubRepository(owner="foo", repo="bar")

    remote.set_url("ssh://git@github.com/foo/bar")
    github_repo = pr._get_github_repo(repo)
    assert github_repo == GitHubRepository(owner="foo", repo="bar")
