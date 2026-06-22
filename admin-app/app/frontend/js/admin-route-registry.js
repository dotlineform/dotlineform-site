import { loadAdminConfig } from "./admin-config.js";

export async function resolveCurrentAdminRoute(options = {}) {
  const config = options.config || await loadAdminConfig();
  const path = options.path || currentPathname();
  const routes = getAdminRouteEntries(config);
  const normalizedPath = normalizeRoutePath(path);
  const route = routes.find((entry) => normalizeRoutePath(entry.path) === normalizedPath);
  if (!route) {
    throw new Error(`Unknown Admin route: ${path}`);
  }
  return { config, route };
}

export function getAdminRouteEntries(config) {
  const routes = config && config.app && config.app.routes;
  if (!routes || typeof routes !== "object" || Array.isArray(routes)) return [];
  return Object.entries(routes)
    .filter(([id, route]) => typeof id === "string" && route && typeof route === "object" && !Array.isArray(route))
    .map(([id, route]) => ({ id, ...route }))
    .filter((route) => typeof route.path === "string" && typeof route.template === "string" && typeof route.script === "string");
}

export function normalizeRoutePath(path) {
  let pathname = "/";
  try {
    pathname = new URL(String(path || "/"), currentOrigin()).pathname;
  } catch (_error) {
    pathname = String(path || "/").split(/[?#]/, 1)[0] || "/";
  }
  pathname = pathname.trim() || "/";
  if (pathname !== "/" && !pathname.endsWith("/")) {
    pathname = `${pathname}/`;
  }
  return pathname;
}

function currentPathname() {
  return typeof window !== "undefined" && window.location ? window.location.pathname : "/";
}

function currentOrigin() {
  return typeof window !== "undefined" && window.location && window.location.origin
    ? window.location.origin
    : "http://127.0.0.1";
}
