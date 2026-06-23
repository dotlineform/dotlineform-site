from __future__ import annotations

import html
import json
import re
import sys
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from .common import (
    SAFE_REF_KIND_PATTERN,
    SEMANTIC_REF_ALLOWED_ACTIONS,
    SEMANTIC_REF_SUPPORTED_KINDS,
    SEMANTIC_REF_TOKEN_PATTERN,
)
from .source import DocRecord


@dataclass(frozen=True)
class SemanticRefToken:
    raw: str
    kind: str
    id: str
    label: str
    action: str
    modifier_error: str


class SemanticReferencesMixin:
    def resolve_semantic_ref_tokens(
        self,
        markdown: str,
        *,
        doc: DocRecord,
        references_by_doc: dict[str, list[dict[str, Any]]],
    ) -> str:
        if "[[ref:" not in markdown:
            references_by_doc[doc.doc_id] = []
            return markdown
        references: list[dict[str, Any]] = []
        ordinal = 0

        def replace_token(raw_token: str, raw_body: str, raw_modifier: str) -> str:
            nonlocal ordinal
            ordinal += 1
            token = self.parse_semantic_ref_token(raw_token, raw_body, raw_modifier)
            if token is None:
                self.warn_semantic_ref(doc, f"malformed semantic reference token {raw_token!r}")
                return f'<span data-ref-status="malformed">{html.escape(raw_token)}</span>'
            resolution = self.resolve_semantic_ref(token)
            warnings = self.semantic_ref_warnings(token, resolution)
            for message in warnings:
                self.warn_semantic_ref(doc, message)
            references.append(self.semantic_ref_record(doc, token, resolution, ordinal))
            return self.render_semantic_ref_token(token, resolution, not warnings)

        rendered = self.replace_semantic_ref_tokens_outside_code(markdown, replace_token)
        references_by_doc[doc.doc_id] = references
        return rendered

    def replace_semantic_ref_tokens_outside_code(self, markdown: str, replacer: Any) -> str:
        output: list[str] = []
        in_fence = False
        fence_marker = ""
        in_html_comment = False
        for line in markdown.splitlines(keepends=True):
            fence_match = re.match(r"\A {0,3}(`{3,}|~{3,})", line)
            if fence_match:
                marker = fence_match.group(1)
                if in_fence and marker.startswith(fence_marker):
                    in_fence = False
                    fence_marker = ""
                elif not in_fence:
                    in_fence = True
                    fence_marker = marker[0]
                output.append(line)
                continue
            if in_fence:
                output.append(line)
                continue
            rendered_line, in_html_comment = self.replace_semantic_ref_tokens_outside_html_comments(
                line,
                replacer,
                in_html_comment=in_html_comment,
            )
            output.append(rendered_line)
        return "".join(output)

    def replace_semantic_ref_tokens_outside_html_comments(
        self,
        line: str,
        replacer: Any,
        *,
        in_html_comment: bool,
    ) -> tuple[str, bool]:
        output: list[str] = []
        index = 0
        while index < len(line):
            if in_html_comment:
                end_index = line.find("-->", index)
                if end_index < 0:
                    output.append(line[index:])
                    return "".join(output), True
                comment_end = end_index + 3
                output.append(line[index:comment_end])
                index = comment_end
                in_html_comment = False
                continue

            start_index = line.find("<!--", index)
            segment_end = start_index if start_index >= 0 else len(line)
            output.append(self.replace_semantic_ref_tokens_outside_inline_code(line[index:segment_end], replacer))
            if start_index < 0:
                return "".join(output), False
            output.append(line[start_index:start_index + 4])
            index = start_index + 4
            in_html_comment = True

        return "".join(output), in_html_comment

    def replace_semantic_ref_tokens_outside_inline_code(self, line: str, replacer: Any) -> str:
        output: list[str] = []
        index = 0
        while index < len(line):
            tick_match = re.search(r"`+", line[index:])
            segment_end = index + tick_match.start(0) if tick_match else len(line)
            output.append(self.replace_semantic_ref_tokens_in_text(line[index:segment_end], replacer))
            if not tick_match:
                break
            tick_start = index + tick_match.start(0)
            tick_end = index + tick_match.end(0)
            tick = tick_match.group(0)
            close_index = line.find(tick, tick_end)
            if close_index >= 0:
                output.append(line[tick_start:close_index + len(tick)])
                index = close_index + len(tick)
            else:
                output.append(line[tick_start:])
                index = len(line)
        return "".join(output)

    def replace_semantic_ref_tokens_in_text(self, text: str, replacer: Any) -> str:
        def replace(match: re.Match[str]) -> str:
            return replacer(match.group(0), match.group(1), match.group(2) or "")

        return SEMANTIC_REF_TOKEN_PATTERN.sub(replace, text)

    def parse_semantic_ref_token(self, raw_token: str, raw_body: str, raw_modifier: str) -> SemanticRefToken | None:
        target, _, explicit_label = raw_body.partition("|")
        kind, sep, target_id = target.partition(":")
        kind = kind.strip().lower()
        target_id = target_id.strip()
        if not sep or not kind or not target_id or not SAFE_REF_KIND_PATTERN.fullmatch(kind):
            return None
        modifier = self.parse_semantic_ref_modifier(raw_modifier)
        return SemanticRefToken(
            raw=raw_token,
            kind=kind,
            id=target_id,
            label=explicit_label.strip(),
            action=modifier.get("action", "link"),
            modifier_error=modifier.get("error", ""),
        )

    def parse_semantic_ref_modifier(self, raw_modifier: str) -> dict[str, str]:
        if not raw_modifier.strip():
            return {"action": "link"}
        inner = raw_modifier.strip().removeprefix("{").removesuffix("}").strip()
        if not inner:
            return {"action": "link", "error": "empty modifier"}
        attrs: dict[str, str] = {}
        for part in inner.split():
            key, sep, value = part.partition("=")
            if not key or not sep or not value:
                return {"action": "link", "error": f"invalid modifier {part!r}"}
            attrs[key] = value
        unsupported = [key for key in attrs if key != "action"]
        if unsupported:
            return {"action": attrs.get("action", "link"), "error": f"unsupported modifier {unsupported[0]!r}"}
        return {"action": attrs.get("action", "link")}

    def resolve_semantic_ref(self, token: SemanticRefToken) -> dict[str, Any]:
        if token.kind not in SEMANTIC_REF_SUPPORTED_KINDS:
            return {
                "target_kind": token.kind,
                "target_id": token.id,
                "target_key": f"{token.kind}:{token.id}",
                "target_href": "",
                "target_title": "",
                "target_status": "unsupported_kind",
                "exists": False,
                "linkable": False,
                "warning": f"unsupported semantic reference kind {token.kind!r}",
            }
        if token.kind == "work":
            return self.resolve_catalogue_ref(token, "works.json", "works", "work_id", 5, "/works")
        if token.kind == "series":
            return self.resolve_catalogue_ref(token, "series.json", "series", "series_id", 3, "/series", allow_slug_id=True)
        return self.resolve_catalogue_ref(token, "moments.json", "moments", "moment_id", None, "/moments", moment_id=True)

    def resolve_catalogue_ref(
        self,
        token: SemanticRefToken,
        filename: str,
        root_key: str,
        id_field: str,
        numeric_width: int | None,
        route_base: str,
        *,
        allow_slug_id: bool = False,
        moment_id: bool = False,
    ) -> dict[str, Any]:
        try:
            if moment_id:
                normalized_id = self.normalize_moment_id(token.id)
            elif allow_slug_id:
                normalized_id = self.normalize_semantic_series_id(token.id, numeric_width or 0)
            else:
                normalized_id = self.normalize_numeric_semantic_id(token.id, numeric_width or 0)
        except ValueError:
            return {
                "target_kind": token.kind,
                "target_id": token.id,
                "target_key": f"{token.kind}:{token.id}",
                "target_href": "",
                "target_title": "",
                "target_status": "invalid_id",
                "exists": False,
                "linkable": False,
                "warning": f"invalid semantic reference id {token.kind}:{token.id}",
            }
        records = self.load_catalogue_records(filename, root_key, id_field)
        record = records.get(normalized_id)
        target_key = f"{token.kind}:{normalized_id}"
        if not record:
            return {
                "target_kind": token.kind,
                "target_id": normalized_id,
                "target_key": target_key,
                "target_href": "",
                "target_title": "",
                "target_status": "missing",
                "exists": False,
                "linkable": False,
                "warning": f"unresolved semantic reference {target_key}",
            }
        status = str(record.get("status") or "").strip().lower() or "unknown"
        return {
            "target_kind": token.kind,
            "target_id": str(record.get(id_field) or normalized_id),
            "target_key": target_key,
            "target_href": self.catalogue_ref_href(token.kind, normalized_id, route_base),
            "target_title": str(record.get("title") or "").strip(),
            "target_status": status,
            "exists": True,
            "linkable": status == "published",
            "warning": "" if status == "published" else f"semantic reference {target_key} targets non-published catalogue record",
        }

    def catalogue_ref_href(self, kind: str, normalized_id: str, route_base: str) -> str:
        encoded_id = quote(normalized_id)
        if kind == "work":
            return f"/works/?work={encoded_id}"
        if kind == "series":
            return f"/series/?series={encoded_id}"
        if kind == "moment":
            return f"/moments/?moment={encoded_id}"
        return f"{route_base}/{encoded_id}/"

    def normalize_numeric_semantic_id(self, value: str, width: int) -> str:
        text = re.sub(r"\D", "", value.strip().removeprefix("'"))
        text = re.sub(r"\.0+\Z", "", text)
        if not text:
            raise ValueError("invalid id")
        return text.rjust(width, "0")

    def normalize_semantic_series_id(self, value: str, width: int) -> str:
        text = re.sub(r"\.0+\Z", "", value.strip().removeprefix("'"))
        if not text:
            raise ValueError("invalid series id")
        if re.fullmatch(r"\d+", text):
            return text.rjust(width, "0")
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", text):
            return text
        raise ValueError("invalid series id")

    def normalize_moment_id(self, value: str) -> str:
        text = value.strip().lower().removesuffix(".md")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", text):
            raise ValueError("invalid moment id")
        return text

    def load_catalogue_records(self, filename: str, root_key: str, id_field: str) -> dict[str, dict[str, Any]]:
        cache_key = f"{filename}:{root_key}:{id_field}"
        if cache_key in self._catalogue_cache:
            return self._catalogue_cache[cache_key]
        path = self.repo_root / "studio" / "data" / "canonical" / "catalogue" / filename
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._catalogue_cache[cache_key] = {}
            return {}
        records = payload.get(root_key)
        rows = records.values() if isinstance(records, dict) else records if isinstance(records, list) else []
        out: dict[str, dict[str, Any]] = {}
        for row in rows:
            if isinstance(row, dict):
                target_id = str(row.get(id_field) or "").strip()
                if target_id:
                    out[target_id] = row
        self._catalogue_cache[cache_key] = out
        return out

    def semantic_ref_warnings(self, token: SemanticRefToken, resolution: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        if token.modifier_error:
            warnings.append(token.modifier_error)
        if token.action not in SEMANTIC_REF_ALLOWED_ACTIONS:
            warnings.append(f"unsupported semantic reference action {token.action!r}")
        if resolution.get("warning"):
            warnings.append(str(resolution["warning"]))
        return warnings

    def warn_semantic_ref(self, doc: DocRecord, message: str) -> None:
        warning = f"Docs semantic reference warning [{self.scope_id}/{doc.doc_id}]: {message}"
        self.warnings.append(warning)
        print(warning, file=sys.stderr)

    def semantic_ref_label(self, token: SemanticRefToken, resolution: dict[str, Any]) -> str:
        return token.label or str(resolution.get("target_title") or "").strip() or str(resolution.get("target_key") or "")

    def semantic_ref_record(
        self,
        doc: DocRecord,
        token: SemanticRefToken,
        resolution: dict[str, Any],
        ordinal: int,
    ) -> dict[str, Any]:
        return {
            "source_scope": self.scope_id,
            "source_doc_id": doc.doc_id,
            "source_title": doc.title,
            "source_path": doc.source_path,
            "source_viewer_url": doc.viewer_url,
            "target_kind": resolution["target_kind"],
            "target_id": resolution["target_id"],
            "target_key": resolution["target_key"],
            "target_href": resolution["target_href"],
            "target_title": resolution.get("target_title", ""),
            "target_status": resolution["target_status"],
            "label": self.semantic_ref_label(token, resolution),
            "action": token.action,
            "ordinal": ordinal,
        }

    def render_semantic_ref_token(self, token: SemanticRefToken, resolution: dict[str, Any], usable: bool) -> str:
        label = html.escape(self.semantic_ref_label(token, resolution))
        attrs = {
            "data-ref-kind": resolution["target_kind"],
            "data-ref-id": resolution["target_id"],
            "data-ref-action": token.action,
        }
        if usable and resolution.get("linkable") and resolution.get("target_href"):
            attrs["target"] = "_blank"
            attrs["rel"] = "noopener noreferrer"
            return f'<a href="{html.escape(str(resolution["target_href"]), quote=True)}" {self.html_attrs(attrs)}>{label}</a>'
        attrs["data-ref-status"] = resolution["target_status"]
        return f"<span {self.html_attrs(attrs)}>{label}</span>"
