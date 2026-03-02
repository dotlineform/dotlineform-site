const GROUPS = ["subject", "domain", "form", "theme"];
const HEALTH_ENDPOINT = "http://127.0.0.1:8787/health";
const IMPORT_ENDPOINT = "http://127.0.0.1:8787/import-tag-registry";
const MUTATE_ENDPOINT = "http://127.0.0.1:8787/mutate-tag";
const MUTATE_PREVIEW_ENDPOINT = "http://127.0.0.1:8787/mutate-tag-preview";
const SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagRegistryPage);
} else {
  initTagRegistryPage();
}

async function initTagRegistryPage() {
  const mount = document.getElementById("tag-registry");
  if (!mount) return;

  const state = {
    mount,
    tags: [],
    filterGroup: "all",
    searchQuery: "",
    sortKey: "label",
    sortDir: "asc",
    importMode: "add",
    saveMode: "patch",
    selectedFile: null,
    patchSnippet: "",
    editTagId: "",
    editPreviewSave: "",
    editPreviewDelete: "",
    editPreviewSaveSeq: 0,
    editPreviewDeleteSeq: 0,
    editPreviewTimer: null,
    refs: null,
    registryUpdatedAt: ""
  };

  renderShell(state);
  wireEvents(state);
  syncImportModeFromControl(state);

  try {
    await loadRegistry(state);
    renderControls(state);
    renderList(state);
  } catch (error) {
    renderError(state, "Failed to load tag registry from /assets/data/tag_registry.json.");
    return;
  }

  void probeImportMode(state);
}

function renderShell(state) {
  state.mount.innerHTML = `
    <section class="tagStudio__panel">
      <div class="tagRegistry__importBox">
        <div class="tagRegistry__importRow">
          <label class="tagRegistry__fileWrap">
            <span class="tagRegistry__importLabel">import file</span>
            <button type="button" class="tagStudio__button tagStudio__button--primary tagRegistry__chooseBtn" data-role="choose-file">Choose file</button>
            <input type="file" class="tagRegistry__fileInput" data-role="import-file" accept=".json,application/json" hidden>
          </label>
          <label class="tagRegistry__modeWrap">
            <span class="tagRegistry__importLabel">mode</span>
            <select class="tagRegistry__modeSelect" data-role="import-mode">
              <option value="add">add (no overwrite)</option>
              <option value="merge">add + overwrite</option>
              <option value="replace">replace entire registry</option>
            </select>
          </label>
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="import-btn">Import</button>
          <span class="tagRegistry__saveMode" data-role="save-mode">Import mode: Patch</span>
        </div>
        <p class="tagRegistry__selected" data-role="selected-file"></p>
        <p class="tagRegistry__result" data-role="import-result"></p>
      </div>

      <div class="tagRegistry__controls">
        <div class="tagStudio__key tagRegistry__key" data-role="key"></div>
        <label class="tagRegistry__searchWrap">
          <span class="visually-hidden">Search tags</span>
          <input
            type="text"
            class="tagStudio__input tagRegistry__searchInput"
            data-role="search"
            placeholder="search"
            autocomplete="off"
          >
        </label>
      </div>
      <div data-role="list"></div>
    </section>

    <div class="tagStudioModal" data-role="patch-modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryPatchTitle">
        <h3 id="tagRegistryPatchTitle">Registry Patch Preview</h3>
        <p class="tagStudioModal__label">Manual patch snippet (new tags only)</p>
        <pre class="tagStudioModal__pre" data-role="patch-snippet"></pre>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="copy-patch">Copy</button>
          <button type="button" class="tagStudio__button" data-role="close-modal">Close</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="edit-modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-edit-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryEditTitle">
        <h3 id="tagRegistryEditTitle">Edit Tag</h3>
        <p class="tagRegistryEdit__meta" data-role="edit-tag-id"></p>
        <div class="tagRegistryEdit__fields">
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">Label</span>
            <input type="text" class="tagStudio__input" data-role="edit-label" autocomplete="off">
          </label>
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">Slug</span>
            <input type="text" class="tagStudio__input" data-role="edit-slug" autocomplete="off">
          </label>
        </div>
        <p class="tagRegistryEdit__impact" data-role="edit-impact-save"></p>
        <p class="tagRegistryEdit__impact" data-role="edit-impact-delete"></p>
        <p class="tagRegistryEdit__status" data-role="edit-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="save-edit">Save</button>
          <button type="button" class="tagStudio__button" data-role="delete-tag">Delete</button>
          <button type="button" class="tagStudio__button" data-role="close-edit-modal">Close</button>
        </div>
      </div>
    </div>
  `;

  state.refs = {
    key: state.mount.querySelector('[data-role="key"]'),
    search: state.mount.querySelector('[data-role="search"]'),
    chooseFile: state.mount.querySelector('[data-role="choose-file"]'),
    importFile: state.mount.querySelector('[data-role="import-file"]'),
    importMode: state.mount.querySelector('[data-role="import-mode"]'),
    importButton: state.mount.querySelector('[data-role="import-btn"]'),
    saveMode: state.mount.querySelector('[data-role="save-mode"]'),
    selectedFile: state.mount.querySelector('[data-role="selected-file"]'),
    importResult: state.mount.querySelector('[data-role="import-result"]'),
    list: state.mount.querySelector('[data-role="list"]'),
    patchModal: state.mount.querySelector('[data-role="patch-modal"]'),
    patchSnippet: state.mount.querySelector('[data-role="patch-snippet"]'),
    copyPatch: state.mount.querySelector('[data-role="copy-patch"]'),
    editModal: state.mount.querySelector('[data-role="edit-modal"]'),
    editTagId: state.mount.querySelector('[data-role="edit-tag-id"]'),
    editLabel: state.mount.querySelector('[data-role="edit-label"]'),
    editSlug: state.mount.querySelector('[data-role="edit-slug"]'),
    editImpactSave: state.mount.querySelector('[data-role="edit-impact-save"]'),
    editImpactDelete: state.mount.querySelector('[data-role="edit-impact-delete"]'),
    editStatus: state.mount.querySelector('[data-role="edit-status"]'),
    saveEdit: state.mount.querySelector('[data-role="save-edit"]'),
    deleteTag: state.mount.querySelector('[data-role="delete-tag"]')
  };
}

