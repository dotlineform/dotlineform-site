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

function lineageSources(preview) {
  return preview && preview.lineage && Array.isArray(preview.lineage.sources)
    ? preview.lineage.sources
    : [];
}

function lineageChoiceMarkup(preview) {
  var sources = lineageSources(preview);
  var markup = noteMarkup(
    "Choose New or one exact existing editorial document for every working document that already has a current target."
  );
  sources.forEach(function (source, sourceIndex) {
    var existing = Array.isArray(source && source.existing_editorials)
      ? source.existing_editorials
      : [];
    var available = existing.filter(function (choice) { return choice && choice.available === true; });
    var unavailable = existing.filter(function (choice) { return choice && choice.available !== true; });
    if (!available.length) return;
    var sourceLabel = String(source && source.title || source && source.source_doc_id || "Working document").trim();
    markup += '<p class="docsViewer__modalNote"><strong>' + escapeHtml(sourceLabel) + "</strong></p>";
    markup += [
      '<label class="docsViewer__field docsViewer__field--checkbox">',
      '  <input class="docsViewer__checkboxInput" type="radio" name="docsViewerDocumentLineageAction-' + sourceIndex + '" value="new">',
      '  <span class="docsViewer__fieldLabel">New editorial copy</span>',
      "</label>"
    ].join("");
    available.forEach(function (choice, choiceIndex) {
      var choiceLabel = String(choice.title || choice.editorial_doc_id).trim();
      markup += [
        '<label class="docsViewer__field docsViewer__field--checkbox">',
        '  <input class="docsViewer__checkboxInput" type="radio" name="docsViewerDocumentLineageAction-' + sourceIndex + '" value="replace:' + choiceIndex + '">',
        '  <span class="docsViewer__fieldLabel">Replace ' + escapeHtml(choiceLabel) + " (" + escapeHtml(choice.editorial_doc_id) + ")</span>",
        "</label>"
      ].join("");
    });
    unavailable.forEach(function (choice) {
      markup += [
        '<label class="docsViewer__field docsViewer__field--checkbox">',
        '  <input class="docsViewer__checkboxInput" type="radio" disabled>',
        '  <span class="docsViewer__fieldLabel">Unavailable editorial target (' + escapeHtml(choice.editorial_doc_id) + ")</span>",
        "</label>"
      ].join("");
    });
  });
  markup += noteMarkup(
    "Replace preserves the selected editorial identity, placement, added date, and current Publish inclusion gate. It overwrites its content without comparison or merge."
  );
  return markup;
}

