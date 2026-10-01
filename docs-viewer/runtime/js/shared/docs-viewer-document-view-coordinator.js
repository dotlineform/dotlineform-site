import {
  createDocsViewerDocumentDisplayModeHost
} from "./docs-viewer-document-display-mode-host.js";
import {
  createDocsViewerInfoPanelController
} from "./docs-viewer-info-panel-controller.js";
import {
  createDocsViewerMainViewHost
} from "./docs-viewer-main-view-host.js";
import { mountDocsViewerRelatedLinks } from "./docs-viewer-related-links.js";

/** Coordinate document modes and exact pin mounts; reader navigation retains capture, Source transitions close it. */
export function createDocsViewerDocumentViewCoordinator(options) {
  var settings = options || {};
  var viewRegistry = settings.viewRegistry;
  var panelLayout = settings.panelLayout;
  var panelView = settings.panelView || null;
  var infoPanelController = null;
  var panelDocumentMode = "rendered-document";

  if (!viewRegistry) throw new Error("Docs Viewer document-view coordinator requires a view registry.");
  if (!panelLayout) throw new Error("Docs Viewer document-view coordinator requires panel layout.");

  function sharedContextOptions() {
    return {
      allDocsById: settings.documentIndex.allDocsById,
      docsById: settings.documentIndex.docsById,
      payloadCache: settings.selectedDocument.payloadCache,
      appContext: typeof settings.appContext === "function" ? settings.appContext() : settings.appContext,
      selectedDocId: settings.selectedDocument.selectedDocId,
      uiStatusByValue: settings.workspaceConfig.uiStatusByValue,
      viewerTargetDocId: settings.viewerTargetDocId,
      viewerUrl: settings.viewerUrl
    };
  }

  function documentModeContextOptions() {
    return Object.assign({}, sharedContextOptions(), {
      collectionProvider: settings.collectionProvider,
      root: settings.root,
      sourceEditorServices: typeof settings.sourceEditorServices === "function"
        ? settings.sourceEditorServices()
        : settings.sourceEditorServices
    });
  }

  var mainViewHost = createDocsViewerMainViewHost({
    contextOptions: sharedContextOptions,
    defaultViewId: "rendered-document",
    mount: settings.mount,
    panelLayout: panelLayout,
    onViewChange: projectControlState,
    projectControlState: settings.projectMainViewControlState,
    projectToolbar: settings.projectMainView,
    projectViewState: function () { return panelLayout.projectViewState(); },
    registry: viewRegistry,
    showWarning: settings.showWarning,
    updatePanelViewState: function (viewState) {
      if (panelView) panelView.viewState = viewState;
    }
  });

  function activeViewState() {
    return {
      activeViewId: mainViewHost.activeViewId(),
      activeModeId: documentDisplayModeHost.activeModeId()
    };
  }

  function controlActive(controlId) {
    var resolved = viewRegistry.resolveControl(controlId, activeViewState());
    return Boolean(resolved.available && resolved.active);
  }

  function projectControlState() {
    if (typeof settings.projectControlStates === "function") settings.projectControlStates();
  }

  var documentDisplayModeHost = createDocsViewerDocumentDisplayModeHost({
    contextOptions: documentModeContextOptions,
    defaultModeId: "rendered-document",
    mount: settings.mount,
    onModeChange: function (modeId) {
      if (modeId !== panelDocumentMode && infoPanelController) infoPanelController.closeIfOpen();
      panelDocumentMode = modeId;
      projectControlState();
    },
    projectToolbar: settings.projectMainView,
    root: settings.root,
    showWarning: settings.showWarning,
    viewRegistry: viewRegistry
  });

  infoPanelController = createDocsViewerInfoPanelController({
    panelView: panelView,
    projectInfoPanel: function (projection) { panelLayout.projectInfoPanel(projection || {}); },
    projectViewState: function () { return panelLayout.projectViewState(); },
    refs: settings.infoPanelRefs,
    registry: viewRegistry,
  });
  projectControlState();

  function requestDocumentMode(modeId, optionsForRequest) {
    return documentDisplayModeHost.requestMode(modeId, optionsForRequest);
  }

  function showView(viewId, onAccepted, optionsForRequest) {
    var viewRequestSettings = Object.assign({}, optionsForRequest || {});
    var requestSettings = Object.assign({}, optionsForRequest || {}, {
      onAccepted: function () {
        mainViewHost.requestView(viewId, Object.assign({}, viewRequestSettings, {
          warn: false,
          onAccepted: function () {
            if (typeof onAccepted === "function") onAccepted();
          }
        }));
      }
    });
    if (!Object.prototype.hasOwnProperty.call(requestSettings, "warn")) requestSettings.warn = false;
    return documentDisplayModeHost.requestMode("rendered-document", requestSettings);
  }

  function showRenderedDocument(onAccepted, optionsForRequest) {
    return showView("rendered-document", onAccepted, optionsForRequest);
  }

  return {
    activeViewState: activeViewState,
    confirmDocumentNavigation: documentDisplayModeHost.confirmNavigation,
    bind: function () { infoPanelController.bind(); },
    closeInfoIfOpen: function () { return infoPanelController.closeIfOpen(); },
    controlActive: controlActive,
    mountRelatedLinks: function (context) {
      var available = viewRegistry.resolveView("related-links").available;
      if (!available || documentDisplayModeHost.activeModeId() !== "rendered-document") return;
      mountDocsViewerRelatedLinks(Object.assign({}, context, {
        onPin: function (capture) {
          if (documentDisplayModeHost.activeModeId() === "rendered-document") infoPanelController.pinRelatedLinks(capture);
        }
      }));
    },
    requestDocumentMode: requestDocumentMode,
    requestMainView: function (viewId, requestOptions) { return mainViewHost.requestView(viewId, requestOptions); },
    showRenderedDocument: showRenderedDocument,
    showView: showView
  };
}
