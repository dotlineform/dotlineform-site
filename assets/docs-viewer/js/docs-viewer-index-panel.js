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

export function buildLegacySidebarStorageKey(scope) {
  return `dotlineform-docs-viewer-sidebar:${normalizeStorageScope(scope)}`;
}

export function readIndexPanelState(options = {}) {
  const storage = options.storage || null;
  if (!storage) return INDEX_PANEL_STATE_NORMAL;
  const storageKey = String(options.storageKey || "");
  const legacyStorageKey = String(options.legacyStorageKey || "");
  try {
    const stored = storageKey ? storage.getItem(storageKey) : "";
    if (stored) return normalizeIndexPanelState(stored);
    const legacyStored = legacyStorageKey ? storage.getItem(legacyStorageKey) : "";
    if (legacyStored === INDEX_PANEL_STATE_COLLAPSED) return INDEX_PANEL_STATE_COLLAPSED;
    if (legacyStored === INDEX_PANEL_STATE_EXPANDED) return INDEX_PANEL_STATE_NORMAL;
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
  const index = INDEX_PANEL_STATES.indexOf(normalized);
  return INDEX_PANEL_STATES[(index + 1) % INDEX_PANEL_STATES.length];
}

export function projectIndexPanelState(state, options = {}) {
  const available = options.available !== false;
  const activeState = available ? normalizeIndexPanelState(state) : INDEX_PANEL_STATE_NORMAL;
  const nextState = available ? nextIndexPanelState(activeState) : INDEX_PANEL_STATE_NORMAL;
  const expanded = activeState !== INDEX_PANEL_STATE_COLLAPSED;
  return {
    activeState,
    nextState,
    documentPaneVisible: activeState !== INDEX_PANEL_STATE_EXPANDED,
    legacySidebarState: activeState === INDEX_PANEL_STATE_COLLAPSED ? INDEX_PANEL_STATE_COLLAPSED : INDEX_PANEL_STATE_EXPANDED,
    toggleHidden: !available,
    toggleAriaExpanded: expanded ? "true" : "false",
    toggleIcon: iconForNextState(nextState),
    toggleLabel: labelForNextState(nextState)
  };
}

function normalizeStorageScope(scope) {
  return String(scope || "").trim() || "docs";
}

function labelForNextState(state) {
  if (state === INDEX_PANEL_STATE_COLLAPSED) return "Collapse index panel";
  if (state === INDEX_PANEL_STATE_EXPANDED) return "Expand index panel";
  return "Restore index panel";
}

function iconForNextState(state) {
  if (state === INDEX_PANEL_STATE_COLLAPSED) return "‹";
  if (state === INDEX_PANEL_STATE_EXPANDED) return "⤢";
  return "›";
}
