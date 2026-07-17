#!/usr/bin/env python3
"""One-off dry-run/write migration from catalogue moments to Docs Viewer source."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_MOMENTS_PATH = Path("studio/data/canonical/catalogue/moments.json")
SOURCE_MARKDOWN_DIR = Path("studio/data/canonical/catalogue-markdown/moments")
GENERATED_MOMENTS_INDEX_DIR = Path("site/assets/moments/index")
DOCS_SCOPE_CONFIG_PATH = Path("docs-viewer/config/scopes/docs_scopes.json")
DEFAULT_OUTPUT_DIR = Path("docs-viewer/source/moments/documents")
TARGET_IMAGE_PREFIX = "docs/moments/img"
TARGET_IMAGE_SIZE = 800


MONTH_LABELS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}


SAFE_PLAIN_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,&()/_'-?")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def render_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def format_front_matter_value(value: Any) -> str:
    if value is None:
        return '""'
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if text and text[0].isalnum() and all(char in SAFE_PLAIN_CHARS for char in text):
        if text.lower() not in {"true", "false"}:
            return text
    return render_json(text)


def front_matter_block(record: dict[str, Any]) -> str:
    preferred_order = [
        "doc_id",
        "title",
        "date",
        "date_display",
        "added_date",
        "parent_id",
        "viewable",
    ]
    lines = ["---"]
    for key in preferred_order:
        if key in record:
            lines.append(f"{key}: {format_front_matter_value(record[key])}")
    lines.append("---")
    return "\n".join(lines)


def parse_iso_date(value: str, *, field: str, moment_id: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{moment_id}: invalid {field}: {value!r}") from exc


def display_date_from_iso(value: str, *, moment_id: str) -> str:
    parsed = parse_iso_date(value, field="date", moment_id=moment_id)
    month = MONTH_LABELS.get(parsed.month)
    if not month:
        raise ValueError(f"{moment_id}: unsupported month in date: {value!r}")
    return f"{parsed.day} {month} {parsed.year}"


def effective_date_display(record: dict[str, Any]) -> str:
    explicit = str(record.get("date_display") or "").strip()
    if explicit:
        return explicit
    return display_date_from_iso(str(record.get("date") or ""), moment_id=str(record.get("moment_id") or ""))


def markdown_alt_text(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("]", "\\]")


def scaled_image_dimensions(width: Any, height: Any) -> tuple[int, int] | None:
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        return None
    longest = max(width, height)
    if longest <= 0:
        return None
    scaled_width = max(1, round(width * TARGET_IMAGE_SIZE / longest))
    scaled_height = max(1, round(height * TARGET_IMAGE_SIZE / longest))
    return scaled_width, scaled_height


def image_token(moment_id: str, title: str, generated_record: dict[str, Any]) -> str:
    moment = generated_record.get("moment") if isinstance(generated_record, dict) else {}
    if not isinstance(moment, dict):
        return ""
    images = moment.get("images")
    if not isinstance(images, list) or not images:
        return ""
    target = f"{TARGET_IMAGE_PREFIX}/{moment_id}-primary-{TARGET_IMAGE_SIZE}.webp"
    dimensions = scaled_image_dimensions(moment.get("width_px"), moment.get("height_px"))
    attrs = ""
    if dimensions:
        attrs = f" width={dimensions[0]} height={dimensions[1]}"
    return f"![{markdown_alt_text(title)}]([[media:{target}{attrs}]])"


def normalize_body(text: str) -> str:
    return text.strip() + "\n"


def render_moment_source(
    canonical_record: dict[str, Any],
    source_body: str,
    generated_record: dict[str, Any],
) -> str:
    moment_id = str(canonical_record["moment_id"])
    title = str(canonical_record["title"])
    date = str(canonical_record["date"])
    date_display = effective_date_display(canonical_record)
    added_date = str(canonical_record.get("published_date") or date)
    parse_iso_date(date, field="date", moment_id=moment_id)
    parse_iso_date(added_date, field="published_date", moment_id=moment_id)

    front_matter = front_matter_block(
        {
            "doc_id": moment_id,
            "title": title,
            "date": date,
            "date_display": date_display,
            "added_date": added_date,
            "parent_id": "",
            "viewable": True,
        }
    )
    parts = [
        front_matter,
        f"# {title}",
        f'<p class="momentDate">{html.escape(date_display)}</p>',
    ]
    token = image_token(moment_id, title, generated_record)
    if token:
        parts.append(token)
    parts.append(normalize_body(source_body))
    return "\n\n".join(parts).rstrip() + "\n"


def load_canonical_moments(repo_root: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(repo_root / CANONICAL_MOMENTS_PATH)
    moments = payload.get("moments") if isinstance(payload, dict) else None
    if not isinstance(moments, dict):
        raise ValueError(f"{CANONICAL_MOMENTS_PATH}: expected object with moments map")
    return {
        str(moment_id): record
        for moment_id, record in moments.items()
        if isinstance(record, dict)
    }


def load_generated_records(repo_root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted((repo_root / GENERATED_MOMENTS_INDEX_DIR).glob("*.json")):
        payload = load_json(path)
        if isinstance(payload, dict):
            records[path.stem] = payload
    return records


def load_scope_default_doc_id(repo_root: Path) -> str:
    path = repo_root / DOCS_SCOPE_CONFIG_PATH
    if not path.exists():
        return ""
    payload = load_json(path)
    scopes = payload.get("scopes") if isinstance(payload, dict) else []
    if not isinstance(scopes, list):
        return ""
    for scope in scopes:
        if isinstance(scope, dict) and scope.get("scope_id") == "moments":
            return str(scope.get("default_doc_id") or "").strip()
    return ""


def build_outputs(repo_root: Path) -> tuple[dict[str, str], list[str], dict[str, int]]:
    warnings: list[str] = []
    canonical = load_canonical_moments(repo_root)
    generated = load_generated_records(repo_root)
    source_dir = repo_root / SOURCE_MARKDOWN_DIR

    source_ids = {path.stem for path in source_dir.glob("*.md")}
    canonical_ids = set(canonical)
    generated_ids = set(generated)
    if source_ids != canonical_ids:
        warnings.append(
            "source markdown ids differ from canonical ids: "
            f"missing={sorted(canonical_ids - source_ids)} extra={sorted(source_ids - canonical_ids)}"
        )
    if generated_ids != canonical_ids:
        warnings.append(
            "generated moment ids differ from canonical ids: "
            f"missing={sorted(canonical_ids - generated_ids)} extra={sorted(generated_ids - canonical_ids)}"
        )

    status_values = sorted({str(record.get("status") or "") for record in canonical.values()})
    if status_values != ["published"]:
        warnings.append(f"unexpected status values: {status_values}")
    image_alt_values = sorted({repr(record.get("image_alt")) for record in canonical.values()})
    if image_alt_values != ["None"]:
        warnings.append(f"unexpected canonical image_alt values: {image_alt_values}")

    outputs: dict[str, str] = {}
    image_count = 0
    dimension_count = 0
    date_display_explicit_count = 0
    placeholder_date_display_count = 0
    for moment_id in sorted(canonical):
        record = canonical[moment_id]
        if record.get("moment_id") != moment_id:
            warnings.append(f"{moment_id}: canonical moment_id differs: {record.get('moment_id')!r}")
        source_path = source_dir / f"{moment_id}.md"
        generated_record = generated.get(moment_id, {})
        source_body = source_path.read_text(encoding="utf-8")
        output_text = render_moment_source(record, source_body, generated_record)
        outputs[f"{moment_id}.md"] = output_text
        moment = generated_record.get("moment") if isinstance(generated_record, dict) else {}
        images = moment.get("images") if isinstance(moment, dict) else []
        if isinstance(images, list) and images:
            image_count += 1
            if scaled_image_dimensions(moment.get("width_px"), moment.get("height_px")):
                dimension_count += 1
        if record.get("date_display"):
            date_display_explicit_count += 1
            if str(record.get("date") or "").endswith("-01-01"):
                placeholder_date_display_count += 1

    stats = {
        "canonical_count": len(canonical),
        "generated_doc_count": len(outputs),
        "image_count": image_count,
        "dimension_count": dimension_count,
        "date_display_explicit_count": date_display_explicit_count,
        "placeholder_date_display_count": placeholder_date_display_count,
    }
    return outputs, warnings, stats


def summarize_changes(output_dir: Path, outputs: dict[str, str]) -> dict[str, list[str]]:
    existing = {
        path.name: path.read_text(encoding="utf-8")
        for path in output_dir.glob("*.md")
    } if output_dir.exists() else {}
    planned = set(outputs)
    current = set(existing)
    return {
        "create": sorted(planned - current),
        "update": sorted(name for name in planned & current if existing[name] != outputs[name]),
        "unchanged": sorted(name for name in planned & current if existing[name] == outputs[name]),
        "extra_existing": sorted(current - planned),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate catalogue moments into Docs Viewer source Markdown.")
    parser.add_argument("--write", action="store_true", help="Write generated Markdown files. Default is dry-run.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Docs Viewer moments source output directory.")
    parser.add_argument("--show-sample", action="append", default=[], help="Print generated Markdown for a moment id.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path.cwd().resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    outputs, warnings, stats = build_outputs(repo_root)
    changes = summarize_changes(output_dir, outputs)
    default_doc_id = load_scope_default_doc_id(repo_root)
    if default_doc_id and f"{default_doc_id}.md" not in outputs:
        warnings.append(
            f"moments scope default_doc_id is {default_doc_id!r}, but this migration does not generate {default_doc_id}.md"
        )

    mode = "write" if args.write else "dry-run"
    print(f"Moments Docs Viewer migration ({mode})")
    print(f"output_dir: {output_dir.relative_to(repo_root).as_posix() if output_dir.is_relative_to(repo_root) else output_dir}")
    print(
        "records: "
        f"canonical={stats['canonical_count']} generated_docs={stats['generated_doc_count']} "
        f"with_images={stats['image_count']} with_dimensions={stats['dimension_count']} "
        f"explicit_date_display={stats['date_display_explicit_count']} "
        f"placeholder_dates_with_display={stats['placeholder_date_display_count']}"
    )
    print(
        "changes: "
        f"create={len(changes['create'])} update={len(changes['update'])} "
        f"unchanged={len(changes['unchanged'])} extra_existing={len(changes['extra_existing'])}"
    )
    if changes["extra_existing"]:
        print("extra_existing:")
        for name in changes["extra_existing"]:
            print(f"  {name}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    for sample_id in args.show_sample:
        filename = f"{sample_id}.md"
        if filename not in outputs:
            print(f"sample {sample_id!r}: not generated", file=sys.stderr)
            return 2
        print(f"\n--- sample: {filename} ---")
        print(outputs[filename], end="" if outputs[filename].endswith("\n") else "\n")

    if args.write:
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, text in outputs.items():
            (output_dir / filename).write_text(text, encoding="utf-8")
        print(f"wrote {len(outputs)} files")
    else:
        print("dry-run only; pass --write to write generated Markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
