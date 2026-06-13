function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizePanelDefaults(rawPanels) {
  var panels = rawPanels && typeof rawPanels === "object" ? rawPanels : {};
  var index = panels.index && typeof panels.index === "object" ? panels.index : {};
  var mainPanel = panels.main && typeof panels.main === "object" ? panels.main : {};
  var info = panels.info && typeof panels.info === "object" ? panels.info : {};
  return {
    index: {
      enabled: index.enabled !== false,
      defaultState: cleanString(index.defaultState || index.default_state) || "normal"
    },
    main: {
      enabled: mainPanel.enabled !== false,
      defaultView: cleanString(mainPanel.defaultView || mainPanel.default_view) || "rendered-document"
    },
    info: {
      enabled: info.enabled !== false,
      defaultView: cleanString(info.defaultView || info.default_view) || "metadata-info"
    }
  };
}

export function createDocsViewerViewState(options) {
  var settings = options || {};
  var panelDefaults = normalizePanelDefaults(settings.panels);
  return {
    routeId: cleanString(settings.routeId),
    mode: cleanString(settings.mode) || "document",
    panels: {
      index: {
        id: "index",
        enabled: panelDefaults.index.enabled,
        state: cleanString(settings.indexPanelState) || panelDefaults.index.defaultState,
        mounted: panelDefaults.index.enabled,
        activeViewId: cleanString(settings.indexViewId) || "index-tree"
      },
      main: {
        id: "main",
        enabled: panelDefaults.main.enabled,
        mounted: panelDefaults.main.enabled,
        activeViewId: cleanString(settings.mainViewId) || panelDefaults.main.defaultView
      },
      info: {
        id: "info",
        enabled: panelDefaults.info.enabled,
        mounted: false,
        activeViewId: cleanString(settings.infoViewId) || panelDefaults.info.defaultView
      }
    }
  };
}

export function updateDocsViewerViewState(viewState, patch) {
  var current = viewState || createDocsViewerViewState();
  var changes = patch || {};
  var next = {
    routeId: current.routeId,
    mode: cleanString(changes.mode) || current.mode,
    panels: {
      index: Object.assign({}, current.panels.index),
      main: Object.assign({}, current.panels.main),
      info: Object.assign({}, current.panels.info)
    }
  };
  if (changes.indexPanelState) {
    next.panels.index.state = cleanString(changes.indexPanelState);
  }
  if (changes.indexViewId) {
    next.panels.index.activeViewId = cleanString(changes.indexViewId);
  }
  if (changes.mainViewId) {
    next.panels.main.activeViewId = cleanString(changes.mainViewId);
  }
  if (changes.infoViewId) {
    next.panels.info.activeViewId = cleanString(changes.infoViewId);
  }
  if (changes.infoMounted != null) {
    next.panels.info.mounted = Boolean(changes.infoMounted) && next.panels.info.enabled;
  }
  return next;
}

export function projectDocsViewerViewState(viewState, options) {
  var settings = options || {};
  var state = viewState || createDocsViewerViewState();
  var indexProjection = settings.indexProjection || {};
  var documentPaneVisible = indexProjection.documentPaneVisible !== false;
  return {
    index: {
      panel: "index",
      visible: Boolean(state.panels.index.enabled),
      mounted: Boolean(state.panels.index.mounted),
      state: cleanString(indexProjection.activeState) || state.panels.index.state,
      activeViewId: state.panels.index.activeViewId
    },
    main: {
      panel: "main",
      visible: Boolean(state.panels.main.enabled && documentPaneVisible),
      mounted: Boolean(state.panels.main.mounted),
      activeViewId: state.panels.main.activeViewId
    },
    info: {
      panel: "info",
      visible: Boolean(state.panels.info.enabled && state.panels.info.mounted),
      mounted: Boolean(state.panels.info.mounted),
      activeViewId: state.panels.info.activeViewId
    }
  };
}