function openLineageChoices(options) {
  var preview = options.preview || {};
  var sources = lineageSources(preview);
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Choose New or Replace",
    size: "compact",
    bodyHtml: lineageChoiceMarkup(preview),
    focusSelector: 'button[data-role="modal-cancel"]',
    actions: [
      { role: "modal-primary", label: "Preview choice" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onSubmit: function (api) {
      var actions = [];
      for (var sourceIndex = 0; sourceIndex < sources.length; sourceIndex += 1) {
        var source = sources[sourceIndex] || {};
        var available = Array.isArray(source.existing_editorials)
          ? source.existing_editorials.filter(function (choice) { return choice && choice.available === true; })
          : [];
        if (!available.length) {
          actions.push({
            source_doc_id: source.source_doc_id,
            action: "new",
            replace_target_doc_id: ""
          });
          continue;
        }
        var selected = api.host.querySelector(
          'input[name="docsViewerDocumentLineageAction-' + sourceIndex + '"]:checked'
        );
        if (!selected) {
          api.setStatus("Choose New or Replace for every listed working document.");
          return false;
        }
        var value = String(selected.value || "");
        if (value === "new") {
          actions.push({
            source_doc_id: source.source_doc_id,
            action: "new",
            replace_target_doc_id: ""
          });
          continue;
        }
        var choiceIndex = Number(value.slice("replace:".length));
        if (!value.startsWith("replace:") || !Number.isInteger(choiceIndex) || !available[choiceIndex]) {
          api.setStatus("The selected Replace target is unavailable.");
          return false;
        }
        actions.push({
          source_doc_id: source.source_doc_id,
          action: "replace",
          replace_target_doc_id: available[choiceIndex].editorial_doc_id
        });
      }
      return { confirmed: true, actions: actions };
    }
  });
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
  var lineage = lineageSources(preview);
  var includesNew = !lineage.length || lineage.some(function (source) {
    return source && source.action === "new";
  });
  if (
    mode === "copy"
    && includesNew
    && Object.prototype.hasOwnProperty.call(preview, "target_default_publishable")
  ) {
    lines.push("New documents will be included in the next Publish.");
  }
  var omitted = preview && preview.custom_metadata && Array.isArray(preview.custom_metadata.omitted)
    ? preview.custom_metadata.omitted
    : [];
  if (mode === "copy" && omitted.length) {
    lines.push(
      countLabel(omitted.length, "custom metadata field", "custom metadata fields")
      + " will be omitted because the target does not support "
      + (omitted.length === 1 ? "it." : "them.")
    );
  }
  lineageSources(preview).forEach(function (source) {
    if (source.action === "replace") {
      lines.push(
        "Replace " + String(source.replace_target_doc_id || "") +
        " from " + String(source.source_doc_id || "") +
        "; its identity and current Publish inclusion gate are preserved."
      );
    } else if (source.action === "new") {
      lines.push("Create a new editorial copy from " + String(source.source_doc_id || "") + ".");
    }
    var unavailableCount = Array.isArray(source.existing_editorials)
      ? source.existing_editorials.filter(function (choice) {
        return choice && choice.available !== true;
      }).length
      : 0;
    if (unavailableCount) {
      lines.push(
        countLabel(unavailableCount, "recorded editorial target is", "recorded editorial targets are")
        + " unavailable and cannot be replaced for " + String(source.source_doc_id || "") + "."
      );
    }
  });
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
  var fixedTarget = options.fixedTarget == null
    ? null
    : normalizeManagedDocumentCollectionTarget(options.fixedTarget);
  var modalTitle = String(options.modalTitle || "").trim();
  if (fixedTarget && mode !== "copy") {
    throw new Error("A fixed document transfer target is available only for Copy.");
  }
  if (fixedTarget && !modalTitle) {
    throw new Error("A fixed document Copy requires an exact modal title.");
  }
  if (fixedTarget && !targets.some(function (record) {
    return collectionKey(record.target) === collectionKey(fixedTarget);
  })) {
    throw new Error("The fixed document Copy target is unavailable.");
  }

  var choice = fixedTarget
    ? {
        confirmed: true,
        target: fixedTarget,
        includeDescendants: false
      }
    : await openTransferOptions({
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
      options.clientOptions || {},
      null
    );
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, "", false);

  if (
    mode === "copy"
    && preview
    && preview.lineage
    && preview.lineage.choice_required === true
  ) {
    var lineageChoice = await openLineageChoices({
      root: options.root,
      restoreFocus: options.restoreFocus,
      preview: preview
    });
    if (!lineageChoice || !lineageChoice.confirmed) return null;
    setBusy(callbacks, true);
    setMessage(callbacks, TRANSFER_TEXT[mode].previewing, false);
    try {
      preview = await previewManagedDocumentTransfer(
        source,
        checkedDocIds,
        choice.target,
        mode,
        choice.includeDescendants,
        options.clientOptions || {},
        lineageChoice.actions
      );
    } finally {
      setBusy(callbacks, false);
    }
    setMessage(callbacks, "", false);
  }

  var canApply = documentTransferPreviewCanApply(preview);
  var hasReplace = lineageSources(preview).some(function (sourceRecord) {
    return sourceRecord && sourceRecord.action === "replace";
  });
  var confirmed = await openDocsViewerConfirmModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: modalTitle || TRANSFER_TEXT[mode].confirmTitle,
    bodyHtml: documentTransferConfirmationBodyHtml(preview),
    primaryLabel: hasReplace ? "Replace selected documents" : TRANSFER_TEXT[mode].confirmButton,
    primaryTone: hasReplace ? "danger" : "",
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
