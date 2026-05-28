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
  var documentIndex = settings.documentIndex || {};
  var selectedDocument = settings.selectedDocument || {};
  var scopeConfig = settings.scopeConfig || {};
  var panelView = settings.panelView || null;
  var host = createDocsViewerInfoPanelHost({
    refs: refs,
    registry: settings.registry,
    project: function (projection) {
      settings.projectInfoPanel(projection || {});
      if (panelView && typeof settings.projectViewState === "function") {
        panelView.viewState = settings.projectViewState();
      }
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
      allDocsById: documentIndex.allDocsById,
      docsById: documentIndex.docsById,
      selectedDocId: selectedDocument.selectedDocId
    });
  }

  function context() {
    return createDocsViewerHostedViewContext({
      allDocsById: documentIndex.allDocsById,
      buildTrail: settings.buildTrail,
      docsById: documentIndex.docsById,
      payloadCache: selectedDocument.payloadCache,
      routeAccess: routeAccess(),
      selectedDocId: selectedDocument.selectedDocId,
      uiStatusByValue: scopeConfig.uiStatusByValue,
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
