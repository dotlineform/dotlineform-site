import {
  getDocumentPackageConfig,
  getPackageDocuments,
  prepareDocumentPackage,
  saveDocumentPackageContext
} from "./document-package-client.js";
import {
  openDocumentPackageModal,
  showDocumentPackageResult
} from "./document-package-modal.js";
import {
  escapePackageHtml,
  packageScopeLabel,
  packageText,
  profileForId,
  renderPackageOptions,
  renderSelectablePackageDocuments,
  selectedScopeFromUrl,
  setPackageBusy,
  setPackageReady,
  setPackageStatus,
  syncPackageScopeLinks
} from "./document-package-view.js";

function prepareState(root) {
  return {
    root,
    status: document.getElementById("documentPackagePrepareStatus"),
    runButton: document.getElementById("documentPackagePrepareRun"),
    contextButton: document.getElementById("documentPackagePrepareContext"),
    scopeValue: document.getElementById("documentPackagePrepareScopeValue"),
    profileSelect: document.getElementById("documentPackagePrepareProfile"),
    formatSelect: document.getElementById("documentPackagePrepareFormat"),
    contentFormatField: document.getElementById("documentPackagePrepareContentFormatField"),
    contentFormatSelect: document.getElementById("documentPackagePrepareContentFormat"),
    descendantsField: document.getElementById("documentPackagePrepareDescendantsField"),
    descendantsInput: document.getElementById("documentPackagePrepareDescendants"),
    filterInput: document.getElementById("documentPackagePrepareFilter"),
    selectAllButton: document.getElementById("documentPackagePrepareSelectAll"),
    clearButton: document.getElementById("documentPackagePrepareClear"),
    selectionSummary: document.getElementById("documentPackagePrepareSelectionSummary"),
    documentsNode: document.getElementById("documentPackagePrepareDocuments"),
    modalHost: document.getElementById("documentPackagePrepareModalHost"),
    profiles: [],
    scopes: [],
    scope: "",
    documents: [],
    selectedIds: new Set(),
    workspaceAvailable: false,
    busy: false,
    requestVersion: 0
  };
}

function selectedProfile(state) {
  return profileForId(state.profiles, state.profileSelect.value);
}

function selectableDocumentIds(state) {
  return state.documents
    .filter((record) => record && record.selectable !== false)
    .map((record) => packageText(record.doc_id || record.id))
    .filter(Boolean);
}

function visibleSelectableDocumentIds(state) {
  const filter = packageText(state.filterInput.value).toLowerCase();
  return state.documents
    .filter((record) => record && record.selectable !== false)
    .filter((record) => {
      const haystack = `${packageText(record.title)} ${packageText(record.doc_id || record.id)}`.toLowerCase();
      return !filter || haystack.includes(filter);
    })
    .map((record) => packageText(record.doc_id || record.id))
    .filter(Boolean);
}

function descendantIds(state, docId) {
  const childrenByParent = new Map();
  state.documents.forEach((record) => {
    const parentId = packageText(record && record.parent_id);
    const childId = packageText(record && (record.doc_id || record.id));
    if (!parentId || !childId) return;
    if (!childrenByParent.has(parentId)) childrenByParent.set(parentId, []);
    childrenByParent.get(parentId).push(childId);
  });
  const descendants = [];
  const pending = [...(childrenByParent.get(docId) || [])];
  const seen = new Set();
  while (pending.length) {
    const childId = pending.shift();
    if (!childId || seen.has(childId)) continue;
    seen.add(childId);
    descendants.push(childId);
    pending.push(...(childrenByParent.get(childId) || []));
  }
  return descendants;
}

function updateSelectionSummary(state) {
  const count = state.selectedIds.size;
  state.selectionSummary.textContent = count === 1 ? "1 document selected." : `${count} documents selected.`;
}

