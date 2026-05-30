import {
  getStudioRouteEntry,
  getStudioRouteRegistry
} from "./studio-config.js";

const SHELL_ROUTE_TYPES = new Set(["python", "javascript"]);

export function listStudioRoutes(config) {
  return Object.entries(getStudioRouteRegistry(config))
    .filter(([routeId, route]) => routeId && isPlainObject(route))
    .map(([routeId, route]) => normalizeRoute(routeId, route));
}

export function findStudioRoute(config, routeId) {
  const normalizedRouteId = normalizeRouteId(routeId);
  const route = getStudioRouteEntry(config, normalizedRouteId);
  return route ? normalizeRoute(normalizedRouteId, route) : null;
}

export function resolveStudioRoute(config, locationLike = currentLocation()) {
  const activePath = normalizeRoutePath(locationLike && locationLike.pathname ? locationLike.pathname : "/");
  return listStudioRoutes(config).find((route) => normalizeRoutePath(route.path) === activePath) || null;
}

export function buildStudioShellContract(config, locationLike = currentLocation()) {
  const route = resolveStudioRoute(config, locationLike);
  if (!route) {
    return {
      route: null,
      shouldRenderShell: false,
      mount: null,
      reason: "route_not_registered"
    };
  }

  const shouldRenderShell = route.shellType === "javascript";
  return {
    route,
    shouldRenderShell,
    mount: shouldRenderShell
      ? {
          rootId: "studioApp",
          script: route.script,
          readyStateRouteId: route.readyStateRouteId,
          title: route.title,
          docId: route.docId
        }
      : null,
    reason: shouldRenderShell ? "" : "route_shell_not_migrated"
  };
}

export function routeRequiresShellScript(route) {
  return route && SHELL_ROUTE_TYPES.has(route.shellType);
}

function normalizeRoute(routeId, route) {
  return {
    id: normalizeRouteId(routeId),
    label: normalizeText(route.label),
    title: normalizeText(route.title),
    path: normalizeText(route.path),
    script: normalizeText(route.script),
    docId: normalizeText(route.doc_id),
    nav: route.nav === true,
    shellType: normalizeText(route.shell_type),
    readyStateRouteId: normalizeText(route.ready_state_route_id)
  };
}

function normalizeRouteId(value) {
  return String(value || "").trim().replace(/-/g, "_").toLowerCase();
}

function normalizeRoutePath(value) {
  const path = normalizeText(value) || "/";
  try {
    const url = new URL(path, currentOrigin());
    return withTrailingSlash(url.pathname || "/");
  } catch (_error) {
    return withTrailingSlash(path.split("?")[0] || "/");
  }
}

function withTrailingSlash(path) {
  const text = path.startsWith("/") ? path : `/${path}`;
  return text === "/" || text.endsWith("/") ? text : `${text}/`;
}

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function isPlainObject(value) {
  return value && typeof value === "object" && !Array.isArray(value);
}

function currentLocation() {
  return typeof window !== "undefined" && window.location ? window.location : { pathname: "/" };
}

function currentOrigin() {
  return typeof window !== "undefined" && window.location && window.location.origin
    ? window.location.origin
    : "http://127.0.0.1";
}
