"""Version representation for inventories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from packaging import version

if TYPE_CHECKING:
    from packaging.version import LegacyVersion, Version
    from typing import Union

__all__ = ["ParsedVersion"]


@dataclass(frozen=True, order=True)
class ParsedVersion:
    """Represents a version string."""

    parsed_version: Union[LegacyVersion, Version]
    """The canonicalized, parsed version, for sorting.

    Notes
    -----
    This field must be first because it's the field we want to sort on and
    dataclass ordering is done as if the dataclass were a tuple, via ordering
    on each element of the tuple in sequence.
    """

    version: str
    """The raw version string, which may start with a v."""

    @classmethod
    def from_str(cls, string: str) -> ParsedVersion:
        """Parse a string into a `~packaging.version.Version`.

        Parameters
        ----------
        string : `str`
            The version as a string.

        Returns
        -------
        version: `packaging.version.Version`
            The parsed version.
        """
        parsed_version = version.parse(string)
        return cls(parsed_version=parsed_version, version=string)

    def __str__(self) -> str:
        return self.version
