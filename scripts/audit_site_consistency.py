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
from typing import Any, Dict, Iterable, List, Optional, Tuple


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
    valid_checks = {"sort_drift", "cross_refs"}
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
