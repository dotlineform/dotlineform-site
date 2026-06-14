"""HTML views for the local Studio app server."""

from __future__ import annotations

import html


def studio_theme_boot_script() -> str:
    return """<script>
    (function () {
      try {
        var theme = localStorage.getItem("theme");
        document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
      } catch (error) {
        document.documentElement.setAttribute("data-theme", "light");
      }
    })();
  </script>"""


def studio_app_bootstrap_view(version: str) -> str:
    escaped_version = html.escape(version, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>dotlineform Studio</title>
  {studio_theme_boot_script()}
  <link rel="stylesheet" href="/shared/frontend/css/search-list.css?v={escaped_version}">
  <link rel="stylesheet" href="/studio/app/assets/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  <div id="studioApp" data-studio-app-root="true"></div>
  <script type="module" src="/studio/app/frontend/js/studio-app.js?v={escaped_version}"></script>
</body>
</html>
"""
