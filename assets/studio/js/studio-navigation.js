import { loadStudioConfig } from "./studio-config.js";

export function getStudioRuntime(config) {
  const runtime = config && config.app && config.app.runtime;
  return runtime && typeof runtime === "object" && !Array.isArray(runtime) ? runtime : {};
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

  const url = new URL(view.path, window.location.origin);
  for (const [key, value] of Object.entries(params || {})) {
    if (!key || value == null || value === "") continue;
    url.searchParams.set(key, String(value));
  }
  return url.origin === window.location.origin
    ? `${url.pathname}${url.search}${url.hash}`
    : url.href;
}

export async function navigateTo(viewId, params = {}) {
  const config = await loadStudioConfig();
  const url = buildStudioViewUrl(config, viewId, params);
  window.location.assign(url);
  return url;
}

export async function attachStudioNavigation(root = document) {
  const config = await loadStudioConfig();
  const targetRoot = root && typeof root.addEventListener === "function" ? root : document;
  targetRoot.addEventListener("click", (event) => {
    const trigger = event.target && event.target.closest
      ? event.target.closest("[data-studio-navigate]")
      : null;
    if (!trigger || !targetRoot.contains(trigger) || shouldUseNativeNavigation(event, trigger)) return;

    const viewId = trigger.getAttribute("data-studio-navigate");
    if (!viewId) return;

    event.preventDefault();
    window.location.assign(buildStudioViewUrl(config, viewId, readNavigationParams(trigger)));
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

if (typeof document !== "undefined") {
  attachStudioNavigation().catch((error) => {
    console.warn("studio_navigation: unavailable", error);
  });
}
