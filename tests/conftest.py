"""pytest fixtures for neophile testing."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from neophile.inventory import CachedHelmInventory

if TYPE_CHECKING:
    from typing import Iterator


@pytest.yield_fixture
def cache_path(tmp_path: Path) -> Iterator[Path]:
    path = tmp_path / ".cache" / "helm.yaml"
    with patch.object(CachedHelmInventory, "_CACHE_PATH", path):
        yield path
