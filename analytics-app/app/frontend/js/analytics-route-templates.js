const templateCache = new Map();

export async function loadAnalyticsRouteTemplate(route, options = {}) {
  const templateUrl = route && typeof route.template === "string" ? route.template.trim() : "";
  if (!templateUrl) {
    throw new Error(`Analytics route ${route && route.id ? route.id : "(unknown)"} is missing template`);
  }
  const version = options.version || readAssetVersion();
  const url = appendAssetVersion(templateUrl, version);
  let request = templateCache.get(url);
  if (!request) {
    request = fetch(url, { cache: "default" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text();
      });
    templateCache.set(url, request);
  }
  const html = await request;
  return parseAnalyticsRouteTemplate(html, route);
}

export function parseAnalyticsRouteTemplate(html, route = {}) {
  const template = document.createElement("template");
  template.innerHTML = String(html || "").trim();
  if (!template.content.childElementCount) {
    throw new Error(`Analytics route template is empty: ${route.template || route.id || "(unknown)"}`);
  }
  validateAnalyticsRouteTemplate(route, template.content);
  return template.content.cloneNode(true);
}

export function validateAnalyticsRouteTemplate(route, content) {
  const readyRoot = content && content.querySelector
    ? content.querySelector("[data-analytics-ready]")
    : null;
  const label = route.template || route.id || "(unknown)";
  if (!readyRoot) {
    throw new Error(`Analytics route template is missing a ready-state root: ${label}`);
  }
  if (!readyRoot.hasAttribute("data-analytics-busy")) {
    throw new Error(`Analytics route template ready-state root is missing data-analytics-busy: ${label}`);
  }
}

export function mountAnalyticsRouteTemplate(outlet, fragment) {
  if (!outlet || !fragment) {
    throw new Error("Analytics route outlet and template fragment are required");
  }
  outlet.replaceChildren(fragment);
}

export function appendAssetVersion(url, version = readAssetVersion()) {
  const value = String(url || "").trim();
  if (!value || !version) return value;
  const separator = value.includes("?") ? "&" : "?";
  return `${value}${separator}v=${encodeURIComponent(version)}`;
}

export function readAssetVersion() {
  if (typeof document === "undefined") return "";
  const meta = document.querySelector('meta[name="dlf-asset-version"]');
  return meta ? String(meta.getAttribute("content") || "").trim() : "";
}
