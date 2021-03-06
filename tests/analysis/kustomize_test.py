"""Tests for the KustomizeAnalyzer class."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from aioresponses import aioresponses

from neophile.config import Configuration
from neophile.factory import Factory
from neophile.update.kustomize import KustomizeUpdate
from tests.util import register_mock_github_tags

if TYPE_CHECKING:
    from aiohttp import ClientSession


@pytest.mark.asyncio
async def test_analyzer(session: ClientSession) -> None:
    data_path = Path(__file__).parent.parent / "data" / "kubernetes"

    with aioresponses() as mock:
        register_mock_github_tags(
            mock, "lsst-sqre", "sqrbot-jr", ["0.6.0", "0.6.1", "0.7.0"]
        )
        register_mock_github_tags(
            mock, "lsst-sqre", "sqrbot", ["20170114", "0.6.1", "0.7.0"]
        )
        factory = Factory(Configuration(), session)
        analyzer = factory.create_kustomize_analyzer(data_path)
        results = await analyzer.analyze()

    assert results == [
        KustomizeUpdate(
            path=data_path / "sqrbot-jr" / "kustomization.yaml",
            applied=False,
            url="github.com/lsst-sqre/sqrbot-jr.git//manifests/base?ref=0.6.0",
            owner="lsst-sqre",
            repo="sqrbot-jr",
            current="0.6.0",
            latest="0.7.0",
        ),
    ]


@pytest.mark.asyncio
async def test_analyzer_missing(session: ClientSession) -> None:
    """Test missing GitHub tags for all resources."""
    data_path = Path(__file__).parent.parent / "data" / "kubernetes"

    with aioresponses():
        factory = Factory(Configuration(), session)
        analyzer = factory.create_kustomize_analyzer(data_path)
        assert await analyzer.analyze() == []
