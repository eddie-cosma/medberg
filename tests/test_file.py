from datetime import datetime
from pathlib import Path

import pytest

from medberg.exceptions import EmptyBufferException, MissingRowPatternException
from medberg.file import File, RowPattern


def test_file_download(file_instance):
    with open(file_instance.location) as f:
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


@pytest.fixture(scope="module")
def file():
    return File(
        conn=None,
        name="340B037AM1234567890101.TXT",
        filesize="1.2M",
        date=datetime.now(),
    )


def test_match_strings(file):
    assert file.matches("name", "340B037AM1234567890101.TXT")
    assert file.matches("filesize", "1.2M")
    assert file.matches("account_type", "340B")
    assert file.matches("specification", "037AM")
    assert file.matches("specification", "*37AM")
    assert file.matches("specification", "*037AM")
    assert file.matches("specification", "037*")
    assert file.matches("specification", "037AM*")
    assert file.matches("account_number", "123456789")


def test_mismatch_strings(file):
    assert file.matches("name", "340B037AM9876543210101.TXT") == False
    assert file.matches("filesize", "10M") == False
    assert file.matches("account_type", "WAC") == False
    assert file.matches("specification", "039A") == False
    assert file.matches("specification", "*39A") == False
    assert file.matches("specification", "039*") == False
    assert file.matches("account_number", "987654321") == False


def test_match_integers(file):
    assert file.matches("account_number", 123456789)


def test_mismatch_integers(file):
    assert file.matches("account_number", 987654321) == False


def test_match_callable(file):
    past_date = datetime(2025, 1, 1, 0, 0, 0)
    assert file.matches("date", lambda x: x > past_date)


def test_mismatch_callable(file):
    past_date = datetime(2025, 1, 1, 0, 0, 0)
    assert file.matches("date", lambda x: x < past_date) == False


def test_match_iterable(file):
    account_types = ["340B", "GPO", "WAC"]
    assert file.matches("account_type", account_types)


def test_mismatch_iterable(file):
    account_types = ["GPO", "WAC"]
    assert file.matches("account_type", account_types) == False


def test_match_none():
    f = File(
        conn=None,
        name="1234567890101.TXT",
        filesize="1.2M",
        date=datetime.now(),
    )
    assert f.matches("account_type", None)
    assert f.matches("specification", None)


def test_mismatch_none():
    f = File(
        conn=None,
        name="1234567890101.TXT",
        filesize="1.2M",
        date=datetime.now(),
    )
    assert f.matches("account_number", None) == False
    assert f.matches("filesize", None) == False


def test_buffer(file_instance):
    file_instance.row_pattern = RowPattern.MATCH_ALL
    with file_instance as f:
        assert len(f._row_buffer) > 0
        f.filter_(lambda x: x.raw.startswith("0"))

    with open(file_instance.location) as f:
        for line in f:
            assert line.startswith("0")


def test_dump_failure(file_instance):
    file_instance.row_pattern = RowPattern.MATCH_ALL
    with pytest.raises(EmptyBufferException):
        with file_instance as f:
            assert len(f._row_buffer) > 0
            f.filter_(lambda x: False)


def test_missing_row_pattern():
    test_file = File(
        conn=None,
        name="1234567890101.TXT",
        filesize="1.2M",
        date=datetime.now(),
    )
    test_file.location = "/placeholder"
    with pytest.raises(MissingRowPatternException):
        with test_file:
            pass


def test_filter(tmp_path):
    file_contents = (
        "00000000000111111  222222222333333333\n"
        "44444444444555555  666666666777777777\n"
        "44444444444888888  999999999000000000\n"
    )
    with open(Path(tmp_path) / "test.txt", "w") as f:
        f.write(file_contents)

    test_file = File(
        conn=None,
        name="1234567890101.TXT",
        filesize="1.2M",
        date=datetime.now(),
    )
    test_file.location = Path(tmp_path) / "test.txt"
    test_file.row_pattern = RowPattern.ICS_039A
    test_file.contents = file_contents
    with test_file as f:
        f.filter_(lambda x: x.parts["ndc11"] == "44444444444")
        f.filter_(lambda x: x.parts["item_id"] == "555555")

    assert len(f._row_buffer) == 1
    assert f._row_buffer[0].parts["ndc11"] == "44444444444"
    assert f._row_buffer[0].parts["item_id"] == "555555"
