"""Tests for the KustomizeAnalyzer class."""

from __future__ import annotations

from pathlib import Path

import aiohttp
import pytest
from aioresponses import aioresponses

from neophile.factory import Factory
from neophile.update.kustomize import KustomizeUpdate
from tests.util import register_mock_github_tags


@pytest.mark.asyncio
async def test_analyzer() -> None:
    datapath = Path(__file__).parent.parent / "data" / "kubernetes"

    with aioresponses() as mock:
        register_mock_github_tags(
            mock, "lsst-sqre", "sqrbot-jr", ["0.6.0", "0.6.1", "0.7.0"]
        )
        register_mock_github_tags(
            mock, "lsst-sqre", "sqrbot", ["20170114", "0.6.1", "0.7.0"]
        )
        async with aiohttp.ClientSession() as session:
            factory = Factory(session)
            analyzer = factory.create_kustomize_analyzer(str(datapath))
            results = await analyzer.analyze()

    assert results == [
        KustomizeUpdate(
            path=str(datapath / "sqrbot-jr" / "kustomization.yaml"),
            applied=False,
            url="github.com/lsst-sqre/sqrbot-jr.git//manifests/base?ref=0.6.0",
            current="0.6.0",
            latest="0.7.0",
        ),
    ]
