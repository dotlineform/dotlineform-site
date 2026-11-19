"""Cloudflare R2 credentials and S3-compatible object transport."""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import http.client
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from studio.shared.python.local_env import SITE_ENV_REL_PATH, runtime_env


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
class RemoteListObject:
    key: str
    size: int
    etag: str


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


class R2Client:
    """Small S3-compatible client for the artifact operations Docs Viewer needs."""

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

    def get_object(self, key: str) -> bytes:
        request = self._request("GET", key, body=b"")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(f"R2 object not found: {key}") from exc
            raise RuntimeError(f"GET {key} failed with HTTP {exc.code}") from exc

    def list_objects(self, prefix: str) -> list[RemoteListObject]:
        objects: list[RemoteListObject] = []
        continuation_token = ""
        while True:
            query = {"list-type": "2", "prefix": prefix}
            if continuation_token:
                query["continuation-token"] = continuation_token
            request = self._request("GET", "", body=b"", query=query)
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    payload = response.read()
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"LIST {prefix} failed with HTTP {exc.code}") from exc
            root = ET.fromstring(payload)
            namespace = root.tag.partition("}")[0].lstrip("{")
            qualify = (lambda name: f"{{{namespace}}}{name}") if namespace else (lambda name: name)
            for item in root.findall(qualify("Contents")):
                key = str(item.findtext(qualify("Key")) or "")
                if not key:
                    continue
                objects.append(
                    RemoteListObject(
                        key=key,
                        size=int(item.findtext(qualify("Size")) or "0"),
                        etag=str(item.findtext(qualify("ETag")) or ""),
                    )
                )
            if str(root.findtext(qualify("IsTruncated")) or "").lower() != "true":
                break
            continuation_token = str(root.findtext(qualify("NextContinuationToken")) or "")
            if not continuation_token:
                raise RuntimeError("R2 LIST response was truncated without a continuation token")
        return objects

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        request = self._request("PUT", key, body=body, content_type=content_type)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status not in {200, 201, 204}:
                    raise RuntimeError(f"PUT {key} failed with HTTP {response.status}")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"PUT {key} failed with HTTP {exc.code}") from exc

    def copy_objects(self, objects: Sequence[Mapping[str, object]]) -> None:
        """Copy a bounded batch using one connection and exact source conditions."""
        parsed = urllib.parse.urlparse(self.credentials.endpoint)
        connection_type = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        connection = connection_type(parsed.hostname, parsed.port, timeout=120)
        try:
            for item in objects:
                source, destination = str(item["source"]), str(item["destination"])
                request = self._request("PUT", destination, body=b"", extra_headers={
                    "X-Amz-Copy-Source": urllib.parse.quote(f"/{self.credentials.bucket}/{source}", safe="/"),
                    "X-Amz-Copy-Source-If-Match": str(item["etag"]),
                    "X-Amz-Metadata-Directive": "COPY",
                    "Cf-Copy-Destination-If-None-Match": "*",
                })
                connection.request("PUT", request.selector, body=b"", headers=dict(request.header_items()))
                response = connection.getresponse()
                body = response.read()
                if response.status != 200:
                    raise RuntimeError(f"COPY {source} to {destination} failed with HTTP {response.status}")
                payload = ET.fromstring(body)
                if payload.tag.rsplit("}", 1)[-1] != "CopyObjectResult":
                    raise RuntimeError(f"COPY {source} to {destination} failed: invalid CopyObject result")
        finally:
            connection.close()

    def delete_objects(self, keys: Sequence[str]) -> None:
        """Delete an explicit batch of at most 1000 keys; propagate per-key errors."""
        if not keys or len(keys) > 1000 or len(set(keys)) != len(keys):
            raise ValueError("R2 deletion requires 1–1000 distinct keys")
        root = ET.Element("Delete", xmlns="http://s3.amazonaws.com/doc/2006-03-01/")
        for key in keys:
            ET.SubElement(ET.SubElement(root, "Object"), "Key").text = key
        ET.SubElement(root, "Quiet").text = "true"
        body = ET.tostring(root, encoding="utf-8")
        request = self._request("POST", "", body=body, query={"delete": ""}, content_type="application/xml",
                                extra_headers={"Content-MD5": base64.b64encode(hashlib.md5(body, usedforsecurity=False).digest()).decode("ascii")})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = ET.fromstring(response.read())
                errors = [node for node in payload.iter() if node.tag.rsplit("}", 1)[-1] == "Error"]
                if payload.tag.rsplit("}", 1)[-1] != "DeleteResult" or errors:
                    raise RuntimeError(f"R2 batch deletion failed: {len(errors)} object error(s)")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"R2 batch deletion failed with HTTP {exc.code}") from exc

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
        query: Mapping[str, str] | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> urllib.request.Request:
        parsed = urllib.parse.urlparse(self.credentials.endpoint)
        encoded_key = "/".join(urllib.parse.quote(part, safe="") for part in key.split("/"))
        path = f"/{urllib.parse.quote(self.credentials.bucket, safe='')}/{encoded_key}"
        canonical_query = urllib.parse.urlencode(
            sorted((query or {}).items()),
            quote_via=urllib.parse.quote,
            safe="-_.~",
        )
        url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", canonical_query, ""))
        now = dt.datetime.now(dt.timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(body).hexdigest()

        headers = {
            "Host": parsed.netloc,
            "X-Amz-Content-Sha256": payload_hash,
            "X-Amz-Date": amz_date,
        }
        if method in {"PUT", "POST"}:
            headers["Content-Length"] = str(len(body))
            if content_type:
                headers["Content-Type"] = content_type
        headers.update(extra_headers or {})

        authorization = self._authorization(
            method=method,
            canonical_uri=path,
            canonical_query=canonical_query,
            headers=headers,
            payload_hash=payload_hash,
            amz_date=amz_date,
            date_stamp=date_stamp,
        )
        headers["Authorization"] = authorization
        return urllib.request.Request(url, data=body if method in {"PUT", "POST"} else None, headers=headers, method=method)

    def _authorization(
        self,
        *,
        method: str,
        canonical_uri: str,
        canonical_query: str = "",
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
                canonical_query,
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
