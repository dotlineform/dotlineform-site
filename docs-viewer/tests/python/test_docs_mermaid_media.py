#!/usr/bin/env python3
"""Focused Mermaid media producer checks."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
for _path in (REPO_ROOT / "docs-viewer/build", REPO_ROOT / "docs-viewer/services"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


from docs_artifact_locations import (  # noqa: E402
    ArtifactLocation,
    ArtifactStat,
    R2_PROVIDER,
    REPOSITORY_PROVIDER,
    artifact_location_adapter,
)
from docs_builder.media_builds import REGISTERED_MEDIA_PRODUCERS, MediaBuildContext  # noqa: E402
from docs_mermaid_media import plan_mermaid_media, produce_mermaid_svg  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402


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
        assert content_type == "image/svg+xml"
        self.objects[key] = path.read_bytes()

    def delete_object(self, key: str) -> None:
        del self.objects[key]


def _context(
    tmp_path: Path,
    *,
    write: bool,
    requested_published_identities: tuple[str, ...] | None = None,
) -> MediaBuildContext:
    source_location = ArtifactLocation(REPOSITORY_PROVIDER, Path("source"))
    published_location = ArtifactLocation(REPOSITORY_PROVIDER, Path("published"))
    return MediaBuildContext(
        scope="studio",
        build_type="mermaid",
        publishes_to="svg",
        source=artifact_location_adapter(tmp_path, source_location),
        published=artifact_location_adapter(tmp_path, published_location),
        write=write,
        requested_published_identities=requested_published_identities,
    )


def _write_toolchain(tmp_path: Path) -> Path:
    toolchain = tmp_path / "toolchain"
    executable = toolchain / "node_modules/.bin/mmdc"
    executable.parent.mkdir(parents=True)
    executable.write_text("fixture", encoding="utf-8")
    (toolchain / "mermaid-config.json").write_text("{}", encoding="utf-8")
    return toolchain


def _write_source(tmp_path: Path, text: str | None = None) -> None:
    source = tmp_path / "source/architecture.mmd"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        text
        or """flowchart LR
    accTitle: Architecture flow
    accDescr: Source flows through the build into published media.
    A[Source] --> B[Published]
""",
        encoding="utf-8",
    )


def _valid_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800">
<title>Architecture flow</title>
<desc>Source flows through the build into published media.</desc>
<script>alert(1)</script>
<g><rect width="10" height="10"/></g>
</svg>"""


def test_mermaid_producer_is_registered() -> None:
    assert REGISTERED_MEDIA_PRODUCERS["mermaid"] is produce_mermaid_svg


def test_checked_studio_config_registers_and_materializes_mermaid_source() -> None:
    config = load_docs_scope_configs(REPO_ROOT)["studio"]
    build = config.source.build_media["mermaid"]

    assert build.path == Path("media/mermaid")
    assert build.producer == "mermaid"
    assert build.publishes_to == "svg"
    assert config.published.media["svg"].build_inputs == ("mermaid",)
    assert (REPO_ROOT / config.source.location.path / build.path).is_dir()


def test_dry_run_plans_sorted_same_basename_outputs_without_toolchain_or_writes(tmp_path: Path) -> None:
    context = _context(tmp_path, write=False)
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "zeta.mmd").write_text("not read during planning", encoding="utf-8")
    (source_root / "alpha.mmd").write_text("not read during planning", encoding="utf-8")
    (source_root / ".gitkeep").touch()

    assert produce_mermaid_svg(context, toolchain_root=tmp_path / "missing") == (
        "alpha.svg",
        "zeta.svg",
    )
    assert not (tmp_path / "published").exists()


def test_plan_preserves_confined_subdirectories_and_ignores_non_mermaid_files() -> None:
    plans = plan_mermaid_media(
        [
            ArtifactStat(identity="nested/diagram.mmd", size=10),
            ArtifactStat(identity="notes.txt", size=5),
        ]
    )

    assert [(item.source_identity, item.published_identity) for item in plans] == [
        ("nested/diagram.mmd", "nested/diagram.svg")
    ]


