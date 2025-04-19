import copy
import os
import shutil

import pytest
from dotenv import load_dotenv

from medberg import SecureSite


@pytest.fixture(scope="session")
def connection():
    load_dotenv()
    username = os.getenv("AMERISOURCE_USERNAME")
    password = os.getenv("AMERISOURCE_PASSWORD")
    return SecureSite(username, password)


@pytest.fixture(scope="session")
def file_master(connection, tmp_path_factory):
    target_dir = tmp_path_factory.mktemp("data")
    connection.files[0].get(save_dir=target_dir)
    return connection.files[0]


@pytest.fixture(scope="function")
def file_instance(file_master, tmp_path):
    file = copy.copy(file_master)
    file.conn = None
    file.location = shutil.copy(file_master.location, tmp_path)
    return file
