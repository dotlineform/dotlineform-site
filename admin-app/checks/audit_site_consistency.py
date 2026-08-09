#!/usr/bin/env python3
"""
Audit generated site consistency (read-only).

Checks:
- cross_refs: validate key cross-artifact references and duplicate IDs
- schema: generated route contract ID format + generated JSON consistency rules
- json_schema: generated JSON shape and count checks (lean Series, exact Series/Work, and Work detail JSON)
- links: generated link target existence + query-contract sanity
- media: expected media/download file presence checks
- orphans: orphan generated route contracts/JSON (and optional media scan)
"""

import argparse
from datetime import datetime
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT,
    REPO_ROOT / "studio" / "shared" / "python",
    REPO_ROOT / "studio" / "services",
    REPO_ROOT / "scripts",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    from pipeline_config import load_pipeline_config
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from studio.shared.python.pipeline_config import load_pipeline_config

try:
    from catalogue.series_ids import normalize_series_id
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.series_ids import normalize_series_id

from tags import tag_source_paths


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
THUMB_SUFFIX = str(PIPELINE_CONFIG["variants"]["thumb"]["suffix"])
PRIMARY_SUFFIX = str(PIPELINE_CONFIG["variants"]["primary"]["suffix"])
ASSET_FORMAT = str(PIPELINE_CONFIG["encoding"]["format"])
THUMB_SIZES = sorted({int(v) for v in PIPELINE_CONFIG["variants"]["thumb"]["sizes"]})
ACCEPTED_THUMB_SIZES = sorted(
    set(THUMB_SIZES)
    | {int(v) for v in PIPELINE_CONFIG["variants"]["compatibility"].get("accepted_legacy_thumb_sizes", [])}
)
ACCEPTED_PRIMARY_WIDTHS = sorted(
    {int(v) for v in PIPELINE_CONFIG["variants"]["compatibility"].get("generate_widths", [])}
    | {int(v) for v in PIPELINE_CONFIG["variants"]["compatibility"].get("accepted_legacy_widths", [])}
)


def expected_thumb_names(item_id: str) -> List[str]:
    return [f"{item_id}-{THUMB_SUFFIX}-{size}.{ASSET_FORMAT}" for size in THUMB_SIZES]


def media_filename_regex(id_pattern: str) -> re.Pattern[str]:
    thumb_alt = "|".join(str(size) for size in ACCEPTED_THUMB_SIZES)
    primary_alt = "|".join(str(width) for width in ACCEPTED_PRIMARY_WIDTHS)
    return re.compile(
        rf"^({id_pattern})-(?:{re.escape(THUMB_SUFFIX)}-(?:{thumb_alt})|{re.escape(PRIMARY_SUFFIX)}-(?:{primary_alt}))\.{re.escape(ASSET_FORMAT)}$"
    )


