import {
  applySubScopeCreate,
  applySubScopeDelete,
  previewSubScopeCreate,
  previewSubScopeDelete
} from "./docs-viewer-management-client.js";
import {
  openDocsViewerManagementModal
} from "./docs-viewer-management-modals.js";
import {
  subScopeCreateSupported,
  subScopeDeleteSupported,
  subScopeLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";
import {
  escapeHtml
} from "../shared/docs-viewer-render.js";

export {
  subScopeCreateSupported,
  subScopeDeleteSupported,
  subScopeLifecycleDeleteTargets
};


var SCOPE_LIFECYCLE_TEXT = {
  cancelButton: "Cancel",
  scopePreviewButton: "Preview",
  scopeSaveButton: "Save",
  scopeDeleteButton: "Delete",
  scopeResultOkButton: "OK",
  scopeDeleteBlockedTitle: "Delete blocked",
  subScopeCreateTitle: "New sub-scope",
  subScopeIdLabel: "sub-scope id",
  subScopeTitleLabel: "title",
  subScopeCreateRequiredMessage: "Enter the required sub-scope fields.",
  subScopeCreatePreviewing: "Previewing new sub-scope...",
  subScopeCreatePreviewTitle: "Preview new sub-scope",
  subScopeCreateSaving: "Saving new sub-scope...",
  subScopeCreateFailed: "New sub-scope failed.",
  subScopeCreateResultTitle: "Sub-scope created",
  subScopeDeleteTitle: "Delete sub-scope",
  subScopeDeleteIntro: "Select the sub-scope to delete from the selected stage.",
  subScopeDeleteTargetLabel: "sub-scope",
  subScopeDeleteRequiredMessage: "Select a sub-scope to delete.",
  subScopeDeleteNoTargets: "No sub-scopes are configured for the selected stage.",
  subScopeDeletePreviewing: "Previewing sub-scope deletion...",
  subScopeDeletePreviewTitle: "Preview delete sub-scope",
  subScopeDeleteDeleting: "Deleting sub-scope...",
  subScopeDeleteFailed: "Delete sub-scope failed.",
  subScopeDeleteBlocked: "Delete sub-scope is blocked.",
  subScopeDeleteResultTitle: "Sub-scope deleted"
};

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function slugFromScopeInput(value) {
  return normalizeText(value)
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function humanTitleFromSlug(value) {
  return slugFromScopeInput(value).split(/[-_]+/g).filter(Boolean).map(function (part) {
    return part.charAt(0).toUpperCase() + part.slice(1);
  }).join(" ");
}

function renderCreateSubScopeFormHtml() {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.subScopeIdLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="sub-scope-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.subScopeTitleLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="sub-scope-title" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
    '</div>'
  );
}

function wireCreateSubScopeForm(api) {
  var host = api.host;
  var subScopeInput = host.querySelector('[data-role="sub-scope-id"]');
  var titleInput = host.querySelector('[data-role="sub-scope-title"]');

  function applyDefaults() {
    if (titleInput && (!titleInput.value || titleInput.dataset.auto === "true")) {
      titleInput.value = humanTitleFromSlug(subScopeInput && subScopeInput.value);
      titleInput.dataset.auto = "true";
    }
  }

  if (subScopeInput) {
    subScopeInput.addEventListener("input", applyDefaults);
  }
  if (titleInput) {
    titleInput.dataset.auto = "true";
    titleInput.addEventListener("input", function () {
      titleInput.dataset.auto = "false";
    });
  }
}

function collectCreateSubScopePayload(api) {
  var host = api.host;
  var subScope = slugFromScopeInput(host.querySelector('[data-role="sub-scope-id"]')?.value);
  var title = normalizeText(host.querySelector('[data-role="sub-scope-title"]')?.value);
  if (!subScope || !title) {
    api.setStatus(SCOPE_LIFECYCLE_TEXT.subScopeCreateRequiredMessage);
    return null;
  }
  return {
    sub_scope: subScope,
    title: title
  };
}

function fileLabel(record) {
  var kind = normalizeText(record && record.kind);
  var path = normalizeText(record && record.path);
  return [kind, path].filter(Boolean).join(": ");
}

function renderList(items, emptyText) {
  var records = Array.isArray(items) ? items.filter(Boolean) : [];
  if (!records.length) {
    return '<p class="docsViewerScopeLifecycle__empty muted small">' + escapeHtml(emptyText || "None") + '</p>';
  }
  return '<ul class="docsViewerScopeLifecycle__list">' + records.map(function (record) {
    var text = typeof record === "string" ? record : fileLabel(record);
    return '<li>' + escapeHtml(text) + '</li>';
  }).join("") + '</ul>';
}

function renderCommands(commands) {
  var records = Array.isArray(commands) ? commands : [];
  if (!records.length) return "";
  return (
    '<section class="docsViewerScopeLifecycle__section">' +
      '<h3>' + escapeHtml("Build commands") + '</h3>' +
      '<ul class="docsViewerScopeLifecycle__list docsViewerScopeLifecycle__list--plain">' + records.map(function (record) {
        var command = normalizeText(record && record.command);
        var status = normalizeText(record && record.status);
        return '<li>' + escapeHtml([command, status].filter(Boolean).join(" - ")) + '</li>';
      }).join("") + '</ul>' +
    '</section>'
  );
}

function renderDetailRows(rows, emptyText) {
  var entries = Array.isArray(rows) ? rows.filter(function (entry) {
    return Array.isArray(entry) && normalizeText(entry[0]) && normalizeText(entry[1]);
  }) : [];
  if (!entries.length) {
    return '<p class="docsViewerScopeLifecycle__empty muted small">' + escapeHtml(emptyText || "None") + '</p>';
  }
  return '<dl class="docsViewerScopeLifecycle__detailGrid">' + entries.map(function (entry) {
    return '<dt>' + escapeHtml(entry[0]) + ':</dt><dd>' + escapeHtml(entry[1]) + '</dd>';
  }).join("") + '</dl>';
}

function hasDetailRows(rows) {
  return Array.isArray(rows) && rows.some(function (entry) {
    return Array.isArray(entry) && normalizeText(entry[0]) && normalizeText(entry[1]);
  });
}

function lifecyclePathRecords(payload) {
  return [
    payload && payload.created_files,
    payload && payload.publish_files,
    payload && payload.delete_files,
    payload && payload.deleted_files,
    payload && payload.missing_files
  ].flatMap(function (records) {
    return Array.isArray(records) ? records : [];
  });
}

function lifecycleRecord(payload, kinds) {
  var allowedKinds = new Set(Array.isArray(kinds) ? kinds : [kinds]);
  return lifecyclePathRecords(payload).find(function (record) {
    return allowedKinds.has(normalizeText(record && record.kind));
  }) || null;
}

function externalLifecycleRoot(payload) {
  var record = lifecycleRecord(payload, ["sub_scope_source_root"]);
  var path = normalizeText(record && record.path);
  var suffix = "/" + payload.stage + "/source/sub-scopes/" + payload.sub_scope;
  return path.endsWith(suffix) ? path.slice(0, -suffix.length) : "";
}

function lifecycleRelativePath(value, root) {
  var path = normalizeText(value);
  if (!path) return "";
  if (root && path.startsWith(root + "/")) return path.slice(root.length + 1);
  if (root) {
    var anchors = ["/source/", "/published/"];
    var anchor = anchors.find(function (candidate) {
      return path.includes(candidate);
    });
    if (anchor) return path.slice(path.indexOf(anchor) + 1);
  }
  return path;
}

function lifecycleFileRows(payload, records) {
  var labels = {
    default_source_doc: "default doc",
    published_docs_index_tree: "index",
    published_docs_recent: "Recent",
    published_search_index: "search index",
    public_docs_index_tree: "public index",
    public_docs_recent: "public Recent",
    public_search_index: "public search index",
    route_file: "public route",
    workspace_config: "workspace config",
    route_config: "route config",
    public_route_config: "public route config"
  };
  var omittedKinds = new Set([
    "source_root",
    "scope_root",
    "published_docs_root",
    "published_docs_payload_root",
    "public_docs_root",
    "public_docs_payload_root",
    "sub_scope_source_root",
    "sub_scope_published_docs_root",
    "sub_scope_published_docs_payload_root",
    "sub_scope_public_docs_root",
    "sub_scope_public_docs_payload_root"
  ]);
  var root = externalLifecycleRoot(payload);
  return (Array.isArray(records) ? records : []).filter(function (record) {
    return !omittedKinds.has(normalizeText(record && record.kind));
  }).map(function (record) {
    var kind = normalizeText(record && record.kind);
    var label = labels[kind] || kind.replace(/_/g, " ");
    return [label, lifecycleRelativePath(record && record.path, root)];
  });
}

function lifecycleOverviewRows(payload) {
  return [
    ["stage", payload.stage], ["sub-scope", payload.sub_scope], ["title", payload.title],
    ["url", payload.urls && payload.urls.management]
  ];
}

function lifecycleStorageRows(payload, root) {
  var contract = payload && payload.storage_contract && typeof payload.storage_contract === "object"
    ? payload.storage_contract
    : {};
  var sourceRecord = lifecycleRecord(payload, ["source_root", "sub_scope_source_root"]);
  var publishedRecord = lifecycleRecord(payload, ["published_docs_root", "sub_scope_published_docs_root"]);
  var publishedSearchRecord = lifecycleRecord(payload, "published_search_index");
  var publicRecord = lifecycleRecord(payload, ["public_docs_root", "sub_scope_public_docs_root"]);
  var publicSearchRecord = lifecycleRecord(payload, "public_search_index");
  var docsOutput = normalizeText(contract.docs_output);
  var publishOutput = normalizeText(contract.publish_output);
  var searchOutput = normalizeText(contract.search_output);
  var publishSearchOutput = normalizeText(contract.publish_search_output);
  var deployOutput = normalizeText(contract.deploy_output);
  var deploySearchOutput = normalizeText(contract.deploy_search_output);
  return [
    ["source", lifecycleRelativePath(contract.source_root || (sourceRecord && sourceRecord.path), root)],
    ["generated documents", lifecycleRelativePath(docsOutput, root)],
    ["generated search", lifecycleRelativePath(searchOutput, root)],
    ["published documents", lifecycleRelativePath(publishOutput || (publishedRecord && publishedRecord.path), root)],
    ["published search", lifecycleRelativePath(publishSearchOutput || (publishedSearchRecord && publishedSearchRecord.path), root)],
    ["deployment documents", lifecycleRelativePath(deployOutput || (publicRecord && publicRecord.path), root)],
    ["deployment search", lifecycleRelativePath(deploySearchOutput || (publicSearchRecord && publicSearchRecord.path), root)]
  ];
}

function renderLifecycleFileSection(heading, payload, records) {
  var rows = lifecycleFileRows(payload, records);
  if (!rows.length) return "";
  return '<section class="docsViewerScopeLifecycle__section"><h3>' + escapeHtml(heading) + '</h3>' +
    renderDetailRows(rows, "") + '</section>';
}

function renderPreviewHtml(payload) {
  var root = externalLifecycleRoot(payload);
  var storageRows = lifecycleStorageRows(payload, root);
  var blockers = Array.isArray(payload && payload.blockers) ? payload.blockers : [];
  var warnings = Array.isArray(payload && payload.warnings) ? payload.warnings : [];
  var deletedFiles = Array.isArray(payload && payload.deleted_files) && payload.deleted_files.length
    ? payload.deleted_files
    : payload && payload.delete_files;
  return (
    '<div class="docsViewerScopeLifecycle docsViewerScopeLifecycle--preview">' +
      renderDetailRows(lifecycleOverviewRows(payload, root), "") +
      (hasDetailRows(storageRows) ? renderDetailRows(storageRows, "") : "") +
      (blockers.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Blockers</h3>' + renderList(blockers, "") + '</section>' : "") +
      (warnings.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Warnings</h3>' + renderList(warnings, "") + '</section>' : "") +
      renderLifecycleFileSection("Created files", payload, payload && payload.created_files) +
      renderLifecycleFileSection("Published files", payload, payload && payload.publish_files) +
      renderLifecycleFileSection("Changed files (repo)", payload, payload && payload.changed_files) +
      renderLifecycleFileSection("Deleted files", payload, deletedFiles) +
      renderLifecycleFileSection("Missing files", payload, payload && payload.missing_files) +
      renderCommands(payload && payload.build_commands) +
    '</div>'
  );
}

function setBusy(callbacks, busy) {
  if (callbacks && typeof callbacks.setBusy === "function") callbacks.setBusy(Boolean(busy));
}

function setMessage(callbacks, message, isError) {
  if (callbacks && typeof callbacks.setMessage === "function") callbacks.setMessage(message, isError);
}

function render(callbacks) {
  if (callbacks && typeof callbacks.render === "function") callbacks.render();
}

function applied(callbacks, payload) {
  if (callbacks && typeof callbacks.onApplied === "function") callbacks.onApplied(payload);
}

async function openPreviewModal(options) {
  var result = await openDocsViewerManagementModal({
    root: options.root,
    title: options.title,
    size: "wide",
    bodyHtml: renderPreviewHtml(options.payload),
    actions: [
      { role: "modal-primary", label: options.primaryLabel },
      { role: "modal-cancel", label: options.cancelLabel }
    ]
  });
  return Boolean(result && result.confirmed);
}

async function openResultModal(options) {
  await openDocsViewerManagementModal({
    root: options.root,
    title: options.title,
    size: "wide",
    bodyHtml: renderPreviewHtml(options.payload),
    actions: [
      { role: "modal-primary", label: options.primaryLabel }
    ]
  });
}

export async function openCreateSubScopeFlow(options = {}) {
  var callbacks = options.callbacks || {};
  var result = await openDocsViewerManagementModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeCreateTitle,
    size: "compact",
    bodyHtml: renderCreateSubScopeFormHtml(),
    focusSelector: '[data-role="sub-scope-id"]',
    actions: [
      { role: "modal-primary", label: SCOPE_LIFECYCLE_TEXT.scopePreviewButton },
      { role: "modal-cancel", label: SCOPE_LIFECYCLE_TEXT.cancelButton }
    ],
    onOpen: function (api) {
      wireCreateSubScopeForm(api);
    },
    onSubmit: function (api) {
      var payload = collectCreateSubScopePayload(api);
      return payload ? { confirmed: true, payload: payload } : false;
    }
  });
  if (!result || !result.confirmed || !result.payload) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeCreatePreviewing, false);
    render(callbacks);
    preview = await previewSubScopeCreate(result.payload, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.subScopeCreateFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeCreatePreviewTitle,
    payload: preview,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeSaveButton,
    cancelLabel: SCOPE_LIFECYCLE_TEXT.cancelButton
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeCreateSaving, false);
    render(callbacks);
    appliedPayload = await applySubScopeCreate(Object.assign({}, result.payload, {
      planned_report_host_identity: preview.planned_report_host_identity
    }), options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.subScopeCreateFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeCreateResultTitle,
    payload: appliedPayload,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
  });
  if (typeof callbacks.followCreatedSubScopeReport === "function") {
    await callbacks.followCreatedSubScopeReport(appliedPayload);
  }
  return appliedPayload;
}

