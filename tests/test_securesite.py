import os

import pytest
from dotenv import load_dotenv

from medberg import SecureSite
from medberg.exceptions import LoginException, InvalidFileException


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()


@pytest.fixture(scope="session")
def connection():
    username = os.getenv("AMERISOURCE_USERNAME")
    password = os.getenv("AMERISOURCE_PASSWORD")
    return SecureSite(username, password)


def test_secure_site_auth(connection):
    assert len(connection.files) > 0


def test_secure_site_bad_auth():
    with pytest.raises(LoginException):
        conn = SecureSite("", "")


def test_file_download(connection, tmp_path):
    test_file = connection.files[0]
    test_file.get(save_dir=tmp_path)

    with open(tmp_path / test_file.name) as f:
        assert f.read() != ""


def test_file_download_name_change(connection, tmp_path):
    test_file = connection.files[0]
    test_file.get(save_dir=tmp_path, save_name="test.txt")

    with open(tmp_path / "test.txt") as f:
        assert f.read() != ""


def test_file_download_by_name(connection, tmp_path):
    test_file_name = connection.files[0].name
    connection.get_file(test_file_name, save_dir=tmp_path, save_name="test.txt")

    with open(tmp_path / "test.txt") as f:
        assert f.read() != ""


def test_file_download_missing_file(connection, tmp_path):
    with pytest.raises(InvalidFileException):
        connection.get_file("not_real.txt", save_dir=tmp_path)
