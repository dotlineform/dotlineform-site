import {
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfigWithText
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
} from "./tag-aliases-domain.js";
import {
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
import {
  openConfirmDetailModal,
  openConfirmModal
} from "./studio-modal.js";
import {
  clearTagAliasesImportResult,
  closeTagAliasesDemoteModal,
  closeTagAliasesEditModal,
  closeTagAliasesPromotionModal,
  collectTagAliasesModalRefs,
  hideTagAliasesDemoteTagPopup,
  hideTagAliasesEditTagPopup,
  hideTagAliasesImportModal,
  hideTagAliasesPatchModal,
  openTagAliasesCreateModal,
  openTagAliasesDemoteModal,
  openTagAliasesEditModal,
  openTagAliasesPromotionModal,
  renderTagAliasesModals,
  renderTagAliasesDemoteSelectionState,
  renderTagAliasesEditModalState,
  setTagAliasesDemoteStatus,
  setTagAliasesEditStatus,
  setTagAliasesImportResult,
  setTagAliasesPromotionStatus,
  setTagAliasesSelectedImportFile,
  showTagAliasesDemoteTagPopup,
  showTagAliasesEditTagPopup,
  showTagAliasesImportModal,
  showTagAliasesPatchModal,
  updateTagAliasesPromotionUi
} from "./tag-aliases-modals.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  tagAliasesUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const ALIAS_RE = /^[a-z0-9][a-z0-9-]*$/;
const MAX_ALIAS_TAGS = 4;
const EDIT_TAG_MATCH_CAP = 12;
const DEMOTE_TAG_MATCH_CAP = 12;
let GROUP_INFO_PAGE_PATH = "/studio/analytics/tag-groups/";
const UI = tagAliasesUi;
const { className: UI_CLASS, selector: UI_SELECTOR, state: UI_STATE } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagAliasesPage);
} else {
  initTagAliasesPage();
}

function routeStateDetail(state) {
  return {
    route: "tag-aliases",
    mode: state.importModalOpen ? "import" : state.editState || state.promotionState || state.demoteState ? "edit" : "list",
    service: state.saveMode === "post" ? "available" : "unavailable",
    recordLoaded: Boolean(state.aliases && state.aliases.length)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.mount, Boolean(state.isBusy), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.mount, ready, routeStateDetail(state));
}

async function withRouteBusy(state, task) {
  state.isBusy = true;
  syncRouteBusyState(state);
  try {
    return await task();
  } finally {
    state.isBusy = false;
    syncRouteBusyState(state);
  }
}

async function initTagAliasesPage() {
  const mount = document.getElementById("tag-aliases");
  if (!mount) return;
  initializeStudioRouteState(mount, { route: "tag-aliases", mode: "list" });

  let config = null;
  try {
    config = await loadStudioConfigWithText("tag_aliases");
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">Failed to load tag aliases config.</div>`;
    setStudioRouteReady(mount, true, {
      route: "tag-aliases",
      mode: "empty",
      service: "unavailable",
      recordLoaded: false
    });
    return;
  }
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
    studioGroups: STUDIO_GROUPS,
    groupInfoPagePath: GROUP_INFO_PAGE_PATH,
    importMode: "add",
    saveMode: "patch",
    importAvailable: false,
    selectedFile: null,
    importModalOpen: false,
    patchSnippet: "",
    registryOptions: [],
    groupDescriptions: new Map(),
    promotionState: null,
    demoteState: null,
    editState: null,
    refs: null,
    isBusy: false
  };

  renderShell(state);
  wireEvents(state);
  syncImportModeFromControl(state);

  try {
    await loadData(state);
    renderControls(state);
    renderList(state);
    markRouteReady(state, true);
  } catch (error) {
    renderError(
      state,
      aliasesText(state.config, "load_failed_error", "Failed to load aliases from /assets/studio/data/tag_aliases.json.")
    );
    markRouteReady(state, true);
    return;
  }

  void probeImportMode(state);
}

