from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_CONFIG_PATH = Path("docs-viewer/config/routes/docs-viewer-routes.json")
RECENT_BASES = {"added", "edited"}


def recent_route_policies(repo_root: Path) -> list[dict[str, str]]:
    payload = json.loads((repo_root / ROUTE_CONFIG_PATH).read_text(encoding="utf-8"))
    routes = payload.get("routes") if isinstance(payload, dict) else None
    if not isinstance(routes, list):
        raise ValueError("Docs Viewer route registry must contain routes")
    policies: list[dict[str, str]] = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        features = {str(value or "").strip() for value in route.get("features") or []}
        basis = str(route.get("recent_basis") or "").strip()
        if "recent" in features and basis not in RECENT_BASES:
            raise ValueError(f"route {route.get('route_id')!r} must declare an added or edited Recent basis")
        if basis and "recent" not in features:
            raise ValueError(f"route {route.get('route_id')!r} declares Recent basis without the feature")
        policies.append(
            {
                "route_id": str(route.get("route_id") or "").strip(),
                "app_kind": str(route.get("app_kind") or "").strip(),
                "scope": str(route.get("default_scope_id") or "").strip(),
                "basis": basis,
            }
        )
    return policies


def recent_basis_for_route(repo_root: Path, *, app_kind: str, scope: str = "") -> str:
    matches = [
        policy
        for policy in recent_route_policies(repo_root)
        if policy["app_kind"] == app_kind and (app_kind == "manage" or policy["scope"] == scope)
    ]
    if not matches:
        return ""
    if len(matches) != 1:
        raise ValueError(f"ambiguous Recent route policy for {app_kind}:{scope}")
    return matches[0]["basis"]
