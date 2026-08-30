import {
  createDocsViewerMainViewModuleContext
} from "./docs-viewer-view-context.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function lifecycleFromLoaded(loaded, fallback) {
  if (loaded && typeof loaded === "object") return loaded;
  return fallback || {};
}

function callLifecycle(lifecycle, name, context) {
  if (!lifecycle || typeof lifecycle[name] !== "function") return Promise.resolve(null);
  return Promise.resolve(lifecycle[name](context));
}

function unavailableStatus(reason) {
  if (reason === "access") return "This view is not available on this route.";
  if (reason === "disabled") return "This view is disabled.";
  if (reason === "missing") return "This view is not registered.";
  return "This view is unavailable.";
}

function immutableValue(value) {
  if (Array.isArray(value)) return Object.freeze(value.map(immutableValue));
  if (!value || typeof value !== "object") return value;
  return Object.freeze(Object.keys(value).reduce(function (copy, key) {
    copy[key] = immutableValue(value[key]);
    return copy;
  }, {}));
}

export function createDocsViewerMainViewHost(options) {
  var settings = options || {};
  var registry = settings.registry || null;
  var panelLayout = settings.panelLayout || null;
  var projectViewState = typeof settings.projectViewState === "function" ? settings.projectViewState : function () { return null; };
  var projectToolbar = typeof settings.projectToolbar === "function" ? settings.projectToolbar : function () {};
  var updatePanelViewState = typeof settings.updatePanelViewState === "function" ? settings.updatePanelViewState : function () {};
  var showWarning = typeof settings.showWarning === "function" ? settings.showWarning : function () {};
  var mount = settings.mount || null;
  var activeViewId = cleanString(settings.defaultViewId) || "rendered-document";
  var activeLifecycle = null;
  var activeTargetContext = null;
  var activeRequestReason = "";
  var requestGeneration = 0;

  function viewOptions() {
    return (registry ? registry.listViews("main") : []).map(function (view) {
      return {
        id: view.id,
        label: view.label,
        available: Boolean(view.available),
        unavailableReason: view.unavailableReason || ""
      };
    });
  }

  function resolve(viewId) {
    var targetViewId = cleanString(viewId);
    if (!registry || typeof registry.resolveView !== "function") {
      return {
        available: false,
        reason: "missing",
        view: null
      };
    }
    return registry.resolveView(targetViewId);
  }

  function projectState() {
    updatePanelViewState(projectViewState());
  }

  function contextOptions(overrides) {
    var base = typeof settings.contextOptions === "function" ? settings.contextOptions() : settings.contextOptions;
    return Object.assign({}, base || {}, overrides || {}, {
      mainView: Object.assign({}, base && base.mainView ? base.mainView : {}, overrides && overrides.mainView ? overrides.mainView : {}, {
        activeViewId: activeViewId,
        projectControlState: typeof settings.projectControlState === "function"
          ? settings.projectControlState
          : function () {},
        projectToolbar: projectToolbar,
        requestView: requestView,
        showWarning: showWarning
      })
    });
  }

  function moduleContext(overrides) {
    return createDocsViewerMainViewModuleContext(contextOptions(overrides));
  }

  function unmountActive(overrides) {
    var lifecycle = activeLifecycle;
    var context = moduleContext(overrides || {});
    activeLifecycle = null;
    return callLifecycle(lifecycle, "unmount", context);
  }

  function loadLifecycle(view, context) {
    return Promise.resolve()
      .then(function () {
        return typeof view.load === "function" ? view.load(context) : null;
      })
      .then(function (loaded) {
        return lifecycleFromLoaded(loaded, view);
      });
  }

  function mountLifecycle(lifecycle, context) {
    activeLifecycle = lifecycle;
    return callLifecycle(lifecycle, "mount", context);
  }

  function requestView(viewId, optionsForRequest) {
    var targetViewId = cleanString(viewId);
    var requestSettings = optionsForRequest || {};
    var resolved = resolve(targetViewId);
    if (!resolved.available || !resolved.view) {
      if (requestSettings.warn !== false) {
        showWarning(unavailableStatus(resolved.reason), true);
      }
      return false;
    }
    if (
      !requestSettings.force &&
      activeLifecycle &&
      typeof activeLifecycle.beforeLeave === "function" &&
      activeLifecycle.beforeLeave(moduleContext({
        mount: mount,
        requestedViewId: resolved.view.id,
        requestReason: cleanString(requestSettings.reason),
        targetContext: activeTargetContext
      })) === false
    ) {
      return false;
    }
    var requestId = requestGeneration + 1;
    requestGeneration = requestId;
    var requestReason = cleanString(requestSettings.reason);
    var previousTargetContext = activeTargetContext;
    var unmountPromise = unmountActive({
      mount: mount,
      requestedViewId: resolved.view.id,
      requestReason: requestReason,
      targetContext: previousTargetContext
    });
    activeViewId = resolved.view.id;
    activeTargetContext = requestSettings.targetContext && typeof requestSettings.targetContext === "object"
      ? immutableValue(requestSettings.targetContext)
      : null;
    activeRequestReason = requestReason;
    if (panelLayout && typeof panelLayout.setActiveMainView === "function") {
      panelLayout.setActiveMainView(activeViewId);
    }
    if (panelLayout && typeof panelLayout.setMainLayoutState === "function") {
      panelLayout.setMainLayoutState(resolved.view.mainLayoutState || "normal");
    }
    projectState();
    if (requestSettings.projectControls !== false && typeof settings.onViewChange === "function") {
      settings.onViewChange(activeViewId);
    }
    if (typeof requestSettings.onAccepted === "function") {
      requestSettings.onAccepted(resolved.view);
    }
    if (resolved.view.id === "rendered-document" || !resolved.view.load) {
      return true;
    }
    var lifecycleContext = moduleContext({
      mount: mount,
      requestReason: activeRequestReason,
      targetContext: activeTargetContext
    });
    unmountPromise
      .then(function () {
        if (requestId !== requestGeneration) return null;
        return loadLifecycle(resolved.view, lifecycleContext);
      })
      .then(function (lifecycle) {
        if (!lifecycle || requestId !== requestGeneration) return null;
        return mountLifecycle(lifecycle, lifecycleContext);
      })
      .catch(function (error) {
        if (requestId !== requestGeneration) return;
        console.warn("docs_viewer: main hosted view failed", error);
        showWarning(error && error.message ? error.message : "View failed to load.", true);
        requestView("rendered-document", {
          force: true,
          reason: "view-failure",
          warn: false
        });
      });
    return true;
  }

  requestView(activeViewId, { projectControls: false, warn: false });

  return {
    activeViewId: function () { return activeViewId; },
    activeTargetContext: function () { return activeTargetContext; },
    moduleContext: moduleContext,
    projectToolbar: projectToolbar,
    requestView: requestView,
    viewOptions: viewOptions
  };
}
