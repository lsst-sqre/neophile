"""Base class for dependency updates.

Notes
-----
This is a bit more complicated than it should have to be to work around
https://github.com/python/mypy/issues/5374.  The mixins avoid the conflict
between an abstract base class and a dataclass in mypy's understanding of the
Python type system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Dict, Union

__all__ = [
    "MethodMixin",
    "Update",
    "UpdateMixin",
]


class MethodMixin(ABC):
    """Add the abstract methods for an update."""

    @abstractmethod
    def apply(self) -> None:
        """Apply an update.

        Raises
        ------
        neophile.exceptions.DependencyNotFoundError
            The specified file doesn't contain a dependency of that name.
        """

    @abstractmethod
    def description(self) -> str:
        """Build a description of this update.

        Returns
        -------
        description : `str`
            Short text description of the update.
        """


@dataclass(order=True)
class UpdateMixin:
    """Add the base data elements for `Update`."""

    path: Path
    """The file that contains the dependency."""

    applied: bool
    """Whether the update has already been applied."""

    def to_dict(self) -> Dict[str, Union[str, bool]]:
        """Convert the object to a dict.

        Notes
        -----
        Required because :py:mod:`ruamel.yaml` cannot serialize
        `~pathlib.Path`.
        """
        result = asdict(self)
        result["path"] = str(result["path"])
        return result


class Update(UpdateMixin, MethodMixin):
    """Base class for a needed dependency version update."""
