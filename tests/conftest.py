"""Keep the entire test suite offline, including SDK regressions."""

import socket

import pytest


@pytest.fixture(autouse=True)
def block_outbound_connections(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network connections are disabled during tests")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