function wireEvents(state) {
  state.refs.search.addEventListener("input", () => {
    state.searchQuery = normalize(state.refs.search.value);
    renderList(state);
  });

  state.refs.chooseFile.addEventListener("click", () => {
    state.refs.importFile.click();
  });

  state.refs.importFile.addEventListener("change", () => {
    const files = state.refs.importFile.files;
    state.selectedFile = files && files.length ? files[0] : null;
    if (state.selectedFile) {
      state.refs.selectedFile.textContent = `Selected: ${state.selectedFile.name}`;
    } else {
      state.refs.selectedFile.textContent = "";
    }
  });

  state.refs.importMode.addEventListener("change", () => {
    syncImportModeFromControl(state);
  });

  state.refs.importButton.addEventListener("click", () => {
    void handleImport(state);
  });

  state.mount.addEventListener("click", (event) => {
    const groupButton = event.target.closest("button[data-group]");
    if (groupButton) {
      const group = normalize(groupButton.getAttribute("data-group"));
      state.filterGroup = group && group !== "all" ? group : "all";
      renderControls(state);
      renderList(state);
      return;
    }

    const tagButton = event.target.closest("button[data-tag-id]");
    if (tagButton) {
      const tagId = normalize(tagButton.getAttribute("data-tag-id"));
      if (tagId) openEditModal(state, tagId);
      return;
    }

    const sortButton = event.target.closest("button[data-sort-key]");
    if (!sortButton) return;
    const nextSortKey = normalize(sortButton.getAttribute("data-sort-key"));
    if (!nextSortKey) return;
    if (state.sortKey === nextSortKey) {
      state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = nextSortKey;
      state.sortDir = "asc";
    }
    renderList(state);
  });

  state.refs.patchModal.addEventListener("click", (event) => {
    if (!event.target.closest('[data-role="close-modal"]')) return;
    closePatchModal(state);
  });

  state.refs.copyPatch.addEventListener("click", async () => {
    if (!state.patchSnippet) return;
    try {
      await navigator.clipboard.writeText(state.patchSnippet);
      setImportResult(state, "success", "Patch snippet copied to clipboard.");
    } catch (error) {
      setImportResult(state, "error", "Copy failed. Select and copy the snippet manually.");
    }
  });

  state.refs.editModal.addEventListener("click", (event) => {
    if (!event.target.closest('[data-role="close-edit-modal"]')) return;
    closeEditModal(state);
  });

  state.refs.saveEdit.addEventListener("click", () => {
    void handleTagEdit(state);
  });

  state.refs.deleteTag.addEventListener("click", () => {
    void handleTagDelete(state);
  });

  state.refs.editLabel.addEventListener("input", () => {
    scheduleSaveImpactPreview(state);
  });
  state.refs.editSlug.addEventListener("input", () => {
    scheduleSaveImpactPreview(state);
  });
}

