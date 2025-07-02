import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .exceptions import EmptyBufferException, MissingRowPatternException


class RowPattern(Enum):
    ICS_039A = re.compile(
        r"^(?P<ndc11>\d{11})(?P<item_id>\d{6}) {2}(?P<price>\d{9})(?P<pack_size>\d{9})$"
    )
    MATCH_ALL = re.compile(r"(?P<full_line>.+)")


@dataclass
class Row:
    raw: str
    parts: dict[str, str] = None


class File:
    """Represents a file available on the secure site.

    File instances are created automatically when a connection to the secure
    site is established and the list of available files is parsed. They should
    not be created manually.
    """

    def __init__(self, conn, name: str, filesize: str, date: datetime):
        self._conn = conn
        self.name = name
        self.filesize = filesize
        self.date = date

        self._filename_parts = self._parse_filename()

        self.contents = None
        self.location = None
        self.row_pattern = None
        self._row_buffer = []
        self._buffered = False

    def __repr__(self) -> str:
        date = datetime.strftime(self.date, "%m/%d/%Y")
        return f"File(name={self.name}, filesize={self.filesize=}, {date=})"

    def __enter__(self):
        if not self.location:
            self.get()

        self._row_buffer = self._buffer_rows()
        self._buffered = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._dump_rows()
        self._buffered = False

    def _parse_filename(self) -> dict[str, str | None]:
        """Try to parse metadata from the file's name.

        If present, will save account type, file specification, and account
        number in a dictionary that can be accessed with class properties.
        """
        filename_pattern = r"(?P<account_type>^|^340B|^WAC)_?(?P<specification>(?:037A|037A|039A|039A|77AX|037G|077A)X?M?)?_?(?P<account_number>\d{9})_?\d{4,6}\.TXT$"
        parts = {
            "account_type": None,
            "specification": None,
            "account_number": None,
        }

        name_matches = re.match(filename_pattern, self.name)
        if name_matches:
            parts.update(name_matches.groupdict())

        # Regex returns empty strings for unmatched groups. We convert them to
        # None for cleanliness.
        for key, value in parts.items():
            if value == "":
                parts[key] = None

        return parts

    def _match_row_pattern(self) -> RowPattern | None:
        """Based on file specification, try to match a row pattern.

        If a specification cannot be matched, return None."""
        if not self.specification:
            return None

        if self.specification.startswith("039"):
            return RowPattern.ICS_039A

        return None

    def _buffer_rows(self) -> list[Row]:
        """Generate a row buffer from the file contents."""
        if not self.row_pattern:
            raise MissingRowPatternException

        buffer = []
        for line in self.contents.splitlines(keepends=True):
            if line.strip():
                parts = re.match(self.row_pattern.value, line).groupdict()
                buffer.append(Row(line, parts))

        return buffer

    def _dump_rows(self):
        """Save the buffered rows back to file contents."""
        if len(self._row_buffer) == 0:
            raise EmptyBufferException

        self.contents = "".join([row.raw for row in self._row_buffer])

        if self.location:
            with open(self.location, "w", encoding="utf-8") as file:
                for row in self._row_buffer:
                    file.write(row.raw)

    @property
    def account_type(self) -> str | None:
        """Get account type (e.g., 340B, WAC) if present in filename."""
        return self._filename_parts.get("account_type")

    @property
    def specification(self) -> str | None:
        """Get file spec (e.g., 037, 039) if present in filename."""
        return self._filename_parts.get("specification")

    @property
    def account_number(self) -> str | None:
        """Get account number if present in filename."""
        return self._filename_parts.get("account_number")

    def matches(self, property_: str, filter_value: Any) -> bool:
        """For a property, get value and determine if the filter value matches.

        Matching works differently based on the filter value type:
        - Callables will cause the function to pass the file value as a
          parameter to the callable and return the result, which should be a
          boolean. This is useful for, e.g., datetimes, where an exact match is
          not as useful as a match using other operators like greater/less than.
        - Iterables (lists, tuples) will cause the file value to be matched
          against all values in the iterable, recursively. Any single match in
          the iterable will return true overall.
        - Other types will generally be matched using strict equality, but if
          the type of the filter value does not match the type of the file
          value, the function will first attempt to convert the filter value
          type to match.
        - Strings are no different from the other types description, except the
          wildcard character (*) can be used for basic pattern matching if
          placed either at the beginning or end of the filter value.
        """
        if not hasattr(self, property_):
            return False

        file_value = getattr(self, property_)
        if file_value == filter_value:
            return True

        if callable(filter_value):
            return filter_value(file_value)

        # If filter is list or tuple, recurse values to see if any matches
        if isinstance(filter_value, (list, tuple)):
            return True in [self.matches(property_, value) for value in filter_value]

        # Try to convert filter value type if different from file value type
        if not type(file_value) == type(filter_value):
            try:
                filter_value = type(file_value)(filter_value)
                return self.matches(property_, filter_value)
            except (ValueError, TypeError):
                return False

        # Handle wildcard character (*) in string filters
        if isinstance(filter_value, str):
            if filter_value.startswith("*"):
                return file_value.endswith(filter_value[1:])
            elif filter_value.endswith("*"):
                return file_value.startswith(filter_value[:-1])

        return False

    def get(
        self,
        save_dir: str | Path | None = None,
        save_name: str | None = None,
        *args,
        **kwargs,
    ) -> str:
        """Download a file from the Amerisource secure site."""

        raw_contents = self._conn.get_file(file=self, *args, **kwargs)
        self.contents = raw_contents.decode("utf-8")

        if save_dir:
            if isinstance(save_dir, str):
                save_dir = Path(save_dir)

            self.location = save_dir / (save_name or self.name)

            with open(self.location, "wb") as price_file:
                price_file.write(raw_contents)

        self.row_pattern = self._match_row_pattern()
        return self.contents

    def filter_(self, function: Callable) -> None:
        """Filter rows from the downloaded file using a callable"""
        if not self._buffered:
            with self as f:
                f.filter_(function)

        self._row_buffer = list(filter(function, self._row_buffer))
