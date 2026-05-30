import { loadStudioConfig } from "./studio-config.js";
import { initStudioThemeToggle } from "./studio-theme.js";

export const STUDIO_MODAL_EVENT = "studio:open-modal";

export function getStudioRuntime(config) {
  const runtime = config && config.app && config.app.runtime;
  return runtime && typeof runtime === "object" && !Array.isArray(runtime) ? runtime : {};
}

export function getStudioServices(config) {
  const services = getStudioRuntime(config).services;
  return services && typeof services === "object" && !Array.isArray(services) ? services : {};
}

export function getStudioSites(config) {
  const sites = getStudioRuntime(config).sites;
  return sites && typeof sites === "object" && !Array.isArray(sites) ? sites : {};
}

export function getStudioExternalLinks(config) {
  const links = config && config.external_links;
  return links && typeof links === "object" && !Array.isArray(links) ? links : {};
}

export function getStudioViews(config) {
  const views = getStudioRuntime(config).views;
  if (Array.isArray(views)) {
    return views.filter((view) => view && typeof view === "object" && typeof view.id === "string");
  }

  const routes = config && config.app && config.app.routes;
  if (!routes || typeof routes !== "object" || Array.isArray(routes)) return [];
  return Object.entries(routes)
    .filter(([routeId, route]) => routeId && route && typeof route === "object" && !Array.isArray(route))
    .map(([routeId, route]) => ({ id: routeId, ...route }));
}

export function getStudioView(config, viewId) {
  const normalizedViewId = normalizeViewId(viewId);
  return getStudioViews(config).find((view) => normalizeViewId(view.id) === normalizedViewId) || null;
}

export function buildStudioViewUrl(config, viewId, params = {}) {
  const view = getStudioView(config, viewId);
  if (!view || typeof view.path !== "string" || !view.path.trim()) {
    throw new Error(`Unknown Studio view: ${viewId}`);
  }

  if (isDocsViewerPath(config, view.path)) {
    return buildDocsViewerUrl(config, view.path, params);
  }

  const url = new URL(view.path, currentOrigin());
  for (const [key, value] of Object.entries(params || {})) {
    if (!key || value == null || value === "") continue;
    url.searchParams.set(key, String(value));
  }
  return url.origin === currentOrigin()
    ? `${url.pathname}${url.search}${url.hash}`
    : url.href;
}

export function buildPublicSiteUrl(config, path = "/", params = {}, options = {}) {
  const siteKey = options && options.site === "production" ? "production" : "public_preview";
  const base = getStudioSiteBase(config, siteKey);
  if (!base) {
    throw new Error(`Missing Studio site base: ${siteKey}`);
  }
  const url = new URL(String(path || "/"), ensureTrailingSlash(base));
  for (const [key, value] of Object.entries(params || {})) {
    if (!key || value == null || value === "") continue;
    url.searchParams.set(key, String(value));
  }
  return url.href;
}

export function buildDocsViewerUrl(config, target = "/docs/", params = {}) {
  const link = getDocsViewerLinkConfig(config);
  const baseUrl = normalizeBaseUrl(link.base_url || currentOrigin());
  const docsPath = normalizePath(link.docs_path || "/docs/");
  const defaultMode = String(link.default_mode || "manage").trim();
  const targetUrl = new URL(String(target || docsPath), currentOrigin());
  const output = new URL(targetUrl.pathname || docsPath, ensureTrailingSlash(baseUrl));

  targetUrl.searchParams.forEach((value, key) => {
    output.searchParams.set(key, value);
  });
  for (const [key, value] of Object.entries(params || {})) {
    if (!key || value == null || value === "") continue;
    output.searchParams.set(key, String(value));
  }
  if (defaultMode && !output.searchParams.has("mode")) {
    output.searchParams.set("mode", defaultMode);
  }
  return output.href;
}

export function buildDocsViewerDocUrl(config, viewId) {
  const link = getDocsViewerLinkConfig(config);
  const view = getStudioView(config, viewId);
  const docId = view && typeof view.doc_id === "string" ? view.doc_id.trim() : "";
  const docScope = String(link.doc_scope || "studio").trim();
  const defaultMode = String(link.default_mode || "manage").trim();
  const params = {};
  if (docScope) params.scope = docScope;
  if (docId) params.doc = docId;
  if (defaultMode) params.mode = defaultMode;
  return buildDocsViewerUrl(config, link.docs_path || "/docs/", params);
}

export function getStudioSiteBase(config, siteKey) {
  const sites = getStudioSites(config);
  const site = sites && sites[siteKey];
  const value = site && site.base;
  return typeof value === "string" && value.trim() ? value.trim().replace(/\/+$/, "") : "";
}

export async function navigateTo(viewId, params = {}) {
  const config = await loadStudioConfig();
  const url = buildStudioViewUrl(config, viewId, params);
  window.location.assign(url);
  return url;
}

