from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = REPO_ROOT / "site-tools"
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

import site_code_update as site_code


CONFIG_PATH = REPO_ROOT / "site-tools" / "config" / "site-code-update.json"


def test_repository_manifest_matches_current_projection() -> None:
    projections = site_code.load_manifest(REPO_ROOT, CONFIG_PATH)
    plan = site_code.plan_site_code_update(REPO_ROOT, projections)

    assert sum(len(projection.files) for projection in projections) == 65
    assert plan.drift_count == 0
    assert len(plan.unchanged) == 65


def test_complete_projection_copies_only_public_and_shared_files(tmp_path: Path) -> None:
    manifest_path = _create_test_repository(tmp_path)
    projections = site_code.load_manifest(tmp_path, manifest_path)
    plan = site_code.plan_site_code_update(tmp_path, projections)

    assert len(plan.added) == 6
    assert not plan.changed
    assert not plan.removed

    site_code.apply_site_code_update(tmp_path, projections, plan)

    for projection in projections:
        for filename in projection.files:
            source = tmp_path / projection.source_root / filename
            target = tmp_path / projection.destination_root / filename
            assert target.read_bytes() == source.read_bytes()
    assert not (
        tmp_path
        / "site/docs-viewer/runtime/js/reports/docs-viewer-management-reports.js"
    ).exists()
    assert not (tmp_path / "site/docs-viewer/static/css/docs-viewer-manage.css").exists()