function syncPrepareControls(state) {
  const profile = selectedProfile(state);
  const hasDocuments = state.documents.length > 0;
  const canRun = Boolean(
    !state.busy
    && state.workspaceAvailable
    && packageText(state.scope)
    && profile
    && state.selectedIds.size
  );
  state.runButton.disabled = !canRun;
  state.contextButton.disabled = state.busy || !state.workspaceAvailable || !state.scope || !profile;
  state.profileSelect.disabled = state.busy || !state.scope || !state.profiles.length;
  state.formatSelect.disabled = state.busy || !state.scope || !profile;
  state.contentFormatSelect.disabled = state.busy || !state.scope || !profile;
  state.filterInput.disabled = state.busy || !hasDocuments;
  state.selectAllButton.disabled = state.busy || !visibleSelectableDocumentIds(state).length;
  state.clearButton.disabled = state.busy || !state.selectedIds.size;
  updateSelectionSummary(state);
}

function renderDocuments(state) {
  const allowedIds = new Set(selectableDocumentIds(state));
  state.selectedIds.forEach((docId) => {
    if (!allowedIds.has(docId)) state.selectedIds.delete(docId);
  });
  renderSelectablePackageDocuments(state.documentsNode, state.documents, {
    filter: state.filterInput.value,
    selectedIds: state.selectedIds,
    onToggle(docId, selected) {
      const affected = [docId];
      if (state.descendantsInput.checked) affected.push(...descendantIds(state, docId));
      affected.forEach((affectedId) => {
        if (!allowedIds.has(affectedId)) return;
        if (selected) state.selectedIds.add(affectedId);
        else state.selectedIds.delete(affectedId);
      });
      renderDocuments(state);
    }
  });
  syncPrepareControls(state);
}

function supportedFormats(profile) {
  const formats = Array.isArray(profile && profile.supported_target_formats)
    ? profile.supported_target_formats.map(packageText).filter(Boolean)
    : [];
  const fallback = packageText(profile && profile.target_format);
  return formats.length ? formats : [fallback].filter(Boolean);
}

function supportedContentFormats(profile) {
  const formats = Array.isArray(profile && profile.supported_content_formats)
    ? profile.supported_content_formats.map(packageText).filter(Boolean)
    : [];
  const fallback = packageText(profile && profile.content_format);
  return formats.length ? formats : [fallback].filter(Boolean);
}

function renderProfileOptions(state) {
  const profile = selectedProfile(state) || state.profiles[0] || null;
  if (profile && state.profileSelect.value !== profile.profile_id) {
    state.profileSelect.value = profile.profile_id;
  }
  const formats = supportedFormats(profile).map((id) => ({ id, label: id.toUpperCase() }));
  renderPackageOptions(state.formatSelect, formats, {
    selectedValue: packageText(profile && profile.target_format) || packageText(formats[0] && formats[0].id)
  });
  const contentFormats = supportedContentFormats(profile).map((id) => ({
    id,
    label: id === "plain_text" ? "Plain text" : id.charAt(0).toUpperCase() + id.slice(1)
  }));
  renderPackageOptions(state.contentFormatSelect, contentFormats, {
    selectedValue: packageText(profile && profile.content_format) || packageText(contentFormats[0] && contentFormats[0].id)
  });
  state.contentFormatField.hidden = !contentFormats.length;

  const selection = profile && typeof profile.selection === "object" ? profile.selection : {};
  const treeProfile = packageText(profile && profile.record_shape) === "document_tree";
  state.descendantsField.hidden = !profile;
  state.descendantsInput.disabled = !state.scope || treeProfile;
  state.descendantsInput.checked = treeProfile || selection.include_descendants !== false;
  syncPrepareControls(state);
}

