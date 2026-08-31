import {
  applyManagedDocsStaticHtmlExport,
  previewManagedDocsStaticHtmlExport,
  readManagedDocsIndex
} from "./docs-viewer-management-client.js";
import {
  scopeStaticHtmlExportCapability
} from "./docs-viewer-management-capabilities.js";
import {
  escapeHtml,
  openDocsViewerConfirmModal,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";
import {
  staticHtmlSnapshotPreviewCanApply,
  validateStaticHtmlSnapshotPreview
} from "./docs-viewer-static-html-export-workflow.js";
import {
  normalizeDocsIndexTreePayload
} from "../shared/docs-viewer-tree-payload-adapter.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeScope(value) {
  return cleanString(value).toLowerCase();
}

function setBusy(callbacks, busy) {
  if (typeof callbacks.setBusy === "function") callbacks.setBusy(busy);
  if (typeof callbacks.render === "function") callbacks.render();
}

function setMessage(callbacks, message, isError) {
  if (typeof callbacks.setMessage === "function") {
    callbacks.setMessage(message, isError);
  }
}

export function docsViewerExportScopeRecords(options = {}) {
  var scopeConfigs = Array.isArray(options.scopeConfigs) ? options.scopeConfigs : [];
  var capabilities = options.capabilities || {};
  var currentScope = normalizeScope(options.currentScope);
  var seen = new Set();
  return scopeConfigs.map(function (config) {
    var scope = normalizeScope(config && (config.scopeId || config.scope_id));
    if (!scope || seen.has(scope)) return null;
    seen.add(scope);
    var capability = scopeStaticHtmlExportCapability(capabilities, scope);
    return {
      scope: scope,
      label: cleanString(config && (config.label || config.scopeId || config.scope_id)) || scope,
      available: capability.available === true,
      reason: cleanString(capability.reason),
      selected: capability.available === true && scope === currentScope
    };
  }).filter(Boolean);
}

export function docsViewerExportScopesAvailable(options = {}) {
  return docsViewerExportScopeRecords(options).some(function (record) {
    return record.available;
  });
}

function scopeChoiceMarkup(record) {
  var checked = record.selected ? " checked" : "";
  var disabled = record.available ? "" : " disabled";
  var title = !record.available && record.reason
    ? ' title="' + escapeHtml(record.reason) + '"'
    : "";
  return "" +
    '<label class="docsViewer__field docsViewer__field--checkbox"' + title + ">" +
      '<input class="docsViewer__checkboxInput" type="checkbox" data-role="export-scope-choice" value="' + escapeHtml(record.scope) + '"' + checked + disabled + ">" +
      '<span class="docsViewer__fieldLabel">' + escapeHtml(record.label) + "</span>" +
    "</label>";
}

export function openDocsViewerExportScopesSelection(options = {}) {
  var records = Array.isArray(options.records) ? options.records : [];
  if (!records.some(function (record) { return record.available; })) {
    return Promise.reject(new Error("Export Scopes is unavailable for every registered scope."));
  }
  var bodyHtml =
    '<p class="docsViewer__modalNote muted small">Select the registered scopes to export as full dated snapshots.</p>' +
    records.map(scopeChoiceMarkup).join("");
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Export Scopes",
    size: "compact",
    bodyHtml: bodyHtml,
    focusSelector: 'input[data-role="export-scope-choice"]:checked',
    actions: [
      { role: "modal-primary", label: "Continue" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var primary = api.host.querySelector('[data-role="modal-primary"]');
      function renderSelection() {
        var selected = api.host.querySelectorAll(
          'input[data-role="export-scope-choice"]:checked:not([disabled])'
        );
        if (primary) primary.disabled = selected.length === 0;
      }
      api.host.querySelectorAll('input[data-role="export-scope-choice"]').forEach(function (input) {
        input.addEventListener("change", renderSelection);
      });
      renderSelection();
    },
    onSubmit: function (api) {
      var scopes = Array.from(api.host.querySelectorAll(
        'input[data-role="export-scope-choice"]:checked:not([disabled])'
      )).map(function (input) {
        return normalizeScope(input.value);
      }).filter(Boolean);
      if (!scopes.length) {
        api.setStatus("Select one or more scopes.");
        return false;
      }
      return { confirmed: true, scopes: scopes };
    }
  }).then(function (result) {
    return result && result.confirmed
      ? { confirmed: true, scopes: result.scopes }
      : { confirmed: false, scopes: [] };
  });
}

function selectedScopeRecords(records, selectedScopes) {
  var normalized = (Array.isArray(selectedScopes) ? selectedScopes : []).map(normalizeScope);
  var unique = Array.from(new Set(normalized.filter(Boolean)));
  if (!unique.length || unique.length !== normalized.length) {
    throw new Error("Select one or more distinct registered scopes.");
  }
  var byScope = new Map(records.map(function (record) {
    return [record.scope, record];
  }));
  return unique.map(function (scope) {
    var record = byScope.get(scope);
    if (!record) throw new Error("Docs scope is not registered: " + scope);
    if (!record.available) {
      throw new Error(record.reason || "Snapshot Export is unavailable for " + scope + ".");
    }
    return record;
  });
}

export function docsViewerExportScopeDocIds(indexPayload, scope) {
  var docs = indexPayload && Array.isArray(indexPayload.docs) ? indexPayload.docs : [];
  var rawIds = docs.map(function (doc) {
    return cleanString(doc && doc.doc_id);
  });
  var docIds = Array.from(new Set(rawIds.filter(Boolean)));
  if (!docIds.length) {
    throw new Error("No generated documents are available to export for " + scope + ".");
  }
  if (docIds.length !== rawIds.length) {
    throw new Error("The generated Index contains invalid document identities for " + scope + ".");
  }
  return docIds;
}

