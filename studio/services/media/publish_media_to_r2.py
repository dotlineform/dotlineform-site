#!/usr/bin/env python3
"""Maintain Catalogue media on R2 and materialize staged Docs media locally."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Protocol, Sequence

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

from catalogue.catalogue_output_paths import catalogue_workspace_config
from studio.shared.python.local_env import runtime_env
from studio.shared.python.media_files import content_type_for, file_md5
from studio.shared.python.r2_client import DEFAULT_ENV_FILES, R2Client, RemoteObject, load_r2_credentials

@dataclass(frozen=True)
class CatalogueKind:
    cli_name: str
    config_prefix_key: str


CATALOGUE_KINDS: Dict[str, CatalogueKind] = {
    "works": CatalogueKind("works", "media_image_works"),
}


@dataclass(frozen=True)
class CataloguePrimaryPolicy:
    remote_prefixes: Mapping[str, str]
    rendition_suffixes: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class LocalMediaObject:
    scope: str
    kind: str
    item_id: str
    width: int
    local_path: Path
    source_root: Path
    object_key: str
    size: int
    md5: str
    blocked_reason: str = ""

    @property
    def relative_path(self) -> str:
        return self.local_path.relative_to(self.source_root).as_posix()


@dataclass
class PublishResult:
    scope: str
    kind: str
    item_id: str
    width: int
    local_path: str
    object_key: str
    size: int
    md5: str
    status: str
    reason: str = ""
    remote_size: int | None = None
    remote_etag: str = ""


@dataclass(frozen=True)
class RemoteMediaObject:
    scope: str
    kind: str
    item_id: str
    width: int
    object_key: str


@dataclass
class MissingVariant:
    kind: str
    item_id: str
    missing_widths: List[int]
    present_widths: List[int]


class RemoteClient(Protocol):
    def head_object(self, key: str) -> RemoteObject | None:
        ...

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        ...

    def delete_object(self, key: str) -> None:
        ...


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Maintain Catalogue media on R2 or copy one staged file into local Docs Working media.",
    )
    ap.add_argument("--scope", choices=["catalogue", "docs"], default="catalogue")
    ap.add_argument(
        "--kind",
        choices=sorted({*CATALOGUE_KINDS, "files", "img"}),
        help="Catalogue media kind or Docs Working media class",
    )
    ap.add_argument("--id", dest="item_id", help="Specific Work ID")
    ap.add_argument("--docs-collection", help="Optional configured Docs collection for --scope docs")
    ap.add_argument("--docs-doc-id", help="Exact owning document ID for --scope docs")
    ap.add_argument(
        "--staged-filename",
        help="One direct-child filename under the shared import-staging drop-zone for --scope docs",
    )
    ap.add_argument("--all", action="store_true", help="Publish every selected kind")
    ap.add_argument("--changed-only", action="store_true", help="Omit unchanged objects from logs and JSON reports")
    ap.add_argument("--force", action="store_true", help="Replace a differing Catalogue R2 object or Docs Working file")
    ap.add_argument("--allow-partial", action="store_true", help="Allow uploads when an item is missing size variants")
    ap.add_argument("--write", action="store_true", help="Apply the selected change. The default is a dry run.")
    ap.add_argument("--delete", action="store_true", help="Delete selected remote primary variants instead of uploading")
    ap.add_argument("--report-json", help="Optional JSON report path")
    ap.add_argument("--env-file", action="append", default=[], help="Additional local env file to load")
    ap.add_argument("--repo-root", help=argparse.SUPPRESS)
    return ap.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else REPO_ROOT
    if args.scope == "docs":
        if args.delete:
            raise SystemExit("Error: --delete is a Catalogue-only option.")
        if args.all or args.item_id:
            raise SystemExit("Error: --all and --id are Catalogue-only options. Use --staged-filename for Docs media.")
        if args.allow_partial or args.changed_only:
            raise SystemExit("Error: --allow-partial and --changed-only are catalogue-only options.")
        if args.kind not in {"files", "img"}:
            raise SystemExit("Error: Docs materialization requires --kind img or --kind files.")
        if not args.staged_filename:
            raise SystemExit("Error: Docs materialization requires --staged-filename <filename>.")
        if not args.docs_doc_id:
            raise SystemExit("Error: Docs materialization requires --docs-doc-id <doc_id>.")
        from docs_media_storage import run_docs_staged_media_publish

        env_files = [repo_root / path for path in DEFAULT_ENV_FILES]
        env_files.extend(Path(path).expanduser() for path in args.env_file)
        try:
            report = run_docs_staged_media_publish(
                repo_root,
                collection=args.docs_collection,
                doc_id=args.docs_doc_id,
                media_class=args.kind,
                staged_filename=args.staged_filename,
                write=args.write,
                force=args.force,
                env_files=env_files,
            )
        except (RuntimeError, ValueError) as exc:
            raise SystemExit(f"Error: {exc}") from exc
        print_docs_report(report)
        write_report(repo_root=repo_root, report=report, report_json=args.report_json)
        failed_statuses = {"blocked_changed", "failed", "not_attempted"}
        return 1 if any(report["counts"].get(status, 0) for status in failed_statuses) else 0
    if args.docs_collection or args.docs_doc_id or args.staged_filename:
        raise SystemExit("Error: --docs-collection, --docs-doc-id and --staged-filename require --scope docs.")
    if args.kind in {"files", "img"}:
        raise SystemExit("Error: catalogue publishing requires --kind works.")
    if args.delete and not args.item_id:
        raise SystemExit("Error: remote delete requires --kind and --id.")
    if args.delete and not args.kind:
        raise SystemExit("Error: remote delete requires --kind.")
    if args.delete and args.all:
        raise SystemExit("Error: remote delete does not support --all.")
    if args.delete and args.allow_partial:
        raise SystemExit("Error: --allow-partial is only valid for upload planning.")
    if args.delete and args.changed_only:
        raise SystemExit("Error: --changed-only is only valid for upload planning.")
    if not args.all and not args.item_id:
        raise SystemExit("Error: choose --all or pass --id <id>.")
    if args.all and args.item_id:
        raise SystemExit("Error: use --all or --id, not both.")
    if args.item_id:
        validate_item_id(args.item_id)

    env_files = [repo_root / path for path in DEFAULT_ENV_FILES]
    env_files.extend(Path(path).expanduser() for path in args.env_file)
    credentials = load_r2_credentials(env_files=env_files)
    client = R2Client(credentials)

    if args.delete:
        report = run_catalogue_remote_delete(
            repo_root=repo_root,
            targets=[(args.kind, args.item_id)],
            write=args.write,
            client=client,
            env_files=env_files,
        )
        print_report(report)
        write_report(repo_root=repo_root, report=report, report_json=args.report_json)
        failed = report["counts"].get("failed", 0)
        return 1 if failed else 0

    report = run_catalogue_upload(
        repo_root=repo_root,
        kind=args.kind,
        item_id=args.item_id,
        write=args.write,
        force=args.force,
        changed_only=args.changed_only,
        allow_partial=args.allow_partial,
        client=client,
        env_files=env_files,
    )
    print_report(report)
    write_report(repo_root=repo_root, report=report, report_json=args.report_json)

    failed = report["counts"].get("failed", 0)
    blocked = sum(count for status, count in report["counts"].items() if status.startswith("blocked"))
    return 1 if failed or blocked else 0


def run_catalogue_upload(
    *,
    repo_root: Path,
    kind: str | None,
    item_id: str | None,
    write: bool,
    force: bool,
    changed_only: bool = False,
    allow_partial: bool = False,
    client: RemoteClient | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Dict[str, object]:
    """Run one catalogue upload plan for CLI or Local Studio callers."""

    resolved_root = repo_root.resolve()
    if kind is not None and kind not in CATALOGUE_KINDS:
        raise SystemExit(f"Error: unsupported catalogue media kind: {kind!r}")
    if item_id:
        validate_item_id(item_id)
    if kind and item_id:
        return run_catalogue_upload_targets(
            repo_root=resolved_root,
            targets=[(kind, item_id)],
            write=write,
            force=force,
            changed_only=changed_only,
            allow_partial=allow_partial,
            client=client,
            env_files=env_files,
            environ=environ,
        )
    selected_env_files = list(env_files) if env_files is not None else [
        resolved_root / path for path in DEFAULT_ENV_FILES
    ]
    try:
        combined_env = runtime_env(environ=environ, env_files=selected_env_files)
        media_root = catalogue_workspace_config(resolved_root, environ=combined_env).assets.work_primary.path
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    remote_client = client
    if remote_client is None:
        remote_client = R2Client(load_r2_credentials(env_files=selected_env_files, environ=environ))

    policy = load_catalogue_primary_policy(resolved_root)
    objects, missing = discover_catalogue_primary_objects(
        policy=policy,
        media_root=media_root,
        kinds=[kind] if kind else sorted(CATALOGUE_KINDS),
        item_id=item_id,
        allow_partial=allow_partial,
    )
    if item_id and not objects:
        selected_kind = kind or "any catalogue kind"
        raise SystemExit(
            "Error: no matching catalogue primary derivatives found for "
            f"{selected_kind} id {item_id!r} in the configured shared primary assets."
        )
    results = plan_and_publish(
        objects=objects,
        client=remote_client,
        write=write,
        force=force,
        changed_only=changed_only,
    )
    return build_report(
        results=results,
        missing=missing,
        write=write,
        force=force,
        changed_only=changed_only,
        action="upload",
    )


def run_catalogue_upload_targets(
    *,
    repo_root: Path,
    targets: Sequence[tuple[str, str]],
    write: bool,
    force: bool,
    changed_only: bool = False,
    allow_partial: bool = False,
    client: RemoteClient | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Dict[str, object]:
    """Publish exact catalogue media targets through one remote client."""

    resolved_root = repo_root.resolve()
    normalized_targets: list[tuple[str, str]] = []
    for kind, item_id in targets:
        kind_name = str(kind or "").strip()
        normalized_id = str(item_id or "").strip()
        if kind_name not in CATALOGUE_KINDS:
            raise SystemExit(f"Error: unsupported catalogue media kind: {kind_name!r}")
        validate_item_id(normalized_id)
        target = (kind_name, normalized_id)
        if target not in normalized_targets:
            normalized_targets.append(target)
    if not normalized_targets:
        raise SystemExit("Error: at least one exact catalogue media upload target is required.")

    selected_env_files = list(env_files) if env_files is not None else [
        resolved_root / path for path in DEFAULT_ENV_FILES
    ]
    try:
        combined_env = runtime_env(environ=environ, env_files=selected_env_files)
        media_root = catalogue_workspace_config(resolved_root, environ=combined_env).assets.work_primary.path
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    remote_client = client
    if remote_client is None:
        remote_client = R2Client(load_r2_credentials(env_files=selected_env_files, environ=environ))

    policy = load_catalogue_primary_policy(resolved_root)
    objects: list[LocalMediaObject] = []
    missing: list[MissingVariant] = []
    for kind_name, item_id in normalized_targets:
        target_objects, target_missing = discover_catalogue_primary_objects(
            policy=policy,
            media_root=media_root,
            kinds=[kind_name],
            item_id=item_id,
            allow_partial=allow_partial,
        )
        if not target_objects:
            raise SystemExit(
                "Error: no matching catalogue primary derivatives found for "
                f"{kind_name} id {item_id!r} under "
                "the configured shared primary assets."
            )
        objects.extend(target_objects)
        missing.extend(target_missing)

    results = plan_and_publish(
        objects=objects,
        client=remote_client,
        write=write,
        force=force,
        changed_only=changed_only,
    )
    return build_report(
        results=results,
        missing=missing,
        write=write,
        force=force,
        changed_only=changed_only,
        action="upload",
    )


def run_catalogue_remote_delete(
    *,
    repo_root: Path,
    targets: Sequence[tuple[str, str]],
    write: bool,
    client: RemoteClient | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Dict[str, object]:
    """Delete exact catalogue media targets for CLI or Local Studio callers."""

    resolved_root = repo_root.resolve()
    normalized_targets: list[tuple[str, str]] = []
    for kind, item_id in targets:
        kind_name = str(kind or "").strip()
        normalized_id = str(item_id or "").strip()
        if kind_name not in CATALOGUE_KINDS:
            raise SystemExit(f"Error: unsupported catalogue media kind: {kind_name!r}")
        validate_item_id(normalized_id)
        target = (kind_name, normalized_id)
        if target not in normalized_targets:
            normalized_targets.append(target)
    if not normalized_targets:
        raise SystemExit("Error: at least one exact catalogue media delete target is required.")

    selected_env_files = list(env_files) if env_files is not None else [
        resolved_root / path for path in DEFAULT_ENV_FILES
    ]
    remote_client = client
    if remote_client is None:
        remote_client = R2Client(load_r2_credentials(env_files=selected_env_files, environ=environ))

    policy = load_catalogue_primary_policy(resolved_root)
    objects = [
        obj
        for kind_name, item_id in normalized_targets
        for obj in build_catalogue_remote_objects(
            policy=policy,
            kind_name=kind_name,
            item_id=item_id,
        )
    ]
    results = plan_and_delete(objects=objects, client=remote_client, write=write)
    return build_report(
        results=results,
        missing=[],
        write=write,
        force=False,
        changed_only=False,
        action="delete",
    )


def write_report(*, repo_root: Path, report: Mapping[str, object], report_json: str | None) -> None:
    if not report_json:
        return
    report_path = Path(report_json).expanduser()
    if not report_path.is_absolute():
        report_path = repo_root / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Report written: {report_path.relative_to(repo_root) if is_relative_to(report_path, repo_root) else report_path}")


def validate_item_id(item_id: str) -> None:
    if item_id in {"", ".", ".."} or "/" in item_id or "\\" in item_id or "\x00" in item_id:
        raise SystemExit(f"Error: invalid id: {item_id!r}")


def discover_catalogue_primary_objects(
    *,
    policy: CataloguePrimaryPolicy,
    media_root: Path,
    kinds: Sequence[str],
    item_id: str | None = None,
    allow_partial: bool = False,
) -> tuple[List[LocalMediaObject], List[MissingVariant]]:
    objects: List[LocalMediaObject] = []
    missing: List[MissingVariant] = []

    for kind_name in kinds:
        kind = CATALOGUE_KINDS[kind_name]
        source_root = media_root
        groups = collect_primary_groups(source_root, policy.rendition_suffixes, item_id=item_id)
        remote_prefix = policy.remote_prefixes[kind.config_prefix_key]

        for current_id in sorted(groups):
            variants = groups[current_id]
            present_widths = sorted(variants)
            missing_widths = [width for width, _ in policy.rendition_suffixes if width not in variants]
            blocked_reason = ""
            if missing_widths:
                missing.append(
                    MissingVariant(
                        kind=kind_name,
                        item_id=current_id,
                        missing_widths=missing_widths,
                        present_widths=present_widths,
                    )
                )
                if not allow_partial:
                    blocked_reason = f"missing variants: {', '.join(str(width) for width in missing_widths)}"

            for width in present_widths:
                path = ensure_allowed_file(variants[width], source_root)
                object_key = f"{remote_prefix}/{path.name}"
                objects.append(
                    LocalMediaObject(
                        scope="catalogue",
                        kind=kind_name,
                        item_id=current_id,
                        width=width,
                        local_path=path,
                        source_root=source_root,
                        object_key=object_key,
                        size=path.stat().st_size,
                        md5=file_md5(path),
                        blocked_reason=blocked_reason,
                    )
                )

    return objects, missing

def build_catalogue_remote_objects(*, policy: CataloguePrimaryPolicy, kind_name: str, item_id: str) -> List[RemoteMediaObject]:
    kind = CATALOGUE_KINDS[kind_name]
    remote_prefix = policy.remote_prefixes[kind.config_prefix_key]
    return [
        RemoteMediaObject(
            scope="catalogue",
            kind=kind_name,
            item_id=item_id,
            width=width,
            object_key=f"{remote_prefix}/{item_id}{suffix}",
        )
        for width, suffix in policy.rendition_suffixes
    ]


def collect_primary_groups(
    source_root: Path,
    rendition_suffixes: tuple[tuple[int, str], ...],
    item_id: str | None = None,
) -> Dict[str, Dict[int, Path]]:
    groups: Dict[str, Dict[int, Path]] = {}
    if not source_root.exists():
        return groups
    for path in sorted(source_root.iterdir()):
        if not path.is_file():
            continue
        parsed = parse_primary_filename(path.name, rendition_suffixes)
        if parsed is None:
            continue
        current_id, width = parsed
        if item_id and current_id != item_id:
            continue
        groups.setdefault(current_id, {})[width] = path
    return groups


def parse_primary_filename(filename: str, rendition_suffixes: tuple[tuple[int, str], ...]) -> tuple[str, int] | None:
    for width, suffix in rendition_suffixes:
        if filename.endswith(suffix):
            item_id = filename[: -len(suffix)]
            if item_id:
                return item_id, width
    return None


def ensure_allowed_file(path: Path, source_root: Path) -> Path:
    resolved_root = source_root.resolve()
    resolved_path = path.resolve()
    if not is_relative_to(resolved_path, resolved_root):
        raise SystemExit(f"Error: refusing media path outside allowlisted root: {path}")
    if not resolved_path.is_file():
        raise SystemExit(f"Error: media path is not a file: {path}")
    return resolved_path


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def load_catalogue_primary_policy(repo_root: Path) -> CataloguePrimaryPolicy:
    from pipeline_config import load_pipeline_config

    pipeline = load_pipeline_config(repo_root=repo_root)
    primary = pipeline["variants"]["primary"]
    suffix = str(primary["suffix"])
    output_format = str(pipeline["encoding"]["format"])
    return CataloguePrimaryPolicy(
        remote_prefixes=load_media_prefixes(repo_root),
        rendition_suffixes=tuple(
            (width, f"-{suffix}-{width}.{output_format}")
            for width in map(int, primary["widths"])
        ),
    )


def load_media_prefixes(repo_root: Path) -> Dict[str, str]:
    config_path = repo_root / "site-tools" / "config" / "site-tools.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    media = payload.get("media") if isinstance(payload, dict) else None
    if not isinstance(media, dict):
        raise SystemExit(f"Error: site-tools media config missing in {config_path}")
    return {
        "media_image_works": normalize_remote_prefix(str(media["image_works"]))
    }


def normalize_remote_prefix(prefix: str) -> str:
    cleaned = prefix.strip().strip("/")
    if cleaned == "" or "\\" in cleaned or ".." in cleaned.split("/"):
        raise SystemExit(f"Error: invalid media remote prefix: {prefix!r}")
    if cleaned == "archive" or cleaned.startswith("archive/"):
        raise SystemExit("Error: active Catalogue media cannot write the frozen archive.")
    return cleaned


def plan_and_publish(
    *,
    objects: Sequence[LocalMediaObject],
    client: RemoteClient,
    write: bool,
    force: bool,
    changed_only: bool = False,
) -> List[PublishResult]:
    results: List[PublishResult] = []
    for obj in objects:
        if obj.blocked_reason:
            result = result_for(obj, status="blocked_partial", reason=obj.blocked_reason)
            results.append(result)
            continue

        try:
            remote = client.head_object(obj.object_key)
        except Exception as exc:  # pragma: no cover - defensive CLI boundary
            results.append(result_for(obj, status="failed", reason=f"remote check failed: {exc}"))
            continue

        if remote is not None and remote_matches(obj, remote):
            results.append(
                result_for(
                    obj,
                    status="unchanged",
                    remote=remote,
                    reason="remote size and ETag match local file",
                )
            )
            continue

        if remote is not None and not force:
            results.append(
                result_for(
                    obj,
                    status="blocked_changed",
                    remote=remote,
                    reason="remote object differs; pass --force to overwrite",
                )
            )
            continue

        if not write:
            results.append(
                result_for(
                    obj,
                    status="would_overwrite" if remote is not None else "would_upload",
                    remote=remote,
                    reason="dry-run",
                )
            )
            continue

        try:
            client.put_object(obj.object_key, obj.local_path, content_type_for(obj.local_path))
            results.append(
                result_for(
                    obj,
                    status="overwritten" if remote is not None else "uploaded",
                    remote=remote,
                )
            )
        except Exception as exc:  # pragma: no cover - defensive CLI boundary
            results.append(result_for(obj, status="failed", remote=remote, reason=f"upload failed: {exc}"))
    return results


def plan_and_delete(
    *,
    objects: Sequence[RemoteMediaObject],
    client: RemoteClient,
    write: bool,
) -> List[PublishResult]:
    results: List[PublishResult] = []
    for obj in objects:
        try:
            remote = client.head_object(obj.object_key)
        except Exception as exc:  # pragma: no cover - defensive CLI boundary
            results.append(delete_result_for(obj, status="failed", reason=f"remote check failed: {exc}"))
            continue

        if remote is None:
            results.append(delete_result_for(obj, status="missing", reason="remote object not found"))
            continue

        if not write:
            results.append(delete_result_for(obj, status="would_delete", remote=remote, reason="dry-run"))
            continue

        try:
            client.delete_object(obj.object_key)
            results.append(delete_result_for(obj, status="deleted", remote=remote))
        except Exception as exc:  # pragma: no cover - defensive CLI boundary
            results.append(delete_result_for(obj, status="failed", remote=remote, reason=f"delete failed: {exc}"))
    return results


def remote_matches(obj: LocalMediaObject, remote: RemoteObject) -> bool:
    etag = remote.etag.strip().strip('"').lower()
    return remote.size == obj.size and etag == obj.md5


def result_for(
    obj: LocalMediaObject,
    *,
    status: str,
    reason: str = "",
    remote: RemoteObject | None = None,
) -> PublishResult:
    return PublishResult(
        scope=obj.scope,
        kind=obj.kind,
        item_id=obj.item_id,
        width=obj.width,
        local_path=obj.relative_path,
        object_key=obj.object_key,
        size=obj.size,
        md5=obj.md5,
        status=status,
        reason=reason,
        remote_size=remote.size if remote else None,
        remote_etag=remote.etag if remote else "",
    )


def delete_result_for(
    obj: RemoteMediaObject,
    *,
    status: str,
    reason: str = "",
    remote: RemoteObject | None = None,
) -> PublishResult:
    return PublishResult(
        scope=obj.scope,
        kind=obj.kind,
        item_id=obj.item_id,
        width=obj.width,
        local_path="",
        object_key=obj.object_key,
        size=0,
        md5="",
        status=status,
        reason=reason,
        remote_size=remote.size if remote else None,
        remote_etag=remote.etag if remote else "",
    )


def build_report(
    *,
    results: Sequence[PublishResult],
    missing: Sequence[MissingVariant],
    write: bool,
    force: bool,
    changed_only: bool,
    action: str,
) -> Dict[str, object]:
    visible_results = [result for result in results if not (changed_only and result.status == "unchanged")]
    counts: Dict[str, int] = {}
    for result in visible_results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "catalogue",
        "action": action,
        "mode": "write" if write else "dry-run",
        "force": force,
        "changed_only": changed_only,
        "counts": dict(sorted(counts.items())),
        "missing_variants": [asdict(item) for item in missing],
        "objects": [asdict(result) for result in visible_results],
    }


def print_report(report: Mapping[str, object]) -> None:
    print(f"R2 media publish {report['mode']}")
    counts = report.get("counts", {})
    if isinstance(counts, Mapping) and counts:
        print("Counts: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)))
    else:
        print("Counts: no matching objects")

    missing = report.get("missing_variants", [])
    if isinstance(missing, list) and missing:
        print("Missing variants:")
        for item in missing:
            if not isinstance(item, Mapping):
                continue
            print(
                "  "
                f"{item.get('kind')} {item.get('item_id')}: "
                f"missing {item.get('missing_widths')} "
                f"(present {item.get('present_widths')})"
            )

    objects = report.get("objects", [])
    if isinstance(objects, list):
        for item in objects:
            if not isinstance(item, Mapping):
                continue
            reason = f" - {item.get('reason')}" if item.get("reason") else ""
            print(
                f"{item.get('status')}: {item.get('kind')} {item.get('item_id')} "
                f"{item.get('width')} -> {item.get('object_key')}{reason}"
            )


def print_docs_report(report: Mapping[str, object]) -> None:
    status_labels = {"would_upload": "would_copy", "uploaded": "copied"}
    print(f"Docs Working media materialization ({report['mode']}) for {report.get('collection') or 'ordinary documents'}")
    counts = report.get("counts", {})
    if isinstance(counts, Mapping) and counts:
        print("Counts: " + ", ".join(f"{status_labels.get(key, key)}={counts[key]}" for key in sorted(counts)))
    else:
        print("No matching files.")
    objects = report.get("objects", [])
    if not isinstance(objects, list):
        return
    for item in objects:
        if not isinstance(item, Mapping):
            continue
        status = item.get("status")
        reason = f" - {item.get('reason')}" if item.get("reason") else ""
        print(
            f"{status_labels.get(status, status)}: {item.get('media_class')}/{item.get('filename')}"
            f"{reason}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
