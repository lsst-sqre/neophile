"""pytest fixtures for neophile testing."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientSession
from git import PushInfo, Remote


@pytest.fixture
def mock_push() -> Iterator[Mock]:
    """Mock out `git.Remote.push`.

    The mock will always return success with a status indicating that a new
    remote head was created.
    """
    with patch.object(Remote, "push") as mock:
        remote = Mock(spec=Remote)
        mock.return_value = [PushInfo(PushInfo.NEW_HEAD, None, "", remote)]
        yield mock


@pytest_asyncio.fixture
async def session() -> AsyncIterator[ClientSession]:
    """Return an `aiohttp.ClientSession` for testing."""
    async with ClientSession() as session:
        yield session
