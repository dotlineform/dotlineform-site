#!/usr/bin/env python3
"""Verify save-time catalogue build follow-through helpers."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_save_build as save_build  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def test_published_changed_save_runs_build_and_preserves_payload() -> None:
    response = {"ok": True}
    calls: list[str] = []

    def run_build():
        calls.append("run")
        return True, {"ok": True, "steps": ["generate"]}

    build_payload = save_build.apply_save_build_follow_through(
        response,
        requested_apply_build=True,
        apply_build=True,
        changed=True,
        build_plan={"build_required": True},
        run_build=run_build,
    )

    assert_equal(calls, ["run"], "build calls")
    assert_equal(response["build_requested"], True, "build requested")
    assert_equal(response["build"], {"ok": True, "steps": ["generate"]}, "build payload")
    assert_equal(build_payload, {"ok": True, "steps": ["generate"]}, "returned build payload")


def test_requested_draft_save_reports_unpublished_skip_without_build() -> None:
    response = {"ok": True}
    calls: list[str] = []

    build_payload = save_build.apply_save_build_follow_through(
        response,
        requested_apply_build=True,
        apply_build=False,
        changed=True,
        build_plan={"build_required": True},
        unpublished_reason="work_not_published",
        unpublished_message="Work must be published before a public update can run.",
        run_build=lambda: (calls.append("run") or (True, {"ok": True})),
    )

    assert_equal(calls, [], "build calls")
    assert_equal(response["build_requested"], False, "build requested")
    assert_equal(
        response["build_skipped"],
        {
            "reason": "work_not_published",
            "summary": "Work must be published before a public update can run.",
        },
        "unpublished skip payload",
    )
    assert_equal(build_payload, None, "returned build payload")


def test_no_public_artifacts_reports_existing_skip_reason() -> None:
    response = {"ok": True}
    calls: list[str] = []

    save_build.apply_save_build_follow_through(
        response,
        requested_apply_build=True,
        apply_build=True,
        changed=True,
        build_plan={"build_required": False},
        run_build=lambda: (calls.append("run") or (True, {"ok": True})),
    )

    assert_equal(calls, [], "build calls")
    assert_equal(response["build_requested"], False, "build requested")
    assert_equal(
        response["build_skipped"],
        {
            "reason": "no_public_build_artifacts",
            "summary": "Changed fields do not require public build artifacts.",
        },
        "no-artifacts skip payload",
    )


def test_moment_skip_payloads_use_message_key() -> None:
    response = {"ok": True}

    save_build.apply_save_build_follow_through(
        response,
        requested_apply_build=True,
        apply_build=False,
        changed=True,
        build_plan={"build_required": True},
        unpublished_reason="moment_not_published",
        unpublished_message="Public moment update skipped because the saved moment is not published.",
        unpublished_message_key="message",
        run_build=lambda: (True, {"ok": True}),
    )

    assert_equal(
        response["build_skipped"],
        {
            "reason": "moment_not_published",
            "message": "Public moment update skipped because the saved moment is not published.",
        },
        "moment unpublished skip payload",
    )

    response = {"ok": True}
    save_build.apply_save_build_follow_through(
        response,
        requested_apply_build=True,
        apply_build=True,
        changed=True,
        build_plan={"build_required": False},
        no_artifacts_message_key="message",
        run_build=lambda: (True, {"ok": True}),
    )

    assert_equal(
        response["build_skipped"],
        {
            "reason": "no_public_build_artifacts",
            "message": "Changed fields do not require public build artifacts.",
        },
        "moment no-artifacts skip payload",
    )


def test_build_failure_payload_stays_attached_to_save_response() -> None:
    response = {"ok": True}

    build_payload = save_build.apply_save_build_follow_through(
        response,
        requested_apply_build=True,
        apply_build=True,
        changed=True,
        build_plan={"build_required": True},
        run_build=lambda: (False, {"ok": False, "error": "build failed", "failed_step": "search"}),
    )

    assert_equal(response["build_requested"], True, "build requested")
    assert_equal(
        response["build"],
        {"ok": False, "error": "build failed", "failed_step": "search"},
        "failure build payload",
    )
    assert_equal(build_payload, {"ok": False, "error": "build failed", "failed_step": "search"}, "return payload")


def main() -> None:
    test_published_changed_save_runs_build_and_preserves_payload()
    test_requested_draft_save_reports_unpublished_skip_without_build()
    test_no_public_artifacts_reports_existing_skip_reason()
    test_moment_skip_payloads_use_message_key()
    test_build_failure_payload_stays_attached_to_save_response()
    print("Catalogue save build tests OK")


if __name__ == "__main__":
    main()
