"""Exercise early-disconnect handling through Python's HTTP parser and dispatch."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from io import BytesIO
from types import SimpleNamespace

import pytest

from studio.shared.python.local_http_logging import IgnoreEarlyDisconnectMixin


class RequestInput(BytesIO):
    def __init__(self, request: bytes, *, reset_on_line: int = 0, reset_on_body: bool = False):
        super().__init__(request)
        self.reset_on_line = reset_on_line
        self.reset_on_body = reset_on_body
        self.line_reads = 0

    def readline(self, size: int = -1) -> bytes:
        self.line_reads += 1
        if self.line_reads == self.reset_on_line:
            raise ConnectionResetError("request line/header reset")
        return super().readline(size)

    def read(self, size: int = -1) -> bytes:
        if self.reset_on_body:
            raise ConnectionResetError("request body reset")
        return super().read(size)


class InMemorySocket:
    def __init__(self, request: RequestInput):
        self.request = request
        self.response = bytearray()

    def makefile(self, _mode: str, _buffering: int) -> RequestInput:
        return self.request

    def sendall(self, data: bytes) -> None:
        self.response.extend(data)


class RequestHandler(IgnoreEarlyDisconnectMixin, BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.server.handled = True
        if self.server.application_error is not None:
            raise self.server.application_error
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_POST(self) -> None:
        self.server.handled = True
        self.rfile.read(int(self.headers["Content-Length"]))
        self.do_GET()

    def log_message(self, _format: str, *_args: object) -> None:
        pass


def test_early_reset_closes_without_dispatch() -> None:
    connection = InMemorySocket(RequestInput(b"", reset_on_line=1))
    server = SimpleNamespace(handled=False, application_error=None)

    handler = RequestHandler(connection, ("127.0.0.1", 0), server)

    assert handler.close_connection is True
    assert server.handled is False
    assert connection.response == b""


def test_header_reset_propagates() -> None:
    connection = InMemorySocket(RequestInput(b"GET / HTTP/1.0\r\n", reset_on_line=2))
    server = SimpleNamespace(handled=False, application_error=None)

    with pytest.raises(ConnectionResetError, match="request line/header reset"):
        RequestHandler(connection, ("127.0.0.1", 0), server)

    assert server.handled is False
    assert connection.response == b""


def test_body_reset_propagates() -> None:
    request = b"POST / HTTP/1.0\r\nContent-Length: 1\r\n\r\nx"
    connection = InMemorySocket(RequestInput(request, reset_on_body=True))
    server = SimpleNamespace(handled=False, application_error=None)

    with pytest.raises(ConnectionResetError, match="request body reset"):
        RequestHandler(connection, ("127.0.0.1", 0), server)

    assert server.handled is True
    assert connection.response == b""


@pytest.mark.parametrize(
    "error",
    [ConnectionResetError("application reset"), RuntimeError("application failure")],
    ids=["connection-reset", "runtime-error"],
)
def test_application_errors_propagate(error: Exception) -> None:
    connection = InMemorySocket(RequestInput(b"GET / HTTP/1.0\r\n\r\n"))
    server = SimpleNamespace(handled=False, application_error=error)

    with pytest.raises(type(error)) as raised:
        RequestHandler(connection, ("127.0.0.1", 0), server)

    assert raised.value is error
    assert server.handled is True
    assert connection.response == b""


def test_normal_request_still_returns_response() -> None:
    connection = InMemorySocket(RequestInput(b"GET / HTTP/1.0\r\n\r\n"))
    server = SimpleNamespace(handled=False, application_error=None)

    RequestHandler(connection, ("127.0.0.1", 0), server)

    assert server.handled is True
    assert connection.response.startswith(b"HTTP/1.0 200 OK\r\n")
    assert connection.response.endswith(b"\r\n\r\nok")
