"""The temporary Catalogue pause exits before public-data reads and writes."""

from pathlib import Path

import pytest

import docs_catalogue_document_url_follow_through as follow_through


@pytest.mark.parametrize("operation", ["apply_projection", "refresh_from_current_public_state"])
def test_paused_refresh_does_not_load_or_apply_public_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    def unexpected_public_access(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Paused Catalogue refresh must exit before public-data access")

    for target in (
        "docs_catalogue_document_urls.load_public_catalogue_documents",
        "catalogue.catalogue_document_url_refresh.build_catalogue_document_url_refresh_plan",
        "catalogue.catalogue_document_url_refresh.apply_catalogue_document_url_refresh_plan",
    ):
        monkeypatch.setattr(target, unexpected_public_access)

    missing_repo = tmp_path / "not-created"
    result = (
        follow_through.apply_projection(missing_repo, {"work": {"00638": []}})
        if operation == "apply_projection"
        else follow_through.refresh_from_current_public_state(missing_repo)
    )

    assert result["status"] == "paused"
    assert result["stale"] is False
    assert result["affected_targets"] == []
    assert result["updated_paths"] == []
    assert result["error"] == ""
    assert not missing_repo.exists()
