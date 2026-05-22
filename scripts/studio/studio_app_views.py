"""HTML views for the local Studio app server."""

from __future__ import annotations

import html
from pathlib import Path

try:
    from studio_app_config import STUDIO_VIEWS
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .studio_app_config import STUDIO_VIEWS


def studio_nav(active_view_id: str = "") -> str:
    items = []
    for view_id, view in STUDIO_VIEWS.items():
        label = html.escape(view["label"])
        href = html.escape(view["path"], quote=True)
        escaped_view_id = html.escape(view_id, quote=True)
        active_class = " is-active" if view_id == active_view_id else ""
        items.append(f'<a class="nav-item{active_class}" href="{href}" data-studio-navigate="{escaped_view_id}">{label}</a>')
    return "\n        ".join(items)


def tag_groups_view(version: str) -> str:
    view = STUDIO_VIEWS["tag_groups"]
    escaped_version = html.escape(version, quote=True)
    title = html.escape(view["title"])
    doc_href = html.escape(view["doc_href"], quote=True)
    script = html.escape(view["script"], quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>{title} | dotlineform Studio</title>
  <link rel="stylesheet" href="/assets/css/main.css?v={escaped_version}">
  <link rel="stylesheet" href="/assets/studio/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  <header class="site-header">
    <div class="container">
      <div class="site-title"><a href="/studio/">dotlineform Studio</a></div>
      <nav class="site-nav" aria-label="Studio">
        {studio_nav("tag_groups")}
      </nav>
    </div>
  </header>
  <main class="container">
    <div class="studio">
      <div class="studio__headerRow">
        <h2>{title}</h2>
        <a
          class="studioLayout__docLink"
          href="{doc_href}"
          target="_blank"
          rel="noopener noreferrer"
          title="Open Studio page implementation notes"
          aria-label="Open Studio page implementation notes"
        >
          <em>i</em>
        </a>
      </div>
      <div class="studio__content">
        <div class="tagStudioPage tagGroupsPage">
          <div id="tag-groups" data-role="tag-groups" data-studio-ready="false" data-studio-busy="false">
            <div class="tagStudio__panel">
              <div data-role="content"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
  <script type="module" src="/assets/studio/js/studio-navigation.js?v={escaped_version}"></script>
  <script type="module" src="{script}?v={escaped_version}"></script>
</body>
</html>
"""


def docs_viewer_shell(version: str, repo_root: Path) -> str:
    template_path = repo_root / "_includes" / "docs_viewer_shell.html"
    text = template_path.read_text(encoding="utf-8")
    lines = []
    active_stack = [True]
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("{%- assign "):
            continue
        if stripped == "{%- if include.allow_management -%}":
            active_stack.append(active_stack[-1])
            continue
        if stripped == "{%- if include.allow_scope_query -%}":
            active_stack.append(active_stack[-1])
            continue
        if stripped == "{%- unless include.enable_search == false -%}":
            active_stack.append(active_stack[-1])
            continue
        if stripped == "{%- if include.allow_scope_query and include.enable_search == false -%}":
            active_stack.append(False)
            continue
        if stripped in {"{%- endif -%}", "{%- endunless -%}"}:
            active_stack.pop()
            continue
        if active_stack[-1]:
            lines.append(raw_line)

    shell = "\n".join(lines)
    replacements = {
        "{{ '/assets/docs-viewer/css/docs-viewer.css' | relative_url }}": "/assets/docs-viewer/css/docs-viewer.css",
        "{{ '/assets/docs-viewer/css/docs-viewer-reports.css' | relative_url }}": "/assets/docs-viewer/css/docs-viewer-reports.css",
        "{{ '/assets/docs-viewer/css/docs-viewer-management.css' | relative_url }}": "/assets/docs-viewer/css/docs-viewer-management.css",
        "{{ '/assets/docs-viewer/js/docs-viewer.js' | relative_url }}": "/assets/docs-viewer/js/docs-viewer.js",
        "{{ site.time | date: '%s' }}": html.escape(version, quote=True),
        "{{ include.index_url }}": "",
        "{{ include.viewer_base_url }}": "/docs/",
        "{{ include.viewer_scope | default: '' }}": "",
        "{{ include.include_scope_param | default: false }}": "true",
        "{{ include.allow_management | default: false }}": "true",
        "{{ include.allow_scope_query | default: false }}": "true",
        "{{ include.default_doc_id | default: '' }}": "",
        "{{ include.search_index_url | default: '' }}": "",
        "{{ docs_viewer_config_url | relative_url }}": "/assets/docs-viewer/data/docs-viewer-config.json",
        "{{ include.ui_text_url | default: '/assets/docs-viewer/data/ui-text.json' | relative_url }}": "/assets/docs-viewer/data/ui-text.json",
        "{{ include.report_registry_url | default: '/assets/data/docs/reports.json' | relative_url }}": "/assets/data/docs/reports.json",
        "{{ docs_viewer_generated_base_url }}": "/studio/api/docs",
        "{{ include.management_base_url | default: '' }}": "/studio/api/docs",
        "{{ include.search_aria_label | default: 'Search docs' }}": "Search Studio docs",
        "{{ include.search_placeholder | default: 'search docs' }}": "search studio docs",
    }
    for token, value in replacements.items():
        shell = shell.replace(token, value)
    return shell


def docs_viewer_manage_view(version: str, repo_root: Path) -> str:
    escaped_version = html.escape(version, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>Docs | dotlineform Studio</title>
  <link rel="stylesheet" href="/assets/css/main.css?v={escaped_version}">
  <link rel="stylesheet" href="/assets/studio/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  <header class="site-header">
    <div class="container">
      <div class="site-title"><a href="/studio/">dotlineform Studio</a></div>
      <nav class="site-nav" aria-label="Studio">
        {studio_nav("docs")}
      </nav>
    </div>
  </header>
  <main class="container studio-local-docs">
    {docs_viewer_shell(version, repo_root)}
  </main>
  <script type="module" src="/assets/studio/js/studio-navigation.js?v={escaped_version}"></script>
</body>
</html>
"""


def studio_home_view(version: str) -> str:
    escaped_version = html.escape(version, quote=True)
    links = "\n          ".join(
        '<li><a class="studioLinkList__item" href="{href}" data-studio-navigate="{view_id}">{label}</a></li>'.format(
            href=html.escape(view["path"], quote=True),
            view_id=html.escape(view_id, quote=True),
            label=html.escape(view["title"]),
        )
        for view_id, view in STUDIO_VIEWS.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>dotlineform Studio</title>
  <link rel="stylesheet" href="/assets/css/main.css?v={escaped_version}">
  <link rel="stylesheet" href="/assets/studio/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  <main class="container">
    <div class="studio">
      <div class="studio__headerRow"><h2>Studio</h2></div>
      <div class="studio__content">
        <ul class="studioLinkList">
          {links}
        </ul>
      </div>
    </div>
  </main>
  <script type="module" src="/assets/studio/js/studio-navigation.js?v={escaped_version}"></script>
</body>
</html>
"""
