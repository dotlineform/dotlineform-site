"""Verify that the current field inventory covers each canonical record family."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402 - script bootstrap

ensure_studio_python_paths(__file__)

from catalogue.catalogue_field_registry import load_catalogue_field_registry  # noqa: E402
from catalogue.catalogue_source import WORK_FIELDS, SERIES_FIELDS, DETAIL_FIELDS, DETAIL_SECTION_FIELDS  # noqa: E402


def main() -> None:
    """Detect inventory drift without maintaining a second generation planner."""
    registry = load_catalogue_field_registry(REPO_ROOT)
    expected = {"work": WORK_FIELDS, "series": SERIES_FIELDS, "work_detail": DETAIL_FIELDS, "work_detail_section": DETAIL_SECTION_FIELDS}
    rules = {rule["record_family"]: rule for rule in registry["rules"]}
    if set(rules) != set(expected):
        raise ValueError("Catalogue registry families differ from the canonical model")
    for family, fields in expected.items():
        if set(rules[family]["fields"]) != set(fields):
            raise ValueError(f"Catalogue registry field mismatch: {family}")
        if not set(rules[family]["artifacts"]).issubset(registry["artifact_families"]):
            raise ValueError(f"Catalogue registry unknown artifact: {family}")
    print("Catalogue field inventory matches the canonical model.")


if __name__ == "__main__":
    main()
