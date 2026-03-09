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
import {
  openConfirmDetailModal,
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  tagRegistryUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const MAX_ALIAS_TAGS = 4;
const DEMOTE_TAG_MATCH_CAP = 12;
const TAG_SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;
let GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";
const UI = tagRegistryUi;
const { className: UI_CLASS, selector: UI_SELECTOR, state: UI_STATE } = UI;

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
  const patchModalHtml = renderStudioModalFrame({
    modalRole: UI.role.patchModal,
    backdropRole: UI.role.patchModalClose,
    titleId: "tagRegistryPatchTitle",
    title: patchModalTitle,
    bodyHtml: `
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(patchModalLabel)}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.patchSnippet}"></pre>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.copyPatch, label: patchModalCopy, primary: true },
      { role: UI.role.patchModalClose, label: patchModalClose }
    ])
  });
  const editModalHtml = renderStudioModalFrame({
    modalRole: UI.role.editModal,
    titleId: "tagRegistryEditTitle",
    title: editModalTitle,
    bodyHtml: `
      <p class="${UI_CLASS.formMeta}" data-role="${UI.role.editTagId}"></p>
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField}">
          <input type="text" class="tagStudio__input ${UI_CLASS.formReadonly}" data-role="${UI.role.editTagName}" autocomplete="off" readonly>
        </label>
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(editDescriptionLabel)}</span>
          <textarea class="tagStudio__input ${UI_CLASS.formDescriptionInput}" data-role="${UI.role.editDescription}" rows="3" autocomplete="off"></textarea>
        </label>
      </div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.editStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.saveEdit, label: editSaveButton, primary: true },
      { role: UI.role.editModalClose, label: editCloseButton }
    ])
  });
  const newModalHtml = renderStudioModalFrame({
    modalRole: UI.role.newModal,
    titleId: "tagRegistryNewTitle",
    title: newModalTitle,
    bodyHtml: `
      <div class="tagStudio__key ${UI_CLASS.newGroupKey}" data-role="${UI.role.newGroupKey}"></div>
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(newSlugLabel)}</span>
          <input type="text" class="tagStudio__input" data-role="${UI.role.newTagSlug}" autocomplete="off">
        </label>
        <p class="${UI_CLASS.formWarning}" data-role="${UI.role.newTagWarning}"></p>
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(newDescriptionLabel)}</span>
          <textarea class="tagStudio__input ${UI_CLASS.formDescriptionInput}" data-role="${UI.role.newTagDescription}" rows="3" autocomplete="off"></textarea>
        </label>
      </div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.newTagStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.createTag, label: newCreateButton, primary: true, disabled: true },
      { role: UI.role.newModalClose, label: newCancelButton }
    ])
  });
  const demoteModalHtml = renderStudioModalFrame({
    modalRole: UI.role.demoteModal,
    backdropRole: UI.role.demoteModalClose,
    titleId: "tagRegistryDemoteTitle",
    title: demoteModalTitle,
    bodyHtml: `
      <p class="${UI_CLASS.formMeta}" data-role="${UI.role.demoteTagMeta}"></p>
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField} ${UI_CLASS.formSearchWrap}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(demoteSearchLabel)}</span>
          <input type="text" class="tagStudio__input" data-role="${UI.role.demoteTagSearch}" autocomplete="off" placeholder="${escapeHtml(demoteSearchPlaceholder)}">
          <div class="${UI_CLASS.popup}" data-role="${UI.role.demoteTagPopupWrap}" hidden>
            <div class="${UI_CLASS.popupInner}" data-role="${UI.role.demoteTagPopup}"></div>
          </div>
        </label>
      </div>
      <div class="tagStudio__key ${UI_CLASS.formKey}" data-role="${UI.role.demoteGroupKey}"></div>
      <div class="tagStudio__chipList ${UI_CLASS.formSelected}" data-role="${UI.role.demoteTagList}"></div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.demoteStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.confirmDemote, label: demoteConfirmButton, primary: true, disabled: true },
      { role: UI.role.demoteModalClose, label: demoteCloseButton }
    ])
  });
  const deleteModalHtml = renderStudioModalFrame({
    modalRole: UI.role.deleteModal,
    backdropRole: UI.role.deleteModalClose,
    titleId: "tagRegistryDeleteTitle",
    title: deleteModalTitle,
    bodyHtml: `
      <p class="${UI_CLASS.formMeta}" data-role="${UI.role.deleteTagMeta}"></p>
      <p class="${UI_CLASS.formImpact}">
        ${escapeHtml(deleteImpactIntro)}
      </p>
      <p class="${UI_CLASS.formImpact}" data-role="${UI.role.deleteImpact}"></p>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.deleteStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.confirmDeleteTag, label: deleteConfirmButton, primary: true },
      { role: UI.role.deleteModalClose, label: deleteCloseButton }
    ])
  });
  const refs = {
    importFileLabel: state.mount.querySelector(UI_SELECTOR.importFileLabel),
    chooseFile: state.mount.querySelector(UI_SELECTOR.chooseFile),
    importFile: state.mount.querySelector(UI_SELECTOR.importFile),
    importModeLabel: state.mount.querySelector(UI_SELECTOR.importModeLabel),
    importMode: state.mount.querySelector(UI_SELECTOR.importMode),
    importButton: state.mount.querySelector(UI_SELECTOR.importButton),
    openNewTag: state.mount.querySelector(UI_SELECTOR.openNewTag),
    saveMode: state.mount.querySelector(UI_SELECTOR.saveMode),
    selectedFile: state.mount.querySelector(UI_SELECTOR.selectedFile),
    importResult: state.mount.querySelector(UI_SELECTOR.importResult),
    key: state.mount.querySelector(UI_SELECTOR.key),
    searchLabel: state.mount.querySelector(UI_SELECTOR.searchLabel),
    search: state.mount.querySelector(UI_SELECTOR.search),
    list: state.mount.querySelector(UI_SELECTOR.list),
    modalHost: state.mount.querySelector(UI_SELECTOR.modalHost)
  };

  const missingRef = Object.entries(refs).find(([, value]) => !value);
  if (missingRef) {
    renderError(
      state,
      registryText(state.config, "missing_template_shell_error", "Tag Registry error: missing template shell markup.")
    );
    return;
  }

  refs.importFileLabel.textContent = importFileLabel;
  refs.chooseFile.textContent = chooseFileLabel;
  refs.importModeLabel.textContent = importModeFieldLabel;
  refs.importButton.textContent = importButtonLabel;
  refs.openNewTag.textContent = newTagButtonLabel;
  refs.saveMode.textContent = importModeLabel;
  refs.searchLabel.textContent = searchLabel;
  refs.search.setAttribute("placeholder", searchPlaceholder);
  setSelectOptionLabel(refs.importMode, "add", importModeOptionAdd);
  setSelectOptionLabel(refs.importMode, "merge", importModeOptionMerge);
  setSelectOptionLabel(refs.importMode, "replace", importModeOptionReplace);
  refs.modalHost.innerHTML = `${patchModalHtml}${editModalHtml}${newModalHtml}${demoteModalHtml}${deleteModalHtml}`;

  state.refs = {
    ...refs,
    patchModal: state.mount.querySelector(UI_SELECTOR.patchModal),
    patchSnippet: state.mount.querySelector(UI_SELECTOR.patchSnippet),
    copyPatch: state.mount.querySelector(UI_SELECTOR.copyPatch),
    editModal: state.mount.querySelector(UI_SELECTOR.editModal),
    editTagId: state.mount.querySelector(UI_SELECTOR.editTagId),
    editTagName: state.mount.querySelector(UI_SELECTOR.editTagName),
    editDescription: state.mount.querySelector(UI_SELECTOR.editDescription),
    editStatus: state.mount.querySelector(UI_SELECTOR.editStatus),
    saveEdit: state.mount.querySelector(UI_SELECTOR.saveEdit),
    newModal: state.mount.querySelector(UI_SELECTOR.newModal),
    newGroupKey: state.mount.querySelector(UI_SELECTOR.newGroupKey),
    newTagSlug: state.mount.querySelector(UI_SELECTOR.newTagSlug),
    newTagWarning: state.mount.querySelector(UI_SELECTOR.newTagWarning),
    newTagDescription: state.mount.querySelector(UI_SELECTOR.newTagDescription),
    newTagStatus: state.mount.querySelector(UI_SELECTOR.newTagStatus),
    createTag: state.mount.querySelector(UI_SELECTOR.createTag),
    demoteModal: state.mount.querySelector(UI_SELECTOR.demoteModal),
    demoteTagMeta: state.mount.querySelector(UI_SELECTOR.demoteTagMeta),
    demoteTagSearch: state.mount.querySelector(UI_SELECTOR.demoteTagSearch),
    demoteTagPopupWrap: state.mount.querySelector(UI_SELECTOR.demoteTagPopupWrap),
    demoteTagPopup: state.mount.querySelector(UI_SELECTOR.demoteTagPopup),
    demoteGroupKey: state.mount.querySelector(UI_SELECTOR.demoteGroupKey),
    demoteTagList: state.mount.querySelector(UI_SELECTOR.demoteTagList),
    demoteStatus: state.mount.querySelector(UI_SELECTOR.demoteStatus),
    confirmDemote: state.mount.querySelector(UI_SELECTOR.confirmDemote),
    deleteModal: state.mount.querySelector(UI_SELECTOR.deleteModal),
    deleteTagMeta: state.mount.querySelector(UI_SELECTOR.deleteTagMeta),
    deleteImpact: state.mount.querySelector(UI_SELECTOR.deleteImpact),
    deleteStatus: state.mount.querySelector(UI_SELECTOR.deleteStatus),
    confirmDeleteTag: state.mount.querySelector(UI_SELECTOR.confirmDeleteTag)
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
    if (!event.target.closest(UI_SELECTOR.patchModalClose)) return;
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
    if (!event.target.closest(UI_SELECTOR.editModalClose)) return;
    closeEditModal(state);
  });

  state.refs.saveEdit.addEventListener("click", () => {
    void handleTagEdit(state);
  });

  state.refs.newModal.addEventListener("click", (event) => {
    if (event.target.closest(UI_SELECTOR.newModalClose)) {
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
    if (event.target.closest(UI_SELECTOR.demoteModalClose)) {
      closeDemoteModal(state);
      return;
    }
    if (state.refs.demoteTagPopupWrap.hidden) return;
    if (!event.target.closest(UI_SELECTOR.demoteTagPopupWrap) && !event.target.closest(UI_SELECTOR.demoteTagSearch)) {
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
    if (!event.target.closest(UI_SELECTOR.deleteModalClose)) return;
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
  const allTagsLabel = registryText(state.config, "all_tags_filter", "All tags [{count}]", { count: totalCount });
  const groupButtons = STUDIO_GROUPS.map((group) => {
    const count = Number(groupCounts[group] || 0);
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="${classNames(UI_CLASS.keyPill, chipGroupClass(group), UI_CLASS.groupFilterButton)}"
        data-group="${escapeHtml(group)}"
        ${stateAttr(state.filterGroup === group ? UI_STATE.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)} [${count}]
      </button>
    `;
  }).join("");

  state.refs.key.innerHTML = `
    <button type="button" class="tagStudio__button ${UI_CLASS.allFilterButton}" data-group="all"${stateAttr(state.filterGroup === "all" ? UI_STATE.active : "")}>${escapeHtml(allTagsLabel)}</button>
    ${groupButtons}
    ${renderGroupInfoControl(state)}
  `;
}

