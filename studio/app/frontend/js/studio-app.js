import { loadStudioConfig } from "./studio-config.js";
import { buildStudioShellContract, listStudioRoutes } from "./studio-route-registry.js";
import { initStudioThemeToggle } from "./studio-theme.js";

const ROUTE_BODY_RENDERERS = {
  activity: async () => {
    const module = await importVersioned("./activity-log-shell.js");
    return module.renderActivityLogShell();
  },
  bulk_add_work: async (config) => {
    const module = await importVersioned("./bulk-add-work-shell.js");
    return module.renderBulkAddWorkShell(config);
  },
  catalogue_field_registry: async () => {
    const module = await importVersioned("./catalogue-field-registry-shell.js");
    return module.renderCatalogueFieldRegistryShell();
  },
  catalogue_moment_editor: async () => {
    const module = await importVersioned("./catalogue-moment-shell.js");
    return module.renderCatalogueMomentShell();
  },
  catalogue_series_editor: async () => {
    const module = await importVersioned("./catalogue-series-shell.js");
    return module.renderCatalogueSeriesShell();
  },
  catalogue_status: async () => {
    const module = await importVersioned("./catalogue-status-shell.js");
    return module.renderCatalogueStatusShell();
  },
  catalogue_work_detail_editor: async (config) => {
    const module = await importVersioned("./catalogue-work-detail-shell.js");
    return module.renderCatalogueWorkDetailShell(config);
  },
  catalogue_work_editor: async (config) => {
    const module = await importVersioned("./catalogue-work-shell.js");
    return module.renderCatalogueWorkShell(config);
  },
  project_state: async () => {
    const module = await importVersioned("./project-state-shell.js");
    return module.renderProjectStateShell();
  },
  studio_works: async () => {
    const module = await importVersioned("./studio-works-shell.js");
    return module.renderStudioWorksShell();
  },
  studio_audits: async () => {
    const module = await importVersioned("./studio-audits-shell.js");
    return module.renderStudioAuditsShell();
  }
};

async function bootStudioApp() {
  const root = document.getElementById("studioApp");
  if (!root) return;

  try {
    const config = await loadStudioConfig();
    const contract = buildStudioShellContract(config, window.location);
    if (!contract.route || !contract.shouldRenderShell) {
      renderAppError(root, "Studio route is not available in the JavaScript shell.");
      return;
    }

    const bodyRenderer = ROUTE_BODY_RENDERERS[contract.route.id];
    if (!bodyRenderer) {
      renderAppError(root, `Studio route body is not registered: ${contract.route.id}`);
      return;
    }

    document.title = `${contract.route.title} | dotlineform Studio`;
    root.innerHTML = renderStudioShell(config, contract.route, await bodyRenderer(config));
    initStudioThemeToggle({ root: document });
    await importVersioned(contract.route.script);
  } catch (error) {
    console.warn("studio_app: boot failed", error);
    renderAppError(root, "Studio route failed to load.");
  }
}

function renderStudioShell(config, activeRoute, bodyHtml) {
  return `${renderHeader(config, activeRoute)}
  <main class="container">
    <div class="studio">
      <div class="studio__headerRow">
        <h2>${escapeHtml(activeRoute.title)}</h2>
        <a
          class="studioLayout__docLink"
          href="${escapeHtml(buildDocsViewerDocUrl(config, activeRoute), true)}"
          data-studio-doc-view="${escapeHtml(activeRoute.id, true)}"
          target="_blank"
          rel="noopener noreferrer"
          title="Open Studio page implementation notes"
          aria-label="Open Studio page implementation notes"
        >
          <em>i</em>
        </a>
      </div>
      <div class="studio__content">
        ${bodyHtml}
      </div>
    </div>
  </main>`;
}

