import {
  createDocsViewerDocumentDisplayModeHost
} from "./docs-viewer-document-display-mode-host.js";
import {
  createDocsViewerInfoPanelController
} from "./docs-viewer-info-panel-controller.js";
import {
  createDocsViewerMainViewHost
} from "./docs-viewer-main-view-host.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function infoPanelDefaultViewId(settings, modeId) {
  var map = settings.infoPanelDefaultViewByDocumentMode;
  if (!map || typeof map !== "object") return "";
  return cleanString(map[cleanString(modeId)]);
}

export function createDocsViewerDocumentViewCoordinator(options) {
  var settings = options || {};
  var viewRegistry = settings.viewRegistry;
  var panelLayout = settings.panelLayout;
  var panelView = settings.panelView || null;
  var infoPanelController = null;

  if (!viewRegistry) throw new Error("Docs Viewer document-view coordinator requires a view registry.");
  if (!panelLayout) throw new Error("Docs Viewer document-view coordinator requires panel layout.");

  function sharedContextOptions() {
    return {
      allDocsById: settings.documentIndex.allDocsById,
      docsById: settings.documentIndex.docsById,
      payloadCache: settings.selectedDocument.payloadCache,
      appContext: typeof settings.appContext === "function" ? settings.appContext() : settings.appContext,
      selectedDocId: settings.selectedDocument.selectedDocId,
      uiStatusByValue: settings.scopeConfig.uiStatusByValue,
      viewerScope: typeof settings.viewerScope === "function" ? settings.viewerScope() : settings.viewerScope,
      viewerTargetDocId: settings.viewerTargetDocId,
      viewerUrl: settings.viewerUrl
    };
  }

  function documentModeContextOptions() {
    return Object.assign({}, sharedContextOptions(), {
      collectionProvider: settings.collectionProvider,
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
    if (typeof settings.renderDocumentControls === "function") settings.renderDocumentControls();
    if (infoPanelController) infoPanelController.renderToggleState();
  }

  var documentDisplayModeHost = createDocsViewerDocumentDisplayModeHost({
    contextOptions: documentModeContextOptions,
    defaultModeId: "rendered-document",
    mount: settings.mount,
    onModeChange: projectControlState,
    projectToolbar: settings.projectMainView,
    root: settings.root,
    showWarning: settings.showWarning,
    viewRegistry: viewRegistry
  });

  infoPanelController = createDocsViewerInfoPanelController({
    buildTrail: settings.buildTrail,
    documentIndex: settings.documentIndex,
    infoToggle: settings.infoToggle,
    controlActive: controlActive,
    panelView: panelView,
    projectMainView: settings.projectMainView,
    projectInfoPanel: function (projection) { panelLayout.projectInfoPanel(projection || {}); },
    projectViewState: function () { return panelLayout.projectViewState(); },
    refs: settings.infoPanelRefs,
    registry: viewRegistry,
    appContext: settings.appContext,
    scopeConfig: settings.scopeConfig,
    selectedDocument: settings.selectedDocument,
    defaultViewId: function () {
      return infoPanelDefaultViewId(settings, documentDisplayModeHost.activeModeId()) || "metadata-info";
    },
    sourceEditorServices: settings.sourceEditorServices,
    viewerScope: settings.viewerScope,
    viewerTargetDocId: settings.viewerTargetDocId,
    viewerUrl: settings.viewerUrl
  });
  projectControlState();

  function syncInfoPanelDefault(modeId) {
    if (!infoPanelController.isOpen()) return;
    var defaultViewId = infoPanelDefaultViewId(settings, modeId) || "metadata-info";
    if (infoPanelController.activeViewId() === defaultViewId) {
      infoPanelController.update();
      return;
    }
    infoPanelController.openView(defaultViewId);
  }

  function requestDocumentMode(modeId, optionsForRequest) {
    var requestSettings = Object.assign({}, optionsForRequest || {});
    var onAccepted = requestSettings.onAccepted;
    requestSettings.onAccepted = function (mode) {
      if (typeof onAccepted === "function") onAccepted(mode);
      syncInfoPanelDefault(mode && mode.id ? mode.id : modeId);
    };
    return documentDisplayModeHost.requestMode(modeId, requestSettings);
  }

  function showView(viewId, onAccepted, optionsForRequest) {
    var requestSettings = Object.assign({}, optionsForRequest || {}, {
      onAccepted: function () {
        mainViewHost.requestView(viewId, {
          warn: false,
          onAccepted: function () {
            if (typeof onAccepted === "function") onAccepted();
          }
        });
      }
    });
    if (!Object.prototype.hasOwnProperty.call(requestSettings, "warn")) requestSettings.warn = false;
    return documentDisplayModeHost.requestMode("rendered-document", requestSettings);
  }

  function showRenderedDocument(onAccepted, optionsForRequest) {
    return showView("rendered-document", onAccepted, optionsForRequest);
  }

  return {
    activeInfoViewId: function () { return infoPanelController.activeViewId(); },
    activeViewState: activeViewState,
    bind: function () { infoPanelController.bind(); },
    closeInfoIfOpen: function () { return infoPanelController.closeIfOpen(); },
    controlActive: controlActive,
    isConfiguredInfoView: function (viewId) {
      var map = settings.infoPanelDefaultViewByDocumentMode;
      if (!map || typeof map !== "object") return false;
      return Object.keys(map).some(function (modeId) {
        var configuredViewId = cleanString(map[modeId]);
        return configuredViewId && configuredViewId !== "metadata-info" && configuredViewId === cleanString(viewId);
      });
    },
    openInfoView: function (viewId) { return infoPanelController.openView(viewId); },
    renderInfoToggle: function () { return infoPanelController.renderToggleState(); },
    requestDocumentMode: requestDocumentMode,
    requestMainView: function (viewId, requestOptions) { return mainViewHost.requestView(viewId, requestOptions); },
    showRenderedDocument: showRenderedDocument,
    showView: showView,
    updateInfoPanel: function () { return infoPanelController.update(); }
  };
}
