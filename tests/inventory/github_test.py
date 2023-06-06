"""Tests for the GitHubInventory class."""

from __future__ import annotations

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from neophile.config import Config
from neophile.inventory.github import GitHubInventory

from ..util import register_mock_github_tags


@pytest.mark.asyncio
async def test_inventory(session: ClientSession) -> None:
    tests = [
        {"tags": ["3.7.0", "3.8.0", "3.9.0", "3.8.1"], "latest": "3.9.0"},
        {"tags": ["v3.1.0", "v3.0.1", "v3.0.0", "v2.5.0"], "latest": "v3.1.0"},
        {"tags": ["4.3.20", "4.3.21-2"], "latest": "4.3.21-2"},
        {"tags": ["19.10b0", "19.3b0", "18.4a4"], "latest": "19.10b0"},
    ]

    for test in tests:
        with aioresponses() as mock:
            register_mock_github_tags(mock, "foo", "bar", test["tags"])
            inventory = GitHubInventory(Config(), session)
            latest = await inventory.inventory("foo", "bar")
        assert latest == test["latest"]


@pytest.mark.asyncio
async def test_inventory_semantic(session: ClientSession) -> None:
    tags = ["1.19.0", "1.18.0", "1.15.1", "20171120-1"]

    with aioresponses() as mock:
        register_mock_github_tags(mock, "foo", "bar", tags)
        inventory = GitHubInventory(Config(), session)
        latest = await inventory.inventory("foo", "bar")
        assert latest == "20171120-1"
        latest = await inventory.inventory("foo", "bar", semantic=True)
        assert latest == "1.19.0"


@pytest.mark.asyncio
async def test_inventory_missing(session: ClientSession) -> None:
    """Missing and empty version lists should return None."""
    with aioresponses() as mock:
        register_mock_github_tags(mock, "foo", "bar", [])
        inventory = GitHubInventory(Config(), session)
        assert await inventory.inventory("foo", "bar") is None
        assert await inventory.inventory("foo", "nonexistent") is None
