import {
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  loadStudioAliasesJson,
  loadStudioGroupsJson,
  loadStudioRegistryJson
} from "./studio-data.js";
import {
  probeStudioHealth
} from "./studio-transport.js";
import {
  buildGroupDescriptionMap,
  buildRegistryLookup,
  buildRegistryOptions,
  configureTagAliasesDomain,
  countAliasesByGroup,
  findAliasEntry as findNormalizedAliasEntry,
  getAliasEditValidation as getNormalizedAliasEditValidation,
  getEditTagMatches as getNormalizedEditTagMatches,
  getVisibleAliases,
  isCreateAliasFlow as isCreateNormalizedAliasFlow,
  normalize,
  normalizeAliases,
  normalizeTimestamp,
  parseTagIdCsv
} from "./tag-aliases-domain.js";
import {
  buildAliasesImportModeText,
  buildManualPatchForAliasCreate,
  buildManualPatchForAliasDelete,
  buildManualPatchForAliasEdit,
  buildManualPatchForAliasPromote,
  buildManualPatchForDemote,
  buildManualPatchForNewAliases,
  readImportAliasesFromFile
} from "./tag-aliases-save.js";
import {
  previewAliasPromote,
  previewTagDemoteFromAliases,
  submitAliasDelete,
  submitAliasEdit,
  submitAliasPromote,
  submitAliasesImport,
  submitTagDemoteFromAliases
} from "./tag-aliases-service.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const ALIAS_RE = /^[a-z0-9][a-z0-9-]*$/;
const MAX_ALIAS_TAGS = 4;
const EDIT_TAG_MATCH_CAP = 12;
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
  configureTagAliasesDomain({
    groups: STUDIO_GROUPS,
    maxAliasTags: MAX_ALIAS_TAGS
  });
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
    loadStudioRegistryJson(state.config),
    loadStudioAliasesJson(state.config)
  ]);
  let groupsData = null;
  try {
    groupsData = await loadStudioGroupsJson(state.config);
  } catch (error) {
    groupsData = null;
  }
  state.registryById = buildRegistryLookup(registryData);
  state.registryOptions = buildRegistryOptions(state.registryById);
  state.groupDescriptions = buildGroupDescriptionMap(groupsData);
  state.aliasesUpdatedAt = normalizeTimestamp(aliasesData && aliasesData.updated_at_utc);
  state.aliases = normalizeAliases(
    aliasesData,
    state.aliasesUpdatedAt,
    state.registryById,
    (key, fallback, tokens) => aliasesText(null, key, fallback, tokens)
  );
}

function makeAliasEntry(state, alias, description, targets, updatedAtUtc) {
  const normalizedAlias = normalize(alias);
  const normalizedDescription = String(description || "").trim();
  const normalizedTargets = Array.isArray(targets) ? targets.map((tagId) => normalize(tagId)).filter(Boolean) : [];
  const resolvedTargets = normalizedTargets.map((tagId) => {
    const info = state.registryById.get(tagId);
    return {
      tagId,
      group: info ? info.group : "",
      label: info ? info.label : tagId,
      known: Boolean(info)
    };
  });
  const groups = Array.from(new Set(resolvedTargets.filter((item) => item.known).map((item) => item.group)));
  const hasUnknown = resolvedTargets.some((item) => !item.known);
  const normalizedUpdatedAt = normalizeTimestamp(updatedAtUtc) || state.aliasesUpdatedAt;
  const updatedAtMs = normalizedUpdatedAt ? Date.parse(normalizedUpdatedAt) : null;
  return {
    alias: normalizedAlias,
    value: {
      description: normalizedDescription,
      tags: normalizedTargets.slice()
    },
    description: normalizedDescription,
    targets: normalizedTargets.slice(),
    resolvedTargets,
    groups,
    hasUnknown,
    updatedAtUtc: normalizedUpdatedAt,
    updatedAtMs: Number.isFinite(updatedAtMs) ? updatedAtMs : null
  };
}

function replaceAliasEntry(state, entry, originalAlias = "") {
  const normalizedOriginal = normalize(originalAlias);
  state.aliases = state.aliases
    .filter((item) => item && item.alias !== entry.alias && item.alias !== normalizedOriginal)
    .concat([entry]);
}

function syncAliasDerivedState(state) {
  state.registryOptions = buildRegistryOptions(state.registryById);
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

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "asc" ? " ↑" : " ↓";
}

function sortBtnClass(state, key) {
  return state.sortKey === key ? " is-active" : "";
}

async function probeImportMode(state) {
  const ok = await probeStudioHealth(500);
  state.saveMode = ok ? "post" : "patch";
  renderImportMode(state);
}

