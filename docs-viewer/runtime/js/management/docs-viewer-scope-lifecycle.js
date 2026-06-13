import {
  applyScopeCreate,
  applyScopeDelete,
  previewScopeCreate,
  previewScopeDelete
} from "./docs-viewer-management-client.js";
import {
  openDocsViewerManagementModal
} from "./docs-viewer-management-modals.js";
import {
  scopeCreateSupported,
  scopeDeleteSupported,
  scopeLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";
import {
  escapeHtml
} from "../shared/docs-viewer-render.js";

export {
  scopeCreateSupported,
  scopeDeleteSupported,
  scopeLifecycleDeleteTargets
};

var DEFAULT_PUBLISHING_MODES = [
  "local_uncommitted",
  "local_committed"
];
var PUBLISHING_MODE_ORDER = [
  "local_uncommitted",
  "local_committed",
  "public_readonly"
];

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function managementText(state, key, fallback) {
  if (state && state.managementText && Object.prototype.hasOwnProperty.call(state.managementText, key)) {
    var value = state.managementText[key];
    return value == null ? fallback : normalizeText(value);
  }
  return fallback;
}

function publishingModes(capabilities) {
  var lifecycle = capabilities && capabilities.scope_lifecycle && typeof capabilities.scope_lifecycle === "object"
    ? capabilities.scope_lifecycle
    : null;
  var rawModes = lifecycle && Array.isArray(lifecycle.publishing_modes)
    ? lifecycle.publishing_modes
    : DEFAULT_PUBLISHING_MODES;
  var seen = new Set();
  var modes = rawModes.map(normalizeText).filter(function (mode) {
    if (!mode || seen.has(mode)) return false;
    seen.add(mode);
    return true;
  });
  var ordered = PUBLISHING_MODE_ORDER.filter(function (mode) {
    return modes.includes(mode);
  });
  return ordered.length ? ordered : DEFAULT_PUBLISHING_MODES.slice();
}

function modeLabel(state, mode) {
  var labels = {
    public_readonly: managementText(state, "scopePublicReadonlyMode", "public read-only scope"),
    local_committed: managementText(state, "scopeLocalCommittedMode", "committed manage-mode scope"),
    local_uncommitted: managementText(state, "scopeLocalUncommittedMode", "local-only uncommitted scope")
  };
  return labels[mode] || mode;
}

function modeNote(state, mode) {
  var notes = {
    public_readonly: managementText(state, "scopePublicReadonlyModeNote", "Creates a source root, scope config, read-only route, manifest record, and generated outputs when requested."),
    local_committed: managementText(state, "scopeLocalCommittedModeNote", "Creates tracked source, config, manifest, and non-public generated outputs under docs-viewer/generated/ when requested. No public route is created."),
    local_uncommitted: managementText(state, "scopeLocalUncommittedModeNote", "Creates local-only scope files and records the result as uncommitted local drift. No public route is created.")
  };
  return notes[mode] || "";
}

function slugFromScopeInput(value) {
  return normalizeText(value)
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function renderModeOptions(state, modes) {
  return modes.map(function (mode) {
    return '<option value="' + escapeHtml(mode) + '">' + escapeHtml(modeLabel(state, mode)) + '</option>';
  }).join("");
}

function renderCreateFormHtml(state, capabilities) {
  var modes = publishingModes(capabilities);
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(managementText(state, "scopeCreateIntro", "Create a Docs Viewer scope through the local management server.")) + '</p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeIdLabel", "scope id")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeTitleLabel", "title")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-title" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopePublishingModeLabel", "publishing mode")) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="scope-publishing-mode">' + renderModeOptions(state, modes) + '</select>' +
      '</label>' +
      '<p class="docsViewer__modalNote muted small" data-role="scope-mode-note"></p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeSourceRootLabel", "source root")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-source-root" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeDefaultDocIdLabel", "default doc id")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-default-doc-id" type="text" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field" data-role="scope-route-field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopePublicRoutePathLabel", "public route path")) + '</span>' +
        '<input class="docsViewer__fieldInput" data-role="scope-public-route-path" type="text" autocomplete="off" spellcheck="false">' +
      '</label>' +
      '<label class="docsViewer__field docsViewer__field--checkbox">' +
        '<input class="docsViewer__checkboxInput" data-role="scope-write-generated" type="checkbox" checked>' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeWriteGeneratedLabel", "write generated outputs immediately")) + '</span>' +
      '</label>' +
      '<label class="docsViewer__field docsViewer__field--checkbox">' +
        '<input class="docsViewer__checkboxInput" data-role="scope-build-search" type="checkbox" checked>' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeBuildSearchLabel", "build inline search")) + '</span>' +
      '</label>' +
    '</div>'
  );
}

function wireCreateForm(api, state) {
  var host = api.host;
  var scopeInput = host.querySelector('[data-role="scope-id"]');
  var titleInput = host.querySelector('[data-role="scope-title"]');
  var modeInput = host.querySelector('[data-role="scope-publishing-mode"]');
  var modeNoteNode = host.querySelector('[data-role="scope-mode-note"]');
  var sourceInput = host.querySelector('[data-role="scope-source-root"]');
  var defaultDocInput = host.querySelector('[data-role="scope-default-doc-id"]');
  var routeField = host.querySelector('[data-role="scope-route-field"]');
  var routeInput = host.querySelector('[data-role="scope-public-route-path"]');
  var writeGeneratedInput = host.querySelector('[data-role="scope-write-generated"]');
  var buildSearchInput = host.querySelector('[data-role="scope-build-search"]');

  function expectedTitle() {
    var slug = slugFromScopeInput(scopeInput && scopeInput.value);
    return slug.split(/[-_]+/g).filter(Boolean).map(function (part) {
      return part.charAt(0).toUpperCase() + part.slice(1);
    }).join(" ");
  }

  function expectedSourceRoot() {
    var slug = slugFromScopeInput(scopeInput && scopeInput.value);
    return slug ? "docs-viewer/source/" + slug : "";
  }

  function expectedDefaultDocId() {
    return slugFromScopeInput(scopeInput && scopeInput.value);
  }

  function expectedRoutePath() {
    var slug = slugFromScopeInput(scopeInput && scopeInput.value);
    return slug ? "/" + slug + "/" : "";
  }

  function applyScopeDefaults() {
    if (titleInput && (!titleInput.value || titleInput.dataset.auto === "true")) {
      titleInput.value = expectedTitle();
      titleInput.dataset.auto = "true";
    }
    if (sourceInput && (!sourceInput.value || sourceInput.dataset.auto === "true")) {
      sourceInput.value = expectedSourceRoot();
      sourceInput.dataset.auto = "true";
    }
    if (defaultDocInput && (!defaultDocInput.value || defaultDocInput.dataset.auto === "true")) {
      defaultDocInput.value = expectedDefaultDocId();
      defaultDocInput.dataset.auto = "true";
    }
    if (routeInput && (!routeInput.value || routeInput.dataset.auto === "true")) {
      routeInput.value = expectedRoutePath();
      routeInput.dataset.auto = "true";
    }
  }

  function syncMode() {
    var mode = normalizeText(modeInput && modeInput.value) || "local_uncommitted";
    if (modeNoteNode) modeNoteNode.textContent = modeNote(state, mode);
    if (routeField) routeField.hidden = mode !== "public_readonly";
    if (routeInput) routeInput.required = mode === "public_readonly";
  }

  function syncGeneratedOutputs() {
    if (!buildSearchInput || !writeGeneratedInput) return;
    buildSearchInput.disabled = !writeGeneratedInput.checked;
  }

  if (scopeInput) {
    scopeInput.addEventListener("input", applyScopeDefaults);
  }
  [titleInput, sourceInput, defaultDocInput, routeInput].forEach(function (input) {
    if (!input) return;
    input.dataset.auto = "true";
    input.addEventListener("input", function () {
      input.dataset.auto = "false";
    });
  });
  if (modeInput) {
    modeInput.addEventListener("change", syncMode);
  }
  if (writeGeneratedInput) {
    writeGeneratedInput.addEventListener("change", syncGeneratedOutputs);
  }
  syncMode();
  syncGeneratedOutputs();
}

function collectCreatePayload(api, state) {
  var host = api.host;
  var scopeId = normalizeText(host.querySelector('[data-role="scope-id"]')?.value).toLowerCase();
  var title = normalizeText(host.querySelector('[data-role="scope-title"]')?.value);
  var publishingMode = normalizeText(host.querySelector('[data-role="scope-publishing-mode"]')?.value) || "local_uncommitted";
  var sourceRoot = normalizeText(host.querySelector('[data-role="scope-source-root"]')?.value);
  var defaultDocId = normalizeText(host.querySelector('[data-role="scope-default-doc-id"]')?.value);
  var publicRoutePath = normalizeText(host.querySelector('[data-role="scope-public-route-path"]')?.value);
  var writeGenerated = Boolean(host.querySelector('[data-role="scope-write-generated"]')?.checked);
  var buildSearch = writeGenerated && Boolean(host.querySelector('[data-role="scope-build-search"]')?.checked);

  if (!scopeId || !title || !sourceRoot || !defaultDocId) {
    api.setStatus(managementText(state, "scopeCreateRequiredMessage", "Enter the required scope fields."));
    return null;
  }
  if (publishingMode === "public_readonly" && !publicRoutePath) {
    api.setStatus(managementText(state, "scopeCreateRouteRequiredMessage", "Enter a public route path for public read-only scopes."));
    return null;
  }

  return {
    scope_id: scopeId,
    title: title,
    source_root: sourceRoot,
    default_doc_id: defaultDocId,
    publishing_mode: publishingMode,
    public_route_path: publishingMode === "public_readonly" ? publicRoutePath : "",
    build_inline_search: buildSearch,
    write_generated_outputs: writeGenerated
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
      '<ul class="docsViewerScopeLifecycle__list">' + records.map(function (record) {
        var command = normalizeText(record && record.command);
        var status = normalizeText(record && record.status);
        return '<li>' + escapeHtml([command, status].filter(Boolean).join(" - ")) + '</li>';
      }).join("") + '</ul>' +
    '</section>'
  );
}

function renderUrls(urls) {
  var entries = [];
  if (urls && urls.management) entries.push(["management", urls.management]);
  if (urls && urls.public) entries.push(["public", urls.public]);
  if (!entries.length) return "";
  return (
    '<section class="docsViewerScopeLifecycle__section">' +
      '<h3>' + escapeHtml("URLs") + '</h3>' +
      '<dl class="docsViewerScopeLifecycle__summaryGrid">' + entries.map(function (entry) {
        return '<div><dt>' + escapeHtml(entry[0]) + '</dt><dd>' + escapeHtml(entry[1]) + '</dd></div>';
      }).join("") + '</dl>' +
    '</section>'
  );
}

function renderStorageContract(contract) {
  if (!contract || typeof contract !== "object") return "";
  var rows = [];
  var summary = normalizeText(contract.summary);
  var docsOutput = normalizeText(contract.docs_output);
  var searchOutput = normalizeText(contract.search_output);
  var publicAssets = contract.public_static_assets === true ? "yes" : "no";
  rows.push(["public static assets", publicAssets]);
  if (docsOutput) rows.push(["docs output", docsOutput]);
  if (searchOutput) rows.push(["search output", searchOutput]);
  return (
    '<section class="docsViewerScopeLifecycle__section">' +
      '<h3>' + escapeHtml("Storage") + '</h3>' +
      (summary ? '<p class="docsViewer__modalNote muted small">' + escapeHtml(summary) + '</p>' : "") +
      '<dl class="docsViewerScopeLifecycle__summaryGrid">' + rows.map(function (entry) {
        return '<div><dt>' + escapeHtml(entry[0]) + '</dt><dd>' + escapeHtml(entry[1]) + '</dd></div>';
      }).join("") + '</dl>' +
    '</section>'
  );
}

function renderPreviewHtml(payload, options) {
  var settings = options || {};
  var title = normalizeText(payload && payload.title) || normalizeText(payload && payload.scope_id);
  var summary = normalizeText(payload && payload.summary_text);
  var blockers = Array.isArray(payload && payload.blockers) ? payload.blockers : [];
  return (
    '<div class="docsViewerScopeLifecycle docsViewerScopeLifecycle--preview">' +
      (summary ? '<p class="docsViewer__modalNote muted small">' + escapeHtml(summary) + '</p>' : "") +
      (title ? '<dl class="docsViewerScopeLifecycle__summaryGrid"><div><dt>scope</dt><dd>' + escapeHtml(payload.scope_id) + '</dd></div><div><dt>title</dt><dd>' + escapeHtml(title) + '</dd></div></dl>' : "") +
      renderStorageContract(payload && payload.storage_contract) +
      (blockers.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Blockers</h3>' + renderList(blockers, "") + '</section>' : "") +
      (Array.isArray(payload && payload.warnings) && payload.warnings.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Warnings</h3>' + renderList(payload.warnings, "") + '</section>' : "") +
      (Array.isArray(payload && payload.created_files) ? '<section class="docsViewerScopeLifecycle__section"><h3>' + escapeHtml(settings.createdHeading || "Created files") + '</h3>' + renderList(payload && payload.created_files, "No files will be created.") + '</section>' : "") +
      '<section class="docsViewerScopeLifecycle__section"><h3>' + escapeHtml(settings.changedHeading || "Changed files") + '</h3>' + renderList(payload && payload.changed_files, "No files will be changed.") + '</section>' +
      (Array.isArray(payload && payload.deleted_files) && payload.deleted_files.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Deleted files</h3>' + renderList(payload.deleted_files, "") + '</section>' : "") +
      (Array.isArray(payload && payload.delete_files) && payload.delete_files.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Deleted files</h3>' + renderList(payload.delete_files, "") + '</section>' : "") +
      (Array.isArray(payload && payload.missing_files) && payload.missing_files.length ? '<section class="docsViewerScopeLifecycle__section"><h3>Missing files</h3>' + renderList(payload.missing_files, "") + '</section>' : "") +
      renderCommands(payload && payload.build_commands) +
      renderUrls(payload && payload.urls) +
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
    bodyHtml: renderPreviewHtml(options.payload, options),
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
    bodyHtml: renderPreviewHtml(options.payload, options),
    actions: [
      { role: "modal-primary", label: options.primaryLabel }
    ]
  });
}

export async function openCreateScopeFlow(options = {}) {
  var state = options.state || {};
  var callbacks = options.callbacks || {};
  var result = await openDocsViewerManagementModal({
    root: options.root,
    title: managementText(state, "scopeCreateTitle", "New scope"),
    size: "wide",
    bodyHtml: renderCreateFormHtml(state, options.capabilities),
    focusSelector: '[data-role="scope-id"]',
    actions: [
      { role: "modal-primary", label: managementText(state, "scopePreviewButton", "Preview") },
      { role: "modal-cancel", label: managementText(state, "cancelButton", "Cancel") }
    ],
    onOpen: function (api) {
      wireCreateForm(api, state);
    },
    onSubmit: function (api) {
      var payload = collectCreatePayload(api, state);
      return payload ? { confirmed: true, payload: payload } : false;
    }
  });
  if (!result || !result.confirmed || !result.payload) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "scopeCreatePreviewing", "Previewing new scope..."), false);
    render(callbacks);
    preview = await previewScopeCreate(result.payload, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "scopeCreateFailed", "New scope failed."), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: managementText(state, "scopeCreatePreviewTitle", "Preview new scope"),
    payload: preview,
    primaryLabel: managementText(state, "scopeSaveButton", "Save"),
    cancelLabel: managementText(state, "cancelButton", "Cancel")
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "scopeCreateSaving", "Saving new scope..."), false);
    render(callbacks);
    appliedPayload = await applyScopeCreate(result.payload, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "scopeCreateFailed", "New scope failed."), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: managementText(state, "scopeCreateResultTitle", "Scope created"),
    payload: appliedPayload,
    primaryLabel: managementText(state, "scopeResultOkButton", "OK")
  });
  return appliedPayload;
}

