"""Test for the Processor class."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING
from unittest.mock import call, patch

import aiohttp
import pytest
from aioresponses import CallbackResult, aioresponses
from git import PushInfo, Remote, Repo

from neophile.config import Configuration, GitHubRepository
from neophile.factory import Factory
from tests.util import register_mock_github_tags, setup_python_repo

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable


@pytest.mark.asyncio
async def test_processor(tmp_path: Path) -> None:
    tmp_repo = setup_python_repo(tmp_path / "tmp")
    upstream_path = tmp_path / "upstream"
    upstream_path.mkdir()
    Repo.init(str(upstream_path), bare=True)
    origin = tmp_repo.create_remote("origin", str(upstream_path))
    origin.push(all=True)
    shutil.rmtree(str(tmp_path / "tmp"))

    config = Configuration(
        repositories=[GitHubRepository(owner="foo", repo="bar")],
        work_area=tmp_path / "work",
    )
    user = {"name": "Someone", "email": "someone@example.com"}
    push_result = [PushInfo(PushInfo.NEW_HEAD, None, "", None)]
    created_pr = False

    def mock_clone_from(
        url: str,
        to_path: str,
        orig_clone: Callable[..., Repo] = Repo.clone_from,
        **kwargs: Any,
    ) -> Repo:
        assert url == "https://github.com/foo/bar"
        repo = orig_clone(str(upstream_path), to_path)
        repo.remotes.origin.set_url(url)
        return repo

    def check_pr_post(url: str, **kwargs: Any) -> CallbackResult:
        assert kwargs["data"]
        nonlocal created_pr
        created_pr = True
        return CallbackResult(status=201)

    with aioresponses() as mock:
        register_mock_github_tags(mock, "ambv", "black", ["20.0.0", "19.10b0"])
        mock.get("https://api.github.com/user", payload=user)
        mock.post(
            "https://api.github.com/repos/foo/bar/pulls",
            callback=check_pr_post,
        )

        # Unfortunately, the mock_push fixture can't be used here because we
        # want to use git.Remote.push above.
        async with aiohttp.ClientSession() as session:
            factory = Factory(config, session)
            processor = factory.create_processor()
            with patch.object(Repo, "clone_from", side_effect=mock_clone_from):
                with patch.object(Remote, "push") as mock_push:
                    mock_push.return_value = push_result
                    await processor.process()

    assert mock_push.call_args_list == [call("u/neophile:u/neophile")]
    assert created_pr
    repo = Repo(str(tmp_path / "work" / "bar"))
    assert not repo.is_dirty()
    assert repo.head.ref.name == "master"
    assert "tmp-neophile" not in [r.name for r in repo.remotes]