def is_empty(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_work_id_selection(expr: str) -> set[str]:
    out: set[str] = set()
    if not expr:
        return out
    token_re = re.compile(r"^[0-9]+(?:-[0-9]+)?$")
    for raw in expr.split(","):
        token = raw.strip()
        if not token:
            continue
        if not token_re.match(token):
            raise SystemExit(f"Invalid --work-ids token: {token}")
        if "-" in token:
            a_raw, b_raw = token.split("-", 1)
            a, b = int(a_raw), int(b_raw)
            if a > b:
                a, b = b, a
            for n in range(a, b + 1):
                out.add(f"{n:05d}")
        else:
            out.add(f"{int(token):05d}")
    return out


def parse_scalar_from_fm_line(raw: str) -> Optional[str]:
    value = raw.strip()
    if value == "" or value == "null":
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_front_matter(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm: Dict[str, Any] = {}
    for line in parts[1].splitlines():
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        fm[m.group(1)] = parse_scalar_from_fm_line(m.group(2))
    return fm


def normalize_series_ref(value: Any) -> str:
    raw = normalize_text(value)
    if raw == "":
        return ""
    try:
        return normalize_series_id(raw)
    except ValueError:
        return raw


def is_valid_series_ref(value: Any) -> bool:
    raw = normalize_text(value)
    if raw == "":
        return False
    try:
        normalize_series_id(raw)
    except ValueError:
        return False
    return True


def load_collection(path_glob: str, id_field: str) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    rows: Dict[str, Dict[str, Any]] = {}
    dups: List[str] = []
    for p in sorted(Path().glob(path_glob)):
        fm = parse_front_matter(p)
        idv = normalize_text(fm.get(id_field))
        if idv == "":
            idv = normalize_text(p.stem)
        if idv == "":
            continue
        if idv in rows:
            dups.append(idv)
        rows[idv] = {"path": str(p), "fm": fm}
    return rows, dups


def work_id_for_detail(detail_uid: str, row: Dict[str, Any]) -> str:
    fm_work_id = normalize_text(row.get("fm", {}).get("work_id"))
    if fm_work_id:
        return fm_work_id
    if "-" in detail_uid:
        return detail_uid.split("-", 1)[0]
    return ""


def add_sample(samples: List[Dict[str, Any]], item: Dict[str, Any], max_samples: int) -> None:
    if len(samples) < max_samples:
        samples.append(item)


def load_exact_series_member_ids(site_root: Path) -> Dict[str, List[str]]:
    members_by_series: Dict[str, List[str]] = {}
    for path in sorted((site_root / "assets/series/index").glob("*.json")):
        series_id = normalize_text(path.stem)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        members = payload.get("member_works") if isinstance(payload, dict) else None
        if series_id == "" or not isinstance(members, list):
            continue
        members_by_series[series_id] = [
            work_id
            for member in members
            if isinstance(member, dict) and (work_id := normalize_text(member.get("work_id"))) != ""
        ]
    return members_by_series


def load_exact_series_work_counts(site_root: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for series_id, member_work_ids in load_exact_series_member_ids(site_root).items():
        counts[series_id] = len(member_work_ids)
    return counts


def load_detail_refs_from_work_json(site_root: Path, work_ids_scope: Optional[set[str]] = None) -> Dict[str, Dict[str, str]]:
    refs: Dict[str, Dict[str, str]] = {}
    for p in sorted((site_root / "assets/works/index").glob("*.json")):
        wid = normalize_text(p.stem)
        if wid == "":
            continue
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        sections = payload.get("sections")
        if not isinstance(sections, list):
            continue
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            details = sec.get("details")
            if not isinstance(details, list):
                continue
            for detail in details:
                if not isinstance(detail, dict):
                    continue
                detail_uid = normalize_text(detail.get("detail_uid"))
                if detail_uid == "":
                    continue
                refs[detail_uid] = {
                    "work_id": normalize_text(detail.get("work_id")) or wid,
                    "path": str(p),
                }
    return refs


def load_exact_record_contracts(
    directory: Path,
    *,
    record_key: str,
    id_field: str,
) -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        record_id = normalize_text(path.stem)
        if record_id == "":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        record = payload.get(record_key) if isinstance(payload, dict) else None
        fm = dict(record) if isinstance(record, dict) else {}
        fm.setdefault(id_field, "")
        if record_key == "work":
            series_ids = fm.get("series_ids")
            fm["series_id"] = normalize_text(series_ids[0]) if isinstance(series_ids, list) and series_ids else ""
        records[record_id] = {"path": str(path), "fm": fm}
    return records


def load_generated_route_contracts(site_root: Path) -> Tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
]:
    works = load_exact_record_contracts(
        site_root / "assets/works/index",
        record_key="work",
        id_field="work_id",
    )
    series = load_exact_record_contracts(
        site_root / "assets/series/index",
        record_key="series",
        id_field="series_id",
    )
    details = {
        detail_uid: {"path": ref.get("path", ""), "fm": {"work_id": ref.get("work_id", "")}}
        for detail_uid, ref in load_detail_refs_from_work_json(site_root).items()
        if normalize_text(detail_uid) != ""
    }
    return works, series, details


def resolve_repo_source_path(rel_path: Path, repo_root: Path = REPO_ROOT) -> Path:
    return (repo_root / rel_path).resolve()


def load_source_series_statuses(repo_root: Path = REPO_ROOT) -> Dict[str, str]:
    path = resolve_repo_source_path(Path("studio/data/canonical/catalogue/series.json"), repo_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    series_map = payload.get("series") if isinstance(payload, dict) else None
    if not isinstance(series_map, dict):
        return {}
    statuses: Dict[str, str] = {}
    for raw_sid, raw_row in series_map.items():
        sid = normalize_text(raw_sid)
        if sid == "" or not isinstance(raw_row, dict):
            continue
        statuses[sid] = normalize_text(raw_row.get("status")).lower() or "unknown"
    return statuses


def normalize_url(url: str) -> str:
    s = normalize_text(url)
    if s == "":
        return "/"
    if s.startswith(("http://", "https://")):
        return s
    if not s.startswith("/"):
        s = "/" + s
    if not s.endswith("/"):
        s = s + "/"
    return s


def check_cross_refs(
    site_root: Path,
    works: Dict[str, Dict[str, Any]],
    series: Dict[str, Dict[str, Any]],
    work_details: Dict[str, Dict[str, Any]],
    works_dups: List[str],
    series_dups: List[str],
    detail_dups: List[str],
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []

    for dup in sorted(set(works_dups)):
        errors += 1
        add_sample(samples, {"check": "cross_refs", "id": dup, "message": "duplicate work_id in _works"}, max_samples)
    for dup in sorted(set(series_dups)):
        errors += 1
        add_sample(samples, {"check": "cross_refs", "id": dup, "message": "duplicate series_id in _series"}, max_samples)
    for dup in sorted(set(detail_dups)):
        errors += 1
        add_sample(samples, {"check": "cross_refs", "id": dup, "message": "duplicate detail_uid in _work_details"}, max_samples)

    # Generated work route contracts may not include series membership directly.
    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = normalize_series_ref(row["fm"].get("series_id"))
        if sid == "":
            continue
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if sid not in series:
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": wid, "path": row["path"], "message": f"missing series contract for series_id '{sid}'"}, max_samples)

    # Work-detail route contracts derive the parent work id from the detail_uid prefix.
    for duid, row in work_details.items():
        wid = work_id_for_detail(duid, row)
        if wid == "":
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": duid, "path": row["path"], "message": "could not derive parent work_id for work detail"}, max_samples)
            continue
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        if wid not in works:
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": duid, "path": row["path"], "message": f"work detail references missing work_id '{wid}'"}, max_samples)

    # Lean Series index -> exact Series/Work route contract references.
    series_index_path = site_root / "assets/data/series_index.json"
    series_map = None
    if not series_index_path.exists():
        errors += 1
        add_sample(samples, {"check": "cross_refs", "id": "series_index", "path": str(series_index_path), "message": "missing series index JSON"}, max_samples)
    else:
        try:
            obj = json.loads(series_index_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": "series_index", "path": str(series_index_path), "message": f"invalid json: {e}"}, max_samples)
            obj = {}

        series_map = obj.get("series") if isinstance(obj, dict) else None
        if not isinstance(series_map, dict):
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": "series_index", "path": str(series_index_path), "message": "missing/invalid series map"}, max_samples)
        else:
            for sid, srow in series_map.items():
                sid_norm = normalize_text(sid)
                if sid_norm == "":
                    continue
                if series_ids_scope is not None and sid_norm not in series_ids_scope:
                    continue
                if sid_norm not in series:
                    errors += 1
                    add_sample(samples, {"check": "cross_refs", "id": sid_norm, "path": str(series_index_path), "message": "series_index references missing series contract"}, max_samples)
                if not isinstance(srow, dict):
                    errors += 1
                    add_sample(samples, {"check": "cross_refs", "id": sid_norm, "path": str(series_index_path), "message": "series_index entry must be an object"}, max_samples)
                    continue
                for field in ("primary_work_id", "single_work_id"):
                    work_id = normalize_text(srow.get(field))
                    if work_id and (work_ids_scope is None or work_id in work_ids_scope) and work_id not in works:
                        errors += 1
                        add_sample(samples, {"check": "cross_refs", "id": sid_norm, "path": str(series_index_path), "message": f"series_index {field} references missing work_id '{work_id}'"}, max_samples)

            for sid_norm, series_row in series.items():
                if series_ids_scope is not None and sid_norm not in series_ids_scope:
                    continue
                if sid_norm not in series_map:
                    errors += 1
                    add_sample(samples, {"check": "cross_refs", "id": sid_norm, "path": series_row["path"], "message": "exact Series payload is missing from series_index"}, max_samples)

    series_membership = load_exact_series_member_ids(site_root)
    for series_id, member_work_ids in series_membership.items():
        if series_ids_scope is not None and series_id not in series_ids_scope:
            continue
        for work_id in member_work_ids:
            if work_ids_scope is not None and work_id not in work_ids_scope:
                continue
            if work_id not in works:
                errors += 1
                add_sample(samples, {"check": "cross_refs", "id": series_id, "path": series.get(series_id, {}).get("path", ""), "message": f"exact Series member references missing work_id '{work_id}'"}, max_samples)

    # Per-work JSON -> work-detail/work route contract references
    detail_refs = load_detail_refs_from_work_json(site_root=site_root, work_ids_scope=work_ids_scope)
    for detail_uid_norm, ref in detail_refs.items():
        wid = normalize_text(ref.get("work_id"))
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        if wid not in works:
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": detail_uid_norm, "path": ref.get("path", ""), "message": f"work JSON references missing work_id '{wid}'"}, max_samples)
        if detail_uid_norm not in work_details:
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": detail_uid_norm, "path": ref.get("path", ""), "message": "work JSON references missing work detail contract"}, max_samples)

    # Tag assignments -> lean Series identity and exact Series membership.
    assignments_path = resolve_repo_source_path(tag_source_paths.TAG_ASSIGNMENTS_REL_PATH)
    if not assignments_path.exists():
        warnings += 1
        add_sample(samples, {"check": "cross_refs", "id": "tag_assignments", "path": str(assignments_path), "message": "missing tag assignments JSON"}, max_samples)
    else:
        try:
            assignments_obj = json.loads(assignments_path.read_text(encoding="utf-8"))
        except Exception as e:
            warnings += 1
            add_sample(samples, {"check": "cross_refs", "id": "tag_assignments", "path": str(assignments_path), "message": f"invalid json: {e}"}, max_samples)
            assignments_obj = {}

        assignments_series = assignments_obj.get("series") if isinstance(assignments_obj, dict) else None
        if not isinstance(assignments_series, dict):
            warnings += 1
            add_sample(samples, {"check": "cross_refs", "id": "tag_assignments", "path": str(assignments_path), "message": "missing/invalid series map"}, max_samples)
        else:
            known_series_index_ids = set(series_map.keys()) if isinstance(series_map, dict) else set()
            source_series_status_by_id = load_source_series_statuses()
            known_work_ids = {normalize_text(wid) for wid in works.keys()}
            series_member_sets: Dict[str, Set[str]] = {
                series_id: set(member_work_ids)
                for series_id, member_work_ids in series_membership.items()
            }

            for sid, row in assignments_series.items():
                sid_norm = normalize_text(sid)
                if sid_norm == "":
                    continue
                if series_ids_scope is not None and sid_norm not in series_ids_scope:
                    continue
                if sid_norm not in known_series_index_ids:
                    if source_series_status_by_id.get(sid_norm) not in {"", "published"}:
                        continue
                    warnings += 1
                    add_sample(samples, {"check": "cross_refs", "id": sid_norm, "path": str(assignments_path), "message": "tag_assignments series row is missing from series_index"}, max_samples)
                    continue
                works_map = row.get("works") if isinstance(row, dict) else None
                if not isinstance(works_map, dict):
                    continue
                for work_id, work_row in works_map.items():
                    work_id_norm = normalize_text(work_id)
                    if work_id_norm == "":
                        continue
                    if work_ids_scope is not None and work_id_norm not in work_ids_scope:
                        continue
                    if work_id_norm not in known_work_ids:
                        warnings += 1
                        add_sample(samples, {"check": "cross_refs", "id": work_id_norm, "path": str(assignments_path), "message": f"tag_assignments work override references unknown work_id '{work_id_norm}'"}, max_samples)
                    members = series_member_sets.get(sid_norm, set())
                    if members and work_id_norm not in members:
                        warnings += 1
                        add_sample(samples, {"check": "cross_refs", "id": work_id_norm, "path": str(assignments_path), "message": f"tag_assignments work override for series '{sid_norm}' is not present in exact Series membership"}, max_samples)

    return {"name": "cross_refs", "error_count": errors, "warning_count": warnings, "samples": samples}


def check_schema(
    site_root: Path,
    works: Dict[str, Dict[str, Any]],
    series: Dict[str, Dict[str, Any]],
    work_details: Dict[str, Dict[str, Any]],
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []

    re_work_id = re.compile(r"^\d{5}$")
    re_detail_uid = re.compile(r"^\d{5}-\d{3}$")
    allowed_sort_fields = {"title", "year", "work_id", "title_sort"}

    # Parse and validate exact Series sort_fields once for downstream Work checks.
    sort_fields_by_series: Dict[str, List[str]] = {}
    sort_fields_raw_by_series: Dict[str, tuple[str, str]] = {}
    series_index_path = site_root / "assets/data/series_index.json"
    try:
        series_index_obj = json.loads(series_index_path.read_text(encoding="utf-8"))
    except Exception:
        series_index_obj = None

    series_index_map = series_index_obj.get("series") if isinstance(series_index_obj, dict) else None
    if isinstance(series_index_map, dict):
        for sid, row in series_index_map.items():
            sid_norm = normalize_text(sid)
            if sid_norm == "":
                continue
            raw = normalize_text((row or {}).get("sort_fields") if isinstance(row, dict) else "")
            if raw == "":
                continue
            sort_fields_raw_by_series[sid_norm] = (raw, str(series_index_path))

    for sid, row in series.items():
        sid_norm = normalize_text(sid)
        if sid_norm == "":
            continue
        if sid_norm in sort_fields_raw_by_series:
            continue
        fm = row["fm"]
        raw = normalize_text(fm.get("sort_fields"))
        if raw == "":
            continue
        sort_fields_raw_by_series[sid_norm] = (raw, row["path"])

    for sid, source in sort_fields_raw_by_series.items():
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        raw, source_path = source
        parsed: List[str] = []
        bad = False
        for token in raw.split(","):
            t = normalize_text(token)
            if t == "":
                continue
            if t.startswith("-"):
                t = t[1:]
            t = t.lower()
            if t == "title_sort":
                t = "title"
            if t not in allowed_sort_fields:
                errors += 1
                add_sample(samples, {"check": "schema", "id": sid, "path": source_path, "message": f"sort_fields has unsupported token '{t}'"}, max_samples)
                bad = True
                continue
            parsed.append(t)
        if bad:
            continue
        if not parsed:
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": source_path, "message": "sort_fields resolves to empty token list"}, max_samples)
            continue
        if parsed[-1] != "work_id":
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": source_path, "message": "sort_fields must end with work_id"}, max_samples)
        if parsed.count("work_id") != 1:
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": source_path, "message": "sort_fields must include work_id exactly once"}, max_samples)
        sort_fields_by_series[sid] = parsed

    # Work route contracts
    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        fm = row["fm"]
        sid = normalize_series_ref(fm.get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        fm_work_id = normalize_text(fm.get("work_id"))
        if fm_work_id and fm_work_id != wid:
            errors += 1
            add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "work_id does not match generated contract id"}, max_samples)
        if not re_work_id.fullmatch(wid):
            errors += 1
            add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "invalid work_id format (expected 5 digits)"}, max_samples)
        layout = normalize_text(fm.get("layout"))
        if layout not in {"", "work"}:
            warnings += 1
            add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "work route contract should not carry a layout"}, max_samples)
        if sid != "" and not is_valid_series_ref(sid):
            errors += 1
            add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "invalid series_id format"}, max_samples)

    # Series route contracts
    for sid, row in series.items():
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        fm = row["fm"]
        fm_series_id = normalize_series_ref(fm.get("series_id"))
        if fm_series_id and fm_series_id != sid:
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": "series_id does not match generated contract id"}, max_samples)
        if not is_valid_series_ref(sid):
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": "invalid series_id format"}, max_samples)
        layout = normalize_text(fm.get("layout"))
        if layout not in {"", "series"}:
            warnings += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": "series route contract should not carry a layout"}, max_samples)

    # Work-detail route contracts
    for duid, row in work_details.items():
        wid = work_id_for_detail(duid, row)
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = ""
        if wid in works:
            sid = normalize_series_ref(works[wid]["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if not re_work_id.fullmatch(wid):
            errors += 1
            add_sample(samples, {"check": "schema", "id": duid, "path": row["path"], "message": "invalid work_detail work_id format"}, max_samples)
        fm_detail_uid = normalize_text(fm.get("detail_uid"))
        if fm_detail_uid and fm_detail_uid != duid:
            errors += 1
            add_sample(samples, {"check": "schema", "id": duid, "path": row["path"], "message": "detail_uid does not match generated contract id"}, max_samples)
        if not re_detail_uid.fullmatch(duid):
            errors += 1
            add_sample(samples, {"check": "schema", "id": duid, "path": row["path"], "message": "invalid detail_uid format (expected 00000-000)"}, max_samples)
        if re_detail_uid.fullmatch(duid):
            detail_work_id = duid.split("-", 1)[0]
            if detail_work_id != wid:
                errors += 1
                add_sample(samples, {"check": "schema", "id": duid, "path": row["path"], "message": "detail_uid prefix must match work_id"}, max_samples)

    return {"name": "schema", "error_count": errors, "warning_count": warnings, "samples": samples}


def check_json_schema(
    site_root: Path,
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []

    # Series index JSON
    series_index_path = site_root / "assets/data/series_index.json"
    series_map: Any = None
    try:
        series_index_obj = json.loads(series_index_path.read_text(encoding="utf-8"))
    except Exception as e:
        errors += 1
        add_sample(samples, {"check": "json_schema", "id": "series_index", "path": str(series_index_path), "message": f"invalid json: {e}"}, max_samples)
        series_index_obj = None

    if not isinstance(series_index_obj, dict):
        errors += 1
        add_sample(samples, {"check": "json_schema", "id": "series_index", "path": str(series_index_path), "message": "series index root must be object"}, max_samples)
    else:
        header = series_index_obj.get("header")
        series_map = series_index_obj.get("series")
        if not isinstance(header, dict):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": "series_index", "path": str(series_index_path), "message": "missing/invalid header object"}, max_samples)
        else:
            for key in ("schema", "version", "generated_at_utc", "count"):
                if key not in header:
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": "series_index", "path": str(series_index_path), "message": f"series index header missing '{key}'"}, max_samples)
            if normalize_text(header.get("schema")) != "series_index_v3":
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": "series_index", "path": str(series_index_path), "message": "series index schema must be series_index_v3"}, max_samples)
        if not isinstance(series_map, dict):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": "series_index", "path": str(series_index_path), "message": "series index series must be object map"}, max_samples)
        else:
            if isinstance(header, dict) and isinstance(header.get("count"), int) and header["count"] != len(series_map):
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": "series_index", "path": str(series_index_path), "message": "series index header.count does not match series map size"}, max_samples)
            for sid, row in series_map.items():
                sid_norm = normalize_text(sid)
                if sid_norm == "":
                    continue
                if series_ids_scope is not None and sid_norm not in series_ids_scope:
                    continue
                if not isinstance(row, dict):
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(series_index_path), "message": "series index entry must be object"}, max_samples)
                    continue
                allowed_fields = {"series_id", "title", "year", "year_display", "primary_work_id", "single_work_id"}
                extra_fields = sorted(set(row) - allowed_fields)
                if extra_fields:
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(series_index_path), "message": f"series index entry has non-lean fields: {', '.join(extra_fields)}"}, max_samples)
                for field in ("series_id", "title", "primary_work_id"):
                    if normalize_text(row.get(field)) == "":
                        errors += 1
                        add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(series_index_path), "message": f"series index entry missing {field}"}, max_samples)
                if normalize_text(row.get("series_id")) != sid_norm:
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(series_index_path), "message": "series index key does not match series_id"}, max_samples)

    # Exact Series JSON owns selected Series metadata and ordered lightweight members.
    for path in sorted((site_root / "assets/series/index").glob("*.json")):
        series_id = normalize_text(path.stem)
        if series_ids_scope is not None and series_id not in series_ids_scope:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": f"invalid exact Series JSON: {exc}"}, max_samples)
            continue
        header = payload.get("header") if isinstance(payload, dict) else None
        series_record = payload.get("series") if isinstance(payload, dict) else None
        member_works = payload.get("member_works") if isinstance(payload, dict) else None
        if not isinstance(header, dict) or normalize_text(header.get("schema")) != "series_record_v3":
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": "exact Series header must use series_record_v3"}, max_samples)
        elif normalize_text(header.get("series_id")) != series_id:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": "exact Series header identity does not match its file target"}, max_samples)
        if not isinstance(series_record, dict) or normalize_text(series_record.get("series_id")) != series_id:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": "exact Series identity does not match its file target"}, max_samples)
        if not isinstance(member_works, list):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": "exact Series member_works must be an array"}, max_samples)
            continue
        if isinstance(header, dict) and header.get("count") != len(member_works):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": "exact Series header.count does not match member_works"}, max_samples)
        member_ids: List[str] = []
        for member in member_works:
            if not isinstance(member, dict):
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": "exact Series member must be an object"}, max_samples)
                continue
            extra_fields = sorted(set(member) - {"work_id", "title", "year", "year_display"})
            work_id = normalize_text(member.get("work_id"))
            if extra_fields or work_id == "" or normalize_text(member.get("title")) == "":
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": "exact Series member must contain only a work_id, title, year, and year_display"}, max_samples)
            if work_id:
                member_ids.append(work_id)
        lean_row = series_map.get(series_id) if isinstance(series_map, dict) else None
        primary_work_id = normalize_text(lean_row.get("primary_work_id")) if isinstance(lean_row, dict) else ""
        if primary_work_id not in member_ids:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(path), "message": "lean primary_work_id is not an exact Series member"}, max_samples)
        if isinstance(lean_row, dict):
            single_work_id = normalize_text(lean_row.get("single_work_id"))
            expected_single_work_id = member_ids[0] if len(member_ids) == 1 else ""
            if single_work_id != expected_single_work_id:
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": series_id, "path": str(series_index_path), "message": "lean single_work_id does not match exact Series membership"}, max_samples)

    tag_assignments_path = resolve_repo_source_path(tag_source_paths.TAG_ASSIGNMENTS_REL_PATH)
    try:
        tag_assignments_obj = json.loads(tag_assignments_path.read_text(encoding="utf-8"))
    except Exception as e:
        errors += 1
        add_sample(samples, {"check": "json_schema", "id": "tag_assignments", "path": str(tag_assignments_path), "message": f"invalid json: {e}"}, max_samples)
        tag_assignments_obj = None

    if not isinstance(tag_assignments_obj, dict):
        errors += 1
        add_sample(samples, {"check": "json_schema", "id": "tag_assignments", "path": str(tag_assignments_path), "message": "tag assignments root must be object"}, max_samples)
    else:
        assignments_series = tag_assignments_obj.get("series")
        if not isinstance(assignments_series, dict):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": "tag_assignments", "path": str(tag_assignments_path), "message": "tag assignments series must be object map"}, max_samples)
        for sid, row in (assignments_series.items() if isinstance(assignments_series, dict) else []):
            sid_norm = normalize_text(sid)
            if sid_norm == "":
                continue
            if series_ids_scope is not None and sid_norm not in series_ids_scope:
                continue
            if not isinstance(row, dict):
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(tag_assignments_path), "message": "tag assignments series row must be object"}, max_samples)
                continue
            tags = row.get("tags")
            if not isinstance(tags, list):
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(tag_assignments_path), "message": "tag assignments series row missing tags list"}, max_samples)
            else:
                for tag_row in tags:
                    if not isinstance(tag_row, dict):
                        errors += 1
                        add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(tag_assignments_path), "message": "tag assignments series tags must be objects"}, max_samples)
                        break
                    if normalize_text(tag_row.get("tag_id")) == "":
                        errors += 1
                        add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(tag_assignments_path), "message": "tag assignments series tag missing tag_id"}, max_samples)
                        break
                    if "w_manual" not in tag_row:
                        errors += 1
                        add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(tag_assignments_path), "message": "tag assignments series tag missing w_manual"}, max_samples)
                        break
            works_map = row.get("works")
            if works_map is not None and not isinstance(works_map, dict):
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": sid_norm, "path": str(tag_assignments_path), "message": "tag assignments works must be object map when present"}, max_samples)
                continue
            if not isinstance(works_map, dict):
                continue
            for work_id, work_row in works_map.items():
                work_id_norm = normalize_text(work_id)
                if work_id_norm == "":
                    continue
                if work_ids_scope is not None and work_id_norm not in work_ids_scope:
                    continue
                if not re.fullmatch(r"\d{5}", work_id_norm):
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": work_id_norm, "path": str(tag_assignments_path), "message": "tag assignments work override key must be a 5-digit work_id"}, max_samples)
                    continue
                if not isinstance(work_row, dict):
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": work_id_norm, "path": str(tag_assignments_path), "message": "tag assignments work override row must be object"}, max_samples)
                    continue
                if not isinstance(work_row.get("tags"), list):
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": work_id_norm, "path": str(tag_assignments_path), "message": "tag assignments work override row missing tags list"}, max_samples)
                    continue
                for tag_row in work_row.get("tags", []):
                    if not isinstance(tag_row, dict):
                        errors += 1
                        add_sample(samples, {"check": "json_schema", "id": work_id_norm, "path": str(tag_assignments_path), "message": "tag assignments work override tags must be objects"}, max_samples)
                        break
                    if normalize_text(tag_row.get("tag_id")) == "":
                        errors += 1
                        add_sample(samples, {"check": "json_schema", "id": work_id_norm, "path": str(tag_assignments_path), "message": "tag assignments work override tag missing tag_id"}, max_samples)
                        break
                    if "w_manual" not in tag_row:
                        errors += 1
                        add_sample(samples, {"check": "json_schema", "id": work_id_norm, "path": str(tag_assignments_path), "message": "tag assignments work override tag missing w_manual"}, max_samples)
                        break
    # Work detail JSON
    for p in sorted((site_root / "assets/works/index").glob("*.json")):
        wid = p.stem
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": f"invalid json: {e}"}, max_samples)
            continue
        if not isinstance(obj, dict):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "work json root must be object"}, max_samples)
            continue
        header = obj.get("header")
        sections = obj.get("sections")
        if not isinstance(header, dict):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "missing/invalid header object"}, max_samples)
            continue
        for key in ("schema", "version", "generated_at_utc", "work_id", "count"):
            if key not in header:
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": f"work header missing '{key}'"}, max_samples)
        if normalize_text(header.get("schema")) != "work_record_v4" or normalize_text(header.get("work_id")) != wid:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "exact Work header schema or identity does not match its file target"}, max_samples)
        work_obj = obj.get("work")
        if not isinstance(work_obj, dict) or normalize_text(work_obj.get("work_id")) != wid:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "exact Work identity does not match its file target"}, max_samples)
        else:
            if "series_ids" not in work_obj:
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "work.series_ids missing"}, max_samples)
            elif not isinstance(work_obj.get("series_ids"), list):
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "work.series_ids must be list"}, max_samples)
            else:
                series_ids = [normalize_text(item) for item in work_obj.get("series_ids", [])]
                if not series_ids:
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "work.series_ids must not be empty"}, max_samples)
                elif any(item == "" for item in series_ids):
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "work.series_ids must not contain empty values"}, max_samples)
            for removed_key in ("series_id", "series_title", "series_sort"):
                if removed_key in work_obj:
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": f"work.{removed_key} is retired; derive it at runtime instead"}, max_samples)
        if not isinstance(sections, list):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "work sections must be list"}, max_samples)
            continue
        details_total = 0
        for sec in sections:
            if not isinstance(sec, dict):
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "section item must be object"}, max_samples)
                continue
            if "section_id" not in sec and "project_subfolder" not in sec:
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "section missing section_id"}, max_samples)
            if "section_title" not in sec and "project_subfolder" not in sec:
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "section missing section_title"}, max_samples)
            details = sec.get("details")
            if not isinstance(details, list):
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "section.details must be list"}, max_samples)
                continue
            details_total += len(details)
            for d in details:
                if not isinstance(d, dict):
                    errors += 1
                    add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "detail item must be object"}, max_samples)
                    continue
                for key in ("detail_id", "detail_uid", "title"):
                    if key not in d:
                        errors += 1
                        add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": f"detail missing '{key}'"}, max_samples)
        if isinstance(header.get("count"), int) and header["count"] != details_total:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "work header.count does not match total details"}, max_samples)

    return {"name": "json_schema", "error_count": errors, "warning_count": warnings, "samples": samples}


