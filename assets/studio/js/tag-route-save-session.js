import {
  probeStudioHealth
} from "./studio-transport.js";

export function tagRouteServiceState(state, options = {}) {
  const availableMode = options.availableMode || "post";
  return state && state.saveMode === availableMode ? "available" : "unavailable";
}

export async function probeTagRouteSaveMode(state, options = {}) {
  const healthProbe = options.healthProbe || probeStudioHealth;
  const timeoutMs = Number.isFinite(Number(options.timeoutMs)) ? Number(options.timeoutMs) : 500;
  const availableMode = options.availableMode || "post";
  const fallbackMode = options.fallbackMode || "patch";
  const ok = await healthProbe(timeoutMs);
  state.saveMode = ok ? availableMode : fallbackMode;
  if ("importAvailable" in state || options.syncImportAvailable) {
    state.importAvailable = ok;
  }
  const result = {
    ok,
    saveMode: state.saveMode,
    importAvailable: Boolean(state.importAvailable),
    service: tagRouteServiceState(state, { availableMode })
  };
  if (typeof options.onSaveModeChange === "function") {
    options.onSaveModeChange(result);
  }
  if (typeof options.onRouteStateChange === "function") {
    options.onRouteStateChange(result);
  }
  return result;
}

export function applyTagRoutePatchFallback(state, options = {}) {
  const fallbackMode = options.fallbackMode || "patch";
  state.saveMode = fallbackMode;
  if ("importAvailable" in state || options.syncImportAvailable) {
    state.importAvailable = false;
  }
  return {
    saveMode: state.saveMode,
    importAvailable: Boolean(state.importAvailable),
    service: tagRouteServiceState(state)
  };
}

export async function withTagRouteBusy(state, task, options = {}) {
  const syncRouteBusyState = options.syncRouteBusyState;
  state.isBusy = true;
  if (typeof syncRouteBusyState === "function") syncRouteBusyState(state);
  try {
    return await task();
  } finally {
    state.isBusy = false;
    if (typeof syncRouteBusyState === "function") syncRouteBusyState(state);
  }
}

export function bindTagSaveModeReprobe(reprobe, options = {}) {
  const windowObject = options.windowObject || window;
  const documentObject = options.documentObject || document;
  const onVisible = () => {
    if (documentObject.visibilityState === "hidden") return;
    reprobe();
  };
  const onVisibilityChange = () => {
    if (documentObject.visibilityState !== "visible") return;
    reprobe();
  };
  windowObject.addEventListener("focus", onVisible);
  windowObject.addEventListener("pageshow", onVisible);
  documentObject.addEventListener("visibilitychange", onVisibilityChange);
  return () => {
    windowObject.removeEventListener("focus", onVisible);
    windowObject.removeEventListener("pageshow", onVisible);
    documentObject.removeEventListener("visibilitychange", onVisibilityChange);
  };
}

export function projectTagPatchFallbackResult(result = {}) {
  const patchResult = result && result.patchResult && typeof result.patchResult === "object"
    ? result.patchResult
    : {};
  return {
    switchedToPatch: Boolean(result && result.switchToPatch),
    switchMessage: String(result && result.message || ""),
    kind: String(patchResult.kind || ""),
    message: String(patchResult.message || ""),
    snippet: String(patchResult.snippet || "")
  };
}
