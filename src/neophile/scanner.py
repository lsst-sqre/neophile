"""Source tree scanning."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from typing import Dict

__all__ = ["Scanner"]


class Scanner:
    """Scan a source tree for version references.

    Parameters
    ----------
    root : `str`
        The root of the source tree.
    """

    def __init__(self, root: str) -> None:
        self._root = root

    def scan(self) -> Dict[str, Dict[str, str]]:
        """Scan a source tree for version references.

        Currently only looks for Helm chart dependencies.

        Returns
        -------
        results : Dict[`str`, Dict[`str`, `str`]]
            The top-level key will be the name of the external package.  The
            value is a dict of information about that reference.  The keys
            will include ``type`` (the type of dependency) and ``version``
            (the pinned version number).
        """
        results = {}
        for dirpath, _, filenames in os.walk(self._root):
            for name in filenames:
                if name not in ("Chart.yaml", "requirements.yaml"):
                    continue
                path = Path(dirpath) / name
                with path.open() as f:
                    requirements = yaml.safe_load(f)
                for dependency in requirements.get("dependencies", []):
                    results[dependency["name"]] = {
                        "type": "helm",
                        "version": dependency["version"],
                        "repository": dependency["repository"],
                    }
        return results
