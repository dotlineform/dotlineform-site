#!/usr/bin/env python3
"""
Audit generated site consistency (read-only).

Initial checks:
- sort_drift: compare per-series JSON order vs _works front-matter series_sort order
- cross_refs: validate key cross-artifact references and duplicate IDs
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


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


def is_slug_safe(s: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s or "") is not None


def load_collection(path_glob: str, id_field: str) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    rows: Dict[str, Dict[str, Any]] = {}
    dups: List[str] = []
    for p in sorted(Path().glob(path_glob)):
        fm = parse_front_matter(p)
        if not fm:
            continue
        idv = normalize_text(fm.get(id_field))
        if idv == "":
            continue
        if idv in rows:
            dups.append(idv)
        rows[idv] = {"path": str(p), "fm": fm}
    return rows, dups


def add_sample(samples: List[Dict[str, Any]], item: Dict[str, Any], max_samples: int) -> None:
    if len(samples) < max_samples:
        samples.append(item)


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


def parse_sitemap_rows(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not path.exists():
        return rows
    current: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("url:"):
            current["url"] = normalize_url(str(parse_scalar_from_fm_line(line.split(":", 1)[1]) or ""))
        elif line.startswith("source:"):
            current["source"] = normalize_text(parse_scalar_from_fm_line(line.split(":", 1)[1]) or "")
        elif line.startswith("title:"):
            current["title"] = normalize_text(parse_scalar_from_fm_line(line.split(":", 1)[1]) or "")
        if "url" in current and "source" in current:
            rows.append(
                {
                    "url": current.get("url", ""),
                    "source": current.get("source", ""),
                    "title": current.get("title", ""),
                }
            )
            current = {}
    return rows


def check_sort_drift(
    site_root: Path,
    works: Dict[str, Dict[str, Any]],
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []

    works_by_series: Dict[str, List[Tuple[str, str]]] = {}
    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        fm = row["fm"]
        sid = normalize_text(fm.get("series_id"))
        if sid == "":
            continue
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        series_sort = normalize_text(fm.get("series_sort")) or wid
        works_by_series.setdefault(sid, []).append((series_sort, wid))

    json_dir = site_root / "assets/series/index"
    for json_path in sorted(json_dir.glob("*.json")):
        series_id = json_path.stem
        if series_ids_scope is not None and series_id not in series_ids_scope:
            continue
        try:
            obj = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors += 1
            add_sample(samples, {"check": "sort_drift", "series_id": series_id, "path": str(json_path), "message": f"invalid json: {e}"}, max_samples)
            continue
        json_ids = [normalize_text(x) for x in obj.get("work_ids", []) if normalize_text(x) != ""]
        if work_ids_scope is not None:
            json_ids = [wid for wid in json_ids if wid in work_ids_scope]
        derived = [wid for _, wid in sorted(works_by_series.get(series_id, []), key=lambda t: (t[0], t[1]))]

        if len(json_ids) != len(derived):
            errors += 1
            add_sample(
                samples,
                {
                    "check": "sort_drift",
                    "series_id": series_id,
                    "path": str(json_path),
                    "message": "count mismatch between series JSON and _works series_sort order",
                    "json_count": len(json_ids),
                    "works_count": len(derived),
                },
                max_samples,
            )

        shared = [wid for wid in json_ids if wid in set(derived)]
        pos = {wid: i for i, wid in enumerate(derived)}
        mismatch_found = False
        for i, wid in enumerate(shared):
            if pos.get(wid) != i:
                mismatch_found = True
                break
        if mismatch_found:
            errors += 1
            add_sample(
                samples,
                {
                    "check": "sort_drift",
                    "series_id": series_id,
                    "path": str(json_path),
                    "message": "order mismatch between series JSON work_ids and _works series_sort ordering",
                },
                max_samples,
            )

        # Sort metadata sanity
        header = obj.get("header") if isinstance(obj, dict) else None
        sort_fields = normalize_text(header.get("sort_fields")) if isinstance(header, dict) else ""
        if sort_fields == "":
            warnings += 1
            add_sample(
                samples,
                {
                    "check": "sort_drift",
                    "series_id": series_id,
                    "path": str(json_path),
                    "message": "missing header.sort_fields",
                },
                max_samples,
            )

    return {"name": "sort_drift", "error_count": errors, "warning_count": warnings, "samples": samples}


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

    # _works -> _series references
    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = normalize_text(row["fm"].get("series_id"))
        if sid == "":
            continue
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if sid not in series:
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": wid, "path": row["path"], "message": f"missing series page for series_id '{sid}'"}, max_samples)

    # _work_details -> _works references
    for duid, row in work_details.items():
        wid = normalize_text(row["fm"].get("work_id"))
        if wid == "":
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": duid, "path": row["path"], "message": "missing work_id in work detail"}, max_samples)
            continue
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        if wid not in works:
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": duid, "path": row["path"], "message": f"work detail references missing work_id '{wid}'"}, max_samples)

    # series json -> _works references
    json_dir = site_root / "assets/series/index"
    for json_path in sorted(json_dir.glob("*.json")):
        sid = json_path.stem
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        try:
            obj = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors += 1
            add_sample(samples, {"check": "cross_refs", "id": sid, "path": str(json_path), "message": f"invalid json: {e}"}, max_samples)
            continue
        for wid_raw in obj.get("work_ids", []):
            wid = normalize_text(wid_raw)
            if wid == "":
                continue
            if work_ids_scope is not None and wid not in work_ids_scope:
                continue
            if wid not in works:
                errors += 1
                add_sample(samples, {"check": "cross_refs", "id": sid, "path": str(json_path), "message": f"series json references missing work_id '{wid}'"}, max_samples)

    return {"name": "cross_refs", "error_count": errors, "warning_count": warnings, "samples": samples}


def check_schema(
    works: Dict[str, Dict[str, Any]],
    series: Dict[str, Dict[str, Any]],
    work_details: Dict[str, Dict[str, Any]],
    moments: Dict[str, Dict[str, Any]],
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []

    re_work_id = re.compile(r"^\d{5}$")
    re_detail_uid = re.compile(r"^\d{5}-\d{3}$")
    re_series_sort = re.compile(r"^(?:\d{5}|\d{3,}-\d{5})$")
    allowed_sort_fields = {"title", "year", "work_id", "title_sort"}

    # Parse/validate series sort_fields once for downstream work-level checks.
    sort_fields_by_series: Dict[str, List[str]] = {}
    for sid, row in series.items():
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        fm = row["fm"]
        raw = normalize_text(fm.get("sort_fields"))
        if raw == "":
            continue
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
                add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": f"sort_fields has unsupported token '{t}'"}, max_samples)
                bad = True
                continue
            parsed.append(t)
        if bad:
            continue
        if not parsed:
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": "sort_fields resolves to empty token list"}, max_samples)
            continue
        if parsed[-1] != "work_id":
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": "sort_fields must end with work_id"}, max_samples)
        if parsed.count("work_id") != 1:
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": "sort_fields must include work_id exactly once"}, max_samples)
        sort_fields_by_series[sid] = parsed

    # _works
    works_required = ["work_id", "title", "series_id", "series_sort"]
    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        fm = row["fm"]
        sid = normalize_text(fm.get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        for field in works_required:
            if is_empty(fm.get(field)):
                errors += 1
                add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": f"missing required works field '{field}'"}, max_samples)
        if not re_work_id.fullmatch(normalize_text(fm.get("work_id"))):
            errors += 1
            add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "invalid work_id format (expected 5 digits)"}, max_samples)
        if sid != "" and not is_slug_safe(sid):
            errors += 1
            add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "invalid series_id slug format"}, max_samples)
        if not re_series_sort.fullmatch(normalize_text(fm.get("series_sort"))):
            errors += 1
            add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "invalid series_sort format"}, max_samples)
        series_sort_value = normalize_text(fm.get("series_sort"))
        sf = sort_fields_by_series.get(sid, ["work_id"])
        if sf == ["work_id"]:
            if series_sort_value != wid:
                errors += 1
                add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "series_sort should equal work_id for default sort_fields"}, max_samples)
        else:
            if not series_sort_value.endswith(f"-{wid}"):
                errors += 1
                add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "series_sort should end with '-<work_id>' for custom sort_fields"}, max_samples)
        title = normalize_text(fm.get("title"))
        title_sort = normalize_text(fm.get("title_sort"))
        if re.search(r"\d", title) and title_sort == "":
            warnings += 1
            add_sample(samples, {"check": "schema", "id": wid, "path": row["path"], "message": "missing title_sort for numeric title"}, max_samples)

    # _series
    series_required = ["series_id", "title", "title_sort", "sort_fields"]
    for sid, row in series.items():
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        fm = row["fm"]
        for field in series_required:
            if is_empty(fm.get(field)):
                errors += 1
                add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": f"missing required series field '{field}'"}, max_samples)
        if not is_slug_safe(normalize_text(fm.get("series_id"))):
            errors += 1
            add_sample(samples, {"check": "schema", "id": sid, "path": row["path"], "message": "invalid series_id slug format"}, max_samples)

    # _work_details
    detail_required = ["work_id", "detail_id", "detail_uid", "title"]
    for duid, row in work_details.items():
        fm = row["fm"]
        wid = normalize_text(fm.get("work_id"))
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = ""
        if wid in works:
            sid = normalize_text(works[wid]["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        for field in detail_required:
            if is_empty(fm.get(field)):
                errors += 1
                add_sample(samples, {"check": "schema", "id": duid, "path": row["path"], "message": f"missing required work_detail field '{field}'"}, max_samples)
        if not re_work_id.fullmatch(wid):
            errors += 1
            add_sample(samples, {"check": "schema", "id": duid, "path": row["path"], "message": "invalid work_detail work_id format"}, max_samples)
        if not re_detail_uid.fullmatch(normalize_text(fm.get("detail_uid"))):
            errors += 1
            add_sample(samples, {"check": "schema", "id": duid, "path": row["path"], "message": "invalid detail_uid format (expected 00000-000)"}, max_samples)
        detail_uid = normalize_text(fm.get("detail_uid"))
        if re_detail_uid.fullmatch(detail_uid):
            detail_work_id = detail_uid.split("-", 1)[0]
            if detail_work_id != wid:
                errors += 1
                add_sample(samples, {"check": "schema", "id": duid, "path": row["path"], "message": "detail_uid prefix must match work_id"}, max_samples)

    # _moments (basic)
    moment_required = ["moment_id", "title"]
    for mid, row in moments.items():
        fm = row["fm"]
        for field in moment_required:
            if is_empty(fm.get(field)):
                errors += 1
                add_sample(samples, {"check": "schema", "id": mid, "path": row["path"], "message": f"missing required moment field '{field}'"}, max_samples)
        if not is_slug_safe(normalize_text(fm.get("moment_id"))):
            errors += 1
            add_sample(samples, {"check": "schema", "id": mid, "path": row["path"], "message": "invalid moment_id slug format"}, max_samples)

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

    # Series JSON
    for p in sorted((site_root / "assets/series/index").glob("*.json")):
        sid = p.stem
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": sid, "path": str(p), "message": f"invalid json: {e}"}, max_samples)
            continue
        if not isinstance(obj, dict):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": sid, "path": str(p), "message": "series json root must be object"}, max_samples)
            continue
        header = obj.get("header")
        work_ids = obj.get("work_ids")
        if not isinstance(header, dict):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": sid, "path": str(p), "message": "missing/invalid header object"}, max_samples)
            continue
        for key in ("series_id", "count", "sort_fields", "hash"):
            if key not in header:
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": sid, "path": str(p), "message": f"series header missing '{key}'"}, max_samples)
        if not isinstance(work_ids, list):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": sid, "path": str(p), "message": "series work_ids must be list"}, max_samples)
            continue
        if isinstance(header.get("count"), int) and header["count"] != len(work_ids):
            errors += 1
            add_sample(samples, {"check": "json_schema", "id": sid, "path": str(p), "message": "series header.count does not match work_ids length"}, max_samples)

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
        for key in ("work_id", "count", "hash"):
            if key not in header:
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": f"work header missing '{key}'"}, max_samples)
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
            if "project_subfolder" not in sec:
                errors += 1
                add_sample(samples, {"check": "json_schema", "id": wid, "path": str(p), "message": "section missing project_subfolder"}, max_samples)
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
    moments: Dict[str, Dict[str, Any]],
    series_ids_scope: Optional[set[str]],
    work_ids_scope: Optional[set[str]],
    max_samples: int,
) -> Dict[str, Any]:
    errors = 0
    warnings = 0
    samples: List[Dict[str, Any]] = []

    # Sitemap target existence (source file/glob + canonical route sanity).
    sitemap_rows = parse_sitemap_rows(site_root / "_data/sitemap.yml")
    pattern_source_to_count = {
        "_works/*.md": len(works),
        "_series/*.md": len(series),
        "_work_details/*.md": len(work_details),
        "_moments/*.md": len(moments),
    }
    static_target_urls: Set[str] = set()
    static_candidates = [
        ("index.md", "/"),
        ("about.md", "/about/"),
        ("works/index.md", "/works/"),
        ("work_details/index.md", "/work_details/"),
        ("series/index.md", "/series/"),
        ("moments/index.md", "/moments/"),
        ("themes/index.md", "/themes/"),
        ("research/index.md", "/research/"),
        ("palette.html", "/palette/"),
    ]
    for rel, default_url in static_candidates:
        path = site_root / rel
        if not path.exists():
            continue
        fm = parse_front_matter(path)
        static_target_urls.add(normalize_url(normalize_text(fm.get("permalink")) or default_url))

    for row in sitemap_rows:
        source = row["source"]
        url = row["url"]
        title = row.get("title", "") or url
        if "*" in source:
            if source in pattern_source_to_count:
                if pattern_source_to_count[source] == 0:
                    errors += 1
                    add_sample(samples, {"check": "links", "id": title, "path": "_data/sitemap.yml", "message": f"sitemap source glob has no matches: {source}"}, max_samples)
            else:
                if len(list(site_root.glob(source))) == 0:
                    errors += 1
                    add_sample(samples, {"check": "links", "id": title, "path": "_data/sitemap.yml", "message": f"sitemap source glob has no matches: {source}"}, max_samples)
        else:
            if not (site_root / source).exists():
                errors += 1
                add_sample(samples, {"check": "links", "id": title, "path": "_data/sitemap.yml", "message": f"sitemap source file missing: {source}"}, max_samples)
        if ":id" not in url and not url.startswith(("http://", "https://")) and url not in static_target_urls:
            warnings += 1
            add_sample(samples, {"check": "links", "id": title, "path": "_data/sitemap.yml", "message": f"sitemap url has no known static target: {url}"}, max_samples)

    # Generated link target existence.
    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = normalize_text(row["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if sid != "" and sid not in series:
            errors += 1
            add_sample(samples, {"check": "links", "id": wid, "path": row["path"], "message": f"work links to missing series target '/series/{sid}/'"}, max_samples)

    for duid, row in work_details.items():
        wid = normalize_text(row["fm"].get("work_id"))
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        if wid in works:
            sid = normalize_text(works[wid]["fm"].get("series_id"))
            if series_ids_scope is not None and sid not in series_ids_scope:
                continue
        if wid not in works:
            errors += 1
            add_sample(samples, {"check": "links", "id": duid, "path": row["path"], "message": f"work detail links to missing work target '/works/{wid}/'"}, max_samples)

    # Query-contract sanity: producer keys should be accepted by destination pages.
    work_page_accepts = {"series", "series_page", "from", "return_sort", "return_dir", "return_series", "details_section", "details_page"}
    details_index_accepts = {"sort", "dir", "from_work", "from_work_title", "section", "section_label", "series", "series_page"}
    details_page_accepts = {"from_work", "from_work_title", "section", "series", "series_page", "details_section", "details_page", "section_label"}

    producers = [
        ("series->work", {"series", "series_page"}, work_page_accepts),
        ("works-index->work", {"from", "return_sort", "return_dir", "return_series"}, work_page_accepts),
        ("work->details-index", {"from_work", "from_work_title", "section", "details_section", "details_page", "series", "series_page"}, details_index_accepts),
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
    works_files_dir = site_root / "assets/works/files"

    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = normalize_text(row["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        fm = row["fm"]
        expected = [
            f"{wid}-thumb-96.webp",
            f"{wid}-thumb-192.webp",
            f"{wid}-primary-800.webp",
            f"{wid}-primary-1200.webp",
            f"{wid}-primary-1600.webp",
        ]
        for name in expected:
            p = works_img_dir / name
            if not p.exists():
                errors += 1
                add_sample(samples, {"check": "media", "id": wid, "path": str(p), "message": f"missing expected work media file: {name}"}, max_samples)
        has_primary_2400 = str(fm.get("has_primary_2400")).lower() == "true"
        p2400 = works_img_dir / f"{wid}-primary-2400.webp"
        if has_primary_2400 and not p2400.exists():
            errors += 1
            add_sample(samples, {"check": "media", "id": wid, "path": str(p2400), "message": "has_primary_2400=true but 2400 file is missing"}, max_samples)
        if (not has_primary_2400) and p2400.exists():
            warnings += 1
            add_sample(samples, {"check": "media", "id": wid, "path": str(p2400), "message": "2400 file exists but has_primary_2400 is not true"}, max_samples)

        download = normalize_text(fm.get("download"))
        if download != "":
            expected_download = works_files_dir / f"{wid}-{Path(download).name}"
            if not expected_download.exists():
                errors += 1
                add_sample(samples, {"check": "media", "id": wid, "path": str(expected_download), "message": "download declared but file missing in assets/works/files"}, max_samples)

    for duid, row in work_details.items():
        fm = row["fm"]
        wid = normalize_text(fm.get("work_id"))
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = ""
        if wid in works:
            sid = normalize_text(works[wid]["fm"].get("series_id"))
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        expected = [
            f"{duid}-thumb-96.webp",
            f"{duid}-thumb-192.webp",
            f"{duid}-primary-800.webp",
            f"{duid}-primary-1200.webp",
            f"{duid}-primary-1600.webp",
        ]
        for name in expected:
            p = details_img_dir / name
            if not p.exists():
                errors += 1
                add_sample(samples, {"check": "media", "id": duid, "path": str(p), "message": f"missing expected detail media file: {name}"}, max_samples)
        has_primary_2400 = str(fm.get("has_primary_2400")).lower() == "true"
        p2400 = details_img_dir / f"{duid}-primary-2400.webp"
        if has_primary_2400 and not p2400.exists():
            errors += 1
            add_sample(samples, {"check": "media", "id": duid, "path": str(p2400), "message": "has_primary_2400=true but 2400 file is missing"}, max_samples)
        if (not has_primary_2400) and p2400.exists():
            warnings += 1
            add_sample(samples, {"check": "media", "id": duid, "path": str(p2400), "message": "2400 file exists but has_primary_2400 is not true"}, max_samples)

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
    series_ids = set(series.keys())
    detail_ids = set(work_details.keys())
    works_by_series: Dict[str, int] = {}
    for wid, row in works.items():
        if work_ids_scope is not None and wid not in work_ids_scope:
            continue
        sid = normalize_text(row["fm"].get("series_id"))
        if sid == "":
            continue
        works_by_series[sid] = works_by_series.get(sid, 0) + 1

    for sid, row in series.items():
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if works_by_series.get(sid, 0) == 0:
            warnings += 1
            add_sample(samples, {"check": "orphans", "id": sid, "path": row["path"], "message": "series page has no works"}, max_samples)

    for p in sorted((site_root / "assets/series/index").glob("*.json")):
        sid = p.stem
        if series_ids_scope is not None and sid not in series_ids_scope:
            continue
        if sid not in series_ids:
            warnings += 1
            add_sample(samples, {"check": "orphans", "id": sid, "path": str(p), "message": "series JSON has no matching series page"}, max_samples)

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
        works_files_dir = site_root / "assets/works/files"

        for p in sorted(works_img_dir.glob("*.webp")):
            m = re.match(r"^(\d{5})-(?:thumb-(?:96|192)|primary-(?:800|1200|1600|2400))\.webp$", p.name)
            if not m:
                continue
            wid = m.group(1)
            if work_ids_scope is not None and wid not in work_ids_scope:
                continue
            if wid not in work_ids:
                warnings += 1
                add_sample(samples, {"check": "orphans", "id": wid, "path": str(p), "message": "orphan work image file (no matching work page)"}, max_samples)

        for p in sorted(details_img_dir.glob("*.webp")):
            m = re.match(r"^(\d{5}-\d{3})-(?:thumb-(?:96|192)|primary-(?:800|1200|1600|2400))\.webp$", p.name)
            if not m:
                continue
            duid = m.group(1)
            if duid not in detail_ids:
                warnings += 1
                add_sample(samples, {"check": "orphans", "id": duid, "path": str(p), "message": "orphan detail image file (no matching detail page)"}, max_samples)

        for p in sorted(works_files_dir.glob("*")):
            if not p.is_file():
                continue
            m = re.match(r"^(\d{5})-.+$", p.name)
            if not m:
                continue
            wid = m.group(1)
            if work_ids_scope is not None and wid not in work_ids_scope:
                continue
            if wid not in work_ids:
                warnings += 1
                add_sample(samples, {"check": "orphans", "id": wid, "path": str(p), "message": "orphan work download file (no matching work page)"}, max_samples)

    return {"name": "orphans", "error_count": errors, "warning_count": warnings, "samples": samples}


def main() -> None:
    t0 = time.time()
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-root", default=".", help="Path to site root (default: current directory)")
    ap.add_argument("--checks", default="sort_drift,cross_refs", help="Comma-separated checks to run")
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
    valid_checks = {"sort_drift", "cross_refs", "schema", "json_schema", "links", "media", "orphans"}
    invalid = sorted(checks_requested - valid_checks)
    if invalid:
        raise SystemExit(f"Invalid --checks value(s): {', '.join(invalid)}. Allowed: {', '.join(sorted(valid_checks))}")

    series_ids_scope = {normalize_text(x) for x in args.series_ids.split(",") if normalize_text(x) != ""} or None
    work_ids_scope = parse_work_id_selection(args.work_ids) if normalize_text(args.work_ids) != "" else None

    cwd_prev = Path.cwd()
    try:
        # Use site_root as base for relative globs.
        import os
        os.chdir(site_root)

        works, works_dups = load_collection("_works/*.md", "work_id")
        series, series_dups = load_collection("_series/*.md", "series_id")
        work_details, detail_dups = load_collection("_work_details/*.md", "detail_uid")
        moments, _moment_dups = load_collection("_moments/*.md", "moment_id")

        checks: List[Dict[str, Any]] = []
        if "sort_drift" in checks_requested:
            checks.append(
                check_sort_drift(
                    site_root=site_root,
                    works=works,
                    series_ids_scope=series_ids_scope,
                    work_ids_scope=work_ids_scope,
                    max_samples=args.max_samples,
                )
            )
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
                    works=works,
                    series=series,
                    work_details=work_details,
                    moments=moments,
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
                    moments=moments,
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

    if args.strict and total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
