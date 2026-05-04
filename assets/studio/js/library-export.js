import {
  DOCS_MANAGEMENT_ENDPOINTS,
  postJson,
  probeDocsManagementHealth
} from "./studio-transport.js";
import {
  getDocsScopeDataPath,
  getStudioDataPath,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  createStudioModalHost,
  renderStudioModalFrame
} from "./studio-modal.js";

const SCOPE = "library";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setText(node, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
}

function setStatus(node, state, message) {
  if (!node) return;
  node.textContent = normalizeText(message);
  if (state) {
    node.setAttribute("data-state", state);
  } else {
    node.removeAttribute("data-state");
  }
}

function documentLabel(count) {
  const safeCount = Number(count || 0);
  return safeCount === 1 ? "1 document" : `${safeCount} documents`;
}

function routeStateDetail(state) {
  return {
    route: "library-export",
    mode: "selection",
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.docs.length)
  };
}

function markBusy(state, busy) {
  setStudioRouteBusy(state.root, busy, routeStateDetail(state));
}

function markReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function enabledConfigsForScope(payload, scope) {
  const configs = Array.isArray(payload?.configs) ? payload.configs : [];
  return configs.filter((config) => {
    if (!config || config.enabled === false) return false;
    const scopes = Array.isArray(config.scopes) ? config.scopes : [];
    return scopes.includes(scope);
  });
}

function archivedRootIds(indexPayload) {
  const roots = indexPayload?.viewer_options?.manage_only_tree_root_ids;
  return new Set(Array.isArray(roots) ? roots.map(normalizeText).filter(Boolean) : ["_archive"]);
}

function buildVisibleDocs(indexPayload) {
  const sourceDocs = Array.isArray(indexPayload?.docs) ? indexPayload.docs : [];
  const archivedRoots = archivedRootIds(indexPayload);
  const archiveDescendants = new Set();
  const collectArchive = (docId) => {
    if (!docId || archiveDescendants.has(docId)) return;
    archiveDescendants.add(docId);
    sourceDocs.forEach((doc) => {
      if (normalizeText(doc?.parent_id) === docId) {
        collectArchive(normalizeText(doc.doc_id));
      }
    });
  };
  archivedRoots.forEach(collectArchive);

  const docs = sourceDocs.filter((doc) => {
    const docId = normalizeText(doc?.doc_id);
    if (!docId || archiveDescendants.has(docId)) return false;
    return doc.published !== false;
  });

  const visibleIds = new Set(docs.map((doc) => normalizeText(doc.doc_id)));
  const childrenByParent = new Map();
  docs.forEach((doc) => {
    const parentId = normalizeText(doc.parent_id);
    const effectiveParent = visibleIds.has(parentId) ? parentId : "";
    if (!childrenByParent.has(effectiveParent)) childrenByParent.set(effectiveParent, []);
    childrenByParent.get(effectiveParent).push(doc);
  });

  const orderedDocs = [];
  const depthById = new Map();
  const visit = (parentId, depth) => {
    const children = childrenByParent.get(parentId) || [];
    children.forEach((doc) => {
      const docId = normalizeText(doc.doc_id);
      orderedDocs.push(doc);
      depthById.set(docId, depth);
      visit(docId, depth + 1);
    });
  };
  visit("", 0);

  const orderedIds = new Set(orderedDocs.map((doc) => normalizeText(doc.doc_id)));
  docs.forEach((doc) => {
    const docId = normalizeText(doc.doc_id);
    if (!orderedIds.has(docId)) {
      orderedDocs.push(doc);
      depthById.set(docId, 0);
    }
  });

  return { docs: orderedDocs, childrenByParent, depthById };
}

function descendantIds(state, docId) {
  const ids = [];
  const collect = (parentId) => {
    const children = state.childrenByParent.get(parentId) || [];
    children.forEach((child) => {
      const childId = normalizeText(child.doc_id);
      if (!childId) return;
      ids.push(childId);
      collect(childId);
    });
  };
  collect(docId);
  return ids;
}

