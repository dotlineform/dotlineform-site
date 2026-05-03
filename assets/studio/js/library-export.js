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

function routeStateDetail(state) {
  return {
    route: "library-export",
    mode: "selection",
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

function selectedSummaryCount(state) {
  let missing = 0;
  state.selectedIds.forEach((docId) => {
    const doc = state.docsById.get(docId);
    if (doc && !normalizeText(doc.summary)) missing += 1;
  });
  return missing;
}

function updateSelectionSummary(state) {
  const count = state.selectedIds.size;
  const missing = selectedSummaryCount(state);
  setText(
    state.selectionSummary,
    getStudioText(
      state.config,
      count === 1
        ? "library_export.selection_summary_one"
        : "library_export.selection_summary",
      count === 1 ? "1 document selected; {missing} missing summaries." : "{count} documents selected; {missing} missing summaries.",
      { count, missing }
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
  setStatus(
    state.statusNode,
    "",
    getStudioText(
      state.config,
      "library_export.idle_status",
      "Select documents for the export. Running the export is enabled in Task 6."
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

async function init() {
  const bootStatus = document.getElementById("libraryExportBootStatus");
  const root = document.getElementById("libraryExportRoot");
  if (!bootStatus || !root) return;
  initializeStudioRouteState(root, { route: "library-export", mode: "selection" });

  const state = {
    bootStatus,
    root,
    introNode: document.getElementById("libraryExportIntro"),
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
    config: null,
    exportConfigs: [],
    docs: [],
    docsById: new Map(),
    childrenByParent: new Map(),
    depthById: new Map(),
    selectedIds: new Set()
  };

  const requiredNodes = [
    state.introNode,
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

  try {
    markBusy(state, true);
    state.config = await loadStudioConfig();
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

    setText(
      state.introNode,
      getStudioText(
        state.config,
        "library_export.intro",
        "Select a Library export pattern and the documents to include."
      )
    );
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
      "Export service endpoint will be added in Task 6."
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
