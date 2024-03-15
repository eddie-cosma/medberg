import re
import shutil
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request, HTTPCookieProcessor, build_opener


class SecureSite:
    """Class for Amerisource tenant account. Used for connection and enumeration."""

    FILENAME_PATTERN = re.compile(
        r'<input type="checkbox" name="fileChk" value="([\w\d\._]+?)" id="fileDownload_fileChk"\/>'
    )
    CUSTOMER_PATTERN = re.compile(
        r'<input type="hidden" name="custName" value="([\w\d\s\._\-]+?)" id="fileDownload_custName"\/>'
    )

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

        self.files = []

        self._customer_name = None
        self._connect_and_list_files()

    def _connect_and_list_files(self):
        """Get a list of filenames from the Amerisource secure site.

        Raises exception if list of files is not obtained.
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
            contract_list_html = login_post_response.read().decode()
            files = re.findall(self.FILENAME_PATTERN, contract_list_html)
            for file_ in files:
                self.files.append(file_)

            customer_match = re.findall(self.CUSTOMER_PATTERN, contract_list_html)
            self._customer_name = customer_match[0]

        if not self.files or not self._customer_name:
            # TODO: Make exception more specific
            raise Exception("Unable to get file list.")

    def get_file(self, filename: str, save_dir: [str | Path | None] = None) -> Path:
        """Download file from Amerisource secure site"""

        if not save_dir:
            save_dir = Path.cwd()

        if type(save_dir) is str:
            save_dir = Path(save_dir)

        contract_post_data = urlencode(
            {
                "custNmaeSelect": self._customer_name,
                "fileChk": f"#{filename}",
                "dnldoption": "none",
                "submit": "Download+Now",
            }
        ).encode()
        contract_post_request = Request(
            f"{self._base_url}/fileDownloadtolocal.action", data=contract_post_data
        )
        with self._opener.open(contract_post_request) as contract_post_response:
            with open(save_dir / filename, "wb") as price_file:
                shutil.copyfileobj(contract_post_response, price_file)

        return save_dir / filename