function groupTitleAttr(state, group) {
  const description = String(state.groupDescriptions.get(group) || "").trim();
  if (!description) return "";
  return `title="${escapeHtml(description)}"`;
}

function renderGroupInfoControl(state) {
  const title = registryText(state.config, "group_info_title", "Open group descriptions in a new tab");
  const ariaLabel = registryText(state.config, "group_info_aria_label", "Open group descriptions in a new tab");
  return `
    <a
      class="${classNames(UI_CLASS.keyPill, UI_CLASS.keyInfoButton)}"
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
    <div class="${UI_CLASS.listHead}">
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="label"${stateAttr(state.sortKey === "label" ? UI_STATE.active : "")}>
        ${escapeHtml(tagHeading)}${sortIndicator(state, "label")}
      </button>
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="description"${stateAttr(state.sortKey === "description" ? UI_STATE.active : "")}>
        ${escapeHtml(descriptionHeading)}${sortIndicator(state, "description")}
      </button>
    </div>
  `;

  if (!visible.length) {
    state.refs.list.innerHTML = `${headerHtml}<p class="${UI_CLASS.empty}">${escapeHtml(registryText(state.config, "empty_state", "none"))}</p>`;
    return;
  }

  state.refs.list.innerHTML = `
    ${headerHtml}
    <ul class="${UI_CLASS.listRows}">
      ${visible.map((tag) => `
        <li class="${UI_CLASS.listRow}">
          <div class="${UI_CLASS.tagCol}">
            <div class="${UI_CLASS.tagActions}">
              <span class="${classNames(UI_CLASS.chip, chipGroupClass(tag.group), UI_CLASS.tagChip)}" title="${escapeHtml(tag.tagId)}">
                <button type="button" class="${UI_CLASS.tagInlineButton}" data-tag-id="${escapeHtml(tag.tagId)}" aria-label="${escapeHtml(registryText(state.config, "tag_edit_aria_label", "Edit {tag_id}", { tag_id: tag.tagId }))}">
                  ${escapeHtml(tag.label)}
                </button>
              <button
                type="button"
                class="${classNames(UI_CLASS.chipRemove, UI_CLASS.demoteButton)}"
                data-demote-tag-id="${escapeHtml(tag.tagId)}"
                title="${escapeHtml(registryText(state.config, "tag_demote_title", "Demote canonical tag to alias"))}"
                aria-label="${escapeHtml(registryText(state.config, "tag_demote_aria_label", "Demote {tag_id}", { tag_id: tag.tagId }))}"
              >
                ←
              </button>
              <button
                type="button"
                class="${UI_CLASS.chipRemove}"
                data-delete-tag-id="${escapeHtml(tag.tagId)}"
                title="${escapeHtml(registryText(state.config, "tag_delete_title", "Delete canonical tag"))}"
                aria-label="${escapeHtml(registryText(state.config, "tag_delete_aria_label", "Delete {tag_id}", { tag_id: tag.tagId }))}"
              >
                ×
              </button>
              </span>
            </div>
          </div>
          <div class="${UI_CLASS.descCol}">
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
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(tag.group))}" title="${escapeHtml(String(state.groupDescriptions.get(tag.group) || tag.tagId))}">
      ${escapeHtml(tag.group)}
    </span>
  `;
  state.refs.editTagName.value = slug;
  state.refs.editDescription.value = String(tag.description || "");
  setStatusText(
    state.refs.editStatus,
    "",
    state.saveMode === "post"
    ? ""
    : registryText(state.config, "local_edit_required", "Local server is required for edit.")
  );
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
  setStatusText(state.refs.newTagStatus, kind, message);
}

function renderNewTagGroupKey(state) {
  if (!state.newTagState) {
    state.refs.newGroupKey.innerHTML = "";
    return;
  }
  state.refs.newGroupKey.innerHTML = STUDIO_GROUPS.map((group) => {
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="${classNames(UI_CLASS.keyPill, chipGroupClass(group))}"
        data-new-group="${escapeHtml(group)}"
        ${stateAttr(state.newTagState.group === group ? UI_STATE.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("") + renderGroupInfoControl(state);
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
  setStatusText(state.refs.editStatus, kind, message);
}

function setImpactPreview(target, kind, message) {
  setStatusText(target, kind, message, UI_CLASS.formImpact);
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
  setStatusText(state.refs.deleteStatus, kind, message);
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
  setStatusText(state.refs.deleteImpact, "", "", UI_CLASS.formImpact);
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
  setStatusText(state.refs.deleteImpact, "", "", UI_CLASS.formImpact);
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
  setStatusText(state.refs.demoteStatus, kind, message);
}

function renderDemoteGroupKey(state) {
  if (!state.demoteState) {
    state.refs.demoteGroupKey.innerHTML = "";
    return;
  }
  const selected = new Set((state.demoteState.tags || []).map((tagId) => normalize(tagId).split(":", 1)[0]));
  state.refs.demoteGroupKey.innerHTML = STUDIO_GROUPS.map((group) => {
    const titleAttr = groupTitleAttr(state, group);
    return `<span class="${classNames(UI_CLASS.keyPill, chipGroupClass(group))}"${stateAttr(selected.has(group) ? UI_STATE.active : "")} ${titleAttr}>${escapeHtml(group)}</span>`;
  }).join("") + renderGroupInfoControl(state);
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
      <span class="${classNames(UI_CLASS.chip, chipGroupClass(group))}" title="${escapeHtml(tagId)}">
        ${escapeHtml(label)}
        <button
          type="button"
          class="${UI_CLASS.chipRemove}"
          data-remove-demote-tag="${escapeHtml(tagId)}"
          aria-label="${escapeHtml(registryText(state.config, "remove_target_tag_aria_label", "Remove {tag_id}", { tag_id: tagId }))}"
        >
          x
        </button>
      </span>
    `;
  }).join("");
  state.refs.demoteTagList.innerHTML = rows || `<span class="${UI_CLASS.empty}">${escapeHtml(registryText(state.config, "empty_state", "none"))}</span>`;
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
      class="${classNames(UI_CLASS.popupPill, chipGroupClass(item.group))}"
      data-popup-demote-tag-id="${escapeHtml(item.tagId)}"
      title="${escapeHtml(item.tagId)}"
    >
      ${escapeHtml(item.label)}
    </button>
  `);
  if (result.truncated) {
    chips.push(`<span class="${classNames(UI_CLASS.popupPill, UI_CLASS.popupMore)}" title="${escapeHtml(registryText(state.config, "popup_more_title", "More matches available"))}">...</span>`);
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
    const confirmResult = await openConfirmDetailModal({
      root: state.mount,
      title: registryText(state.config, "demote_confirm_title", "Confirm Tag Demotion"),
      body: registryText(
        state.config,
        "demote_confirm_template",
        "Demote \"{tag_id}\" to alias \"{alias_key}\"?\n\nTargets: {targets}",
        {
          tag_id: tag.tagId,
          alias_key: aliasKey,
          targets: aliasTargets.join(", ")
        }
      ),
      impact: previewSummary,
      primaryLabel: registryText(state.config, "demote_confirm_button", "Demote"),
      cancelLabel: registryText(state.config, "demote_cancel_button", "Cancel")
    });
    if (!confirmResult.confirmed) {
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
  setStatusText(state.refs.importResult, kind, message, UI_CLASS.toolbarResult);
}

function clearImportResult(state) {
  setImportResult(state, "", "");
}

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
}

function renderError(state, message) {
  state.mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(message)}</div>`;
}

function setSelectOptionLabel(select, value, label) {
  if (!select) return;
  const option = select.querySelector(`option[value="${value}"]`);
  if (option) option.textContent = label;
}

function setStatusText(target, kind, message, baseClass = UI_CLASS.formStatus) {
  if (!target) return;
  target.textContent = message || "";
  target.className = baseClass;
  if (kind) {
    target.dataset.state = kind;
    return;
  }
  delete target.dataset.state;
}

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
}

function stateAttr(stateValue) {
  return stateValue ? ` data-state="${escapeHtml(stateValue)}"` : "";
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
