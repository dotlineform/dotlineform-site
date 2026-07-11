import {
  buildIndexPanelStorageKey,
  expandedIndexPanelState,
  nextIndexPanelState,
  persistIndexPanelState,
  projectIndexPanelState,
  readIndexPanelState
} from "./docs-viewer-index-panel.js";
import {
  renderDocsViewerAppShellMainViewState,
  renderDocsViewerAppShellIndexViewToggleState,
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
  var indexViewToggleRefs = settings.indexViewToggleRefs || {};
  var mainViewRefs = settings.mainViewRefs || {};
  var infoPanelRefs = settings.infoPanelRefs || {};
  var indexPanelAvailable = settings.indexPanelAvailable || function () { return true; };
  var viewRegistry = settings.viewRegistry || null;
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
    return viewRegistry ? viewRegistry.listViews("index") : [];
  }

  function availableIndexViews() {
    return indexViews().filter(function (view) {
      return view.available !== false;
    });
  }

  function mainViews() {
    return viewRegistry ? viewRegistry.listViews("main") : [];
  }

  function availableMainViews() {
    return mainViews().filter(function (view) {
      return view.available !== false;
    });
  }

  function fallbackMainView() {
    return availableMainViews()[0] || null;
  }

  function fallbackIndexView() {
    return availableIndexViews()[0] || DEFAULT_INDEX_VIEW;
  }

  function activeIndexView() {
    var activeViewId = viewState && viewState.panels && viewState.panels.index
      ? viewState.panels.index.activeViewId
      : "";
    var resolved = viewRegistry && typeof viewRegistry.resolveView === "function"
      ? viewRegistry.resolveView(activeViewId)
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

  function nextIndexViewId(activeView) {
    var options = availableIndexViews();
    if (options.length <= 1) return "";
    var activeId = activeView && activeView.id ? activeView.id : "";
    var activeIndex = options.findIndex(function (view) {
      return view.id === activeId;
    });
    var next = options[(activeIndex + 1) % options.length] || null;
    return next && next.id ? next.id : "";
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
    projection.nextViewId = nextIndexViewId(activeView);
    projection.placeholderText = activeView && activeView.placeholderText
      ? activeView.placeholderText
      : projection.activeViewLabel;
    projection.treeHidden = projection.activeViewRenderer !== "index-tree";
    projection.placeholderHidden = projection.activeViewRenderer !== "index-placeholder";
    projection.toggleHidden = !projection.nextViewId;
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
    renderDocsViewerAppShellIndexViewToggleState({
      refs: indexViewToggleRefs,
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

  function projectMainView(projection) {
    renderDocsViewerAppShellMainViewState({
      refs: mainViewRefs,
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
    var resolved = viewRegistry && typeof viewRegistry.resolveView === "function"
      ? viewRegistry.resolveView(targetViewId)
      : null;
    if (!resolved || !resolved.view) return activeIndexView();
    viewState = updateDocsViewerViewState(viewState, {
      indexViewId: resolved.view.id
    });
    renderIndexPanelState();
    return resolved.view;
  }

  function setActiveMainView(viewId) {
    var targetViewId = String(viewId || "").trim();
    var resolved = viewRegistry && typeof viewRegistry.resolveView === "function"
      ? viewRegistry.resolveView(targetViewId)
      : null;
    if (!resolved || !resolved.view) {
      return fallbackMainView();
    }
    viewState = updateDocsViewerViewState(viewState, {
      mainViewId: resolved.view.id
    });
    return resolved.view;
  }

  return {
    expandIndexPanelState: expandIndexPanelState,
    indexPanelState: function () { return indexPanelState; },
    projectInfoPanel: projectInfoPanel,
    projectMainView: projectMainView,
    projectViewState: projectViewState,
    renderIndexPanelState: renderIndexPanelState,
    setActiveIndexView: setActiveIndexView,
    setActiveMainView: setActiveMainView,
    setStorageScope: setStorageScope,
    toggleIndexPanelState: toggleIndexPanelState
  };
}
