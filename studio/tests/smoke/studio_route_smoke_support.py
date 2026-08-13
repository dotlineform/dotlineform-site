"""Small server harness for retained Studio route-boundary smokes."""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_studio_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def start_public_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    root = site_root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"site root does not exist: {root}")
    handler = partial(QuietStaticHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def wait_for_studio_route(page, root_selector: str, timeout_ms: int) -> None:
    wait_for_route_ready(
        page,
        root_selector,
        "data-studio-ready",
        "data-studio-busy",
        timeout_ms,
    )
