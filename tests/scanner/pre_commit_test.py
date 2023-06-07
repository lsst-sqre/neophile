"""Tests for the PreCommitScanner class."""

from __future__ import annotations

from pathlib import Path

from neophile.models.dependencies import PreCommitDependency
from neophile.scanner.pre_commit import PreCommitScanner


def test_scanner() -> None:
    data_path = Path(__file__).parent.parent / "data" / "python"
    scanner = PreCommitScanner()
    results = scanner.scan(data_path)

    assert results == [
        PreCommitDependency(
            repository="https://github.com/pre-commit/pre-commit-hooks",
            owner="pre-commit",
            repo="pre-commit-hooks",
            version="v3.1.0",
            path=data_path / ".pre-commit-config.yaml",
        ),
        PreCommitDependency(
            repository="https://github.com/timothycrosley/isort",
            owner="timothycrosley",
            repo="isort",
            version="4.3.21-2",
            path=data_path / ".pre-commit-config.yaml",
        ),
        PreCommitDependency(
            repository="https://github.com/ambv/black",
            owner="ambv",
            repo="black",
            version="19.10b0",
            path=data_path / ".pre-commit-config.yaml",
        ),
        PreCommitDependency(
            repository="https://gitlab.com/pycqa/flake8",
            owner="pycqa",
            repo="flake8",
            version="3.8.1",
            path=data_path / ".pre-commit-config.yaml",
        ),
    ]
