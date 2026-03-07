import {
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  buildStudioGroupDescriptionMap,
  loadStudioAliasesJson,
  loadStudioGroupsJson,
  loadStudioRegistryJson
} from "./studio-data.js";
import {
  probeStudioHealth,
} from "./studio-transport.js";
import {
  buildAliasKeySet,
  buildRegistryOptions,
  configureTagRegistryDomain,
  countTagsByGroup,
  findTagById as findRegistryTagById,
  getDemoteTagMatches as getRegistryDemoteTagMatches,
  getDemoteValidation as getRegistryDemoteValidation,
  getNewTagValidation as getRegistryNewTagValidation,
  getVisibleSortedTags,
  normalize,
  normalizeRegistryTags,
  normalizeTimestamp
} from "./tag-registry-domain.js";
import {
  buildManualPatchForCreateTag,
  buildManualPatchForDemote,
  buildManualPatchForNewTags,
  buildRegistryImportModeText
} from "./tag-registry-save.js";
import {
  previewDeleteImpact,
  previewTagDemote,
  readImportRegistryFromFile as readRegistryImportFromFile,
  submitCreateTag,
  submitDeleteTag,
  submitRegistryImport,
  submitTagDemote,
  submitTagEdit
} from "./tag-registry-service.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
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
  configureTagRegistryDomain({ groups: STUDIO_GROUPS });
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
    renderError(
      state,
      registryText(
        state.config,
        "load_failed_error",
        "Failed to load tag data from /assets/studio/data/tag_registry.json and /assets/studio/data/tag_aliases.json."
      )
    );
    return;
  }

  void probeImportMode(state);
}

