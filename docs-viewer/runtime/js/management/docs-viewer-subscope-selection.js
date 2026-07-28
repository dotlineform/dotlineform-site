import {
  clearDocsViewerSelection,
  createDocsViewerSelectionState,
  enterDocsViewerSelection,
  exitDocsViewerSelection,
  reconcileDocsViewerSelection,
  selectAllDocsViewerSelection,
  selectDocsViewerSelectionRange,
  toggleDocsViewerSelection
} from "./docs-viewer-selection-rules.js";

function normalizeCollectionId(value) {
  return String(value == null ? "" : value).trim().toLowerCase();
}

function normalizeCollection(collection) {
  var record = collection && typeof collection === "object" ? collection : {};
  return Object.freeze({
    scope: normalizeCollectionId(record.scope),
    sub_scope: normalizeCollectionId(record.sub_scope)
  });
}

function collectionKey(collection) {
  var normalized = normalizeCollection(collection);
  return normalized.scope && normalized.sub_scope
    ? normalized.scope + "\n" + normalized.sub_scope
    : "";
}

function documentIds(documents) {
  return (Array.isArray(documents) ? documents : []).map(function (documentRecord) {
    if (documentRecord && typeof documentRecord === "object") return documentRecord.doc_id;
    return documentRecord;
  });
}

export function createDocsViewerSubscopeSelectionOwner(options = {}) {
  var current = createDocsViewerSelectionState(options.initialState);
  var owningCollection = normalizeCollection(options.collection);
  var owningCollectionKey = collectionKey(owningCollection);
  var managementContext = Boolean(options.managementContext);
  var mounted = Boolean(options.mounted);

  function transition(nextState) {
    current = nextState;
    return current;
  }

  function available() {
    return Boolean(owningCollectionKey && managementContext && mounted);
  }

  function clearUnavailableState() {
    if (!available()) transition(exitDocsViewerSelection());
    return current;
  }

  function syncContext(contextOptions) {
    var context = contextOptions && typeof contextOptions === "object" ? contextOptions : {};
    if (Object.prototype.hasOwnProperty.call(context, "collection")) {
      var nextCollection = normalizeCollection(context.collection);
      var nextCollectionKey = collectionKey(nextCollection);
      if (nextCollectionKey !== owningCollectionKey) transition(exitDocsViewerSelection());
      owningCollection = nextCollection;
      owningCollectionKey = nextCollectionKey;
    }
    if (Object.prototype.hasOwnProperty.call(context, "managementContext")) {
      managementContext = Boolean(context.managementContext);
    }
    if (Object.prototype.hasOwnProperty.call(context, "mounted")) {
      mounted = Boolean(context.mounted);
    }
    return clearUnavailableState();
  }

  function notify(event, contextOptions) {
    var lifecycleEvent = event && typeof event === "object" ? event : {};
    var type = String(lifecycleEvent.type || "").trim().toLowerCase();
    var context = Object.assign({}, contextOptions || {});
    if (Object.prototype.hasOwnProperty.call(lifecycleEvent, "collection")) {
      context.collection = lifecycleEvent.collection;
    }
    if (type === "mount") context.mounted = true;
    if (type === "unmount") context.mounted = false;
    syncContext(context);
    if (!available()) return current;
    if (type === "refresh") {
      return transition(reconcileDocsViewerSelection(
        current,
        documentIds(lifecycleEvent.documents)
      ));
    }
    return current;
  }

  clearUnavailableState();
  return Object.freeze({
    available: available,
    clear: function () {
      if (!available()) return current;
      return transition(clearDocsViewerSelection(current));
    },
    collection: function () { return owningCollection; },
    done: function () { return transition(exitDocsViewerSelection()); },
    enter: function () {
      if (!available()) return current;
      return transition(enterDocsViewerSelection(current));
    },
    notify: notify,
    selectAll: function (visibleEligibleDocIds) {
      if (!available()) return current;
      return transition(selectAllDocsViewerSelection(current, visibleEligibleDocIds));
    },
    selectedDocIds: function () { return current.selectedDocIds.slice(); },
    selectRange: function (docId, visibleEligibleDocIds) {
      if (!available()) return current;
      return transition(selectDocsViewerSelectionRange(
        current,
        docId,
        visibleEligibleDocIds
      ));
    },
    snapshot: function () { return current; },
    syncContext: syncContext,
    toggle: function (docId, checked) {
      if (!available()) return current;
      return transition(toggleDocsViewerSelection(current, docId, checked));
    }
  });
}
