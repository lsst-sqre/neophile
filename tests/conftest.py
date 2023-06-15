"""pytest fixtures for neophile testing."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from git import PushInfo, Remote
from httpx import AsyncClient

__all__ = [
    "client",
    "github_key",
    "mock_push",
]


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Return an `httpx.AsyncClient` for testing."""
    async with AsyncClient() as client:
        yield client


@pytest.fixture(scope="session")
def github_key() -> str:
    """RSA private key for mock GitHub API."""
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    pem = private_key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    )
    return pem.decode()


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
