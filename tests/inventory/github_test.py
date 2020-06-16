"""Tests for the GitHubInventory class."""

from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
import pytest
from aioresponses import aioresponses

from neophile.config import Configuration
from neophile.inventory.github import GitHubInventory

if TYPE_CHECKING:
    from typing import Sequence


def register_mock_tags(
    mock: aioresponses, owner: str, repo: str, tags: Sequence[str]
) -> None:
    """Register a list of tags for a repository.

    Parameters
    ----------
    mock : `aioresponses.aioresponses`
        The mock object for aiohttp requests.
    repo : `str`
        The name of the GitHub repository.
    tags : List[`str`]
        The list of tags to return for that repository.
    """
    data = [{"name": version} for version in tags]
    mock.get(f"https://api.github.com/repos/{owner}/{repo}/tags", payload=data)


@pytest.mark.asyncio
async def test_inventory() -> None:
    tests = [
        {"tags": ["3.7.0", "3.8.0", "3.9.0", "3.8.1"], "latest": "3.9.0"},
        {"tags": ["v3.1.0", "v3.0.1", "v3.0.0", "v2.5.0"], "latest": "v3.1.0"},
        {"tags": ["4.3.20", "4.3.21-2"], "latest": "4.3.21-2"},
        {"tags": ["19.10b0", "19.3b0", "18.4a4"], "latest": "19.10b0"},
    ]

    for test in tests:
        with aioresponses() as mock:
            register_mock_tags(mock, "foo", "bar", test["tags"])
            async with aiohttp.ClientSession() as session:
                inventory = GitHubInventory(Configuration(), session)
                latest = await inventory.inventory("foo", "bar")
        assert latest == test["latest"]
