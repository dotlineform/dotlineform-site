"""Shared route ready-state waits for browser smoke checks."""

from __future__ import annotations

from playwright.sync_api import Page


def wait_for_route_ready(
    page: Page,
    root_selector: str,
    ready_attr: str,
    busy_attr: str,
    timeout_ms: int = 10_000,
) -> dict[str, str]:
    page.wait_for_selector(f"{root_selector}:not([hidden])", timeout=timeout_ms)
    page.wait_for_selector(f"{root_selector}[{ready_attr}='true']", timeout=timeout_ms)
    page.wait_for_function(
        """([selector, attr]) => document.querySelector(selector)?.getAttribute(attr) !== "true" """,
        arg=[root_selector, busy_attr],
        timeout=timeout_ms,
    )
    return page.locator(root_selector).evaluate(
        """root => Object.fromEntries(
            Array.from(root.attributes, attr => [attr.name, attr.value])
        )"""
    )
