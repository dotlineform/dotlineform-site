#!/usr/bin/env python3
"""Sanitize self-contained SVG bytes for Docs media publication."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from lxml import etree


DANGEROUS_SVG_ELEMENTS = {
    "embed",
    "foreignobject",
    "iframe",
    "object",
    "script",
}
REFERENCE_ATTRIBUTES = {"href", "src"}
URL_ATTRIBUTES = {
    "clip-path",
    "cursor",
    "fill",
    "filter",
    "marker",
    "marker-end",
    "marker-mid",
    "marker-start",
    "mask",
    "stroke",
}
UNSAFE_CSS_PATTERN = re.compile(
    r"(?:@import\b|expression\s*\(|javascript\s*:|behavior\s*:|-moz-binding\s*:)",
    re.IGNORECASE,
)
CSS_URL_PATTERN = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE | re.DOTALL)
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


@dataclass(frozen=True)
class SanitizedSvg:
    bytes: bytes
    title: str
    warnings: tuple[str, ...]
    removed_elements: int
    removed_attributes: int
    removed_styles: int

    def diagnostics(self) -> dict[str, Any]:
        return {
            "removed_elements": self.removed_elements,
            "removed_attributes": self.removed_attributes,
            "removed_styles": self.removed_styles,
            "warnings": list(self.warnings),
        }


def _local_name(value: str) -> str:
    try:
        return etree.QName(value).localname.lower()
    except ValueError:
        return str(value or "").split(":")[-1].lower()


def _fragment_url(value: str) -> bool:
    return str(value or "").strip().startswith("#")


def _css_is_self_contained(value: str) -> bool:
    css = str(value or "")
    if UNSAFE_CSS_PATTERN.search(css):
        return False
    return all(_fragment_url(match.group(2)) for match in CSS_URL_PATTERN.finditer(css))


def _sanitize_style_attribute(value: str) -> tuple[str, int]:
    kept: list[str] = []
    removed = 0
    for declaration in str(value or "").split(";"):
        clean = declaration.strip()
        if not clean:
            continue
        if ":" not in clean or not _css_is_self_contained(clean):
            removed += 1
            continue
        kept.append(clean)
    return "; ".join(kept), removed


def _svg_parser() -> etree.XMLParser:
    return etree.XMLParser(
        no_network=True,
        load_dtd=False,
        resolve_entities=False,
        remove_comments=True,
        remove_pis=True,
        recover=False,
        huge_tree=False,
    )


def sanitize_svg_bytes(source: bytes | str) -> SanitizedSvg:
    """Return safe, deterministic SVG bytes or raise for an invalid SVG source."""

    raw = source.encode("utf-8") if isinstance(source, str) else bytes(source)
    lowered = raw.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise ValueError("SVG document type and entity declarations are not supported")
    try:
        root = etree.fromstring(raw, parser=_svg_parser())
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise ValueError(f"SVG is not well-formed XML: {exc}") from exc
    if _local_name(root.tag) != "svg":
        raise ValueError("SVG source must have one <svg> document root")
    root_namespace = etree.QName(root.tag).namespace
    if root_namespace not in {None, "", SVG_NAMESPACE}:
        raise ValueError("SVG root must use the standard SVG namespace")
    if not root_namespace:
        root.set("xmlns", SVG_NAMESPACE)

    warnings: list[str] = []
    removed_elements = 0
    removed_attributes = 0
    removed_styles = 0

    for element in list(root.iter()):
        if not isinstance(element.tag, str):
            continue
        element_name = _local_name(element.tag)
        if element is not root and element_name in DANGEROUS_SVG_ELEMENTS:
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
                removed_elements += 1
            continue

        if element_name == "style" and not _css_is_self_contained(element.text or ""):
            element.text = ""
            removed_styles += 1

        for attribute_name, value in list(element.attrib.items()):
            local_attribute = _local_name(attribute_name)
            lowered_value = str(value or "").strip().lower()
            remove = local_attribute.startswith("on") or "javascript:" in lowered_value
            if local_attribute in REFERENCE_ATTRIBUTES and not _fragment_url(value):
                remove = True
            if local_attribute in URL_ATTRIBUTES and not _css_is_self_contained(value):
                remove = True
            if local_attribute == "style":
                sanitized_style, removed_declarations = _sanitize_style_attribute(value)
                removed_styles += removed_declarations
                if sanitized_style:
                    element.attrib[attribute_name] = sanitized_style
                else:
                    remove = True
            if remove:
                element.attrib.pop(attribute_name, None)
                removed_attributes += 1

    if removed_elements:
        warnings.append(f"Removed {removed_elements} unsafe SVG element(s).")
    if removed_attributes:
        warnings.append(f"Removed {removed_attributes} unsafe or external SVG attribute(s).")
    if removed_styles:
        warnings.append(f"Removed {removed_styles} unsafe SVG style value(s).")

    title = ""
    for element in root.iter():
        if isinstance(element.tag, str) and _local_name(element.tag) == "title":
            title = " ".join("".join(element.itertext()).split())
            break

    sanitized = etree.tostring(
        root,
        encoding="utf-8",
        xml_declaration=False,
        pretty_print=False,
    ).strip()
    if not sanitized:
        raise ValueError("SVG sanitizer produced an empty document")
    return SanitizedSvg(
        bytes=sanitized,
        title=title,
        warnings=tuple(warnings),
        removed_elements=removed_elements,
        removed_attributes=removed_attributes,
        removed_styles=removed_styles,
    )


__all__ = ["SanitizedSvg", "sanitize_svg_bytes"]
