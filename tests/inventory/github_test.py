"""Tests for the GitHubInventory class."""

from __future__ import annotations

import pytest
import respx
from httpx import AsyncClient, Response

from neophile.inventory.github import GitHubInventory

from ..support.github import mock_github_tags


@pytest.mark.asyncio
async def test_inventory(
    client: AsyncClient, respx_mock: respx.Router
) -> None:
    tests = [
        {"tags": ["3.7.0", "3.8.0", "3.9.0", "3.8.1"], "latest": "3.9.0"},
        {"tags": ["v3.1.0", "v3.0.1", "v3.0.0", "v2.5.0"], "latest": "v3.1.0"},
        {"tags": ["4.3.20", "4.3.21-2"], "latest": "4.3.21-2"},
        {"tags": ["19.10b0", "19.3b0", "18.4a4"], "latest": "19.10b0"},
    ]

    for test in tests:
        mock_github_tags(respx_mock, "foo/bar", test["tags"])
        inventory = GitHubInventory(client)
        latest = await inventory.inventory("foo", "bar")
        assert latest == test["latest"]


@pytest.mark.asyncio
async def test_inventory_semantic(
    client: AsyncClient, respx_mock: respx.Router
) -> None:
    tags = ["1.19.0", "1.18.0", "1.15.1", "20171120-1"]

    mock_github_tags(respx_mock, "foo/bar", tags)
    inventory = GitHubInventory(client)
    latest = await inventory.inventory("foo", "bar")
    assert latest == "20171120-1"
    latest = await inventory.inventory("foo", "bar", semantic=True)
    assert latest == "1.19.0"


@pytest.mark.asyncio
async def test_inventory_missing(
    client: AsyncClient, respx_mock: respx.Router
) -> None:
    """Missing and empty version lists should return None."""
    mock_github_tags(respx_mock, "foo/bar", [])
    respx_mock.get("https://api.github.com/repos/foo/nonexistent/tags").mock(
        return_value=Response(404)
    )
    inventory = GitHubInventory(client)
    assert await inventory.inventory("foo", "bar") is None
    assert await inventory.inventory("foo", "nonexistent") is None
