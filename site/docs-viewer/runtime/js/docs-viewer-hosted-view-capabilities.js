const LAYOUT_STATES = ["normal", "collapsed", "expanded"];

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeBoolean(value) {
  return value === true || value === "true";
}

function normalizeLayoutStates(value, fallback) {
  const values = Array.isArray(value) ? value : [];
  const states = [];
  values.forEach(function (item) {
    const state = cleanString(item).toLowerCase();
    if (LAYOUT_STATES.indexOf(state) !== -1 && states.indexOf(state) === -1) {
      states.push(state);
    }
  });
  if (states.length > 0) return states;
  return Array.isArray(fallback) && fallback.length > 0 ? fallback.slice() : ["normal"];
}

export function normalizeHostedViewCapabilities(rawCapabilities, defaults) {
  const raw = rawCapabilities && typeof rawCapabilities === "object" && !Array.isArray(rawCapabilities)
    ? rawCapabilities
    : {};
  const fallback = defaults && typeof defaults === "object" ? defaults : {};
  const rawLayoutStates = raw.layout_states || raw.layoutStates;
  const fallbackLayoutStates = fallback.layoutStates || fallback.layout_states || ["normal"];
  return {
    layoutStates: normalizeLayoutStates(rawLayoutStates, fallbackLayoutStates),
    toolbar: raw.toolbar == null ? normalizeBoolean(fallback.toolbar) : normalizeBoolean(raw.toolbar),
    toolbarView: cleanString(raw.toolbar_view || raw.toolbarView || fallback.toolbarView || fallback.toolbar_view)
  };
}

export function hostedViewSupportsLayoutState(capabilities, state) {
  const viewCapabilities = normalizeHostedViewCapabilities(capabilities);
  return viewCapabilities.layoutStates.indexOf(cleanString(state).toLowerCase()) !== -1;
}

export function firstHostedViewLayoutState(capabilities, fallback) {
  const normalizedFallback = cleanString(fallback).toLowerCase() || "normal";
  const viewCapabilities = normalizeHostedViewCapabilities(capabilities);
  if (viewCapabilities.layoutStates.indexOf(normalizedFallback) !== -1) return normalizedFallback;
  if (viewCapabilities.layoutStates.indexOf("normal") !== -1) return "normal";
  return viewCapabilities.layoutStates[0] || "normal";
}
