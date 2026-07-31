import {
  applyManagedDocsStaticHtmlExport,
  previewManagedDocsStaticHtmlExport
} from "./docs-viewer-management-client.js";
import {
  openDocsViewerConfirmModal
} from "./docs-viewer-management-modals.js";

const PREVIEW_SCHEMA_VERSION = "docs_static_html_snapshot_preview_v1";
const REVISION_PATTERN = /^[0-9a-f]{64}$/;
const TARGET_STATES = new Set(["absent", "recognized", "unrecognized", "non_directory"]);

function normalizeIds(values) {
  var seen = new Set();
  return (Array.isArray(values) ? values : []).map(function (value) {
    return String(value || "").trim();
  }).filter(function (docId) {
    if (!docId || seen.has(docId)) return false;
    seen.add(docId);
    return true;
  });
}

function sameIds(left, right) {
  if (left.length !== right.length) return false;
  var expected = new Set(left);
  return right.every(function (docId) { return expected.has(docId); });
}

function setBusy(callbacks, busy) {
  if (typeof callbacks.setBusy === "function") callbacks.setBusy(busy);
  if (typeof callbacks.render === "function") callbacks.render();
}

function setMessage(callbacks, message, isError) {
  if (typeof callbacks.setMessage === "function") callbacks.setMessage(message, isError);
}

export function validateStaticHtmlSnapshotPreview(preview, options = {}) {
  var payload = preview && typeof preview === "object" ? preview : {};
  var scope = String(options.scope || "").trim();
  var requestedDocIds = normalizeIds(options.checkedDocIds);
  var previewDocIds = normalizeIds(payload.doc_ids);
  var rawPreviewDocIds = Array.isArray(payload.doc_ids) ? payload.doc_ids : [];
  var targetState = String(payload.target_state || "").trim();
  var destinationLabel = String(payload.destination_label || "").trim();
  if (
    payload.ok !== true
    || payload.schema_version !== PREVIEW_SCHEMA_VERSION
    || payload.operation !== "preview"
    || payload.dry_run !== true
  ) {
    throw new Error("Snapshot preview response is invalid.");
  }
  if (!scope || String(payload.scope || "").trim() !== scope) {
    throw new Error("Snapshot preview scope no longer matches the active scope.");
  }
  if (
    !requestedDocIds.length
    || rawPreviewDocIds.length !== previewDocIds.length
    || !sameIds(requestedDocIds, previewDocIds)
  ) {
    throw new Error("Snapshot preview documents no longer match the checked selection.");
  }
  if (Number(payload.document_count) !== previewDocIds.length) {
    throw new Error("Snapshot preview document count is invalid.");
  }
  var selectionKind = String(payload.selection_kind || "");
  if (!["single", "partial", "complete"].includes(selectionKind)) {
    throw new Error("Snapshot preview selection kind is invalid.");
  }
  if (
    (selectionKind === "single" && previewDocIds.length !== 1)
    || (selectionKind === "partial" && previewDocIds.length < 2)
  ) {
    throw new Error("Snapshot preview selection kind is invalid.");
  }
  if (!TARGET_STATES.has(targetState)) {
    throw new Error("Snapshot preview target state is invalid.");
  }
  if (
    !destinationLabel.startsWith("/docs-export/")
    || !destinationLabel.endsWith("/")
    || destinationLabel.includes("\n")
    || Object.prototype.hasOwnProperty.call(payload, "destination")
  ) {
    throw new Error("Snapshot preview destination is invalid.");
  }
  if (
    !REVISION_PATTERN.test(String(payload.plan_revision || ""))
    || !REVISION_PATTERN.test(String(payload.target_revision || ""))
    || !/^\d{4}-\d{2}-\d{2}$/.test(String(payload.export_date || ""))
  ) {
    throw new Error("Snapshot preview revision is invalid.");
  }
  var replacementRequired = targetState === "recognized" || targetState === "unrecognized";
  if (Boolean(payload.replacement_required) !== replacementRequired) {
    throw new Error("Snapshot preview replacement state is invalid.");
  }
  if (Boolean(payload.replace_allowed) !== (targetState !== "non_directory")) {
    throw new Error("Snapshot preview replacement permission is invalid.");
  }
  var hasExistingSnapshot = payload.existing_snapshot && typeof payload.existing_snapshot === "object";
  if ((targetState === "recognized") !== Boolean(hasExistingSnapshot)) {
    throw new Error("Snapshot preview provenance state is invalid.");
  }
  return payload;
}

export function staticHtmlSnapshotPreviewCanApply(preview) {
  return Boolean(preview && preview.replace_allowed === true && preview.target_state !== "non_directory");
}

export function buildStaticHtmlSnapshotConfirmationBody(preview) {
  return [preview.destination_label];
}

export function staticHtmlSnapshotConfirmationTitle(preview) {
  var documentCount = Number(preview.document_count || 0);
  return "Export " + documentCount + " document" + (documentCount === 1 ? "" : "s") + " to:";
}

export function staticHtmlSnapshotConfirmationOptions(preview, options = {}) {
  var canApply = staticHtmlSnapshotPreviewCanApply(preview);
  var replacing = preview.target_state === "recognized" || preview.target_state === "unrecognized";
  return {
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: staticHtmlSnapshotConfirmationTitle(preview),
    body: buildStaticHtmlSnapshotConfirmationBody(preview),
    primaryLabel: replacing ? "Replace" : canApply ? "Create snapshot" : "Unavailable",
    primaryDisabled: !canApply,
    primaryTone: replacing ? "danger" : "",
    initialFocus: replacing || !canApply ? "cancel" : "",
    cancelLabel: "Cancel"
  };
}

export async function openStaticHtmlSnapshotExportWorkflow(options = {}) {
  var scope = String(options.scope || "").trim();
  var checkedDocIds = normalizeIds(options.checkedDocIds);
  var callbacks = options.callbacks || {};
  var clientOptions = options.clientOptions || {};
  var previewSnapshot = options.previewSnapshot || previewManagedDocsStaticHtmlExport;
  var applySnapshot = options.applySnapshot || applyManagedDocsStaticHtmlExport;
  var confirmSnapshot = options.confirmSnapshot || openDocsViewerConfirmModal;
  if (!scope) throw new Error("Snapshot Export requires an active scope.");
  if (!checkedDocIds.length) throw new Error("Select one or more documents.");

  var preview;
  setBusy(callbacks, true);
  setMessage(callbacks, "Preparing dated snapshot…", false);
  try {
    preview = await previewSnapshot(checkedDocIds, clientOptions);
  } finally {
    setBusy(callbacks, false);
  }
  preview = validateStaticHtmlSnapshotPreview(preview, {
    scope: scope,
    checkedDocIds: checkedDocIds
  });
  setMessage(callbacks, "", false);

  var canApply = staticHtmlSnapshotPreviewCanApply(preview);
  var confirmed = await confirmSnapshot(staticHtmlSnapshotConfirmationOptions(preview, options));
  if (!confirmed) return null;
  if (!canApply) throw new Error("Snapshot destination cannot be replaced.");

  var applied;
  setBusy(callbacks, true);
  setMessage(callbacks, "Exporting dated snapshot…", false);
  try {
    applied = await applySnapshot(preview, clientOptions);
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, applied && applied.summary_text || "Dated snapshot exported.", false);
  if (typeof callbacks.onApplied === "function") await callbacks.onApplied(applied);
  return applied;
}
