import {
  applyManagedDocumentTransfer,
  previewManagedDocumentTransfer
} from "./docs-viewer-management-client.js";
import {
  escapeHtml,
  openDocsViewerConfirmModal,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";
import {
  normalizeManagedDocumentCollectionTarget
} from "./docs-viewer-management-document-target.js";

var TRANSFER_TEXT = {
  copy: {
    optionsTitle: "Copy to…",
    optionsIntro: "Choose the collection that will receive independent copies of the checked documents.",
    previewButton: "Preview copy",
    previewing: "Planning document copy...",
    confirmTitle: "Confirm copy",
    confirmButton: "Copy documents",
    applying: "Copying documents..."
  },
  move: {
    optionsTitle: "Move to scope",
    optionsIntro: "Choose the scope that will receive the checked documents and their complete descendant subtrees.",
    previewButton: "Preview move",
    previewing: "Planning document move...",
    confirmTitle: "Confirm move",
    confirmButton: "Move documents",
    applying: "Moving documents..."
  }
};

function normalizedMode(value) {
  var mode = String(value || "").trim().toLowerCase();
  if (mode !== "copy" && mode !== "move") {
    throw new Error("Document transfer mode must be copy or move.");
  }
  return mode;
}

function countLabel(count, singular, plural) {
  return count + " " + (count === 1 ? singular : plural);
}

function noteMarkup(text) {
  return '<p class="docsViewer__modalNote muted small">' + escapeHtml(text) + "</p>";
}

function collectionLabel(target) {
  var exact = { scope: target && target.scope };
  if (target && Object.prototype.hasOwnProperty.call(target, "sub_scope")) {
    exact.sub_scope = target.sub_scope;
  }
  var normalized = normalizeManagedDocumentCollectionTarget(exact);
  return normalized.sub_scope
    ? normalized.scope + " / " + normalized.sub_scope
    : normalized.scope;
}

function collectionKey(target) {
  var normalized = normalizeManagedDocumentCollectionTarget(target);
  return normalized.scope + "\u0000" + String(normalized.sub_scope || "");
}

function optionMarkup(options) {
  var mode = normalizedMode(options.mode);
  var targets = Array.isArray(options.targets) ? options.targets : [];
  var markup = noteMarkup(TRANSFER_TEXT[mode].optionsIntro);
  markup += targets.map(function (record, index) {
    var target = normalizeManagedDocumentCollectionTarget(record && record.target);
    var label = String(record && record.label || collectionLabel(target)).trim();
    return [
      '<label class="docsViewer__field docsViewer__field--checkbox">',
      '  <input class="docsViewer__checkboxInput" type="radio" name="docsViewerDocumentTransferTarget" value="' + index + '"' + (index === 0 ? " checked" : "") + ">",
      '  <span class="docsViewer__fieldLabel">' + escapeHtml(label) + "</span>",
      "</label>"
    ].join("");
  }).join("");
  if (mode === "copy" && options.copyDescendantsAvailable) {
    markup += [
      '<label class="docsViewer__field docsViewer__field--checkbox">',
      '  <input class="docsViewer__checkboxInput" type="checkbox" data-role="document-transfer-descendants">',
      '  <span class="docsViewer__fieldLabel">Include descendants of checked documents</span>',
      "</label>"
    ].join("");
  }
  if (mode === "move") {
    markup += noteMarkup("Move always includes every descendant of each checked document.");
  }
  return markup;
}

export function buildDocumentTransferConfirmationBody(preview) {
  var mode = normalizedMode(preview && preview.mode);
  var documentCount = Number(preview && preview.document_count) || 0;
  var mediaCount = Number(preview && preview.unique_media_count) || 0;
  var blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
  var warnings = Array.isArray(preview && preview.warnings) ? preview.warnings : [];
  var target = preview && preview.target || {};
  var targetName = collectionLabel(target);
  var documentNoun = documentCount === 1 ? "document" : "documents";
  var lines = [
    (mode === "copy" ? "Copy" : "Move") + " " + documentCount +
      " " + documentNoun + " to " + targetName,
    "includes " + mediaCount + " media"
  ];
  blockers.forEach(function (blocker) {
    lines.push("Blocked: " + String(blocker && blocker.message || blocker || "").trim());
  });
  var inboundLinkWarnings = warnings.filter(function (warning) {
    return warning && warning.code === "inbound_viewer_link";
  });
  if (inboundLinkWarnings.length) {
    var sourceScope = String(preview && preview.source && preview.source.scope || "").trim();
    var singularInboundLink = inboundLinkWarnings.length === 1;
    lines.push(
      "Warning: This move will leave " +
      countLabel(inboundLinkWarnings.length, "broken link", "broken links") +
      " in “" + sourceScope + "”. After the move, review “" + sourceScope +
      "” in Docs Broken Links and either remove " +
      (singularInboundLink ? "that reference" : "those references") +
      " or replace " + (singularInboundLink ? "it" : "them") +
      " with plain text such as “Document title (doc archived)”."
    );
  }
  warnings.filter(function (warning) {
    return !warning || warning.code !== "inbound_viewer_link";
  }).forEach(function (warning) {
    lines.push("Warning: " + String(warning && warning.message || warning || "").trim());
  });
  if (mode === "copy") {
    lines.push(
      preview.target_default_viewable === false
        ? "New documents will be non-viewable."
        : "New documents will use the target's viewable default."
    );
    var omitted = preview && preview.custom_metadata && Array.isArray(preview.custom_metadata.omitted)
      ? preview.custom_metadata.omitted
      : [];
    if (omitted.length) {
      lines.push(
        countLabel(omitted.length, "custom metadata field", "custom metadata fields")
        + " will be omitted because the target does not support "
        + (omitted.length === 1 ? "it." : "them.")
      );
    }
  }
  return lines.filter(Boolean);
}

function documentTransferConfirmationBodyHtml(preview) {
  var mode = normalizedMode(preview && preview.mode);
  var lines = buildDocumentTransferConfirmationBody(preview);
  var documentCount = Number(preview && preview.document_count) || 0;
  var mediaCount = Number(preview && preview.unique_media_count) || 0;
  var targetName = collectionLabel(preview && preview.target || {});
  var documentNoun = documentCount === 1 ? "document" : "documents";
  return [
    '<p class="docsViewer__modalNote muted small">' +
      (mode === "copy" ? "Copy" : "Move") + " <strong>" +
      escapeHtml(documentCount) + "</strong> " + documentNoun + " to <strong>" +
      escapeHtml(targetName) + "</strong></p>",
    '<p class="docsViewer__modalNote muted small">includes <strong>' +
      escapeHtml(mediaCount) + "</strong> media</p>",
    lines.slice(2).map(noteMarkup).join("")
  ].join("");
}

export function documentTransferPreviewCanApply(preview) {
  return Boolean(
    preview
    && preview.ok === true
    && preview.apply_plan
    && (!Array.isArray(preview.blockers) || preview.blockers.length === 0)
  );
}

function setBusy(callbacks, busy) {
  if (typeof callbacks.setBusy === "function") callbacks.setBusy(busy);
  if (typeof callbacks.render === "function") callbacks.render();
}

function setMessage(callbacks, message, isError) {
  if (typeof callbacks.setMessage === "function") callbacks.setMessage(message, isError);
}

function openTransferOptions(options) {
  var mode = normalizedMode(options.mode);
  var targets = Array.isArray(options.targets) ? options.targets : [];
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: TRANSFER_TEXT[mode].optionsTitle,
    size: "compact",
    bodyHtml: optionMarkup({
      mode: mode,
      targets: targets,
      copyDescendantsAvailable: options.copyDescendantsAvailable
    }),
    focusSelector: 'button[data-role="modal-cancel"]',
    actions: [
      { role: "modal-primary", label: TRANSFER_TEXT[mode].previewButton },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onSubmit: function (api) {
      var selected = api.host.querySelector('input[name="docsViewerDocumentTransferTarget"]:checked');
      var targetIndex = Number(selected && selected.value);
      if (!Number.isInteger(targetIndex) || !targets[targetIndex]) {
        api.setStatus("Choose a target collection.");
        return false;
      }
      var descendants = api.host.querySelector('[data-role="document-transfer-descendants"]');
      return {
        confirmed: true,
        target: normalizeManagedDocumentCollectionTarget(targets[targetIndex].target),
        includeDescendants: mode === "copy" && Boolean(descendants && descendants.checked)
      };
    }
  });
}

