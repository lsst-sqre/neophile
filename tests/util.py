"""Utility functions for tests."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from aioresponses import aioresponses
    from typing import Any, Dict, Sequence


def register_mock_github_tags(
    mock: aioresponses, owner: str, repo: str, tags: Sequence[str]
) -> None:
    """Register a list of tags for a GitHub repository.

    Parameters
    ----------
    mock : `aioresponses.aioresponses`
        The mock object for aiohttp requests.
    repo : `str`
        The name of the GitHub repository.
    tags : Sequence[`str`]
        The list of tags to return for that repository.
    """
    data = [{"name": version} for version in tags]
    mock.get(
        f"https://api.github.com/repos/{owner}/{repo}/tags",
        payload=data,
        repeat=True,
    )


def yaml_to_string(data: Dict[str, Any]) -> str:
    yaml = YAML()
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()