function renderShell(state) {
  const importButtonLabel = aliasesText(state.config, "import_button", "Import");
  const newAliasButtonLabel = aliasesText(state.config, "new_alias_button", "New alias");
  const searchLabel = aliasesText(state.config, "search_label", "Search aliases");
  const searchPlaceholder = aliasesText(state.config, "search_placeholder", "search");
  const refs = {
    openImportModal: state.mount.querySelector(UI_SELECTOR.openImportModal),
    openNewAlias: state.mount.querySelector(UI_SELECTOR.openNewAlias),
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
      aliasesText(state.config, "missing_template_shell_error", "Tag Aliases error: missing template shell markup.")
    );
    return;
  }

  refs.openImportModal.textContent = importButtonLabel;
  refs.openNewAlias.textContent = newAliasButtonLabel;
  refs.searchLabel.textContent = searchLabel;
  refs.search.setAttribute("placeholder", searchPlaceholder);
  refs.modalHost.innerHTML = renderTagAliasesModals(state);

  state.refs = {
    ...refs,
    ...collectTagAliasesModalRefs(state.mount)
  };
  renderImportAvailability(state);
}

function wireEvents(state) {
  state.refs.search.addEventListener("input", () => {
    state.searchQuery = normalize(state.refs.search.value);
    renderList(state);
  });

  state.refs.openImportModal.addEventListener("click", () => {
    if (!state.importAvailable) return;
    clearImportResult(state);
    showTagAliasesImportModal(state);
    syncRouteBusyState(state);
  });

  state.refs.chooseFile.addEventListener("click", () => {
    state.refs.importFile.click();
  });

  state.refs.importFile.addEventListener("change", () => {
    const files = state.refs.importFile.files;
    setTagAliasesSelectedImportFile(state, files && files.length ? files[0] : null);
  });

  state.refs.importMode.addEventListener("change", () => {
    syncImportModeFromControl(state);
  });

  state.refs.importButton.addEventListener("click", () => {
    void withRouteBusy(state, () => handleImport(state));
  });

  state.refs.openNewAlias.addEventListener("click", () => {
    openAliasCreateModal(state);
  });

  state.mount.addEventListener("click", (event) => {
    const demoteButton = event.target.closest("button[data-demote-tag-id]");
    if (demoteButton) {
      const tagId = normalize(demoteButton.getAttribute("data-demote-tag-id"));
      if (tagId) openDemoteModal(state, tagId);
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
      if (alias) void withRouteBusy(state, () => handleAliasDelete(state, alias));
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
      const isAllGroups = !group || group === "all";
      state.filterGroup = isAllGroups ? "all" : group;
      if (isAllGroups) {
        state.searchQuery = "";
        state.refs.search.value = "";
      }
      renderControls(state);
      renderList(state);
      return;
    }

    const sortButton = event.target.closest("button[data-sort-key]");
    if (sortButton) {
      const key = normalize(sortButton.getAttribute("data-sort-key"));
      if (key !== "alias" && key !== "tags") return;
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
    if (!event.target.closest(UI_SELECTOR.patchModalClose)) return;
    closePatchModal(state);
  });

  state.refs.importModal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.importModalClose)) return;
    closeImportModal(state);
  });

  state.refs.promotionModal.addEventListener("click", (event) => {
    if (event.target.closest(UI_SELECTOR.promotionModalClose)) {
      closePromotionModal(state);
      return;
    }
    const groupButton = event.target.closest("button[data-promotion-group]");
    if (!groupButton || !state.promotionState) return;
    const group = normalize(groupButton.getAttribute("data-promotion-group"));
    if (!STUDIO_GROUPS.includes(group)) return;
    state.promotionState.group = group;
    updateTagAliasesPromotionUi(state);
  });

  state.refs.confirmPromotion.addEventListener("click", () => {
    void withRouteBusy(state, () => submitAliasPromotion(state));
  });

  state.refs.demoteModal.addEventListener("click", (event) => {
    if (event.target.closest(UI_SELECTOR.demoteModalClose)) {
      closeDemoteModal(state);
      return;
    }
    if (state.refs.demoteTagPopupWrap.hidden) return;
    if (!event.target.closest(UI_SELECTOR.demoteTagPopupWrap) && !event.target.closest(UI_SELECTOR.demoteTagSearch)) {
      hideTagAliasesDemoteTagPopup(state);
    }
  });

  state.refs.demoteTagSearch.addEventListener("input", () => {
    renderDemoteTagPopup(state);
  });

  state.refs.demoteTagSearch.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      hideTagAliasesDemoteTagPopup(state);
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
    hideTagAliasesDemoteTagPopup(state);
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
    void withRouteBusy(state, () => handleTagDemoteFromAliases(state));
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
    if (event.target.closest(UI_SELECTOR.editModalClose)) {
      closeAliasEditModal(state);
      return;
    }
    if (state.refs.editTagPopupWrap.hidden) return;
    if (!event.target.closest(UI_SELECTOR.editTagPopupWrap) && !event.target.closest(UI_SELECTOR.editTagSearch)) {
      hideTagAliasesEditTagPopup(state);
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
      hideTagAliasesEditTagPopup(state);
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
    hideTagAliasesEditTagPopup(state);
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
    void withRouteBusy(state, () => saveAliasEdit(state));
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

function closeImportModal(state) {
  hideTagAliasesImportModal(state);
  syncRouteBusyState(state);
}

function openPromotionModal(state, aliasKey, suggestedGroup) {
  openTagAliasesPromotionModal(state, aliasKey, suggestedGroup);
  syncRouteBusyState(state);
}

function closePromotionModal(state) {
  closeTagAliasesPromotionModal(state);
  syncRouteBusyState(state);
}

function openDemoteModal(state, tagId) {
  clearImportResult(state);
  const canonicalTagId = normalize(tagId);
  if (!canonicalTagId) return;
  const tagInfo = state.registryById.get(canonicalTagId);
  if (!tagInfo) {
    setImportResult(
      state,
      "error",
      aliasesText(state.config, "unknown_tag_selected", "Unknown tag selected: {tag_id}", { tag_id: canonicalTagId })
    );
    return;
  }

  openTagAliasesDemoteModal(state, {
    canonicalTagId,
    aliasKey: canonicalTagId.split(":", 2)[1] || canonicalTagId
  });
  syncRouteBusyState(state);
}

function closeDemoteModal(state) {
  closeTagAliasesDemoteModal(state);
  syncRouteBusyState(state);
}

function setDemoteStatus(state, kind, message) {
  setTagAliasesDemoteStatus(state, kind, message);
}

function getDemoteValidation(state) {
  if (!state.demoteState) return { valid: false, warning: "", tags: [] };
  const selectedTags = Array.isArray(state.demoteState.tags) ? state.demoteState.tags.slice() : [];
  let warning = "";

  if (!selectedTags.length) {
    warning = aliasesText(state.config, "target_tag_required", "At least one canonical target tag is required.");
  } else if (selectedTags.length > MAX_ALIAS_TAGS) {
    warning = aliasesText(state.config, "target_tags_max", "At most {max_tags} target tags are allowed.", { max_tags: MAX_ALIAS_TAGS });
  } else {
    const seenGroups = new Set();
    for (const tagId of selectedTags) {
      if (tagId === state.demoteState.tagId) {
        warning = aliasesText(state.config, "demotion_target_self", "Target list must not include the demoted tag.");
        break;
      }
      const info = state.registryById.get(tagId);
      if (!info) {
        warning = aliasesText(state.config, "unknown_tag_selected", "Unknown tag selected: {tag_id}", { tag_id: tagId });
        break;
      }
      if (seenGroups.has(info.group)) {
        warning = aliasesText(state.config, "target_tags_one_per_group", "Only one target tag per group is allowed ({group}).", { group: info.group });
        break;
      }
      seenGroups.add(info.group);
    }
  }

  return {
    valid: !warning,
    warning,
    tags: selectedTags
  };
}

function updateDemoteUi(state) {
  if (!state.demoteState) return;
  const validation = getDemoteValidation(state);
  let statusKind = "";
  let statusMessage = "";
  if (validation.warning) {
    const emptyWarning = aliasesText(state.config, "target_tag_required", "At least one canonical target tag is required.");
    statusKind = validation.warning === emptyWarning ? "" : "error";
    statusMessage = validation.warning;
  }
  renderTagAliasesDemoteSelectionState(state, {
    canConfirm: validation.valid,
    statusKind,
    statusMessage
  });
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
    hideTagAliasesDemoteTagPopup(state);
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
    chips.push(`<span class="${classNames(UI_CLASS.popupPill, UI_CLASS.popupMore)}" title="${escapeHtml(aliasesText(state.config, "popup_more_title", "More matches available"))}">…</span>`);
  }
  showTagAliasesDemoteTagPopup(state, chips.join(""));
}

