#!/usr/bin/env python3
"""Focused atomic public Mermaid theme-pair producer checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from docs_artifact_locations import (  # noqa: E402
    ArtifactLocation,
    R2_PROVIDER,
    REPOSITORY_PROVIDER,
    artifact_location_adapter,
)
from docs_mermaid_accessibility import mermaid_accessibility_metadata  # noqa: E402
from docs_public_mermaid_producer import (  # noqa: E402
    DOCS_VIEWER_THEME_CSS_REL_PATH,
    PUBLIC_MERMAID_MANIFEST_IDENTITY,
    produce_public_mermaid_projection,
)
from docs_public_mermaid_projection import plan_public_mermaid_projection  # noqa: E402


DOC_ID = "d-20260624-000000-000010"
OTHER_DOC_ID = "d-20260624-000000-000011"
THEME_CSS_PATH = REPO_ROOT / DOCS_VIEWER_THEME_CSS_REL_PATH


class FakeR2Client:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def list_objects(self, prefix: str):
        return [
            SimpleNamespace(key=key, size=len(value), etag="")
            for key, value in self.objects.items()
            if key.startswith(prefix)
        ]

    def get_object(self, key: str) -> bytes:
        return self.objects[key]

    def head_object(self, key: str):
        value = self.objects.get(key)
        return None if value is None else SimpleNamespace(size=len(value), etag="")

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        assert content_type in {"image/svg+xml", "application/json", "application/octet-stream"}
        self.objects[key] = path.read_bytes()

    def delete_object(self, key: str) -> None:
        del self.objects[key]


def mermaid_source(
    title: str = "Projection flow",
    description: str = "Source becomes a verified public theme pair.",
    edge: str = "A --> B",
) -> str:
    return "\n".join(
        [
            "flowchart LR",
            f"  accTitle: {title}",
            f"  accDescr: {description}",
            f"  {edge}",
            "",
        ]
    )


def fenced(source: str) -> str:
    return f"```mermaid\n{source}```\n"


def projection_plan(
    documents: list[tuple[str, str]],
    *,
    previous_manifest: dict[str, object] | None = None,
) -> dict[str, object]:
    return plan_public_mermaid_projection(
        scope="library",
        documents=documents,
        public_url_prefix="/assets/data/docs/scopes/library",
        previous_manifest=previous_manifest,
    )


def write_toolchain(tmp_path: Path) -> Path:
    toolchain = tmp_path / "toolchain"
    executable = toolchain / "node_modules/.bin/mmdc"
    executable.parent.mkdir(parents=True)
    executable.write_text("fixture", encoding="utf-8")
    (toolchain / "mermaid-config.json").write_text("{}", encoding="utf-8")
    return toolchain


def fixture_renderer(
    calls: list[dict[str, object]],
    *,
    dark_view_box: str = "0 0 1200 800",
    fail_theme: str = "",
    unsafe_theme: str = "",
):
    def run(command: list[str], **options) -> subprocess.CompletedProcess[str]:
        assert options == {"capture_output": True, "text": True, "check": False}
        config_path = Path(command[command.index("--configFile") + 1])
        config = json.loads(config_path.read_text(encoding="utf-8"))
        theme = "dark" if config["themeVariables"]["darkMode"] else "light"
        source_path = Path(command[command.index("--input") + 1])
        source = source_path.read_text(encoding="utf-8")
        accessibility = mermaid_accessibility_metadata(source_path.name, source)
        calls.append(
            {
                "theme": theme,
                "config": config,
                "background": command[command.index("--backgroundColor") + 1],
            }
        )
        if theme == fail_theme:
            return subprocess.CompletedProcess(command, 1, "", f"{theme} render failed")
        output_path = Path(command[command.index("--output") + 1])
        view_box = dark_view_box if theme == "dark" else "0 0 1200 800"
        visible = (
            "<script>alert(1)</script>"
            if theme == unsafe_theme
            else f'<rect width="10" height="10" fill="{config["themeVariables"]["primaryColor"]}"/>'
        )
        output_path.write_text(
            f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}">
<title>{accessibility.title}</title>
<desc>{accessibility.description}</desc>
{visible}
</svg>""",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    return run


def filesystem_adapter(tmp_path: Path):
    return artifact_location_adapter(
        tmp_path,
        ArtifactLocation(REPOSITORY_PROVIDER, Path("prepared")),
    )