function syncImportModeFromControl(state) {
  const mode = normalize(state.refs.importMode.value);
  if (mode === "replace") {
    state.importMode = "replace";
  } else if (mode === "merge") {
    state.importMode = "merge";
  } else {
    state.importMode = "add";
  }
}

async function probeImportMode(state) {
  const ok = await pingHealthEndpoint();
  state.saveMode = ok ? "post" : "patch";
  renderImportMode(state);
}

async function pingHealthEndpoint() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 500);
  try {
    const response = await fetch(HEALTH_ENDPOINT, { signal: controller.signal, cache: "no-store" });
    if (!response.ok) return false;
    const payload = await response.json();
    return Boolean(payload && payload.ok);
  } catch (error) {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

function renderImportMode(state) {
  const label = state.saveMode === "post" ? "Local server" : "Patch";
  state.refs.saveMode.textContent = `Import mode: ${label}`;
}

async function loadRegistry(state) {
  const data = await fetchJson("/assets/data/tag_registry.json");
  state.registryUpdatedAt = normalizeTimestamp(data && data.updated_at_utc);
  state.tags = normalizeRegistryTags(data, state.registryUpdatedAt);
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function normalizeRegistryTags(data, fallbackUpdatedAt) {
  const rawTags = Array.isArray(data && data.tags) ? data.tags : [];
  const tags = [];

  for (const raw of rawTags) {
    if (!raw || typeof raw !== "object") continue;
    const group = normalize(raw.group);
    const tagId = normalize(raw.tag_id);
    const label = String(raw.label || "").trim();
    const description = String(raw.description || "").trim();
    const status = normalize(raw.status || "active");
    const updatedAtUtc = normalizeTimestamp(raw.updated_at_utc) || fallbackUpdatedAt;

    if (!GROUPS.includes(group) || !tagId || !label) continue;
    tags.push({
      group,
      tagId,
      label,
      description,
      status,
      updatedAtUtc,
      updatedAtMs: toTimestampMs(updatedAtUtc)
    });
  }

  return tags;
}

function renderControls(state) {
  const groupCounts = countTagsByGroup(state.tags);
  const totalCount = state.tags.length;
  const allActiveClass = state.filterGroup === "all" ? " is-active" : "";
  const groupButtons = GROUPS.map((group) => {
    const activeClass = state.filterGroup === group ? " is-active" : "";
    const count = Number(groupCounts[group] || 0);
    return `
      <button
        type="button"
        class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)} tagRegistry__groupBtn${activeClass}"
        data-group="${escapeHtml(group)}"
      >
        ${escapeHtml(group)} [${count}]
      </button>
    `;
  }).join("");

  state.refs.key.innerHTML = `
    <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">All tags [${totalCount}]</button>
    ${groupButtons}
  `;
}

function countTagsByGroup(tags) {
  const counts = { subject: 0, domain: 0, form: 0, theme: 0 };
  for (const tag of tags || []) {
    const group = normalize(tag && tag.group);
    if (GROUPS.includes(group)) {
      counts[group] += 1;
    }
  }
  return counts;
}

function renderList(state) {
  const visible = getVisibleSortedTags(state);
  const headerHtml = `
    <div class="tagRegistry__head">
      <button type="button" class="tagRegistry__sortBtn${sortBtnClass(state, "updatedat")}" data-sort-key="updatedat">
        timestamp${sortIndicator(state, "updatedat")}
      </button>
      <button type="button" class="tagRegistry__sortBtn${sortBtnClass(state, "label")}" data-sort-key="label">
        tag${sortIndicator(state, "label")}
      </button>
      <button type="button" class="tagRegistry__sortBtn${sortBtnClass(state, "description")}" data-sort-key="description">
        description${sortIndicator(state, "description")}
      </button>
    </div>
  `;

  if (!visible.length) {
    state.refs.list.innerHTML = `${headerHtml}<p class="tagStudio__empty">none</p>`;
    return;
  }

  state.refs.list.innerHTML = `
    ${headerHtml}
    <ul class="tagRegistry__rows">
      ${visible.map((tag) => `
        <li class="tagRegistry__row">
          <div class="tagRegistry__tsCol">${escapeHtml(formatTimestamp(tag.updatedAtUtc))}</div>
          <div class="tagRegistry__tagCol">
            <button type="button" class="tagStudio__chip tagStudio__chip--${escapeHtml(tag.group)} tagRegistry__tagBtn" data-tag-id="${escapeHtml(tag.tagId)}" title="${escapeHtml(tag.tagId)}">
              ${escapeHtml(tag.label)}
            </button>
          </div>
          <div class="tagRegistry__descCol">
            ${escapeHtml(tag.description || "—")}
          </div>
        </li>
      `).join("")}
    </ul>
  `;
}

function getVisibleSortedTags(state) {
  const filtered = state.tags.filter((tag) => {
    const groupMatch = state.filterGroup === "all" ? true : tag.group === state.filterGroup;
    if (!groupMatch) return false;
    if (!state.searchQuery) return true;
    return normalize(tag.label).startsWith(state.searchQuery);
  });

  const direction = state.sortDir === "desc" ? -1 : 1;
  filtered.sort((a, b) => direction * compareTags(a, b, state.sortKey));
  return filtered;
}

function compareTags(a, b, sortKey) {
  if (sortKey === "updatedat") {
    if (a.updatedAtMs === null && b.updatedAtMs === null) return compareTags(a, b, "label");
    if (a.updatedAtMs === null) return 1;
    if (b.updatedAtMs === null) return -1;
    if (a.updatedAtMs !== b.updatedAtMs) return a.updatedAtMs - b.updatedAtMs;
    return compareTags(a, b, "label");
  }

  if (sortKey === "description") {
    const ad = normalize(a.description);
    const bd = normalize(b.description);
    const byDescription = ad.localeCompare(bd, undefined, { sensitivity: "base" });
    if (byDescription !== 0) return byDescription;
    return compareTags(a, b, "label");
  }

  const byLabel = a.label.localeCompare(b.label, undefined, { sensitivity: "base" });
  if (byLabel !== 0) return byLabel;
  return a.tagId.localeCompare(b.tagId);
}

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "asc" ? " ↑" : " ↓";
}

function sortBtnClass(state, key) {
  return state.sortKey === key ? " is-active" : "";
}

function findTagById(state, tagId) {
  return state.tags.find((tag) => tag.tagId === normalize(tagId)) || null;
}

function openEditModal(state, tagId) {
  const tag = findTagById(state, tagId);
  if (!tag) return;
  const [, slug = ""] = String(tag.tagId || "").split(":", 2);
  state.editTagId = tag.tagId;
  state.editPreviewSave = "";
  state.editPreviewDelete = "";
  state.editPreviewSaveSeq += 1;
  state.editPreviewDeleteSeq += 1;
  if (state.editPreviewTimer) {
    clearTimeout(state.editPreviewTimer);
    state.editPreviewTimer = null;
  }
  state.refs.editTagId.textContent = `tag: ${tag.tagId} (${tag.group})`;
  state.refs.editLabel.value = tag.label;
  state.refs.editSlug.value = slug;
  state.refs.editImpactSave.textContent = "";
  state.refs.editImpactDelete.textContent = "";
  state.refs.editImpactSave.className = "tagRegistryEdit__impact";
  state.refs.editImpactDelete.className = "tagRegistryEdit__impact";
  state.refs.editStatus.className = "tagRegistryEdit__status";
  state.refs.editStatus.textContent = state.saveMode === "post"
    ? ""
    : "Local server is required for edit/delete.";
  state.refs.editModal.hidden = false;
  if (state.saveMode === "post") {
    void refreshSaveImpactPreview(state);
    void refreshDeleteImpactPreview(state);
  } else {
    state.refs.editImpactSave.textContent = "Save impact: unavailable (local server required).";
    state.refs.editImpactDelete.textContent = "Delete impact: unavailable (local server required).";
  }
}

function closeEditModal(state) {
  state.refs.editModal.hidden = true;
  state.editTagId = "";
  state.editPreviewSave = "";
  state.editPreviewDelete = "";
  state.editPreviewSaveSeq += 1;
  state.editPreviewDeleteSeq += 1;
  if (state.editPreviewTimer) {
    clearTimeout(state.editPreviewTimer);
    state.editPreviewTimer = null;
  }
}

function setEditStatus(state, kind, message) {
  state.refs.editStatus.textContent = message || "";
  state.refs.editStatus.className = "tagRegistryEdit__status";
  if (kind) state.refs.editStatus.classList.add(`is-${kind}`);
}

function setImpactPreview(target, kind, message) {
  target.textContent = message || "";
  target.className = "tagRegistryEdit__impact";
  if (kind) target.classList.add(`is-${kind}`);
}

function buildEditPreviewPayload(state) {
  if (!state.editTagId) return null;
  const tag = findTagById(state, state.editTagId);
  if (!tag) return null;
  const nextLabel = String(state.refs.editLabel.value || "").trim();
  const nextSlug = normalize(state.refs.editSlug.value);
  if (!nextLabel) return { error: "label required" };
  if (!SLUG_RE.test(nextSlug)) return { error: "slug invalid" };
  const nextTagId = `${tag.group}:${nextSlug}`;
  return {
    action: "edit",
    tag_id: tag.tagId,
    new_label: nextLabel,
    new_slug: nextSlug,
    allow_canonical_rename: nextTagId !== tag.tagId,
    client_time_utc: utcTimestamp()
  };
}

function buildDeletePreviewPayload(state) {
  if (!state.editTagId) return null;
  return {
    action: "delete",
    tag_id: state.editTagId,
    client_time_utc: utcTimestamp()
  };
}

function scheduleSaveImpactPreview(state) {
  if (state.editPreviewTimer) clearTimeout(state.editPreviewTimer);
  state.editPreviewTimer = setTimeout(() => {
    state.editPreviewTimer = null;
    void refreshSaveImpactPreview(state);
  }, 180);
}

async function refreshSaveImpactPreview(state) {
  if (state.saveMode !== "post") {
    setImpactPreview(state.refs.editImpactSave, "error", "Save impact: unavailable (local server required).");
    return;
  }
  const payload = buildEditPreviewPayload(state);
  if (!payload) {
    setImpactPreview(state.refs.editImpactSave, "error", "Save impact: unavailable.");
    return;
  }
  if (payload.error) {
    setImpactPreview(state.refs.editImpactSave, "error", "Save impact: enter valid label and slug.");
    return;
  }
  const seq = ++state.editPreviewSaveSeq;
  try {
    const response = await postJson(MUTATE_PREVIEW_ENDPOINT, payload);
    if (seq !== state.editPreviewSaveSeq || state.refs.editModal.hidden) return;
    state.editPreviewSave = buildMutationSummary(response);
    setImpactPreview(state.refs.editImpactSave, "", `Save impact: ${state.editPreviewSave}`);
  } catch (error) {
    if (seq !== state.editPreviewSaveSeq || state.refs.editModal.hidden) return;
    setImpactPreview(state.refs.editImpactSave, "error", "Save impact: preview failed.");
  }
}

async function refreshDeleteImpactPreview(state) {
  if (state.saveMode !== "post") {
    setImpactPreview(state.refs.editImpactDelete, "error", "Delete impact: unavailable (local server required).");
    return;
  }
  const payload = buildDeletePreviewPayload(state);
  if (!payload) {
    setImpactPreview(state.refs.editImpactDelete, "error", "Delete impact: unavailable.");
    return;
  }
  const seq = ++state.editPreviewDeleteSeq;
  try {
    const response = await postJson(MUTATE_PREVIEW_ENDPOINT, payload);
    if (seq !== state.editPreviewDeleteSeq || state.refs.editModal.hidden) return;
    state.editPreviewDelete = buildMutationSummary(response);
    setImpactPreview(state.refs.editImpactDelete, "", `Delete impact: ${state.editPreviewDelete}`);
  } catch (error) {
    if (seq !== state.editPreviewDeleteSeq || state.refs.editModal.hidden) return;
    setImpactPreview(state.refs.editImpactDelete, "error", "Delete impact: preview failed.");
  }
}

async function handleTagEdit(state) {
  if (!state.editTagId) return;
  if (state.saveMode !== "post") {
    setEditStatus(state, "error", "Local server is required for edit/delete.");
    return;
  }

  const tag = findTagById(state, state.editTagId);
  if (!tag) {
    setEditStatus(state, "error", "Selected tag is no longer available.");
    return;
  }

  const nextLabel = String(state.refs.editLabel.value || "").trim();
  const nextSlug = normalize(state.refs.editSlug.value);
  if (!nextLabel) {
    setEditStatus(state, "error", "Label is required.");
    return;
  }
  if (!SLUG_RE.test(nextSlug)) {
    setEditStatus(state, "error", "Slug must be lowercase letters/numbers/hyphens.");
    return;
  }

  const nextTagId = `${tag.group}:${nextSlug}`;
  const canonicalChanged = nextTagId !== tag.tagId;
  if (canonicalChanged) {
    const impact = state.editPreviewSave ? `\n\nImpact:\n${state.editPreviewSave}` : "";
    const ok = window.confirm(
      `Rename canonical tag ID?\n\n${tag.tagId} -> ${nextTagId}\n\nThis will update assignments and aliases.${impact}`
    );
    if (!ok) return;
  }

  try {
    const response = await postJson(MUTATE_ENDPOINT, {
      action: "edit",
      tag_id: tag.tagId,
      new_label: nextLabel,
      new_slug: nextSlug,
      allow_canonical_rename: canonicalChanged,
      client_time_utc: utcTimestamp()
    });
    setEditStatus(state, "success", "Saved.");
    setImportResult(state, "success", buildMutationSummary(response));
    await loadRegistry(state);
    renderControls(state);
    renderList(state);
    closeEditModal(state);
  } catch (error) {
    setEditStatus(state, "error", String(error.message || "Save failed."));
  }
}

async function handleTagDelete(state) {
  if (!state.editTagId) return;
  if (state.saveMode !== "post") {
    setEditStatus(state, "error", "Local server is required for edit/delete.");
    return;
  }

  const tag = findTagById(state, state.editTagId);
  if (!tag) {
    setEditStatus(state, "error", "Selected tag is no longer available.");
    return;
  }

  const ok = window.confirm(
    `Delete tag ${tag.tagId}?\n\nThis also removes it from series assignments and aliases.${state.editPreviewDelete ? `\n\nImpact:\n${state.editPreviewDelete}` : ""}`
  );
  if (!ok) return;

  try {
    const response = await postJson(MUTATE_ENDPOINT, {
      action: "delete",
      tag_id: tag.tagId,
      client_time_utc: utcTimestamp()
    });
    setImportResult(state, "success", buildMutationSummary(response));
    await loadRegistry(state);
    renderControls(state);
    renderList(state);
    closeEditModal(state);
  } catch (error) {
    setEditStatus(state, "error", String(error.message || "Delete failed."));
  }
}

async function handleImport(state) {
  if (!state.selectedFile) {
    setImportResult(state, "error", "Choose an import file first.");
    return;
  }

  let importRegistry = null;
  try {
    importRegistry = await readImportRegistryFromFile(state.selectedFile);
  } catch (error) {
    setImportResult(state, "error", String(error.message || "Invalid import file."));
    return;
  }

  if (state.saveMode === "post") {
    try {
      const response = await postJson(IMPORT_ENDPOINT, {
        mode: state.importMode,
        import_registry: importRegistry,
        import_filename: state.selectedFile ? String(state.selectedFile.name || "") : "",
        client_time_utc: utcTimestamp()
      });
      setImportResult(state, "success", buildImportSummary(response));
      await loadRegistry(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderImportMode(state);
      setImportResult(state, "error", `Server import failed; switched to patch mode. ${error.message || ""}`.trim());
    }
  }

  const patchResult = buildManualPatchForNewTags(state, importRegistry);
  setImportResult(state, patchResult.kind, patchResult.message);
  if (patchResult.snippet) {
    openPatchModal(state, patchResult.snippet);
  }
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  let responsePayload = null;
  try {
    responsePayload = await response.json();
  } catch (error) {
    throw new Error(`HTTP ${response.status}`);
  }

  if (!response.ok || !responsePayload || !responsePayload.ok) {
    const message = responsePayload && responsePayload.error ? responsePayload.error : `HTTP ${response.status}`;
    throw new Error(message);
  }
  return responsePayload;
}

async function readImportRegistryFromFile(file) {
  const rawText = await file.text();
  let payload = null;
  try {
    payload = JSON.parse(rawText);
  } catch (error) {
    throw new Error("Import file is not valid JSON.");
  }
  if (!payload || typeof payload !== "object") {
    throw new Error("Import file must be a JSON object.");
  }

  const rawTags = Array.isArray(payload.tags) ? payload.tags : null;
  if (!rawTags) {
    throw new Error("Import file must include a tags array.");
  }

  const normalizedTags = [];
  const seen = new Set();
  for (let idx = 0; idx < rawTags.length; idx += 1) {
    const normalized = normalizeImportTag(rawTags[idx], idx);
    if (!normalized) continue;
    if (seen.has(normalized.tag_id)) {
      const replaceIndex = normalizedTags.findIndex((item) => item.tag_id === normalized.tag_id);
      if (replaceIndex >= 0) normalizedTags[replaceIndex] = normalized;
      continue;
    }
    seen.add(normalized.tag_id);
    normalizedTags.push(normalized);
  }

  return {
    tag_registry_version: String(payload.tag_registry_version || "tag_registry_v1"),
    updated_at_utc: normalizeTimestamp(payload.updated_at_utc) || "",
    policy: payload.policy && typeof payload.policy === "object" ? payload.policy : undefined,
    tags: normalizedTags
  };
}

function normalizeImportTag(raw, idx) {
  if (!raw || typeof raw !== "object") {
    throw new Error(`Import tag at index ${idx} must be an object.`);
  }

  const tagId = normalize(raw.tag_id);
  const group = normalize(raw.group);
  const label = String(raw.label || "").trim();
  const status = normalize(raw.status || "active");
  const description = String(raw.description || "").trim();

  if (!tagId || tagId.indexOf(":") <= 0) {
    throw new Error(`Import tag ${idx} has invalid tag_id.`);
  }
  if (!GROUPS.includes(group)) {
    throw new Error(`Import tag ${idx} has invalid group.`);
  }
  if (!label) {
    throw new Error(`Import tag ${idx} must include label.`);
  }
  if (!["active", "deprecated", "candidate"].includes(status)) {
    throw new Error(`Import tag ${idx} has invalid status.`);
  }

  const tagGroup = tagId.split(":", 1)[0];
  if (tagGroup !== group) {
    throw new Error(`Import tag ${idx} group must match tag_id prefix.`);
  }

  return {
    tag_id: tagId,
    group,
    label,
    status,
    description
  };
}

function buildManualPatchForNewTags(state, importRegistry) {
  const importTags = Array.isArray(importRegistry && importRegistry.tags) ? importRegistry.tags : [];
  const existingIds = new Set(state.tags.map((tag) => tag.tagId));
  const nowUtc = utcTimestamp();

  const newTags = importTags
    .filter((tag) => tag && typeof tag === "object" && !existingIds.has(normalize(tag.tag_id)))
    .map((tag) => ({
      tag_id: normalize(tag.tag_id),
      group: normalize(tag.group),
      label: String(tag.label || "").trim(),
      status: normalize(tag.status || "active"),
      description: String(tag.description || "").trim(),
      updated_at_utc: nowUtc
    }));

  if (!newTags.length) {
    return {
      kind: "warn",
      message: `Patch mode (${state.importMode}): ${importTags.length} imported; 0 new tags to add.`,
      snippet: ""
    };
  }

  const snippet = JSON.stringify(
    {
      updated_at_utc: nowUtc,
      tags_to_append: newTags
    },
    null,
    2
  );

  return {
    kind: "warn",
    message: `Patch mode (${state.importMode}): ${importTags.length} imported; ${newTags.length} new tags available to append.`,
    snippet
  };
}

function openPatchModal(state, snippet) {
  state.patchSnippet = snippet;
  state.refs.patchSnippet.textContent = snippet;
  state.refs.patchModal.hidden = false;
}

function closePatchModal(state) {
  state.refs.patchModal.hidden = true;
}

function setImportResult(state, kind, message) {
  state.refs.importResult.textContent = message || "";
  state.refs.importResult.className = "tagRegistry__result";
  if (kind) state.refs.importResult.classList.add(`is-${kind}`);
}

function buildImportSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  const mode = normalize(response.mode || "");
  return [
    `mode ${mode || "unknown"}`,
    `Imported ${Number(response.imported_total || 0)} tags`,
    `added ${Number(response.added || 0)}`,
    `overwritten ${Number(response.overwritten || 0)}`,
    `unchanged ${Number(response.unchanged || 0)}`,
    `removed ${Number(response.removed || 0)}`,
    `final ${Number(response.final_total || 0)}`
  ].join("; ");
}

function buildMutationSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  const action = normalize(response.action || "");
  const oldTagId = String(response.old_tag_id || "");
  const newTagId = String(response.new_tag_id || "");
  const seriesRows = Number(response.series_rows_touched || 0);
  const refs = Number(response.series_tag_refs_rewritten || 0);
  const aliasesRewritten = Number(response.aliases_rewritten || 0);
  const aliasesRemovedEmpty = Number(response.aliases_removed_empty || 0);
  const aliasesRemovedRedundant = Number(response.aliases_removed_redundant || 0);
  const idPart = newTagId ? `${oldTagId} -> ${newTagId}` : oldTagId;
  return [
    `mode ${action || "unknown"}`,
    `tag ${idPart}`,
    `series rows ${seriesRows}`,
    `refs ${refs}`,
    `aliases rewritten ${aliasesRewritten}`,
    `aliases removed-empty ${aliasesRemovedEmpty}`,
    `aliases removed-redundant ${aliasesRemovedRedundant}`
  ].join("; ");
}

function toTimestampMs(value) {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isFinite(ms) ? ms : null;
}

function normalizeTimestamp(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const ms = Date.parse(raw);
  if (!Number.isFinite(ms)) return "";
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
}

function formatTimestamp(value) {
  const normalized = normalizeTimestamp(value);
  if (!normalized) return "—";
  const date = new Date(normalized);
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hour = String(date.getUTCHours()).padStart(2, "0");
  const minute = String(date.getUTCMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} - ${hour}:${minute}`;
}

function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function renderError(state, message) {
  state.mount.innerHTML = `<div class="tagStudioError">${escapeHtml(message)}</div>`;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
