#!/usr/bin/env python3
"""Focused contract tests for Docs Viewer local-folder links."""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote

import pytest

from docs_management_test_support import docs_management_service, make_repo

import docs_local_links
import docs_management_routes as routes


def configure_base(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    base = tmp_path / "Projects Base"
    base.mkdir()
    monkeypatch.setenv(docs_local_links.PROJECTS_BASE_DIR_ENV, str(base))
    return base.resolve()


def test_authoring_normalizes_all_supported_forms_and_missing_targets(tmp_path: Path) -> None:
    base = tmp_path / "Projects Base"
    base.mkdir()
    target = base / "3 symbols" / "München ✓"
    inputs = [
        str(target),
        str(target).replace(" ", "\\ "),
        target.as_uri(),
        f"file://localhost{quote(str(target), safe='/')}",
    ]

    expected = {
        "target": "3 symbols/München ✓",
        "encoded_target": "3%20symbols/M%C3%BCnchen%20%E2%9C%93",
        "label": "München ✓",
        "markdown": "[München ✓](dlf-local:3%20symbols/M%C3%BCnchen%20%E2%9C%93)",
    }
    assert all(docs_local_links.normalize_local_path_input(value, base) == expected for value in inputs)
    prospective = docs_local_links.normalize_local_path_input(str(base / "future" / "[draft]"), base)
    assert prospective["markdown"] == r"[\[draft\]](dlf-local:future/%5Bdraft%5D)"


def test_authoring_rejects_ambiguous_or_outside_values(tmp_path: Path) -> None:
    base = tmp_path / "projects"
    base.mkdir()
    child = str(base / "child")
    rejected = [
        str(base), str(tmp_path / "other"), f" {child}", f"{child} ",
        f"{child}\nsecond-line", f"{child}?query=yes", f"{child}#fragment",
        f"{base}/empty//segment", f"{base}/dot/../segment", f"{base}/dot/./segment",
        f"{child}\\", f"{base}/literal\\\\backslash", "~/child", "$HOME/child",
        "https://example.com/child", "//[invalid", f"file://remote{child}",
        f"file://{child}?query=yes", f"file://{child}#fragment",
        f"file://{base}/bad%ZZ", f"file://{base}/bad%FF", f"{child}\x00",
    ]

    for value in rejected:
        with pytest.raises(docs_local_links.LocalLinkInputError):
            docs_local_links.normalize_local_path_input(value, base)


def test_structured_targets_accept_relative_or_contained_absolute_input(
    tmp_path: Path,
) -> None:
    base = tmp_path / "Projects Base"
    base.mkdir()
    target = base / "projects" / "Future Folder"

    accepted = [
        "projects/Future Folder",
        str(target),
        str(target).replace(" ", "\\ "),
        target.as_uri(),
    ]
    assert [
        docs_local_links.normalize_structured_local_target_input(value, base)
        for value in accepted
    ] == ["projects/Future Folder"] * len(accepted)

    rejected = [
        "dlf-local:projects/Future%20Folder",
        "[Future Folder](dlf-local:projects/Future%20Folder)",
        "../Future Folder",
        "projects/../Future Folder",
        "https://example.com/Future Folder",
        str(tmp_path / "outside"),
    ]
    for value in rejected:
        with pytest.raises(docs_local_links.LocalLinkInputError):
            docs_local_links.normalize_structured_local_target_input(value, base)


def test_encoded_targets_require_a_canonical_safe_round_trip() -> None:
    encoded = "projects/3%20symbols/M%C3%BCnchen%20%E2%9C%93~"
    decoded = docs_local_links.decode_relative_target(encoded)
    assert decoded == "projects/3 symbols/München ✓~"
    assert docs_local_links.encode_relative_target(decoded) == encoded

    rejected = [
        "", " projects/child", "projects/child ", "/absolute", "projects//child",
        "projects/./child", "projects/../child", "projects\\child", "https:child",
        "projects/bad%ZZ", "projects/bad%FF", "projects/3%2Fsymbols",
        "projects/%7Etilde", "projects/3 symbols", "projects/child\nsecond-line",
    ]
    for target in rejected:
        with pytest.raises(docs_local_links.LocalLinkInputError):
            docs_local_links.decode_relative_target(target)


@pytest.mark.parametrize("kind", ["directory", "file"])
def test_activation_invokes_exact_finder_command_for_valid_targets(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = configure_base(monkeypatch, tmp_path)
    target = base / ("project" if kind == "directory" else "project.txt")
    target.mkdir() if kind == "directory" else target.write_text("content", encoding="utf-8")
    monkeypatch.setattr(docs_local_links.sys, "platform", "darwin")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(docs_local_links.subprocess, "run", fake_run)
    status, payload = docs_local_links.open_local_target_response(tmp_path, {"target": target.name})

    expected = ["open", str(target)] if kind == "directory" else ["open", "-R", str(target)]
    assert status == HTTPStatus.OK
    assert payload == {
        "ok": True, "state": "opened", "summary_text": "Local target opened.",
        "target": target.name, "dry_run": False,
    }
    assert calls == [(
        expected,
        {"cwd": tmp_path, "capture_output": True, "text": True, "check": False},
    )]
    assert str(base) not in json.dumps(payload)


def test_activation_contains_invalid_missing_outside_and_unavailable_states(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = configure_base(monkeypatch, tmp_path)
    (base / "project").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (base / "escape").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(docs_local_links.sys, "platform", "darwin")
    monkeypatch.setattr(
        docs_local_links.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("Finder must not run for contained outcomes"),
    )

    cases = [
        ({}, HTTPStatus.BAD_REQUEST, "invalid_target"),
        ({"target": "project", "scope": "studio"}, HTTPStatus.BAD_REQUEST, "invalid_target"),
        ({"target": "../project"}, HTTPStatus.BAD_REQUEST, "invalid_target"),
        ({"target": "missing"}, HTTPStatus.NOT_FOUND, "missing_target"),
        ({"target": "escape"}, HTTPStatus.FORBIDDEN, "outside_root"),
    ]
    outcomes = [docs_local_links.open_local_target_response(tmp_path, body) for body, _, _ in cases]
    for (_, expected_status, expected_state), (status, payload) in zip(cases, outcomes):
        assert (status, payload["state"]) == (expected_status, expected_state)
        assert str(base) not in json.dumps(payload)

    monkeypatch.setattr(docs_local_links.sys, "platform", "linux")
    status, payload = docs_local_links.open_local_target_response(tmp_path, {"target": "project"})
    assert (status, payload["state"]) == (HTTPStatus.NOT_IMPLEMENTED, "unsupported_platform")
    monkeypatch.setenv(docs_local_links.PROJECTS_BASE_DIR_ENV, str(base / "missing"))
    status, payload = docs_local_links.open_local_target_response(tmp_path, {"target": "project"})
    assert (status, payload["state"]) == (HTTPStatus.SERVICE_UNAVAILABLE, "base_unavailable")


def test_management_endpoint_dry_run_validates_without_invoking_finder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as repo_name:
        repo_root = Path(repo_name)
        base = configure_base(monkeypatch, tmp_path)
        (base / "project").mkdir()
        monkeypatch.setattr(docs_local_links.sys, "platform", "darwin")
        monkeypatch.setattr(
            docs_local_links.subprocess,
            "run",
            lambda *args, **kwargs: pytest.fail("Finder must not run during dry-run"),
        )
        status, payload = docs_management_service.docs_management_post_response(
            repo_root, routes.OPEN_LOCAL_TARGET_PATH, {"target": "project"}, dry_run=True,
        )

    assert status == HTTPStatus.OK
    assert payload["state"] == "opened"
    assert payload["summary_text"] == "Local target validated."
    assert payload["dry_run"] is True
