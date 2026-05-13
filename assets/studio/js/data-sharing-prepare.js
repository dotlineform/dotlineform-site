import {
  DATA_SHARING_ENDPOINTS,
  DOCS_MANAGEMENT_ENDPOINTS,
  postJson,
  probeDataSharingHealth
} from "./studio-transport.js";
import {
  getDocsScopeDataPath,
  getStudioDataPath,
  getStudioText,
  loadStudioConfigWithText
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
import { buildStudioActivityContext } from "./studio-activity-context.js";
import {
  workflowCapabilityForOperation,
  workflowDomainForKey,
  workflowDomainFromUrl,
  workflowDomainIsActive,
  workflowScopeParamForKey,
  workflowDomainsForOperation
} from "./data-sharing-adapters.js";

const DEFAULT_SCOPE = "library";
const WORKFLOW_SCOPES = [
  { key: "library", labelKey: "scope_library", fallback: "library" },
  { key: "tags", labelKey: "scope_tags", fallback: "tags" }
];
const LIST_FILTERS = [
  { key: "all", labelKey: "filter_show_all", fallback: "show all [{count}]" },
  { key: "no_content", labelKey: "filter_no_content", fallback: "no content [{count}]" },
  { key: "not_viewable", labelKey: "filter_not_viewable", fallback: "not viewable [{count}]" }
];
const FORMAT_OPTIONS = [
  { key: "json", labelKey: "format_json", fallback: "JSON" },
  { key: "jsonl", labelKey: "format_jsonl", fallback: "JSONL" }
];

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

function countLabel(count, unit = "document") {
  const safeCount = Number(count || 0);
  const normalizedUnit = normalizeText(unit) || "document";
  if (normalizedUnit === "record") return safeCount === 1 ? "1 record" : `${safeCount} records`;
  if (normalizedUnit === "file") return safeCount === 1 ? "1 file" : `${safeCount} files`;
  return documentLabel(safeCount);
}

function workflowScopeFromUrl(domains = WORKFLOW_SCOPES) {
  return workflowDomainFromUrl(domains, DEFAULT_SCOPE);
}

function scopeLabel(state, scope = state.scope) {
  const item = workflowDomainForKey(state.workflowScopes, scope) || WORKFLOW_SCOPES[0];
  if (item.labelKey) return getStudioText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback);
  return normalizeText(item.label) || item.fallback || scope;
}

function scopeTitle(state, scope = state.scope) {
  const label = scopeLabel(state, scope);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : scope;
}

function renderScopeSelect(state) {
  state.scopeSelect.innerHTML = state.workflowScopes.map((item) => {
    const label = item.labelKey
      ? getStudioText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback)
      : (normalizeText(item.label) || item.fallback);
    const selected = item.key === state.scope ? " selected" : "";
    return `<option value="${escapeHtml(item.key)}"${selected}>${escapeHtml(label)}</option>`;
  }).join("");
}

function updateScopeUrl(scope, domains = WORKFLOW_SCOPES) {
  const nextScope = normalizeText(scope).toLowerCase();
  if (!domains.some((item) => item.key === nextScope)) return;
  const scopeParam = workflowScopeParamForKey(domains, nextScope);
  const url = new URL(window.location.href);
  if (nextScope === DEFAULT_SCOPE) {
    url.searchParams.delete("scope");
  } else {
    url.searchParams.set("scope", scopeParam);
  }
  window.location.href = url.toString();
}

async function loadAdapterRegistry(config) {
  const registryPath = getStudioDataPath(config, "data_sharing_adapters")
    || "/assets/studio/data/data_sharing_adapters.json";
  return loadJson(registryPath);
}

function scopeUnavailableMessage(state) {
  const domain = workflowDomainForKey(state.workflowScopes, state.scope);
  return normalizeText(domain && domain.message)
    || getStudioText(
      state.config,
      "data_sharing_prepare.scope_unsupported",
      "{scope_label} package preparation is not implemented yet.",
      { scope_label: scopeTitle(state) }
    );
}

