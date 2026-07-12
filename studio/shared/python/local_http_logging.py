"""Shared request logging for quiet local HTTP services."""

from __future__ import annotations


def is_error_status(code: int | str) -> bool:
    try:
        return int(code) >= 400
    except (TypeError, ValueError):
        return False


class QuietErrorLoggingMixin:
    """Keep successful access logs quiet while identifying error responses."""

    service_log_name = "local-service"

    def access_log_enabled(self) -> bool:
        return bool(getattr(self.server, "access_log_enabled", False))

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        if self.access_log_enabled():
            super().log_request(code, size)
            return
        if is_error_status(code):
            self.log_message(
                '[%s] "%s %s %s" %s %s',
                self.service_log_name,
                self.command,
                self.path,
                self.request_version,
                code,
                size,
            )

    def log_error(self, format: str, *args: object) -> None:  # noqa: A002
        if self.access_log_enabled():
            super().log_error(format, *args)
