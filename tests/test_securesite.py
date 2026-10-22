from datetime import datetime
from io import BytesIO
from unittest.mock import Mock
from urllib.parse import parse_qs

import pytest

from medberg import SecureSite
from medberg.exceptions import (
    FileDownloadFailureException,
    InvalidFileException,
    LoginException,
)


def response(body, status=200):
    result = BytesIO(body)
    result.status = status
    return result


@pytest.fixture
def site(fixture_dir, monkeypatch):
    login = (fixture_dir / "login.html").read_bytes()
    listing = (fixture_dir / "listing.html").read_bytes()
    monkeypatch.setattr("medberg.securesite.urlopen", lambda request: response(login))
    monkeypatch.setattr(
        "medberg.securesite.HTTPCookieProcessor.https_response",
        lambda self, request, result: result,
    )
    opener = Mock()
    opener.open.side_effect = lambda request: response(listing)
    monkeypatch.setattr("medberg.securesite.build_opener", lambda processor: opener)
    return SecureSite("synthetic-user", "synthetic-password")


def test_listing_metadata(site):
    assert site._customer_name == "  Synthetic Customer  "
    assert len(site.files) == 2
    file = site.files[0]
    assert file.name == "039A_012345678_0101.TXT"
    assert file.account_number == "012345678"
    assert file.specification == "039A"
    assert file.filesize == "148 B"
    assert file.date == datetime(2025, 1, 1, 8, 13, 58)
    assert site.files[1].date == datetime(2025, 1, 2, 13, 2, 3)


def test_bad_auth(site, fixture_dir):
    body = (fixture_dir / "login_failure.html").read_bytes()
    site._opener.open.side_effect = lambda request: response(body)
    with pytest.raises(LoginException):
        site._connect_and_retrieve_html()


def test_file_selection(site):
    assert site.match_files(account_number="012345678") == [site.files[0]]
    assert site.match_files(specification="037*", account_type="WAC") == [site.files[1]]
    assert site.match_latest_file() is site.files[1]
    assert site.match_latest_file(account_number="012345678") is site.files[0]
    assert site.match_files(account_number="missing") == []
    assert site.match_latest_file(account_number="missing") is None


@pytest.mark.parametrize("by_name", [True, False])
def test_download(site, fixture_dir, by_name):
    expected = (fixture_dir / site.files[0].name).read_bytes()

    def download(request):
        data = parse_qs(request.data.decode())
        assert data["fileChk"] == ["#039A_012345678_0101.TXT"]
        assert data["custNmaeSelect"] == ["  Synthetic Customer  "]
        return response(expected)

    site._opener.open.side_effect = download
    target = site.files[0].name if by_name else site.files[0]
    assert site.get_file(target) == expected


def test_missing_file(site):
    with pytest.raises(InvalidFileException):
        site.get_file("not_real.txt")


@pytest.mark.parametrize(
    "body,status", [(b"Some Error Occured!!", 200), (b"unavailable", 503)]
)
def test_download_retry(site, fixture_dir, monkeypatch, body, status):
    expected = (fixture_dir / site.files[0].name).read_bytes()
    site._opener.open.side_effect = [response(body, status), response(expected)]
    monkeypatch.setattr("medberg.securesite.sleep", lambda seconds: None)
    assert site.get_file(site.files[0], max_tries=2) == expected


def test_download_retry_exhausted(site, monkeypatch):
    site._opener.open.side_effect = lambda request: response(b"Some Error Occured!!")
    monkeypatch.setattr("medberg.securesite.sleep", lambda seconds: None)
    with pytest.raises(FileDownloadFailureException):
        site.get_file(site.files[0], max_tries=2)


def test_unexpected_html_download(site, fixture_dir):
    body = (fixture_dir / "login.html").read_bytes()
    site._opener.open.side_effect = lambda request: response(body)
    with pytest.raises(FileDownloadFailureException):
        site.get_file(site.files[0], max_tries=1)
