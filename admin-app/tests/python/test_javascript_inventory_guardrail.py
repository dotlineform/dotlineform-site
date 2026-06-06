from __future__ import annotations

import collections
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_APP_DIR = REPO_ROOT / "admin-app"
if str(ADMIN_APP_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_APP_DIR))

from checks import javascript_inventory_guardrail as guardrail  # noqa: E402


def make_row(
    path: str,
    family: str,
    maintenance: int,
    structural: int,
    performance: int,
    architectural: int,
    risk: int,
    lines: int,
) -> guardrail.InventoryRow:
    return guardrail.InventoryRow(
        rank=1,
        path=path,
        family=family,
        maintenance=maintenance,
        structural=structural,
        performance=performance,
        architectural=architectural,
        risk=risk,
        focus="test focus",
        lines=lines,
    )


def test_summarize_counts_maintenance_risk_concentration() -> None:
    rows = [
        make_row("assets/a.js", "Alpha", 2, 2, 1, 1, 6, 100),
        make_row("assets/b.js", "Alpha", 2, 1, 1, 1, 5, 50),
        make_row("assets/c.js", "Beta", 1, 1, 1, 1, 4, 25),
    ]
    touches = collections.Counter({"assets/a.js": 4, "assets/b.js": 1})

    summary = guardrail.summarize(rows, touches, top_limit=2)

    assert summary["totals"] == {
        "files": 3,
        "lines": 175,
        "maintenance_2_files": 2,
        "maintenance_2_lines": 150,
        "maintenance_2_file_percent": 66.7,
        "maintenance_2_line_percent": 85.7,
        "maintenance_2_overlap_files": 1,
    }
    assert summary["files_by_maintenance"] == {1: 1, 2: 2}
    assert summary["lines_by_maintenance"] == {1: 25, 2: 150}
    assert summary["maintenance_2_by_family"] == [
        {"family": "Alpha", "files": 2, "lines": 150, "touches": 5}
    ]
    assert [item["path"] for item in summary["maintenance_2_overlap_files"]] == ["assets/a.js"]
    assert [item["path"] for item in summary["top_maintenance_risk_files"]] == ["assets/a.js", "assets/b.js"]


def test_parse_inventory_table_allows_zero_category_scores() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "assets" / "example.js"
        source.parent.mkdir(parents=True)
        source.write_text("export const ok = true;\n", encoding="utf-8")
        inventory = root / "inventory.md"
        inventory.write_text(
            "| Rank | File | Family | Maint. | Struct. | Perf. | Arch. | Risk | Focus |\n"
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |\n"
            "| 1 | `assets/example.js` | Example | 1 | 0 | 0 | 1 | 2 | Isolated helper. |\n",
            encoding="utf-8",
        )

        rows = guardrail.parse_inventory_table(inventory, root)

    assert len(rows) == 1
    assert rows[0].risk == 2
    assert rows[0].structural == 0
    assert rows[0].performance == 0