export async function openDocumentTransferWorkflow(options = {}) {
  var mode = normalizedMode(options.mode);
  var source = normalizeManagedDocumentCollectionTarget(options.source);
  var checkedDocIds = Array.isArray(options.checkedDocIds)
    ? options.checkedDocIds.map(function (docId) { return String(docId || "").trim(); }).filter(Boolean)
    : [];
  var targets = Array.isArray(options.targets) ? options.targets : [];
  var callbacks = options.callbacks || {};
  if (!checkedDocIds.length) throw new Error("Select one or more documents.");
  if (!targets.length) throw new Error("No other writable Docs Viewer collection is available.");

  var choice = await openTransferOptions({
    root: options.root,
    restoreFocus: options.restoreFocus,
    mode: mode,
    targets: targets,
    copyDescendantsAvailable: options.copyDescendantsAvailable === true
  });
  if (!choice || !choice.confirmed) return null;
  if (!targets.some(function (record) {
    return collectionKey(record.target) === collectionKey(choice.target);
  })) {
    throw new Error("The selected target collection is no longer available.");
  }

  var preview;
  setBusy(callbacks, true);
  setMessage(callbacks, TRANSFER_TEXT[mode].previewing, false);
  try {
    preview = await previewManagedDocumentTransfer(
      source,
      checkedDocIds,
      choice.target,
      mode,
      choice.includeDescendants,
      options.clientOptions || {}
    );
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, "", false);

  var canApply = documentTransferPreviewCanApply(preview);
  var confirmed = await openDocsViewerConfirmModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: TRANSFER_TEXT[mode].confirmTitle,
    bodyHtml: documentTransferConfirmationBodyHtml(preview),
    primaryLabel: TRANSFER_TEXT[mode].confirmButton,
    primaryDisabled: !canApply,
    initialFocus: "cancel",
    cancelLabel: "Cancel"
  });
  if (!confirmed) return null;
  if (!canApply) throw new Error("Document transfer is blocked.");

  var applied;
  setBusy(callbacks, true);
  setMessage(callbacks, TRANSFER_TEXT[mode].applying, false);
  try {
    applied = await applyManagedDocumentTransfer(
      preview.apply_plan,
      options.clientOptions || {}
    );
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, applied && applied.summary_text || "Document transfer completed.", false);
  if (typeof callbacks.onApplied === "function") callbacks.onApplied(applied);
  return applied;
}
