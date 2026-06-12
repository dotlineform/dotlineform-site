from __future__ import annotations

from html import escape

from .config import PublicSiteConfig


def asset_url(path: str, config: PublicSiteConfig) -> str:
    baseurl = config.site.get("baseurl", "").rstrip("/")
    normalized = "/" + path.lstrip("/")
    return baseurl + normalized


def versioned_asset(path: str, config: PublicSiteConfig) -> str:
    version = config.assets.get("version", "static")
    return f"{asset_url(path, config)}?v={escape(version, quote=True)}"


def script_tag(path: str, config: PublicSiteConfig, *, module: bool = False) -> str:
    type_attr = ' type="module"' if module else ""
    return f'<script{type_attr} src="{versioned_asset(path, config)}"></script>'


def stylesheet_tag(path: str, config: PublicSiteConfig) -> str:
    return f'<link rel="stylesheet" href="{versioned_asset(path, config)}">'


def render_page(
    config: PublicSiteConfig,
    *,
    title: str,
    body: str,
    path: str,
    section: str = "page",
    description: str = "",
    extra_head: tuple[str, ...] = (),
    main_class: str = "container",
    wrap_main: bool = True,
) -> str:
    site_title = config.site.get("title", "dotlineform")
    document_title = site_title if title == site_title else f"{title} | {site_title}"
    body_class = escape(section or "page", quote=True)
    head = render_head(config, title=document_title, description=description, extra_head=extra_head)
    footer = render_footer(config)
    global_scripts = "\n".join(
        (
            script_tag("/assets/js/site-nav.js", config),
            script_tag("/assets/js/theme-toggle.js", config),
        )
    )
    if wrap_main:
        main = f'  <main class="{escape(main_class, quote=True)}">\n{indent(body, 4)}\n  </main>'
    else:
        main = body
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            indent(head, 2),
            "</head>",
            f'<body class="{body_class}">',
            render_header(config, path=path, section=section),
            "",
            main,
            "",
            footer,
            "",
            global_scripts,
            "</body>",
            "</html>",
            "",
        )
    )


def render_head(
    config: PublicSiteConfig,
    *,
    title: str,
    description: str = "",
    extra_head: tuple[str, ...] = (),
) -> str:
    version = config.assets.get("version", "static")
    lines = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{escape(title)}</title>",
    ]
    if description:
        lines.append(f'<meta name="description" content="{escape(description, quote=True)}">')
    lines.extend(
        [
            f'<meta name="dlf-asset-version" content="{escape(version, quote=True)}">',
            '<link rel="icon" href="/favicon.ico" sizes="any">',
            '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
            '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">',
            '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">',
            '<link rel="manifest" href="/site.webmanifest">',
            '<link rel="mask-icon" href="/safari-pinned-tab.svg" color="#111111">',
            "<script>",
            "  (function () {",
            "    try {",
            "      var t = localStorage.getItem('theme');",
            "      document.documentElement.setAttribute('data-theme', (t === 'light' || t === 'dark') ? t : 'light');",
            "    } catch (e) {",
            "      document.documentElement.setAttribute('data-theme', 'light');",
            "    }",
            "  })();",
            "</script>",
            stylesheet_tag("/assets/css/main.css", config),
        ]
    )
    lines.extend(extra_head)
    return "\n".join(lines)


def render_header(config: PublicSiteConfig, *, path: str, section: str) -> str:
    site_title = config.site.get("title", "dotlineform")
    return "\n".join(
        (
            '  <header class="site-header">',
            '    <div class="container">',
            '      <div class="site-title">',
            f'        <a href="/">{escape(site_title)}</a>',
            "      </div>",
            '      <div class="siteHeader__actions">',
            render_nav(config, path=path, section=section, indent_size=8),
            indent(render_theme_toggle(), 8),
            "      </div>",
            "    </div>",
            "  </header>",
        )
    )


