"""Tests for the PreCommitAnalyzer class."""

from __future__ import annotations

from pathlib import Path

import pytest
import respx
from httpx import AsyncClient

from neophile.factory import Factory
from neophile.update.pre_commit import PreCommitUpdate

from ..support.github import mock_github_tags


@pytest.mark.asyncio
async def test_analyzer(client: AsyncClient, respx_mock: respx.Router) -> None:
    data_path = Path(__file__).parent.parent / "data" / "python"
    pre_commit_path = data_path / ".pre-commit-config.yaml"
    mock_github_tags(
        respx_mock,
        "pre-commit/pre-commit-hooks",
        ["v3.0.0", "v3.1.0", "v3.2.0"],
    )
    mock_github_tags(respx_mock, "timothycrosley/isort", ["4.3.21-2"])
    mock_github_tags(respx_mock, "ambv/black", ["20.0.0", "19.10b0"])
    mock_github_tags(respx_mock, "pycqa/flake8", ["3.7.0", "3.9.0"])

    factory = Factory(client)
    analyzer = factory.create_pre_commit_analyzer()
    results = await analyzer.analyze(data_path)

    assert results == [
        PreCommitUpdate(
            path=pre_commit_path,
            applied=False,
            repository="https://github.com/pre-commit/pre-commit-hooks",
            current="v3.1.0",
            latest="v3.2.0",
        ),
        PreCommitUpdate(
            path=pre_commit_path,
            applied=False,
            repository="https://github.com/ambv/black",
            current="19.10b0",
            latest="20.0.0",
        ),
        PreCommitUpdate(
            path=pre_commit_path,
            applied=False,
            repository="https://gitlab.com/pycqa/flake8",
            current="3.8.1",
            latest="3.9.0",
        ),
    ]