function routeStateDetail(state) {
  if (state && state.root) state.root.dataset.studioScope = state.scope;
  return {
    route: "data-sharing-prepare",
    mode: prepareSelectionModel(state),
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.docs.length || state.exportConfigs.length)
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

function docsGeneratedIndexUrl(scope) {
  const url = new URL(DOCS_MANAGEMENT_ENDPOINTS.generatedIndex);
  url.searchParams.set("scope", scope);
  return url.href;
}

function enabledConfigsForScope(payload, scope) {
  const configs = Array.isArray(payload?.configs) ? payload.configs : [];
  return configs.filter((config) => {
    if (!config || config.enabled === false) return false;
    const scopes = Array.isArray(config.scopes) ? config.scopes : [];
    return scopes.includes(scope);
  });
}

function prepareSelectionModel(state) {
  return normalizeText(state?.prepareCapability?.capability?.selection_model) || "documents";
}

function usesDocumentSelection(state) {
  return prepareSelectionModel(state) === "documents";
}

function prepareProfilesForCapability(capabilityInfo) {
  const profiles = Array.isArray(capabilityInfo?.capability?.sharing_profiles)
    ? capabilityInfo.capability.sharing_profiles
    : [];
  return profiles.filter((profile) => profile && profile.enabled !== false);
}

function buildVisibleDocs(indexPayload) {
  const sourceDocs = Array.isArray(indexPayload?.docs) ? indexPayload.docs : [];
  const docs = sourceDocs.filter((doc) => {
    const docId = normalizeText(doc?.doc_id);
    if (!docId) return false;
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

function contentTextLength(doc) {
  const value = Number(doc && doc.content_text_length);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function docHasNoContent(doc) {
  return contentTextLength(doc) === 0;
}

function docMatchesListFilter(state, doc) {
  if (!doc) return false;
  if (state.listFilter === "no_content") return docHasNoContent(doc);
  if (state.listFilter === "not_viewable") return doc.published !== false && doc.viewable === false;
  return true;
}

function docMatchesConfigFilter(state, docId) {
  const missingOnly = state.missingSummaryOnly.checked && state.missingSummaryOnlyWrap.hidden === false;
  const doc = state.docsById.get(docId);
  if (!doc) return false;
  return !missingOnly || !normalizeText(doc.summary);
}

function rowMatchesCurrentFilters(state, docId) {
  const doc = state.docsById.get(docId);
  return Boolean(doc && docMatchesConfigFilter(state, docId) && docMatchesListFilter(state, doc));
}

function selectableDocIds(state, { visibleOnly = false } = {}) {
  return state.docs
    .filter((doc) => {
      const docId = normalizeText(doc.doc_id);
      if (!docMatchesConfigFilter(state, docId)) return false;
      return !visibleOnly || docMatchesListFilter(state, doc);
    })
    .map((doc) => normalizeText(doc.doc_id))
    .filter(Boolean);
}

function syncCheckboxStates(state) {
  const visibleSelected = new Set(
    selectableDocIds(state, { visibleOnly: true }).filter((docId) => state.selectedIds.has(docId))
  );
  state.listNode.querySelectorAll("[data-data-sharing-prepare-doc]").forEach((row) => {
    const docId = normalizeText(row.getAttribute("data-data-sharing-prepare-doc"));
    const checkbox = row.querySelector("input[type='checkbox']");
    if (!(checkbox instanceof HTMLInputElement)) return;
    const subtreeIds = [docId, ...descendantIds(state, docId)].filter((id) => rowMatchesCurrentFilters(state, id));
    const selectedCount = subtreeIds.filter((id) => visibleSelected.has(id)).length;
    checkbox.checked = subtreeIds.length > 0 && selectedCount === subtreeIds.length;
    checkbox.indeterminate = selectedCount > 0 && selectedCount < subtreeIds.length;
  });
}

function applySelectionFilter(state) {
  if (!usesDocumentSelection(state)) {
    state.selectedIds.clear();
    return;
  }
  const allowedIds = new Set(selectableDocIds(state));
  state.selectedIds.forEach((docId) => {
    if (!allowedIds.has(docId)) state.selectedIds.delete(docId);
  });
}

function updateSelectionSummary(state) {
  if (!usesDocumentSelection(state)) {
    setText(
      state.selectionSummary,
      getStudioText(
        state.config,
        "data_sharing_prepare.selection_not_required",
        "No record selection required."
      )
    );
    return;
  }
  const count = state.selectedIds.size;
  setText(
    state.selectionSummary,
    getStudioText(
      state.config,
      count === 1
        ? "data_sharing_prepare.selection_summary_one"
        : "data_sharing_prepare.selection_summary",
      count === 1 ? "1 document selected." : "{count} documents selected.",
      { count }
    )
  );
}

function listFilterCounts(state) {
  const docs = state.docs.filter((doc) => docMatchesConfigFilter(state, normalizeText(doc.doc_id)));
  return {
    all: docs.length,
    no_content: docs.filter((doc) => docHasNoContent(doc)).length,
    not_viewable: docs.filter((doc) => doc.published !== false && doc.viewable === false).length
  };
}

function renderListFilters(state) {
  const actions = state.filterNode.closest(".dataSharingPreparePage__listActions");
  if (!usesDocumentSelection(state)) {
    if (actions) actions.hidden = true;
    state.filterNode.innerHTML = "";
    return;
  }
  if (actions) actions.hidden = false;
  const counts = listFilterCounts(state);
  state.filterNode.innerHTML = LIST_FILTERS.map((filter) => {
    const count = Number(counts[filter.key] || 0);
    const active = state.listFilter === filter.key;
    const label = getStudioText(state.config, `data_sharing_prepare.${filter.labelKey}`, filter.fallback, { count });
    return `
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" data-data-sharing-prepare-filter="${escapeHtml(filter.key)}" data-state="${active ? "active" : ""}" aria-pressed="${active ? "true" : "false"}">
        ${escapeHtml(label)}
      </button>
    `;
  }).join("");
}

function selectedConfig(state) {
  const configId = normalizeText(state.configSelect.value);
  return state.exportConfigs.find((config) => normalizeText(config.id) === configId) || null;
}

function supportedFormatsForConfig(config) {
  const target = config && typeof config.target === "object" ? config.target : {};
  const configured = Array.isArray(target.supported_formats)
    ? target.supported_formats.map(normalizeText).filter(Boolean)
    : [];
  const fallback = normalizeText(target.format);
  const formats = configured.length ? configured : [fallback].filter(Boolean);
  return formats.filter((format, index) => FORMAT_OPTIONS.some((item) => item.key === format) && formats.indexOf(format) === index);
}

function defaultFormatForConfig(config) {
  const formats = supportedFormatsForConfig(config);
  const target = config && typeof config.target === "object" ? config.target : {};
  const preferred = normalizeText(target.format);
  return formats.includes(preferred) ? preferred : formats[0] || "";
}

function renderFormatOptions(state) {
  const config = selectedConfig(state);
  const supportedFormats = supportedFormatsForConfig(config);
  if (!config) {
    state.formatOptionsNode.innerHTML = "";
    state.targetFormat = "";
    return;
  }
  if (!supportedFormats.includes(state.targetFormat)) {
    state.targetFormat = defaultFormatForConfig(config);
  }
  state.formatOptionsNode.innerHTML = FORMAT_OPTIONS.map((format) => {
    const supported = supportedFormats.includes(format.key);
    const checked = state.targetFormat === format.key;
    const label = getStudioText(state.config, `data_sharing_prepare.${format.labelKey}`, format.fallback);
    return `
      <label class="dataSharingPreparePage__formatOption">
        <input type="radio" name="dataSharingPrepareFormat" value="${escapeHtml(format.key)}"${checked ? " checked" : ""}${supported ? "" : " disabled"}>
        <span class="tagStudio__keyPill tagStudioFilters__groupBtn" data-state="${checked ? "active" : ""}" aria-disabled="${supported ? "false" : "true"}">${escapeHtml(label)}</span>
      </label>
    `;
  }).join("");
}

function syncConfigOptions(state) {
  const config = selectedConfig(state);
  const selection = config && typeof config.selection === "object" ? config.selection : {};
  const supportsMissing = Boolean(selection.supports_missing_summary_only);
  state.missingSummaryOnlyWrap.hidden = !usesDocumentSelection(state) || !supportsMissing;
  state.missingSummaryOnly.checked = supportsMissing && Boolean(selection.default_missing_summary_only);
  state.targetFormat = defaultFormatForConfig(config);
  renderFormatOptions(state);
  applySelectionFilter(state);
  renderListFilters(state);
  renderDocList(state);
  updateStatus(state);
}

function updateStatus(state) {
  if (!workflowDomainIsActive(state.workflowScopes, state.scope)) {
    setStatus(state.statusNode, "warn", scopeUnavailableMessage(state));
    state.runButton.disabled = true;
    return;
  }
  const config = selectedConfig(state);
  if (!config) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "data_sharing_prepare.no_config",
        "No enabled {scope_label} sharing profiles found.",
        { scope_label: scopeTitle(state) }
      )
    );
    state.runButton.disabled = true;
    return;
  }
  if (usesDocumentSelection(state) && state.docsIndexError) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "data_sharing_prepare.docs_index_unavailable",
        "No generated {scope_label} data index is available for this sharing profile.",
        { scope_label: scopeTitle(state) }
      )
    );
    state.runButton.disabled = true;
    return;
  }
  if (!state.serviceAvailable) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "data_sharing_prepare.service_unavailable",
        "Docs management service unavailable. Start bin/dev-studio to prepare packages."
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
      "data_sharing_prepare.idle_status",
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
  const noContent = docHasNoContent(doc);
  return `
    <li class="tagStudioList__row tagStudioList__row--center dataSharingPrepareList__row" data-data-sharing-prepare-doc="${escapeHtml(docId)}" data-data-sharing-prepare-viewable="${viewable ? "true" : "false"}" data-data-sharing-prepare-no-content="${noContent ? "true" : "false"}" style="--data-sharing-prepare-depth: ${depth};">
      <label class="dataSharingPrepareList__label">
        <input class="dataSharingPrepareList__checkbox" type="checkbox" value="${escapeHtml(docId)}">
        <span class="dataSharingPrepareList__viewable${viewable ? " is-viewable" : ""}" aria-label="${viewable ? "viewable" : ""}"></span>
        <span class="dataSharingPrepareList__title">${escapeHtml(title)}</span>
      </label>
    </li>
  `;
}

