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

  function appContext() {
    return typeof settings.appContext === "function" ? settings.appContext() : settings.appContext;
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
      collectionProvider: settings.collectionProvider,
      docsById: documentIndex.docsById,
      payloadCache: selectedDocument.payloadCache,
      appContext: appContext(),
      selectedDocId: selectedDocument.selectedDocId,
      sourceEditorServices: typeof settings.sourceEditorServices === "function" ? settings.sourceEditorServices() : settings.sourceEditorServices,
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
    var eligible = typeof settings.controlActive !== "function" || settings.controlActive("info");
    var canShow = eligible && Boolean(currentSelectedDoc() && metadataInfoAvailable());
    var open = host.isOpen();
    var label = open ? "Hide document info" : "Show document info";
    if (typeof settings.projectControlState === "function") {
      settings.projectControlState("info", {
        hidden: !canShow,
        expanded: open,
        label: label
      });
    }
  }

  function update() {
    renderToggleState();
    if (host.isOpen()) {
      host.update(context());
    }
  }

  function openView(viewId) {
    if (!currentSelectedDoc()) return;
    var defaultViewId = typeof settings.defaultViewId === "function" ? settings.defaultViewId() : settings.defaultViewId;
    var targetViewId = String(viewId || "").trim() || String(defaultViewId || "").trim() || host.activeViewId() || "metadata-info";
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
    if (refs.closeButton) {
      refs.closeButton.addEventListener("click", function () {
        close();
      });
    }
  }

  return {
    activeViewId: function () { return host.activeViewId(); },
    bind: bind,
    close: close,
    closeIfOpen: closeIfOpen,
    currentSelectedDoc: currentSelectedDoc,
    isOpen: function () { return host.isOpen(); },
    handleControl: function () {
      if (!closeIfOpen()) openView("");
    },
    openView: openView,
    renderToggleState: renderToggleState,
    update: update
  };
}