function renderDeleteSelectHtml(state, targets) {
  return (
    '<div class="docsViewerScopeLifecycle">' +
      '<p class="docsViewer__modalNote muted small">' + escapeHtml(managementText(state, "scopeDeleteIntro", "Select the user-created scope to delete.")) + '</p>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(managementText(state, "scopeDeleteTargetLabel", "scope")) + '</span>' +
        '<select class="docsViewer__fieldInput" data-role="scope-delete-target">' + targets.map(function (target) {
          var label = target.scopeId + (target.root ? " - " + target.root : "");
          return '<option value="' + escapeHtml(target.scopeId) + '">' + escapeHtml(label) + '</option>';
        }).join("") + '</select>' +
      '</label>' +
    '</div>'
  );
}

export async function openDeleteScopeFlow(options = {}) {
  var state = options.state || {};
  var callbacks = options.callbacks || {};
  var targets = scopeLifecycleDeleteTargets(options.capabilities);
  if (!targets.length) {
    setMessage(callbacks, managementText(state, "scopeDeleteNoTargets", "No user-created scopes are eligible for deletion."), true);
    return null;
  }

  var selection = await openDocsViewerManagementModal({
    root: options.root,
    title: managementText(state, "scopeDeleteTitle", "Delete scope"),
    size: "compact",
    bodyHtml: renderDeleteSelectHtml(state, targets),
    focusSelector: '[data-role="scope-delete-target"]',
    actions: [
      { role: "modal-primary", label: managementText(state, "scopePreviewButton", "Preview") },
      { role: "modal-cancel", label: managementText(state, "cancelButton", "Cancel") }
    ],
    onSubmit: function (api) {
      var scopeId = normalizeText(api.host.querySelector('[data-role="scope-delete-target"]')?.value);
      if (!scopeId) {
        api.setStatus(managementText(state, "scopeDeleteRequiredMessage", "Select a scope to delete."));
        return false;
      }
      return { confirmed: true, scopeId: scopeId };
    }
  });
  if (!selection || !selection.confirmed || !selection.scopeId) return null;

  var preview;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "scopeDeletePreviewing", "Previewing scope deletion..."), false);
    render(callbacks);
    preview = await previewScopeDelete(selection.scopeId, options.clientOptions);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "scopeDeleteFailed", "Delete scope failed."), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  if (!preview.allowed) {
    setMessage(callbacks, (preview.blockers || []).join("; ") || managementText(state, "scopeDeleteBlocked", "Delete scope is blocked."), true);
    await openResultModal({
      root: options.root,
      title: managementText(state, "scopeDeleteBlockedTitle", "Delete blocked"),
      payload: preview,
      primaryLabel: managementText(state, "scopeResultOkButton", "OK")
    });
    return null;
  }

  var confirmed = await openPreviewModal({
    root: options.root,
    title: managementText(state, "scopeDeletePreviewTitle", "Preview delete scope"),
    payload: preview,
    createdHeading: "Created files",
    changedHeading: "Changed files",
    primaryLabel: managementText(state, "scopeDeleteButton", "Delete"),
    cancelLabel: managementText(state, "cancelButton", "Cancel")
  });
  if (!confirmed) {
    setMessage(callbacks, "", false);
    return null;
  }

  var appliedPayload;
  try {
    setBusy(callbacks, true);
    setMessage(callbacks, managementText(state, "scopeDeleteDeleting", "Deleting scope..."), false);
    render(callbacks);
    appliedPayload = await applyScopeDelete(selection.scopeId, options.clientOptions);
    setMessage(callbacks, normalizeText(appliedPayload.summary_text), false);
    applied(callbacks, appliedPayload);
  } catch (error) {
    setMessage(callbacks, error && error.message ? error.message : managementText(state, "scopeDeleteFailed", "Delete scope failed."), true);
    return null;
  } finally {
    setBusy(callbacks, false);
    render(callbacks);
  }

  await openResultModal({
    root: options.root,
    title: managementText(state, "scopeDeleteResultTitle", "Scope deleted"),
    payload: appliedPayload,
    primaryLabel: managementText(state, "scopeResultOkButton", "OK")
  });
  return appliedPayload;
}
