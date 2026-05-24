import { loadStudioConfig } from "./studio-config.js";

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

export function getStudioViews(config) {
  const views = getStudioRuntime(config).views;
  return Array.isArray(views)
    ? views.filter((view) => view && typeof view === "object" && typeof view.id === "string")
    : [];
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

if (typeof document !== "undefined") {
  attachStudioNavigation().catch((error) => {
    console.warn("studio_navigation: unavailable", error);
  });
}