def test_producer_builds_explicit_pair_from_shared_semantic_theme_roles(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []
    plan = projection_plan([(DOC_ID, fenced(mermaid_source()))])
    prepared = filesystem_adapter(tmp_path)

    result = produce_public_mermaid_projection(
        plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=write_toolchain(tmp_path),
        run_command=fixture_renderer(calls),
    )

    variants = plan["diagrams"][0]["projection"]["variants"]
    light_identity = variants["light"]["artifact_identity"]
    dark_identity = variants["dark"]["artifact_identity"]
    manifest = json.loads(prepared.read(PUBLIC_MERMAID_MANIFEST_IDENTITY))
    assert result["summary"] == {
        "successful_diagram_count": 1,
        "published_variant_count": 2,
        "failure_count": 0,
        "removed_variant_count": 0,
    }
    assert prepared.stat(light_identity) is not None
    assert prepared.stat(dark_identity) is not None
    assert [call["theme"] for call in calls] == ["light", "dark"]
    assert calls[0]["background"] == "#fafafa"
    assert calls[1]["background"] == "#161618"
    for call in calls:
        config = call["config"]
        assert config["theme"] == "base"
        assert config["securityLevel"] == "strict"
        assert config["htmlLabels"] is False
        assert config["flowchart"]["htmlLabels"] is False
        assert config["themeVariables"]["fontFamily"] == (
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
        )
    assert calls[0]["config"]["themeVariables"]["primaryColor"] == "#f6f6f6"
    assert calls[1]["config"]["themeVariables"]["primaryColor"] == "#1c1c1f"
    assert manifest == result["manifest"]


def test_pair_geometry_failure_publishes_neither_variant(
    tmp_path: Path,
) -> None:
    plan = projection_plan([(DOC_ID, fenced(mermaid_source()))])
    prepared = filesystem_adapter(tmp_path)

    result = produce_public_mermaid_projection(
        plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=write_toolchain(tmp_path),
        run_command=fixture_renderer([], dark_view_box="0 0 400 100"),
    )

    variants = plan["diagrams"][0]["projection"]["variants"]
    assert result["summary"]["failure_count"] == 1
    assert "incompatible responsive geometry" in result["failures"][0]["message"]
    assert all(
        prepared.stat(variants[theme]["artifact_identity"]) is None
        for theme in ("light", "dark")
    )
    assert json.loads(prepared.read(PUBLIC_MERMAID_MANIFEST_IDENTITY))["diagrams"] == []


def test_sanitizer_failure_in_one_variant_publishes_neither_variant(
    tmp_path: Path,
) -> None:
    plan = projection_plan([(DOC_ID, fenced(mermaid_source()))])
    prepared = filesystem_adapter(tmp_path)

    result = produce_public_mermaid_projection(
        plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=write_toolchain(tmp_path),
        run_command=fixture_renderer([], unsafe_theme="dark"),
    )

    variants = plan["diagrams"][0]["projection"]["variants"]
    assert result["summary"]["failure_count"] == 1
    assert "contains no visible diagram content" in result["failures"][0]["message"]
    assert all(
        prepared.stat(variants[theme]["artifact_identity"]) is None
        for theme in ("light", "dark")
    )


def test_second_variant_failure_removes_manifest_owned_old_pair_without_partial_output(
    tmp_path: Path,
) -> None:
    prepared = filesystem_adapter(tmp_path)
    toolchain = write_toolchain(tmp_path)
    initial_plan = projection_plan([(DOC_ID, fenced(mermaid_source()))])
    initial_result = produce_public_mermaid_projection(
        initial_plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=toolchain,
        run_command=fixture_renderer([]),
    )
    changed_plan = projection_plan(
        [(DOC_ID, fenced(mermaid_source(edge="A --> C")))],
        previous_manifest=initial_result["manifest"],
    )

    failed_result = produce_public_mermaid_projection(
        changed_plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=toolchain,
        run_command=fixture_renderer([], fail_theme="dark"),
    )

    variants = changed_plan["diagrams"][0]["projection"]["variants"]
    assert failed_result["summary"] == {
        "successful_diagram_count": 0,
        "published_variant_count": 0,
        "failure_count": 1,
        "removed_variant_count": 2,
    }
    assert "dark render failed" in failed_result["failures"][0]["message"]
    assert all(
        prepared.stat(variants[theme]["artifact_identity"]) is None
        for theme in ("light", "dark")
    )
    assert json.loads(prepared.read(PUBLIC_MERMAID_MANIFEST_IDENTITY))["diagrams"] == []


def test_publication_failure_rolls_back_pair_and_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = filesystem_adapter(tmp_path)
    toolchain = write_toolchain(tmp_path)
    initial_plan = projection_plan([(DOC_ID, fenced(mermaid_source()))])
    initial_result = produce_public_mermaid_projection(
        initial_plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=toolchain,
        run_command=fixture_renderer([]),
    )
    changed_plan = projection_plan(
        [(DOC_ID, fenced(mermaid_source(edge="A --> C")))],
        previous_manifest=initial_result["manifest"],
    )
    variants = changed_plan["diagrams"][0]["projection"]["variants"]
    old_light = prepared.read(variants["light"]["artifact_identity"])
    old_dark = prepared.read(variants["dark"]["artifact_identity"])
    old_manifest = prepared.read(PUBLIC_MERMAID_MANIFEST_IDENTITY)
    original_replace = prepared.replace
    failed_once = False

    def fail_dark_once(identity, data, *, content_type=""):
        nonlocal failed_once
        if str(identity).endswith("/dark.svg") and not failed_once:
            failed_once = True
            raise RuntimeError("fixture publication failure")
        return original_replace(identity, data, content_type=content_type)

    monkeypatch.setattr(prepared, "replace", fail_dark_once)

    with pytest.raises(RuntimeError, match="rolled back"):
        produce_public_mermaid_projection(
            changed_plan,
            prepared=prepared,
            write=True,
            theme_css_path=THEME_CSS_PATH,
            toolchain_root=toolchain,
            run_command=fixture_renderer([]),
        )

    assert prepared.read(variants["light"]["artifact_identity"]) == old_light
    assert prepared.read(variants["dark"]["artifact_identity"]) == old_dark
    assert prepared.read(PUBLIC_MERMAID_MANIFEST_IDENTITY) == old_manifest


def test_stale_cleanup_removes_only_manifest_pairs_and_preserves_unowned_artifacts(
    tmp_path: Path,
) -> None:
    prepared = filesystem_adapter(tmp_path)
    toolchain = write_toolchain(tmp_path)
    initial_plan = projection_plan(
        [
            (DOC_ID, fenced(mermaid_source())),
            (OTHER_DOC_ID, fenced(mermaid_source("Other flow", "Another public diagram."))),
        ]
    )
    initial_result = produce_public_mermaid_projection(
        initial_plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=toolchain,
        run_command=fixture_renderer([]),
    )
    prepared.replace("authored.svg", b"authored", content_type="image/svg+xml")
    empty_plan = projection_plan([], previous_manifest=initial_result["manifest"])

    result = produce_public_mermaid_projection(
        empty_plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=tmp_path / "missing-toolchain",
        run_command=lambda *_args, **_kwargs: pytest.fail("renderer must not run"),
    )

    assert result["summary"]["removed_variant_count"] == 4
    assert prepared.read("authored.svg") == b"authored"
    assert json.loads(prepared.read(PUBLIC_MERMAID_MANIFEST_IDENTITY))["diagrams"] == []
    assert sorted(item.identity for item in prepared.list()) == [
        "authored.svg",
        PUBLIC_MERMAID_MANIFEST_IDENTITY,
    ]


def test_producer_rederives_ownership_and_rejects_tampered_plan(
    tmp_path: Path,
) -> None:
    prepared = filesystem_adapter(tmp_path)
    prepared.replace("authored.svg", b"authored", content_type="image/svg+xml")
    plan = projection_plan([(DOC_ID, fenced(mermaid_source()))])
    plan["diagrams"][0]["projection"]["variants"]["light"]["artifact_identity"] = "authored.svg"
    plan["manifest"]["diagrams"][0]["variants"]["light"]["artifact_identity"] = "authored.svg"

    with pytest.raises(ValueError, match="outside projection ownership"):
        produce_public_mermaid_projection(
            plan,
            prepared=prepared,
            write=True,
            theme_css_path=THEME_CSS_PATH,
            toolchain_root=write_toolchain(tmp_path),
            run_command=fixture_renderer([]),
        )

    assert prepared.read("authored.svg") == b"authored"
    assert prepared.stat(PUBLIC_MERMAID_MANIFEST_IDENTITY) is None


def test_provider_neutral_r2_write_verifies_pair_and_manifest(
    tmp_path: Path,
) -> None:
    client = FakeR2Client()
    prepared = artifact_location_adapter(
        tmp_path,
        ArtifactLocation(R2_PROVIDER, Path("prepared/library")),
        remote_client=client,
    )
    plan = projection_plan([(DOC_ID, fenced(mermaid_source()))])

    result = produce_public_mermaid_projection(
        plan,
        prepared=prepared,
        write=True,
        theme_css_path=THEME_CSS_PATH,
        toolchain_root=write_toolchain(tmp_path),
        run_command=fixture_renderer([]),
    )

    assert result["summary"]["published_variant_count"] == 2
    assert sorted(client.objects) == [
        "prepared/library/manifest.json",
        (
            "prepared/library/projection-assets/mermaid/"
            f"{DOC_ID}--mermaid-0001/dark.svg"
        ),
        (
            "prepared/library/projection-assets/mermaid/"
            f"{DOC_ID}--mermaid-0001/light.svg"
        ),
    ]
