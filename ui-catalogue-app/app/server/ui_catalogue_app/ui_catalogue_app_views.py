"""HTML views for the standalone UI Catalogue app."""

from __future__ import annotations

import html
import re
from pathlib import Path

try:
    from ui_catalogue_app_config import ui_catalogue_demo_views
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .ui_catalogue_app_config import ui_catalogue_demo_views


UI_CATALOGUE_DEMO_ROUTES: dict[str, str] = {
    "/ui-catalogue/demos/": "ui_catalogue_demos",
    "/ui-catalogue/demos/primitives/button/": "ui_catalogue_demo_button",
    "/ui-catalogue/demos/primitives/input/": "ui_catalogue_demo_input",
    "/ui-catalogue/demos/primitives/list/": "ui_catalogue_demo_list",
    "/ui-catalogue/demos/primitives/modal-shell/": "ui_catalogue_demo_modal_shell",
    "/ui-catalogue/demos/primitives/panel/": "ui_catalogue_demo_panel",
    "/ui-catalogue/demos/patterns/action-menu/": "ui_catalogue_demo_action_menu",
    "/ui-catalogue/demos/patterns/reopenable-command-result/": "ui_catalogue_demo_reopenable_command_result",
    "/ui-catalogue/demos/patterns/select-menu/": "ui_catalogue_demo_select_menu",
    "/ui-catalogue/demos/patterns/column-links/": "ui_catalogue_demo_column_links",
}

CAPTURE_RE = re.compile(r"{%\s*capture\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%}(.*?){%\s*endcapture\s*%}", re.DOTALL)
FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
RELATIVE_URL_RE = re.compile(r"{{\s*'([^']+)'\s*\|\s*relative_url\s*}}")
ESCAPED_CAPTURE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*escape\s*}}")
RAW_CAPTURE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


def ui_catalogue_demo_view(version: str, repo_root: Path, view_id: str) -> str:
    view = ui_catalogue_demo_views(repo_root)[view_id]
    escaped_version = html.escape(version, quote=True)
    title = html.escape(view["title"])
    body = render_ui_catalogue_demo_body(repo_root, version, view_id)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <title>{title} | dotlineform UI Catalogue</title>
  {ui_catalogue_theme_boot_script()}
  <link rel="stylesheet" href="/ui-catalogue/app/assets/css/ui-catalogue-shell.css?v={escaped_version}">
  <link rel="stylesheet" href="/ui-catalogue/app/assets/css/ui-catalogue-demo.css?v={escaped_version}">
</head>
<body class="uiCatalogueApp">
  {ui_catalogue_header()}
  <main class="uiCatalogueShellMain">
    <div class="uiCatalogueShellHeading">
      <h2>{title}</h2>
    </div>
    <div class="uiCatalogueShellContent">
      {body}
    </div>
  </main>
  <script type="module" src="/ui-catalogue/app/assets/js/ui-catalogue-shell.js?v={escaped_version}"></script>
  <script type="module" src="/ui-catalogue/app/assets/js/ui-catalogue-demo.js?v={escaped_version}"></script>
</body>
</html>
"""


def ui_catalogue_header() -> str:
    return """<header class="uiCatalogueShellHeader">
    <div class="uiCatalogueShellHeader__inner">
      <div class="uiCatalogueShellTitle"><a href="/ui-catalogue/demos/">dotlineform UI catalogue</a></div>
      <div class="uiCatalogueShellHeader__actions">
        <nav class="uiCatalogueShellNav" aria-label="UI Catalogue">
          <a class="uiCatalogueShellNav__item" href="/ui-catalogue/demos/">demos</a>
        </nav>
        <button class="uiCatalogueThemeToggle" type="button" data-ui-catalogue-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
          <svg class="uiCatalogueThemeToggle__icon" data-ui-catalogue-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="4"></circle>
            <path d="M12 2v2"></path>
            <path d="M12 20v2"></path>
            <path d="M4.93 4.93l1.41 1.41"></path>
            <path d="M17.66 17.66l1.41 1.41"></path>
            <path d="M2 12h2"></path>
            <path d="M20 12h2"></path>
            <path d="M4.93 19.07l1.41-1.41"></path>
            <path d="M17.66 6.34l1.41-1.41"></path>
          </svg>
          <svg class="uiCatalogueThemeToggle__icon" data-ui-catalogue-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden>
            <path d="M21 12.79A8.5 8.5 0 1 1 11.21 3 6.5 6.5 0 0 0 21 12.79z"></path>
          </svg>
        </button>
      </div>
    </div>
  </header>"""


def ui_catalogue_theme_boot_script() -> str:
    return """<script>
    (function () {
      try {
        var theme = window.localStorage ? window.localStorage.getItem('theme') : '';
        if (theme === 'dark' || theme === 'light') {
          document.documentElement.setAttribute('data-theme', theme);
        }
      } catch (_error) {}
    })();
  </script>"""


def render_ui_catalogue_demo_body(repo_root: Path, version: str, view_id: str) -> str:
    view = ui_catalogue_demo_views(repo_root).get(view_id)
    if not view:
        raise ValueError(f"Unknown UI Catalogue demo view: {view_id}")
    path = repo_root / view["source"]
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
        raise ValueError(f"Unsupported Liquid token in UI Catalogue demo source: {view['source']}")
    return body.strip()


def remove_local_shell_assets(body: str) -> str:
    lines = []
    for line in body.splitlines():
        if "<link" in line and "/ui-catalogue/app/assets/css/ui-catalogue-demo.css" in line:
            continue
        if "<script" in line and "/ui-catalogue/app/assets/js/ui-catalogue-demo.js" in line:
            continue
        lines.append(line)
    return "\n".join(lines)