function selectableDocIds(state) {
  const missingOnly = state.missingSummaryOnly.checked && state.missingSummaryOnlyWrap.hidden === false;
  return state.docs
    .filter((doc) => !missingOnly || !normalizeText(doc.summary))
    .map((doc) => normalizeText(doc.doc_id))
    .filter(Boolean);
}

function syncCheckboxStates(state) {
  const visibleSelected = new Set(selectableDocIds(state).filter((docId) => state.selectedIds.has(docId)));
  state.listNode.querySelectorAll("[data-library-export-doc]").forEach((row) => {
    const docId = normalizeText(row.getAttribute("data-library-export-doc"));
    const checkbox = row.querySelector("input[type='checkbox']");
    if (!(checkbox instanceof HTMLInputElement)) return;
    const subtreeIds = [docId, ...descendantIds(state, docId)].filter((id) => rowMatchesSelectionFilter(state, id));
    const selectedCount = subtreeIds.filter((id) => visibleSelected.has(id)).length;
    checkbox.checked = subtreeIds.length > 0 && selectedCount === subtreeIds.length;
    checkbox.indeterminate = selectedCount > 0 && selectedCount < subtreeIds.length;
  });
}

function rowMatchesSelectionFilter(state, docId) {
  if (state.missingSummaryOnly.checked && state.missingSummaryOnlyWrap.hidden === false) {
    const doc = state.docsById.get(docId);
    return doc ? !normalizeText(doc.summary) : false;
  }
  return state.docsById.has(docId);
}

function applySelectionFilter(state) {
  const allowedIds = new Set(selectableDocIds(state));
  state.selectedIds.forEach((docId) => {
    if (!allowedIds.has(docId)) state.selectedIds.delete(docId);
  });
}

function updateSelectionSummary(state) {
  const count = state.selectedIds.size;
  setText(
    state.selectionSummary,
    getStudioText(
      state.config,
      count === 1
        ? "library_export.selection_summary_one"
        : "library_export.selection_summary",
      count === 1 ? "1 document selected." : "{count} documents selected.",
      { count }
    )
  );
}

function selectedConfig(state) {
  const configId = normalizeText(state.configSelect.value);
  return state.exportConfigs.find((config) => normalizeText(config.id) === configId) || null;
}

function syncConfigOptions(state) {
  const config = selectedConfig(state);
  const selection = config && typeof config.selection === "object" ? config.selection : {};
  const supportsMissing = Boolean(selection.supports_missing_summary_only);
  state.missingSummaryOnlyWrap.hidden = !supportsMissing;
  state.missingSummaryOnly.checked = supportsMissing && Boolean(selection.default_missing_summary_only);
  applySelectionFilter(state);
  renderDocList(state);
  updateStatus(state);
}

function updateStatus(state) {
  const config = selectedConfig(state);
  if (!config) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "library_export.no_config", "No enabled Library export configs found.")
    );
    return;
  }
  if (!state.serviceAvailable) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "library_export.service_unavailable",
        "Docs management service unavailable. Start bin/dev-studio to run exports."
      )
    );
    state.runButton.disabled = true;
    return;
  }
  state.runButton.disabled = false;
  setStatus(
    state.statusNode,
    "",
    getStudioText(
      state.config,
      "library_export.idle_status",
      ""
    )
  );
}

function renderConfigSelect(state) {
  state.configSelect.innerHTML = state.exportConfigs.map((config) => {
    const id = normalizeText(config.id);
    const label = normalizeText(config.label) || id;
    return `<option value="${escapeHtml(id)}">${escapeHtml(label)}</option>`;
  }).join("");
}

