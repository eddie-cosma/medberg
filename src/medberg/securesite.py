"""File and connection handling for the medberg package.

This file contains two classes: File and SecureSite. The intended usage is to
start by creating an instance of SecureSite with a valid username and password.
On instantiation, a connection will be made and authentication will be
attempted. If successful, the webpage on which files are listed will be parsed
automatically for a customer name and file list.

The secure site file table contains columns for name, filesize, and upload date,
which are used to instantiate the File class. Instances are stored in a list
in SecureSite.files. From here, either the File.get or SecureSite.get_file
methods can be used to download the needed files.
"""

import shutil
from datetime import datetime
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request, HTTPCookieProcessor, build_opener

from bs4 import BeautifulSoup

from .exceptions import InvalidFileException, LoginException


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

    def get(
        self, save_dir: str | Path | None = None, save_name: str | None = None
    ) -> Path:
        """Download a file from the Amerisource secure site."""

        if save_dir is None:
            save_dir = Path.cwd()
        elif isinstance(save_dir, str):
            save_dir = Path(save_dir)

        if save_name is None:
            save_name = self.name

        contract_post_data = urlencode(
            {
                "custNmaeSelect": self._conn._customer_name,
                "fileChk": f"#{self.name}",
                "dnldoption": "none",
                "submit": "Download+Now",
            }
        ).encode()
        contract_post_request = Request(
            f"{self._conn._base_url}/fileDownloadtolocal.action",
            data=contract_post_data,
        )
        with self._conn._opener.open(contract_post_request) as contract_post_response:
            with open(save_dir / save_name, "wb") as price_file:
                shutil.copyfileobj(contract_post_response, price_file)

        return save_dir / save_name


class SecureSite:
    """Represents a connection to the secure site.

    After the initial connection is established, a list of available files is
    stored in the self.files variable.
    """

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str = "https://secure.amerisourcebergen.com/secureProject",
    ):
        self._cookies = CookieJar()
        self._cookie_processor = HTTPCookieProcessor(self._cookies)
        self._opener = build_opener(self._cookie_processor)

        self._username = username
        self._password = password
        self._base_url = base_url

        self._soup = self._connect_and_retrieve_html()
        self._customer_name = self._parse_customer()
        self.files = self._parse_files()

    def _connect_and_retrieve_html(self) -> BeautifulSoup:
        """Get a BeautifulSoup object representing the secure site file listing.

        Raises LoginException on authentication failure.
        """
        login_get_request = Request(f"{self._base_url}/jsp/Login.jsp")
        with urlopen(login_get_request) as login_get_response:
            self._cookie_processor.https_response(login_get_request, login_get_response)

        login_post_data = urlencode(
            {
                "userName": self._username,
                "password": self._password,
                "action:welcome": "Logon",
            }
        ).encode()
        login_post_request = Request(
            f"{self._base_url}/welcome.action", data=login_post_data
        )
        with self._opener.open(login_post_request) as login_post_response:
            raw_html = login_post_response.read().decode()
            if "The login information that you entered is invalid." in raw_html:
                raise LoginException
            return BeautifulSoup(raw_html, "html.parser")

    def _parse_customer(self) -> str:
        """Get the customer name to be passed into the download request.

        Note that a large amount of whitespace is expected.
        """
        return self._soup.find(id="fileDownload_custName")["value"]

    def _parse_files(self) -> list[File]:
        """Get the list of files available for download."""
        files = []
        for row in self._soup.find(id="fileDownload").find_all("tr"):
            if not row.find(id="fileDownload_fileChk"):
                # If there is no file in this table row, move on
                continue

            date_tags = row.find_all(title="Date/Time Uploaded")
            date_string = [part.get_text(strip=True) for part in date_tags]
            date_string = " ".join(date_string)

            files.append(
                File(
                    conn=self,
                    name=row.find(id="fileDownload_fileChk")["value"],
                    filesize=row.find(title="#size# Bytes").get_text(strip=True),
                    date=datetime.strptime(date_string, "%m/%d/%Y %I:%M:%S %p"),
                )
            )

        return files

    def _match_filename(self, filename: str) -> File | None:
        """For a string filename, try to match to a file on the remote site."""
        for file in self.files:
            if file.name == filename:
                return file
        return None

    def get_file(self, file: File | str, *args, **kwargs) -> Path:
        """Download a file from the Amerisource secure site.

        Raises InvalidFileException if a string is passed as the filename and
        that filename does not exist on the remote site.
        """
        if isinstance(file, File) or (file := self._match_filename(file)):
            return file.get(*args, **kwargs)
        else:
            raise InvalidFileException
