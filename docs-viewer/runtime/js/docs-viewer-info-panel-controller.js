import {
  createDocsViewerInfoPanelHost
} from "./docs-viewer-info-panel-host.js";
import {
  createDocsViewerHostedViewContext,
  resolveDocsViewerSelectedDoc
} from "./docs-viewer-view-context.js";

export function createDocsViewerInfoPanelController(options) {
  var settings = options || {};
  var refs = settings.refs || {};
  var state = settings.state;
  var host = createDocsViewerInfoPanelHost({
    refs: refs,
    registry: settings.registry,
    project: function (projection) {
      settings.projectInfoPanel(projection || {});
      state.viewState = settings.projectViewState();
      renderToggleState();
    }
  });

  function viewerScope() {
    return typeof settings.viewerScope === "function" ? settings.viewerScope() : settings.viewerScope;
  }

  function routeAccess() {
    return typeof settings.routeAccess === "function" ? settings.routeAccess() : settings.routeAccess;
  }

  function currentSelectedDoc() {
    return resolveDocsViewerSelectedDoc({
      allDocsById: state.allDocsById,
      docsById: state.docsById,
      selectedDocId: state.selectedDocId
    });
  }

  function context() {
    return createDocsViewerHostedViewContext({
      allDocsById: state.allDocsById,
      buildTrail: settings.buildTrail,
      docsById: state.docsById,
      payloadCache: state.payloadCache,
      routeAccess: routeAccess(),
      selectedDocId: state.selectedDocId,
      uiStatusByValue: state.uiStatusByValue,
      viewerScope: viewerScope(),
      viewerTargetDocId: settings.viewerTargetDocId,
      viewerUrl: settings.viewerUrl
    });
  }

  function metadataInfoAvailable() {
    return host.viewOptions().some(function (view) {
      return view.available;
    });
  }

  function renderToggleState() {
    if (!settings.infoToggle) return;
    var canShow = Boolean(currentSelectedDoc() && metadataInfoAvailable());
    var open = host.isOpen();
    var label = open ? "Hide document info" : "Show document info";
    settings.projectDocumentShell({
      infoToggleHidden: !canShow,
      infoToggleLabel: label,
      infoTogglePressed: open
    });
  }

  function update() {
    renderToggleState();
    if (host.isOpen()) {
      host.update(context());
    }
  }

  function openView(viewId) {
    if (!currentSelectedDoc()) return;
    var targetViewId = String(viewId || "").trim() || host.activeViewId() || "metadata-info";
    host.open(targetViewId, context()).then(function () {
      renderToggleState();
    });
  }

  function close() {
    host.close().then(function () {
      renderToggleState();
    });
  }

  function closeIfOpen() {
    if (!host.isOpen()) return false;
    close();
    return true;
  }

  function bind() {
    if (settings.infoToggle) {
      settings.infoToggle.addEventListener("click", function () {
        if (!closeIfOpen()) {
          openView("metadata-info");
        }
      });
    }

    if (refs.closeButton) {
      refs.closeButton.addEventListener("click", function () {
        close();
      });
    }

    if (refs.toolbar) {
      refs.toolbar.addEventListener("click", function (event) {
        var button = event.target.closest("[data-info-panel-view]");
        if (!button || button.disabled) return;
        openView(button.dataset.infoPanelView);
      });
    }
  }

  return {
    bind: bind,
    close: close,
    closeIfOpen: closeIfOpen,
    currentSelectedDoc: currentSelectedDoc,
    isOpen: function () { return host.isOpen(); },
    openView: openView,
    renderToggleState: renderToggleState,
    update: update
  };
}