async function loadDocuments(state) {
  const scope = packageText(state.scope);
  const version = ++state.requestVersion;
  state.selectedIds.clear();
  state.documents = [];
  if (!scope) {
    state.documentsNode.innerHTML = '<p class="docsPackageEmpty">Open this route from Docs Viewer Actions for a scope.</p>';
    setPackageStatus(state.status, "error", "A valid Docs Viewer scope is required.");
    syncPrepareControls(state);
    return;
  }
  state.busy = true;
  setPackageBusy(state.root, true);
  setPackageStatus(state.status, "", "Loading source documents…");
  syncPrepareControls(state);
  try {
    const payload = await getPackageDocuments(scope);
    if (version !== state.requestVersion) return;
    state.documents = Array.isArray(payload.records) ? payload.records : [];
    renderDocuments(state);
    setPackageStatus(
      state.status,
      "success",
      state.documents.length === 1 ? "Loaded 1 document." : `Loaded ${state.documents.length} documents.`
    );
  } catch (error) {
    if (version !== state.requestVersion) return;
    state.documentsNode.innerHTML = '<p class="docsPackageEmpty">Documents could not be loaded.</p>';
    setPackageStatus(state.status, "error", error.message || "Documents could not be loaded.");
  } finally {
    if (version === state.requestVersion) {
      state.busy = false;
      setPackageBusy(state.root, false);
      syncPrepareControls(state);
    }
  }
}

function contextBody(profile) {
  const context = profile && typeof profile.external_context === "object" ? profile.external_context : {};
  const descriptions = context && typeof context.field_descriptions === "object" ? context.field_descriptions : {};
  const fields = Array.isArray(profile && profile.document_fields) ? profile.document_fields : [];
  return `
    <label class="docsPackageModal__field" for="documentPackageContextTask">
      <span>task</span>
      <input id="documentPackageContextTask" data-package-context-task value="${escapePackageHtml(context.task || "")}">
    </label>
    <label class="docsPackageModal__field" for="documentPackageContextGuidance">
      <span>response guidance</span>
      <textarea id="documentPackageContextGuidance" data-package-context-guidance rows="3">${escapePackageHtml(context.response_guidance || "")}</textarea>
    </label>
    ${fields.map((field, index) => {
      const outputPath = packageText(field && field.output_path);
      return `
        <label class="docsPackageModal__field" for="documentPackageContextField-${index + 1}">
          <span>${escapePackageHtml(outputPath)}</span>
          <textarea id="documentPackageContextField-${index + 1}" data-package-context-field data-output-path="${escapePackageHtml(outputPath)}" rows="2">${escapePackageHtml(descriptions[outputPath] || "")}</textarea>
        </label>
      `;
    }).join("")}
  `;
}

function contextPayload(modal) {
  const fieldDescriptions = {};
  modal.querySelectorAll("[data-package-context-field]").forEach((node) => {
    const outputPath = packageText(node.dataset.outputPath);
    if (outputPath) fieldDescriptions[outputPath] = packageText(node.value);
  });
  return {
    task: packageText(modal.querySelector("[data-package-context-task]")?.value),
    response_guidance: packageText(modal.querySelector("[data-package-context-guidance]")?.value),
    field_descriptions: fieldDescriptions
  };
}

async function editContext(state) {
  const profile = selectedProfile(state);
  if (!profile) return;
  await openDocumentPackageModal({
    host: state.modalHost,
    restoreFocus: state.contextButton,
    title: "Edit package context",
    meta: profile.label || profile.profile_id,
    bodyHtml: contextBody(profile),
    primaryLabel: "Save context",
    cancelLabel: "Cancel",
    wide: true,
    focusSelector: "[data-package-context-task]",
    runningMessage: "Saving context…",
    async onSubmit({ host, status }) {
      const externalContext = contextPayload(host);
      const values = [
        externalContext.task,
        externalContext.response_guidance,
        ...Object.values(externalContext.field_descriptions)
      ];
      if (values.some((value) => !packageText(value))) {
        status.dataset.state = "error";
        status.textContent = "Complete every context field.";
        const blank = Array.from(host.querySelectorAll("input, textarea")).find((node) => !packageText(node.value));
        if (blank) blank.focus();
        return false;
      }
      const payload = await saveDocumentPackageContext({
        profile_id: profile.profile_id,
        external_context: externalContext,
        dry_run: false
      });
      profile.external_context = payload.external_context || externalContext;
      setPackageStatus(state.status, "success", payload.summary_text || "Saved package context.");
      return { confirmed: true, payload };
    }
  });
}

