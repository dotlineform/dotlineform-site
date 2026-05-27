import {
  buildIndexPanelStorageKey,
  buildLegacySidebarStorageKey,
  expandedIndexPanelState,
  nextIndexPanelState,
  persistIndexPanelState,
  projectIndexPanelState,
  readIndexPanelState
} from "./docs-viewer-index-panel.js";
import {
  renderDocsViewerAppShellDocumentState,
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
  var indexPanelAvailable = settings.indexPanelAvailable || function () { return true; };
  var storageScope = normalizeScope(settings.storageScope);
  var storageKey = buildIndexPanelStorageKey(storageScope);
  var legacyStorageKey = buildLegacySidebarStorageKey(storageScope);
  var indexPanelState = readStoredIndexPanelState();
  var viewState = createDocsViewerViewState({
    indexPanelState: indexPanelState,
    panels: settings.panels,
    routeId: settings.routeId
  });

  function readStoredIndexPanelState() {
    return readIndexPanelState({
      storage: storage,
      storageKey: storageKey,
      legacyStorageKey: legacyStorageKey
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
    legacyStorageKey = buildLegacySidebarStorageKey(storageScope);
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

  return {
    expandIndexPanelState: expandIndexPanelState,
    indexPanelState: function () { return indexPanelState; },
    projectDocumentShell: projectDocumentShell,
    projectViewState: projectViewState,
    renderIndexPanelState: renderIndexPanelState,
    setStorageScope: setStorageScope,
    toggleIndexPanelState: toggleIndexPanelState
  };
}
