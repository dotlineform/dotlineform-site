import {
  renderDocsViewerAppShellMainViewState,
  renderDocsViewerAppShellInfoPanelState,
  renderDocsViewerAppShellIndexPanelState
} from "./docs-viewer-app-shell.js";
import {
  createDocsViewerViewState,
  projectDocsViewerViewState,
  updateDocsViewerViewState
} from "./docs-viewer-view-state.js";

var DEFAULT_INDEX_VIEW = {
  id: "index-tree",
  label: "Index tree",
  renderer: "index-tree"
};

function normalizeMainLayoutState(value) {
  return String(value || "").trim() === "expanded-main" ? "expanded-main" : "normal";
}

/**
 * Project the index, main and info panels without saved index sizing state.
 * Content Detail can temporarily hide the index through its main-view layout.
 */
export function createDocsViewerPanelLayout(options) {
  var settings = options || {};
  var root = settings.root || null;
  var indexPanelRefs = settings.indexPanelRefs || {};
  var mainViewRefs = settings.mainViewRefs || {};
  var infoPanelRefs = settings.infoPanelRefs || {};
  var viewRegistry = settings.viewRegistry || null;
  var viewState = createDocsViewerViewState({
    panels: settings.panels,
    routeId: settings.routeId
  });
  var infoPanelProjection = {};
  var mainLayoutState = "normal";
  var treeVisible = false;

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

  function renderIndexPanelState() {
    var activeView = activeIndexView();
    if (activeView && activeView.id !== viewState.panels.index.activeViewId) {
      viewState = updateDocsViewerViewState(viewState, {
        indexViewId: activeView.id
      });
    }
    var projection = {};
    projection.activeViewId = activeView && activeView.id ? activeView.id : "";
    projection.activeViewLabel = activeView && activeView.label ? activeView.label : projection.activeViewId;
    projection.activeViewRenderer = activeView && activeView.renderer ? activeView.renderer : "";
    projection.placeholderText = activeView && activeView.placeholderText
      ? activeView.placeholderText
      : projection.activeViewLabel;
    projection.treeHidden = projection.activeViewRenderer !== "index-tree";
    projection.placeholderHidden = projection.activeViewRenderer !== "index-placeholder";
    viewState = updateDocsViewerViewState(viewState, {
      indexViewId: projection.activeViewId
    });
    renderDocsViewerAppShellIndexPanelState({
      root: root,
      refs: indexPanelRefs,
      projection: projection
    });
    if (typeof settings.onIndexProjection === "function") settings.onIndexProjection(projection);
    renderInfoPanelState();
    return projection;
  }

  function projectViewState() {
    var projected = projectDocsViewerViewState(viewState);
    projected.main.layoutState = mainLayoutState;
    if (mainLayoutState === "expanded-main") {
      projected.index.visible = false;
      projected.info.visible = false;
    }
    return projected;
  }

  function projectMainView(projection) {
    renderDocsViewerAppShellMainViewState({
      refs: mainViewRefs,
      projection: projection || {}
    });
  }

  function viewerLayoutName(projection) {
    if (mainLayoutState === "expanded-main") return "expanded-main";
    if (projection.info.visible) return "index-document-info";
    return "index-document";
  }

  function renderInfoPanelState() {
    var projected = projectViewState();
    if (indexPanelRefs.sidebar) {
      indexPanelRefs.sidebar.hidden = mainLayoutState === "expanded-main" || !projected.index.visible;
    }
    renderDocsViewerAppShellInfoPanelState({
      root: root,
      refs: infoPanelRefs,
      projection: Object.assign({}, infoPanelProjection, {
        activeViewId: projected.info.activeViewId,
        layout: viewerLayoutName(projected),
        visible: projected.info.visible
      })
    });
    var nextTreeVisible = mainLayoutState !== "expanded-main" && projected.index.visible
      && projected.index.activeViewId === "index-tree";
    if (nextTreeVisible && !treeVisible && typeof settings.onTreeVisible === "function") settings.onTreeVisible();
    treeVisible = nextTreeVisible;
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

  /** Switch visibility of retained Index content; acquisition stays with each view's owner. */
  function setActiveIndexView(viewId) {
    var resolved = viewRegistry.resolveView(viewId);
    if (!resolved.available || !resolved.view || resolved.view.panel !== "index") return null;
    viewState = updateDocsViewerViewState(viewState, { indexViewId: resolved.view.id });
    return renderIndexPanelState();
  }

  function setMainLayoutState(state) {
    mainLayoutState = normalizeMainLayoutState(state);
    renderInfoPanelState();
    return mainLayoutState;
  }

  return {
    projectInfoPanel: projectInfoPanel,
    projectMainView: projectMainView,
    projectViewState: projectViewState,
    renderIndexPanelState: renderIndexPanelState,
    setActiveMainView: setActiveMainView,
    setActiveIndexView: setActiveIndexView,
    setMainLayoutState: setMainLayoutState,
    mainLayoutState: function () { return mainLayoutState; }
  };
}
