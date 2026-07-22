import {
  buildChildrenMap
} from "../shared/docs-viewer-tree.js";
import {
  collectDescendantDocIds
} from "./docs-viewer-management-action-workflow.js";

var METADATA_TEXT = {
  parentRootOption: "Root",
  parentInvalid: "Select a parent from the search field suggestions or enter Root."
};

export function createDocsViewerManagementMetadataWorkflow(options = {}) {
  var documentIndex = options.documentIndex || {};
  var management = options.management || {};
  var refs = options.refs || {};
  var callbacks = options.callbacks || {};

  function modalController() {
    return typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
  }

  function currentActiveDoc() {
    return typeof callbacks.currentActiveDoc === "function" ? callbacks.currentActiveDoc() : null;
  }

  function parentOptions(doc) {
    var blockedIds = collectDescendantDocIds(documentIndex.allDocs, doc.doc_id, new Set([doc.doc_id]));
    var options = [{ value: "", label: METADATA_TEXT.parentRootOption }];
    var docsByParent = buildChildrenMap(documentIndex.allDocs);
    function pushChildren(parentId, depth) {
      (docsByParent.get(parentId) || []).forEach(function (candidate) {
        if (!blockedIds.has(candidate.doc_id)) {
          options.push({
            value: candidate.doc_id,
            label: (depth > 0 ? new Array(depth + 1).join("- ") : "") + candidate.title
          });
        }
        pushChildren(candidate.doc_id, depth + 1);
      });
    }
    pushChildren("", 0);
    return options;
  }

  function payloadFromModal() {
    var modal = modalController();
    var doc = management.metadataEditingDocId ? documentIndex.docsById.get(management.metadataEditingDocId) : currentActiveDoc();
    if (!modal || !doc || !refs.titleInput || !refs.summaryInput || !refs.dateInput || !refs.dateDisplayInput || !refs.statusInput || !refs.nonViewableInput || !refs.parentInput) return null;

    var title = String(refs.titleInput.value || "").trim();
    if (!title) {
      refs.titleInput.focus();
      return null;
    }

    var parentId = modal.resolveMetadataParentId(doc);
    if (parentId === null) {
      if (typeof callbacks.setManagementMessage === "function") {
        callbacks.setManagementMessage(METADATA_TEXT.parentInvalid, true);
      }
      refs.parentInput.focus();
      return null;
    }
    return {
      doc_id: doc.doc_id,
      title: title,
      summary: String(refs.summaryInput.value || "").replace(/\s+/g, " ").trim(),
      date: String(refs.dateInput.value || "").trim(),
      date_display: String(refs.dateDisplayInput.value || "").trim(),
      ui_status: String(refs.statusInput.value || "").trim(),
      viewable: !refs.nonViewableInput.checked,
      parent_id: parentId
    };
  }

  function confirm() {
    var modal = modalController();
    var payload = payloadFromModal();
    if (modal && payload) modal.closeMetadataModal(payload);
  }

  function openForDoc(doc) {
    var modal = modalController();
    var result = modal ? modal.openMetadataModal(doc) : Promise.resolve(null);
    return Promise.resolve(result).then(function (payload) {
      if (payload && typeof callbacks.onSave === "function") callbacks.onSave(payload);
      return payload;
    });
  }

  function openForDocId(docId) {
    return openForDoc(documentIndex.docsById.get(docId) || null);
  }

  function refreshEditingOptions() {
    var modal = modalController();
    if (!modal || !management.metadataEditingDocId) return;
    var doc = documentIndex.docsById.get(management.metadataEditingDocId);
    modal.renderMetadataStatusOptions(doc);
    modal.renderMetadataParentOptions(doc);
  }

  function render() {
    if (refs.saveButton) refs.saveButton.disabled = Boolean(management.managementBusy);
  }

  return {
    confirm: confirm,
    openForDocId: openForDocId,
    parentOptions: parentOptions,
    refreshEditingOptions: refreshEditingOptions,
    render: render
  };
}
