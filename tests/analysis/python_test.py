"""Tests for the PythonAnalyzer class."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import aiohttp
import pytest
from git import Actor, Repo

from neophile.exceptions import UncommittedChangesError
from neophile.factory import Factory
from neophile.update.python import PythonFrozenUpdate


@pytest.mark.asyncio
async def test_analyzer_python(tmp_path: Path) -> None:
    data_path = Path(__file__).parent.parent / "data" / "python"
    shutil.copytree(str(data_path), str(tmp_path), dirs_exist_ok=True)
    repo = Repo.init(str(tmp_path))
    repo.index.add(
        [
            str(tmp_path / ".pre-commit-config.yaml"),
            str(tmp_path / "Makefile"),
            str(tmp_path / "requirements"),
        ]
    )
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)

    async with aiohttp.ClientSession() as session:
        factory = Factory(session)
        analyzer = factory.create_python_analyzer(str(tmp_path))
        results = await analyzer.analyze()

    assert results == [PythonFrozenUpdate(path=str(tmp_path / "requirements"))]

    # Ensure that the tree is restored to the previous contents.
    assert not repo.is_dirty()

    # If the repo is dirty, analysis will fail.
    subprocess.run(["make", "update-deps"], cwd=str(tmp_path), check=True)
    assert repo.is_dirty()
    async with aiohttp.ClientSession() as session:
        factory = Factory(session)
        analyzer = factory.create_python_analyzer(str(tmp_path))
        with pytest.raises(UncommittedChangesError):
            results = await analyzer.analyze()

    # Commit the changed dependencies and remove the pre-commit configuration
    # file.  Analysis should now return no changes.
    repo.index.add(str(tmp_path / "requirements"))
    repo.index.commit("Update dependencies", author=actor, committer=actor)
    async with aiohttp.ClientSession() as session:
        factory = Factory(session)
        analyzer = factory.create_python_analyzer(str(tmp_path))
        results = await analyzer.analyze()
    assert results == []
