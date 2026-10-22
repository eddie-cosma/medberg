import socket
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from medberg.file import File


@pytest.fixture
def fixture_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def block_network(request, monkeypatch):
    if request.node.get_closest_marker("integration"):
        return

    def deny_network(*args, **kwargs):
        pytest.fail("Network access is disabled in offline tests")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)
    monkeypatch.setattr(socket, "getaddrinfo", deny_network)


@pytest.fixture
def file_instance(fixture_dir, tmp_path):
    name = "039A_012345678_0101.TXT"
    contents = (fixture_dir / name).read_bytes()
    connection = Mock()
    connection.get_file.return_value = contents
    file = File(connection, name, "148 B", datetime(2025, 1, 1, 8, 13, 58))
    file.get(save_dir=tmp_path)
    return file
