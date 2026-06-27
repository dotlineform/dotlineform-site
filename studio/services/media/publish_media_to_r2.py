#!/usr/bin/env python3
"""Publish approved local media derivatives to Cloudflare R2."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import mimetypes
import sys
import urllib.error
import urllib.parse
import urllib.request
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

try:
    from pipeline_config import (
        load_pipeline_config,
        media_mode_output_subdir,
    )
    from local_env import SITE_ENV_REL_PATH, runtime_env
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from studio.shared.python.pipeline_config import (
        load_pipeline_config,
        media_mode_output_subdir,
    )
    from studio.shared.python.local_env import SITE_ENV_REL_PATH, runtime_env


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PRIMARY_SUFFIX = str(PIPELINE_CONFIG["variants"]["primary"]["suffix"])
PRIMARY_OUTPUT_SUBDIR = str(PIPELINE_CONFIG["variants"]["primary"]["output_subdir"])
OUTPUT_FORMAT = str(PIPELINE_CONFIG["encoding"]["format"])
PRIMARY_WIDTHS = [int(v) for v in PIPELINE_CONFIG["variants"]["compatibility"]["generate_widths"]]

R2_ENV_VARS = (
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET",
    "R2_ENDPOINT",
)

DEFAULT_ENV_FILES = (
    SITE_ENV_REL_PATH,
)


@dataclass(frozen=True)
class CatalogueKind:
    cli_name: str
    pipeline_mode: str
    config_prefix_key: str


CATALOGUE_KINDS: Dict[str, CatalogueKind] = {
    "works": CatalogueKind("works", "work", "media_image_works"),
    "work_details": CatalogueKind("work_details", "work_details", "media_image_work_details"),
    "moments": CatalogueKind("moments", "moment", "media_image_moments"),
}


@dataclass(frozen=True)
class R2Credentials:
    account_id: str
    access_key_id: str
    secret_access_key: str
    bucket: str
    endpoint: str


@dataclass(frozen=True)
class RemoteObject:
    size: int | None
    etag: str


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
        description="Publish approved media derivatives to Cloudflare R2. Defaults to dry-run.",
    )
    ap.add_argument("--scope", choices=["catalogue", "docs"], default="catalogue")
    ap.add_argument("--kind", choices=sorted(CATALOGUE_KINDS), help="Catalogue media kind to publish")
    ap.add_argument("--id", dest="item_id", help="Specific work, work-detail, or moment id")
    ap.add_argument("--all", action="store_true", help="Publish every selected kind")
    ap.add_argument("--changed-only", action="store_true", help="Omit unchanged objects from logs and JSON reports")
    ap.add_argument("--force", action="store_true", help="Overwrite changed remote objects")
    ap.add_argument("--allow-partial", action="store_true", help="Allow uploads when an item is missing size variants")
    ap.add_argument("--write", action="store_true", help="Upload objects; without this flag the command is a dry-run")
    ap.add_argument("--delete", action="store_true", help="Delete selected remote primary variants instead of uploading")
    ap.add_argument("--report-json", help="Optional JSON report path")
    ap.add_argument("--env-file", action="append", default=[], help="Additional local env file to load")
    ap.add_argument("--repo-root", help=argparse.SUPPRESS)
    return ap.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else REPO_ROOT
    if args.scope == "docs":
        raise SystemExit("Error: docs media publishing is not implemented in this milestone.")
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
        objects = build_catalogue_remote_objects(repo_root=repo_root, kind_name=args.kind, item_id=args.item_id)
        results = plan_and_delete(objects=objects, client=client, write=args.write)
        report = build_report(
            results=results,
            missing=[],
            write=args.write,
            force=False,
            changed_only=False,
            action="delete",
        )
        print_report(report)
        write_report(repo_root=repo_root, report=report, report_json=args.report_json)
        failed = report["counts"].get("failed", 0)
        return 1 if failed else 0

    objects, missing = discover_catalogue_primary_objects(
        repo_root=repo_root,
        kinds=[args.kind] if args.kind else sorted(CATALOGUE_KINDS),
        item_id=args.item_id,
        allow_partial=args.allow_partial,
    )
    if args.item_id and not objects:
        selected_kind = args.kind or "any catalogue kind"
        raise SystemExit(
            "Error: no matching catalogue primary derivatives found for "
            f"{selected_kind} id {args.item_id!r} under {catalogue_media_staging_root(repo_root)}."
        )
    results = plan_and_publish(
        objects=objects,
        client=client,
        write=args.write,
        force=args.force,
        changed_only=args.changed_only,
    )

    report = build_report(
        results=results,
        missing=missing,
        write=args.write,
        force=args.force,
        changed_only=args.changed_only,
        action="upload",
    )
    print_report(report)
    write_report(repo_root=repo_root, report=report, report_json=args.report_json)

    failed = report["counts"].get("failed", 0)
    blocked = sum(count for status, count in report["counts"].items() if status.startswith("blocked"))
    return 1 if failed or blocked else 0


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


def load_r2_credentials(
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> R2Credentials:
    try:
        combined = runtime_env(environ=environ, env_files=env_files)
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    missing = [name for name in R2_ENV_VARS if not str(combined.get(name, "")).strip()]
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            "Error: missing R2 configuration: "
            f"{names}. Add them to .env.local for local runs or provide cloud environment variables."
        )

    endpoint = str(combined["R2_ENDPOINT"]).strip().rstrip("/")
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc or parsed.username or parsed.password:
        raise SystemExit("Error: R2_ENDPOINT must be an http(s) endpoint without credentials.")

    return R2Credentials(
        account_id=str(combined["R2_ACCOUNT_ID"]).strip(),
        access_key_id=str(combined["R2_ACCESS_KEY_ID"]).strip(),
        secret_access_key=str(combined["R2_SECRET_ACCESS_KEY"]).strip(),
        bucket=str(combined["R2_BUCKET"]).strip(),
        endpoint=endpoint,
    )


def discover_catalogue_primary_objects(
    *,
    repo_root: Path,
    kinds: Sequence[str],
    item_id: str | None = None,
    allow_partial: bool = False,
) -> tuple[List[LocalMediaObject], List[MissingVariant]]:
    prefixes = load_media_prefixes(repo_root)
    objects: List[LocalMediaObject] = []
    missing: List[MissingVariant] = []

    for kind_name in kinds:
        kind = CATALOGUE_KINDS[kind_name]
        source_root = (
            repo_root
            / media_mode_output_subdir(PIPELINE_CONFIG, kind.pipeline_mode)
            / PRIMARY_OUTPUT_SUBDIR
        ).resolve()
        groups = collect_primary_groups(source_root, item_id=item_id)
        remote_prefix = prefixes[kind.config_prefix_key]

        for current_id in sorted(groups):
            variants = groups[current_id]
            present_widths = sorted(variants)
            missing_widths = [width for width in PRIMARY_WIDTHS if width not in variants]
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


def catalogue_media_staging_root(repo_root: Path) -> Path:
    return (repo_root / "var" / "catalogue" / "media").resolve()


def build_catalogue_remote_objects(*, repo_root: Path, kind_name: str, item_id: str) -> List[RemoteMediaObject]:
    kind = CATALOGUE_KINDS[kind_name]
    prefixes = load_media_prefixes(repo_root)
    remote_prefix = prefixes[kind.config_prefix_key]
    return [
        RemoteMediaObject(
            scope="catalogue",
            kind=kind_name,
            item_id=item_id,
            width=width,
            object_key=f"{remote_prefix}/{item_id}-{PRIMARY_SUFFIX}-{width}.{OUTPUT_FORMAT}",
        )
        for width in PRIMARY_WIDTHS
    ]


def collect_primary_groups(source_root: Path, item_id: str | None = None) -> Dict[str, Dict[int, Path]]:
    groups: Dict[str, Dict[int, Path]] = {}
    if not source_root.exists():
        return groups
    for path in sorted(source_root.iterdir()):
        if not path.is_file():
            continue
        parsed = parse_primary_filename(path.name)
        if parsed is None:
            continue
        current_id, width = parsed
        if item_id and current_id != item_id:
            continue
        groups.setdefault(current_id, {})[width] = path
    return groups


def parse_primary_filename(filename: str) -> tuple[str, int] | None:
    for width in PRIMARY_WIDTHS:
        suffix = f"-{PRIMARY_SUFFIX}-{width}.{OUTPUT_FORMAT}"
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


def load_media_prefixes(repo_root: Path) -> Dict[str, str]:
    config_path = repo_root / "site-tools" / "config" / "site-tools.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    media = payload.get("media") if isinstance(payload, dict) else None
    if not isinstance(media, dict):
        raise SystemExit(f"Error: site-tools media config missing in {config_path}")
    defaults = {
        "media_image_works": "works/img",
        "media_image_work_details": "work_details/img",
        "media_image_moments": "moments/img",
    }
    config_keys = {
        "media_image_works": "image_works",
        "media_image_work_details": "image_work_details",
        "media_image_moments": "image_moments",
    }
    return {
        key: normalize_remote_prefix(str(media.get(config_keys[key], default_value)))
        for key, default_value in defaults.items()
    }


def normalize_remote_prefix(prefix: str) -> str:
    cleaned = prefix.strip().strip("/")
    if cleaned == "" or "\\" in cleaned or ".." in cleaned.split("/"):
        raise SystemExit(f"Error: invalid media remote prefix: {prefix!r}")
    return cleaned


def file_md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
            if not changed_only:
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


def content_type_for(path: Path) -> str:
    content_type, _encoding = mimetypes.guess_type(path.name)
    return content_type or "application/octet-stream"


def build_report(
    *,
    results: Sequence[PublishResult],
    missing: Sequence[MissingVariant],
    write: bool,
    force: bool,
    changed_only: bool,
    action: str,
) -> Dict[str, object]:
    counts: Dict[str, int] = {}
    for result in results:
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
        "objects": [asdict(result) for result in results],
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


class R2Client:
    """Minimal S3-compatible client for R2 HEAD and PUT operations."""

    def __init__(self, credentials: R2Credentials) -> None:
        self.credentials = credentials

    def head_object(self, key: str) -> RemoteObject | None:
        request = self._request("HEAD", key, body=b"")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return RemoteObject(
                    size=int(response.headers.get("Content-Length", "0") or "0"),
                    etag=response.headers.get("ETag", ""),
                )
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise RuntimeError(f"HEAD {key} failed with HTTP {exc.code}") from exc

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        request = self._request("PUT", key, body=body, content_type=content_type)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status not in {200, 201, 204}:
                    raise RuntimeError(f"PUT {key} failed with HTTP {response.status}")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"PUT {key} failed with HTTP {exc.code}") from exc

    def delete_object(self, key: str) -> None:
        request = self._request("DELETE", key, body=b"")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status not in {200, 202, 204}:
                    raise RuntimeError(f"DELETE {key} failed with HTTP {response.status}")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"DELETE {key} failed with HTTP {exc.code}") from exc

    def _request(
        self,
        method: str,
        key: str,
        *,
        body: bytes,
        content_type: str = "",
    ) -> urllib.request.Request:
        parsed = urllib.parse.urlparse(self.credentials.endpoint)
        encoded_key = "/".join(urllib.parse.quote(part, safe="") for part in key.split("/"))
        path = f"/{urllib.parse.quote(self.credentials.bucket, safe='')}/{encoded_key}"
        url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
        now = dt.datetime.now(dt.timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(body).hexdigest()

        headers = {
            "Host": parsed.netloc,
            "X-Amz-Content-Sha256": payload_hash,
            "X-Amz-Date": amz_date,
        }
        if method == "PUT":
            headers["Content-Length"] = str(len(body))
            headers["Content-Type"] = content_type

        authorization = self._authorization(
            method=method,
            canonical_uri=path,
            headers=headers,
            payload_hash=payload_hash,
            amz_date=amz_date,
            date_stamp=date_stamp,
        )
        headers["Authorization"] = authorization
        return urllib.request.Request(url, data=body if method == "PUT" else None, headers=headers, method=method)

    def _authorization(
        self,
        *,
        method: str,
        canonical_uri: str,
        headers: Mapping[str, str],
        payload_hash: str,
        amz_date: str,
        date_stamp: str,
    ) -> str:
        canonical_headers = "".join(f"{key.lower()}:{headers[key]}\n" for key in sorted(headers, key=str.lower))
        signed_headers = ";".join(key.lower() for key in sorted(headers, key=str.lower))
        canonical_request = "\n".join(
            [
                method,
                canonical_uri,
                "",
                canonical_headers,
                signed_headers,
                payload_hash,
            ]
        )
        credential_scope = f"{date_stamp}/auto/s3/aws4_request"
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )
        signing_key = sigv4_signing_key(self.credentials.secret_access_key, date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        return (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.credentials.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )


def sigv4_signing_key(secret_access_key: str, date_stamp: str) -> bytes:
    key_date = hmac.new(("AWS4" + secret_access_key).encode("utf-8"), date_stamp.encode("utf-8"), hashlib.sha256).digest()
    key_region = hmac.new(key_date, b"auto", hashlib.sha256).digest()
    key_service = hmac.new(key_region, b"s3", hashlib.sha256).digest()
    return hmac.new(key_service, b"aws4_request", hashlib.sha256).digest()


if __name__ == "__main__":
    raise SystemExit(main())