function renderHeader(config, activeRoute) {
  return `<header class="site-header">
    <div class="container">
      <div class="site-title"><a href="/studio/">dotlineform studio</a></div>
      <div class="studioHeader__actions">
        <nav class="site-nav" aria-label="Studio">
          ${renderNavItems(config, activeRoute)}
        </nav>
        <button class="studioThemeToggle" type="button" data-studio-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
          <svg class="studioThemeToggle__icon" data-studio-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="4"></circle>
            <path d="M12 2v2"></path>
            <path d="M12 20v2"></path>
            <path d="M4.93 4.93l1.41 1.41"></path>
            <path d="M17.66 17.66l1.41 1.41"></path>
            <path d="M2 12h2"></path>
            <path d="M20 12h2"></path>
            <path d="M4.93 19.07l1.41-1.41"></path>
            <path d="M17.66 6.34l1.41-1.41"></path>
          </svg>
          <svg class="studioThemeToggle__icon" data-studio-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden>
            <path d="M21 12.79A8.5 8.5 0 1 1 11.21 3 6.5 6.5 0 0 0 21 12.79z"></path>
          </svg>
        </button>
      </div>
    </div>
  </header>`;
}

function renderNavItems(config, activeRoute) {
  return listStudioRoutes(config)
    .filter((route) => route.nav)
    .map((route) => {
      const href = route.shellType === "external" && route.id === "docs"
        ? buildDocsViewerUrl(config, route.path)
        : route.path;
      const activeClass = route.id === activeRoute.id ? " is-active" : "";
      return `<a class="nav-item${activeClass}" href="${escapeHtml(href, true)}" data-studio-navigate="${escapeHtml(route.id, true)}">${escapeHtml(route.label)}</a>`;
    })
    .join("\n          ");
}

function renderAppError(root, message) {
  root.innerHTML = `<main class="container">
    <div class="studio">
      <p class="tagStudio__status" data-state="error">${escapeHtml(message)}</p>
    </div>
  </main>`;
}

function buildDocsViewerDocUrl(config, route) {
  const link = getDocsViewerLinkConfig(config);
  const params = {};
  if (link.doc_scope) params.scope = link.doc_scope;
  if (route.docId) params.doc = route.docId;
  if (link.default_mode) params.mode = link.default_mode;
  return buildDocsViewerUrl(config, link.docs_path || "/docs/", params);
}

function buildDocsViewerUrl(config, target = "/docs/", params = {}) {
  const link = getDocsViewerLinkConfig(config);
  const baseUrl = normalizeBaseUrl(link.base_url || currentOrigin());
  const targetUrl = new URL(String(target || link.docs_path || "/docs/"), currentOrigin());
  const output = new URL(targetUrl.pathname || "/docs/", ensureTrailingSlash(baseUrl));

  targetUrl.searchParams.forEach((value, key) => {
    output.searchParams.set(key, value);
  });
  for (const [key, value] of Object.entries(params || {})) {
    if (!key || value == null || value === "") continue;
    output.searchParams.set(key, String(value));
  }
  return output.href;
}

function getDocsViewerLinkConfig(config) {
  const links = config && config.external_links;
  const docsViewer = links && links.docs_viewer;
  return docsViewer && typeof docsViewer === "object" && !Array.isArray(docsViewer) ? docsViewer : {};
}

function importVersioned(path) {
  const url = new URL(path, import.meta.url);
  const version = readAssetVersion();
  if (version) url.searchParams.set("v", version);
  return import(url.href);
}

function readAssetVersion() {
  try {
    const importVersion = new URL(import.meta.url).searchParams.get("v");
    if (importVersion) return importVersion;
  } catch (_error) {
    // Continue to DOM-based lookup.
  }
  const meta = document.querySelector('meta[name="dlf-asset-version"]');
  return meta ? String(meta.getAttribute("content") || "").trim() : "";
}

function ensureTrailingSlash(value) {
  const text = String(value || "");
  return text.endsWith("/") ? text : `${text}/`;
}

function normalizeBaseUrl(value) {
  const text = String(value || "").trim();
  return text ? text.replace(/\/+$/, "") : "";
}

function currentOrigin() {
  return typeof window !== "undefined" && window.location && window.location.origin
    ? window.location.origin
    : "http://127.0.0.1";
}

function escapeHtml(value, attribute = false) {
  const text = String(value == null ? "" : value);
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return attribute
    ? escaped.replace(/"/g, "&quot;").replace(/'/g, "&#39;")
    : escaped;
}

bootStudioApp();
