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

from datetime import datetime
from http.cookiejar import CookieJar
from random import randint
from time import sleep
from urllib.parse import urlencode
from urllib.request import urlopen, Request, HTTPCookieProcessor, build_opener

from bs4 import BeautifulSoup

from .exceptions import (
    InvalidFileException,
    LoginException,
    FileDownloadFailureException,
)
from .file import File


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

    def match_files(self, **kwargs) -> list[File]:
        """Given a series of filter arguments, return list of matching Files.

        Argument keys should match to file properties and argument values should
        match to file property values. For example, to return a list of File
        objects for which account_number = 12345, simply call
        `match_files(account_number=12345)`. Any number of keyword arguments
        can be included to further filter the results. Complex logic is
        available using callables, iterables, and wildcards. For more details,
        see `File.matches()`.
        """
        matched_files = []
        for file in self.files:
            is_match = True
            for arg, value in kwargs.items():
                if not file.matches(arg, value):
                    is_match = False
                    break  # Exclusion is determined; stop evaluating this file

            if is_match:
                matched_files.append(file)

        return matched_files

    def match_latest_file(self, **kwargs) -> File | None:
        """Given a series of filter arguments, return newest matching file.

        See `match_files()` for more information on allowed arguments.
        """
        matches = self.match_files(**kwargs)
        if not matches:
            return None

        latest = matches[0]
        for match_ in matches:
            if match_.date > latest.date:
                latest = match_

        return latest

    def _process_download(self, contract_post_request: Request) -> bytes:
        with self._opener.open(contract_post_request) as contract_post_response:
            success_status = contract_post_response.status == 200
            file_contents = contract_post_response.read()

            download_failure = b"Some Error Occured!!" in file_contents
            if download_failure or not success_status:
                raise FileDownloadFailureException

            return file_contents

    def get_file(self, file: File | str, max_tries: int = 5) -> bytes:
        """Download a file from the Amerisource secure site.

        Raises InvalidFileException if a string is passed as the filename and
        that filename does not exist on the remote site.

        Raises FileDownloadFailureException if the file could not be downloaded
        after max_tries attempts.
        """
        if isinstance(file, File) or (file := self._match_filename(file)):
            pass
        else:
            raise InvalidFileException

        contract_post_data = urlencode(
            {
                "custNmaeSelect": self._customer_name,
                "fileChk": f"#{file.name}",
                "dnldoption": "none",
                "submit": "Download+Now",
            }
        ).encode()
        contract_post_request = Request(
            f"{self._base_url}/fileDownloadtolocal.action",
            data=contract_post_data,
        )

        for try_num in range(max_tries):
            try:
                return self._process_download(contract_post_request)
            except FileDownloadFailureException:
                if try_num == max_tries - 1:
                    raise
                else:
                    sleep(randint(4, 12))
                    continue