function renderShell(state) {
  const importFileLabel = registryText(state.config, "import_file_label", "import file");
  const importModeFieldLabel = registryText(state.config, "import_mode_label", "mode");
  const importModeOptionAdd = registryText(state.config, "import_mode_option_add", "add (no overwrite)");
  const importModeOptionMerge = registryText(state.config, "import_mode_option_merge", "add + overwrite");
  const importModeOptionReplace = registryText(state.config, "import_mode_option_replace", "replace entire registry");
  const chooseFileLabel = registryText(state.config, "choose_file_button", "Choose file");
  const importButtonLabel = registryText(state.config, "import_button", "Import");
  const importModeLabel = buildRegistryImportModeText(state, "patch");
  const newTagButtonLabel = registryText(state.config, "new_tag_button", "New tag");
  const searchLabel = registryText(state.config, "search_label", "Search tags");
  const searchPlaceholder = registryText(state.config, "search_placeholder", "search");
  const patchModalTitle = registryText(state.config, "patch_modal_title", "Registry Patch Preview");
  const patchModalLabel = registryText(state.config, "patch_modal_label", "Manual patch snippet");
  const patchModalCopy = registryText(state.config, "patch_modal_copy_button", "Copy");
  const patchModalClose = registryText(state.config, "patch_modal_close_button", "Close");
  const editModalTitle = registryText(state.config, "edit_modal_title", "Edit Tag");
  const editDescriptionLabel = registryText(state.config, "edit_description_label", "description");
  const editSaveButton = registryText(state.config, "edit_save_button", "Save");
  const editCloseButton = registryText(state.config, "edit_close_button", "Close");
  const newModalTitle = registryText(state.config, "new_modal_title", "New Tag");
  const newSlugLabel = registryText(state.config, "new_slug_label", "slug");
  const newDescriptionLabel = registryText(state.config, "new_description_label", "description");
  const newCreateButton = registryText(state.config, "new_create_button", "Create");
  const newCancelButton = registryText(state.config, "new_cancel_button", "Cancel");
  const demoteModalTitle = registryText(state.config, "demote_modal_title", "Demote Tag to Alias");
  const demoteSearchLabel = registryText(state.config, "demote_search_label", "find target tags");
  const demoteSearchPlaceholder = registryText(state.config, "demote_search_placeholder", "search tags");
  const demoteConfirmButton = registryText(state.config, "demote_confirm_button", "Demote");
  const demoteCloseButton = registryText(state.config, "demote_close_button", "Close");
  const deleteModalTitle = registryText(state.config, "delete_modal_title", "Delete Tag");
  const deleteImpactIntro = registryText(
    state.config,
    "delete_impact_intro",
    "Deleting this tag also removes matching tag assignments and removes this tag from aliases. Aliases left with no targets are deleted."
  );
  const deleteConfirmButton = registryText(state.config, "delete_confirm_button", "Delete");
  const deleteCloseButton = registryText(state.config, "delete_close_button", "Close");
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
          <button type="button" class="tagStudio__button tagStudio__button--primary tagRegistry__newTagBtn" data-role="open-new-tag">${escapeHtml(newTagButtonLabel)}</button>
        </div>
        <p class="tagRegistry__selected" data-role="selected-file"></p>
        <p class="tagRegistry__result" data-role="import-result"></p>
      </div>

      <div class="tagRegistry__controls">
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
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryPatchTitle">
        <h3 id="tagRegistryPatchTitle">${escapeHtml(patchModalTitle)}</h3>
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
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryEditTitle">
        <h3 id="tagRegistryEditTitle">${escapeHtml(editModalTitle)}</h3>
        <p class="tagRegistryEdit__meta" data-role="edit-tag-id"></p>
        <div class="tagRegistryEdit__fields">
          <label class="tagRegistryEdit__field">
            <input type="text" class="tagStudio__input tagRegistryEdit__readonly" data-role="edit-tag-name" autocomplete="off" readonly>
          </label>
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">${escapeHtml(editDescriptionLabel)}</span>
            <textarea class="tagStudio__input tagRegistryEdit__descriptionInput" data-role="edit-description" rows="3" autocomplete="off"></textarea>
          </label>
        </div>
        <p class="tagRegistryEdit__status" data-role="edit-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="save-edit">${escapeHtml(editSaveButton)}</button>
          <button type="button" class="tagStudio__button" data-role="close-edit-modal">${escapeHtml(editCloseButton)}</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="new-modal" hidden>
      <div class="tagStudioModal__backdrop"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryNewTitle">
        <h3 id="tagRegistryNewTitle">${escapeHtml(newModalTitle)}</h3>
        <div class="tagStudio__key tagRegistryNew__key" data-role="new-group-key"></div>
        <div class="tagRegistryEdit__fields">
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">${escapeHtml(newSlugLabel)}</span>
            <input type="text" class="tagStudio__input" data-role="new-tag-slug" autocomplete="off">
          </label>
          <p class="tagAliasesEdit__warning" data-role="new-tag-warning"></p>
          <label class="tagRegistryEdit__field">
            <span class="tagRegistryEdit__label">${escapeHtml(newDescriptionLabel)}</span>
            <textarea class="tagStudio__input tagRegistryEdit__descriptionInput" data-role="new-tag-description" rows="3" autocomplete="off"></textarea>
          </label>
        </div>
        <p class="tagRegistryEdit__status" data-role="new-tag-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="create-tag" disabled>${escapeHtml(newCreateButton)}</button>
          <button type="button" class="tagStudio__button" data-role="close-new-modal">${escapeHtml(newCancelButton)}</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="demote-modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-demote-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryDemoteTitle">
        <h3 id="tagRegistryDemoteTitle">${escapeHtml(demoteModalTitle)}</h3>
        <p class="tagRegistryEdit__meta" data-role="demote-tag-meta"></p>
        <div class="tagRegistryEdit__fields">
          <label class="tagRegistryEdit__field tagAliasesEdit__searchWrap">
            <span class="tagRegistryEdit__label">${escapeHtml(demoteSearchLabel)}</span>
            <input type="text" class="tagStudio__input" data-role="demote-tag-search" autocomplete="off" placeholder="${escapeHtml(demoteSearchPlaceholder)}">
            <div class="tagStudio__popup" data-role="demote-tag-popup-wrap" hidden>
              <div class="tagStudio__popupInner" data-role="demote-tag-popup"></div>
            </div>
          </label>
        </div>
        <div class="tagStudio__key tagAliasesEdit__key" data-role="demote-group-key"></div>
        <div class="tagStudio__chipList tagAliasesEdit__selectedTags" data-role="demote-tag-list"></div>
        <p class="tagRegistryEdit__status" data-role="demote-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="confirm-demote" disabled>${escapeHtml(demoteConfirmButton)}</button>
          <button type="button" class="tagStudio__button" data-role="close-demote-modal">${escapeHtml(demoteCloseButton)}</button>
        </div>
      </div>
    </div>

    <div class="tagStudioModal" data-role="delete-modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-delete-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagRegistryDeleteTitle">
        <h3 id="tagRegistryDeleteTitle">${escapeHtml(deleteModalTitle)}</h3>
        <p class="tagRegistryEdit__meta" data-role="delete-tag-meta"></p>
        <p class="tagRegistryEdit__impact">
          ${escapeHtml(deleteImpactIntro)}
        </p>
        <p class="tagRegistryEdit__impact" data-role="delete-impact"></p>
        <p class="tagRegistryEdit__status" data-role="delete-status"></p>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="confirm-delete-tag">${escapeHtml(deleteConfirmButton)}</button>
          <button type="button" class="tagStudio__button" data-role="close-delete-modal">${escapeHtml(deleteCloseButton)}</button>
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
      state.refs.selectedFile.textContent = registryText(
        state.config,
        "selected_file_template",
        "Selected: {filename}",
        { filename: state.selectedFile.name }
      );
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
      setImportResult(state, "success", registryText(state.config, "patch_copy_success", "Patch snippet copied to clipboard."));
    } catch (error) {
      setImportResult(state, "error", registryText(state.config, "patch_copy_failed", "Copy failed. Select and copy the snippet manually."));
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
  const ok = await probeStudioHealth(500);
  state.saveMode = ok ? "post" : "patch";
  renderImportMode(state);
}

