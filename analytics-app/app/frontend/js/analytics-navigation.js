import { loadAnalyticsConfig } from "./analytics-config.js";
import { initAnalyticsThemeToggle } from "./analytics-theme.js";

export const ANALYTICS_MODAL_EVENT = "analytics:open-modal";

export function getAnalyticsRuntime(config) {
  const runtime = config && config.app && config.app.runtime;
  return runtime && typeof runtime === "object" && !Array.isArray(runtime) ? runtime : {};
}

export function getAnalyticsServices(config) {
  const services = getAnalyticsRuntime(config).services;
  return services && typeof services === "object" && !Array.isArray(services) ? services : {};
}

export function getAnalyticsSites(config) {
  const sites = getAnalyticsRuntime(config).sites;
  return sites && typeof sites === "object" && !Array.isArray(sites) ? sites : {};
}

export function getAnalyticsExternalLinks(config) {
  const links = config && config.external_links;
  return links && typeof links === "object" && !Array.isArray(links) ? links : {};
}

export function getAnalyticsViews(config) {
  const views = getAnalyticsRuntime(config).views;
  return Array.isArray(views)
    ? views.filter((view) => view && typeof view === "object" && typeof view.id === "string")
    : [];
}

export function getAnalyticsView(config, viewId) {
  const normalizedViewId = normalizeViewId(viewId);
  return getAnalyticsViews(config).find((view) => normalizeViewId(view.id) === normalizedViewId) || null;
}

export function buildAnalyticsViewUrl(config, viewId, params = {}) {
  const view = getAnalyticsView(config, viewId);
  if (!view || typeof view.path !== "string" || !view.path.trim()) {
    throw new Error(`Unknown Analytics view: ${viewId}`);
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
  const base = getAnalyticsSiteBase(config, siteKey);
  if (!base) {
    throw new Error(`Missing Analytics site base: ${siteKey}`);
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

export function getAnalyticsSiteBase(config, siteKey) {
  const sites = getAnalyticsSites(config);
  const site = sites && sites[siteKey];
  const value = site && site.base;
  return typeof value === "string" && value.trim() ? value.trim().replace(/\/+$/, "") : "";
}

export async function navigateTo(viewId, params = {}) {
  const config = await loadAnalyticsConfig();
  const url = buildAnalyticsViewUrl(config, viewId, params);
  window.location.assign(url);
  return url;
}

export function openModal(name, params = {}, options = {}) {
  const modalName = normalizeModalName(name);
  if (!modalName) {
    throw new Error("Analytics modal name is required");
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
  const event = new EventConstructor(ANALYTICS_MODAL_EVENT, {
    bubbles: true,
    cancelable: true,
    detail,
  });
  target.dispatchEvent(event);
  return event;
}

export async function attachAnalyticsNavigation(root = document) {
  const config = await loadAnalyticsConfig();
  const targetRoot = root && typeof root.addEventListener === "function" ? root : document;
  updateDocsViewerLinks(config, targetRoot);
  targetRoot.addEventListener("click", (event) => {
    const navigateTrigger = event.target && event.target.closest
      ? event.target.closest("[data-analytics-navigate]")
      : null;
    if (navigateTrigger && targetRoot.contains(navigateTrigger) && !shouldUseNativeNavigation(event, navigateTrigger)) {
      const viewId = navigateTrigger.getAttribute("data-analytics-navigate");
      if (!viewId) return;

      event.preventDefault();
      window.location.assign(buildAnalyticsViewUrl(config, viewId, readNavigationParams(navigateTrigger)));
      return;
    }

    const modalTrigger = event.target && event.target.closest
      ? event.target.closest("[data-analytics-modal]")
      : null;
    if (!modalTrigger || !targetRoot.contains(modalTrigger) || shouldUseNativeNavigation(event, modalTrigger)) return;

    const modalName = modalTrigger.getAttribute("data-analytics-modal");
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
    const href = link.getAttribute("href") || "";
    if (!isDocsViewerPath(config, href)) return;
    link.setAttribute("href", buildDocsViewerUrl(config, href));
  });
}

function readNavigationParams(trigger) {
  const rawParams = trigger.getAttribute("data-analytics-params");
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
  const links = getAnalyticsExternalLinks(config);
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
  return class AnalyticsCustomEvent extends Event {
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
  initAnalyticsThemeToggle();
  attachAnalyticsNavigation().catch((error) => {
    console.warn("analytics_navigation: unavailable", error);
  });
}
