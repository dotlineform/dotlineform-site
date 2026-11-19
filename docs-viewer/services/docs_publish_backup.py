"""Commit and push the saved Docs data and site content authorized by Publish."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


DOCS_BACKUP_PATHS = (
    "working/source",
    "working/assets/media",
    "working/catalogue-updates-pending.json",
    "working/catalogue-publish-pending.json",
    "working/docs-publish-pending.json",
)
SITE_BACKUP_PATHS = (
    "site/assets/data/docs/",
    "site/assets/data/catalogue/",
    "site/assets/data/search/",
    "studio/data/canonical/catalogue/works.json",
    "studio/data/canonical/catalogue/series.json",
    "studio/data/canonical/catalogue/galleries.json",
    "studio/data/canonical/catalogue/galleries-by-work.json",
    "studio/data/canonical/catalogue/series-galleries.json",
)
UNMERGED_STATUS = {b"DD", b"AU", b"UD", b"UA", b"DU", b"AA", b"UU"}


class PublishBackupError(RuntimeError):
    """A Git backup could not complete."""


def _git(root: Path, operation: str, *args: str, paths: bytes | None = None) -> bytes:
    try:
        return subprocess.run(
            ["git", "--literal-pathspecs", *args], cwd=root,
            input=paths or b"", capture_output=True, check=True, timeout=120,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        ).stdout
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode(errors="replace").strip() or f"Git exited with status {error.returncode}."
        raise PublishBackupError(f"Could not {operation}. {detail}") from error
    except subprocess.TimeoutExpired as error:
        raise PublishBackupError(f"Timed out while trying to {operation}.") from error
    except OSError as error:
        raise PublishBackupError(f"Could not {operation}. {error.strerror or 'Git could not start.'}") from error


def _check_repository(root: Path, repository: str) -> None:
    checkout = _git(root, "locate the Git checkout", "rev-parse", "--show-toplevel")
    if Path(os.fsdecode(checkout.rstrip(b"\n"))).resolve() != root:
        raise PublishBackupError(f"The backup root must be the {repository} checkout root.")
    branch = _git(root, "read the Git branch", "branch", "--show-current").strip()
    if branch != b"main":
        raise PublishBackupError(f"Check out main in {repository}.")
    origins = _git(root, "read the Git push destination", "remote", "get-url", "--push", "--all", "origin")
    urls = origins.decode(errors="replace").splitlines()
    expected = {f"https://github.com/{repository}", f"git@github.com:{repository}"}
    if len(urls) != 1 or urls[0].removesuffix(".git") not in expected:
        raise PublishBackupError(f"Set the checkout's origin to {repository}.")


def _commit_changes(root: Path, scope: tuple[str, ...], message: str) -> bool:
    status = _git(root, "read backup changes", "status", "--porcelain=v1", "-z",
                  "--no-renames", "--untracked-files=normal", "--", *scope)
    changes = status.split(b"\0")[:-1]
    if any(change[:2] in UNMERGED_STATUS for change in changes):
        raise PublishBackupError("Resolve Git conflicts in the backup paths before retrying Publish.")
    unstaged = b"".join(change[3:] + b"\0" for change in changes if change[1:2] != b" ")
    if unstaged:
        _git(root, "stage backup changes", "add", "--all", "--pathspec-from-file=-", "--pathspec-file-nul", paths=unstaged)
    staged = _git(root, "select staged backup changes", "diff", "--cached", "--name-only", "--no-renames", "-z", "--", *scope)
    if staged:
        _git(root, "commit the backup", "commit", "--only", "-m", message,
             "--pathspec-from-file=-", "--pathspec-file-nul", paths=staged)
    return bool(staged)


def _push_backup(root: Path, *, committed: bool) -> None:
    try:
        _git(root, "push the backup", "push", "--no-follow-tags", "--recurse-submodules=no", "origin", "HEAD:refs/heads/main")
    except PublishBackupError as error:
        if committed:
            raise PublishBackupError(f"The backup commit is saved locally. {error}") from error
        raise


def backup_docs_workspace(root: Path) -> None:
    _check_repository(root, "dotlineform/docs-viewer-data")
    committed = _commit_changes(root, DOCS_BACKUP_PATHS, "Back up Docs workspace")
    _push_backup(root, committed=committed)


def backup_site_content(root: Path) -> None:
    _check_repository(root, "dotlineform/dotlineform-site")
    outgoing = _git(root, "inspect unpushed site commits", "log", "--format=", "--no-show-signature", "--name-only", "--no-renames",
                    "--diff-merges=first-parent", "-z", "refs/remotes/origin/main..HEAD", "--")
    scope = tuple(os.fsencode(path) for path in SITE_BACKUP_PATHS)
    for path in outgoing.split(b"\0")[:-1]:
        if not any(path == allowed or (allowed.endswith(b"/") and path.startswith(allowed)) for allowed in scope):
            raise PublishBackupError("Site main has unpushed commits outside the Publish backup paths. Handle those commits separately, then retry Publish.")
    committed = _commit_changes(root, SITE_BACKUP_PATHS, "Back up published site content")
    if committed or outgoing:
        _push_backup(root, committed=committed)
