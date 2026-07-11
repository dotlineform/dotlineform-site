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
        projectToolbar: projectToolbar,
        requestView: requestView,
        showWarning: showWarning
      })
    });
  }

  function moduleContext(overrides) {
    return createDocsViewerMainViewModuleContext(contextOptions(overrides));
  }

  function unmountActive() {
    var lifecycle = activeLifecycle;
    activeLifecycle = null;
    return callLifecycle(lifecycle, "unmount", moduleContext({ mount: mount }));
  }

  function loadLifecycle(view) {
    return Promise.resolve()
      .then(function () {
        return typeof view.load === "function" ? view.load() : null;
      })
      .then(function (loaded) {
        return lifecycleFromLoaded(loaded, view);
      });
  }

  function mountLifecycle(lifecycle) {
    activeLifecycle = lifecycle;
    return callLifecycle(lifecycle, "mount", moduleContext({ mount: mount }));
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
        requestedViewId: resolved.view.id
      })) === false
    ) {
      return false;
    }
    activeViewId = resolved.view.id;
    if (panelLayout && typeof panelLayout.setActiveMainView === "function") {
      panelLayout.setActiveMainView(activeViewId);
    }
    projectState();
    if (typeof requestSettings.onAccepted === "function") {
      requestSettings.onAccepted(resolved.view);
    }
    if (resolved.view.id === "rendered-document" || !resolved.view.load) {
      unmountActive();
      return true;
    }
    unmountActive()
      .then(function () {
        return loadLifecycle(resolved.view);
      })
      .then(mountLifecycle)
      .catch(function (error) {
        console.warn("docs_viewer: main hosted view failed", error);
        activeLifecycle = null;
        showWarning(error && error.message ? error.message : "View failed to load.", true);
      });
    return true;
  }

  requestView(activeViewId, { warn: false });

  return {
    activeViewId: function () { return activeViewId; },
    moduleContext: moduleContext,
    projectToolbar: projectToolbar,
    requestView: requestView,
    viewOptions: viewOptions
  };
}