function renderImportMode(state) {
  state.refs.saveMode.textContent = buildAliasesImportModeText(state, state.saveMode);
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

  const result = await submitAliasesImport({
    saveMode: state.saveMode,
    importMode: state.importMode,
    importAliases,
    filename: state.selectedFile ? String(state.selectedFile.name || "") : "",
    config: state.config,
    state
  });
  if (result.ok && result.mode === "post") {
    setImportResult(state, "success", result.summary);
    await loadData(state);
    renderControls(state);
    renderList(state);
    return;
  }

  if (result.switchToPatch) {
    state.saveMode = "patch";
    renderImportMode(state);
    setImportResult(state, "error", result.message);
  }

  const patchResult = result.patchResult || buildManualPatchForNewAliases(state, importAliases);
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

  const result = await submitAliasDelete({
    saveMode: state.saveMode,
    aliasKey,
    config: state.config
  });
  if (result.ok && result.mode === "post") {
    setImportResult(state, "success", result.summary);
    state.aliasesUpdatedAt = normalizeTimestamp(result.response && result.response.updated_at_utc) || state.aliasesUpdatedAt;
    state.aliases = state.aliases.filter((entry) => entry && entry.alias !== aliasKey);
    renderControls(state);
    renderList(state);
    return;
  }

  if (result.switchToPatch) {
    state.saveMode = "patch";
    renderImportMode(state);
    setImportResult(state, "error", result.message);
  }

  const patchResult = result.patchResult || buildManualPatchForAliasDelete(aliasKey);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function findAliasEntry(state, aliasKey) {
  return findNormalizedAliasEntry(state.aliases, aliasKey);
}

function isCreateAliasFlow(state) {
  return isCreateNormalizedAliasFlow(state.editState);
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
  return getNormalizedAliasEditValidation({
    editState: state.editState,
    aliasInput: state.refs.editAliasName.value,
    descriptionInput: state.refs.editAliasDescription.value,
    aliases: state.aliases,
    registryById: state.registryById,
    aliasRe: ALIAS_RE,
    maxAliasTags: MAX_ALIAS_TAGS,
    text: (key, fallback, tokens) => aliasesText(state.config, key, fallback, tokens)
  });
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
  return getNormalizedEditTagMatches({
    query,
    editState: state.editState,
    registryOptions: state.registryOptions,
    cap: EDIT_TAG_MATCH_CAP
  });
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
  const result = await submitAliasEdit({
    saveMode: state.saveMode,
    isCreate,
    originalAlias: state.editState.originalAlias,
    validation,
    config: state.config
  });
  if (result.ok && result.mode === "post") {
    if (result.summary) {
      setImportResult(state, "success", result.summary);
    }
    state.aliasesUpdatedAt = normalizeTimestamp(result.response && result.response.updated_at_utc) || state.aliasesUpdatedAt;
    replaceAliasEntry(
      state,
      makeAliasEntry(state, validation.alias, validation.description, validation.tags, state.aliasesUpdatedAt),
      state.editState.originalAlias
    );
    renderControls(state);
    renderList(state);
    closeAliasEditModal(state);
    return;
  }

  if (result.switchToPatch) {
    state.saveMode = "patch";
    renderImportMode(state);
    setAliasEditStatus(state, "error", result.message);
  }

  const patchResult = result.patchResult || (isCreate
    ? buildManualPatchForAliasCreate(
        validation.alias,
        validation.description,
        validation.tags
      )
    : buildManualPatchForAliasEdit(
        state.editState.originalAlias,
        validation.alias,
        validation.description,
        validation.tags
      ));
  closeAliasEditModal(state);
  openPatchModal(state, patchResult.snippet);
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

  if (state.saveMode === "post") {
    const preview = await previewAliasPromote({
      aliasKey,
      group,
      config: state.config
    });
    if (!preview.ok) {
      setImportResult(state, "error", preview.message);
      return;
    }
    const previewSummary = preview.summary;
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
  }

  const result = await submitAliasPromote({
    saveMode: state.saveMode,
    state,
    aliasKey,
    group
  });
  if (!result.ok) {
    setImportResult(state, "error", result.message);
    return;
  }
  if (result.mode === "post") {
    setImportResult(state, "success", result.summary);
    const updatedAtUtc = normalizeTimestamp(result.response && result.response.updated_at_utc) || state.aliasesUpdatedAt;
    state.aliasesUpdatedAt = updatedAtUtc || state.aliasesUpdatedAt;
    state.aliases = state.aliases.filter((entry) => entry && entry.alias !== aliasKey);
    state.registryById.set(`${group}:${aliasKey}`, { group, label: aliasKey });
    syncAliasDerivedState(state);
    renderControls(state);
    renderList(state);
    return;
  }

  const patchResult = result.patchResult || buildManualPatchForAliasPromote(state, aliasKey, group);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
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
    aliasTargets = parseTagIdCsv(input, (key, fallback, tokens) => aliasesText(null, key, fallback, tokens));
  } catch (error) {
    setImportResult(state, "error", String(error.message || aliasesText(state.config, "invalid_target_tags", "Invalid target tags.")));
    return;
  }
  if (aliasTargets.includes(canonicalTagId)) {
    setImportResult(state, "error", aliasesText(state.config, "demotion_target_self", "Target list must not include the demoted tag."));
    return;
  }

  if (state.saveMode === "post") {
    const preview = await previewTagDemoteFromAliases({
      canonicalTagId,
      aliasTargets,
      config: state.config
    });
    if (!preview.ok) {
      setImportResult(state, "error", preview.message);
      return;
    }
    const previewSummary = preview.summary;
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
  }

  const result = await submitTagDemoteFromAliases({
    saveMode: state.saveMode,
    canonicalTagId,
    aliasTargets
  });
  if (!result.ok) {
    setImportResult(state, "error", result.message || aliasesText(state.config, "demotion_failed", "Demotion failed."));
    return;
  }
  if (result.mode === "post") {
    setImportResult(state, "success", String(result.response.summary_text || aliasesText(state.config, "demoted_success", "Demoted.")));
    const updatedAtUtc = normalizeTimestamp(result.response && result.response.updated_at_utc) || state.aliasesUpdatedAt;
    state.aliasesUpdatedAt = updatedAtUtc || state.aliasesUpdatedAt;
    state.registryById.delete(canonicalTagId);
    replaceAliasEntry(
      state,
      makeAliasEntry(state, canonicalTagId.split(":")[1] || canonicalTagId, "", aliasTargets, updatedAtUtc)
    );
    syncAliasDerivedState(state);
    renderControls(state);
    renderList(state);
    return;
  }

  const patchResult = result.patchResult || buildManualPatchForDemote(canonicalTagId, aliasTargets);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
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

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
}

function renderError(state, message) {
  state.mount.innerHTML = `<div class="tagStudioError">${escapeHtml(message)}</div>`;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
