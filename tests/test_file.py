from datetime import datetime

import pytest

from medberg.file import File


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


@pytest.mark.parametrize(
    "test_filename, expected",
    [
        ("340B037AM1234567890101.TXT", "340B"),
        ("037AM1234567890101.TXT", None),
        ("039A_123456789_0101.TXT", None),
        ("WAC77AX1234567890101.TXT", "WAC"),
        ("123456789010125.TXT", None),
        ("WAC_037AM_1234567890101.TXT", "WAC"),
    ],
)
def test_filename_parse_account_type(test_filename, expected):
    f = File(
        conn=None,
        name=test_filename,
        filesize="1.2M",
        date=datetime.now(),
    )
    assert f.account_type == expected


@pytest.mark.parametrize(
    "test_filename, expected",
    [
        ("340B037AM1234567890101.TXT", "037AM"),
        ("037AM1234567890101.TXT", "037AM"),
        ("039A_123456789_0101.TXT", "039A"),
        ("WAC77AX1234567890101.TXT", "77AX"),
        ("123456789010125.TXT", None),
        ("WAC_037AM_1234567890101.TXT", "037AM"),
    ],
)
def test_filename_parse_specification(test_filename, expected):
    f = File(
        conn=None,
        name=test_filename,
        filesize="1.2M",
        date=datetime.now(),
    )
    assert f.specification == expected


@pytest.mark.parametrize(
    "test_filename",
    [
        "340B037AM1234567890101.TXT",
        "037AM1234567890101.TXT",
        "039A_123456789_0101.TXT",
        "WAC77AX1234567890101.TXT",
        "123456789010125.TXT",
        "WAC_037AM_1234567890101.TXT",
    ],
)
def test_filename_account_number(test_filename):
    f = File(
        conn=None,
        name=test_filename,
        filesize="1.2M",
        date=datetime.now(),
    )
    assert f.account_number == "123456789"
