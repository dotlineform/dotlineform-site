import {
  applyManagedDocSubtreeCopy,
  previewManagedDocSubtreeCopy
} from "./docs-viewer-management-client.js";
import {
  openDocsViewerChoiceModal,
  openDocsViewerConfirmModal
} from "./docs-viewer-management-modals.js";

var COPY_TEXT = {
  title: "Copy subtree to scope",
  targetPrompt: "Choose the scope that will receive a new independent copy of “{title}” and all of its descendants.",
  targetButton: "Preview copy",
  targetRequired: "Choose a target scope.",
  previewing: "Planning subtree copy...",
  confirmTitle: "Confirm subtree copy",
  confirmButton: "Copy subtree",
  applying: "Copying subtree...",
  cancelButton: "Cancel"
};

function interpolate(template, values) {
  return String(template || "").replace(/\{([^}]+)\}/g, function (_match, key) {
    return values && values[key] != null ? String(values[key]) : "";
  });
}

function countLabel(count, singular, plural) {
  return count + " " + (count === 1 ? singular : plural);
}

export function buildCopySubtreeConfirmationBody(preview) {
  var source = preview && preview.source || {};
  var target = preview && preview.target || {};
  var title = String(source.title || source.doc_id || "the selected document").trim();
  var descendantCount = Number(preview && preview.descendant_count) || 0;
  var documentCount = Number(preview && preview.document_count) || descendantCount + 1;
  return [
    "Copy “" + title + "” and " + countLabel(descendantCount, "descendant", "descendants") + " to “" + String(target.scope || "").trim() + "”?",
    countLabel(documentCount, "new document", "new documents") + " will be created at the target scope root. The source subtree will not change."
  ];
}

function setBusy(callbacks, busy) {
  if (typeof callbacks.setBusy === "function") callbacks.setBusy(busy);
  if (typeof callbacks.render === "function") callbacks.render();
}

function setMessage(callbacks, message, isError) {
  if (typeof callbacks.setMessage === "function") callbacks.setMessage(message, isError);
}

export async function openCopySubtreeFlow(options = {}) {
  var root = options.root || null;
  var sourceDoc = options.sourceDoc || null;
  var targets = Array.isArray(options.targets) ? options.targets : [];
  var callbacks = options.callbacks || {};
  var sourceDocId = String(sourceDoc && sourceDoc.doc_id || "").trim();
  var sourceTitle = String(sourceDoc && sourceDoc.title || sourceDocId).trim();
  if (!sourceDocId) throw new Error("Copy subtree requires an active source document.");
  if (!targets.length) throw new Error("No other writable Docs Viewer scope is available.");

  var targetResult = await openDocsViewerChoiceModal({
    root: root,
    title: COPY_TEXT.title,
    body: interpolate(COPY_TEXT.targetPrompt, { title: sourceTitle }),
    value: targets[0].scopeId,
    choices: targets.map(function (target) {
      return { value: target.scopeId, label: target.label || target.scopeId };
    }),
    primaryLabel: COPY_TEXT.targetButton,
    cancelLabel: COPY_TEXT.cancelButton,
    requiredMessage: COPY_TEXT.targetRequired
  });
  if (!targetResult || !targetResult.confirmed) return null;

  var targetScope = String(targetResult.value || "").trim();
  if (!targets.some(function (target) { return target.scopeId === targetScope; })) {
    throw new Error("The selected target scope is no longer available.");
  }

  var preview;
  setBusy(callbacks, true);
  setMessage(callbacks, COPY_TEXT.previewing, false);
  try {
    preview = await previewManagedDocSubtreeCopy(sourceDocId, targetScope, options.clientOptions || {});
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, "", false);

  var confirmed = await openDocsViewerConfirmModal({
    root: root,
    title: COPY_TEXT.confirmTitle,
    body: buildCopySubtreeConfirmationBody(preview),
    primaryLabel: COPY_TEXT.confirmButton,
    cancelLabel: COPY_TEXT.cancelButton
  });
  if (!confirmed) return null;
  if (!preview || !preview.apply_plan) throw new Error("Copy subtree preview did not return an apply plan.");

  var applied;
  setBusy(callbacks, true);
  setMessage(callbacks, COPY_TEXT.applying, false);
  try {
    applied = await applyManagedDocSubtreeCopy(preview.apply_plan, options.clientOptions || {});
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, applied && applied.summary_text || "Subtree copied.", false);
  if (typeof callbacks.onApplied === "function") callbacks.onApplied(applied);
  return applied;
}