def check_links(
    site_root: Path,
    works: Dict[str, Dict[str, Any]],
    series: Dict[str, Dict[str, Any]],
    work_details: Dict[str, Dict[str, Any]],
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []

    # Generated link target existence.
    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = normalize_series_ref(row["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if sid != "" and sid not in series:
            errors += 1
            add_sample(samples, {"check": "links", "id": wid, "path": row["path"], "message": f"work links to missing series target '/series/?series={sid}'"}, max_samples)

    for duid, row in work_details.items():
        wid = work_id_for_detail(duid, row)
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        if wid in works:
            sid = normalize_series_ref(works[wid]["fm"].get("series_id"))
            if series_ids_scope is not None and sid not in series_ids_scope:
                continue
        if wid not in works:
            errors += 1
            add_sample(samples, {"check": "links", "id": duid, "path": row["path"], "message": f"work detail links to missing work target '/works/?work={wid}'"}, max_samples)

    # Query-contract sanity: producer keys should be accepted by destination pages.
    work_page_accepts = {"series", "series_page", "from", "return_sort", "return_dir", "return_series", "details_section", "details_page"}
    details_index_accepts = {"sort", "dir", "from_work", "from_work_title", "section", "section_label", "series", "series_page"}
    details_page_accepts = {"from_work", "from_work_title", "section", "series", "series_page", "details_section", "details_page", "section_label"}

    producers = [
        ("series->work", {"series", "series_page"}, work_page_accepts),
        ("work->details-index", {"from_work", "from_work_title", "section", "section_label", "series", "series_page"}, details_index_accepts),
        ("work->details-page", {"from_work", "from_work_title", "section", "details_section", "details_page", "series", "series_page"}, details_page_accepts),
        ("details-page->work", {"series", "series_page", "details_section", "details_page"}, work_page_accepts),
    ]
    for label, produced, accepted in producers:
        extra = sorted(produced - accepted)
        if extra:
            warnings += 1
            add_sample(samples, {"check": "links", "id": label, "message": f"query contract mismatch; unsupported keys: {', '.join(extra)}"}, max_samples)

    return {"name": "links", "error_count": errors, "warning_count": warnings, "samples": samples}


def check_media(
    site_root: Path,
    works: Dict[str, Dict[str, Any]],
    work_details: Dict[str, Dict[str, Any]],
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []
    works_img_dir = site_root / "assets/works/img"
    details_img_dir = site_root / "assets/work_details/img"

    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = normalize_series_ref(row["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        expected = expected_thumb_names(wid)
        for name in expected:
            p = works_img_dir / name
            if not p.exists():
                errors += 1
                add_sample(samples, {"check": "media", "id": wid, "path": str(p), "message": f"missing expected work media file: {name}"}, max_samples)
        # Primary files are intentionally remote-hosted in this project.
        # Do not assert local primary-* presence in this project.

    for duid, row in work_details.items():
        wid = work_id_for_detail(duid, row)
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = ""
        if wid in works:
            sid = normalize_series_ref(works[wid]["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        expected = expected_thumb_names(duid)
        for name in expected:
            p = details_img_dir / name
            if not p.exists():
                errors += 1
                add_sample(samples, {"check": "media", "id": duid, "path": str(p), "message": f"missing expected detail media file: {name}"}, max_samples)
        # Primary files are intentionally remote-hosted in this project.
        # Do not assert local primary-* presence in this project.

    return {"name": "media", "error_count": errors, "warning_count": warnings, "samples": samples}


def check_orphans(
    site_root: Path,
    works: Dict[str, Dict[str, Any]],
    series: Dict[str, Dict[str, Any]],
    work_details: Dict[str, Dict[str, Any]],
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    include_media_scan: bool,
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []

    work_ids = set(works.keys())
    detail_ids = set(work_details.keys())
    canonical_detail_refs = load_detail_refs_from_work_json(site_root=site_root, work_ids_scope=work_ids_scope)
    canonical_detail_ids = set(canonical_detail_refs.keys())
    works_by_series = load_exact_series_work_counts(site_root)
    if not works_by_series:
        for wid, row in works.items():
            if work_ids_scope is not None and wid not in work_ids_scope:
                continue
            sid = normalize_series_ref(row["fm"].get("series_id"))
            if sid == "":
                continue
            works_by_series[sid] = works_by_series.get(sid, 0) + 1

    for sid, row in series.items():
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if works_by_series.get(sid, 0) == 0:
            warnings += 1
            add_sample(samples, {"check": "orphans", "id": sid, "path": row["path"], "message": "series contract has no works"}, max_samples)

    for duid, row in work_details.items():
        wid = work_id_for_detail(duid, row)
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = ""
        if wid in works:
            sid = normalize_series_ref(works[wid]["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if duid not in canonical_detail_ids:
            warnings += 1
            add_sample(
                samples,
                {
                    "check": "orphans",
                    "id": duid,
                    "path": row["path"],
                    "message": "work detail contract is not present in any work JSON",
                },
                max_samples,
            )

    for p in sorted((site_root / "assets/works/index").glob("*.json")):
        wid = p.stem
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        if wid not in work_ids:
            warnings += 1
            add_sample(samples, {"check": "orphans", "id": wid, "path": str(p), "message": "work details JSON has no matching work page"}, max_samples)

    if include_media_scan:
        works_img_dir = site_root / "assets/works/img"
        details_img_dir = site_root / "assets/work_details/img"
        works_media_pattern = media_filename_regex(r"\d{5}")
        details_media_pattern = media_filename_regex(r"\d{5}-\d{3}")

        for p in sorted(works_img_dir.glob(f"*.{ASSET_FORMAT}")):
            m = works_media_pattern.match(p.name)
            if not m:
                continue
            wid = m.group(1)
            if work_ids_scope is not None and wid not in work_ids_scope:
                continue
            if wid not in work_ids:
                warnings += 1
                add_sample(samples, {"check": "orphans", "id": wid, "path": str(p), "message": "orphan work image file (no matching work page)"}, max_samples)

        for p in sorted(details_img_dir.glob(f"*.{ASSET_FORMAT}")):
            m = details_media_pattern.match(p.name)
            if not m:
                continue
            duid = m.group(1)
            wid = duid.split("-", 1)[0]
            if work_ids_scope is not None and wid not in work_ids_scope:
                continue
            if duid not in detail_ids and duid not in canonical_detail_ids:
                warnings += 1
                add_sample(samples, {"check": "orphans", "id": duid, "path": str(p), "message": "orphan detail image file (no matching detail page)"}, max_samples)

    return {"name": "orphans", "error_count": errors, "warning_count": warnings, "samples": samples}


def render_markdown_report(report: Dict[str, Any], flag_rows: List[Dict[str, str]]) -> str:
    summary = report.get("summary", {})
    checks = report.get("checks", [])
    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    lines: List[str] = []
    lines.append("# Audit Report")
    lines.append("")
    lines.append(f"- Run at: `{ts}`")
    lines.append(f"- Duration: `{summary.get('duration_ms', 0)}ms`")
    lines.append(f"- Checks: `{', '.join(summary.get('checks_run', []))}`")
    lines.append(f"- Errors: `{summary.get('errors', 0)}`")
    lines.append(f"- Warnings: `{summary.get('warnings', 0)}`")
    lines.append("")
    lines.append("## Flags")
    lines.append("")
    lines.append("| flag | value | default? |")
    lines.append("| --- | --- | --- |")
    for row in flag_rows:
        lines.append(f"| `{row['flag']}` | `{row['value']}` | `{row['is_default']}` |")
    lines.append("")
    lines.append("## Check Summary")
    lines.append("")
    for c in checks:
        lines.append(f"- `{c.get('name', '-')}`: errors={c.get('error_count', 0)} warnings={c.get('warning_count', 0)}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for c in checks:
        name = c.get("name", "-")
        lines.append(f"### {name}")
        lines.append("")
        samples = c.get("samples", []) or []
        total_findings = int(c.get("error_count", 0)) + int(c.get("warning_count", 0))
        if total_findings > len(samples):
            lines.append(f"_Showing first {len(samples)} of {total_findings} findings (see `--max-samples`)._")
            lines.append("")
        if not samples:
            lines.append("- none")
            lines.append("")
            continue
        for s in samples:
            ident = s.get("id") or s.get("series_id") or "-"
            msg = s.get("message", "")
            p = s.get("path", "")
            if p:
                lines.append(f"- `{ident}`: {msg} (`{p}`)")
            else:
                lines.append(f"- `{ident}`: {msg}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    t0 = time.time()
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-root", default=".", help="Path to site root (default: current directory)")
    ap.add_argument("--checks", default="cross_refs,schema", help="Comma-separated checks to run")
    ap.add_argument(
        "--check-only",
        action="append",
        default=[],
        help=(
            "Convenience alias to run only specific check(s). "
            "Repeat flag and/or pass comma-separated values. "
            "Overrides --checks when provided."
        ),
    )
    ap.add_argument("--series-ids", default="", help="Comma-separated series_ids scope")
    ap.add_argument("--work-ids", default="", help="Comma-separated work_ids/ranges scope (e.g. 66-74,38-40)")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero when errors are found")
    ap.add_argument("--json-out", default="", help="Optional path to write JSON report")
    ap.add_argument("--md-out", default="var/studio/reports/audit-latest.md", help="Path to write Markdown report (overwrites on each run)")
    ap.add_argument("--max-samples", type=int, default=20, help="Max sample findings per check")
    ap.add_argument("--orphans-media", action="store_true", help="Include orphan media-file scan in the orphans check")
    args = ap.parse_args()

    site_root = Path(args.site_root).expanduser().resolve()
    if args.check_only:
        checks_requested = {
            normalize_text(item).lower()
            for raw in args.check_only
            for item in str(raw).split(",")
            if normalize_text(item) != ""
        }
    else:
        checks_requested = {normalize_text(c).lower() for c in args.checks.split(",") if normalize_text(c) != ""}
    valid_checks = {"cross_refs", "schema", "json_schema", "links", "media", "orphans"}
    invalid = sorted(checks_requested - valid_checks)
    if invalid:
        raise SystemExit(f"Invalid --checks value(s): {', '.join(invalid)}. Allowed: {', '.join(sorted(valid_checks))}")

    try:
        series_ids_scope = {normalize_series_id(x) for x in args.series_ids.split(",") if normalize_text(x) != ""} or None
    except ValueError as exc:
        raise SystemExit(f"Invalid --series-ids value: {exc}") from exc
    work_ids_scope = parse_work_id_selection(args.work_ids) if normalize_text(args.work_ids) != "" else None

    cwd_prev = Path.cwd()
    try:
        # Use site_root as base for relative globs.
        import os
        os.chdir(site_root)

        works, series, work_details = load_generated_route_contracts(site_root)
        works_dups: List[str] = []
        series_dups: List[str] = []
        detail_dups: List[str] = []

        checks: List[Dict[str, Any]] = []
        if "cross_refs" in checks_requested:
            checks.append(
                check_cross_refs(
                    site_root=site_root,
                    works=works,
                    series=series,
                    work_details=work_details,
                    works_dups=works_dups,
                    series_dups=series_dups,
                    detail_dups=detail_dups,
                    series_ids_scope=series_ids_scope,
                    work_ids_scope=work_ids_scope,
                    max_samples=args.max_samples,
                )
            )
        if "schema" in checks_requested:
            checks.append(
                check_schema(
                    site_root=site_root,
                    works=works,
                    series=series,
                    work_details=work_details,
                    series_ids_scope=series_ids_scope,
                    work_ids_scope=work_ids_scope,
                    max_samples=args.max_samples,
                )
            )
        if "json_schema" in checks_requested:
            checks.append(
                check_json_schema(
                    site_root=site_root,
                    series_ids_scope=series_ids_scope,
                    work_ids_scope=work_ids_scope,
                    max_samples=args.max_samples,
                )
            )
        if "links" in checks_requested:
            checks.append(
                check_links(
                    site_root=site_root,
                    works=works,
                    series=series,
                    work_details=work_details,
                    series_ids_scope=series_ids_scope,
                    work_ids_scope=work_ids_scope,
                    max_samples=args.max_samples,
                )
            )
        if "media" in checks_requested:
            checks.append(
                check_media(
                    site_root=site_root,
                    works=works,
                    work_details=work_details,
                    series_ids_scope=series_ids_scope,
                    work_ids_scope=work_ids_scope,
                    max_samples=args.max_samples,
                )
            )
        if "orphans" in checks_requested:
            checks.append(
                check_orphans(
                    site_root=site_root,
                    works=works,
                    series=series,
                    work_details=work_details,
                    series_ids_scope=series_ids_scope,
                    work_ids_scope=work_ids_scope,
                    include_media_scan=args.orphans_media,
                    max_samples=args.max_samples,
                )
            )
    finally:
        import os
        os.chdir(cwd_prev)

    total_errors = sum(c["error_count"] for c in checks)
    total_warnings = sum(c["warning_count"] for c in checks)
    duration_ms = int((time.time() - t0) * 1000)
    report = {
        "summary": {
            "errors": total_errors,
            "warnings": total_warnings,
            "checks_run": [c["name"] for c in checks],
            "duration_ms": duration_ms,
        },
        "checks": checks,
    }

    # Human summary
    print(f"Audit complete in {duration_ms}ms")
    print(f"Errors: {total_errors}  Warnings: {total_warnings}")
    for c in checks:
        print(f"- {c['name']}: errors={c['error_count']} warnings={c['warning_count']}")
        for s in c.get("samples", [])[: args.max_samples]:
            msg = s.get("message", "")
            ident = s.get("id") or s.get("series_id") or "-"
            p = s.get("path", "")
            print(f"  * {ident}: {msg}{' [' + p + ']' if p else ''}")

    if args.json_out:
        out = Path(args.json_out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote JSON report: {out}")

    default_map: Dict[str, Any] = {
        "site_root": ".",
        "checks": "cross_refs,schema",
        "check_only": [],
        "series_ids": "",
        "work_ids": "",
        "strict": False,
        "json_out": "",
        "md_out": "var/studio/reports/audit-latest.md",
        "max_samples": 20,
        "orphans_media": False,
    }
    flag_rows: List[Dict[str, str]] = []
    for key in [
        "site_root",
        "checks",
        "check_only",
        "series_ids",
        "work_ids",
        "strict",
        "json_out",
        "md_out",
        "max_samples",
        "orphans_media",
    ]:
        value = getattr(args, key)
        if isinstance(value, list):
            shown_value = ",".join(str(v) for v in value) if value else "(none)"
            is_default = "yes" if value == default_map[key] else "no"
        else:
            shown_value = str(value) if str(value) != "" else "(empty)"
            is_default = "yes" if value == default_map[key] else "no"
        flag_rows.append({"flag": "--" + key.replace("_", "-"), "value": shown_value, "is_default": is_default})

    md_out = Path(args.md_out).expanduser()
    md_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_report = render_markdown_report(report, flag_rows)
    md_out.write_text(markdown_report, encoding="utf-8")
    print(f"Wrote Markdown report: {md_out}")

    if args.strict and total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
