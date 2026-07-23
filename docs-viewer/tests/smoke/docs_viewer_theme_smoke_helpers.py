"""Shared computed-style assertions for Docs Viewer theme route smokes."""

from __future__ import annotations

from playwright.sync_api import Page


THEME_ROLES = (
    "canvas",
    "surface",
    "surface-subtle",
    "text",
    "text-muted",
    "border",
    "border-strong",
    "link",
    "link-hover",
    "link-visited",
    "focus-ring",
    "selection-surface",
    "selection-text",
    "overlay",
    "text-disabled",
    "busy",
    "success",
    "warning",
    "danger",
)


def read_docs_viewer_theme_state(page: Page) -> dict[str, object]:
    return page.locator("#docsViewerRoot").evaluate(
        """(root, roles) => {
            const htmlStyle = getComputedStyle(document.documentElement);
            const rootStyle = getComputedStyle(root);
            const panel = root.querySelector('.docsViewer__sidebarInner');
            const content = root.querySelector('#docsViewerContent');
            const action = root.querySelector('#docsViewerRecentButton');
            const active = root.querySelector('.docsViewer__navLink.is-active');
            const probe = document.createElement('span');
            probe.style.position = 'absolute';
            probe.style.visibility = 'hidden';
            document.body.appendChild(probe);
            const resolveColor = value => {
                probe.style.backgroundColor = '';
                probe.style.backgroundColor = value;
                return getComputedStyle(probe).backgroundColor;
            };
            const tokens = Object.fromEntries(roles.map(role => [
                role,
                htmlStyle.getPropertyValue(`--docs-viewer-theme-${role}`).trim()
            ]));
            const resolved = Object.fromEntries(
                Object.entries(tokens).map(([role, value]) => [role, resolveColor(value)])
            );
            probe.remove();
            return {
                theme: document.documentElement.getAttribute('data-theme') || '',
                colorScheme: htmlStyle.colorScheme,
                managementUi: root.dataset.managementUi || '',
                allowManagementAttribute: root.hasAttribute('data-allow-management'),
                themeStylesheetCount: Array.from(document.styleSheets).filter(sheet => (
                    (sheet.href || '').includes('/docs-viewer/static/css/docs-viewer-theme.css')
                )).length,
                managementControls: root.querySelectorAll(
                    '#docsViewerManageActionsButton, #docsViewerManageEditButton'
                ).length,
                tokens,
                resolved,
                bodyBackground: getComputedStyle(document.body).backgroundColor,
                rootColor: rootStyle.color,
                panelBackground: panel ? getComputedStyle(panel).backgroundColor : '',
                contentColor: content ? getComputedStyle(content).color : '',
                actionBackground: action ? getComputedStyle(action).backgroundColor : '',
                actionColor: action ? getComputedStyle(action).color : '',
                activeBackground: active ? getComputedStyle(active).backgroundColor : '',
                activeColor: active ? getComputedStyle(active).color : ''
            };
        }""",
        list(THEME_ROLES),
    )


def assert_docs_viewer_theme_state(
    state: dict[str, object],
    *,
    theme: str,
    management_ui: bool,
    body_uses_viewer_palette: bool,
) -> None:
    tokens = state.get("tokens") if isinstance(state.get("tokens"), dict) else {}
    resolved = state.get("resolved") if isinstance(state.get("resolved"), dict) else {}
    missing = [role for role in THEME_ROLES if not str(tokens.get(role) or "").strip()]
    if missing:
        raise AssertionError(f"{theme} theme omitted shared roles {missing!r}: {state!r}")
    if state.get("theme") != theme or state.get("colorScheme") != theme:
        raise AssertionError(f"expected authoritative {theme} theme projection: {state!r}")
    if state.get("managementUi") != ("true" if management_ui else "false"):
        raise AssertionError(f"theme changed the route management context: {state!r}")
    if state.get("allowManagementAttribute") is not False:
        raise AssertionError(f"theme styling restored the retired management attribute: {state!r}")
    if state.get("themeStylesheetCount") != 1:
        raise AssertionError(f"route did not load one shared Docs Viewer theme owner: {state!r}")
    if bool(state.get("managementControls")) is not management_ui:
        raise AssertionError(f"theme and management presentation were coupled: {state!r}")
    expected_pairs = {
        "rootColor": "text",
        "panelBackground": "surface",
        "contentColor": "text",
        "actionBackground": "surface",
        "actionColor": "text",
        "activeBackground": "selection-surface",
        "activeColor": "selection-text",
    }
    mismatched = {
        field: (state.get(field), resolved.get(role))
        for field, role in expected_pairs.items()
        if state.get(field) != resolved.get(role)
    }
    if body_uses_viewer_palette and state.get("bodyBackground") != resolved.get("canvas"):
        mismatched["bodyBackground"] = (state.get("bodyBackground"), resolved.get("canvas"))
    if mismatched:
        raise AssertionError(f"{theme} computed styles did not consume semantic roles: {mismatched!r}")


def assert_docs_viewer_theme_pair(
    light: dict[str, object],
    dark: dict[str, object],
) -> None:
    light_tokens = light.get("tokens") if isinstance(light.get("tokens"), dict) else {}
    dark_tokens = dark.get("tokens") if isinstance(dark.get("tokens"), dict) else {}
    unchanged = [
        role
        for role in (
            "canvas",
            "surface",
            "text",
            "text-muted",
            "border",
            "link",
            "focus-ring",
            "selection-surface",
            "overlay",
            "text-disabled",
            "success",
            "warning",
            "danger",
        )
        if light_tokens.get(role) == dark_tokens.get(role)
    ]
    if unchanged:
        raise AssertionError(f"light and dark shared semantic roles did not diverge: {unchanged!r}")
