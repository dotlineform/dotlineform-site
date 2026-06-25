export async function loadStudioRouteTemplate(route, options = {}) {
  if (!route || !route.template) {
    throw new Error("Studio route is missing a template path.");
  }
  const fetchImpl = typeof options.fetchImpl === "function" ? options.fetchImpl : fetch;
  const response = await fetchImpl(withAssetVersion(route.template), {
    cache: "no-store"
  });
  if (!response || !response.ok) {
    throw new Error(`Studio route template failed to load: ${route.template}`);
  }
  const html = await response.text();
  validateStudioRouteTemplate(route, html);
  return html;
}

export function validateStudioRouteTemplate(route, html) {
  const text = String(html == null ? "" : html).trim();
  if (!text) {
    throw new Error(`Studio route template is empty: ${route && route.template}`);
  }
  if (typeof DOMParser === "undefined") return;

  const doc = new DOMParser().parseFromString(text, "text/html");
  if (!doc.body || !doc.body.firstElementChild) {
    throw new Error(`Studio route template has no body content: ${route && route.template}`);
  }
  const readyRoot = doc.body.querySelector("[data-studio-ready]");
  if (!readyRoot) {
    throw new Error(`Studio route template is missing a ready-state root: ${route && route.template}`);
  }
  if (!readyRoot.hasAttribute("data-studio-busy")) {
    throw new Error(`Studio route template ready-state root is missing data-studio-busy: ${route && route.template}`);
  }
}

function withAssetVersion(path) {
  const url = new URL(path, window.location.href);
  const version = readAssetVersion();
  if (version) url.searchParams.set("v", version);
  return url.href;
}

function readAssetVersion() {
  const meta = document.querySelector('meta[name="dlf-asset-version"]');
  return meta ? String(meta.getAttribute("content") || "").trim() : "";
}
