const templateCache = new Map();

export async function loadAdminRouteTemplate(route, options = {}) {
  const templateUrl = route && typeof route.template === "string" ? route.template.trim() : "";
  if (!templateUrl) {
    throw new Error(`Admin route ${route && route.id ? route.id : "(unknown)"} is missing template`);
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
  return parseAdminRouteTemplate(html, route);
}

export function parseAdminRouteTemplate(html, route = {}) {
  const template = document.createElement("template");
  template.innerHTML = String(html || "").trim();
  if (!template.content.childElementCount) {
    throw new Error(`Admin route template is empty: ${route.template || route.id || "(unknown)"}`);
  }
  validateAdminRouteTemplate(route, template.content);
  return template.content.cloneNode(true);
}

export function validateAdminRouteTemplate(route, content) {
  const readyRoot = content && content.querySelector
    ? content.querySelector("[data-admin-ready]")
    : null;
  const label = route.template || route.id || "(unknown)";
  if (!readyRoot) {
    throw new Error(`Admin route template is missing a ready-state root: ${label}`);
  }
  if (!readyRoot.hasAttribute("data-admin-busy")) {
    throw new Error(`Admin route template ready-state root is missing data-admin-busy: ${label}`);
  }
}

export function mountAdminRouteTemplate(outlet, fragment) {
  if (!outlet || !fragment) {
    throw new Error("Admin route outlet and template fragment are required");
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
