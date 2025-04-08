import os

import pytest
from dotenv import load_dotenv

from medberg import SecureSite


@pytest.fixture(scope="session")
def connection():
    load_dotenv()
    username = os.getenv("AMERISOURCE_USERNAME")
    password = os.getenv("AMERISOURCE_PASSWORD")
    return SecureSite(username, password)
