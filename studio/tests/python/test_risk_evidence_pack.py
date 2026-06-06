from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_DIR = REPO_ROOT / "studio"
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

from checks import risk_evidence_pack as risk_pack  # noqa: E402


def test_collect_static_metrics_counts_selected_app_roots(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs-viewer"
    docs_root.mkdir()
    (docs_root / "runtime.js").write_text("import x from './x.js';\nexport const ok = true;\n", encoding="utf-8")
    (docs_root / "notes.md").write_text("# Notes\n\nBody\n", encoding="utf-8")
    ignored = tmp_path / "analytics-app"
    ignored.mkdir()
    (ignored / "analytics.py").write_text("print('skip')\n", encoding="utf-8")

    metrics = risk_pack.collect_static_metrics("docs-viewer", tmp_path)

    assert metrics["roots"] == ["docs-viewer"]
    assert metrics["totals"]["files"] == 2
    assert metrics["totals"]["lines"] == 5
    assert metrics["by_extension"] == {".js": 1, ".md": 1}


def test_collect_static_metrics_excludes_generated_and_canonical_data(tmp_path: Path) -> None:
    docs_generated = tmp_path / "docs-viewer" / "generated" / "docs" / "studio"
    docs_generated.mkdir(parents=True)
    (docs_generated / "index.json").write_text("[1]\n[2]\n", encoding="utf-8")
    studio_generated = tmp_path / "studio" / "workflows" / "change-requests" / "generated"
    studio_generated.mkdir(parents=True)
    (studio_generated / "search-index.json").write_text("[1]\n[2]\n", encoding="utf-8")
    studio_canonical = tmp_path / "studio" / "data" / "canonical" / "catalogue"
    studio_canonical.mkdir(parents=True)
    (studio_canonical / "works.json").write_text("[1]\n[2]\n", encoding="utf-8")
    source_root = tmp_path / "studio" / "checks"
    source_root.mkdir(parents=True)
    (source_root / "risk.py").write_text("print('count')\n", encoding="utf-8")

    metrics = risk_pack.collect_static_metrics("all", tmp_path)

    assert metrics["totals"]["files"] == 1
    assert metrics["totals"]["lines"] == 1
    assert metrics["largest_files"] == [{"path": "studio/checks/risk.py", "lines": 1, "bytes": 15}]


def test_import_export_scan_reports_js_dependency_counts(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs-viewer"
    docs_root.mkdir()
    (docs_root / "runtime.js").write_text(
        "import thing from './thing.js';\n"
        "import('../studio/example.js');\n"
        "export const ok = true;\n",
        encoding="utf-8",
    )

    scan = risk_pack.import_export_scan("docs-viewer", tmp_path)

    assert scan["totals"]["files"] == 1
    assert scan["totals"]["imports"] == 2
    assert scan["totals"]["exports"] == 1
    assert scan["totals"]["cross_app_references"] == 1


def test_static_searches_include_negative_test_assertion_inventory(tmp_path: Path) -> None:
    test_root = tmp_path / "studio" / "tests" / "python"
    test_root.mkdir(parents=True)
    (test_root / "test_contract.py").write_text(
        "def test_contract():\n"
        "    assert 'old_field' not in payload\n",
        encoding="utf-8",
    )
    source_root = tmp_path / "studio" / "services"
    source_root.mkdir(parents=True)
    (source_root / "service.py").write_text("assert 'old_field' not in payload\n", encoding="utf-8")

    searches = risk_pack.collect_static_searches("studio", tmp_path)
    patterns = {item["name"]: item for item in searches["patterns"]}
    inventory = patterns["negative_test_assertion_inventory"]

    assert inventory["include_prefixes"] == ["docs-viewer/tests/", "studio/tests/"]
    assert inventory["match_count"] == 1
    assert inventory["matches"][0]["path"] == "studio/tests/python/test_contract.py"


def test_collect_generated_payloads_summarizes_json_shapes(tmp_path: Path) -> None:
    generated_root = tmp_path / "assets" / "data"
    generated_root.mkdir(parents=True)
    (generated_root / "index.json").write_text(json.dumps({"items": [1, 2]}), encoding="utf-8")
    (generated_root / "list.json").write_text(json.dumps([{"id": "a"}]), encoding="utf-8")

    payloads = risk_pack.collect_generated_payloads("public-site", tmp_path)

    assert payloads["totals"]["files"] == 2
    shapes = {item["path"]: item["top_level_type"] for item in payloads["largest_payloads"]}
    assert shapes["assets/data/index.json"] == "object"
    assert shapes["assets/data/list.json"] == "array"


def test_collect_script_family_inventory_groups_active_python_ruby_roots(tmp_path: Path) -> None:
    catalogue_root = tmp_path / "studio" / "services" / "catalogue"
    catalogue_root.mkdir(parents=True)
    (catalogue_root / "catalogue_write_server.py").write_text("print('one')\nprint('two')\n", encoding="utf-8")
    docs_root = tmp_path / "docs-viewer" / "build"
    docs_root.mkdir(parents=True)
    (docs_root / "public_preview_helper.rb").write_text("puts 'docs'\n", encoding="utf-8")
    test_root = tmp_path / "docs-viewer" / "tests"
    test_root.mkdir(parents=True)
    (test_root / "test_docs.py").write_text("print('skip')\n", encoding="utf-8")

    inventory = risk_pack.collect_script_family_inventory(tmp_path)

    assert inventory["totals"] == {"files": 2, "lines": 3, "python": 1, "ruby": 1}
    families = {item["family"]: item for item in inventory["by_family"]}
    assert families["studio/services/catalogue"]["files"] == 1
    assert families["docs-viewer"]["ruby"] == 1
    assert "docs-viewer/tests/test_docs.py" not in {item["path"] for item in inventory["largest_files"]}


def test_runtime_lighthouse_hook_is_deferred_without_marking_passed() -> None:
    args = Namespace(
        app="docs-viewer",
        include_runtime=False,
        include_lighthouse=True,
        runtime_profile=[],
    )

    commands, runtime = risk_pack.collect_runtime_checks(args, "unit-test")

    assert commands == []
    assert runtime["status"] == "deferred"
    assert runtime["lighthouse"]["status"] == "deferred"