function confirmationStateLabel(preview) {
  if (!staticHtmlSnapshotPreviewCanApply(preview)) return "Unavailable";
  if (preview.target_state === "absent") return "Create snapshot";
  return "Replace existing snapshot";
}

export function exportScopesConfirmationOptions(plans, options = {}) {
  var records = Array.isArray(plans) ? plans : [];
  var replacements = records.some(function (plan) {
    return plan.preview.target_state === "recognized" || plan.preview.target_state === "unrecognized";
  });
  var canApply = records.length > 0 && records.every(function (plan) {
    return staticHtmlSnapshotPreviewCanApply(plan.preview);
  });
  return {
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Export " + records.length + " scope" + (records.length === 1 ? "" : "s") + " to docs-export",
    body: records.map(function (plan) {
      var count = Number(plan.preview.document_count || 0);
      return plan.preview.destination_label + " — " + count + " document" +
        (count === 1 ? "" : "s") + " — " + confirmationStateLabel(plan.preview);
    }),
    size: "wide",
    primaryLabel: canApply ? "Export scopes" : "Unavailable",
    primaryDisabled: !canApply,
    primaryTone: replacements ? "danger" : "",
    initialFocus: replacements || !canApply ? "cancel" : "",
    cancelLabel: "Cancel"
  };
}

export function docsViewerExportScopesWorkflowMessage(result) {
  var scopes = Array.isArray(result && result.scopes) ? result.scopes : [];
  var documentCount = Number(result && result.documentCount || 0);
  if (!scopes.length) return "";
  return "Exported " + scopes.length + " scope" + (scopes.length === 1 ? "" : "s") +
    " (" + documentCount + " document" + (documentCount === 1 ? "" : "s") + ") to docs-export.";
}

export async function runManagedDocsExportScopesWorkflow(options = {}) {
  var callbacks = options.callbacks || {};
  var operations = options.operations || {};
  var records = docsViewerExportScopeRecords({
    capabilities: options.capabilities,
    currentScope: options.currentScope,
    scopeConfigs: options.scopeConfigs
  });
  var selectScopes = operations.selectScopes || openDocsViewerExportScopesSelection;
  var confirmBatch = operations.confirmBatch || function (confirmationOptions) {
    return openDocsViewerConfirmModal(confirmationOptions);
  };
  var readIndex = operations.readIndex || function (scope) {
    return readManagedDocsIndex(scope, options.clientOptions || {})
      .then(normalizeDocsIndexTreePayload);
  };
  var previewSnapshot = operations.previewSnapshot || function (scope, docIds, clientOptions) {
    return previewManagedDocsStaticHtmlExport(docIds, Object.assign({}, clientOptions, {
      scope: scope
    }));
  };
  var applySnapshot = operations.applySnapshot || function (scope, preview, clientOptions) {
    return applyManagedDocsStaticHtmlExport(preview, Object.assign({}, clientOptions, {
      scope: scope
    }));
  };
  var selection = options.selection || await selectScopes({
    root: options.root,
    restoreFocus: options.restoreFocus,
    records: records
  });
  if (!selection || selection.confirmed !== true) {
    return { cancelled: true, scopes: [], documentCount: 0, results: [] };
  }

  var selectedRecords = selectedScopeRecords(records, selection.scopes);
  var plans = [];
  setBusy(callbacks, true);
  try {
    for (var index = 0; index < selectedRecords.length; index += 1) {
      var record = selectedRecords[index];
      setMessage(
        callbacks,
        "Preparing " + (index + 1) + " of " + selectedRecords.length + ": " + record.scope + "…",
        false
      );
      var indexPayload = await readIndex(record.scope);
      var docIds = docsViewerExportScopeDocIds(indexPayload, record.scope);
      var preview = await previewSnapshot(record.scope, docIds, options.clientOptions || {});
      preview = validateStaticHtmlSnapshotPreview(preview, {
        scope: record.scope,
        checkedDocIds: docIds
      });
      if (preview.selection_kind !== "complete") {
        throw new Error(
          "The generated Index changed before the full-scope preview for " + record.scope + "."
        );
      }
      plans.push({ scope: record.scope, docIds: docIds, preview: preview });
    }
  } finally {
    setBusy(callbacks, false);
  }
  setMessage(callbacks, "", false);

  var confirmed = await confirmBatch(exportScopesConfirmationOptions(plans, options));
  if (!confirmed) {
    return { cancelled: true, scopes: [], documentCount: 0, results: [] };
  }

  var results = [];
  setBusy(callbacks, true);
  try {
    for (var applyIndex = 0; applyIndex < plans.length; applyIndex += 1) {
      var plan = plans[applyIndex];
      setMessage(
        callbacks,
        "Exporting " + (applyIndex + 1) + " of " + plans.length + ": " + plan.scope + "…",
        false
      );
      try {
        var applied = await applySnapshot(
          plan.scope,
          plan.preview,
          options.clientOptions || {}
        );
        results.push({ scope: plan.scope, payload: applied });
      } catch (error) {
        var detail = cleanString(error && error.message) || "Snapshot Export failed.";
        var partial = results.length
          ? " Exported " + results.length + " of " + plans.length + " scopes before the failure."
          : "";
        var workflowError = new Error("Export Scopes failed for " + plan.scope + ": " + detail + partial);
        workflowError.cause = error;
        throw workflowError;
      }
    }
  } finally {
    setBusy(callbacks, false);
  }

  var result = {
    cancelled: false,
    scopes: plans.map(function (plan) { return plan.scope; }),
    documentCount: plans.reduce(function (total, plan) {
      return total + plan.docIds.length;
    }, 0),
    results: results
  };
  setMessage(callbacks, docsViewerExportScopesWorkflowMessage(result), false);
  return result;
}