function renderDocRow(state, doc) {
  const docId = normalizeText(doc.doc_id);
  const title = normalizeText(doc.title) || docId;
  const depth = Math.max(0, Number(state.depthById.get(docId) || 0));
  const viewable = doc.viewable === true;
  return `
    <li class="tagStudioList__row tagStudioList__row--center libraryExportList__row" data-library-export-doc="${escapeHtml(docId)}" style="--library-export-depth: ${depth};">
      <label class="libraryExportList__label">
        <input class="libraryExportList__checkbox" type="checkbox" value="${escapeHtml(docId)}">
        <span class="libraryExportList__viewable${viewable ? " is-viewable" : ""}" aria-label="${viewable ? "viewable" : ""}"></span>
        <span class="libraryExportList__title">${escapeHtml(title)}</span>
      </label>
    </li>
  `;
}

function renderDocList(state) {
  const visibleDocIds = new Set(selectableDocIds(state));
  const rows = state.docs
    .filter((doc) => visibleDocIds.has(normalizeText(doc.doc_id)))
    .map((doc) => renderDocRow(state, doc));
  state.listNode.innerHTML = rows.length
    ? `<ul class="tagStudioList__rows libraryExportList__rows">${rows.join("")}</ul>`
    : `<p class="tagStudio__status">${escapeHtml(getStudioText(state.config, "library_export.empty_state", "No matching Library docs."))}</p>`;
  syncCheckboxStates(state);
  updateSelectionSummary(state);
}

function resetResult(state) {
  if (state.modalHost) state.modalHost.innerHTML = "";
}

function basename(path) {
  const value = normalizeText(path);
  if (!value) return "";
  const parts = value.split(/[\\/]+/).filter(Boolean);
  return parts[parts.length - 1] || value;
}

function outputFiles(payload) {
  const files = [];
  const outputFiles = Array.isArray(payload?.output_files) ? payload.output_files : [];
  outputFiles.forEach((file) => {
    const filename = basename(file);
    if (filename) files.push(filename);
  });
  const outputFile = basename(payload?.output_file);
  if (outputFile && !files.includes(outputFile)) files.push(outputFile);
  return files;
}

function countRows(state, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  const rows = [
    ["selected", "library_export.count_selected", "selected", Number(safeCounts.selected || 0)],
    ["exported", "library_export.count_exported", "exported", Number(safeCounts.exported || 0)],
    ["skipped", "library_export.count_skipped", "skipped", Number(safeCounts.skipped || 0)],
    ["failed", "library_export.count_failed", "failed", Number(safeCounts.failed || 0)],
    ["truncated", "library_export.count_truncated", "truncated", Number(safeCounts.truncated || 0)]
  ];
  return rows.map(([key, textKey, fallback, count]) => `
    <div class="libraryExportModal__countRow" data-count-key="${escapeHtml(key)}">
      <dt>${escapeHtml(getStudioText(state.config, textKey, fallback))}</dt>
      <dd>${escapeHtml(documentLabel(count))}</dd>
    </div>
  `).join("");
}