function renderDeleteSubScopeSelectHtml(targets) {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.subScopeDeleteIntro) + '</p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(SCOPE_LIFECYCLE_TEXT.subScopeDeleteTargetLabel) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="sub-scope-delete-target">' + targets.map(function (target) {
          var label = target.subScope + (target.title ? " - " + target.title : "");
          return '<option value="' + escapeHtml(target.subScope) + '">' + escapeHtml(label) + '</option>';
        }).join("") + '</select>' +
      '</label>' +
    '</div>'
  );
}

export async function openDeleteSubScopeFlow(options = {}) {
  var callbacks = options.callbacks || {};
  var targets = subScopeLifecycleDeleteTargets(options.capabilities, options.clientOptions.stage);
  if (!targets.length) {
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeDeleteNoTargets, true);
    return null;
  }

  var selection = await openDocsViewerManagementModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeDeleteTitle,
    size: "compact",
    bodyHtml: renderDeleteSubScopeSelectHtml(targets),
    focusSelector: '[data-role="sub-scope-delete-target"]',
    actions: [
      { role: "modal-primary", label: SCOPE_LIFECYCLE_TEXT.scopePreviewButton },
      { role: "modal-cancel", label: SCOPE_LIFECYCLE_TEXT.cancelButton }
    ],
    onSubmit: function (api) {
      var subScope = normalizeText(api.host.querySelector('[data-role="sub-scope-delete-target"]')?.value);
      if (!subScope) {
        api.setStatus(SCOPE_LIFECYCLE_TEXT.subScopeDeleteRequiredMessage);
        return false;
      }
      return { confirmed: true, subScope: subScope };
    }
  });
  if (!selection || !selection.confirmed || !selection.subScope) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeDeletePreviewing, false);
    render(callbacks);
    preview = await previewSubScopeDelete(selection.subScope, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.subScopeDeleteFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  if (!preview.allowed) {
    setMessage(callbacks, (preview.blockers || []).join("; ") || SCOPE_LIFECYCLE_TEXT.subScopeDeleteBlocked, true);
    await openResultModal({
      root: options.root,
      title: SCOPE_LIFECYCLE_TEXT.scopeDeleteBlockedTitle,
      payload: preview,
      primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
    });
    return null;
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeDeletePreviewTitle,
    payload: preview,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeDeleteButton,
    cancelLabel: SCOPE_LIFECYCLE_TEXT.cancelButton
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, SCOPE_LIFECYCLE_TEXT.subScopeDeleteDeleting, false);
    render(callbacks);
    appliedPayload = await applySubScopeDelete(selection.subScope, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : SCOPE_LIFECYCLE_TEXT.subScopeDeleteFailed, true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: SCOPE_LIFECYCLE_TEXT.subScopeDeleteResultTitle,
    payload: appliedPayload,
    primaryLabel: SCOPE_LIFECYCLE_TEXT.scopeResultOkButton
  });
  return appliedPayload;
}
