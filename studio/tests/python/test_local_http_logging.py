#!/usr/bin/env python3
"""Focused tests for quiet local-service HTTP logging."""

from __future__ import annotations

from types import SimpleNamespace

from studio.shared.python.local_http_logging import QuietErrorLoggingMixin, is_error_status


class RecordingBase:
    def __init__(self, *, access_log_enabled: bool) -> None:
        self.server = SimpleNamespace(access_log_enabled=access_log_enabled)
        self.command = "GET"
        self.path = "/missing?source=test"
        self.request_version = "HTTP/1.1"
        self.messages: list[str] = []

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        self.messages.append(f"parent request {code} {size}")

    def log_error(self, format: str, *args: object) -> None:  # noqa: A002
        self.messages.append("parent error " + (format % args))

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        self.messages.append(format % args)


class RecordingHandler(QuietErrorLoggingMixin, RecordingBase):
    service_log_name = "test-service"


def test_error_status_normalization() -> None:
    assert is_error_status(404) is True
    assert is_error_status("500") is True
    assert is_error_status(200) is False
    assert is_error_status("-") is False


def test_quiet_logging_keeps_success_quiet_and_identifies_error_request() -> None:
    handler = RecordingHandler(access_log_enabled=False)

    handler.log_request(200)
    handler.log_error("code %d, message %s", 404, "Not found")
    handler.log_request(404)

    assert handler.messages == [
        '[test-service] "GET /missing?source=test HTTP/1.1" 404 -'
    ]


def test_enabled_access_logging_delegates_to_normal_handler() -> None:
    handler = RecordingHandler(access_log_enabled=True)

    handler.log_request(200, 12)
    handler.log_error("code %d", 404)

    assert handler.messages == ["parent request 200 12", "parent error code 404"]
