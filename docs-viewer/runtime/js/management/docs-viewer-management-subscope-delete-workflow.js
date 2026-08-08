import {
  applyManagedSubScopeDocDelete,
  previewManagedSubScopeDocDelete,
  readManagementCapabilities
} from "./docs-viewer-management-client.js";
import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";
import {
  buildDocsViewerDeletePreviewBody,
  docsViewerDeleteCompletionMessage,
  openDocsViewerConfirmModal
} from "./docs-viewer-management-modals.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function sameTarget(left, right) {
  return (
    left.scope === right.scope
    && left.sub_scope === right.sub_scope
    && left.doc_id === right.doc_id
  );
}

function responseTarget(payload) {
  var candidate = payload && payload.target && typeof payload.target === "object"
    ? payload.target
    : {
        scope: payload && payload.scope,
        sub_scope: payload && payload.sub_scope,
        doc_id: payload && payload.doc_id
      };
  return normalizeManagedDocumentTarget(candidate);
}

function assertPreviewReceipt(payload, target) {
  if (!payload || typeof payload !== "object" || !sameTarget(responseTarget(payload), target)) {
    throw new Error("Delete preview did not match the displayed sub-scope document.");
  }
  var revision = cleanString(payload.source_revision);
  if (!/^sha256:[0-9a-f]{64}$/.test(revision)) {
    throw new Error("Delete preview did not return a valid source revision.");
  }
  if (Number(payload.delete_count) !== 1) {
    throw new Error("Delete preview did not remain singular.");
  }
  return revision;
}

function assertApplyReceipt(payload, target, sourceRevision) {
  var deletedIds = Array.isArray(payload && payload.deleted_doc_ids)
    ? payload.deleted_doc_ids.map(cleanString).filter(Boolean)
    : [];
  if (
    !payload
    || typeof payload !== "object"
    || !sameTarget(responseTarget(payload), target)
    || cleanString(payload.source_revision) !== sourceRevision
    || Number(payload.delete_count) !== 1
    || deletedIds.length !== 1
    || deletedIds[0] !== target.doc_id
  ) {
    throw new Error("Delete result did not match the confirmed sub-scope document.");
  }
}

export function subScopeDetailDeleteCapability(payload) {
  var capabilities = payload && payload.capabilities
    ? payload.capabilities
    : payload;
  var deletion = capabilities && capabilities.document_delete;
  return Boolean(
    deletion
    && typeof deletion === "object"
    && deletion.preview === true
    && deletion.apply === true
    && deletion.sub_scope_detail === true
  );
}

function previewBody(preview, target, title) {
  var body = [
    "Document: " + (cleanString(title) || target.doc_id),
    "Document ID: " + target.doc_id,
    "Sub-scope: " + target.scope + "/" + target.sub_scope
  ];
  return body.concat(buildDocsViewerDeletePreviewBody(preview));
}

function deleteErrorMessage(error) {
  var message = cleanString(error && error.message) || "Delete failed.";
  var payload = error && error.payload && typeof error.payload === "object"
    ? error.payload
    : null;
  if (!payload || payload.source_restored !== true) return message;
  if (payload.retry_safe === true) {
    return message + " The source was restored and it is safe to retry.";
  }
  return message + " The source was restored, but the generated report could not be fully reconciled.";
}