function renderDocList(state) {
  if (!usesDocumentSelection(state)) {
    state.listNode.innerHTML = `<p class="tagStudio__status">${escapeHtml(getStudioText(
      state.config,
      "data_sharing_prepare.profile_only_empty_state",
      "This profile packages the selected data family."
    ))}</p>`;
    updateSelectionSummary(state);
    return;
  }
  const visibleDocIds = new Set(selectableDocIds(state, { visibleOnly: true }));
  const rows = state.docs
    .filter((doc) => visibleDocIds.has(normalizeText(doc.doc_id)))
    .map((doc) => renderDocRow(state, doc));
  state.listNode.innerHTML = rows.length
    ? `<ul class="tagStudioList__rows dataSharingPrepareList__rows">${rows.join("")}</ul>`
    : `<p class="tagStudio__status">${escapeHtml(getStudioText(
      state.config,
      "data_sharing_prepare.empty_state",
      "No matching {scope_label} documents.",
      { scope_label: scopeTitle(state) }
    ))}</p>`;
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

function countRows(state, counts, payload) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  const unit = normalizeText(payload?.count_unit) || "document";
  const rows = [
    ["selected", "data_sharing_prepare.count_selected", "selected", Number(safeCounts.selected || 0)],
    ["exported", "data_sharing_prepare.count_exported", "packaged", Number(safeCounts.exported || 0)],
    ["skipped", "data_sharing_prepare.count_skipped", "skipped", Number(safeCounts.skipped || 0)],
    ["failed", "data_sharing_prepare.count_failed", "failed", Number(safeCounts.failed || 0)],
    ["truncated", "data_sharing_prepare.count_truncated", "truncated", Number(safeCounts.truncated || 0)]
  ];
  return rows.map(([key, textKey, fallback, count]) => `
    <div class="dataSharingPrepareModal__countRow" data-count-key="${escapeHtml(key)}">
      <dt>${escapeHtml(getStudioText(state.config, textKey, fallback))}</dt>
      <dd>${escapeHtml(countLabel(count, unit))}</dd>
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
    errorItems.length ? "data_sharing_prepare.issues_heading" : "data_sharing_prepare.warnings_heading",
    errorItems.length ? "Issues" : "Warnings"
  );
  return `
    <div class="dataSharingPrepareModal__issues">
      <h4>${escapeHtml(heading)}</h4>
      <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function showResultModal(state, payload, failed = false) {
  const files = outputFiles(payload);
  const fileText = files.join("\n");
  const fileLabel = getStudioText(state.config, "data_sharing_prepare.result_files_label", "files created");
  const emptyFiles = getStudioText(state.config, "data_sharing_prepare.result_files_empty", "No files created.");
  const formatLabel = getStudioText(state.config, "data_sharing_prepare.result_format_label", "format");
  const targetFormat = normalizeText(payload?.target_format).toUpperCase();
  const bodyHtml = `
    <dl class="dataSharingPrepareModal__details">
      <div class="dataSharingPrepareModal__countRow" data-detail-key="format">
        <dt>${escapeHtml(formatLabel)}</dt>
        <dd>${escapeHtml(targetFormat || "n/a")}</dd>
      </div>
    </dl>
    <dl class="dataSharingPrepareModal__counts">
      ${countRows(state, payload?.counts, payload)}
    </dl>
    <label class="dataSharingPrepareModal__files">
      <span>${escapeHtml(fileLabel)}</span>
      <textarea class="tagStudio__input dataSharingPrepareModal__fileList" readonly rows="${Math.max(1, files.length)}">${escapeHtml(fileText || emptyFiles)}</textarea>
    </label>
    ${issueList(state, payload?.warnings, payload?.errors)}
  `;
  const closeRole = "data-sharing-prepare-modal-close";
  state.modalHost.innerHTML = renderStudioModalFrame({
    hidden: false,
    modalRole: "data-sharing-prepare-result-modal",
    backdropRole: closeRole,
    titleId: "dataSharingPrepareResultModalTitle",
    title: failed
      ? getStudioText(state.config, "data_sharing_prepare.result_title_failed", "Package preparation failed")
      : getStudioText(state.config, "data_sharing_prepare.result_title", "Package result"),
    bodyHtml,
    actions: [
      { role: closeRole, label: getStudioText(state.config, "data_sharing_prepare.result_close", "Close") }
    ]
  });
  state.modalHost.querySelectorAll(`[data-role="${closeRole}"]`).forEach((node) => {
    node.addEventListener("click", () => {
      state.modalHost.innerHTML = "";
    });
  });
}

function setDocAndDescendantSelection(state, docId, selected) {
  const ids = [docId, ...descendantIds(state, docId)].filter((id) => rowMatchesCurrentFilters(state, id));
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
  const row = target.closest("[data-data-sharing-prepare-doc]");
  const docId = normalizeText(row ? row.getAttribute("data-data-sharing-prepare-doc") : "");
  if (!docId) return;
  setDocAndDescendantSelection(state, docId, target.checked);
  syncCheckboxStates(state);
  updateSelectionSummary(state);
}

async function runPreparePackage(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  if (!workflowDomainIsActive(state.workflowScopes, state.scope)) {
    updateStatus(state);
    return;
  }
  const config = selectedConfig(state);
  if (!config) {
    updateStatus(state);
    return;
  }
  const configId = normalizeText(config.id);
  const targetFormat = normalizeText(state.targetFormat);
  if (!supportedFormatsForConfig(config).includes(targetFormat)) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "data_sharing_prepare.format_required", "Select a supported package format.")
    );
    return;
  }
  const selection = config && typeof config.selection === "object" ? config.selection : {};
  const selectAll = usesDocumentSelection(state) && normalizeText(selection.mode) === "all_matching";
  const docIds = selectAll ? [] : Array.from(state.selectedIds);
  if (usesDocumentSelection(state) && !selectAll && !docIds.length) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "data_sharing_prepare.selection_required", "Select at least one document.")
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
    getStudioText(state.config, "data_sharing_prepare.status_running", "Running Data Sharing prepare...")
  );

  try {
    const payload = await postJson(DATA_SHARING_ENDPOINTS.prepare, {
      data_domain: state.scope,
      config_id: configId,
      target_format: targetFormat,
      doc_ids: docIds,
      select_all: selectAll,
      missing_summary_only: usesDocumentSelection(state) && !state.missingSummaryOnlyWrap.hidden
        ? Boolean(state.missingSummaryOnly.checked)
        : null,
      activity_context: buildStudioActivityContext({
        pageId: "data-sharing-prepare",
        actionId: "prepare-share-package",
        route: "/studio/data-sharing/prepare/",
        controlId: "dataSharingPrepareRun",
        controlSelector: "#dataSharingPrepareRun",
        recordIdField: "export_id",
        recordId: `${state.scope}:${configId}`
      })
    });
    showResultModal(state, payload);
    setStatus(
      state.statusNode,
      "success",
      payload.summary_text || getStudioText(state.config, "data_sharing_prepare.status_success", "Package prepared.")
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    showResultModal(state, payload, true);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message)
        || getStudioText(state.config, "data_sharing_prepare.status_failed", "Package preparation failed.")
    );
  } finally {
    state.isRunning = false;
    state.runButton.disabled = !state.serviceAvailable;
    markBusy(state, false);
  }
}

