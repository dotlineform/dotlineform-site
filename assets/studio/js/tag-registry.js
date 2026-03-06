import {
  getStudioDataPath,
  getStudioGroups,
  getStudioRoute,
  loadStudioConfig
} from "./studio-config.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const HEALTH_ENDPOINT = "http://127.0.0.1:8787/health";
const IMPORT_ENDPOINT = "http://127.0.0.1:8787/import-tag-registry";
const MUTATE_ENDPOINT = "http://127.0.0.1:8787/mutate-tag";
const MUTATE_PREVIEW_ENDPOINT = "http://127.0.0.1:8787/mutate-tag-preview";
const DEMOTE_ENDPOINT = "http://127.0.0.1:8787/demote-tag";
const DEMOTE_PREVIEW_ENDPOINT = "http://127.0.0.1:8787/demote-tag-preview";
const MAX_ALIAS_TAGS = 4;
const DEMOTE_TAG_MATCH_CAP = 12;
const TAG_SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;
let GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagRegistryPage);
} else {
  initTagRegistryPage();
}

async function initTagRegistryPage() {
  const mount = document.getElementById("tag-registry");
  if (!mount) return;

  const config = await loadStudioConfig();
  STUDIO_GROUPS = getStudioGroups(config);
  GROUP_INFO_PAGE_PATH = getStudioRoute(config, "tag_groups");

  const state = {
    mount,
    config,
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
    newTagState: null,
    demoteState: null,
    aliasKeys: new Set(),
    groupDescriptions: new Map(),
    deleteTagId: "",
    deletePreview: "",
    deletePreviewSeq: 0,
    registryOptions: [],
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
    renderError(state, "Failed to load tag data from /assets/studio/data/tag_registry.json and /assets/studio/data/tag_aliases.json.");
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
          <button type="button" class="tagStudio__button tagStudio__button--primary tagRegistry__newTagBtn" data-role="open-new-tag">New tag</button>
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
        <p class="tagStudioModal__label">Manual patch snippet</p>
        <pre class="tagStudioModal__pre" data-role="patch-snippet"></pre>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="copy-patch">Copy</button>
          <button type="button" class="tagStudio__button" data-role="close-modal">Close</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="edit-modal" hidden>
      <div class="tagStudioModal__backdrop"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryEditTitle">
        <h3 id="tagRegistryEditTitle">Edit Tag</h3>
        <p class="tagRegistryEdit__meta" data-role="edit-tag-id"></p>
        <div class="tagRegistryEdit__fields">
          <label class="tagRegistryEdit__field">
            <input type="text" class="tagStudio__input tagRegistryEdit__readonly" data-role="edit-tag-name" autocomplete="off" readonly>
          </label>
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">description</span>
            <textarea class="tagStudio__input tagRegistryEdit__descriptionInput" data-role="edit-description" rows="3" autocomplete="off"></textarea>
          </label>
        </div>
        <p class="tagRegistryEdit__status" data-role="edit-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="save-edit">Save</button>
          <button type="button" class="tagStudio__button" data-role="close-edit-modal">Close</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="new-modal" hidden>
      <div class="tagStudioModal__backdrop"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryNewTitle">
        <h3 id="tagRegistryNewTitle">New Tag</h3>
        <div class="tagStudio__key tagRegistryNew__key" data-role="new-group-key"></div>
        <div class="tagRegistryEdit__fields">
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">slug</span>
            <input type="text" class="tagStudio__input" data-role="new-tag-slug" autocomplete="off">
          </label>
          <p class="tagAliasesEdit__warning" data-role="new-tag-warning"></p>
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">description</span>
            <textarea class="tagStudio__input tagRegistryEdit__descriptionInput" data-role="new-tag-description" rows="3" autocomplete="off"></textarea>
          </label>
        </div>
        <p class="tagRegistryEdit__status" data-role="new-tag-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="create-tag" disabled>Create</button>
          <button type="button" class="tagStudio__button" data-role="close-new-modal">Cancel</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="demote-modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-demote-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryDemoteTitle">
        <h3 id="tagRegistryDemoteTitle">Demote Tag to Alias</h3>
        <p class="tagRegistryEdit__meta" data-role="demote-tag-meta"></p>
        <div class="tagRegistryEdit__fields">
          <label class="tagRegistryEdit__field tagAliasesEdit__searchWrap">
            <span class="tagRegistryEdit__label">find target tags</span>
            <input type="text" class="tagStudio__input" data-role="demote-tag-search" autocomplete="off" placeholder="search tags">
            <div class="tagStudio__popup" data-role="demote-tag-popup-wrap" hidden>
              <div class="tagStudio__popupInner" data-role="demote-tag-popup"></div>
            </div>
          </label>
        </div>
        <div class="tagStudio__key tagAliasesEdit__key" data-role="demote-group-key"></div>
        <div class="tagStudio__chipList tagAliasesEdit__selectedTags" data-role="demote-tag-list"></div>
        <p class="tagRegistryEdit__status" data-role="demote-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="confirm-demote" disabled>Demote</button>
          <button type="button" class="tagStudio__button" data-role="close-demote-modal">Close</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="delete-modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-delete-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryDeleteTitle">
        <h3 id="tagRegistryDeleteTitle">Delete Tag</h3>
        <p class="tagRegistryEdit__meta" data-role="delete-tag-meta"></p>
        <p class="tagRegistryEdit__impact">
          Deleting this tag also removes matching tag assignments and removes this tag from aliases. Aliases left with no targets are deleted.
        </p>
        <p class="tagRegistryEdit__impact" data-role="delete-impact"></p>
        <p class="tagRegistryEdit__status" data-role="delete-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="confirm-delete-tag">Delete</button>
          <button type="button" class="tagStudio__button" data-role="close-delete-modal">Close</button>
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
    openNewTag: state.mount.querySelector('[data-role="open-new-tag"]'),
    saveMode: state.mount.querySelector('[data-role="save-mode"]'),
    selectedFile: state.mount.querySelector('[data-role="selected-file"]'),
    importResult: state.mount.querySelector('[data-role="import-result"]'),
    list: state.mount.querySelector('[data-role="list"]'),
    patchModal: state.mount.querySelector('[data-role="patch-modal"]'),
    patchSnippet: state.mount.querySelector('[data-role="patch-snippet"]'),
    copyPatch: state.mount.querySelector('[data-role="copy-patch"]'),
    editModal: state.mount.querySelector('[data-role="edit-modal"]'),
    editTagId: state.mount.querySelector('[data-role="edit-tag-id"]'),
    editTagName: state.mount.querySelector('[data-role="edit-tag-name"]'),
    editDescription: state.mount.querySelector('[data-role="edit-description"]'),
    editStatus: state.mount.querySelector('[data-role="edit-status"]'),
    saveEdit: state.mount.querySelector('[data-role="save-edit"]'),
    newModal: state.mount.querySelector('[data-role="new-modal"]'),
    newGroupKey: state.mount.querySelector('[data-role="new-group-key"]'),
    newTagSlug: state.mount.querySelector('[data-role="new-tag-slug"]'),
    newTagWarning: state.mount.querySelector('[data-role="new-tag-warning"]'),
    newTagDescription: state.mount.querySelector('[data-role="new-tag-description"]'),
    newTagStatus: state.mount.querySelector('[data-role="new-tag-status"]'),
    createTag: state.mount.querySelector('[data-role="create-tag"]'),
    demoteModal: state.mount.querySelector('[data-role="demote-modal"]'),
    demoteTagMeta: state.mount.querySelector('[data-role="demote-tag-meta"]'),
    demoteTagSearch: state.mount.querySelector('[data-role="demote-tag-search"]'),
    demoteTagPopupWrap: state.mount.querySelector('[data-role="demote-tag-popup-wrap"]'),
    demoteTagPopup: state.mount.querySelector('[data-role="demote-tag-popup"]'),
    demoteGroupKey: state.mount.querySelector('[data-role="demote-group-key"]'),
    demoteTagList: state.mount.querySelector('[data-role="demote-tag-list"]'),
    demoteStatus: state.mount.querySelector('[data-role="demote-status"]'),
    confirmDemote: state.mount.querySelector('[data-role="confirm-demote"]'),
    deleteModal: state.mount.querySelector('[data-role="delete-modal"]'),
    deleteTagMeta: state.mount.querySelector('[data-role="delete-tag-meta"]'),
    deleteImpact: state.mount.querySelector('[data-role="delete-impact"]'),
    deleteStatus: state.mount.querySelector('[data-role="delete-status"]'),
    confirmDeleteTag: state.mount.querySelector('[data-role="confirm-delete-tag"]')
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
      clearImportResult(state);
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

  state.refs.openNewTag.addEventListener("click", () => {
    openNewTagModal(state);
  });

  state.mount.addEventListener("click", (event) => {
    const groupButton = event.target.closest("button[data-group]");
    if (groupButton) {
      const group = normalize(groupButton.getAttribute("data-group"));
      if (!group || group === "all") {
        state.filterGroup = "all";
        state.searchQuery = "";
        state.refs.search.value = "";
      } else {
        state.filterGroup = group;
      }
      renderControls(state);
      renderList(state);
      return;
    }

    const tagButton = event.target.closest("button[data-tag-id]");
    const demoteButton = event.target.closest("button[data-demote-tag-id]");
    const deleteButton = event.target.closest("button[data-delete-tag-id]");
    if (demoteButton) {
      const tagId = normalize(demoteButton.getAttribute("data-demote-tag-id"));
      if (tagId) openDemoteModal(state, tagId);
      return;
    }
    if (deleteButton) {
      const tagId = normalize(deleteButton.getAttribute("data-delete-tag-id"));
      if (tagId) openDeleteModal(state, tagId);
      return;
    }

    if (tagButton) {
      const tagId = normalize(tagButton.getAttribute("data-tag-id"));
      if (tagId) openEditModal(state, tagId);
      return;
    }

    const sortButton = event.target.closest("button[data-sort-key]");
    if (!sortButton) return;
    const nextSortKey = normalize(sortButton.getAttribute("data-sort-key"));
    if (!["label", "description"].includes(nextSortKey)) return;
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

  state.refs.newModal.addEventListener("click", (event) => {
    if (event.target.closest('[data-role="close-new-modal"]')) {
      closeNewTagModal(state);
      return;
    }
    const groupButton = event.target.closest("button[data-new-group]");
    if (!groupButton || !state.newTagState) return;
    const group = normalize(groupButton.getAttribute("data-new-group"));
    if (!STUDIO_GROUPS.includes(group)) return;
    state.newTagState.group = group;
    updateNewTagUi(state);
  });

  state.refs.newTagSlug.addEventListener("input", () => {
    updateNewTagUi(state);
  });

  state.refs.newTagDescription.addEventListener("input", () => {
    updateNewTagUi(state);
  });

  state.refs.createTag.addEventListener("click", () => {
    void handleCreateTag(state);
  });

  state.refs.demoteModal.addEventListener("click", (event) => {
    if (event.target.closest('[data-role="close-demote-modal"]')) {
      closeDemoteModal(state);
      return;
    }
    if (state.refs.demoteTagPopupWrap.hidden) return;
    if (!event.target.closest('[data-role="demote-tag-popup-wrap"]') && !event.target.closest('[data-role="demote-tag-search"]')) {
      hideDemoteTagPopup(state);
    }
  });

  state.refs.demoteTagSearch.addEventListener("input", () => {
    renderDemoteTagPopup(state);
  });

  state.refs.demoteTagSearch.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      hideDemoteTagPopup(state);
      state.refs.demoteTagSearch.blur();
    }
  });

  state.refs.demoteTagPopup.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-popup-demote-tag-id]");
    if (!button) return;
    const tagId = normalize(button.getAttribute("data-popup-demote-tag-id"));
    if (!tagId) return;
    addDemoteTag(state, tagId);
    state.refs.demoteTagSearch.value = "";
    hideDemoteTagPopup(state);
    updateDemoteUi(state);
  });

  state.refs.demoteTagList.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-remove-demote-tag]");
    if (!button || !state.demoteState) return;
    const tagId = normalize(button.getAttribute("data-remove-demote-tag"));
    if (!tagId) return;
    state.demoteState.tags = state.demoteState.tags.filter((item) => item !== tagId);
    updateDemoteUi(state);
  });

  state.refs.confirmDemote.addEventListener("click", () => {
    void handleTagDemote(state);
  });

  state.refs.deleteModal.addEventListener("click", (event) => {
    if (!event.target.closest('[data-role="close-delete-modal"]')) return;
    closeDeleteModal(state);
  });

  state.refs.confirmDeleteTag.addEventListener("click", () => {
    void handleDeleteFromModal(state);
  });

  state.refs.editDescription.addEventListener("input", () => {
    setEditStatus(state, "", "");
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
  const [registryData, aliasesData] = await Promise.all([
    fetchJson(getStudioDataPath(state.config, "tag_registry")),
    fetchJson(getStudioDataPath(state.config, "tag_aliases"))
  ]);
  let groupsData = null;
  try {
    groupsData = await fetchJson(getStudioDataPath(state.config, "tag_groups"));
  } catch (error) {
    groupsData = null;
  }
  state.registryUpdatedAt = normalizeTimestamp(registryData && registryData.updated_at_utc);
  state.tags = normalizeRegistryTags(registryData, state.registryUpdatedAt);
  state.aliasKeys = buildAliasKeySet(aliasesData);
  state.groupDescriptions = buildGroupDescriptionMap(groupsData);
  state.registryOptions = buildRegistryOptions(state.tags);
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
    const label = normalize(raw.label) || labelFromTagId(tagId);
    const description = String(raw.description || "").trim();
    const status = normalize(raw.status || "active");
    const updatedAtUtc = normalizeTimestamp(raw.updated_at_utc) || fallbackUpdatedAt;

    if (!STUDIO_GROUPS.includes(group) || !tagId || !label) continue;
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

function buildRegistryOptions(tags) {
  const options = [];
  for (const tag of tags || []) {
    if (!tag || !tag.tagId || !STUDIO_GROUPS.includes(tag.group)) continue;
    options.push({
      tagId: tag.tagId,
      group: tag.group,
      label: normalize(tag.label) || labelFromTagId(tag.tagId) || tag.tagId
    });
  }
  options.sort((a, b) => {
    const byLabel = a.label.localeCompare(b.label, undefined, { sensitivity: "base" });
    if (byLabel !== 0) return byLabel;
    return a.tagId.localeCompare(b.tagId);
  });
  return options;
}

function buildAliasKeySet(data) {
  const out = new Set();
  const aliasesObj = data && typeof data.aliases === "object" && data.aliases ? data.aliases : {};
  for (const rawKey of Object.keys(aliasesObj)) {
    const key = normalize(rawKey);
    if (!key) continue;
    out.add(key);
  }
  return out;
}

function buildGroupDescriptionMap(data) {
  const out = new Map();
  const groups = Array.isArray(data && data.groups) ? data.groups : [];
  for (const raw of groups) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalize(raw.group_id);
    const description = String(raw.description || "").trim();
    if (!STUDIO_GROUPS.includes(groupId) || !description) continue;
    out.set(groupId, description);
  }
  return out;
}

function renderControls(state) {
  const groupCounts = countTagsByGroup(state.tags);
  const totalCount = state.tags.length;
  const allActiveClass = state.filterGroup === "all" ? " is-active" : "";
  const groupButtons = STUDIO_GROUPS.map((group) => {
    const activeClass = state.filterGroup === group ? " is-active" : "";
    const count = Number(groupCounts[group] || 0);
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)} tagRegistry__groupBtn${activeClass}"
        data-group="${escapeHtml(group)}"
        ${titleAttr}
      >
        ${escapeHtml(group)} [${count}]
      </button>
    `;
  }).join("");

  state.refs.key.innerHTML = `
    <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">All tags [${totalCount}]</button>
    ${groupButtons}
    ${renderGroupInfoControl(state, "registry")}
  `;
}

function countTagsByGroup(tags) {
  const counts = { subject: 0, domain: 0, form: 0, theme: 0 };
  for (const tag of tags || []) {
    const group = normalize(tag && tag.group);
    if (STUDIO_GROUPS.includes(group)) {
      counts[group] += 1;
    }
  }
  return counts;
}

function groupTitleAttr(state, group) {
  const description = String(state.groupDescriptions.get(group) || "").trim();
  if (!description) return "";
  return `title="${escapeHtml(description)}"`;
}

function renderGroupInfoControl(state, scope) {
  return `
    <a
      class="tagStudio__keyPill tagStudio__keyInfoBtn"
      href="${GROUP_INFO_PAGE_PATH}"
      target="_blank"
      rel="noopener noreferrer"
      title="Open group descriptions in a new tab"
      aria-label="Open group descriptions in a new tab"
    >
      <em>i</em>
    </a>
  `;
}

function renderList(state) {
  const visible = getVisibleSortedTags(state);
  const headerHtml = `
    <div class="tagRegistry__head">
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
          <div class="tagRegistry__tagCol">
            <div class="tagRegistry__tagActions">
              <span class="tagStudio__chip tagStudio__chip--${escapeHtml(tag.group)} tagRegistry__tagChip" title="${escapeHtml(tag.tagId)}">
                <button type="button" class="tagRegistry__tagInlineBtn" data-tag-id="${escapeHtml(tag.tagId)}" aria-label="Edit ${escapeHtml(tag.tagId)}">
                  ${escapeHtml(tag.label)}
                </button>
              <button
                type="button"
                class="tagStudio__chipRemove tagRegistry__demoteBtn"
                data-demote-tag-id="${escapeHtml(tag.tagId)}"
                title="Demote canonical tag to alias"
                aria-label="Demote ${escapeHtml(tag.tagId)}"
              >
                ←
              </button>
              <button
                type="button"
                class="tagStudio__chipRemove"
                data-delete-tag-id="${escapeHtml(tag.tagId)}"
                title="Delete canonical tag"
                aria-label="Delete ${escapeHtml(tag.tagId)}"
              >
                ×
              </button>
              </span>
            </div>
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
  clearImportResult(state);
  const [, slug = ""] = String(tag.tagId || "").split(":", 2);
  state.editTagId = tag.tagId;
  state.refs.editTagId.innerHTML = `
    <span class="tagStudio__chip tagStudio__chip--${escapeHtml(tag.group)}" title="${escapeHtml(String(state.groupDescriptions.get(tag.group) || tag.tagId))}">
      ${escapeHtml(tag.group)}
    </span>
  `;
  state.refs.editTagName.value = slug;
  state.refs.editDescription.value = String(tag.description || "");
  state.refs.editStatus.className = "tagRegistryEdit__status";
  state.refs.editStatus.textContent = state.saveMode === "post"
    ? ""
    : "Local server is required for edit.";
  state.refs.editModal.hidden = false;
}

function closeEditModal(state) {
  state.refs.editModal.hidden = true;
  state.editTagId = "";
  state.refs.editTagName.value = "";
  state.refs.editDescription.value = "";
}

function openNewTagModal(state) {
  clearImportResult(state);
  state.newTagState = {
    group: "",
    slug: "",
    description: ""
  };
  state.refs.newTagSlug.value = "";
  state.refs.newTagDescription.value = "";
  state.refs.newTagWarning.textContent = "";
  setNewTagStatus(state, "", "");
  renderNewTagGroupKey(state);
  state.refs.createTag.disabled = true;
  state.refs.newModal.hidden = false;
  state.refs.newTagSlug.focus();
}

function closeNewTagModal(state) {
  state.newTagState = null;
  state.refs.newModal.hidden = true;
  state.refs.newTagSlug.value = "";
  state.refs.newTagDescription.value = "";
  state.refs.newTagWarning.textContent = "";
  setNewTagStatus(state, "", "");
  state.refs.newGroupKey.innerHTML = "";
  state.refs.createTag.disabled = true;
}

function setNewTagStatus(state, kind, message) {
  state.refs.newTagStatus.textContent = message || "";
  state.refs.newTagStatus.className = "tagRegistryEdit__status";
  if (kind) state.refs.newTagStatus.classList.add(`is-${kind}`);
}

function renderNewTagGroupKey(state) {
  if (!state.newTagState) {
    state.refs.newGroupKey.innerHTML = "";
    return;
  }
  state.refs.newGroupKey.innerHTML = STUDIO_GROUPS.map((group) => {
    const activeClass = state.newTagState.group === group ? " is-active" : "";
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)}${activeClass}"
        data-new-group="${escapeHtml(group)}"
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("") + renderGroupInfoControl(state, "new");
}

function getNewTagValidation(state) {
  if (!state.newTagState) {
    return { valid: false, warning: "", group: "", slug: "", description: "", tagId: "" };
  }
  const group = normalize(state.newTagState.group);
  const slug = normalize(state.refs.newTagSlug.value);
  const description = String(state.refs.newTagDescription.value || "").trim();
  let warning = "";

  if (!STUDIO_GROUPS.includes(group)) {
    warning = "Select a tag group.";
  } else if (!slug) {
    warning = "Tag slug is required.";
  } else if (!TAG_SLUG_RE.test(slug)) {
    warning = "Tag slug must be lowercase letters, numbers, or hyphens.";
  } else {
    const tagId = `${group}:${slug}`;
    const exists = state.tags.some((tag) => tag.tagId === tagId);
    if (exists) warning = "Tag already exists.";
  }

  return {
    valid: !warning,
    warning,
    group,
    slug,
    description,
    tagId: group && slug ? `${group}:${slug}` : ""
  };
}

function updateNewTagUi(state) {
  if (!state.newTagState) return;
  const slug = normalize(state.refs.newTagSlug.value);
  if (state.refs.newTagSlug.value !== slug) {
    state.refs.newTagSlug.value = slug;
  }
  state.newTagState.slug = slug;
  state.newTagState.description = String(state.refs.newTagDescription.value || "").trim();

  renderNewTagGroupKey(state);
  const validation = getNewTagValidation(state);
  state.refs.newTagWarning.textContent = validation.warning || "";
  state.refs.createTag.disabled = !validation.valid;
  if (!validation.warning) {
    setNewTagStatus(state, "", "");
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

function buildDeletePreviewPayload(tagId) {
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId) return null;
  return {
    action: "delete",
    tag_id: normalizedTagId,
    client_time_utc: utcTimestamp()
  };
}

async function refreshDeleteImpactPreview(state) {
  if (state.saveMode !== "post") {
    setImpactPreview(state.refs.deleteImpact, "error", "Delete impact: unavailable (local server required).");
    return;
  }
  const payload = buildDeletePreviewPayload(state.deleteTagId);
  if (!payload) {
    setImpactPreview(state.refs.deleteImpact, "error", "Delete impact: unavailable.");
    return;
  }
  const seq = ++state.deletePreviewSeq;
  try {
    const response = await postJson(MUTATE_PREVIEW_ENDPOINT, payload);
    if (seq !== state.deletePreviewSeq || state.refs.deleteModal.hidden) return;
    state.deletePreview = buildMutationSummary(response);
    setImpactPreview(state.refs.deleteImpact, "", `Delete impact: ${state.deletePreview}`);
  } catch (error) {
    if (seq !== state.deletePreviewSeq || state.refs.deleteModal.hidden) return;
    const message = String(error && error.message ? error.message : "preview failed");
    setImpactPreview(state.refs.deleteImpact, "error", `Delete impact: ${message}`);
  }
}

async function handleTagEdit(state) {
  if (!state.editTagId) return;
  if (state.saveMode !== "post") {
    setEditStatus(state, "error", "Local server is required for edit.");
    return;
  }

  const tag = findTagById(state, state.editTagId);
  if (!tag) {
    setEditStatus(state, "error", "Selected tag is no longer available.");
    return;
  }

  const description = String(state.refs.editDescription.value || "").trim();
  if (description === String(tag.description || "").trim()) {
    setEditStatus(state, "", "No changes to save.");
    return;
  }

  try {
    const response = await postJson(MUTATE_ENDPOINT, {
      action: "edit",
      tag_id: tag.tagId,
      description,
      allow_canonical_rename: false,
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

async function handleCreateTag(state) {
  if (!state.newTagState) return;
  const validation = getNewTagValidation(state);
  if (!validation.valid) {
    state.refs.newTagWarning.textContent = validation.warning || "";
    return;
  }

  const newTagRow = {
    tag_id: validation.tagId,
    group: validation.group,
    label: validation.slug,
    status: "active",
    description: validation.description
  };

  if (state.saveMode === "post") {
    try {
      const response = await postJson(IMPORT_ENDPOINT, {
        mode: "add",
        import_registry: {
          tags: [newTagRow]
        },
        import_filename: "",
        client_time_utc: utcTimestamp()
      });
      closeNewTagModal(state);
      setImportResult(state, "success", buildImportSummary(response));
      await loadRegistry(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderImportMode(state);
      setNewTagStatus(state, "error", `Server create failed; switched to patch mode. ${error.message || ""}`.trim());
    }
  }

  const patchResult = buildManualPatchForCreateTag(newTagRow);
  closeNewTagModal(state);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function setDeleteStatus(state, kind, message) {
  state.refs.deleteStatus.textContent = message || "";
  state.refs.deleteStatus.className = "tagRegistryEdit__status";
  if (kind) state.refs.deleteStatus.classList.add(`is-${kind}`);
}

function openDeleteModal(state, tagId) {
  clearImportResult(state);
  const tag = findTagById(state, tagId);
  if (!tag) {
    setImportResult(state, "error", "Selected tag is no longer available.");
    return;
  }
  state.deleteTagId = tag.tagId;
  state.deletePreview = "";
  state.deletePreviewSeq += 1;
  state.refs.deleteTagMeta.textContent = `tag: ${tag.tagId}`;
  state.refs.deleteImpact.textContent = "";
  state.refs.deleteImpact.className = "tagRegistryEdit__impact";
  setDeleteStatus(state, "", "");
  state.refs.confirmDeleteTag.disabled = state.saveMode !== "post";
  state.refs.deleteModal.hidden = false;

  if (state.saveMode !== "post") {
    setDeleteStatus(state, "error", "Local server is required for delete.");
    setImpactPreview(state.refs.deleteImpact, "error", "Delete impact: unavailable (local server required).");
    return;
  }

  void refreshDeleteImpactPreview(state);
}

function closeDeleteModal(state) {
  state.refs.deleteModal.hidden = true;
  state.deleteTagId = "";
  state.deletePreview = "";
  state.deletePreviewSeq += 1;
  state.refs.deleteTagMeta.textContent = "";
  state.refs.deleteImpact.textContent = "";
  state.refs.deleteImpact.className = "tagRegistryEdit__impact";
  setDeleteStatus(state, "", "");
  state.refs.confirmDeleteTag.disabled = false;
}

async function handleDeleteFromModal(state) {
  if (!state.deleteTagId) return;
  if (state.saveMode !== "post") {
    setDeleteStatus(state, "error", "Local server is required for delete.");
    return;
  }

  const tag = findTagById(state, state.deleteTagId);
  if (!tag) {
    setDeleteStatus(state, "error", "Selected tag is no longer available.");
    return;
  }

  try {
    const response = await postJson(MUTATE_ENDPOINT, {
      action: "delete",
      tag_id: tag.tagId,
      client_time_utc: utcTimestamp()
    });
    closeDeleteModal(state);
    setImportResult(state, "success", buildMutationSummary(response));
    await loadRegistry(state);
    renderControls(state);
    renderList(state);
  } catch (error) {
    setDeleteStatus(state, "error", String(error.message || "Delete failed."));
  }
}

function openDemoteModal(state, tagId) {
  clearImportResult(state);
  const tag = findTagById(state, tagId);
  if (!tag) {
    setImportResult(state, "error", "Selected tag is no longer available.");
    return;
  }
  const aliasKey = tag.tagId.split(":")[1] || tag.tagId;
  if (state.aliasKeys.has(aliasKey)) {
    setImportResult(state, "error", `Alias already exists: ${aliasKey}. Demotion overwrite is not permitted.`);
    return;
  }

  state.demoteState = {
    tagId: tag.tagId,
    tags: []
  };
  state.refs.demoteTagMeta.textContent = `tag: ${tag.tagId} -> alias "${aliasKey}"`;
  state.refs.demoteTagSearch.value = "";
  hideDemoteTagPopup(state);
  updateDemoteUi(state);
  state.refs.demoteModal.hidden = false;
  state.refs.demoteTagSearch.focus();
}

function closeDemoteModal(state) {
  state.demoteState = null;
  state.refs.demoteModal.hidden = true;
  state.refs.demoteTagMeta.textContent = "";
  state.refs.demoteTagSearch.value = "";
  state.refs.demoteTagList.innerHTML = "";
  state.refs.demoteGroupKey.innerHTML = "";
  state.refs.confirmDemote.disabled = true;
  setDemoteStatus(state, "", "");
  hideDemoteTagPopup(state);
}

function setDemoteStatus(state, kind, message) {
  state.refs.demoteStatus.textContent = message || "";
  state.refs.demoteStatus.className = "tagRegistryEdit__status";
  if (kind) state.refs.demoteStatus.classList.add(`is-${kind}`);
}

function renderDemoteGroupKey(state) {
  if (!state.demoteState) {
    state.refs.demoteGroupKey.innerHTML = "";
    return;
  }
  const selected = new Set((state.demoteState.tags || []).map((tagId) => normalize(tagId).split(":", 1)[0]));
  state.refs.demoteGroupKey.innerHTML = STUDIO_GROUPS.map((group) => {
    const activeClass = selected.has(group) ? " is-active" : "";
    const titleAttr = groupTitleAttr(state, group);
    return `<span class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)}${activeClass}" ${titleAttr}>${escapeHtml(group)}</span>`;
  }).join("") + renderGroupInfoControl(state, "demote");
}

function renderDemoteTagList(state) {
  if (!state.demoteState) {
    state.refs.demoteTagList.innerHTML = "";
    return;
  }
  const rows = state.demoteState.tags.map((tagId) => {
    const info = findTagById(state, tagId);
    const group = info && STUDIO_GROUPS.includes(info.group) ? info.group : "warning";
    const label = info ? info.label : tagId;
    return `
      <span class="tagStudio__chip tagStudio__chip--${escapeHtml(group)}" title="${escapeHtml(tagId)}">
        ${escapeHtml(label)}
        <button
          type="button"
          class="tagStudio__chipRemove"
          data-remove-demote-tag="${escapeHtml(tagId)}"
          aria-label="Remove ${escapeHtml(tagId)}"
        >
          x
        </button>
      </span>
    `;
  }).join("");
  state.refs.demoteTagList.innerHTML = rows || '<span class="tagStudio__empty">none</span>';
}

function getDemoteValidation(state) {
  if (!state.demoteState) return { valid: false, tags: [], warning: "" };
  const tags = Array.isArray(state.demoteState.tags) ? state.demoteState.tags.slice() : [];

  let warning = "";
  if (!tags.length) {
    warning = "Select at least one target tag.";
  } else if (tags.length > MAX_ALIAS_TAGS) {
    warning = `Select up to ${MAX_ALIAS_TAGS} tags.`;
  } else {
    const seenGroups = new Set();
    for (const tagId of tags) {
      if (tagId === state.demoteState.tagId) {
        warning = "Target list must not include the demoted tag.";
        break;
      }
      const info = findTagById(state, tagId);
      if (!info) {
        warning = `Unknown tag selected: ${tagId}`;
        break;
      }
      if (seenGroups.has(info.group)) {
        warning = `Only one target tag per group is allowed (${info.group}).`;
        break;
      }
      seenGroups.add(info.group);
    }
  }

  return {
    valid: !warning,
    tags,
    warning
  };
}

function updateDemoteUi(state) {
  if (!state.demoteState) return;
  renderDemoteGroupKey(state);
  renderDemoteTagList(state);
  const validation = getDemoteValidation(state);
  state.refs.confirmDemote.disabled = !validation.valid;
  if (validation.warning) {
    const kind = validation.warning === "Select at least one target tag." ? "" : "error";
    setDemoteStatus(state, kind, validation.warning);
  } else {
    setDemoteStatus(state, "", "");
  }
}

function getDemoteTagMatches(state, query) {
  const normalizedQuery = normalize(query);
  if (!normalizedQuery || !state.demoteState) {
    return { matches: [], truncated: false };
  }
  const selected = new Set(state.demoteState.tags || []);
  const allMatches = state.registryOptions.filter((item) => {
    if (selected.has(item.tagId)) return false;
    if (item.tagId === state.demoteState.tagId) return false;
    const slug = item.tagId.split(":", 2)[1] || "";
    return (
      normalize(item.label).startsWith(normalizedQuery) ||
      normalize(slug).startsWith(normalizedQuery)
    );
  });
  return {
    matches: allMatches.slice(0, DEMOTE_TAG_MATCH_CAP),
    truncated: allMatches.length > DEMOTE_TAG_MATCH_CAP
  };
}

function renderDemoteTagPopup(state) {
  if (!state.demoteState) return;
  const result = getDemoteTagMatches(state, state.refs.demoteTagSearch.value);
  if (!result.matches.length) {
    hideDemoteTagPopup(state);
    return;
  }
  const chips = result.matches.map((item) => `
    <button
      type="button"
      class="tagStudio__popupPill tagStudio__chip--${escapeHtml(item.group)}"
      data-popup-demote-tag-id="${escapeHtml(item.tagId)}"
      title="${escapeHtml(item.tagId)}"
    >
      ${escapeHtml(item.label)}
    </button>
  `);
  if (result.truncated) {
    chips.push('<span class="tagStudio__popupPill tagAliasesEdit__popupMore" title="More matches available">...</span>');
  }
  state.refs.demoteTagPopup.innerHTML = chips.join("");
  state.refs.demoteTagPopupWrap.hidden = false;
}

function hideDemoteTagPopup(state) {
  state.refs.demoteTagPopupWrap.hidden = true;
  state.refs.demoteTagPopup.innerHTML = "";
}

function addDemoteTag(state, tagId) {
  if (!state.demoteState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId) return;
  const tag = findTagById(state, normalizedTagId);
  if (!tag) return;
  if (normalizedTagId === state.demoteState.tagId) {
    setDemoteStatus(state, "error", "Target list must not include the demoted tag.");
    return;
  }
  if (state.demoteState.tags.includes(normalizedTagId)) return;
  if (state.demoteState.tags.length >= MAX_ALIAS_TAGS) {
    setDemoteStatus(state, "error", `Select up to ${MAX_ALIAS_TAGS} tags.`);
    return;
  }
  const nextGroup = tag.group;
  const groupConflict = state.demoteState.tags.some((item) => {
    const existing = findTagById(state, item);
    return Boolean(existing && existing.group === nextGroup);
  });
  if (groupConflict) {
    setDemoteStatus(state, "error", `Only one target tag per group is allowed (${nextGroup}).`);
    return;
  }
  state.demoteState.tags.push(normalizedTagId);
}

async function handleTagDemote(state) {
  if (!state.demoteState) return;
  const tag = findTagById(state, state.demoteState.tagId);
  if (!tag) {
    setDemoteStatus(state, "error", "Selected tag is no longer available.");
    setImportResult(state, "error", "Selected tag is no longer available.");
    return;
  }

  const aliasKey = tag.tagId.split(":")[1] || tag.tagId;
  if (state.aliasKeys.has(aliasKey)) {
    const message = `Alias already exists: ${aliasKey}. Demotion overwrite is not permitted.`;
    setDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }

  const validation = getDemoteValidation(state);
  if (!validation.valid) {
    setDemoteStatus(state, "error", validation.warning || "Invalid target tags.");
    return;
  }

  const aliasTargets = validation.tags.slice().sort((a, b) => a.localeCompare(b));

  const payload = {
    tag_id: tag.tagId,
    alias_targets: aliasTargets,
    client_time_utc: utcTimestamp()
  };

  if (state.saveMode === "post") {
    let preview = null;
    try {
      preview = await postJson(DEMOTE_PREVIEW_ENDPOINT, payload);
    } catch (error) {
      const message = String(error.message || "Demotion preview failed.");
      setDemoteStatus(state, "error", message);
      setImportResult(state, "error", message);
      return;
    }

    const previewSummary = String(preview.summary_text || "").trim() || `demote ${tag.tagId}`;
    if (Number(preview.demoted_alias_overwritten || 0) > 0) {
      const message = `Alias already exists: ${aliasKey}. Demotion overwrite is not permitted.`;
      setDemoteStatus(state, "error", message);
      setImportResult(state, "error", message);
      return;
    }
    const ok = window.confirm(
      `Demote "${tag.tagId}" to alias "${aliasKey}"?\n\nTargets: ${aliasTargets.join(", ")}\n\nImpact:\n${previewSummary}`
    );
    if (!ok) {
      clearImportResult(state);
      return;
    }

    try {
      const response = await postJson(DEMOTE_ENDPOINT, payload);
      closeDemoteModal(state);
      setImportResult(state, "success", String(response.summary_text || "Demoted."));
      await loadRegistry(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      const message = String(error.message || "Demotion failed.");
      setDemoteStatus(state, "error", message);
      setImportResult(state, "error", message);
      return;
    }
  }

  const patchResult = buildManualPatchForDemote(tag.tagId, aliasTargets);
  closeDemoteModal(state);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function buildManualPatchForDemote(tagId, aliasTargets) {
  const parts = String(tagId || "").split(":", 2);
  const aliasKey = parts.length === 2 ? parts[1] : "";
  const aliasValue = {
    description: "",
    tags: aliasTargets.slice()
  };

  const snippet = JSON.stringify(
    {
      tag_registry: {
        remove_tag_ids: [tagId]
      },
      tag_aliases: {
        set_aliases: {
          [aliasKey]: aliasValue
        },
        replace_target_refs: {
          from: tagId,
          to: aliasTargets
        }
      },
      tag_assignments: {
        replace_tag_refs: {
          from: tagId,
          to: aliasTargets
        }
      }
    },
    null,
    2
  );

  return {
    kind: "warn",
    message: `Patch mode: section snippets prepared for demoting "${tagId}".`,
    snippet
  };
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
  const status = normalize(raw.status || "active");
  const description = String(raw.description || "").trim();

  if (!tagId || tagId.indexOf(":") <= 0) {
    throw new Error(`Import tag ${idx} has invalid tag_id.`);
  }
  if (!STUDIO_GROUPS.includes(group)) {
    throw new Error(`Import tag ${idx} has invalid group.`);
  }
  if (!["active", "deprecated", "candidate"].includes(status)) {
    throw new Error(`Import tag ${idx} has invalid status.`);
  }

  const tagGroup = tagId.split(":", 1)[0];
  if (tagGroup !== group) {
    throw new Error(`Import tag ${idx} group must match tag_id prefix.`);
  }

  const [, slug = ""] = tagId.split(":", 2);

  return {
    tag_id: tagId,
    group,
    label: labelFromSlug(slug),
    status,
    description
  };
}

function buildManualPatchForCreateTag(tagRow) {
  const normalizedTagId = normalize(tagRow && tagRow.tag_id);
  const snippet = JSON.stringify(
    [
      {
        tag_id: normalizedTagId,
        group: normalize(tagRow && tagRow.group),
        label: labelFromTagId(normalizedTagId),
        status: normalize((tagRow && tagRow.status) || "active"),
        description: String((tagRow && tagRow.description) || "").trim(),
        updated_at_utc: utcTimestamp()
      }
    ],
    null,
    2
  );
  return {
    kind: "warn",
    message: `Patch mode: new tag row prepared for assets/studio/data/tag_registry.json tags[].`,
    snippet
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
      label: labelFromTagId(normalize(tag.tag_id)),
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
    newTags,
    null,
    2
  );

  return {
    kind: "warn",
    message: `Patch mode (${state.importMode}): ${importTags.length} imported; ${newTags.length} new tag rows prepared for assets/studio/data/tag_registry.json tags[].`,
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

function clearImportResult(state) {
  setImportResult(state, "", "");
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

function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function renderError(state, message) {
  state.mount.innerHTML = `<div class="tagStudioError">${escapeHtml(message)}</div>`;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function labelFromTagId(tagId) {
  const normalized = normalize(tagId);
  if (!normalized || !normalized.includes(":")) return "";
  const [, slug = ""] = normalized.split(":", 2);
  return labelFromSlug(slug);
}

function labelFromSlug(slug) {
  return normalize(slug);
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