function addDemoteTag(state, tagId) {
  if (!state.demoteState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId || !state.registryById.has(normalizedTagId)) return;
  if (normalizedTagId === state.demoteState.tagId) {
    setDemoteStatus(state, "error", aliasesText(state.config, "demotion_target_self", "Target list must not include the demoted tag."));
    return;
  }
  if (state.demoteState.tags.includes(normalizedTagId)) return;
  if (state.demoteState.tags.length >= MAX_ALIAS_TAGS) {
    setDemoteStatus(state, "error", aliasesText(state.config, "target_tags_max", "At most {max_tags} target tags are allowed.", { max_tags: MAX_ALIAS_TAGS }));
    return;
  }

  const nextGroup = normalizedTagId.split(":", 1)[0];
  const groupConflict = state.demoteState.tags.some((item) => item.split(":", 1)[0] === nextGroup);
  if (groupConflict) {
    setDemoteStatus(state, "error", aliasesText(state.config, "target_tags_one_per_group", "Only one target tag per group is allowed ({group}).", { group: nextGroup }));
    return;
  }

  state.demoteState.tags.push(normalizedTagId);
}

function setPromotionStatus(state, kind, message) {
  setTagAliasesPromotionStatus(state, kind, message);
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
  const allTagsLabel = aliasesText(state.config, "all_tags_filter", "All tags [{count}]", { count: totalCount });
  const groupButtons = STUDIO_GROUPS.map((group) => {
    const count = Number(counts[group] || 0);
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
  const title = aliasesText(state.config, "group_info_title", "Open group descriptions in a new tab");
  const ariaLabel = aliasesText(state.config, "group_info_aria_label", "Open group descriptions in a new tab");
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
  const visible = getVisibleAliases(state);
  const aliasHeading = aliasesText(state.config, "table_heading_alias", "alias");
  const tagsHeading = aliasesText(state.config, "group_tags_heading", "tags");

  const headerHtml = `
    <div class="${UI_CLASS.listHead}">
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="alias"${stateAttr(state.sortKey === "alias" ? UI_STATE.active : "")}>
        ${escapeHtml(aliasHeading)}${sortIndicator(state, "alias")}
      </button>
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="tags"${stateAttr(state.sortKey === "tags" ? UI_STATE.active : "")}>
        ${escapeHtml(tagsHeading)}${sortIndicator(state, "tags")}
      </button>
    </div>
  `;

  if (!visible.length) {
    state.refs.list.innerHTML = `${headerHtml}<p class="${UI_CLASS.empty}">${escapeHtml(aliasesText(state.config, "empty_state", "none"))}</p>`;
    return;
  }

  state.refs.list.innerHTML = `
    ${headerHtml}
    <ul class="${UI_CLASS.listRows}">
      ${visible.map((entry) => {
        const sortedTargets = entry.resolvedTargets.slice().sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" }));
        return `
        <li class="${UI_CLASS.listRow}">
          <div class="${UI_CLASS.aliasCol}">
            <span class="${UI_CLASS.chip}">
              <button
                type="button"
                class="${UI_CLASS.aliasButton}"
                data-edit-alias="${escapeHtml(entry.alias)}"
                title="${escapeHtml(aliasesText(state.config, "alias_edit_title", "Edit alias {alias}", { alias: entry.alias }))}"
                aria-label="${escapeHtml(aliasesText(state.config, "alias_edit_aria_label", "Edit alias {alias}", { alias: entry.alias }))}"
              >
                ${escapeHtml(entry.alias)}
              </button>
              <button
                type="button"
                class="${UI_CLASS.chipRemove}"
                data-promote-alias="${escapeHtml(entry.alias)}"
                aria-label="${escapeHtml(aliasesText(state.config, "alias_promote_aria_label", "Promote alias {alias}", { alias: entry.alias }))}"
                title="${escapeHtml(aliasesText(state.config, "alias_promote_title", "Promote alias to canonical tag"))}"
              >
                →
              </button>
              <button
                type="button"
                class="${UI_CLASS.chipRemove}"
                data-delete-alias="${escapeHtml(entry.alias)}"
                aria-label="${escapeHtml(aliasesText(state.config, "alias_delete_aria_label", "Delete alias {alias}", { alias: entry.alias }))}"
                title="${escapeHtml(aliasesText(state.config, "alias_delete_title", "Delete alias"))}"
              >
                ×
              </button>
            </span>
          </div>
          <div class="${UI_CLASS.tagsCol}">
            <div class="${UI_CLASS.tagList}">
              ${sortedTargets.map((target) => `
                <span class="${classNames(UI_CLASS.chip, target.known ? chipGroupClass(target.group) : UI_CLASS.chipWarning)}" title="${escapeHtml(target.tagId)}">
                  ${escapeHtml(String(target.label || "").toLowerCase())}
                  ${target.known ? `
                    <button
                      type="button"
                      class="${UI_CLASS.chipRemove}"
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

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "asc" ? " ↑" : " ↓";
}

async function probeImportMode(state) {
  const ok = await probeStudioHealth(500);
  state.saveMode = ok ? "post" : "patch";
  state.importAvailable = ok;
  renderImportAvailability(state);
  syncRouteBusyState(state);
}

function renderImportAvailability(state) {
  const available = Boolean(state.importAvailable && state.saveMode === "post");
  state.importAvailable = available;
  if (state.refs.openImportModal) state.refs.openImportModal.disabled = !available;
  if (state.refs.importButton) state.refs.importButton.disabled = !available;
  if (!available && state.importModalOpen) closeImportModal(state);
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
    state.importAvailable = false;
    renderImportAvailability(state);
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

  const modalResult = await openConfirmModal({
    root: state.mount,
    title: aliasesText(state.config, "delete_modal_title", "Delete Alias"),
    body: aliasesText(state.config, "delete_confirm_template", "Delete alias \"{alias_key}\"?", { alias_key: aliasKey }),
    primaryLabel: aliasesText(state.config, "delete_confirm_button", "Delete"),
    cancelLabel: aliasesText(state.config, "delete_cancel_button", "Cancel")
  });
  if (!modalResult.confirmed) {
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
    state.importAvailable = false;
    renderImportAvailability(state);
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

function openAliasEditModal(state, aliasKey) {
  clearImportResult(state);
  const entry = findAliasEntry(state, aliasKey);
  if (!entry) {
    setImportResult(state, "error", aliasesText(state.config, "alias_not_found", "Alias not found: {alias_key}", { alias_key: aliasKey }));
    return;
  }

  openTagAliasesEditModal(state, entry);
  updateAliasEditUi(state);
  syncRouteBusyState(state);
}

function openAliasCreateModal(state) {
  clearImportResult(state);
  openTagAliasesCreateModal(state);
  updateAliasEditUi(state);
  syncRouteBusyState(state);
}

function closeAliasEditModal(state) {
  closeTagAliasesEditModal(state);
  syncRouteBusyState(state);
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
  setTagAliasesEditStatus(state, kind, message);
}

function updateAliasEditUi(state) {
  if (!state.editState) return;
  const validation = getAliasEditValidation(state);
  state.refs.editAliasName.value = normalize(state.refs.editAliasName.value);
  let statusKind = "";
  let statusMessage = "";
  if (validation.tagsWarning) {
    statusKind = "error";
    statusMessage = validation.tagsWarning;
  }
  renderTagAliasesEditModalState(state, {
    warning: validation.warning || "",
    canSave: validation.valid && validation.changed,
    statusKind,
    statusMessage
  });
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
    hideTagAliasesEditTagPopup(state);
    return;
  }
  const chips = matches.map((item) => `
    <button
      type="button"
      class="${classNames(UI_CLASS.popupPill, chipGroupClass(item.group))}"
      data-popup-tag-id="${escapeHtml(item.tagId)}"
      title="${escapeHtml(item.tagId)}"
    >
      ${escapeHtml(item.label)}
    </button>
  `);
  if (result.truncated) {
    chips.push(`<span class="${classNames(UI_CLASS.popupPill, UI_CLASS.popupMore)}" title="${escapeHtml(aliasesText(state.config, "popup_more_title", "More matches available"))}">…</span>`);
  }
  showTagAliasesEditTagPopup(state, chips.join(""));
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
    state.importAvailable = false;
    renderImportAvailability(state);
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

async function handleAliasPromote(state, alias) {
  const aliasKey = normalize(alias);
  if (!aliasKey) return;
  clearImportResult(state);

  const entry = findAliasEntry(state, aliasKey);
  if (!entry) {
    setImportResult(state, "error", aliasesText(state.config, "alias_not_found", "Alias not found: {alias_key}", { alias_key: aliasKey }));
    return;
  }

  const suggestedGroup = entry && Array.isArray(entry.groups) && entry.groups.length ? entry.groups[0] : "subject";
  openPromotionModal(state, aliasKey, suggestedGroup);
}

async function submitAliasPromotion(state) {
  if (!state.promotionState) return;
  const aliasKey = normalize(state.promotionState.aliasKey);
  const group = normalize(state.promotionState.group);
  if (!aliasKey) return;
  if (!group) {
    setPromotionStatus(state, "", aliasesText(state.config, "promotion_group_required", "Choose a group."));
    return;
  }
  if (!STUDIO_GROUPS.includes(group)) {
    setPromotionStatus(
      state,
      "error",
      aliasesText(state.config, "promotion_group_invalid", "Promotion group must be one of: subject, domain, form, theme.")
    );
    return;
  }
  closePromotionModal(state);

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

async function handleTagDemoteFromAliases(state) {
  if (!state.demoteState) return;
  const canonicalTagId = normalize(state.demoteState.tagId);
  if (!canonicalTagId) return;
  const validation = getDemoteValidation(state);
  if (!validation.valid) {
    setDemoteStatus(state, "error", validation.warning || aliasesText(state.config, "invalid_target_tags", "Invalid target tags."));
    return;
  }
  const aliasTargets = validation.tags.slice().sort((a, b) => a.localeCompare(b));

  if (state.saveMode === "post") {
    const preview = await previewTagDemoteFromAliases({
      canonicalTagId,
      aliasTargets,
      config: state.config
    });
    if (!preview.ok) {
      setDemoteStatus(state, "error", preview.message);
      setImportResult(state, "error", preview.message);
      return;
    }
    const previewSummary = preview.summary;
    const aliasKey = canonicalTagId.split(":")[1] || canonicalTagId;
    const confirmResult = await openConfirmDetailModal({
      root: state.mount,
      title: aliasesText(state.config, "demotion_confirm_title", "Confirm Tag Demotion"),
      body: aliasesText(
        state.config,
        "demotion_confirm_template",
        "Demote \"{tag_id}\" to alias \"{alias_key}\"?\n\nTargets: {targets}",
        {
          tag_id: canonicalTagId,
          alias_key: aliasKey,
          targets: aliasTargets.join(", ")
        }
      ),
      impact: previewSummary,
      primaryLabel: aliasesText(state.config, "demotion_confirm_button", "Demote"),
      cancelLabel: aliasesText(state.config, "demotion_cancel_button", "Cancel")
    });
    if (!confirmResult.confirmed) {
      return;
    }
  }

  const result = await submitTagDemoteFromAliases({
    saveMode: state.saveMode,
    canonicalTagId,
    aliasTargets
  });
  if (!result.ok) {
    const message = result.message || aliasesText(state.config, "demotion_failed", "Demotion failed.");
    setDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }
  if (result.mode === "post") {
    closeDemoteModal(state);
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
  closeDemoteModal(state);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function openPatchModal(state, snippet) {
  showTagAliasesPatchModal(state, snippet);
}

function closePatchModal(state) {
  hideTagAliasesPatchModal(state);
}

function setImportResult(state, kind, message) {
  setTagAliasesImportResult(state, kind, message);
}

function clearImportResult(state) {
  clearTagAliasesImportResult(state);
}

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
}

function renderError(state, message) {
  state.mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(message)}</div>`;
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
