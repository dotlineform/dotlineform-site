import {
  applyManagedDocumentTransfer,
  previewManagedDocumentTransfer
} from "./docs-viewer-management-client.js";
import {
  escapeHtml,
  openDocsViewerConfirmModal,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";

var TRANSFER_TEXT = {
  copy: {
    optionsTitle: "Copy to scope",
    optionsIntro: "Choose the scope that will receive independent copies of the checked documents.",
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

function optionMarkup(options) {
  var mode = normalizedMode(options.mode);
  var targets = Array.isArray(options.targets) ? options.targets : [];
  var selectedTarget = String(options.selectedTarget || "").trim();
  var markup = noteMarkup(TRANSFER_TEXT[mode].optionsIntro);
  markup += targets.map(function (target) {
    var scopeId = String(target && target.scopeId || "").trim();
    var label = String(target && target.label || scopeId).trim();
    return [
      '<label class="docsViewer__field docsViewer__field--checkbox">',
      '  <input class="docsViewer__checkboxInput" type="radio" name="docsViewerDocumentTransferTarget" value="' + escapeHtml(scopeId) + '"' + (scopeId === selectedTarget ? " checked" : "") + ">",
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
  var rootCount = Number(preview && preview.effective_root_count) || 0;
  var descendantCount = Number(preview && preview.descendant_count) || 0;
  var mediaCount = Number(preview && preview.unique_media_count) || 0;
  var retained = Array.isArray(preview && preview.retained_external_dependencies)
    ? preview.retained_external_dependencies
    : [];
  var media = Array.isArray(preview && preview.media) ? preview.media : [];
  var buildSourceCount = media.reduce(function (count, item) {
    return count + (Array.isArray(item && item.build_sources) ? item.build_sources.length : 0);
  }, 0);
  var blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
  var warnings = Array.isArray(preview && preview.warnings) ? preview.warnings : [];
  var target = preview && preview.target || {};
  var lines = [
    (mode === "copy" ? "Copy" : "Move") + " " +
      countLabel(documentCount, "document", "documents") + " across " +
      countLabel(rootCount, "target root", "target roots") + " to “" +
      String(target.scope || "").trim() + "”.",
    countLabel(descendantCount, "descendant", "descendants") + " and " +
      countLabel(mediaCount, "unique media item", "unique media items") +
      " are included."
  ];
  if (buildSourceCount) {
    lines.push(countLabel(buildSourceCount, "registered media source", "registered media sources") + " will also transfer.");
  }
  if (retained.length) {
    lines.push(countLabel(retained.length, "external dependency", "external dependencies") + " will remain unchanged.");
  }
  lines.push(
    mode === "copy"
      ? "The source documents and media will not change."
      : "The target is completed first; source documents and exclusive media are removed only after both rebuilds succeed."
  );
  blockers.forEach(function (blocker) {
    lines.push("Blocked: " + String(blocker && blocker.message || blocker || "").trim());
  });
  warnings.forEach(function (warning) {
    lines.push("Warning: " + String(warning && warning.message || warning || "").trim());
  });
  return lines.filter(Boolean);
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
      selectedTarget: targets[0] && targets[0].scopeId,
      copyDescendantsAvailable: options.copyDescendantsAvailable
    }),
    focusSelector: 'button[data-role="modal-cancel"]',
    actions: [
      { role: "modal-primary", label: TRANSFER_TEXT[mode].previewButton },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onSubmit: function (api) {
      var selected = api.host.querySelector('input[name="docsViewerDocumentTransferTarget"]:checked');
      var targetScope = String(selected && selected.value || "").trim();
      if (!targetScope) {
        api.setStatus("Choose a target scope.");
        return false;
      }
      var descendants = api.host.querySelector('[data-role="document-transfer-descendants"]');
      return {
        confirmed: true,
        targetScope: targetScope,
        includeDescendants: mode === "copy" && Boolean(descendants && descendants.checked)
      };
    }
  });
}

export async function openDocumentTransferWorkflow(options = {}) {
  var mode = normalizedMode(options.mode);
  var checkedDocIds = Array.isArray(options.checkedDocIds)
    ? options.checkedDocIds.map(function (docId) { return String(docId || "").trim(); }).filter(Boolean)
    : [];
  var targets = Array.isArray(options.targets) ? options.targets : [];
  var callbacks = options.callbacks || {};
  if (!checkedDocIds.length) throw new Error("Select one or more documents.");
  if (!targets.length) throw new Error("No other writable Docs Viewer scope is available.");

  var choice = await openTransferOptions({
    root: options.root,
    restoreFocus: options.restoreFocus,
    mode: mode,
    targets: targets,
    copyDescendantsAvailable: options.copyDescendantsAvailable === true
  });
  if (!choice || !choice.confirmed) return null;
  if (!targets.some(function (target) { return target.scopeId === choice.targetScope; })) {
    throw new Error("The selected target scope is no longer available.");
  }

  var preview;
  setBusy(callbacks, true);
  setMessage(callbacks, TRANSFER_TEXT[mode].previewing, false);
  try {
    preview = await previewManagedDocumentTransfer(
      checkedDocIds,
      choice.targetScope,
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
    body: buildDocumentTransferConfirmationBody(preview),
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