async function runPrepare(state) {
  const profile = selectedProfile(state);
  const scope = packageText(state.scope);
  if (!profile || !scope || !state.selectedIds.size || state.busy) return;
  state.busy = true;
  setPackageBusy(state.root, true);
  setPackageStatus(state.status, "", "Preparing document package…");
  syncPrepareControls(state);
  try {
    const payload = await prepareDocumentPackage({
      scope,
      profile_id: profile.profile_id,
      doc_ids: Array.from(state.selectedIds),
      select_all: false,
      target_format: packageText(state.formatSelect.value),
      content_format: packageText(state.contentFormatSelect.value),
      dry_run: false,
      activity_context: {
        page_id: "docs-package-prepare",
        action_id: "prepare-document-package",
        route: `/docs/packages/prepare/?scope=${encodeURIComponent(scope)}`,
        control_id: "documentPackagePrepareRun",
        control_selector: "#documentPackagePrepareRun",
        correlation_id: `document-package-prepare:${Date.now()}`
      }
    });
    setPackageStatus(state.status, "success", payload.summary_text || "Document package prepared.");
    await showDocumentPackageResult({
      host: state.modalHost,
      restoreFocus: state.runButton,
      title: "Document package prepared",
      meta: profile.label || profile.profile_id,
      payload
    });
  } catch (error) {
    const payload = error && error.payload ? error.payload : { ok: false, summary_text: error.message };
    setPackageStatus(state.status, "error", error.message || "Document package preparation failed.");
    await showDocumentPackageResult({
      host: state.modalHost,
      restoreFocus: state.runButton,
      title: "Document package was not prepared",
      meta: profile.label || profile.profile_id,
      payload
    });
  } finally {
    state.busy = false;
    setPackageBusy(state.root, false);
    syncPrepareControls(state);
  }
}

function bindPrepareEvents(state) {
  state.profileSelect.addEventListener("change", () => renderProfileOptions(state));
  state.filterInput.addEventListener("input", () => renderDocuments(state));
  state.descendantsInput.addEventListener("change", () => renderDocuments(state));
  state.selectAllButton.addEventListener("click", () => {
    visibleSelectableDocumentIds(state).forEach((docId) => state.selectedIds.add(docId));
    renderDocuments(state);
  });
  state.clearButton.addEventListener("click", () => {
    state.selectedIds.clear();
    renderDocuments(state);
  });
  state.contextButton.addEventListener("click", () => editContext(state));
  state.runButton.addEventListener("click", () => runPrepare(state));
}

async function initDocumentPackagePrepare() {
  const root = document.getElementById("documentPackagePrepareRoot");
  if (!root) return;
  const state = prepareState(root);
  bindPrepareEvents(state);
  try {
    const payload = await getDocumentPackageConfig();
    state.profiles = Array.isArray(payload.profiles) ? payload.profiles : [];
    state.scopes = Array.isArray(payload.scopes) ? payload.scopes : [];
    state.scope = selectedScopeFromUrl(state.scopes);
    state.workspaceAvailable = payload.workspace && payload.workspace.available === true;
    state.scopeValue.textContent = state.scope ? packageScopeLabel(state.scopes, state.scope) : "Scope required";
    if (state.scope) delete state.scopeValue.dataset.state;
    else state.scopeValue.dataset.state = "error";
    syncPackageScopeLinks(state.scope);
    renderPackageOptions(state.profileSelect, state.profiles, {
      valueKey: "profile_id",
      labelKey: "label",
      selectedValue: packageText(state.profiles[0] && state.profiles[0].profile_id)
    });
    renderProfileOptions(state);
    if (!state.scope) {
      state.documentsNode.innerHTML = '<p class="docsPackageEmpty">Open this route from Docs Viewer Actions for a scope.</p>';
      setPackageStatus(state.status, "error", "A valid Docs Viewer scope is required.");
    } else if (!state.workspaceAvailable) {
      setPackageStatus(state.status, "warn", packageText(payload.workspace && payload.workspace.message) || "The document-package workspace is unavailable.");
    } else {
      await loadDocuments(state);
    }
  } catch (error) {
    setPackageStatus(state.status, "error", error.message || "Document-package configuration could not be loaded.");
  } finally {
    setPackageReady(root, true);
    syncPrepareControls(state);
  }
}

initDocumentPackagePrepare();