export function createDocsViewerManagementSubscopeDeleteWorkflow(options = {}) {
  var target = normalizeManagedDocumentTarget(options.target);
  if (!target.sub_scope) {
    throw new Error("Sub-scope detail Delete requires an exact child target.");
  }
  var button = options.button || null;
  var clientOptions = options.clientOptions || {};
  var title = cleanString(options.title) || target.doc_id;
  var readCapabilities = options.readCapabilities || readManagementCapabilities;
  var previewDelete = options.previewDelete || previewManagedSubScopeDocDelete;
  var applyDelete = options.applyDelete || applyManagedSubScopeDocDelete;
  var confirmDelete = options.confirmDelete || openDocsViewerConfirmModal;
  var commitDeletedDocument = options.commitDeletedDocument;
  var setStatus = typeof options.setStatus === "function" ? options.setStatus : function () {};
  var active = true;
  var available = false;
  var busy = false;
  var modalAbortController = null;

  if (!button || typeof button.addEventListener !== "function") {
    throw new Error("Sub-scope detail Delete requires a button.");
  }
  if (typeof commitDeletedDocument !== "function") {
    throw new Error("Sub-scope detail Delete requires report reconciliation.");
  }

  function projectButton(reason) {
    var unavailableReason = cleanString(reason);
    button.disabled = busy || !available;
    button.title = unavailableReason || ("Delete " + title);
    button.setAttribute("aria-label", unavailableReason
      ? "Delete " + title + ". " + unavailableReason
      : "Delete " + title);
    if (busy) {
      button.setAttribute("aria-busy", "true");
    } else {
      button.removeAttribute("aria-busy");
    }
  }

  function visibleStatus(message, isError) {
    if (active) setStatus(message, Boolean(isError));
  }

  async function initialize() {
    projectButton("Checking Delete availability.");
    try {
      var payload = await readCapabilities(clientOptions);
      if (!active) return false;
      available = subScopeDetailDeleteCapability(payload);
      projectButton(available ? "" : "Sub-scope detail Delete is unavailable.");
      return available;
    } catch (error) {
      if (!active) return false;
      available = false;
      projectButton("Sub-scope detail Delete is unavailable.");
      visibleStatus(deleteErrorMessage(error), true);
      return false;
    }
  }

  async function run() {
    if (!active || !available || busy) return null;
    busy = true;
    projectButton("");
    visibleStatus("Checking delete impact for " + title + "...", false);
    var applyStarted = false;
    try {
      var preview = await previewDelete(target, clientOptions);
      if (!active) return null;
      if (preview.allowed !== true) {
        var blockers = (Array.isArray(preview.blockers) ? preview.blockers : [])
          .map(cleanString)
          .filter(Boolean);
        visibleStatus(blockers.join("; ") || "Delete is blocked.", true);
        return null;
      }
      var sourceRevision = assertPreviewReceipt(preview, target);
      busy = false;
      projectButton("");
      visibleStatus("", false);
      modalAbortController = typeof AbortController === "function"
        ? new AbortController()
        : null;
      var confirmed = await confirmDelete({
        root: options.root,
        restoreFocus: button,
        title: "Delete " + title + "?",
        body: previewBody(preview, target, title),
        primaryLabel: "Delete document",
        primaryTone: "danger",
        initialFocus: "cancel",
        cancelLabel: "Cancel",
        signal: modalAbortController && modalAbortController.signal
      });
      modalAbortController = null;
      if (!active || !confirmed) return null;
      busy = true;
      applyStarted = true;
      projectButton("");
      visibleStatus("Deleting " + title + "...", false);
      var applied = await applyDelete(target, sourceRevision, clientOptions);
      assertApplyReceipt(applied, target, sourceRevision);
      var completionMessage = docsViewerDeleteCompletionMessage(applied);
      visibleStatus(completionMessage, false);
      await commitDeletedDocument(target);
      if (active && completionMessage) visibleStatus(completionMessage, false);
      return applied;
    } catch (error) {
      if (active) {
        visibleStatus(deleteErrorMessage(error), true);
      } else if (applyStarted) {
        setStatus(deleteErrorMessage(error), true);
      }
      return null;
    } finally {
      busy = false;
      if (active) projectButton("");
    }
  }

  function destroy() {
    active = false;
    available = false;
    busy = false;
    if (modalAbortController) {
      modalAbortController.abort();
      modalAbortController = null;
    }
    button.removeEventListener("click", run);
    button.disabled = true;
  }

  button.addEventListener("click", run);

  return {
    destroy: destroy,
    initialize: initialize,
    run: run
  };
}
