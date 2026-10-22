"""Optional tests that contact the real Cencora site."""

import os

import pytest
from dotenv import load_dotenv

from medberg import SecureSite

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def live_connection():
    load_dotenv()
    username = os.getenv("AMERISOURCE_USERNAME")
    password = os.getenv("AMERISOURCE_PASSWORD")
    if not username or not password:
        pytest.skip("Cencora credentials are required for integration tests")
    return SecureSite(username, password)


def test_live_listing(live_connection):
    assert live_connection.files


def test_live_download(live_connection):
    assert live_connection.get_file(live_connection.files[0])