def render_nav(config: PublicSiteConfig, *, path: str, section: str, indent_size: int = 0) -> str:
    works_active = section in {"series", "works"} or path in {"/series/", "/moments/", "/recent/", "/works/", "/work-details/"}
    analysis_active = section == "analysis" or path == "/analysis/"
    library_active = section == "library" or path == "/library/"
    lines = [
        '<nav class="site-nav" aria-label="Primary">',
        "  " + render_nav_item("works", "/series/", current=False, active=works_active),
        "  " + render_nav_item("analysis", "/analysis/", current=path == "/analysis/", active=analysis_active),
        "  " + render_nav_item("library", "/library/", current=path == "/library/", active=library_active),
        "</nav>",
    ]
    return indent("\n".join(lines), indent_size) if indent_size else "\n".join(lines)


def render_nav_item(label: str, href: str, *, current: bool, active: bool) -> str:
    classes = "nav-item" + (" is-active" if active else "")
    if current:
        return f'<span class="{classes}" aria-current="page">{escape(label)}</span>'
    if active:
        return f'<a class="{classes}" href="{escape(href, quote=True)}" aria-current="page">{escape(label)}</a>'
    return f'<a class="nav-item" href="{escape(href, quote=True)}">{escape(label)}</a>'


def render_theme_toggle() -> str:
    return "\n".join(
        (
            '<button class="siteThemeToggle" type="button" id="themeToggle" aria-label="Switch to dark mode" title="Switch to dark mode">',
            '  <svg class="siteThemeToggle__icon" data-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">',
            '    <circle cx="12" cy="12" r="4"></circle>',
            '    <path d="M12 2v2"></path>',
            '    <path d="M12 20v2"></path>',
            '    <path d="M4.93 4.93l1.41 1.41"></path>',
            '    <path d="M17.66 17.66l1.41 1.41"></path>',
            '    <path d="M2 12h2"></path>',
            '    <path d="M20 12h2"></path>',
            '    <path d="M4.93 19.07l1.41-1.41"></path>',
            '    <path d="M17.66 6.34l1.41-1.41"></path>',
            "  </svg>",
            '  <svg class="siteThemeToggle__icon" data-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden>',
            '    <path d="M21 12.79A8.5 8.5 0 1 1 11.21 3 6.5 6.5 0 0 0 21 12.79z"></path>',
            "  </svg>",
            "</button>",
        )
    )


def render_footer(config: PublicSiteConfig) -> str:
    site_title = config.site.get("title", "dotlineform")
    return "\n".join(
        (
            '  <footer class="site-footer">',
            '    <div class="container">',
            f'      <span class="muted">&copy; 2026 {escape(site_title)} &middot; <a href="/about/">about</a></span>',
            "    </div>",
            "  </footer>",
        )
    )


def indent(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def docs_viewer_shell(
    config: PublicSiteConfig,
    *,
    route_id: str,
    search_placeholder: str,
    search_aria_label: str,
) -> str:
    route_config_url = config.docs_viewer["route_config_url"]
    entrypoint = config.docs_viewer["entrypoint"]
    return "\n".join(
        (
            '<section',
            '  class="docsViewer"',
            '  id="docsViewerRoot"',
            '  data-allow-management="false"',
            f'  data-route-id="{escape(route_id, quote=True)}"',
            f'  data-route-config-url="{escape(route_config_url, quote=True)}"',
            ">",
            '  <div class="docsViewer__controls">',
            "    <div",
            '      id="docsViewerHeaderControlsMount"',
            "      data-docs-viewer-header-controls-mount",
            '      data-enable-search="true"',
            f'      data-search-placeholder="{escape(search_placeholder, quote=True)}"',
            f'      data-search-aria-label="{escape(search_aria_label, quote=True)}"',
            "    ></div>",
            '    <p class="docsViewer__status muted small" id="docsViewerStatus" hidden></p>',
            '    <div class="docsViewer__bookmarkRow" id="docsViewerBookmarkRow" hidden></div>',
            "  </div>",
            '  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>',
            '  <div id="docsViewerMainViewMount" data-docs-viewer-main-view-mount>',
            "    <noscript>This docs viewer requires JavaScript to load the generated docs index.</noscript>",
            "  </div>",
            '  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>',
            "</section>",
            script_tag(entrypoint, config, module=True),
        )
    )