function renderImportMode(state) {
  state.refs.saveMode.textContent = buildRegistryImportModeText(state, state.saveMode);
}

async function loadRegistry(state, options = {}) {
  const [registryData, aliasesData] = await Promise.all([
    loadStudioRegistryJson(state.config, options),
    loadStudioAliasesJson(state.config, options)
  ]);
  let groupsData = null;
  try {
    groupsData = await loadStudioGroupsJson(state.config, options);
  } catch (error) {
    groupsData = null;
  }
  state.registryUpdatedAt = normalizeTimestamp(registryData && registryData.updated_at_utc);
  state.tags = normalizeRegistryTags(registryData, state.registryUpdatedAt);
  state.aliasKeys = buildAliasKeySet(aliasesData);
  state.groupDescriptions = buildStudioGroupDescriptionMap(groupsData, STUDIO_GROUPS);
  state.registryOptions = buildRegistryOptions(state.tags);
}

function renderControls(state) {
  const groupCounts = countTagsByGroup(state.tags);
  const totalCount = state.tags.length;
  const allActiveClass = state.filterGroup === "all" ? " is-active" : "";
  const allTagsLabel = registryText(state.config, "all_tags_filter", "All tags [{count}]", { count: totalCount });
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
    <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">${escapeHtml(allTagsLabel)}</button>
    ${groupButtons}
    ${renderGroupInfoControl(state, "registry")}
  `;
}

function groupTitleAttr(state, group) {
  const description = String(state.groupDescriptions.get(group) || "").trim();
  if (!description) return "";
  return `title="${escapeHtml(description)}"`;
}

function renderGroupInfoControl(state, scope) {
  const title = registryText(state.config, "group_info_title", "Open group descriptions in a new tab");
  const ariaLabel = registryText(state.config, "group_info_aria_label", "Open group descriptions in a new tab");
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
  const visible = getVisibleSortedTags(state);
  const tagHeading = registryText(state.config, "table_heading_tag", "tag");
  const descriptionHeading = registryText(state.config, "table_heading_description", "description");
  const headerHtml = `
    <div class="tagRegistry__head">
      <button type="button" class="tagRegistry__sortBtn${sortBtnClass(state, "label")}" data-sort-key="label">
        ${escapeHtml(tagHeading)}${sortIndicator(state, "label")}
      </button>
      <button type="button" class="tagRegistry__sortBtn${sortBtnClass(state, "description")}" data-sort-key="description">
        ${escapeHtml(descriptionHeading)}${sortIndicator(state, "description")}
      </button>
    </div>
  `;

  if (!visible.length) {
    state.refs.list.innerHTML = `${headerHtml}<p class="tagStudio__empty">${escapeHtml(registryText(state.config, "empty_state", "none"))}</p>`;
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
                <button type="button" class="tagRegistry__tagInlineBtn" data-tag-id="${escapeHtml(tag.tagId)}" aria-label="${escapeHtml(registryText(state.config, "tag_edit_aria_label", "Edit {tag_id}", { tag_id: tag.tagId }))}">
                  ${escapeHtml(tag.label)}
                </button>
              <button
                type="button"
                class="tagStudio__chipRemove tagRegistry__demoteBtn"
                data-demote-tag-id="${escapeHtml(tag.tagId)}"
                title="${escapeHtml(registryText(state.config, "tag_demote_title", "Demote canonical tag to alias"))}"
                aria-label="${escapeHtml(registryText(state.config, "tag_demote_aria_label", "Demote {tag_id}", { tag_id: tag.tagId }))}"
              >
                ←
              </button>
              <button
                type="button"
                class="tagStudio__chipRemove"
                data-delete-tag-id="${escapeHtml(tag.tagId)}"
                title="${escapeHtml(registryText(state.config, "tag_delete_title", "Delete canonical tag"))}"
                aria-label="${escapeHtml(registryText(state.config, "tag_delete_aria_label", "Delete {tag_id}", { tag_id: tag.tagId }))}"
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

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "asc" ? " ↑" : " ↓";
}

function sortBtnClass(state, key) {
  return state.sortKey === key ? " is-active" : "";
}

function findTagById(state, tagId) {
  return findRegistryTagById(state.tags, tagId);
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
    : registryText(state.config, "local_edit_required", "Local server is required for edit.");
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
  return getRegistryNewTagValidation({
    newTagState: state.newTagState,
    slugInput: state.refs.newTagSlug.value,
    descriptionInput: state.refs.newTagDescription.value,
    tags: state.tags,
    tagSlugRe: TAG_SLUG_RE,
    studioGroups: STUDIO_GROUPS,
    text: (key, fallback, tokens) => registryText(state.config, key, fallback, tokens)
  });
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

async function refreshDeleteImpactPreview(state) {
  const seq = ++state.deletePreviewSeq;
  const result = await previewDeleteImpact({
    saveMode: state.saveMode,
    tagId: state.deleteTagId,
    config: state.config
  });
  if (seq !== state.deletePreviewSeq || state.refs.deleteModal.hidden) return;
  if (result.ok) {
    state.deletePreview = result.summary;
    setImpactPreview(state.refs.deleteImpact, "", result.message);
    return;
  }
  setImpactPreview(state.refs.deleteImpact, "error", result.message);
}

async function handleTagEdit(state) {
  if (!state.editTagId) return;
  const tagId = state.editTagId;
  const description = String(state.refs.editDescription.value || "").trim();
  const result = await submitTagEdit({
    saveMode: state.saveMode,
    tag: findTagById(state, tagId),
    description,
    config: state.config
  });
  if (!result.ok) {
    setEditStatus(state, result.code === "no_changes" ? "" : "error", result.message);
    return;
  }

  setEditStatus(state, "success", result.message);
  setImportResult(state, "success", result.summary);
  const updatedAtUtc = normalizeTimestamp(result.response && result.response.updated_at_utc) || state.registryUpdatedAt;
  const updatedAtMs = updatedAtUtc ? Date.parse(updatedAtUtc) : null;
  state.registryUpdatedAt = updatedAtUtc || state.registryUpdatedAt;
  state.tags = state.tags.map((tag) => {
    if (!tag || tag.tagId !== tagId) return tag;
    return {
      ...tag,
      description,
      updatedAtUtc,
      updatedAtMs: Number.isFinite(updatedAtMs) ? updatedAtMs : tag.updatedAtMs
    };
  });
  state.registryOptions = buildRegistryOptions(state.tags);
  renderControls(state);
  renderList(state);
  closeEditModal(state);
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

  const result = await submitCreateTag({
    saveMode: state.saveMode,
    newTagRow,
    config: state.config,
    importMode: "add"
  });
  if (result.ok && result.mode === "post") {
    closeNewTagModal(state);
    setImportResult(state, "success", result.summary);
    const updatedAtUtc = normalizeTimestamp(result.response && result.response.updated_at_utc) || state.registryUpdatedAt;
    const updatedAtMs = updatedAtUtc ? Date.parse(updatedAtUtc) : null;
    state.registryUpdatedAt = updatedAtUtc || state.registryUpdatedAt;
    state.tags = state.tags
      .filter((tag) => tag && tag.tagId !== validation.tagId)
      .concat([{
        group: validation.group,
        tagId: validation.tagId,
        label: validation.slug,
        description: validation.description,
        status: "active",
        updatedAtUtc,
        updatedAtMs: Number.isFinite(updatedAtMs) ? updatedAtMs : null
      }]);
    state.registryOptions = buildRegistryOptions(state.tags);
    renderControls(state);
    renderList(state);
    return;
  }

  if (result.switchToPatch) {
    state.saveMode = "patch";
    renderImportMode(state);
    setNewTagStatus(state, "error", result.message);
  }

  const patchResult = result.patchResult || buildManualPatchForCreateTag(newTagRow);
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
    setImportResult(state, "error", registryText(state.config, "selected_tag_missing", "Selected tag is no longer available."));
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
    setDeleteStatus(state, "error", registryText(state.config, "local_delete_required", "Local server is required for delete."));
    setImpactPreview(state.refs.deleteImpact, "error", registryText(state.config, "delete_impact_unavailable_local", "Delete impact: unavailable (local server required)."));
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
  const deletedTagId = state.deleteTagId;
  const result = await submitDeleteTag({
    saveMode: state.saveMode,
    tag: findTagById(state, deletedTagId),
    config: state.config
  });
  if (!result.ok) {
    setDeleteStatus(state, "error", result.message);
    return;
  }

  closeDeleteModal(state);
  setImportResult(state, "success", result.summary);
  state.registryUpdatedAt = normalizeTimestamp(result.response && result.response.updated_at_utc) || state.registryUpdatedAt;
  state.tags = state.tags.filter((tag) => tag && tag.tagId !== deletedTagId);
  state.registryOptions = buildRegistryOptions(state.tags);
  renderControls(state);
  renderList(state);
}

function openDemoteModal(state, tagId) {
  clearImportResult(state);
  const tag = findTagById(state, tagId);
  if (!tag) {
    setImportResult(state, "error", registryText(state.config, "selected_tag_missing", "Selected tag is no longer available."));
    return;
  }
  const aliasKey = tag.tagId.split(":")[1] || tag.tagId;
  if (state.aliasKeys.has(aliasKey)) {
    setImportResult(
      state,
      "error",
      registryText(
        state.config,
        "alias_exists_demote_error",
        "Alias already exists: {alias_key}. Demotion overwrite is not permitted.",
        { alias_key: aliasKey }
      )
    );
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
          aria-label="${escapeHtml(registryText(state.config, "remove_target_tag_aria_label", "Remove {tag_id}", { tag_id: tagId }))}"
        >
          x
        </button>
      </span>
    `;
  }).join("");
  state.refs.demoteTagList.innerHTML = rows || `<span class="tagStudio__empty">${escapeHtml(registryText(state.config, "empty_state", "none"))}</span>`;
}

