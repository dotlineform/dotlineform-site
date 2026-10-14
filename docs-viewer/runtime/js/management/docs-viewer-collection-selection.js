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

export function createDocsViewerCollectionSelectionOwner(options = {}) {
  var current = createDocsViewerSelectionState(options.initialState);
  var owningCollection = options.collection || Object.freeze({ collection: "" });
  var owningCollectionKey = owningCollection.collection;
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
      var nextCollection = context.collection;
      var nextCollectionKey = nextCollection.collection;
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
    var type = lifecycleEvent.type;
    var context = Object.assign({}, contextOptions || {});
    if (Object.prototype.hasOwnProperty.call(lifecycleEvent, "collection")) {
      context.collection = lifecycleEvent.collection;
    }
    if (type === "mount") context.mounted = true;
    if (type === "unmount") context.mounted = false;
    syncContext(context);
    if (!available()) return current;
    if (type === "refresh" && lifecycleEvent.membershipChanged) {
      return transition(reconcileDocsViewerSelection(
        current,
        lifecycleEvent.docIds
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
    restore: function (saved, docIds) {
      if (!available()) return current;
      return transition(reconcileDocsViewerSelection(createDocsViewerSelectionState(saved), docIds));
    },
    syncContext: syncContext,
    toggle: function (docId, checked) {
      if (!available()) return current;
      return transition(toggleDocsViewerSelection(current, docId, checked));
    }
  });
}
