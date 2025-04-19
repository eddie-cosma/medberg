from random import randint
from time import sleep

import pytest

from medberg import SecureSite
from medberg.exceptions import LoginException, InvalidFileException


def test_secure_site_auth(connection):
    assert len(connection.files) > 0


def test_secure_site_bad_auth():
    with pytest.raises(LoginException):
        conn = SecureSite("", "")


def test_file_download_by_name(connection, tmp_path):
    test_file_name = connection.files[0].name
    sleep(randint(4, 12))
    connection.get_file(test_file_name, save_dir=tmp_path, save_name="test.txt")

    with open(tmp_path / "test.txt") as f:
        assert f.read() != ""


def test_file_download_missing_file(connection, tmp_path):
    with pytest.raises(InvalidFileException):
        sleep(randint(4, 12))
        connection.get_file("not_real.txt", save_dir=tmp_path)