function getDemoteValidation(state) {
  return getRegistryDemoteValidation({
    demoteState: state.demoteState,
    tags: state.tags,
    maxAliasTags: MAX_ALIAS_TAGS,
    text: (key, fallback, tokens) => registryText(state.config, key, fallback, tokens)
  });
}

function updateDemoteUi(state) {
  if (!state.demoteState) return;
  renderDemoteGroupKey(state);
  renderDemoteTagList(state);
  const validation = getDemoteValidation(state);
  state.refs.confirmDemote.disabled = !validation.valid;
  if (validation.warning) {
    const emptyWarning = registryText(state.config, "demote_select_target_warning", "Select at least one target tag.");
    const kind = validation.warning === emptyWarning ? "" : "error";
    setDemoteStatus(state, kind, validation.warning);
  } else {
    setDemoteStatus(state, "", "");
  }
}

function getDemoteTagMatches(state, query) {
  return getRegistryDemoteTagMatches({
    query,
    demoteState: state.demoteState,
    registryOptions: state.registryOptions,
    cap: DEMOTE_TAG_MATCH_CAP
  });
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
    chips.push(`<span class="tagStudio__popupPill tagAliasesEdit__popupMore" title="${escapeHtml(registryText(state.config, "popup_more_title", "More matches available"))}">...</span>`);
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
    setDemoteStatus(state, "error", registryText(state.config, "demote_target_includes_self", "Target list must not include the demoted tag."));
    return;
  }
  if (state.demoteState.tags.includes(normalizedTagId)) return;
  if (state.demoteState.tags.length >= MAX_ALIAS_TAGS) {
    setDemoteStatus(state, "error", registryText(state.config, "demote_max_tags_warning", "Select up to {max_tags} tags.", { max_tags: MAX_ALIAS_TAGS }));
    return;
  }
  const nextGroup = tag.group;
  const groupConflict = state.demoteState.tags.some((item) => {
    const existing = findTagById(state, item);
    return Boolean(existing && existing.group === nextGroup);
  });
  if (groupConflict) {
    setDemoteStatus(
      state,
      "error",
      registryText(state.config, "demote_one_per_group_warning", "Only one target tag per group is allowed ({group}).", { group: nextGroup })
    );
    return;
  }
  state.demoteState.tags.push(normalizedTagId);
}

