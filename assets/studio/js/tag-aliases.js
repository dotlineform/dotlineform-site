import {
  getStudioDataPath,
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const TAG_ID_RE = /^[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$/;
const ALIAS_RE = /^[a-z0-9][a-z0-9-]*$/;
const MAX_ALIAS_TAGS = 4;
const EDIT_TAG_MATCH_CAP = 12;
const HEALTH_ENDPOINT = "http://127.0.0.1:8787/health";
const IMPORT_ENDPOINT = "http://127.0.0.1:8787/import-tag-aliases";
const DELETE_ENDPOINT = "http://127.0.0.1:8787/delete-tag-alias";
const MUTATE_ALIAS_ENDPOINT = "http://127.0.0.1:8787/mutate-tag-alias";
const PROMOTE_ENDPOINT = "http://127.0.0.1:8787/promote-tag-alias";
const PROMOTE_PREVIEW_ENDPOINT = "http://127.0.0.1:8787/promote-tag-alias-preview";
const DEMOTE_ENDPOINT = "http://127.0.0.1:8787/demote-tag";
const DEMOTE_PREVIEW_ENDPOINT = "http://127.0.0.1:8787/demote-tag-preview";
let GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagAliasesPage);
} else {
  initTagAliasesPage();
}

async function initTagAliasesPage() {
  const mount = document.getElementById("tag-aliases");
  if (!mount) return;

  const config = await loadStudioConfig();
  STUDIO_GROUPS = getStudioGroups(config);
  GROUP_INFO_PAGE_PATH = getStudioRoute(config, "tag_groups");

  const state = {
    mount,
    config,
    aliases: [],
    registryById: new Map(),
    aliasesUpdatedAt: "",
    searchQuery: "",
    filterGroup: "all",
    sortKey: "alias",
    sortDir: "asc",
    importMode: "add",
    saveMode: "patch",
    selectedFile: null,
    patchSnippet: "",
    registryOptions: [],
    groupDescriptions: new Map(),
    editState: null,
    refs: null
  };

  renderShell(state);
  wireEvents(state);
  syncImportModeFromControl(state);

  try {
    await loadData(state);
    renderControls(state);
    renderList(state);
  } catch (error) {
    renderError(
      state,
      aliasesText(state.config, "load_failed_error", "Failed to load aliases from /assets/studio/data/tag_aliases.json.")
    );
    return;
  }

  void probeImportMode(state);
}

