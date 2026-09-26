"""Shared OS opening for local targets already confined by their domain owner."""

from pathlib import Path
import subprocess
import sys


class FinderUnavailableError(ValueError):
    """The current platform cannot perform Finder actions."""


def open_in_finder(
    repo_root: Path, path: Path, *, reveal: bool, dry_run: bool, failure_message: str,
) -> None:
    """Open a directory or reveal a file after caller-owned identity/path validation.

    Dry runs retain the platform check but never launch an OS process. This helper
    does not select a workspace root or interpret browser-supplied targets.
    """
    if sys.platform != "darwin":
        raise FinderUnavailableError("Open in Finder is unavailable on this platform")
    if not dry_run:
        command = ["open", "-R", str(path)] if reveal else ["open", str(path)]
        completed = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(failure_message)
