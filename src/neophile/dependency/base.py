"""Base class for dependency information."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Dict

__all__ = ["Dependency"]


@dataclass(frozen=True, order=True)
class Dependency:
    """Base class for a dependency returned by a scanner."""

    path: Path
    """The file that contains the dependency declaration."""

    def to_dict(self) -> Dict[str, str]:
        """Convert the object to a dict.

        Notes
        -----
        Required because :py:mod:`ruamel.yaml` cannot serialize
        `~pathlib.Path`.
        """
        result = asdict(self)
        result["path"] = str(result["path"])
        return result
