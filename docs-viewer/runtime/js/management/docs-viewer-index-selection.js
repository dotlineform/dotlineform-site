import {
  clearDocsViewerSelection,
  createDocsViewerSelectionState,
  enterDocsViewerSelection,
  exitDocsViewerSelection,
  normalizeDocsViewerSelectionDocIds,
  reconcileDocsViewerSelection,
  selectAllDocsViewerSelection,
  selectDocsViewerSelectionRange,
  toggleDocsViewerSelection
} from "./docs-viewer-selection-rules.js";

function normalizeDocId(value) {
  return String(value == null ? "" : value).trim();
}

export function createDocsViewerIndexSelectionState(options = {}) {
  return createDocsViewerSelectionState(options);
}

export function enterDocsViewerIndexSelection(state) {
  return enterDocsViewerSelection(state);
}

export function toggleDocsViewerIndexSelection(state, docId, checked) {
  return toggleDocsViewerSelection(state, docId, checked);
}

export function selectDocsViewerIndexSelectionRange(state, docId, visibleDocIds) {
  return selectDocsViewerSelectionRange(state, docId, visibleDocIds);
}

export function clearDocsViewerIndexSelection(state) {
  return clearDocsViewerSelection(state);
}

export function selectAllDocsViewerIndexSelection(state, eligibleDocIds) {
  return selectAllDocsViewerSelection(state, eligibleDocIds);
}

export function exitDocsViewerIndexSelection() {
  return exitDocsViewerSelection();
}

export function reconcileDocsViewerIndexSelection(state, eligibleDocIds) {
  return reconcileDocsViewerSelection(state, eligibleDocIds);
}

export function createDocsViewerIndexSelectionOwner(options = {}) {
  var current = createDocsViewerIndexSelectionState(options.initialState);
  var owningScopeId = normalizeDocId(options.initialScopeId);

  function transition(nextState) {
    current = nextState;
    return current;
  }

  function lifecycleContext(contextOptions) {
    var context = contextOptions || {};
    return {
      scopeId: normalizeDocId(context.scopeId),
      managementContext: Boolean(context.managementContext),
      indexViewId: normalizeDocId(context.indexViewId)
    };
  }

  function syncContext(contextOptions) {
    var context = lifecycleContext(contextOptions);
    var scopeChanged = context.scopeId !== owningScopeId;
    owningScopeId = context.scopeId;
    if (
      scopeChanged
      || !context.scopeId
      || !context.managementContext
      || context.indexViewId !== "index-tree"
    ) {
      return transition(exitDocsViewerIndexSelection());
    }
    return current;
  }

  return Object.freeze({
    snapshot: function () { return current; },
    selectedDocIds: function () { return current.selectedDocIds.slice(); },
    enter: function () { return transition(enterDocsViewerIndexSelection(current)); },
    toggle: function (docId, checked) {
      return transition(toggleDocsViewerIndexSelection(current, docId, checked));
    },
    selectRange: function (docId, visibleDocIds) {
      return transition(selectDocsViewerIndexSelectionRange(current, docId, visibleDocIds));
    },
    selectAll: function (eligibleDocIds) {
      return transition(selectAllDocsViewerIndexSelection(current, eligibleDocIds));
    },
    clear: function () { return transition(clearDocsViewerIndexSelection(current)); },
    exit: function () { return transition(exitDocsViewerIndexSelection()); },
    reconcile: function (eligibleDocIds) {
      return transition(reconcileDocsViewerIndexSelection(current, eligibleDocIds));
    },
    reconcileReload: function (eligibleDocIds, contextOptions) {
      var context = lifecycleContext(contextOptions);
      syncContext(context);
      if (
        context.scopeId
        && context.managementContext
        && context.indexViewId === "index-tree"
      ) {
        return transition(reconcileDocsViewerIndexSelection(current, eligibleDocIds));
      }
      return current;
    },
    syncContext: syncContext
  });
}

export function createDocsViewerIndexSelectionGutter(options = {}) {
  var documentRef = options.document || document;
  var doc = options.doc && typeof options.doc === "object" ? options.doc : {};
  var docId = normalizeDocId(doc.doc_id);
  var state = createDocsViewerIndexSelectionState(options.state);
  var gutter = documentRef.createElement("span");
  gutter.className = "docsViewer__indexSelectionGutter";
  gutter.dataset.docsViewerSelectionGutter = docId;
  gutter.hidden = !state.selectionModeActive;

  var checkbox = documentRef.createElement("input");
  checkbox.className = "docsViewer__indexSelectionCheckbox";
  checkbox.type = "checkbox";
  checkbox.dataset.docsViewerSelectionCheckbox = docId;
  checkbox.checked = state.selectedDocIds.indexOf(docId) !== -1;
  checkbox.disabled = Boolean(options.disabled);
  checkbox.setAttribute("aria-label", "Select " + (normalizeDocId(doc.title) || docId));
  gutter.appendChild(checkbox);
  return gutter;
}

export function projectDocsViewerIndexSelectionRows(options = {}) {
  var nav = options.nav || null;
  var state = createDocsViewerIndexSelectionState(options.state);
  var selected = new Set(state.selectedDocIds);
  if (!nav) return state;
  nav.querySelectorAll("[data-docs-viewer-selection-gutter]").forEach(function (gutter) {
    var checkbox = gutter.querySelector("[data-docs-viewer-selection-checkbox]");
    var docId = normalizeDocId(gutter.dataset.docsViewerSelectionGutter);
    gutter.hidden = !state.selectionModeActive;
    if (!checkbox) return;
    checkbox.checked = selected.has(docId);
    checkbox.disabled = Boolean(options.disabled);
  });
  return state;
}

export function visibleDocsViewerIndexSelectionDocIds(nav) {
  if (!nav) return [];
  return normalizeDocsViewerSelectionDocIds(Array.from(nav.querySelectorAll("[data-docs-viewer-selection-checkbox]"))
    .filter(function (checkbox) {
      var gutter = checkbox.closest("[data-docs-viewer-selection-gutter]");
      return gutter && !gutter.hidden && !checkbox.hidden;
    })
    .map(function (checkbox) { return checkbox.dataset.docsViewerSelectionCheckbox; }));
}