function renderShell(state) {
  const importFileLabel = aliasesText(state.config, "import_file_label", "import file");
  const importModeFieldLabel = aliasesText(state.config, "import_mode_label", "mode");
  const importModeOptionAdd = aliasesText(state.config, "import_mode_option_add", "add (no overwrite)");
  const importModeOptionMerge = aliasesText(state.config, "import_mode_option_merge", "add + overwrite");
  const importModeOptionReplace = aliasesText(state.config, "import_mode_option_replace", "replace entire aliases");
  const chooseFileLabel = aliasesText(state.config, "choose_file_button", "Choose file");
  const importButtonLabel = aliasesText(state.config, "import_button", "Import");
  const importModeLabel = buildAliasesImportModeText(state, "patch");
  const newAliasButtonLabel = aliasesText(state.config, "new_alias_button", "New alias");
  const searchLabel = aliasesText(state.config, "search_label", "Search aliases");
  const searchPlaceholder = aliasesText(state.config, "search_placeholder", "search");
  const patchModalTitle = aliasesText(state.config, "patch_modal_title", "Aliases Patch Preview");
  const patchModalLabel = aliasesText(state.config, "patch_modal_label", "Manual patch snippet");
  const patchModalCopy = aliasesText(state.config, "patch_modal_copy_button", "Copy");
  const patchModalClose = aliasesText(state.config, "patch_modal_close_button", "Close");
  const editModalTitle = aliasesText(state.config, "edit_modal_title", "Edit Alias");
  const editAliasLabel = aliasesText(state.config, "edit_alias_label", "alias");
  const editDescriptionLabel = aliasesText(state.config, "edit_description_label", "description");
  const editSearchLabel = aliasesText(state.config, "edit_search_label", "find tags");
  const editSearchPlaceholder = aliasesText(state.config, "edit_search_placeholder", "search tags");
  const editSaveButton = aliasesText(state.config, "edit_save_button", "Save");
  const editCancelButton = aliasesText(state.config, "edit_cancel_button", "Cancel");
  state.mount.innerHTML = `
    <section class="tagStudio__panel">
      <div class="tagRegistry__importBox">
        <div class="tagRegistry__importRow">
          <label class="tagRegistry__fileWrap">
            <span class="tagRegistry__importLabel">${escapeHtml(importFileLabel)}</span>
            <button type="button" class="tagStudio__button tagStudio__button--primary tagRegistry__chooseBtn" data-role="choose-file">${escapeHtml(chooseFileLabel)}</button>
            <input type="file" class="tagRegistry__fileInput" data-role="import-file" accept=".json,application/json" hidden>
          </label>
          <label class="tagRegistry__modeWrap">
            <span class="tagRegistry__importLabel">${escapeHtml(importModeFieldLabel)}</span>
            <select class="tagRegistry__modeSelect" data-role="import-mode">
              <option value="add">${escapeHtml(importModeOptionAdd)}</option>
              <option value="merge">${escapeHtml(importModeOptionMerge)}</option>
              <option value="replace">${escapeHtml(importModeOptionReplace)}</option>
            </select>
          </label>
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="import-btn">${escapeHtml(importButtonLabel)}</button>
          <span class="tagRegistry__saveMode" data-role="save-mode">${escapeHtml(importModeLabel)}</span>
          <button type="button" class="tagStudio__button tagStudio__button--primary tagAliases__newAliasBtn" data-role="open-new-alias">${escapeHtml(newAliasButtonLabel)}</button>
        </div>
        <p class="tagRegistry__selected" data-role="selected-file"></p>
        <p class="tagRegistry__result" data-role="import-result"></p>
      </div>

      <div class="tagAliases__controls">
        <div class="tagStudio__key tagRegistry__key" data-role="key"></div>
        <label class="tagRegistry__searchWrap">
          <span class="visually-hidden">${escapeHtml(searchLabel)}</span>
          <input
            type="text"
            class="tagStudio__input tagRegistry__searchInput"
            data-role="search"
            placeholder="${escapeHtml(searchPlaceholder)}"
            autocomplete="off"
          >
        </label>
      </div>

      <div data-role="list"></div>
    </section>

    <div class="tagStudioModal" data-role="patch-modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagAliasesPatchTitle">
        <h3 id="tagAliasesPatchTitle">${escapeHtml(patchModalTitle)}</h3>
        <p class="tagStudioModal__label">${escapeHtml(patchModalLabel)}</p>
        <pre class="tagStudioModal__pre" data-role="patch-snippet"></pre>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="copy-patch">${escapeHtml(patchModalCopy)}</button>
          <button type="button" class="tagStudio__button" data-role="close-modal">${escapeHtml(patchModalClose)}</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="edit-modal" hidden>
      <div class="tagStudioModal__backdrop"></div>
      <div class="tagStudioModal__dialog tagAliasesEdit__dialog" role="dialog" aria-modal="true" aria-labelledby="tagAliasesEditTitle">
        <h3 id="tagAliasesEditTitle" data-role="edit-modal-title">${escapeHtml(editModalTitle)}</h3>
        <div class="tagRegistryEdit__fields">
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">${escapeHtml(editAliasLabel)}</span>
            <input type="text" class="tagStudio__input" data-role="edit-alias-name" autocomplete="off">
          </label>
          <p class="tagAliasesEdit__warning" data-role="edit-alias-warning"></p>
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">${escapeHtml(editDescriptionLabel)}</span>
            <textarea class="tagStudio__input tagAliasesEdit__description" data-role="edit-alias-description" rows="2"></textarea>
          </label>
          <label class="tagRegistryEdit__field tagAliasesEdit__searchWrap">
            <span class="tagRegistryEdit__label">${escapeHtml(editSearchLabel)}</span>
            <input type="text" class="tagStudio__input" data-role="edit-tag-search" autocomplete="off" placeholder="${escapeHtml(editSearchPlaceholder)}">
            <div class="tagStudio__popup" data-role="edit-tag-popup-wrap" hidden>
              <div class="tagStudio__popupInner" data-role="edit-tag-popup"></div>
            </div>
          </label>
        </div>
        <div class="tagStudio__key tagAliasesEdit__key" data-role="edit-group-key"></div>
        <div class="tagStudio__chipList tagAliasesEdit__selectedTags" data-role="edit-tag-list"></div>
        <p class="tagRegistryEdit__status" data-role="edit-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="save-edit-alias" disabled>${escapeHtml(editSaveButton)}</button>
          <button type="button" class="tagStudio__button" data-role="close-edit-modal">${escapeHtml(editCancelButton)}</button>
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
    openNewAlias: state.mount.querySelector('[data-role="open-new-alias"]'),
    saveMode: state.mount.querySelector('[data-role="save-mode"]'),
    selectedFile: state.mount.querySelector('[data-role="selected-file"]'),
    importResult: state.mount.querySelector('[data-role="import-result"]'),
    list: state.mount.querySelector('[data-role="list"]'),
    patchModal: state.mount.querySelector('[data-role="patch-modal"]'),
    patchSnippet: state.mount.querySelector('[data-role="patch-snippet"]'),
    copyPatch: state.mount.querySelector('[data-role="copy-patch"]'),
    editModal: state.mount.querySelector('[data-role="edit-modal"]'),
    editModalTitle: state.mount.querySelector('[data-role="edit-modal-title"]'),
    editAliasName: state.mount.querySelector('[data-role="edit-alias-name"]'),
    editAliasWarning: state.mount.querySelector('[data-role="edit-alias-warning"]'),
    editAliasDescription: state.mount.querySelector('[data-role="edit-alias-description"]'),
    editTagSearch: state.mount.querySelector('[data-role="edit-tag-search"]'),
    editTagPopupWrap: state.mount.querySelector('[data-role="edit-tag-popup-wrap"]'),
    editTagPopup: state.mount.querySelector('[data-role="edit-tag-popup"]'),
    editGroupKey: state.mount.querySelector('[data-role="edit-group-key"]'),
    editTagList: state.mount.querySelector('[data-role="edit-tag-list"]'),
    editStatus: state.mount.querySelector('[data-role="edit-status"]'),
    saveEditAlias: state.mount.querySelector('[data-role="save-edit-alias"]')
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
    state.refs.selectedFile.textContent = state.selectedFile
      ? aliasesText(state.config, "selected_file_template", "Selected: {filename}", { filename: state.selectedFile.name })
      : "";
    if (state.selectedFile) clearImportResult(state);
  });

  state.refs.importMode.addEventListener("change", () => {
    syncImportModeFromControl(state);
  });

  state.refs.importButton.addEventListener("click", () => {
    void handleImport(state);
  });

  state.refs.openNewAlias.addEventListener("click", () => {
    openAliasCreateModal(state);
  });

  state.mount.addEventListener("click", (event) => {
    const demoteButton = event.target.closest("button[data-demote-tag-id]");
    if (demoteButton) {
      const tagId = normalize(demoteButton.getAttribute("data-demote-tag-id"));
      if (tagId) void handleTagDemoteFromAliases(state, tagId);
      return;
    }

    const promoteButton = event.target.closest("button[data-promote-alias]");
    if (promoteButton) {
      const alias = normalize(promoteButton.getAttribute("data-promote-alias"));
      if (alias) void handleAliasPromote(state, alias);
      return;
    }

    const deleteButton = event.target.closest("button[data-delete-alias]");
    if (deleteButton) {
      const alias = normalize(deleteButton.getAttribute("data-delete-alias"));
      if (alias) void handleAliasDelete(state, alias);
      return;
    }

    const editButton = event.target.closest("button[data-edit-alias]");
    if (editButton) {
      const alias = normalize(editButton.getAttribute("data-edit-alias"));
      if (alias) openAliasEditModal(state, alias);
      return;
    }

    const groupButton = event.target.closest("button[data-group]");
    if (groupButton) {
      const group = normalize(groupButton.getAttribute("data-group"));
      state.filterGroup = group && group !== "all" ? group : "all";
      renderControls(state);
      renderList(state);
      return;
    }

    const sortButton = event.target.closest("button[data-sort-key]");
    if (sortButton) {
      const key = normalize(sortButton.getAttribute("data-sort-key"));
      if (key !== "alias") return;
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDir = "asc";
      }
      renderList(state);
      return;
    }
  });

  state.refs.patchModal.addEventListener("click", (event) => {
    if (!event.target.closest('[data-role="close-modal"]')) return;
    closePatchModal(state);
  });

  state.refs.copyPatch.addEventListener("click", async () => {
    if (!state.patchSnippet) return;
    try {
      await navigator.clipboard.writeText(state.patchSnippet);
      setImportResult(state, "success", aliasesText(state.config, "patch_copy_success", "Patch snippet copied to clipboard."));
    } catch (error) {
      setImportResult(state, "error", aliasesText(state.config, "patch_copy_failed", "Copy failed. Select and copy the snippet manually."));
    }
  });

  state.refs.editModal.addEventListener("click", (event) => {
    if (event.target.closest('[data-role="close-edit-modal"]')) {
      closeAliasEditModal(state);
      return;
    }
    if (state.refs.editTagPopupWrap.hidden) return;
    if (!event.target.closest('[data-role="edit-tag-popup-wrap"]') && !event.target.closest('[data-role="edit-tag-search"]')) {
      hideEditTagPopup(state);
    }
  });

  state.refs.editAliasName.addEventListener("input", () => {
    updateAliasEditUi(state);
  });

  state.refs.editAliasDescription.addEventListener("input", () => {
    updateAliasEditUi(state);
  });

  state.refs.editTagSearch.addEventListener("input", () => {
    renderEditTagPopup(state);
  });

  state.refs.editTagSearch.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      hideEditTagPopup(state);
      state.refs.editTagSearch.blur();
    }
  });

  state.refs.editTagPopup.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-popup-tag-id]");
    if (!button) return;
    const tagId = normalize(button.getAttribute("data-popup-tag-id"));
    if (!tagId) return;
    addEditTag(state, tagId);
    state.refs.editTagSearch.value = "";
    hideEditTagPopup(state);
    updateAliasEditUi(state);
  });

  state.refs.editTagList.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-remove-edit-tag]");
    if (!button || !state.editState) return;
    const tagId = normalize(button.getAttribute("data-remove-edit-tag"));
    if (!tagId) return;
    state.editState.tags = state.editState.tags.filter((item) => item !== tagId);
    updateAliasEditUi(state);
  });

  state.refs.saveEditAlias.addEventListener("click", () => {
    void saveAliasEdit(state);
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

async function loadData(state) {
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
  state.registryById = buildRegistryLookup(registryData);
  state.registryOptions = buildRegistryOptions(state.registryById);
  state.groupDescriptions = buildGroupDescriptionMap(groupsData);
  state.aliasesUpdatedAt = normalizeTimestamp(aliasesData && aliasesData.updated_at_utc);
  state.aliases = normalizeAliases(aliasesData, state.aliasesUpdatedAt, state.registryById);
}

function buildRegistryLookup(data) {
  const map = new Map();
  const tags = Array.isArray(data && data.tags) ? data.tags : [];
  for (const raw of tags) {
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id);
    const group = normalize(raw.group);
    const label = normalize(raw.label);
    if (!tagId || !STUDIO_GROUPS.includes(group) || !label) continue;
    map.set(tagId, { group, label });
  }
  return map;
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

function normalizeAliases(data, fallbackUpdatedAt, registryById) {
  const aliasesObj = data && typeof data.aliases === "object" && data.aliases ? data.aliases : {};
  const entries = [];

  for (const [rawAlias, rawValue] of Object.entries(aliasesObj)) {
    const alias = normalize(rawAlias);
    if (!alias) continue;
    let normalizedValue = null;
    try {
      normalizedValue = normalizeAliasValue(rawValue);
    } catch (error) {
      continue;
    }

    const targets = normalizedValue.targets;
    const resolvedTargets = targets.map((tagId) => {
      const info = registryById.get(tagId);
      return {
        tagId,
        group: info ? info.group : "",
        label: info ? info.label : tagId,
        known: Boolean(info)
      };
    });
    const groups = Array.from(new Set(resolvedTargets.filter((item) => item.known).map((item) => item.group)));
    const hasUnknown = resolvedTargets.some((item) => !item.known);
    const updatedAtUtc = fallbackUpdatedAt;

    entries.push({
      alias,
      value: normalizedValue.value,
      description: normalizedValue.description,
      targets,
      resolvedTargets,
      groups,
      hasUnknown,
      updatedAtUtc,
      updatedAtMs: toTimestampMs(updatedAtUtc)
    });
  }
  return entries;
}

function normalizeAliasValue(rawValue) {
  if (rawValue && typeof rawValue === "object" && !Array.isArray(rawValue)) {
    const description = String(rawValue.description || "").trim();
    const tags = normalizeAliasTagsArray(rawValue.tags);
    return {
      description,
      value: { description, tags },
      targets: tags.slice()
    };
  }

  if (typeof rawValue === "string") {
    const value = normalize(rawValue);
    if (!TAG_ID_RE.test(value)) {
      throw new Error(aliasesText(null, "alias_value_invalid_tag_id", "Invalid alias tag_id value."));
    }
    return {
      description: "",
      value: { description: "", tags: [value] },
      targets: [value]
    };
  }
  const out = normalizeAliasTagsArray(rawValue);
  return {
    description: "",
    value: { description: "", tags: out },
    targets: out.slice()
  };
}

function normalizeAliasTagsArray(rawValue) {
  if (!Array.isArray(rawValue)) {
    throw new Error(aliasesText(null, "alias_tags_array_required", "Alias tags must be an array."));
  }
  if (!rawValue.length) {
    throw new Error(aliasesText(null, "alias_tags_required", "Alias tags must include at least one tag_id."));
  }
  if (rawValue.length > MAX_ALIAS_TAGS) {
    throw new Error(aliasesText(null, "alias_tags_max", "Alias tags may include at most {max_tags} tags.", { max_tags: MAX_ALIAS_TAGS }));
  }

  const out = [];
  const seen = new Set();
  const seenGroups = new Set();
  for (const raw of rawValue) {
    const value = normalize(raw);
    if (!value || !TAG_ID_RE.test(value)) {
      throw new Error(aliasesText(null, "alias_tag_array_invalid_value", "Invalid alias tag_id array value."));
    }
    if (seen.has(value)) continue;
    const group = value.split(":", 1)[0];
    if (seenGroups.has(group)) {
      throw new Error(aliasesText(null, "alias_tags_one_per_group", "Alias tags may include only one tag per group: {group}", { group }));
    }
    seen.add(value);
    seenGroups.add(group);
    out.push(value);
  }
  if (!out.length) {
    throw new Error(aliasesText(null, "alias_tags_required", "Alias tags must include at least one tag_id."));
  }
  return out;
}

function buildRegistryOptions(registryById) {
  const out = [];
  for (const [tagId, info] of registryById.entries()) {
    if (!info || !STUDIO_GROUPS.includes(info.group)) continue;
    out.push({
      tagId,
      group: info.group,
      label: normalize(info.label) || tagId.split(":")[1] || tagId
    });
  }
  out.sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" }));
  return out;
}

function renderControls(state) {
  const counts = countAliasesByGroup(state.aliases);
  const totalCount = state.aliases.length;
  const allActiveClass = state.filterGroup === "all" ? " is-active" : "";
  const allTagsLabel = aliasesText(state.config, "all_tags_filter", "All tags [{count}]", { count: totalCount });
  const groupButtons = STUDIO_GROUPS.map((group) => {
    const activeClass = state.filterGroup === group ? " is-active" : "";
    const count = Number(counts[group] || 0);
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
    <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">${escapeHtml(allTagsLabel)}</button>
    ${groupButtons}
    ${renderGroupInfoControl(state, "aliases")}
  `;
}

