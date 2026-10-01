import {
  createDocsViewerInfoPanelHost
} from "./docs-viewer-info-panel-host.js";
import {
  createDocsViewerHostedViewContext,
  resolveDocsViewerSelectedDoc
} from "./docs-viewer-view-context.js";

/** Own detached reader capture and live Source context in the shared shell; Close releases either. */
export function createDocsViewerInfoPanelController(options) {
  var settings = options || {};
  var refs = settings.refs || {};
  var documentIndex = settings.documentIndex || {};
  var selectedDocument = settings.selectedDocument || {};
  var workspaceConfig = settings.workspaceConfig || {};
  var panelView = settings.panelView || null;
  var capture = null;
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
      managedDocumentContext: typeof settings.managedDocumentContext === "function"
        ? settings.managedDocumentContext()
        : settings.managedDocumentContext,
      selectedDocId: selectedDocument.selectedDocId,
      sourceEditorServices: typeof settings.sourceEditorServices === "function" ? settings.sourceEditorServices() : settings.sourceEditorServices,
      uiStatusByValue: workspaceConfig.uiStatusByValue,
      viewerTargetDocId: settings.viewerTargetDocId,
      viewerUrl: settings.viewerUrl
    });
  }

  function renderToggleState() {
    var eligible = typeof settings.controlActive !== "function" || settings.controlActive("info");
    var defaultViewId = typeof settings.defaultViewId === "function" ? settings.defaultViewId() : settings.defaultViewId;
    var resolved = defaultViewId ? settings.registry.resolveView(defaultViewId) : null;
    var canShow = eligible && Boolean(currentSelectedDoc() && resolved && resolved.available);
    var open = host.isOpen();
    var view = canShow ? settings.registry.resolveView(open ? host.activeViewId() : defaultViewId) : null;
    var description = view && view.view ? view.view.label.toLowerCase() : "document info";
    var label = (open ? "Hide " : "Show ") + description;
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
    if (host.isOpen() && !capture) {
      host.update(context());
    }
  }

  function openView(viewId) {
    if (!currentSelectedDoc()) return;
    var defaultViewId = typeof settings.defaultViewId === "function" ? settings.defaultViewId() : settings.defaultViewId;
    var targetViewId = String(viewId || "").trim() || String(defaultViewId || "").trim();
    if (!targetViewId || targetViewId === "related-links") return;
    capture = null;
    host.open(targetViewId, context()).then(function () {
      renderToggleState();
    });
  }

  function close() {
    capture = null;
    host.close().then(function () {
      renderToggleState();
    });
  }

  /** Retain one detached reader capture until replacement, Close or Source entry. */
  function pinRelatedLinks(nextCapture) {
    if (capture && host.isOpen() && capture.target.collection === nextCapture.target.collection
        && capture.target.doc_id === nextCapture.target.doc_id) return;
    capture = nextCapture;
    host.open("related-links", { capture: capture, panelTitle: capture.title });
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
    pinRelatedLinks: pinRelatedLinks,
    renderToggleState: renderToggleState,
    update: update
  };
}