function issueList(state, warnings, errors) {
  const errorItems = Array.isArray(errors) ? errors.map(normalizeText).filter(Boolean) : [];
  const warningItems = Array.isArray(warnings) ? warnings.map(normalizeText).filter(Boolean) : [];
  const items = [...errorItems, ...warningItems];
  if (!items.length) return "";
  const heading = getStudioText(
    state.config,
    errorItems.length ? "library_export.issues_heading" : "library_export.warnings_heading",
    errorItems.length ? "Issues" : "Warnings"
  );
  return `
    <div class="libraryExportModal__issues">
      <h4>${escapeHtml(heading)}</h4>
      <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function showResultModal(state, payload, failed = false) {
  const files = outputFiles(payload);
  const fileText = files.join("\n");
  const fileLabel = getStudioText(state.config, "library_export.result_files_label", "files created");
  const emptyFiles = getStudioText(state.config, "library_export.result_files_empty", "No files created.");
  const bodyHtml = `
    <dl class="libraryExportModal__counts">
      ${countRows(state, payload?.counts)}
    </dl>
    <label class="libraryExportModal__files">
      <span>${escapeHtml(fileLabel)}</span>
      <textarea class="tagStudio__input libraryExportModal__fileList" readonly rows="${Math.max(1, files.length)}">${escapeHtml(fileText || emptyFiles)}</textarea>
    </label>
    ${issueList(state, payload?.warnings, payload?.errors)}
  `;
  const closeRole = "library-export-modal-close";
  state.modalHost.innerHTML = renderStudioModalFrame({
    hidden: false,
    modalRole: "library-export-result-modal",
    backdropRole: closeRole,
    titleId: "libraryExportResultModalTitle",
    title: failed
      ? getStudioText(state.config, "library_export.result_title_failed", "Export failed")
      : getStudioText(state.config, "library_export.result_title", "Export result"),
    bodyHtml,
    actions: [
      { role: closeRole, label: getStudioText(state.config, "library_export.result_close", "Close") }
    ]
  });
  state.modalHost.querySelectorAll(`[data-role="${closeRole}"]`).forEach((node) => {
    node.addEventListener("click", () => {
      state.modalHost.innerHTML = "";
    });
  });
}

function setDocAndDescendantSelection(state, docId, selected) {
  const ids = [docId, ...descendantIds(state, docId)].filter((id) => rowMatchesSelectionFilter(state, id));
  ids.forEach((id) => {
    if (selected) {
      state.selectedIds.add(id);
    } else {
      state.selectedIds.delete(id);
    }
  });
}

function handleListChange(state, event) {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) return;
  const row = target.closest("[data-library-export-doc]");
  const docId = normalizeText(row ? row.getAttribute("data-library-export-doc") : "");
  if (!docId) return;
  setDocAndDescendantSelection(state, docId, target.checked);
  syncCheckboxStates(state);
  updateSelectionSummary(state);
}

async function runExport(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  const config = selectedConfig(state);
  if (!config) {
    updateStatus(state);
    return;
  }
  const configId = normalizeText(config.id);
  const selection = config && typeof config.selection === "object" ? config.selection : {};
  const selectAll = normalizeText(selection.mode) === "all_matching";
  const docIds = selectAll ? [] : Array.from(state.selectedIds);
  if (!selectAll && !docIds.length) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "library_export.selection_required", "Select at least one document.")
    );
    return;
  }

  resetResult(state);
  state.isRunning = true;
  state.runButton.disabled = true;
  markBusy(state, true);
  setStatus(
    state.statusNode,
    "",
    getStudioText(state.config, "library_export.status_running", "Running Library export...")
  );

  try {
    const payload = await postJson(DOCS_MANAGEMENT_ENDPOINTS.exportDocs, {
      scope: SCOPE,
      config_id: configId,
      doc_ids: docIds,
      select_all: selectAll,
      missing_summary_only: state.missingSummaryOnlyWrap.hidden ? null : Boolean(state.missingSummaryOnly.checked)
    });
    showResultModal(state, payload);
    setStatus(
      state.statusNode,
      "success",
      payload.summary_text || getStudioText(state.config, "library_export.status_success", "Export completed.")
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    showResultModal(state, payload, true);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message)
        || getStudioText(state.config, "library_export.status_failed", "Export failed.")
    );
  } finally {
    state.isRunning = false;
    state.runButton.disabled = !state.serviceAvailable;
    markBusy(state, false);
  }
}

async function init() {
  const bootStatus = document.getElementById("libraryExportBootStatus");
  const root = document.getElementById("libraryExportRoot");
  if (!bootStatus || !root) return;
  initializeStudioRouteState(root, { route: "library-export", mode: "selection" });

  const state = {
    bootStatus,
    root,
    configLabelNode: document.getElementById("libraryExportConfigLabel"),
    configSelect: document.getElementById("libraryExportConfigSelect"),
    missingSummaryOnlyWrap: document.getElementById("libraryExportMissingSummaryWrap"),
    missingSummaryOnly: document.getElementById("libraryExportMissingSummaryOnly"),
    missingSummaryLabelNode: document.getElementById("libraryExportMissingSummaryLabel"),
    selectAllButton: document.getElementById("libraryExportSelectAll"),
    clearButton: document.getElementById("libraryExportClear"),
    statusNode: document.getElementById("libraryExportStatus"),
    selectionSummary: document.getElementById("libraryExportSelectionSummary"),
    listNode: document.getElementById("libraryExportList"),
    runButton: document.getElementById("libraryExportRun"),
    modalHost: null,
    config: null,
    exportConfigs: [],
    docs: [],
    docsById: new Map(),
    childrenByParent: new Map(),
    depthById: new Map(),
    selectedIds: new Set(),
    serviceAvailable: false,
    isRunning: false
  };

  const requiredNodes = [
    state.configLabelNode,
    state.configSelect,
    state.missingSummaryOnlyWrap,
    state.missingSummaryOnly,
    state.missingSummaryLabelNode,
    state.selectAllButton,
    state.clearButton,
    state.statusNode,
    state.selectionSummary,
    state.listNode,
    state.runButton
  ];
  if (requiredNodes.some((node) => !node)) return;
  state.modalHost = createStudioModalHost({ root });

  try {
    markBusy(state, true);
    state.config = await loadStudioConfig();
    state.serviceAvailable = Boolean(await probeDocsManagementHealth());
    const exportConfigPath = getStudioDataPath(state.config, "library_export_configs")
      || "/assets/studio/data/library_export_configs.json";
    const docsIndexPath = getDocsScopeDataPath(state.config, SCOPE, "index")
      || "/assets/data/docs/scopes/library/index.json";
    const [exportConfigPayload, docsIndexPayload] = await Promise.all([
      loadJson(exportConfigPath),
      loadJson(docsIndexPath)
    ]);

    state.exportConfigs = enabledConfigsForScope(exportConfigPayload, SCOPE);
    const docsTree = buildVisibleDocs(docsIndexPayload);
    state.docs = docsTree.docs;
    state.childrenByParent = docsTree.childrenByParent;
    state.depthById = docsTree.depthById;
    state.docsById = new Map(state.docs.map((doc) => [normalizeText(doc.doc_id), doc]));

    setText(state.configLabelNode, getStudioText(state.config, "library_export.config_label", "export pattern"));
    setText(
      state.missingSummaryLabelNode,
      getStudioText(state.config, "library_export.missing_summary_label", "missing summaries only")
    );
    setText(state.selectAllButton, getStudioText(state.config, "library_export.select_all", "Select all"));
    setText(state.clearButton, getStudioText(state.config, "library_export.clear", "Clear"));
    setText(state.runButton, getStudioText(state.config, "library_export.run_button", "Run export"));
    state.runButton.title = getStudioText(
      state.config,
      "library_export.run_disabled_title",
      "Requires the local docs-management service."
    );

    renderConfigSelect(state);
    syncConfigOptions(state);

    state.configSelect.addEventListener("change", () => syncConfigOptions(state));
    state.missingSummaryOnly.addEventListener("change", () => {
      applySelectionFilter(state);
      renderDocList(state);
      updateStatus(state);
    });
    state.selectAllButton.addEventListener("click", () => {
      selectableDocIds(state).forEach((docId) => state.selectedIds.add(docId));
      syncCheckboxStates(state);
      updateSelectionSummary(state);
    });
    state.clearButton.addEventListener("click", () => {
      state.selectedIds.clear();
      syncCheckboxStates(state);
      updateSelectionSummary(state);
    });
    state.listNode.addEventListener("change", (event) => handleListChange(state, event));
    state.runButton.addEventListener("click", () => {
      runExport(state).catch((error) => console.warn("library_export: unexpected run failure", error));
    });

    root.hidden = false;
    bootStatus.hidden = true;
    markReady(state, true);
  } catch (error) {
    console.warn("library_export: load failed", error);
    root.hidden = false;
    bootStatus.hidden = true;
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "library_export.load_failed", "Failed to load Library export data.")
    );
    markReady(state, true);
  } finally {
    markBusy(state, false);
  }
}

init();
