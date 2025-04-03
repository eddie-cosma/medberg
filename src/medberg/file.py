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

    def __repr__(self) -> str:
        date = datetime.strftime(self.date, "%m/%d/%Y")
        return f"File(name={self.name}, filesize={self.filesize=}, {date=})"

    def get(self, *args, **kwargs) -> Path:
        """Download a file from the Amerisource secure site."""
        return self._conn.get_file(file=self, *args, **kwargs)
