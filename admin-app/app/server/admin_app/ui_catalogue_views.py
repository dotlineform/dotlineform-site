"""HTML views for Admin-hosted UI Catalogue routes."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

try:
    from admin_app_views import admin_header, admin_theme_boot_script
    from ui_catalogue_config import ui_catalogue_demo_views
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .admin_app_views import admin_header, admin_theme_boot_script
    from .ui_catalogue_config import ui_catalogue_demo_views


UI_CATALOGUE_DEMO_ROUTES: dict[str, str] = {
    "/admin/ui-catalogue/demos/": "ui_catalogue_demos",
    "/admin/ui-catalogue/demos/primitives/button/": "ui_catalogue_demo_button",
    "/admin/ui-catalogue/demos/primitives/input/": "ui_catalogue_demo_input",
    "/admin/ui-catalogue/demos/primitives/list/": "ui_catalogue_demo_list",
    "/admin/ui-catalogue/demos/primitives/modal-shell/": "ui_catalogue_demo_modal_shell",
    "/admin/ui-catalogue/demos/primitives/panel/": "ui_catalogue_demo_panel",
    "/admin/ui-catalogue/demos/patterns/action-menu/": "ui_catalogue_demo_action_menu",
    "/admin/ui-catalogue/demos/patterns/reopenable-command-result/": "ui_catalogue_demo_reopenable_command_result",
    "/admin/ui-catalogue/demos/patterns/select-menu/": "ui_catalogue_demo_select_menu",
    "/admin/ui-catalogue/demos/patterns/column-links/": "ui_catalogue_demo_column_links",
}

PALETTE_DATA_RELATIVE_PATH = Path("admin-app/ui-catalogue/source/palette/palette.yml")
CAPTURE_RE = re.compile(r"{%\s*capture\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%}(.*?){%\s*endcapture\s*%}", re.DOTALL)
FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
RELATIVE_URL_RE = re.compile(r"{{\s*'([^']+)'\s*\|\s*relative_url\s*}}")
ESCAPED_CAPTURE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*escape\s*}}")
RAW_CAPTURE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")
HEX_COLOR_RE = re.compile(r"\A#[0-9a-fA-F]{3,8}\Z")


def ui_catalogue_demo_view(version: str, repo_root: Path, view_id: str) -> str:
    view = ui_catalogue_demo_views(repo_root)[view_id]
    body = render_ui_catalogue_demo_body(repo_root, version, view_id)
    return ui_catalogue_shell(version, view["title"], body)


def ui_catalogue_palette_view(version: str, repo_root: Path) -> str:
    items = load_palette_items(repo_root)
    body = render_palette_body(items)
    return ui_catalogue_shell(version, "Palette", body)


def ui_catalogue_shell(version: str, page_title: str, body: str) -> str:
    escaped_version = html.escape(version, quote=True)
    title = html.escape(page_title)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <title>{title} | dotlineform UI Catalogue</title>
  {admin_theme_boot_script()}
  <link rel="stylesheet" href="/admin/app/assets/css/admin.css?v={escaped_version}">
  <link rel="stylesheet" href="/admin/ui-catalogue/assets/css/ui-catalogue-shell.css?v={escaped_version}">
  <link rel="stylesheet" href="/admin/ui-catalogue/assets/css/ui-catalogue-demo.css?v={escaped_version}">
</head>
<body class="adminApp uiCatalogueApp">
  <div class="adminShell">
    {admin_header()}
    <main class="adminMain uiCatalogueShellMain">
      <div class="uiCatalogueShellHeading">
        <h2>{title}</h2>
      </div>
      <div class="uiCatalogueShellContent">
        {body}
      </div>
    </main>
  </div>
  <script type="module" src="/admin/app/frontend/js/admin-theme.js?v={escaped_version}"></script>
  <script type="module" src="/admin/ui-catalogue/assets/js/ui-catalogue-demo.js?v={escaped_version}"></script>
</body>
</html>
"""


def parse_palette_scalar(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return ""
    if value[0:1] in {'"', "'"}:
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, str) else str(parsed)
        except json.JSONDecodeError:
            return value.strip("\"'")
    return value


def load_palette_items(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / PALETTE_DATA_RELATIVE_PATH
    if not path.exists():
        return []

    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped == "items:":
            continue
        if stripped == "-":
            current = {}
            items.append(current)
            continue
        if current is None or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        current[key.strip()] = parse_palette_scalar(raw_value)
    return items


def safe_palette_color(value: str) -> str:
    return value if HEX_COLOR_RE.fullmatch(value.strip()) else "transparent"


def render_palette_body(items: list[dict[str, str]]) -> str:
    rows = []
    for item in items:
        identifier = html.escape(item.get("id", ""))
        usage = html.escape(item.get("usage", ""))
        light_hex = html.escape(item.get("light_hex", ""))
        dark_hex = html.escape(item.get("dark_hex", ""))
        light_color = html.escape(safe_palette_color(item.get("light_hex", "")), quote=True)
        dark_color = html.escape(safe_palette_color(item.get("dark_hex", "")), quote=True)
        rows.append(
            f"""<tr>
          <td class="uiCataloguePalette__id">{identifier}</td>
          <td>{usage}</td>
          <td class="uiCataloguePalette__hex">{light_hex}</td>
          <td><span class="uiCataloguePalette__swatch" style="background:{light_color};"></span></td>
          <td class="uiCataloguePalette__hex">{dark_hex}</td>
          <td><span class="uiCataloguePalette__swatch" style="background:{dark_color};"></span></td>
        </tr>"""
        )
    table_body = "\n        ".join(rows)
    if table_body:
        content = f"""<table class="uiCataloguePalette__table">
      <thead>
        <tr>
          <th>Identifier</th>
          <th>Usage</th>
          <th>Light Hex</th>
          <th>Light Swatch</th>
          <th>Dark Hex</th>
          <th>Dark Swatch</th>
        </tr>
      </thead>
      <tbody>
        {table_body}
      </tbody>
    </table>"""
    else:
        content = """<p class="uiCataloguePalette__note">No palette data found. Run <code>$HOME/miniconda3/bin/python3 studio/services/media/build_palette_data.py --write</code>.</p>"""
    return f"""<div class="uiCatalogueDemoRoot uiCataloguePalette" id="uiCataloguePaletteRoot">
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCataloguePaletteHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow">Reference</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCataloguePaletteHeading">Public CSS palette</h3>
      <p class="uiCatalogueDemoIntro">Generated from <code>assets/css/main.css</code>. The checked-in palette data is owned by UI Catalogue at <code>admin-app/ui-catalogue/source/palette/palette.yml</code>.</p>
    </div>
  </section>

  <section class="uiCataloguePalette__guide" aria-labelledby="uiCataloguePaletteGuideHeading">
    <h3 class="uiCatalogueDemoHeading" id="uiCataloguePaletteGuideHeading">How identifier and usage are derived</h3>
    <ul>
      <li><code>identifier</code>: CSS variable name for token colors or <code>direct #hex</code> for non-token literals.</li>
      <li><code>usage</code>: selectors where <code>var(--token)</code> is referenced, or selectors where the direct hex appears.</li>
      <li>Selector lists are truncated for readability when there are many matches.</li>
    </ul>
  </section>

  {content}
</div>"""


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
        if "<link" in line and "/admin/ui-catalogue/assets/css/ui-catalogue-demo.css" in line:
            continue
        if "<script" in line and "/admin/ui-catalogue/assets/js/ui-catalogue-demo.js" in line:
            continue
        lines.append(line)
    return "\n".join(lines)
