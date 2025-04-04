import re
from datetime import datetime
from pathlib import Path


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

    def __repr__(self) -> str:
        date = datetime.strftime(self.date, "%m/%d/%Y")
        return f"File(name={self.name}, filesize={self.filesize=}, {date=})"

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

    def get(self, *args, **kwargs) -> Path:
        """Download a file from the Amerisource secure site."""
        return self._conn.get_file(file=self, *args, **kwargs)
