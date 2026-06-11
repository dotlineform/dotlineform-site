import {
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";

export function collectOperationalRouteElements(spec) {
  const elements = {};
  const missing = [];
  for (const [key, value] of Object.entries(spec || {})) {
    elements[key] = value || null;
    if (!value) missing.push(key);
  }
  return {
    elements,
    missing,
    ok: missing.length === 0
  };
}

export function buildOperationalRouteStateDetail(state, options = {}) {
  return {
    route: String(options.route || ""),
    mode: resolveOption(state, options.mode, "idle"),
    service: isServiceAvailable(state, options) ? "available" : "unavailable",
    recordLoaded: Boolean(resolveOption(state, options.recordLoaded, false))
  };
}

export function syncOperationalRouteBusyState(state, options = {}) {
  const root = resolveOption(state, options.root, state && (state.root || state.mount));
  if (!root) return;
  setStudioRouteBusy(
    root,
    Boolean(resolveOption(state, options.isBusy, false)),
    buildOperationalRouteStateDetail(state, options)
  );
}

export function markOperationalRouteReady(state, ready, options = {}) {
  const root = resolveOption(state, options.root, state && (state.root || state.mount));
  if (!root) return;
  setStudioRouteReady(root, ready, buildOperationalRouteStateDetail(state, options));
}

export function projectOperationalRunButtonState(state, options = {}) {
  const serviceAvailable = isServiceAvailable(state, options);
  const isBusy = Boolean(resolveOption(state, options.isBusy, false));
  const canRun = Boolean(resolveOption(state, options.canRun, true));
  return {
    disabled: isBusy || !serviceAvailable || !canRun,
    serviceAvailable,
    isBusy,
    canRun
  };
}

export function applyOperationalRunButtonState(button, state, options = {}) {
  const projection = projectOperationalRunButtonState(state, options);
  if (button) button.disabled = projection.disabled;
  return projection;
}

function isServiceAvailable(state, options) {
  return Boolean(resolveOption(
    state,
    options.serviceAvailable,
    state && (state.serviceAvailable ?? state.serverAvailable)
  ));
}

function resolveOption(state, value, fallback) {
  return typeof value === "function" ? value(state) : value ?? fallback;
}