def test_check_detects_drift_without_writing(tmp_path: Path) -> None:
    manifest_path = _create_test_repository(tmp_path)
    projections = site_code.load_manifest(tmp_path, manifest_path)
    site_code.apply_site_code_update(
        tmp_path,
        projections,
        site_code.plan_site_code_update(tmp_path, projections),
    )
    target = tmp_path / "site/docs-viewer/runtime/js/public/public.js"
    target.write_bytes(b"stale public bytes\n")

    exit_code = site_code.main(
        [
            "--check",
            "--repo-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ]
    )

    assert exit_code == 1
    assert target.read_bytes() == b"stale public bytes\n"


def test_write_removes_only_stale_files_in_owned_destinations(tmp_path: Path) -> None:
    manifest_path = _create_test_repository(tmp_path)
    projections = site_code.load_manifest(tmp_path, manifest_path)
    site_code.apply_site_code_update(
        tmp_path,
        projections,
        site_code.plan_site_code_update(tmp_path, projections),
    )
    stale = tmp_path / "site/docs-viewer/runtime/js/shared/retired.js"
    stale.write_bytes(b"retired\n")
    unrelated = tmp_path / "site/archive/assets/js/theme-toggle.js"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_bytes(b"unrelated\n")

    plan = site_code.plan_site_code_update(tmp_path, projections)
    assert plan.removed == ("site/docs-viewer/runtime/js/shared/retired.js",)

    site_code.apply_site_code_update(tmp_path, projections, plan)

    assert not stale.exists()
    assert unrelated.read_bytes() == b"unrelated\n"


def test_second_write_is_a_no_op(tmp_path: Path) -> None:
    manifest_path = _create_test_repository(tmp_path)
    projections = site_code.load_manifest(tmp_path, manifest_path)
    site_code.apply_site_code_update(
        tmp_path,
        projections,
        site_code.plan_site_code_update(tmp_path, projections),
    )

    plan = site_code.plan_site_code_update(tmp_path, projections)
    assert plan.drift_count == 0
    assert len(plan.unchanged) == 6

    site_code.apply_site_code_update(tmp_path, projections, plan)
    assert site_code.plan_site_code_update(tmp_path, projections).drift_count == 0


@pytest.mark.parametrize("relative", ["site/assets/js/unrelated.js", "site/archive/assets/js/theme-toggle.js"])
def test_apply_rejects_removal_outside_manifest_owned_destinations(
    tmp_path: Path,
    relative: str,
) -> None:
    manifest_path = _create_test_repository(tmp_path)
    projections = site_code.load_manifest(tmp_path, manifest_path)
    unrelated = tmp_path / relative
    unrelated.parent.mkdir(parents=True)
    unrelated.write_bytes(b"unrelated\n")
    plan = site_code.SiteCodeUpdatePlan(
        added=(),
        changed=(),
        removed=(relative,),
        unchanged=(),
    )

    with pytest.raises(site_code.SiteCodeUpdateError, match="planned removal"):
        site_code.apply_site_code_update(tmp_path, projections, plan)

    assert unrelated.read_bytes() == b"unrelated\n"


def test_manifest_rejects_private_runtime_assets(tmp_path: Path) -> None:
    manifest_path = _create_test_repository(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["projections"][2]["files"].append("docs-viewer-management-reports.js")
    payload["projections"][2]["files"].sort()
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(site_code.SiteCodeUpdateError, match="must list exactly"):
        site_code.load_manifest(tmp_path, manifest_path)


def test_projection_rejects_unsafe_destination_entry(tmp_path: Path) -> None:
    manifest_path = _create_test_repository(tmp_path)
    projections = site_code.load_manifest(tmp_path, manifest_path)
    destination = tmp_path / "site/docs-viewer/runtime/js/public"
    destination.mkdir(parents=True)
    (destination / "nested").mkdir()

    with pytest.raises(site_code.SiteCodeUpdateError, match="unsupported entry"):
        site_code.plan_site_code_update(tmp_path, projections)


def test_manifest_rejects_symlinked_source(tmp_path: Path) -> None:
    manifest_path = _create_test_repository(tmp_path)
    source = (
        tmp_path
        / "docs-viewer/runtime/js/reports/docs-viewer-public-reports.js"
    )
    source.unlink()
    source.symlink_to("docs-viewer-management-reports.js")

    with pytest.raises(site_code.SiteCodeUpdateError, match="symlink"):
        site_code.load_manifest(tmp_path, manifest_path)


def _create_test_repository(repo_root: Path) -> Path:
    sources = {
        "docs-viewer/runtime/js/public/public.js": b"public\n",
        "docs-viewer/runtime/js/shared/shared.js": b"shared\n",
        "docs-viewer/runtime/js/reports/docs-viewer-public-reports.js": b"reports\n",
        "docs-viewer/runtime/js/reports/docs-viewer-management-reports.js": b"private\n",
        "docs-viewer/static/css/docs-viewer-reports.css": b"reports css\n",
        "docs-viewer/static/css/docs-viewer-theme.css": b"theme css\n",
        "docs-viewer/static/css/docs-viewer.css": b"viewer css\n",
        "docs-viewer/static/css/docs-viewer-manage.css": b"private css\n",
    }
    for relative, content in sources.items():
        target = repo_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    manifest = {
        "schema_version": site_code.SCHEMA_VERSION,
        "projections": [
            {
                "id": "docs-viewer-public-js",
                "source_root": "docs-viewer/runtime/js/public",
                "destination_root": "site/docs-viewer/runtime/js/public",
                "files": ["public.js"],
            },
            {
                "id": "docs-viewer-shared-js",
                "source_root": "docs-viewer/runtime/js/shared",
                "destination_root": "site/docs-viewer/runtime/js/shared",
                "files": ["shared.js"],
            },
            {
                "id": "docs-viewer-public-report-js",
                "source_root": "docs-viewer/runtime/js/reports",
                "destination_root": "site/docs-viewer/runtime/js/reports",
                "files": ["docs-viewer-public-reports.js"],
            },
            {
                "id": "docs-viewer-shared-css",
                "source_root": "docs-viewer/static/css",
                "destination_root": "site/docs-viewer/static/css",
                "files": [
                    "docs-viewer-reports.css",
                    "docs-viewer-theme.css",
                    "docs-viewer.css",
                ],
            },
        ],
    }
    manifest_path = repo_root / "site-tools/config/site-code-update.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path
