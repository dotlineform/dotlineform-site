import {
  listDocsViewerHostedViewsForPanel
} from "./docs-viewer-hosted-views.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
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
  var updatePanelViewState = typeof settings.updatePanelViewState === "function" ? settings.updatePanelViewState : function () {};
  var showWarning = typeof settings.showWarning === "function" ? settings.showWarning : function () {};
  var activeViewId = cleanString(settings.defaultViewId) || "rendered-document";

  function viewOptions() {
    return listDocsViewerHostedViewsForPanel(registry, "main").map(function (view) {
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
    if (!registry || typeof registry.resolve !== "function") {
      return {
        available: false,
        reason: "missing",
        view: null
      };
    }
    return registry.resolve(targetViewId);
  }

  function projectState() {
    updatePanelViewState(projectViewState());
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
    activeViewId = resolved.view.id;
    if (panelLayout && typeof panelLayout.setActiveMainView === "function") {
      panelLayout.setActiveMainView(activeViewId);
    }
    projectState();
    if (typeof requestSettings.onAccepted === "function") {
      requestSettings.onAccepted(resolved.view);
    }
    return true;
  }

  requestView(activeViewId, { warn: false });

  return {
    activeViewId: function () { return activeViewId; },
    requestView: requestView,
    viewOptions: viewOptions
  };
}
