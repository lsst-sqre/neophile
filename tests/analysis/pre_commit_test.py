"""Tests for the PreCommitAnalyzer class."""

from __future__ import annotations

from pathlib import Path

import aiohttp
import pytest
from aioresponses import aioresponses

from neophile.factory import Factory
from neophile.update.pre_commit import PreCommitUpdate
from tests.util import register_mock_github_tags


@pytest.mark.asyncio
async def test_analyzer() -> None:
    data_path = Path(__file__).parent.parent / "data" / "python"

    with aioresponses() as mock:
        register_mock_github_tags(
            mock,
            "pre-commit",
            "pre-commit-hooks",
            ["v3.0.0", "v3.1.0", "v3.2.0"],
        )
        register_mock_github_tags(
            mock, "timothycrosley", "isort", ["4.3.21-2"]
        )
        register_mock_github_tags(mock, "ambv", "black", ["20.0.0", "19.10b0"])
        register_mock_github_tags(mock, "pycqa", "flake8", ["3.7.0", "3.9.0"])
        async with aiohttp.ClientSession() as session:
            factory = Factory(session)
            analyzer = factory.create_pre_commit_analyzer(str(data_path))
            results = await analyzer.analyze()

    pre_commit_path = data_path / ".pre-commit-config.yaml"
    assert results == [
        PreCommitUpdate(
            path=str(pre_commit_path),
            applied=False,
            repository="https://github.com/pre-commit/pre-commit-hooks",
            current="v3.1.0",
            latest="v3.2.0",
        ),
        PreCommitUpdate(
            path=str(pre_commit_path),
            applied=False,
            repository="https://github.com/ambv/black",
            current="19.10b0",
            latest="20.0.0",
        ),
        PreCommitUpdate(
            path=str(pre_commit_path),
            applied=False,
            repository="https://gitlab.com/pycqa/flake8",
            current="3.8.1",
            latest="3.9.0",
        ),
    ]
