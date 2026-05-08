"""Save-time public build follow-through helpers for catalogue writes."""

from __future__ import annotations

from typing import Any, Callable, Mapping, MutableMapping


BuildRunner = Callable[[], tuple[bool, Mapping[str, Any]]]

NO_PUBLIC_ARTIFACTS_REASON = "no_public_build_artifacts"
NO_PUBLIC_ARTIFACTS_MESSAGE = "Changed fields do not require public build artifacts."


def skip_payload(reason: str, message: str, *, message_key: str = "summary") -> dict[str, str]:
    return {
        "reason": reason,
        message_key: message,
    }


def apply_save_build_follow_through(
    response_payload: MutableMapping[str, Any],
    *,
    requested_apply_build: bool,
    apply_build: bool,
    changed: bool,
    build_plan: Mapping[str, Any],
    run_build: BuildRunner,
    unpublished_reason: str = "",
    unpublished_message: str = "",
    unpublished_message_key: str = "summary",
    no_artifacts_message_key: str = "summary",
) -> Mapping[str, Any] | None:
    """Apply common save-time build response decisions and optional execution."""

    response_payload["build_requested"] = bool(apply_build and changed)
    if requested_apply_build and changed and not apply_build and unpublished_reason:
        response_payload["build_skipped"] = skip_payload(
            unpublished_reason,
            unpublished_message,
            message_key=unpublished_message_key,
        )
        return None

    if apply_build and changed and not build_plan.get("build_required", True):
        response_payload["build_requested"] = False
        response_payload["build_skipped"] = skip_payload(
            NO_PUBLIC_ARTIFACTS_REASON,
            NO_PUBLIC_ARTIFACTS_MESSAGE,
            message_key=no_artifacts_message_key,
        )
        return None

    if apply_build and changed:
        _build_success, build_payload = run_build()
        response_payload["build"] = dict(build_payload)
        return build_payload

    return None