def test_requested_outputs_render_only_matching_mermaid_sources(tmp_path: Path) -> None:
    _write_source(tmp_path)
    other_source = tmp_path / "source/other.mmd"
    other_source.write_text(
        """flowchart LR
    accTitle: Other flow
    accDescr: Only this requested diagram is rendered.
    A --> B
""",
        encoding="utf-8",
    )
    rendered_inputs: list[str] = []

    def render(command: list[str], **_options) -> subprocess.CompletedProcess[str]:
        rendered_inputs.append(Path(command[command.index("--input") + 1]).name)
        output = Path(command[command.index("--output") + 1])
        output.write_text(_valid_svg(), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    outputs = produce_mermaid_svg(
        _context(
            tmp_path,
            write=True,
            requested_published_identities=("standalone.svg", "other.svg"),
        ),
        toolchain_root=_write_toolchain(tmp_path),
        run_command=render,
    )

    assert outputs == ("other.svg",)
    assert rendered_inputs == ["other.mmd"]
    assert (tmp_path / "published/other.svg").is_file()
    assert not (tmp_path / "published/architecture.svg").exists()


def test_write_invokes_local_cli_sanitizes_publishes_and_verifies(tmp_path: Path) -> None:
    _write_source(tmp_path)
    toolchain = _write_toolchain(tmp_path)
    calls: list[list[str]] = []
    remote_client = FakeR2Client()
    filesystem_context = _context(tmp_path, write=True)
    context = MediaBuildContext(
        scope="studio",
        build_type="mermaid",
        publishes_to="svg",
        source=filesystem_context.source,
        published=artifact_location_adapter(
            tmp_path,
            ArtifactLocation(R2_PROVIDER, Path("docs/studio/svg")),
            remote_client=remote_client,
        ),
        write=True,
    )

    def run_command(command: list[str], **options) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        assert options == {"capture_output": True, "text": True, "check": False}
        output = Path(command[command.index("--output") + 1])
        output.write_text(_valid_svg(), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    outputs = produce_mermaid_svg(
        context,
        toolchain_root=toolchain,
        run_command=run_command,
    )

    assert outputs == ("architecture.svg",)
    command = calls[0]
    assert command[0] == str(toolchain / "node_modules/.bin/mmdc")
    assert command[command.index("--configFile") + 1] == str(toolchain / "mermaid-config.json")
    assert command[command.index("--backgroundColor") + 1] == "white"
    assert command[command.index("--width") + 1] == "1200"
    assert command[command.index("--height") + 1] == "800"
    published = remote_client.objects["docs/studio/svg/architecture.svg"].decode("utf-8")
    assert "<script" not in published
    assert "viewBox=\"0 0 1200 800\"" in published
    assert "<title>Architecture flow</title>" in published
    assert "<desc>Source flows through the build into published media.</desc>" in published


def test_write_fails_explicitly_when_local_cli_is_not_installed(tmp_path: Path) -> None:
    _write_source(tmp_path)
    with pytest.raises(RuntimeError, match="Mermaid CLI is not installed"):
        produce_mermaid_svg(
            _context(tmp_path, write=True),
            toolchain_root=tmp_path / "missing",
        )


@pytest.mark.parametrize(
    ("source_text", "message"),
    [
        ("flowchart LR\nA --> B\n", "requires a non-empty accTitle"),
        ("flowchart LR\naccTitle: Flow\nA --> B\n", "requires a non-empty accDescr"),
    ],
)
def test_write_requires_accessible_mermaid_source(
    tmp_path: Path,
    source_text: str,
    message: str,
) -> None:
    _write_source(tmp_path, source_text)
    with pytest.raises(ValueError, match=message):
        produce_mermaid_svg(
            _context(tmp_path, write=True),
            toolchain_root=_write_toolchain(tmp_path),
            run_command=lambda *_args, **_kwargs: pytest.fail("renderer must not run"),
        )


def test_write_reports_renderer_failure_without_publishing(tmp_path: Path) -> None:
    _write_source(tmp_path)

    def failed(command: list[str], **_options) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, "", "Parse error on line 2")

    with pytest.raises(RuntimeError, match="renderer failed.*Parse error on line 2"):
        produce_mermaid_svg(
            _context(tmp_path, write=True),
            toolchain_root=_write_toolchain(tmp_path),
            run_command=failed,
        )
    assert not (tmp_path / "published").exists()


def test_write_rejects_sanitized_output_that_loses_diagram_content(tmp_path: Path) -> None:
    _write_source(tmp_path)

    def unsafe_only(command: list[str], **_options) -> subprocess.CompletedProcess[str]:
        output = Path(command[command.index("--output") + 1])
        output.write_text(
            """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800">
<title>Architecture flow</title><desc>Description</desc><foreignObject>removed</foreignObject></svg>""",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    with pytest.raises(RuntimeError, match="contains no visible diagram content"):
        produce_mermaid_svg(
            _context(tmp_path, write=True),
            toolchain_root=_write_toolchain(tmp_path),
            run_command=unsafe_only,
        )
    assert not (tmp_path / "published").exists()


def test_write_reports_failed_publication_verification(tmp_path: Path, monkeypatch) -> None:
    _write_source(tmp_path)
    context = _context(tmp_path, write=True)
    monkeypatch.setattr(context.published, "verify_bytes", lambda *_args, **_kwargs: False)

    def render(command: list[str], **_options) -> subprocess.CompletedProcess[str]:
        output = Path(command[command.index("--output") + 1])
        output.write_text(_valid_svg(), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    with pytest.raises(RuntimeError, match="publication verification failed"):
        produce_mermaid_svg(
            context,
            toolchain_root=_write_toolchain(tmp_path),
            run_command=render,
        )
