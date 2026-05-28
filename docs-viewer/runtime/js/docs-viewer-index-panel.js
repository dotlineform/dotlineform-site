export const INDEX_PANEL_STATE_COLLAPSED = "collapsed";
export const INDEX_PANEL_STATE_NORMAL = "normal";
export const INDEX_PANEL_STATE_EXPANDED = "expanded";

const INDEX_PANEL_STATES = [
  INDEX_PANEL_STATE_COLLAPSED,
  INDEX_PANEL_STATE_NORMAL,
  INDEX_PANEL_STATE_EXPANDED
];

export function normalizeIndexPanelState(value, fallback = INDEX_PANEL_STATE_NORMAL) {
  const state = String(value || "").trim();
  if (INDEX_PANEL_STATES.includes(state)) return state;
  return INDEX_PANEL_STATES.includes(fallback) ? fallback : INDEX_PANEL_STATE_NORMAL;
}

export function buildIndexPanelStorageKey(scope) {
  return `dotlineform-docs-viewer-index-panel:${normalizeStorageScope(scope)}`;
}

export function readIndexPanelState(options = {}) {
  const storage = options.storage || null;
  if (!storage) return INDEX_PANEL_STATE_NORMAL;
  const storageKey = String(options.storageKey || "");
  try {
    const stored = storageKey ? storage.getItem(storageKey) : "";
    if (stored) return normalizeIndexPanelState(stored);
  } catch (error) {
    return INDEX_PANEL_STATE_NORMAL;
  }
  return INDEX_PANEL_STATE_NORMAL;
}

export function persistIndexPanelState(options = {}) {
  const storage = options.storage || null;
  const storageKey = String(options.storageKey || "");
  if (!storage || !storageKey) return;
  try {
    storage.setItem(storageKey, normalizeIndexPanelState(options.state));
  } catch (error) {
    return;
  }
}

export function nextIndexPanelState(state) {
  const normalized = normalizeIndexPanelState(state);
  if (normalized === INDEX_PANEL_STATE_COLLAPSED) return INDEX_PANEL_STATE_NORMAL;
  if (normalized === INDEX_PANEL_STATE_EXPANDED) return INDEX_PANEL_STATE_NORMAL;
  return INDEX_PANEL_STATE_COLLAPSED;
}

export function expandedIndexPanelState(state) {
  const normalized = normalizeIndexPanelState(state);
  return normalized === INDEX_PANEL_STATE_EXPANDED ? normalized : INDEX_PANEL_STATE_EXPANDED;
}

export function projectIndexPanelState(state, options = {}) {
  const available = options.available !== false;
  const activeState = available ? normalizeIndexPanelState(state) : INDEX_PANEL_STATE_NORMAL;
  const nextState = available ? nextIndexPanelState(activeState) : INDEX_PANEL_STATE_NORMAL;
  const expanded = activeState !== INDEX_PANEL_STATE_COLLAPSED;
  const expandHidden = !available || activeState !== INDEX_PANEL_STATE_NORMAL;
  const stepIcon = activeState === INDEX_PANEL_STATE_COLLAPSED ? "›" : "‹";
  const stepLabel = activeState === INDEX_PANEL_STATE_NORMAL ? "Collapse index panel" : "Restore index panel";
  return {
    activeState,
    nextState,
    expandedState: expandedIndexPanelState(activeState),
    documentPaneVisible: activeState !== INDEX_PANEL_STATE_EXPANDED,
    toggleHidden: !available,
    toggleAriaExpanded: expanded ? "true" : "false",
    toggleIcon: stepIcon,
    toggleLabel: stepLabel,
    stepHidden: !available,
    stepAriaExpanded: expanded ? "true" : "false",
    stepIcon,
    stepLabel,
    expandHidden,
    expandAriaExpanded: "true",
    expandIcon: "⤢",
    expandLabel: "Expand index panel"
  };
}

function normalizeStorageScope(scope) {
  return String(scope || "").trim() || "docs";
}
