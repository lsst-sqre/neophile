"""Tests for the PythonAnalyzer class."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from aiohttp import ClientSession
from git.util import Actor

from neophile.config import Config
from neophile.exceptions import UncommittedChangesError
from neophile.factory import Factory
from neophile.update.python import PythonFrozenUpdate

from ..util import setup_python_repo


@pytest.mark.asyncio
async def test_analyzer(tmp_path: Path, session: ClientSession) -> None:
    repo = setup_python_repo(tmp_path)
    actor = Actor("Someone", "someone@example.com")

    factory = Factory(Config(), session)
    analyzer = factory.create_python_analyzer(tmp_path)
    results = await analyzer.analyze()

    assert results == [
        PythonFrozenUpdate(path=tmp_path / "requirements", applied=False)
    ]

    # Ensure that the tree is restored to the previous contents.
    assert not repo.is_dirty()

    # If the repo is dirty, analysis will fail.
    subprocess.run(["make", "update-deps"], cwd=str(tmp_path), check=True)
    assert repo.is_dirty()
    factory = Factory(Config(), session)
    analyzer = factory.create_python_analyzer(tmp_path)
    with pytest.raises(UncommittedChangesError):
        results = await analyzer.analyze()

    # Commit the changed dependencies and remove the pre-commit configuration
    # file.  Analysis should now return no changes.
    repo.index.add(str(tmp_path / "requirements"))
    repo.index.commit("Update dependencies", author=actor, committer=actor)
    factory = Factory(Config(), session)
    analyzer = factory.create_python_analyzer(tmp_path)
    results = await analyzer.analyze()
    assert results == []


@pytest.mark.asyncio
async def test_analyzer_update(tmp_path: Path, session: ClientSession) -> None:
    repo = setup_python_repo(tmp_path)

    factory = Factory(Config(), session)
    analyzer = factory.create_python_analyzer(tmp_path)
    results = await analyzer.update()

    assert results == [
        PythonFrozenUpdate(path=tmp_path / "requirements", applied=True)
    ]
    assert repo.is_dirty()


@pytest.mark.asyncio
async def test_virtualenv(
    tmp_path: Path, session: ClientSession, caplog: LogCaptureFixture
) -> None:
    setup_python_repo(tmp_path, require_venv=True)

    factory = Factory(Config(), session)
    analyzer = factory.create_python_analyzer(tmp_path)
    assert await analyzer.analyze() == []
    assert "make update-deps failed" in caplog.records[0].msg
