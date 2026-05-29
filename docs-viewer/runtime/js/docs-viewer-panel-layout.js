import {
  buildIndexPanelStorageKey,
  expandedIndexPanelState,
  nextIndexPanelState,
  persistIndexPanelState,
  projectIndexPanelState,
  readIndexPanelState
} from "./docs-viewer-index-panel.js";
import {
  listDocsViewerHostedViewsForPanel
} from "./docs-viewer-hosted-views.js";
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

var DEFAULT_INDEX_VIEW = {
  id: "index-tree",
  label: "Index tree",
  renderer: "index-tree",
  capabilities: {
    layoutStates: ["normal", "collapsed"],
    toolbar: false
  }
};

export function createDocsViewerPanelLayout(options) {
  var settings = options || {};
  var root = settings.root || null;
  var storage = settings.storage || null;
  var indexPanelRefs = settings.indexPanelRefs || {};
  var documentShellRefs = settings.documentShellRefs || {};
  var infoPanelRefs = settings.infoPanelRefs || {};
  var indexPanelAvailable = settings.indexPanelAvailable || function () { return true; };
  var hostedViewRegistry = settings.hostedViewRegistry || null;
  var storageScope = normalizeScope(settings.storageScope);
  var storageKey = buildIndexPanelStorageKey(storageScope);
  var indexPanelState = readStoredIndexPanelState();
  var viewState = createDocsViewerViewState({
    indexPanelState: indexPanelState,
    panels: settings.panels,
    routeId: settings.routeId
  });
  var infoPanelProjection = {};

  function indexViews() {
    return listDocsViewerHostedViewsForPanel(hostedViewRegistry, "index");
  }

  function availableIndexViews() {
    return indexViews().filter(function (view) {
      return view.available !== false;
    });
  }

  function fallbackIndexView() {
    return availableIndexViews()[0] || DEFAULT_INDEX_VIEW;
  }

  function activeIndexView() {
    var activeViewId = viewState && viewState.panels && viewState.panels.index
      ? viewState.panels.index.activeViewId
      : "";
    var resolved = hostedViewRegistry && typeof hostedViewRegistry.resolve === "function"
      ? hostedViewRegistry.resolve(activeViewId)
      : null;
    if (resolved && resolved.view) return resolved.view;
    return fallbackIndexView();
  }

  function activeIndexViewCapabilities() {
    var view = activeIndexView();
    return view && view.capabilities ? view.capabilities : null;
  }

  function viewOptionProjection(activeView) {
    var activeId = activeView && activeView.id ? activeView.id : "";
    return availableIndexViews().map(function (view) {
      return {
        id: view.id,
        label: view.label || view.id,
        active: view.id === activeId
      };
    });
  }

  function normalizeCurrentIndexState() {
    var projection = projectIndexPanelState(indexPanelState, {
      available: indexPanelAvailable(),
      capabilities: activeIndexViewCapabilities()
    });
    if (indexPanelState !== projection.activeState) {
      indexPanelState = projection.activeState;
      persistCurrentIndexPanelState();
    }
    return projection;
  }

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
      state: indexPanelState,
      capabilities: activeIndexViewCapabilities()
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
    var activeView = activeIndexView();
    if (activeView && activeView.id !== viewState.panels.index.activeViewId) {
      viewState = updateDocsViewerViewState(viewState, {
        indexViewId: activeView.id
      });
    }
    var projection = normalizeCurrentIndexState();
    projection.activeViewId = activeView && activeView.id ? activeView.id : "";
    projection.activeViewLabel = activeView && activeView.label ? activeView.label : projection.activeViewId;
    projection.activeViewRenderer = activeView && activeView.renderer ? activeView.renderer : "";
    projection.placeholderText = activeView && activeView.placeholderText
      ? activeView.placeholderText
      : projection.activeViewLabel;
    projection.treeHidden = projection.activeViewRenderer !== "index-tree";
    projection.placeholderHidden = projection.activeViewRenderer !== "index-placeholder";
    projection.viewOptions = viewOptionProjection(activeView);
    viewState = updateDocsViewerViewState(viewState, {
      indexPanelState: projection.activeState,
      indexViewId: projection.activeViewId
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
        available: indexPanelAvailable(),
        capabilities: activeIndexViewCapabilities()
      })
    });
  }

  function toggleIndexPanelState() {
    if (!indexPanelAvailable()) return indexPanelState;
    indexPanelState = nextIndexPanelState(indexPanelState, {
      capabilities: activeIndexViewCapabilities()
    });
    persistCurrentIndexPanelState();
    renderIndexPanelState();
    return indexPanelState;
  }

  function expandIndexPanelState() {
    if (!indexPanelAvailable()) return indexPanelState;
    indexPanelState = expandedIndexPanelState(indexPanelState, {
      capabilities: activeIndexViewCapabilities()
    });
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

  function setActiveIndexView(viewId) {
    var targetViewId = String(viewId || "").trim();
    var resolved = hostedViewRegistry && typeof hostedViewRegistry.resolve === "function"
      ? hostedViewRegistry.resolve(targetViewId)
      : null;
    if (!resolved || !resolved.view) return activeIndexView();
    viewState = updateDocsViewerViewState(viewState, {
      indexViewId: resolved.view.id
    });
    renderIndexPanelState();
    return resolved.view;
  }

  return {
    expandIndexPanelState: expandIndexPanelState,
    indexPanelState: function () { return indexPanelState; },
    projectInfoPanel: projectInfoPanel,
    projectDocumentShell: projectDocumentShell,
    projectViewState: projectViewState,
    renderIndexPanelState: renderIndexPanelState,
    setActiveIndexView: setActiveIndexView,
    setStorageScope: setStorageScope,
    toggleIndexPanelState: toggleIndexPanelState
  };
}
