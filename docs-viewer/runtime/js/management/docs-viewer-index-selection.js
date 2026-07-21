function normalizeDocId(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeDocIds(values) {
  var seen = new Set();
  return (Array.isArray(values) ? values : []).map(normalizeDocId).filter(function (docId) {
    if (!docId || seen.has(docId)) return false;
    seen.add(docId);
    return true;
  });
}

function selectionState(selectionModeActive, selectedDocIds, rangeAnchorDocId) {
  var active = Boolean(selectionModeActive);
  return Object.freeze({
    selectionModeActive: active,
    selectedDocIds: Object.freeze(active ? normalizeDocIds(selectedDocIds) : []),
    rangeAnchorDocId: active ? normalizeDocId(rangeAnchorDocId) : ""
  });
}

export function createDocsViewerIndexSelectionState(options = {}) {
  return selectionState(
    options.selectionModeActive,
    options.selectedDocIds,
    options.rangeAnchorDocId
  );
}

export function enterDocsViewerIndexSelection(state) {
  var current = createDocsViewerIndexSelectionState(state);
  return selectionState(true, current.selectedDocIds, current.rangeAnchorDocId);
}

export function toggleDocsViewerIndexSelection(state, docId, checked) {
  var current = createDocsViewerIndexSelectionState(state);
  var normalizedDocId = normalizeDocId(docId);
  if (!current.selectionModeActive || !normalizedDocId) return current;

  var nextIds = current.selectedDocIds.slice();
  var currentIndex = nextIds.indexOf(normalizedDocId);
  var shouldCheck = typeof checked === "boolean" ? checked : currentIndex === -1;
  if (shouldCheck && currentIndex === -1) nextIds.push(normalizedDocId);
  if (!shouldCheck && currentIndex !== -1) nextIds.splice(currentIndex, 1);
  return selectionState(true, nextIds, normalizedDocId);
}

export function selectDocsViewerIndexSelectionRange(state, docId, visibleDocIds) {
  var current = createDocsViewerIndexSelectionState(state);
  var normalizedDocId = normalizeDocId(docId);
  var visibleIds = normalizeDocIds(visibleDocIds);
  if (!current.selectionModeActive || !normalizedDocId || visibleIds.indexOf(normalizedDocId) === -1) {
    return current;
  }

  var anchorIndex = visibleIds.indexOf(current.rangeAnchorDocId);
  if (anchorIndex === -1) {
    return toggleDocsViewerIndexSelection(current, normalizedDocId);
  }

  var docIndex = visibleIds.indexOf(normalizedDocId);
  var rangeStart = Math.min(anchorIndex, docIndex);
  var rangeEnd = Math.max(anchorIndex, docIndex);
  var nextIds = current.selectedDocIds.slice();
  visibleIds.slice(rangeStart, rangeEnd + 1).forEach(function (visibleDocId) {
    if (nextIds.indexOf(visibleDocId) === -1) nextIds.push(visibleDocId);
  });
  return selectionState(true, nextIds, current.rangeAnchorDocId);
}

export function clearDocsViewerIndexSelection(state) {
  var current = createDocsViewerIndexSelectionState(state);
  return selectionState(current.selectionModeActive, [], "");
}

export function exitDocsViewerIndexSelection() {
  return selectionState(false, [], "");
}

export function reconcileDocsViewerIndexSelection(state, eligibleDocIds) {
  var current = createDocsViewerIndexSelectionState(state);
  if (!current.selectionModeActive) return current;

  var eligible = new Set(normalizeDocIds(eligibleDocIds));
  return selectionState(
    true,
    current.selectedDocIds.filter(function (docId) { return eligible.has(docId); }),
    eligible.has(current.rangeAnchorDocId) ? current.rangeAnchorDocId : ""
  );
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
  return normalizeDocIds(Array.from(nav.querySelectorAll("[data-docs-viewer-selection-checkbox]"))
    .filter(function (checkbox) {
      var gutter = checkbox.closest("[data-docs-viewer-selection-gutter]");
      return gutter && !gutter.hidden && !checkbox.hidden;
    })
    .map(function (checkbox) { return checkbox.dataset.docsViewerSelectionCheckbox; }));
}
