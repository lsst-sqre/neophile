"""pytest fixtures for neophile testing."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from aiohttp import ClientSession
from git import PushInfo, Remote

if TYPE_CHECKING:
    from typing import AsyncIterator, Iterator


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


@pytest.fixture
async def session() -> AsyncIterator[ClientSession]:
    """Return an `aiohttp.ClientSession` for testing."""
    async with ClientSession() as session:
        yield session