export function openModal(name, params = {}, options = {}) {
  const modalName = normalizeModalName(name);
  if (!modalName) {
    throw new Error("Studio modal name is required");
  }
  const detail = {
    name: modalName,
    params: isPlainObject(params) ? { ...params } : {},
    returnContext: options.returnContext || null,
  };
  const target = options.target || currentDocument();
  if (!target || typeof target.dispatchEvent !== "function") {
    return { detail, defaultPrevented: false };
  }
  const EventConstructor = currentCustomEvent();
  const event = new EventConstructor(STUDIO_MODAL_EVENT, {
    bubbles: true,
    cancelable: true,
    detail,
  });
  target.dispatchEvent(event);
  return event;
}

export async function attachStudioNavigation(root = document) {
  const config = await loadStudioConfig();
  const targetRoot = root && typeof root.addEventListener === "function" ? root : document;
  updateDocsViewerLinks(config, targetRoot);
  targetRoot.addEventListener("click", (event) => {
    const navigateTrigger = event.target && event.target.closest
      ? event.target.closest("[data-studio-navigate]")
      : null;
    if (navigateTrigger && targetRoot.contains(navigateTrigger) && !shouldUseNativeNavigation(event, navigateTrigger)) {
      const viewId = navigateTrigger.getAttribute("data-studio-navigate");
      if (!viewId) return;

      event.preventDefault();
      window.location.assign(buildStudioViewUrl(config, viewId, readNavigationParams(navigateTrigger)));
      return;
    }

    const modalTrigger = event.target && event.target.closest
      ? event.target.closest("[data-studio-modal]")
      : null;
    if (!modalTrigger || !targetRoot.contains(modalTrigger) || shouldUseNativeNavigation(event, modalTrigger)) return;

    const modalName = modalTrigger.getAttribute("data-studio-modal");
    if (!modalName) return;

    event.preventDefault();
    openModal(modalName, readNavigationParams(modalTrigger), { target: targetRoot });
  });
  return config;
}

export function updateDocsViewerLinks(config, root = document) {
  const targetRoot = root && typeof root.querySelectorAll === "function" ? root : document;
  if (!targetRoot || typeof targetRoot.querySelectorAll !== "function") return;
  targetRoot.querySelectorAll("a[href]").forEach((link) => {
    const docViewId = link.getAttribute("data-studio-doc-view") || "";
    if (docViewId.trim()) {
      link.setAttribute("href", buildDocsViewerDocUrl(config, docViewId));
      return;
    }
    const href = link.getAttribute("href") || "";
    if (!isDocsViewerPath(config, href)) return;
    link.setAttribute("href", buildDocsViewerUrl(config, href));
  });
}

function readNavigationParams(trigger) {
  const rawParams = trigger.getAttribute("data-studio-params");
  if (!rawParams) return {};
  try {
    const parsed = JSON.parse(rawParams);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch (_error) {
    return {};
  }
}

function shouldUseNativeNavigation(event, trigger) {
  if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    return true;
  }
  const target = trigger.getAttribute("target");
  return Boolean(target && target !== "_self");
}

function normalizeViewId(value) {
  return String(value || "").trim().replace(/-/g, "_").toLowerCase();
}

function normalizeModalName(value) {
  return String(value || "").trim().replace(/\s+/g, "-").toLowerCase();
}

function getDocsViewerLinkConfig(config) {
  const links = getStudioExternalLinks(config);
  const docsViewer = links.docs_viewer;
  return docsViewer && typeof docsViewer === "object" && !Array.isArray(docsViewer) ? docsViewer : {};
}

function isDocsViewerPath(config, path) {
  const text = String(path || "").trim();
  if (!text) return false;
  const docsPath = normalizePath(getDocsViewerLinkConfig(config).docs_path || "/docs/");
  try {
    const url = new URL(text, currentOrigin());
    const normalizedPath = normalizePath(url.pathname);
    return normalizedPath === docsPath || normalizedPath.startsWith(docsPath);
  } catch (_error) {
    return false;
  }
}

function isPlainObject(value) {
  return value && typeof value === "object" && !Array.isArray(value);
}

function currentOrigin() {
  return typeof window !== "undefined" && window.location && window.location.origin
    ? window.location.origin
    : "http://127.0.0.1";
}

function currentDocument() {
  return typeof document !== "undefined" ? document : null;
}

function currentCustomEvent() {
  if (typeof CustomEvent !== "undefined") {
    return CustomEvent;
  }
  return class StudioCustomEvent extends Event {
    constructor(type, options = {}) {
      super(type, options);
      this.detail = options.detail;
    }
  };
}

function ensureTrailingSlash(value) {
  const text = String(value || "");
  return text.endsWith("/") ? text : `${text}/`;
}

function normalizeBaseUrl(value) {
  const text = String(value || "").trim();
  return text ? text.replace(/\/+$/, "") : "";
}

function normalizePath(value) {
  const text = String(value || "").trim() || "/";
  const withLeadingSlash = text.startsWith("/") ? text : `/${text}`;
  return withLeadingSlash.endsWith("/") ? withLeadingSlash : `${withLeadingSlash}/`;
}

if (typeof document !== "undefined") {
  initStudioThemeToggle();
  attachStudioNavigation().catch((error) => {
    console.warn("studio_navigation: unavailable", error);
  });
}
