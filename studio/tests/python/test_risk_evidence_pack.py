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
