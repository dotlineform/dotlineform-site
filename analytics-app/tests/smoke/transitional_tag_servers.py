"""Run the transitional Analytics shell against the Studio-owned tag API."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from threading import Thread


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server" / "analytics_app"
STUDIO_SERVER_DIR = REPO_ROOT / "studio" / "app" / "server" / "studio"
for path in (REPO_ROOT, ANALYTICS_SERVER_DIR, STUDIO_SERVER_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from analytics_app_server import AnalyticsAppServer  # noqa: E402
from studio_app_server import StudioAppServer  # noqa: E402


def start_transitional_tag_servers(
    repo_root: Path,
) -> tuple[StudioAppServer, AnalyticsAppServer, str, tuple[str | None, str | None]]:
    previous = (os.environ.get("STUDIO_APP_HOST"), os.environ.get("STUDIO_APP_PORT"))
    studio_server = StudioAppServer(("127.0.0.1", 0), repo_root)
    Thread(target=studio_server.serve_forever, daemon=True).start()
    os.environ["STUDIO_APP_HOST"] = "127.0.0.1"
    os.environ["STUDIO_APP_PORT"] = str(studio_server.server_address[1])
    analytics_server = AnalyticsAppServer(("127.0.0.1", 0), repo_root)
    Thread(target=analytics_server.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{analytics_server.server_address[1]}"
    return studio_server, analytics_server, base_url, previous


def stop_transitional_tag_servers(
    studio_server: StudioAppServer,
    analytics_server: AnalyticsAppServer,
    previous: tuple[str | None, str | None],
) -> None:
    analytics_server.shutdown()
    analytics_server.server_close()
    studio_server.shutdown()
    studio_server.server_close()
    for key, value in zip(("STUDIO_APP_HOST", "STUDIO_APP_PORT"), previous):
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