function countAliasesByGroup(aliases) {
  const counts = { subject: 0, domain: 0, form: 0, theme: 0 };
  for (const entry of aliases || []) {
    for (const group of entry.groups || []) {
      if (STUDIO_GROUPS.includes(group)) {
        counts[group] += 1;
      }
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
  const title = aliasesText(state.config, "group_info_title", "Open group descriptions in a new tab");
  const ariaLabel = aliasesText(state.config, "group_info_aria_label", "Open group descriptions in a new tab");
  return `
    <a
      class="tagStudio__keyPill tagStudio__keyInfoBtn"
      href="${GROUP_INFO_PAGE_PATH}"
      target="_blank"
      rel="noopener noreferrer"
      title="${escapeHtml(title)}"
      aria-label="${escapeHtml(ariaLabel)}"
    >
      <em>i</em>
    </a>
  `;
}

function renderList(state) {
  const visible = getVisibleAliases(state);
  const aliasHeading = aliasesText(state.config, "table_heading_alias", "alias");

  const headerHtml = `
    <div class="tagAliases__head">
      <button type="button" class="tagRegistry__sortBtn${sortBtnClass(state, "alias")}" data-sort-key="alias">
        ${escapeHtml(aliasHeading)}${sortIndicator(state, "alias")}
      </button>
      <span class="tagAliases__headLabel">${escapeHtml(aliasesText(state.config, "group_tags_heading", "group tags"))}</span>
    </div>
  `;

  if (!visible.length) {
    state.refs.list.innerHTML = `${headerHtml}<p class="tagStudio__empty">${escapeHtml(aliasesText(state.config, "empty_state", "none"))}</p>`;
    return;
  }

  state.refs.list.innerHTML = `
    ${headerHtml}
    <ul class="tagAliases__rows">
      ${visible.map((entry) => {
        const sortedTargets = entry.resolvedTargets.slice().sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" }));
        return `
        <li class="tagAliases__row">
          <div class="tagAliases__aliasCol">
            <span class="tagStudio__chip ${escapeHtml(getAliasClass(entry))}">
              <button
                type="button"
                class="tagAliases__aliasBtn"
                data-edit-alias="${escapeHtml(entry.alias)}"
                title="${escapeHtml(aliasesText(state.config, "alias_edit_title", "Edit alias {alias}", { alias: entry.alias }))}"
                aria-label="${escapeHtml(aliasesText(state.config, "alias_edit_aria_label", "Edit alias {alias}", { alias: entry.alias }))}"
              >
                ${escapeHtml(entry.alias)}
              </button>
              <button
                type="button"
                class="tagStudio__chipRemove"
                data-promote-alias="${escapeHtml(entry.alias)}"
                aria-label="${escapeHtml(aliasesText(state.config, "alias_promote_aria_label", "Promote alias {alias}", { alias: entry.alias }))}"
                title="${escapeHtml(aliasesText(state.config, "alias_promote_title", "Promote alias to canonical tag"))}"
              >
                →
              </button>
              <button
                type="button"
                class="tagStudio__chipRemove"
                data-delete-alias="${escapeHtml(entry.alias)}"
                aria-label="${escapeHtml(aliasesText(state.config, "alias_delete_aria_label", "Delete alias {alias}", { alias: entry.alias }))}"
                title="${escapeHtml(aliasesText(state.config, "alias_delete_title", "Delete alias"))}"
              >
                ×
              </button>
            </span>
          </div>
          <div class="tagAliases__tagsCol">
            <div class="tagAliases__tagList">
              ${sortedTargets.map((target) => `
                <span class="tagStudio__chip ${escapeHtml(target.known ? `tagStudio__chip--${target.group}` : "tagStudio__chip--warning")}" title="${escapeHtml(target.tagId)}">
                  ${escapeHtml(String(target.label || "").toLowerCase())}
                  ${target.known ? `
                    <button
                      type="button"
                      class="tagStudio__chipRemove"
                      data-demote-tag-id="${escapeHtml(target.tagId)}"
                      title="${escapeHtml(aliasesText(state.config, "tag_demote_title", "Demote canonical tag to alias"))}"
                      aria-label="${escapeHtml(aliasesText(state.config, "tag_demote_aria_label", "Demote {tag_id}", { tag_id: target.tagId }))}"
                    >
                      ←
                    </button>
                  ` : ""}
                </span>
              `).join("")}
            </div>
          </div>
        </li>
      `;
      }).join("")}
    </ul>
  `;
}

function getAliasClass(entry) {
  if (!entry || entry.hasUnknown || !entry.groups.length || entry.groups.length > 1) {
    return "tagStudio__chip--warning";
  }
  const group = entry.groups[0];
  return STUDIO_GROUPS.includes(group) ? `tagStudio__chip--${group}` : "tagStudio__chip--warning";
}

function getVisibleAliases(state) {
  const filtered = state.aliases.filter((entry) => {
    const searchMatch = !state.searchQuery || normalize(entry.alias).startsWith(state.searchQuery);
    if (!searchMatch) return false;
    if (state.filterGroup === "all") return true;
    return Array.isArray(entry.groups) && entry.groups.includes(state.filterGroup);
  });

  const direction = state.sortDir === "desc" ? -1 : 1;
  filtered.sort((a, b) => direction * compareAliases(a, b, state.sortKey));
  return filtered;
}

function compareAliases(a, b, sortKey) {
  return a.alias.localeCompare(b.alias, undefined, { sensitivity: "base" });
}

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "asc" ? " ↑" : " ↓";
}

function sortBtnClass(state, key) {
  return state.sortKey === key ? " is-active" : "";
}

async function probeImportMode(state) {
  const ok = await pingHealthEndpoint();
  state.saveMode = ok ? "post" : "patch";
  renderImportMode(state);
}

function renderImportMode(state) {
  state.refs.saveMode.textContent = buildAliasesImportModeText(state, state.saveMode);
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

async function handleImport(state) {
  if (!state.selectedFile) {
    setImportResult(state, "error", aliasesText(state.config, "choose_import_file_error", "Choose an import file first."));
    return;
  }

  let importAliases = null;
  try {
    importAliases = await readImportAliasesFromFile(state.selectedFile);
  } catch (error) {
    setImportResult(state, "error", String(error.message || aliasesText(state.config, "invalid_import_file", "Invalid import file.")));
    return;
  }

  if (state.saveMode === "post") {
    try {
      const response = await postJson(IMPORT_ENDPOINT, {
        mode: state.importMode,
        import_aliases: importAliases,
        import_filename: state.selectedFile ? String(state.selectedFile.name || "") : "",
        client_time_utc: utcTimestamp()
      });
      setImportResult(state, "success", buildImportSummary(response));
      await loadData(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderImportMode(state);
      setImportResult(
        state,
        "error",
        aliasesText(
          state.config,
          "server_import_failed",
          "Server import failed; switched to patch mode. {message}",
          { message: String(error.message || "").trim() }
        ).trim()
      );
    }
  }

  const patchResult = buildManualPatchForNewAliases(state, importAliases);
  setImportResult(state, patchResult.kind, patchResult.message);
  if (patchResult.snippet) {
    openPatchModal(state, patchResult.snippet);
  }
}

async function handleAliasDelete(state, alias) {
  const aliasKey = normalize(alias);
  if (!aliasKey) return;

  const ok = window.confirm(
    aliasesText(state.config, "delete_confirm_template", "Delete alias \"{alias_key}\"?", { alias_key: aliasKey })
  );
  if (!ok) {
    clearImportResult(state);
    return;
  }

  if (state.saveMode === "post") {
    try {
      const response = await postJson(DELETE_ENDPOINT, {
        alias: aliasKey,
        client_time_utc: utcTimestamp()
      });
      const summary = String(response.summary_text || "").trim() || aliasesText(
        state.config,
        "delete_success_summary",
        "deleted alias {alias_key}",
        { alias_key: aliasKey }
      );
      setImportResult(state, "success", summary);
      await loadData(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderImportMode(state);
      setImportResult(
        state,
        "error",
        aliasesText(
          state.config,
          "server_delete_failed",
          "Server delete failed; switched to patch mode. {message}",
          { message: String(error.message || "").trim() }
        ).trim()
      );
    }
  }

  const patchResult = buildManualPatchForAliasDelete(aliasKey);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function findAliasEntry(state, aliasKey) {
  const normalized = normalize(aliasKey);
  return state.aliases.find((entry) => normalize(entry.alias) === normalized) || null;
}

function isCreateAliasFlow(state) {
  return Boolean(state.editState && !normalize(state.editState.originalAlias));
}

function setAliasEditModalMode(state, mode) {
  const normalizedMode = mode === "new" ? "new" : "edit";
  state.refs.editModalTitle.textContent = normalizedMode === "new"
    ? aliasesText(state.config, "new_modal_title", "New Alias")
    : aliasesText(state.config, "edit_modal_title", "Edit Alias");
  state.refs.saveEditAlias.textContent = normalizedMode === "new"
    ? aliasesText(state.config, "edit_create_button", "Create")
    : aliasesText(state.config, "edit_save_button", "Save");
}

function openAliasEditModal(state, aliasKey) {
  clearImportResult(state);
  const entry = findAliasEntry(state, aliasKey);
  if (!entry) {
    setImportResult(state, "error", aliasesText(state.config, "alias_not_found", "Alias not found: {alias_key}", { alias_key: aliasKey }));
    return;
  }

  state.editState = {
    originalAlias: entry.alias,
    originalDescription: String(entry.description || "").trim(),
    originalTags: Array.isArray(entry.targets) ? entry.targets.slice() : [],
    tags: Array.isArray(entry.targets) ? entry.targets.slice() : []
  };

  state.refs.editAliasName.value = entry.alias;
  state.refs.editAliasDescription.value = String(entry.description || "").trim();
  state.refs.editTagSearch.value = "";
  hideEditTagPopup(state);
  setAliasEditModalMode(state, "edit");
  renderEditGroupKey(state);
  updateAliasEditUi(state);
  state.refs.editModal.hidden = false;
}

function openAliasCreateModal(state) {
  clearImportResult(state);
  state.editState = {
    originalAlias: "",
    originalDescription: "",
    originalTags: [],
    tags: []
  };
  state.refs.editAliasName.value = "";
  state.refs.editAliasDescription.value = "";
  state.refs.editTagSearch.value = "";
  hideEditTagPopup(state);
  setAliasEditModalMode(state, "new");
  renderEditGroupKey(state);
  updateAliasEditUi(state);
  state.refs.editModal.hidden = false;
  state.refs.editAliasName.focus();
}

function closeAliasEditModal(state) {
  state.editState = null;
  state.refs.editModal.hidden = true;
  state.refs.editAliasName.value = "";
  state.refs.editAliasDescription.value = "";
  state.refs.editTagSearch.value = "";
  setAliasEditModalMode(state, "edit");
  state.refs.editAliasWarning.textContent = "";
  state.refs.editStatus.textContent = "";
  state.refs.saveEditAlias.disabled = true;
  state.refs.editTagList.innerHTML = "";
  hideEditTagPopup(state);
}

function renderEditGroupKey(state) {
  if (!state.editState) {
    state.refs.editGroupKey.innerHTML = "";
    return;
  }
  const selected = new Set((state.editState.tags || []).map((tagId) => normalize(tagId).split(":", 1)[0]));
  state.refs.editGroupKey.innerHTML = STUDIO_GROUPS.map((group) => {
    const activeClass = selected.has(group) ? " is-active" : "";
    const titleAttr = groupTitleAttr(state, group);
    return `<span class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)}${activeClass}" ${titleAttr}>${escapeHtml(group)}</span>`;
  }).join("") + renderGroupInfoControl(state, "edit");
}

function renderEditTagList(state) {
  if (!state.editState) {
    state.refs.editTagList.innerHTML = "";
    return;
  }
  const rows = state.editState.tags.map((tagId) => {
    const info = state.registryById.get(tagId);
    const group = info && STUDIO_GROUPS.includes(info.group) ? info.group : "warning";
    const label = info ? info.label : tagId;
    return `
      <span class="tagStudio__chip tagStudio__chip--${escapeHtml(group)}" title="${escapeHtml(tagId)}">
        ${escapeHtml(label)}
        <button
          type="button"
          class="tagStudio__chipRemove"
          data-remove-edit-tag="${escapeHtml(tagId)}"
          aria-label="${escapeHtml(aliasesText(state.config, "remove_target_tag_aria_label", "Remove {tag_id}", { tag_id: tagId }))}"
        >
          x
        </button>
      </span>
    `;
  }).join("");

  state.refs.editTagList.innerHTML = rows || `<span class="tagStudio__empty">${escapeHtml(aliasesText(state.config, "empty_state", "none"))}</span>`;
}

function getAliasEditValidation(state) {
  const edit = state.editState;
  if (!edit) return { valid: false, changed: false, alias: "", tags: [], description: "", warning: "" };

  const alias = normalize(state.refs.editAliasName.value);
  const description = String(state.refs.editAliasDescription.value || "").trim();
  const tags = Array.isArray(edit.tags) ? edit.tags.slice() : [];

  let warning = "";
  if (!alias) {
    warning = aliasesText(state.config, "alias_required", "Alias is required.");
  } else if (!ALIAS_RE.test(alias)) {
    warning = aliasesText(state.config, "alias_invalid", "Alias must be lowercase letters, numbers, or hyphens.");
  } else {
    const conflict = state.aliases.some((entry) => entry.alias !== edit.originalAlias && entry.alias === alias);
    if (conflict) warning = aliasesText(state.config, "alias_exists_warning", "Alias already exists.");
  }

  let tagsWarning = "";
  if (!tags.length) {
    tagsWarning = aliasesText(state.config, "select_one_tag_warning", "Select at least one tag.");
  } else if (tags.length > MAX_ALIAS_TAGS) {
    tagsWarning = aliasesText(state.config, "max_tags_warning", "Select up to {max_tags} tags.", { max_tags: MAX_ALIAS_TAGS });
  } else {
    const seenGroups = new Set();
    for (const tagId of tags) {
      if (!state.registryById.has(tagId)) {
        tagsWarning = aliasesText(state.config, "unknown_tag_selected", "Unknown tag selected: {tag_id}", { tag_id: tagId });
        break;
      }
      const group = tagId.split(":", 1)[0];
      if (seenGroups.has(group)) {
        tagsWarning = aliasesText(state.config, "one_tag_per_group_warning", "Only one tag per group is allowed ({group}).", { group });
        break;
      }
      seenGroups.add(group);
    }
  }

  const valid = !warning && !tagsWarning;
  const changed = (
    alias !== edit.originalAlias ||
    description !== edit.originalDescription ||
    !sameStringArray(tags, edit.originalTags)
  );

  return {
    valid,
    changed,
    alias,
    tags,
    description,
    warning,
    tagsWarning
  };
}

function setAliasEditStatus(state, kind, message) {
  state.refs.editStatus.textContent = message || "";
  state.refs.editStatus.className = "tagRegistryEdit__status";
  if (kind) state.refs.editStatus.classList.add(`is-${kind}`);
}

function updateAliasEditUi(state) {
  if (!state.editState) return;
  renderEditGroupKey(state);
  renderEditTagList(state);
  const validation = getAliasEditValidation(state);
  state.refs.editAliasName.value = normalize(state.refs.editAliasName.value);
  state.refs.editAliasWarning.textContent = validation.warning || "";
  state.refs.saveEditAlias.disabled = !(validation.valid && validation.changed);
  if (validation.tagsWarning) {
    setAliasEditStatus(state, "error", validation.tagsWarning);
  } else if (!validation.changed && !isCreateAliasFlow(state)) {
    setAliasEditStatus(state, "", aliasesText(state.config, "edit_no_changes", "No changes."));
  } else if (!validation.warning) {
    setAliasEditStatus(state, "", "");
  }
}

function getEditTagMatches(state, query) {
  const normalizedQuery = normalize(query);
  if (!normalizedQuery) return { matches: [], truncated: false };
  const selected = new Set((state.editState && state.editState.tags) || []);
  const allMatches = state.registryOptions
    .filter((item) => {
      if (selected.has(item.tagId)) return false;
      const slug = item.tagId.split(":", 2)[1] || "";
      return (
        normalize(item.label).startsWith(normalizedQuery) ||
        normalize(slug).startsWith(normalizedQuery)
      );
    });
  return {
    matches: allMatches.slice(0, EDIT_TAG_MATCH_CAP),
    truncated: allMatches.length > EDIT_TAG_MATCH_CAP
  };
}

function renderEditTagPopup(state) {
  if (!state.editState) return;
  const query = state.refs.editTagSearch.value;
  const result = getEditTagMatches(state, query);
  const matches = result.matches;
  if (!matches.length) {
    hideEditTagPopup(state);
    return;
  }
  const chips = matches.map((item) => `
    <button
      type="button"
      class="tagStudio__popupPill tagStudio__chip--${escapeHtml(item.group)}"
      data-popup-tag-id="${escapeHtml(item.tagId)}"
      title="${escapeHtml(item.tagId)}"
    >
      ${escapeHtml(item.label)}
    </button>
  `);
  if (result.truncated) {
    chips.push(`<span class="tagStudio__popupPill tagAliasesEdit__popupMore" title="${escapeHtml(aliasesText(state.config, "popup_more_title", "More matches available"))}">…</span>`);
  }
  state.refs.editTagPopup.innerHTML = chips.join("");
  state.refs.editTagPopupWrap.hidden = false;
}

function hideEditTagPopup(state) {
  state.refs.editTagPopupWrap.hidden = true;
  state.refs.editTagPopup.innerHTML = "";
}

function addEditTag(state, tagId) {
  if (!state.editState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId || !state.registryById.has(normalizedTagId)) return;
  if (state.editState.tags.includes(normalizedTagId)) return;
  if (state.editState.tags.length >= MAX_ALIAS_TAGS) {
    setAliasEditStatus(state, "error", aliasesText(state.config, "max_tags_warning", "Select up to {max_tags} tags.", { max_tags: MAX_ALIAS_TAGS }));
    return;
  }

  const nextGroup = normalizedTagId.split(":", 1)[0];
  const groupConflict = state.editState.tags.some((item) => item.split(":", 1)[0] === nextGroup);
  if (groupConflict) {
    setAliasEditStatus(state, "error", aliasesText(state.config, "one_tag_per_group_warning", "Only one tag per group is allowed ({group}).", { group: nextGroup }));
    return;
  }

  state.editState.tags.push(normalizedTagId);
}

async function saveAliasEdit(state) {
  if (!state.editState) return;
  const validation = getAliasEditValidation(state);
  if (!validation.valid || !validation.changed) return;
  const isCreate = isCreateAliasFlow(state);

  if (isCreate) {
    if (state.saveMode === "post") {
      try {
        const response = await postJson(IMPORT_ENDPOINT, {
          mode: "add",
          import_aliases: {
            aliases: {
              [validation.alias]: {
                description: validation.description,
                tags: validation.tags
              }
            }
          },
          import_filename: "",
          client_time_utc: utcTimestamp()
        });
        setImportResult(state, "success", buildImportSummary(response));
        await loadData(state);
        renderControls(state);
        renderList(state);
        closeAliasEditModal(state);
        return;
      } catch (error) {
        state.saveMode = "patch";
        renderImportMode(state);
        setAliasEditStatus(
          state,
          "error",
          aliasesText(
            state.config,
            "server_create_failed",
            "Server create failed; switched to patch mode. {message}",
            { message: String(error.message || "").trim() }
          ).trim()
        );
      }
    }

    const patchResult = buildManualPatchForAliasCreate(
      validation.alias,
      validation.description,
      validation.tags
    );
    closeAliasEditModal(state);
    openPatchModal(state, patchResult.snippet);
    return;
  }

  const payload = {
    alias: state.editState.originalAlias,
    new_alias: validation.alias,
    description: validation.description,
    tags: validation.tags,
    client_time_utc: utcTimestamp()
  };

  if (state.saveMode === "post") {
    try {
      await postJson(MUTATE_ALIAS_ENDPOINT, payload);
      await loadData(state);
      renderControls(state);
      renderList(state);
      closeAliasEditModal(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderImportMode(state);
      setAliasEditStatus(
        state,
        "error",
        aliasesText(
          state.config,
          "server_save_failed",
          "Server save failed; switched to patch mode. {message}",
          { message: String(error.message || "").trim() }
        ).trim()
      );
    }
  }

  const patchResult = buildManualPatchForAliasEdit(
    state.editState.originalAlias,
    validation.alias,
    validation.description,
    validation.tags
  );
  closeAliasEditModal(state);
  openPatchModal(state, patchResult.snippet);
}

function sameStringArray(a, b) {
  const left = Array.isArray(a) ? a.map((item) => normalize(item)).slice().sort() : [];
  const right = Array.isArray(b) ? b.map((item) => normalize(item)).slice().sort() : [];
  if (left.length !== right.length) return false;
  for (let idx = 0; idx < left.length; idx += 1) {
    if (left[idx] !== right[idx]) return false;
  }
  return true;
}

function promptPromotionGroup(state, entry) {
  const suggested = entry && Array.isArray(entry.groups) && entry.groups.length ? entry.groups[0] : "subject";
  const raw = window.prompt(
    aliasesText(state.config, "promotion_group_prompt", "Promote alias: choose group (subject/domain/form/theme)"),
    suggested || "subject"
  );
  if (raw === null) return "";
  return normalize(raw);
}

async function handleAliasPromote(state, alias) {
  const aliasKey = normalize(alias);
  if (!aliasKey) return;

  const entry = findAliasEntry(state, aliasKey);
  if (!entry) {
    setImportResult(state, "error", aliasesText(state.config, "alias_not_found", "Alias not found: {alias_key}", { alias_key: aliasKey }));
    return;
  }

  const group = promptPromotionGroup(state, entry);
  if (!group) {
    clearImportResult(state);
    return;
  }
  if (!STUDIO_GROUPS.includes(group)) {
    setImportResult(state, "error", aliasesText(state.config, "promotion_group_invalid", "Promotion group must be one of: subject, domain, form, theme."));
    return;
  }

  const payload = {
    alias: aliasKey,
    group,
    client_time_utc: utcTimestamp()
  };

  if (state.saveMode === "post") {
    let preview = null;
    try {
      preview = await postJson(PROMOTE_PREVIEW_ENDPOINT, payload);
    } catch (error) {
      setImportResult(state, "error", String(error.message || aliasesText(state.config, "promotion_preview_failed", "Promotion preview failed.")));
      return;
    }

    const previewSummary = String(preview.summary_text || "").trim() || `alias ${aliasKey} -> ${group}:${aliasKey}`;
    const ok = window.confirm(
      aliasesText(
        state.config,
        "promotion_confirm_template",
        "Promote alias \"{alias_key}\" to canonical tag \"{new_tag_id}\"?\n\nImpact:\n{preview_summary}",
        {
          alias_key: aliasKey,
          new_tag_id: `${group}:${aliasKey}`,
          preview_summary: previewSummary
        }
      )
    );
    if (!ok) {
      clearImportResult(state);
      return;
    }

    try {
      const response = await postJson(PROMOTE_ENDPOINT, payload);
      setImportResult(state, "success", String(response.summary_text || aliasesText(state.config, "promoted_success", "Promoted.")));
      await loadData(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      setImportResult(state, "error", String(error.message || aliasesText(state.config, "promotion_failed", "Promotion failed.")));
      return;
    }
  }

  const patchResult = buildManualPatchForAliasPromote(state, aliasKey, group);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function parseTagIdCsv(input) {
  const values = String(input || "")
    .split(",")
    .map((item) => normalize(item))
    .filter((item) => Boolean(item));
  const out = [];
  const seen = new Set();
  for (const value of values) {
    if (!TAG_ID_RE.test(value)) {
      throw new Error(aliasesText(null, "target_tag_invalid", "Invalid tag_id: {value}", { value }));
    }
    if (seen.has(value)) continue;
    seen.add(value);
    out.push(value);
  }
  if (!out.length) {
    throw new Error(aliasesText(null, "target_tag_required", "At least one canonical target tag_id is required."));
  }
  if (out.length > MAX_ALIAS_TAGS) {
    throw new Error(aliasesText(null, "target_tags_max", "At most {max_tags} target tags are allowed.", { max_tags: MAX_ALIAS_TAGS }));
  }
  const seenGroups = new Set();
  for (const value of out) {
    const group = value.split(":", 1)[0];
    if (seenGroups.has(group)) {
      throw new Error(aliasesText(null, "target_tags_one_per_group", "Only one target tag per group is allowed ({group}).", { group }));
    }
    seenGroups.add(group);
  }
  return out;
}

function promptDemotionTargets(state, tagId) {
  const promptText = [
    aliasesText(state.config, "demotion_prompt_line_1", "Demote {tag_id} to alias.", { tag_id: tagId }),
    aliasesText(state.config, "demotion_prompt_line_2", "Enter canonical target tag_ids (comma-separated)."),
    aliasesText(state.config, "demotion_prompt_line_3", "Example: form:line,theme:emergence")
  ].join("\n");
  return window.prompt(promptText, "");
}

async function handleTagDemoteFromAliases(state, tagId) {
  const canonicalTagId = normalize(tagId);
  if (!canonicalTagId) return;

  const input = promptDemotionTargets(state, canonicalTagId);
  if (input === null) return;

  let aliasTargets = [];
  try {
    aliasTargets = parseTagIdCsv(input);
  } catch (error) {
    setImportResult(state, "error", String(error.message || aliasesText(state.config, "invalid_target_tags", "Invalid target tags.")));
    return;
  }
  if (aliasTargets.includes(canonicalTagId)) {
    setImportResult(state, "error", aliasesText(state.config, "demotion_target_self", "Target list must not include the demoted tag."));
    return;
  }

  const payload = {
    tag_id: canonicalTagId,
    alias_targets: aliasTargets,
    client_time_utc: utcTimestamp()
  };

  if (state.saveMode === "post") {
    let preview = null;
    try {
      preview = await postJson(DEMOTE_PREVIEW_ENDPOINT, payload);
    } catch (error) {
      setImportResult(state, "error", String(error.message || aliasesText(state.config, "demotion_preview_failed", "Demotion preview failed.")));
      return;
    }

    const previewSummary = String(preview.summary_text || "").trim() || `demote ${canonicalTagId}`;
    const aliasKey = canonicalTagId.split(":")[1] || canonicalTagId;
    const ok = window.confirm(
      aliasesText(
        state.config,
        "demotion_confirm_template",
        "Demote \"{tag_id}\" to alias \"{alias_key}\"?\n\nTargets: {targets}\n\nImpact:\n{preview_summary}",
        {
          tag_id: canonicalTagId,
          alias_key: aliasKey,
          targets: aliasTargets.join(", "),
          preview_summary: previewSummary
        }
      )
    );
    if (!ok) {
      clearImportResult(state);
      return;
    }

    try {
      const response = await postJson(DEMOTE_ENDPOINT, payload);
      setImportResult(state, "success", String(response.summary_text || aliasesText(state.config, "demoted_success", "Demoted.")));
      await loadData(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      setImportResult(state, "error", String(error.message || aliasesText(state.config, "demotion_failed", "Demotion failed.")));
      return;
    }
  }

  const patchResult = buildManualPatchForDemote(canonicalTagId, aliasTargets);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function buildManualPatchForNewAliases(state, importAliases) {
  const importRows = normalizeImportAliasRows(importAliases.aliases || {});
  const existing = new Set(state.aliases.map((entry) => entry.alias));
  const aliasesToAdd = {};
  let newCount = 0;

  for (const row of importRows) {
    if (existing.has(row.alias)) continue;
    aliasesToAdd[row.alias] = row.value;
    newCount += 1;
  }

  if (newCount === 0) {
    return {
      kind: "warn",
      message: aliasesText(
        state.config,
        "patch_import_none_message",
        "Patch mode ({import_mode}): {imported_count} imported; 0 new aliases to add.",
        {
          import_mode: state.importMode,
          imported_count: importRows.length
        }
      ),
      snippet: ""
    };
  }

  const snippet = JSON.stringify(
    aliasesToAdd,
    null,
    2
  );

  return {
    kind: "warn",
    message: aliasesText(
      state.config,
      "patch_import_message",
      "Patch mode ({import_mode}): {imported_count} imported; {new_count} alias rows prepared for assets/studio/data/tag_aliases.json aliases object.",
      {
        import_mode: state.importMode,
        imported_count: importRows.length,
        new_count: newCount
      }
    ),
    snippet
  };
}

function buildImportSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  const mode = normalize(response.mode || "");
  return [
    `mode ${mode || "unknown"}`,
    `Imported ${Number(response.imported_total || 0)} aliases`,
    `added ${Number(response.added || 0)}`,
    `overwritten ${Number(response.overwritten || 0)}`,
    `unchanged ${Number(response.unchanged || 0)}`,
    `removed ${Number(response.removed || 0)}`,
    `final ${Number(response.final_total || 0)}`
  ].join("; ");
}

function buildManualPatchForAliasPromote(state, aliasKey, group) {
  const newTagId = `${group}:${aliasKey}`;
  const canonicalExists = state.registryById.has(newTagId);
  const sectionSnippet = {
    tag_registry: {},
    tag_aliases: {
      remove_alias_keys: [aliasKey]
    }
  };

  if (!canonicalExists) {
    sectionSnippet.tag_registry = {
      tags_append: [
        {
          tag_id: newTagId,
          group,
          label: aliasKey,
          status: "active",
          description: "",
          updated_at_utc: utcTimestamp()
        }
      ]
    };
  }

  const snippet = JSON.stringify(sectionSnippet, null, 2);

  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_promote_message",
      "Patch mode: section snippets prepared for promoting \"{alias_key}\".",
      { alias_key: aliasKey }
    ),
    snippet
  };
}

function buildManualPatchForAliasDelete(aliasKey) {
  const snippet = JSON.stringify(
    {
      remove_alias_keys: [aliasKey]
    },
    null,
    2
  );

  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_delete_message",
      "Patch mode: remove this alias key from assets/studio/data/tag_aliases.json aliases object."
    ),
    snippet
  };
}

function buildManualPatchForAliasCreate(aliasKey, description, tags) {
  const normalizedAlias = normalize(aliasKey);
  const fragment = {
    [normalizedAlias]: {
      description: String(description || "").trim(),
      tags: Array.isArray(tags) ? tags.slice() : []
    }
  };
  const snippet = JSON.stringify(fragment, null, 2);
  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_create_message",
      "Patch mode: alias fragment prepared for new alias \"{alias_key}\". Paste inside aliases object.",
      { alias_key: normalizedAlias }
    ),
    snippet
  };
}

function buildManualPatchForAliasEdit(aliasKey, newAliasKey, description, tags) {
  const normalizedOld = normalize(aliasKey);
  const normalizedNew = normalize(newAliasKey);
  const fragment = {
    [normalizedNew]: {
      description: String(description || "").trim(),
      tags: Array.isArray(tags) ? tags.slice() : []
    }
  };
  const snippet = JSON.stringify(fragment, null, 2);
  const renameNote = normalizedOld !== normalizedNew
    ? aliasesText(
        null,
        "patch_edit_rename_note",
        " Also remove old alias key \"{alias_key}\" from assets/studio/data/tag_aliases.json.",
        { alias_key: normalizedOld }
      )
    : "";

  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_edit_message",
      "Patch mode: alias fragment prepared for \"{alias_key}\". Paste inside aliases object.{rename_note}",
      {
        alias_key: normalizedOld,
        rename_note: renameNote
      }
    ),
    snippet
  };
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
    message: aliasesText(
      null,
      "patch_demote_message",
      "Patch mode: section snippets prepared for demoting \"{tag_id}\".",
      { tag_id: tagId }
    ),
    snippet
  };
}

