import {
  createDocsViewerDocumentDisplayModeContext
} from "./docs-viewer-view-context.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function noop() {}

function lifecycleFromLoaded(loaded, fallback) {
  if (loaded && typeof loaded === "object") return loaded;
  return fallback || {};
}

function callLifecycle(lifecycle, name, context) {
  if (!lifecycle || typeof lifecycle[name] !== "function") return Promise.resolve(null);
  return Promise.resolve(lifecycle[name](context));
}

function unavailableStatus(reason) {
  if (reason === "access") return "This document mode is not available on this route.";
  if (reason === "disabled" || reason === "unavailable") return "This document mode is disabled.";
  if (reason === "missing") return "This document mode is not registered.";
  return "This document mode is unavailable.";
}

export function createDocsViewerDocumentDisplayModeHost(options) {
  var settings = options || {};
  var viewRegistry = settings.viewRegistry || null;
  var onModeChange = typeof settings.onModeChange === "function" ? settings.onModeChange : noop;
  var projectToolbar = typeof settings.projectToolbar === "function" ? settings.projectToolbar : noop;
  var showWarning = typeof settings.showWarning === "function" ? settings.showWarning : noop;
  var root = settings.root || null;
  var mount = settings.mount || null;
  var activeModeId = cleanString(settings.defaultModeId) || "rendered-document";
  var activeLifecycle = null;

  function projectModeState() {
    if (root && root.dataset) {
      root.dataset.documentDisplayMode = activeModeId;
    }
    onModeChange(activeModeId);
  }

  function resolve(modeId) {
    var id = cleanString(modeId);
    if (!viewRegistry || typeof viewRegistry.resolveMode !== "function") {
      return { id: id, mode: null, registered: false, available: false, reason: "missing" };
    }
    return viewRegistry.resolveMode(id);
  }

  function contextOptions(overrides) {
    var base = typeof settings.contextOptions === "function" ? settings.contextOptions() : settings.contextOptions;
    return Object.assign({}, base || {}, overrides || {}, {
      documentView: Object.assign({}, base && base.documentView ? base.documentView : {}, overrides && overrides.documentView ? overrides.documentView : {}, {
        activeModeId: activeModeId,
        projectToolbar: projectToolbar,
        requestMode: requestMode,
        showWarning: showWarning
      })
    });
  }

  function modeContext(overrides) {
    return createDocsViewerDocumentDisplayModeContext(contextOptions(overrides));
  }

  function unmountActive() {
    var lifecycle = activeLifecycle;
    activeLifecycle = null;
    return callLifecycle(lifecycle, "unmount", modeContext({ mount: mount }));
  }

  function loadLifecycle(mode) {
    return Promise.resolve()
      .then(function () {
        return typeof mode.load === "function" ? mode.load() : null;
      })
      .then(function (loaded) {
        return lifecycleFromLoaded(loaded, mode);
      });
  }

  function mountLifecycle(lifecycle) {
    activeLifecycle = lifecycle;
    return callLifecycle(lifecycle, "mount", modeContext({ mount: mount }));
  }

  function requestMode(modeId, optionsForRequest) {
    var targetModeId = cleanString(modeId) || "rendered-document";
    var requestSettings = optionsForRequest || {};
    var resolved = resolve(targetModeId);
    if (!resolved.available || !resolved.mode) {
      if (requestSettings.warn !== false) {
        showWarning(unavailableStatus(resolved.reason), true);
      }
      return false;
    }
    if (
      !requestSettings.force &&
      activeLifecycle &&
      typeof activeLifecycle.beforeLeave === "function" &&
      activeLifecycle.beforeLeave(modeContext({
        mount: mount,
        requestedModeId: resolved.mode.id
      })) === false
    ) {
      return false;
    }
    activeModeId = resolved.mode.id;
    projectModeState();
    if (resolved.mode.id === "rendered-document" || !resolved.mode.load) {
      unmountActive().then(function () {
        if (typeof requestSettings.onAccepted === "function") requestSettings.onAccepted(resolved.mode);
      });
      return true;
    }
    unmountActive()
      .then(function () {
        return loadLifecycle(resolved.mode);
      })
      .then(mountLifecycle)
      .then(function () {
        if (typeof requestSettings.onAccepted === "function") requestSettings.onAccepted(resolved.mode);
      })
      .catch(function (error) {
        console.warn("docs_viewer: document display mode failed", error);
        activeLifecycle = null;
        showWarning(error && error.message ? error.message : "Document mode failed to load.", true);
      });
    return true;
  }

  projectModeState();

  return {
    activeModeId: function () { return activeModeId; },
    modeContext: modeContext,
    requestMode: requestMode,
    resolve: resolve
  };
}
