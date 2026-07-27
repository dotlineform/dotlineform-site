import {
  buildChildrenMap
} from "../shared/docs-viewer-tree.js";
import {
  collectDescendantDocIds
} from "./docs-viewer-management-action-workflow.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

var METADATA_TEXT = {
  parentRootOption: "Root",
  parentInvalid: "Select a parent from the search field suggestions or enter Root.",
  titleRequired: "Enter a title."
};

export function createDocsViewerManagementMetadataWorkflow(options = {}) {
  var documentIndex = options.documentIndex || {};
  var management = options.management || {};
  var refs = options.refs || {};
  var callbacks = options.callbacks || {};
  var editingTarget = null;
  var editingDoc = null;

  function modalController() {
    return typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
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
    if (!modal || !editingTarget || !editingDoc || !refs.titleInput || !refs.summaryInput || !refs.dateInput || !refs.dateDisplayInput || !refs.statusInput || !refs.nonViewableInput) return null;

    var title = String(refs.titleInput.value || "").trim();
    if (!title) {
      modal.setMetadataStatus(METADATA_TEXT.titleRequired, "error");
      refs.titleInput.focus();
      return null;
    }

    var payload = {
      title: title,
      summary: String(refs.summaryInput.value || "").replace(/\s+/g, " ").trim(),
      date: String(refs.dateInput.value || "").trim(),
      date_display: String(refs.dateDisplayInput.value || "").trim(),
      ui_status: String(refs.statusInput.value || "").trim(),
      viewable: !refs.nonViewableInput.checked
    };
    if (!editingTarget.sub_scope) {
      if (!refs.parentInput) return null;
      var parentId = modal.resolveMetadataParentId(editingDoc);
      if (parentId === null) {
        modal.setMetadataStatus(METADATA_TEXT.parentInvalid, "error");
        refs.parentInput.focus();
        return null;
      }
      payload.parent_id = parentId;
    }
    return payload;
  }

  function confirm() {
    var modal = modalController();
    var payload = payloadFromModal();
    if (modal && payload) modal.closeMetadataModal(payload);
  }

  function metadataDocFromResponse(response, target) {
    if (!response || typeof response !== "object") {
      throw new Error("Document metadata could not be loaded.");
    }
    var responseTarget = {
      scope: response.scope,
      doc_id: response.doc_id
    };
    if (Object.prototype.hasOwnProperty.call(response, "sub_scope")) {
      responseTarget.sub_scope = response.sub_scope;
    }
    if (!managedDocumentTargetsEqual(responseTarget, target)) {
      throw new Error("Loaded document metadata did not match the requested target.");
    }
    var record = response.record;
    if (!record || typeof record !== "object" || String(record.doc_id || "").trim() !== target.doc_id) {
      throw new Error("Loaded document metadata did not match the requested document.");
    }
    return record;
  }

  function clearEditingState() {
    editingTarget = null;
    editingDoc = null;
  }

  function openForTarget(target) {
    var normalizedTarget;
    try {
      normalizedTarget = normalizeManagedDocumentTarget(target);
    } catch (error) {
      if (typeof callbacks.onLoadError === "function") callbacks.onLoadError(error);
      return Promise.resolve(null);
    }
    if (typeof callbacks.loadMetadataDoc !== "function") {
      var missingLoader = new Error("Local document metadata loader is unavailable.");
      if (typeof callbacks.onLoadError === "function") callbacks.onLoadError(missingLoader);
      return Promise.resolve(null);
    }
    return Promise.resolve()
      .then(function () {
        return callbacks.loadMetadataDoc(normalizedTarget);
      })
      .then(function (response) {
        var metadataDoc = metadataDocFromResponse(response, normalizedTarget);
        editingTarget = normalizedTarget;
        editingDoc = metadataDoc;
        var modal = modalController();
        return modal ? modal.openMetadataModal(metadataDoc, {
          target: normalizedTarget,
          showParent: !normalizedTarget.sub_scope
        }) : null;
      })
      .then(function (payload) {
        if (payload && editingTarget && typeof callbacks.onSave === "function") {
          callbacks.onSave(editingTarget, payload);
        }
        clearEditingState();
        return payload;
      })
      .catch(function (error) {
        clearEditingState();
        if (typeof callbacks.onLoadError === "function") callbacks.onLoadError(error);
        return null;
      });
  }

  function refreshEditingOptions() {
    var modal = modalController();
    if (!modal || !editingTarget || !editingDoc) return;
    modal.renderMetadataStatusOptions(editingDoc);
    if (!editingTarget.sub_scope) {
      modal.renderMetadataParentOptions(editingDoc);
    }
  }

  function render() {
    if (refs.saveButton) refs.saveButton.disabled = Boolean(management.managementBusy);
  }

  return {
    confirm: confirm,
    openForTarget: openForTarget,
    parentOptions: parentOptions,
    refreshEditingOptions: refreshEditingOptions,
    render: render
  };
}
