function normalizeDocId(value) {
  return String(value == null ? "" : value).trim();
}

export function normalizeDocsViewerSelectionDocIds(values) {
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
    selectedDocIds: Object.freeze(active ? normalizeDocsViewerSelectionDocIds(selectedDocIds) : []),
    rangeAnchorDocId: active ? normalizeDocId(rangeAnchorDocId) : ""
  });
}

export function createDocsViewerSelectionState(options = {}) {
  return selectionState(
    options.selectionModeActive,
    options.selectedDocIds,
    options.rangeAnchorDocId
  );
}

export function enterDocsViewerSelection(state) {
  var current = createDocsViewerSelectionState(state);
  return selectionState(true, current.selectedDocIds, current.rangeAnchorDocId);
}

export function toggleDocsViewerSelection(state, docId, checked) {
  var current = createDocsViewerSelectionState(state);
  var normalizedDocId = normalizeDocId(docId);
  if (!current.selectionModeActive || !normalizedDocId) return current;

  var nextIds = current.selectedDocIds.slice();
  var currentIndex = nextIds.indexOf(normalizedDocId);
  var shouldCheck = typeof checked === "boolean" ? checked : currentIndex === -1;
  if (shouldCheck && currentIndex === -1) nextIds.push(normalizedDocId);
  if (!shouldCheck && currentIndex !== -1) nextIds.splice(currentIndex, 1);
  return selectionState(true, nextIds, normalizedDocId);
}

export function selectDocsViewerSelectionRange(state, docId, visibleDocIds) {
  var current = createDocsViewerSelectionState(state);
  var normalizedDocId = normalizeDocId(docId);
  var visibleIds = normalizeDocsViewerSelectionDocIds(visibleDocIds);
  if (!current.selectionModeActive || !normalizedDocId || visibleIds.indexOf(normalizedDocId) === -1) {
    return current;
  }

  var anchorIndex = visibleIds.indexOf(current.rangeAnchorDocId);
  if (anchorIndex === -1) {
    return toggleDocsViewerSelection(current, normalizedDocId);
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

export function clearDocsViewerSelection(state) {
  var current = createDocsViewerSelectionState(state);
  return selectionState(current.selectionModeActive, [], "");
}

export function selectAllDocsViewerSelection(state, visibleEligibleDocIds) {
  var current = createDocsViewerSelectionState(state);
  if (!current.selectionModeActive) return current;
  return selectionState(true, visibleEligibleDocIds, "");
}

export function exitDocsViewerSelection() {
  return selectionState(false, [], "");
}

export function reconcileDocsViewerSelection(state, eligibleDocIds) {
  var current = createDocsViewerSelectionState(state);
  if (!current.selectionModeActive) return current;

  var eligible = new Set(normalizeDocsViewerSelectionDocIds(eligibleDocIds));
  return selectionState(
    true,
    current.selectedDocIds.filter(function (docId) { return eligible.has(docId); }),
    eligible.has(current.rangeAnchorDocId) ? current.rangeAnchorDocId : ""
  );
}
