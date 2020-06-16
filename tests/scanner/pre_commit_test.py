"""Tests for the PreCommitScanner class."""

from __future__ import annotations

from pathlib import Path

from neophile.scanner.pre_commit import PreCommitDependency, PreCommitScanner


def test_scanner() -> None:
    datapath = Path(__file__).parent.parent / "data" / "python"
    scanner = PreCommitScanner(root=str(datapath))
    results = scanner.scan()

    assert results == [
        PreCommitDependency(
            repository="https://github.com/pre-commit/pre-commit-hooks",
            owner="pre-commit",
            repo="pre-commit-hooks",
            version="v3.1.0",
            path=str(datapath / ".pre-commit-config.yaml"),
        ),
        PreCommitDependency(
            repository="https://github.com/timothycrosley/isort",
            owner="timothycrosley",
            repo="isort",
            version="4.3.21-2",
            path=str(datapath / ".pre-commit-config.yaml"),
        ),
        PreCommitDependency(
            repository="https://github.com/ambv/black",
            owner="ambv",
            repo="black",
            version="19.10b0",
            path=str(datapath / ".pre-commit-config.yaml"),
        ),
        PreCommitDependency(
            repository="https://gitlab.com/pycqa/flake8",
            owner="pycqa",
            repo="flake8",
            version="3.8.1",
            path=str(datapath / ".pre-commit-config.yaml"),
        ),
    ]
