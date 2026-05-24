"""UI Catalogue demo views for the local Studio app server."""

from __future__ import annotations

import html
import re
from pathlib import Path

try:
    from studio_app_config import STUDIO_VIEWS
    from studio_app_views import studio_header
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .studio_app_config import STUDIO_VIEWS
    from .studio_app_views import studio_header


UI_CATALOGUE_DEMO_SOURCES: dict[str, str] = {
    "ui_catalogue_demos": "studio/ui-catalogue/demos/index.md",
    "ui_catalogue_demo_button": "studio/ui-catalogue/demos/primitives/button/index.md",
    "ui_catalogue_demo_input": "studio/ui-catalogue/demos/primitives/input/index.md",
    "ui_catalogue_demo_list": "studio/ui-catalogue/demos/primitives/list/index.md",
    "ui_catalogue_demo_modal_shell": "studio/ui-catalogue/demos/primitives/modal-shell/index.md",
    "ui_catalogue_demo_panel": "studio/ui-catalogue/demos/primitives/panel/index.md",
    "ui_catalogue_demo_reopenable_command_result": "studio/ui-catalogue/demos/patterns/reopenable-command-result/index.md",
    "ui_catalogue_demo_column_links": "studio/ui-catalogue/demos/patterns/column-links/index.md",
}

UI_CATALOGUE_DEMO_ROUTES: dict[str, str] = {
    "/studio/ui-catalogue/demos/": "ui_catalogue_demos",
    "/studio/ui-catalogue/demos/primitives/button/": "ui_catalogue_demo_button",
    "/studio/ui-catalogue/demos/primitives/input/": "ui_catalogue_demo_input",
    "/studio/ui-catalogue/demos/primitives/list/": "ui_catalogue_demo_list",
    "/studio/ui-catalogue/demos/primitives/modal-shell/": "ui_catalogue_demo_modal_shell",
    "/studio/ui-catalogue/demos/primitives/panel/": "ui_catalogue_demo_panel",
    "/studio/ui-catalogue/demos/patterns/reopenable-command-result/": "ui_catalogue_demo_reopenable_command_result",
    "/studio/ui-catalogue/demos/patterns/column-links/": "ui_catalogue_demo_column_links",
}

CAPTURE_RE = re.compile(r"{%\s*capture\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%}(.*?){%\s*endcapture\s*%}", re.DOTALL)
FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
RELATIVE_URL_RE = re.compile(r"{{\s*'([^']+)'\s*\|\s*relative_url\s*}}")
ESCAPED_CAPTURE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*escape\s*}}")
RAW_CAPTURE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


def ui_catalogue_demo_view(version: str, repo_root: Path, view_id: str) -> str:
    view = STUDIO_VIEWS[view_id]
    escaped_version = html.escape(version, quote=True)
    title = html.escape(view["title"])
    doc_href = html.escape(view["doc_href"], quote=True)
    active_nav_id = view_id if view.get("nav", "true") != "false" else "ui_catalogue_demos"
    body = render_ui_catalogue_demo_body(repo_root, version, view_id)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>{title} | dotlineform Studio</title>
  <link rel="stylesheet" href="/assets/css/main.css?v={escaped_version}">
  <link rel="stylesheet" href="/assets/ui-catalogue/css/ui-catalogue-demo.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  {studio_header(active_nav_id)}
  <main class="container">
    <div class="studio">
      <div class="studio__headerRow">
        <h2>{title}</h2>
        <a
          class="studioLayout__docLink"
          href="{doc_href}"
          target="_blank"
          rel="noopener noreferrer"
          title="Open UI Catalogue implementation notes"
          aria-label="Open UI Catalogue implementation notes"
        >
          <em>i</em>
        </a>
      </div>
      <div class="studio__content">
        {body}
      </div>
    </div>
  </main>
  <script type="module" src="/studio/app/frontend/js/studio-navigation.js?v={escaped_version}"></script>
  <script type="module" src="/assets/ui-catalogue/js/ui-catalogue-demo.js?v={escaped_version}"></script>
</body>
</html>
"""


def render_ui_catalogue_demo_body(repo_root: Path, version: str, view_id: str) -> str:
    source = UI_CATALOGUE_DEMO_SOURCES.get(view_id)
    if not source:
        raise ValueError(f"Unknown UI Catalogue demo view: {view_id}")
    path = repo_root / source
    text = path.read_text(encoding="utf-8")
    body = FRONT_MATTER_RE.sub("", text, count=1)
    body = remove_local_shell_assets(body)

    captures: dict[str, str] = {}

    def store_capture(match: re.Match[str]) -> str:
        captures[match.group(1)] = match.group(2)
        return ""

    body = CAPTURE_RE.sub(store_capture, body)
    body = RELATIVE_URL_RE.sub(lambda match: match.group(1), body)
    body = body.replace("{{ site.time | date: '%s' }}", html.escape(version, quote=True))
    body = ESCAPED_CAPTURE_RE.sub(lambda match: html.escape(captures.get(match.group(1), "")), body)
    body = RAW_CAPTURE_RE.sub(lambda match: captures.get(match.group(1), ""), body)
    if "{{" in body or "{%" in body:
        raise ValueError(f"Unsupported Liquid token in UI Catalogue demo source: {source}")
    return body.strip()


def remove_local_shell_assets(body: str) -> str:
    lines = []
    for line in body.splitlines():
        if "<link" in line and "/assets/ui-catalogue/css/ui-catalogue-demo.css" in line:
            continue
        if "<script" in line and "/assets/ui-catalogue/js/ui-catalogue-demo.js" in line:
            continue
        lines.append(line)
    return "\n".join(lines)
