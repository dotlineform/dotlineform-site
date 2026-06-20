import { loadStudioConfig } from "./studio-config.js";
import { hasStudioRouteBodyRenderer, renderStudioRouteBody } from "./studio-route-body-renderers.js";
import { buildStudioShellContract, listStudioRoutes } from "./studio-route-registry.js";
import { initStudioThemeToggle } from "./studio-theme.js";

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

    if (!hasStudioRouteBodyRenderer(contract.route.id)) {
      renderAppError(root, `Studio route body is not registered: ${contract.route.id}`);
      return;
    }

    document.title = `${contract.route.title} | dotlineform Studio`;
    root.innerHTML = renderStudioShell(
      config,
      contract.route,
      await renderStudioRouteBody(contract.route.id, config, { importModule: importVersioned })
    );
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
      const activeClass = route.id === activeRoute.id ? " is-active" : "";
      return `<a class="nav-item${activeClass}" href="${escapeHtml(route.path, true)}" data-studio-navigate="${escapeHtml(route.id, true)}">${escapeHtml(route.label)}</a>`;
    })
    .join("\n          ");
}

function renderAppError(root, message) {
  root.innerHTML = `<main class="container">
    <div class="studio">
      <p class="studioUi__status" data-state="error">${escapeHtml(message)}</p>
    </div>
  </main>`;
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
