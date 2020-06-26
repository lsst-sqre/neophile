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
from dataclasses import dataclass

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


@dataclass(frozen=True, eq=True)
class UpdateMixin:
    """Add the base data elements for `Update`."""

    path: str
    """The file that contains the dependency."""


class Update(UpdateMixin, MethodMixin):
    """Base class for a needed dependency version update."""
