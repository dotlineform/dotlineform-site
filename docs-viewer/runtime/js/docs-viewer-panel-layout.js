import {
  buildIndexPanelStorageKey,
  expandedIndexPanelState,
  nextIndexPanelState,
  persistIndexPanelState,
  projectIndexPanelState,
  readIndexPanelState
} from "./docs-viewer-index-panel.js";
import {
  renderDocsViewerAppShellDocumentState,
  renderDocsViewerAppShellInfoPanelState,
  renderDocsViewerAppShellIndexPanelState
} from "./docs-viewer-app-shell.js";
import {
  createDocsViewerViewState,
  projectDocsViewerViewState,
  updateDocsViewerViewState
} from "./docs-viewer-view-state.js";

function normalizeScope(scope) {
  return String(scope || "").trim() || "docs";
}

export function createDocsViewerPanelLayout(options) {
  var settings = options || {};
  var root = settings.root || null;
  var storage = settings.storage || null;
  var indexPanelRefs = settings.indexPanelRefs || {};
  var documentShellRefs = settings.documentShellRefs || {};
  var infoPanelRefs = settings.infoPanelRefs || {};
  var indexPanelAvailable = settings.indexPanelAvailable || function () { return true; };
  var storageScope = normalizeScope(settings.storageScope);
  var storageKey = buildIndexPanelStorageKey(storageScope);
  var indexPanelState = readStoredIndexPanelState();
  var viewState = createDocsViewerViewState({
    indexPanelState: indexPanelState,
    panels: settings.panels,
    routeId: settings.routeId
  });
  var infoPanelProjection = {};

  function readStoredIndexPanelState() {
    return readIndexPanelState({
      storage: storage,
      storageKey: storageKey
    });
  }

  function persistCurrentIndexPanelState() {
    persistIndexPanelState({
      storage: storage,
      storageKey: storageKey,
      state: indexPanelState
    });
  }

  function setStorageScope(scope) {
    storageScope = normalizeScope(scope);
    storageKey = buildIndexPanelStorageKey(storageScope);
    indexPanelState = readStoredIndexPanelState();
    viewState = updateDocsViewerViewState(viewState, {
      indexPanelState: indexPanelState
    });
    return indexPanelState;
  }

  function renderIndexPanelState() {
    var projection = projectIndexPanelState(indexPanelState, {
      available: indexPanelAvailable()
    });
    viewState = updateDocsViewerViewState(viewState, {
      indexPanelState: projection.activeState
    });
    renderDocsViewerAppShellIndexPanelState({
      root: root,
      refs: indexPanelRefs,
      projection: projection
    });
    renderInfoPanelState();
    return projection;
  }

  function projectViewState() {
    return projectDocsViewerViewState(viewState, {
      indexProjection: projectIndexPanelState(indexPanelState, {
        available: indexPanelAvailable()
      })
    });
  }

  function toggleIndexPanelState() {
    if (!indexPanelAvailable()) return indexPanelState;
    indexPanelState = nextIndexPanelState(indexPanelState);
    persistCurrentIndexPanelState();
    renderIndexPanelState();
    return indexPanelState;
  }

  function expandIndexPanelState() {
    if (!indexPanelAvailable()) return indexPanelState;
    indexPanelState = expandedIndexPanelState(indexPanelState);
    persistCurrentIndexPanelState();
    renderIndexPanelState();
    return indexPanelState;
  }

  function projectDocumentShell(projection) {
    renderDocsViewerAppShellDocumentState({
      refs: documentShellRefs,
      projection: projection || {}
    });
  }

  function viewerLayoutName(projection) {
    if (projection.index.state === "expanded") return "index-expanded";
    if (projection.info.visible) return "index-document-info";
    return "index-document";
  }

  function renderInfoPanelState() {
    var projected = projectViewState();
    renderDocsViewerAppShellInfoPanelState({
      root: root,
      refs: infoPanelRefs,
      projection: Object.assign({}, infoPanelProjection, {
        activeViewId: projected.info.activeViewId,
        layout: viewerLayoutName(projected),
        visible: projected.info.visible
      })
    });
    return projected.info;
  }

  function projectInfoPanel(projection) {
    infoPanelProjection = Object.assign({}, infoPanelProjection, projection || {});
    viewState = updateDocsViewerViewState(viewState, {
      infoMounted: infoPanelProjection.visible === true,
      infoViewId: infoPanelProjection.activeViewId
    });
    return renderInfoPanelState();
  }

  return {
    expandIndexPanelState: expandIndexPanelState,
    indexPanelState: function () { return indexPanelState; },
    projectInfoPanel: projectInfoPanel,
    projectDocumentShell: projectDocumentShell,
    projectViewState: projectViewState,
    renderIndexPanelState: renderIndexPanelState,
    setStorageScope: setStorageScope,
    toggleIndexPanelState: toggleIndexPanelState
  };
}
