"""pytest fixtures for neophile testing."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from git import PushInfo, Remote
from httpx import AsyncClient


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
async def client() -> AsyncIterator[AsyncClient]:
    """Return an `httpx.AsyncClient` for testing."""
    async with AsyncClient() as client:
        yield client
