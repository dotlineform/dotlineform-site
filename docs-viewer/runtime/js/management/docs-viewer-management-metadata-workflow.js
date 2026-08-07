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
  var editingChoices = null;
  var editingRevision = "";

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
    if (!modal || !editingTarget || !editingDoc || !refs.titleInput || !refs.summaryInput || !refs.dateInput || !refs.dateDisplayInput || !refs.statusInput) return null;

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
      ui_status: String(refs.statusInput.value || "").trim()
    };
    if (editingRevision) payload.source_revision = editingRevision;
    var customisation = typeof modal.readMetadataCustomisation === "function"
      ? modal.readMetadataCustomisation()
      : null;
    if (customisation !== null) payload.customisation = customisation;
    if (editingTarget.sub_scope) {
      var groupChoices = Array.isArray(editingChoices && editingChoices.group)
        ? editingChoices.group
        : [];
      if (groupChoices.length) {
        if (!refs.groupInput) return null;
        payload.group = String(refs.groupInput.value || "").trim();
      }
    } else {
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

  function normalizedChoices(response, target) {
    if (!target.sub_scope) return null;
    var rawChoices = response && response.choices;
    if (!rawChoices || typeof rawChoices !== "object") {
      throw new Error("Sub-scope metadata choices could not be loaded.");
    }
    return {
      ui_status: Array.isArray(rawChoices.ui_status)
        ? rawChoices.ui_status.map(String).map(function (value) { return value.trim(); }).filter(Boolean)
        : [],
      group: Array.isArray(rawChoices.group)
        ? rawChoices.group.map(String).map(function (value) { return value.trim(); }).filter(Boolean)
        : []
    };
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
    return {
      record: record,
      choices: normalizedChoices(response, target),
      sourceRevision: String(response.source_revision || "").trim()
    };
  }

  function clearEditingState() {
    editingTarget = null;
    editingDoc = null;
    editingChoices = null;
    editingRevision = "";
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
        var loaded = metadataDocFromResponse(response, normalizedTarget);
        editingTarget = normalizedTarget;
        editingDoc = loaded.record;
        editingChoices = loaded.choices;
        editingRevision = loaded.sourceRevision;
        if (normalizedTarget.sub_scope && !/^sha256:[0-9a-f]{64}$/.test(editingRevision)) {
          throw new Error("Sub-scope metadata revision could not be loaded.");
        }
        var contributionRequest = typeof callbacks.resolveMetadataContribution === "function"
          ? callbacks.resolveMetadataContribution(normalizedTarget)
          : null;
        return Promise.resolve(contributionRequest).then(function (metadataContribution) {
          var modal = modalController();
          if (!modal) return null;
          var modalOptions = {
            target: normalizedTarget,
            showParent: !normalizedTarget.sub_scope,
            choices: editingChoices
          };
          if (metadataContribution) {
            modalOptions.metadataContribution = metadataContribution;
          }
          return modal.openMetadataModal(editingDoc, modalOptions);
        });
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
    modal.renderMetadataStatusOptions(editingDoc, editingChoices);
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