async function init() {
  const bootStatus = document.getElementById("dataSharingPrepareBootStatus");
  const root = document.getElementById("dataSharingPrepareRoot");
  if (!bootStatus || !root) return;
  initializeStudioRouteState(root, { route: "data-sharing-prepare", mode: "selection" });

  const state = {
    bootStatus,
    root,
    scope: workflowScopeFromUrl(),
    workflowScopes: WORKFLOW_SCOPES,
    scopeLabelNode: document.getElementById("dataSharingPrepareScopeLabel"),
    scopeSelect: document.getElementById("dataSharingPrepareScopeSelect"),
    configLabelNode: document.getElementById("dataSharingPrepareConfigLabel"),
    configSelect: document.getElementById("dataSharingPrepareConfigSelect"),
    missingSummaryOnlyWrap: document.getElementById("dataSharingPrepareMissingSummaryWrap"),
    missingSummaryOnly: document.getElementById("dataSharingPrepareMissingSummaryOnly"),
    missingSummaryLabelNode: document.getElementById("dataSharingPrepareMissingSummaryLabel"),
    formatLabelNode: document.getElementById("dataSharingPrepareFormatLabel"),
    formatOptionsNode: document.getElementById("dataSharingPrepareFormatOptions"),
    filterNode: document.getElementById("dataSharingPrepareListFilters"),
    selectAllButton: document.getElementById("dataSharingPrepareSelectAll"),
    clearButton: document.getElementById("dataSharingPrepareClear"),
    statusNode: document.getElementById("dataSharingPrepareStatus"),
    selectionSummary: document.getElementById("dataSharingPrepareSelectionSummary"),
    listNode: document.getElementById("dataSharingPrepareList"),
    runButton: document.getElementById("dataSharingPrepareRun"),
    modalHost: null,
    config: null,
    exportConfigs: [],
    docs: [],
    docsById: new Map(),
    childrenByParent: new Map(),
    depthById: new Map(),
    selectedIds: new Set(),
    listFilter: "all",
    targetFormat: "",
    docsIndexError: false,
    serviceAvailable: false,
    isRunning: false,
    prepareCapability: null
  };

  const requiredNodes = [
    state.scopeLabelNode,
    state.scopeSelect,
    state.configLabelNode,
    state.configSelect,
    state.missingSummaryOnlyWrap,
    state.missingSummaryOnly,
    state.missingSummaryLabelNode,
    state.formatLabelNode,
    state.formatOptionsNode,
    state.filterNode,
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
    state.config = await loadStudioConfigWithText("data_sharing_prepare");
    const adapterRegistry = await loadAdapterRegistry(state.config);
    state.workflowScopes = workflowDomainsForOperation(adapterRegistry, "prepare", WORKFLOW_SCOPES);
    state.scope = workflowScopeFromUrl(state.workflowScopes);
    state.prepareCapability = workflowCapabilityForOperation(adapterRegistry, "prepare", state.scope);
    renderScopeSelect(state);
    state.serviceAvailable = Boolean(await probeDataSharingHealth());
    if (workflowDomainIsActive(state.workflowScopes, state.scope)) {
      const capabilityProfiles = prepareProfilesForCapability(state.prepareCapability);
      const exportConfigPayload = capabilityProfiles.length
        ? { configs: capabilityProfiles }
        : await loadJson(
          getStudioDataPath(state.config, "library_export_configs")
            || "/assets/studio/data/library_export_configs.json"
        );
      state.exportConfigs = enabledConfigsForScope(exportConfigPayload, state.scope);
    }

    let docsIndexPayload = { docs: [] };
    if (usesDocumentSelection(state) && workflowDomainIsActive(state.workflowScopes, state.scope) && state.exportConfigs.length) {
      const docsIndexPath = getDocsScopeDataPath(state.config, state.scope, "index")
        || `/assets/data/docs/scopes/${encodeURIComponent(state.scope)}/index.json`;
      const docsIndexReadPath = state.serviceAvailable ? docsGeneratedIndexUrl(state.scope) : docsIndexPath;
      try {
        docsIndexPayload = await loadJson(docsIndexReadPath);
      } catch (error) {
        console.warn("data_sharing_prepare: docs index load failed", state.scope, error);
        state.docsIndexError = true;
      }
    }

    const docsTree = buildVisibleDocs(docsIndexPayload);
    state.docs = docsTree.docs;
    state.childrenByParent = docsTree.childrenByParent;
    state.depthById = docsTree.depthById;
    state.docsById = new Map(state.docs.map((doc) => [normalizeText(doc.doc_id), doc]));

    setText(state.scopeLabelNode, getStudioText(state.config, "data_sharing_prepare.scope_label", "scope"));
    setText(state.configLabelNode, getStudioText(state.config, "data_sharing_prepare.config_label", "sharing profile"));
    setText(
      state.missingSummaryLabelNode,
      getStudioText(state.config, "data_sharing_prepare.missing_summary_label", "missing summaries only")
    );
    setText(state.formatLabelNode, getStudioText(state.config, "data_sharing_prepare.format_label", "format"));
    setText(state.selectAllButton, getStudioText(state.config, "data_sharing_prepare.select_all", "Select all"));
    setText(state.clearButton, getStudioText(state.config, "data_sharing_prepare.clear", "Clear"));
    setText(state.runButton, getStudioText(state.config, "data_sharing_prepare.run_button", "Prepare package"));
    state.runButton.title = getStudioText(
      state.config,
      "data_sharing_prepare.run_disabled_title",
      "Requires the local docs-management service."
    );

    renderConfigSelect(state);
    syncConfigOptions(state);

    state.scopeSelect.addEventListener("change", () => updateScopeUrl(state.scopeSelect.value, state.workflowScopes));
    state.configSelect.addEventListener("change", () => syncConfigOptions(state));
    state.formatOptionsNode.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement) || target.name !== "dataSharingPrepareFormat") return;
      state.targetFormat = normalizeText(target.value);
      renderFormatOptions(state);
      updateStatus(state);
    });
    state.missingSummaryOnly.addEventListener("change", () => {
      applySelectionFilter(state);
      renderListFilters(state);
      renderDocList(state);
      updateStatus(state);
    });
    state.filterNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest
        ? event.target.closest("[data-data-sharing-prepare-filter]")
        : null;
      if (!button) return;
      const filter = normalizeText(button.getAttribute("data-data-sharing-prepare-filter"));
      if (!LIST_FILTERS.some((item) => item.key === filter)) return;
      state.listFilter = filter;
      renderListFilters(state);
      renderDocList(state);
      updateStatus(state);
    });
    state.selectAllButton.addEventListener("click", () => {
      selectableDocIds(state, { visibleOnly: true }).forEach((docId) => state.selectedIds.add(docId));
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
      runPreparePackage(state).catch((error) => console.warn("data_sharing_prepare: unexpected run failure", error));
    });

    root.hidden = false;
    bootStatus.hidden = true;
    markReady(state, true);
  } catch (error) {
    console.warn("data_sharing_prepare: load failed", error);
    root.hidden = false;
    bootStatus.hidden = true;
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "data_sharing_prepare.load_failed",
        "Failed to load {scope_label} package data.",
        { scope_label: state.config ? scopeTitle(state) : "Library" }
      )
    );
    markReady(state, true);
  } finally {
    markBusy(state, false);
  }
}

init();
