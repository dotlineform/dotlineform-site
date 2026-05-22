#!/usr/bin/env python3
"""Serve the local vanilla Studio app shell."""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_PREFIXES = ("/assets/",)
STATIC_FILES = {
    "/favicon.ico",
    "/favicon-16x16.png",
    "/favicon-32x32.png",
    "/apple-touch-icon.png",
    "/safari-pinned-tab.svg",
    "/site.webmanifest",
}
STUDIO_VIEWS: dict[str, dict[str, str]] = {
    "tag_groups": {
        "label": "tag groups",
        "title": "Tag Groups",
        "path": "/studio/analytics/tag-groups/",
        "doc_href": "/docs/?scope=studio&doc=tag-groups",
        "script": "/assets/studio/js/tag-groups.js",
    },
}


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "assets" / "studio" / "js" / "studio-navigation.js",
        repo_root / "assets" / "studio" / "js" / "tag-groups.js",
        repo_root / "assets" / "studio" / "css" / "studio.css",
        repo_root / "assets" / "studio" / "data" / "studio_config.json",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def runtime_config(repo_root: Path, version: str) -> dict[str, object]:
    config_path = repo_root / "assets" / "studio" / "data" / "studio_config.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Studio config: {config_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Studio config must be a JSON object: {config_path}")

    payload.setdefault("app", {})
    app_config = payload["app"]
    if not isinstance(app_config, dict):
        app_config = {}
        payload["app"] = app_config
    app_config["runtime"] = {
        "host": "local-studio-app",
        "asset_version": version,
        "routes": {
            "health": "/health",
            "runtime_config": "/studio/runtime-config.json",
        },
        "views": [
            {"id": view_id, **view}
            for view_id, view in STUDIO_VIEWS.items()
        ],
        "navigation": {
            "primary": list(STUDIO_VIEWS.keys()),
        },
    }
    return payload


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


class StudioAppRequestHandler(BaseHTTPRequestHandler):
    server_version = "StudioAppServer/0.1"

    @property
    def repo_root(self) -> Path:
        return self.server.repo_root  # type: ignore[attr-defined]

    @property
    def version(self) -> str:
        return self.server.asset_version  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        path = unquote(urlsplit(self.path).path)
        if path == "/health":
            self.send_json({"status": "ok", "app": "studio"})
            return
        if path == "/studio/runtime-config.json":
            self.send_json(runtime_config(self.repo_root, self.version))
            return
        if path in {"/studio", "/studio/"}:
            self.send_html(studio_home_view(self.version))
            return
        if path in {"/studio/analytics/tag-groups", "/studio/analytics/tag-groups/"}:
            self.send_html(tag_groups_view(self.version))
            return
        if self.is_allowed_static_path(path):
            self.send_static(path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def is_allowed_static_path(self, path: str) -> bool:
        return path in STATIC_FILES or any(path.startswith(prefix) for prefix in STATIC_PREFIXES)

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html_text: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, request_path: str) -> None:
        relative = request_path.lstrip("/")
        if not relative or ".." in Path(relative).parts:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        path = (self.repo_root / relative).resolve()
        try:
            path.relative_to(self.repo_root)
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class StudioAppServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], repo_root: Path):
        super().__init__(server_address, StudioAppRequestHandler)
        self.repo_root = repo_root.resolve()
        self.asset_version = asset_version(self.repo_root)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    server = StudioAppServer((args.host, args.port), REPO_ROOT)
    host, port = server.server_address
    print(f"Studio app server: http://{host}:{port}/studio/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
