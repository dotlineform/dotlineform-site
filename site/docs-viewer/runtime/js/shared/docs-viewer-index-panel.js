import {
  firstHostedViewLayoutState,
  hostedViewSupportsLayoutState
} from "./docs-viewer-hosted-view-capabilities.js";

export const INDEX_PANEL_STATE_COLLAPSED = "collapsed";
export const INDEX_PANEL_STATE_NORMAL = "normal";
export const INDEX_PANEL_STATE_EXPANDED = "expanded";

const INDEX_PANEL_STATES = [
  INDEX_PANEL_STATE_COLLAPSED,
  INDEX_PANEL_STATE_NORMAL,
  INDEX_PANEL_STATE_EXPANDED
];

export function normalizeIndexPanelState(value, fallback = INDEX_PANEL_STATE_NORMAL, options = {}) {
  const state = String(value || "").trim();
  const capabilities = options.capabilities || null;
  if (INDEX_PANEL_STATES.includes(state) && (!capabilities || hostedViewSupportsLayoutState(capabilities, state))) return state;
  if (INDEX_PANEL_STATES.includes(fallback) && (!capabilities || hostedViewSupportsLayoutState(capabilities, fallback))) return fallback;
  if (capabilities) return firstHostedViewLayoutState(capabilities, INDEX_PANEL_STATE_NORMAL);
  return INDEX_PANEL_STATE_NORMAL;
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
    storage.setItem(storageKey, normalizeIndexPanelState(options.state, INDEX_PANEL_STATE_NORMAL, {
      capabilities: options.capabilities
    }));
  } catch (error) {
    return;
  }
}

export function nextIndexPanelState(state, options = {}) {
  const capabilities = options.capabilities || null;
  const normalized = normalizeIndexPanelState(state, INDEX_PANEL_STATE_NORMAL, { capabilities });
  const normal = normalizeIndexPanelState(INDEX_PANEL_STATE_NORMAL, INDEX_PANEL_STATE_NORMAL, { capabilities });
  if (normalized === INDEX_PANEL_STATE_COLLAPSED) return normal;
  if (normalized === INDEX_PANEL_STATE_EXPANDED) return normal;
  if (!capabilities || hostedViewSupportsLayoutState(capabilities, INDEX_PANEL_STATE_COLLAPSED)) {
    return INDEX_PANEL_STATE_COLLAPSED;
  }
  return normal;
}

export function expandedIndexPanelState(state, options = {}) {
  const capabilities = options.capabilities || null;
  const normalized = normalizeIndexPanelState(state, INDEX_PANEL_STATE_NORMAL, { capabilities });
  if (capabilities && !hostedViewSupportsLayoutState(capabilities, INDEX_PANEL_STATE_EXPANDED)) return normalized;
  return normalized === INDEX_PANEL_STATE_EXPANDED ? normalized : INDEX_PANEL_STATE_EXPANDED;
}

export function projectIndexPanelState(state, options = {}) {
  const available = options.available !== false;
  const capabilities = options.capabilities || null;
  const activeState = available
    ? normalizeIndexPanelState(state, INDEX_PANEL_STATE_NORMAL, { capabilities })
    : INDEX_PANEL_STATE_NORMAL;
  const nextState = available ? nextIndexPanelState(activeState, { capabilities }) : INDEX_PANEL_STATE_NORMAL;
  const expanded = activeState !== INDEX_PANEL_STATE_COLLAPSED;
  const collapseAllowed = !capabilities || hostedViewSupportsLayoutState(capabilities, INDEX_PANEL_STATE_COLLAPSED);
  const expandAllowed = !capabilities || hostedViewSupportsLayoutState(capabilities, INDEX_PANEL_STATE_EXPANDED);
  const expandHidden = !available || !expandAllowed || activeState !== INDEX_PANEL_STATE_NORMAL;
  const stepHidden = !available || (activeState === INDEX_PANEL_STATE_NORMAL && !collapseAllowed);
  const stepIcon = activeState === INDEX_PANEL_STATE_COLLAPSED ? "›" : "‹";
  const stepLabel = activeState === INDEX_PANEL_STATE_NORMAL ? "Collapse index panel" : "Restore index panel";
  return {
    activeState,
    nextState,
    expandedState: expandedIndexPanelState(activeState, { capabilities }),
    documentPaneVisible: activeState !== INDEX_PANEL_STATE_EXPANDED,
    toggleHidden: !available,
    toggleAriaExpanded: expanded ? "true" : "false",
    toggleIcon: stepIcon,
    toggleLabel: stepLabel,
    stepHidden,
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
