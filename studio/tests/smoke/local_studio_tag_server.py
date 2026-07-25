"""Run the Studio shell and Studio-owned tag API for tag workflow smokes."""

from __future__ import annotations

import sys
from pathlib import Path
from threading import Thread


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVER_DIR = REPO_ROOT / "studio" / "app" / "server" / "studio"
for path in (REPO_ROOT, STUDIO_SERVER_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from studio_app_server import StudioAppServer  # noqa: E402


def start_studio_tag_server(repo_root: Path) -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), repo_root)
    Thread(target=server.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    return server, base_url


def stop_studio_tag_server(server: StudioAppServer) -> None:
    server.shutdown()
    server.server_close()