async function handleTagDemote(state) {
  if (!state.demoteState) return;
  const tag = findTagById(state, state.demoteState.tagId);
  if (!tag) {
    const message = registryText(state.config, "selected_tag_missing", "Selected tag is no longer available.");
    setDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }

  const aliasKey = tag.tagId.split(":")[1] || tag.tagId;
  if (state.aliasKeys.has(aliasKey)) {
    const message = registryText(
      state.config,
      "alias_exists_demote_error",
      "Alias already exists: {alias_key}. Demotion overwrite is not permitted.",
      { alias_key: aliasKey }
    );
    setDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }

  const validation = getDemoteValidation(state);
  if (!validation.valid) {
    setDemoteStatus(state, "error", validation.warning || registryText(state.config, "demote_invalid_targets", "Invalid target tags."));
    return;
  }

  const aliasTargets = validation.tags.slice().sort((a, b) => a.localeCompare(b));

  if (state.saveMode === "post") {
    const preview = await previewTagDemote({
      tagId: tag.tagId,
      aliasTargets,
      config: state.config
    });
    if (!preview.ok) {
      const message = preview.message;
      setDemoteStatus(state, "error", message);
      setImportResult(state, "error", message);
      return;
    }

    const previewSummary = preview.summary;
    if (Number(preview.response && preview.response.demoted_alias_overwritten || 0) > 0) {
      const message = registryText(
        state.config,
        "alias_exists_demote_error",
        "Alias already exists: {alias_key}. Demotion overwrite is not permitted.",
        { alias_key: aliasKey }
      );
      setDemoteStatus(state, "error", message);
      setImportResult(state, "error", message);
      return;
    }
    const ok = window.confirm(
      registryText(
        state.config,
        "demote_confirm_template",
        "Demote \"{tag_id}\" to alias \"{alias_key}\"?\n\nTargets: {targets}\n\nImpact:\n{preview_summary}",
        {
          tag_id: tag.tagId,
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

  const result = await submitTagDemote({
    saveMode: state.saveMode,
    tagId: tag.tagId,
    aliasTargets,
    config: state.config
  });
  if (!result.ok) {
    setDemoteStatus(state, "error", result.message);
    setImportResult(state, "error", result.message);
    return;
  }
  if (result.mode === "post") {
    closeDemoteModal(state);
    setImportResult(state, "success", result.summary);
    const updatedAtUtc = normalizeTimestamp(result.response && result.response.updated_at_utc) || state.registryUpdatedAt;
    state.registryUpdatedAt = updatedAtUtc || state.registryUpdatedAt;
    state.tags = state.tags.filter((item) => item && item.tagId !== tag.tagId);
    state.aliasKeys.add(aliasKey);
    state.registryOptions = buildRegistryOptions(state.tags);
    renderControls(state);
    renderList(state);
    return;
  }

  const patchResult = result.patchResult || buildManualPatchForDemote(tag.tagId, aliasTargets);
  closeDemoteModal(state);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

async function handleImport(state) {
  if (!state.selectedFile) {
    setImportResult(state, "error", registryText(state.config, "choose_import_file_error", "Choose an import file first."));
    return;
  }

  let importRegistry = null;
  try {
    importRegistry = await readImportRegistryFromFile(state.selectedFile);
  } catch (error) {
    setImportResult(state, "error", String(error.message || registryText(state.config, "invalid_import_file", "Invalid import file.")));
    return;
  }

  const result = await submitRegistryImport({
    saveMode: state.saveMode,
    importMode: state.importMode,
    importRegistry,
    filename: state.selectedFile ? String(state.selectedFile.name || "") : "",
    config: state.config,
    state
  });
  if (result.ok && result.mode === "post") {
    setImportResult(state, "success", result.summary);
    await loadRegistry(state, { cache: "no-store" });
    renderControls(state);
    renderList(state);
    return;
  }

  if (result.switchToPatch) {
    state.saveMode = "patch";
    renderImportMode(state);
    setImportResult(state, "error", result.message);
  }

  const patchResult = result.patchResult || buildManualPatchForNewTags(state, importRegistry);
  setImportResult(state, patchResult.kind, patchResult.message);
  if (patchResult.snippet) {
    openPatchModal(state, patchResult.snippet);
  }
}

async function readImportRegistryFromFile(file) {
  return readRegistryImportFromFile(file, STUDIO_GROUPS);
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

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
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