function normalizeImportAliasRows(rawAliases) {
  if (!rawAliases || typeof rawAliases !== "object") return [];
  const out = [];
  const seen = new Set();
  for (const [rawAlias, rawValue] of Object.entries(rawAliases)) {
    const alias = normalize(rawAlias);
    if (!alias) continue;
    let normalized = null;
    try {
      normalized = normalizeAliasValue(rawValue);
    } catch (error) {
      continue;
    }
    if (seen.has(alias)) {
      const idx = out.findIndex((item) => item.alias === alias);
      if (idx >= 0) out[idx] = { alias, value: normalized.value, targets: normalized.targets };
      continue;
    }
    seen.add(alias);
    out.push({ alias, value: normalized.value, targets: normalized.targets });
  }
  return out;
}

async function readImportAliasesFromFile(file) {
  const rawText = await file.text();
  let payload = null;
  try {
    payload = JSON.parse(rawText);
  } catch (error) {
    throw new Error(aliasesText(null, "import_invalid_json", "Import file is not valid JSON."));
  }

  if (!payload || typeof payload !== "object") {
    throw new Error(aliasesText(null, "import_invalid_object", "Import file must be a JSON object."));
  }
  const rows = normalizeImportAliasRows(payload.aliases);
  if (!rows.length) {
    throw new Error(aliasesText(null, "import_missing_aliases_object", "Import file must include aliases object with at least one alias."));
  }

  const aliasesObj = {};
  for (const row of rows) {
    aliasesObj[row.alias] = row.value;
  }
  return {
    tag_aliases_version: String(payload.tag_aliases_version || "tag_aliases_v1"),
    updated_at_utc: normalizeTimestamp(payload.updated_at_utc) || "",
    aliases: aliasesObj
  };
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

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function toTimestampMs(value) {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isFinite(ms) ? ms : null;
}

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
}

function buildAliasesImportModeText(state, mode) {
  const label = mode === "post"
    ? aliasesText(state.config, "import_mode_local_server", "Local server")
    : aliasesText(state.config, "import_mode_patch", "Patch");
  return aliasesText(state.config, "import_mode_template", "Import mode: {mode}", { mode: label });
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

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
