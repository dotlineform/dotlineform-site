// Studio-owned role, class, and state contracts for tag workflows.
function freezeMap(map) {
  return Object.freeze({ ...map });
}

function selectorMap(roleMap) {
  return freezeMap(
    Object.fromEntries(
      Object.entries(roleMap).map(([key, value]) => [key, `[data-role="${value}"]`])
    )
  );
}

export function createUiContract({ role, className = {}, state = {} }) {
  const frozenRole = freezeMap(role);
  return Object.freeze({
    role: frozenRole,
    selector: selectorMap(frozenRole),
    className: freezeMap(className),
    state: freezeMap(state)
  });
}

export const seriesTagEditorUi = createUiContract({
  role: {
    editorRoot: "series-tag-editor",
    editorShell: "editor-shell",
    workSection: "work-section",
    workInput: "work-input",
    workSelection: "selected-work",
    workPopup: "work-popup",
    workPopupList: "work-popup-list",
    messageSection: "message-section",
    contextHint: "context-hint",
    status: "status",
    saveWarning: "save-warning",
    saveResult: "save-result",
    groupsSection: "groups-section",
    groups: "groups",
    searchSection: "search-section",
    tagInput: "tag-input",
    addTag: "add-tag",
    save: "save",
    popup: "popup",
    popupList: "popup-list"
  },
  className: {
    error: "studioForm__status",
    selectedWorkPill: "analytics__selectedWorkPill",
    selectedWorkButton: "analytics__selectedWorkBtn",
    selectedWorkId: "analytics__selectedWorkId",
    chipRemove: "studioUi__chipRemove",
    suggest: "analyticsSuggest",
    suggestSection: "analyticsSuggest__section",
    suggestHeading: "analyticsSuggest__heading",
    suggestWorkRows: "analyticsSuggest__workRows",
    suggestWorkButton: "analyticsSuggest__workButton",
    suggestWorkId: "analyticsSuggest__workId",
    suggestWorkTitle: "analyticsSuggest__workTitle",
    suggestTagRows: "analyticsSuggest__tagRows",
    suggestAliasRows: "analyticsSuggest__aliasRows",
    suggestAliasRow: "analyticsSuggest__aliasRow",
    suggestAliasPill: "analyticsSuggest__aliasPill",
    suggestAliasTargets: "analyticsSuggest__aliasTargets",
    suggestAliasTarget: "analyticsSuggest__aliasTarget",
    popupPill: "studioUi__popupPill",
    empty: "studioUi__empty",
    groups: "analyticsGroups",
    groupRow: "analyticsGroupRow",
    groupRowLabel: "analyticsGroupRow__label",
    groupRowChips: "analyticsGroupRow__chips",
    chip: "analytics__chip",
    chipText: "studioUi__chipText",
    chipInherited: "analytics__chip--inherited",
    chipTag: "analytics__chipTag",
    chipGroupPrefix: "analytics__chip--",
    weightDot: "analytics__weightDot",
    weightDotLow: "analytics__weightDot--low",
    weightDotMid: "analytics__weightDot--mid",
    weightDotHigh: "analytics__weightDot--high"
  },
  state: {
    active: "active",
    success: "success",
    warn: "warn",
    error: "error"
  }
});

export const seriesTagsUi = createUiContract({
  role: {
    pageRoot: "series-tags"
  },
  className: {
    error: "studioForm__status",
    empty: "studioUi__empty",
    chip: "analytics__chip",
    chipText: "studioUi__chipText",
    chipTag: "analytics__chipTag",
    chipGroupPrefix: "analytics__chip--",
    keyPill: "studioUi__keyPill",
    allFilterButton: "analyticsFilters__allBtn",
    groupFilterButton: "analyticsFilters__groupBtn",
    sortButton: "analyticsList__sortBtn",
    filters: "analyticsFilters seriesTags__filters"
  },
  state: {
    active: "active",
    success: "success",
    warn: "warn",
    error: "error"
  }
});

export const tagRegistryUi = createUiContract({
  role: {
    pageRoot: "tag-registry",
    toolbar: "toolbar",
    openNewTag: "open-new-tag",
    routeResult: "route-result",
    filters: "filters",
    key: "key",
    searchLabel: "search-label",
    search: "search",
    list: "list",
    modalHost: "modal-host",
    patchModal: "patch-modal",
    patchModalClose: "close-patch-modal",
    patchSnippet: "patch-snippet",
    copyPatch: "copy-patch",
    promotionModal: "promotion-modal",
    promotionModalClose: "close-promotion-modal",
    promotionAliasMeta: "promotion-alias-meta",
    promotionGroupKey: "promotion-group-key",
    promotionStatus: "promotion-status",
    confirmPromotion: "confirm-promotion",
    editModal: "edit-modal",
    editModalClose: "close-edit-modal",
    editTagId: "edit-tag-id",
    editGroupKey: "edit-group-key",
    editTagName: "edit-tag-name",
    editDescription: "edit-description",
    editStatus: "edit-status",
    saveEdit: "save-edit",
    newModal: "new-modal",
    newModalClose: "close-new-modal",
    newGroupKey: "new-group-key",
    newTagSlug: "new-tag-slug",
    newTagWarning: "new-tag-warning",
    newTagDescription: "new-tag-description",
    newTagStatus: "new-tag-status",
    createTag: "create-tag",
    demoteModal: "demote-modal",
    demoteModalClose: "close-demote-modal",
    demoteTagMeta: "demote-tag-meta",
    demoteTagSearch: "demote-tag-search",
    demoteTagPopupWrap: "demote-tag-popup-wrap",
    demoteTagPopup: "demote-tag-popup",
    demoteGroupKey: "demote-group-key",
    demoteTagList: "demote-tag-list",
    demoteStatus: "demote-status",
    confirmDemote: "confirm-demote",
    deleteModal: "delete-modal",
    deleteModalClose: "close-delete-modal",
    deleteTagMeta: "delete-tag-meta",
    deleteImpact: "delete-impact",
    deleteStatus: "delete-status",
    confirmDeleteTag: "confirm-delete-tag"
  },
  className: {
    modalLabel: "studioModal__label",
    modalPre: "studioModal__pre",
    error: "studioForm__status",
    keyPill: "studioUi__keyPill",
    allFilterButton: "analyticsFilters__allBtn",
    groupFilterButton: "analyticsFilters__groupBtn",
    toolbarResult: "analyticsToolbar__result",
    empty: "studioUi__empty",
    listHead: "analyticsList__head tagRegistry__head",
    listRows: "analyticsList__rows tagRegistry__rows",
    listRow: "analyticsList__row tagRegistry__row",
    sortButton: "analyticsList__sortBtn tagRegistry__sortBtn",
    chip: "analytics__chip",
    chipGroupPrefix: "analytics__chip--",
    chipRemove: "studioUi__chipRemove",
    tagChip: "tagRegistry__tagChip",
    tagCol: "tagRegistry__tagCol",
    tagActions: "tagRegistry__tagActions",
    tagInlineButton: "tagRegistry__tagInlineBtn",
    demoteButton: "tagRegistry__demoteBtn",
    descCol: "tagRegistry__descCol",
    updatedCol: "tagRegistry__updatedCol",
    formMeta: "analyticsForm__meta",
    formFields: "analyticsForm__fields",
    formField: "analyticsForm__field",
    formLabel: "analyticsForm__label",
    formReadonly: "analyticsForm__readonly",
    formDescriptionInput: "analyticsForm__descriptionInput",
    formWarning: "analyticsForm__warning",
    formStatus: "analyticsForm__status",
    formImpact: "analyticsForm__impact",
    deleteMetaTag: "tagRegistryDelete__metaTag",
    deleteMetaId: "tagRegistryDelete__metaId",
    deleteImpactList: "tagRegistryDelete__impactList",
    deleteImpactItem: "tagRegistryDelete__impactItem",
    deleteImpactValue: "tagRegistryDelete__impactValue",
    deleteImpactLinks: "tagRegistryDelete__impactLinks",
    deleteImpactLink: "tagRegistryDelete__impactLink",
    formSearchWrap: "analyticsForm__searchWrap",
    formKey: "analyticsForm__key",
    formSelected: "analyticsForm__selected",
    popup: "studioUi__popup",
    popupInner: "studioUi__popupInner",
    popupPill: "studioUi__popupPill",
    popupMore: "studioUi__popupMore",
    newGroupKey: "tagRegistryNew__key"
  },
  state: {
    active: "active",
    success: "success",
    warn: "warn",
    error: "error"
  }
});

export const tagAliasesUi = createUiContract({
  role: {
    pageRoot: "tag-aliases",
    toolbar: "toolbar",
    openNewAlias: "open-new-alias",
    routeResult: "route-result",
    filters: "filters",
    key: "key",
    searchLabel: "search-label",
    search: "search",
    list: "list",
    modalHost: "modal-host",
    patchModal: "patch-modal",
    patchModalClose: "close-patch-modal",
    patchSnippet: "patch-snippet",
    copyPatch: "copy-patch",
    promotionModal: "promotion-modal",
    promotionModalClose: "close-promotion-modal",
    promotionAliasMeta: "promotion-alias-meta",
    promotionGroupKey: "promotion-group-key",
    promotionStatus: "promotion-status",
    confirmPromotion: "confirm-promotion",
    demoteModal: "demote-modal",
    demoteModalClose: "close-demote-modal",
    demoteTagMeta: "demote-tag-meta",
    demoteTagSearch: "demote-tag-search",
    demoteTagPopupWrap: "demote-tag-popup-wrap",
    demoteTagPopup: "demote-tag-popup",
    demoteGroupKey: "demote-group-key",
    demoteTagList: "demote-tag-list",
    demoteStatus: "demote-status",
    confirmDemote: "confirm-demote",
    editModal: "edit-modal",
    editModalClose: "close-edit-modal",
    editModalTitle: "edit-modal-title",
    editAliasName: "edit-alias-name",
    editAliasWarning: "edit-alias-warning",
    editAliasDescription: "edit-alias-description",
    editTagSearch: "edit-tag-search",
    editTagPopupWrap: "edit-tag-popup-wrap",
    editTagPopup: "edit-tag-popup",
    editGroupKey: "edit-group-key",
    editTagList: "edit-tag-list",
    editStatus: "edit-status",
    saveEditAlias: "save-edit-alias"
  },
  className: {
    modalLabel: "studioModal__label",
    modalPre: "studioModal__pre",
    error: "studioForm__status",
    keyPill: "studioUi__keyPill",
    allFilterButton: "analyticsFilters__allBtn",
    groupFilterButton: "analyticsFilters__groupBtn",
    toolbarResult: "analyticsToolbar__result",
    empty: "studioUi__empty",
    listHead: "analyticsList__head tagAliases__head",
    listRows: "analyticsList__rows tagAliases__rows",
    listRow: "analyticsList__row tagAliases__row",
    sortButton: "tagRegistry__sortBtn",
    headLabel: "analyticsList__headLabel tagAliases__headLabel",
    chip: "analytics__chip",
    chipGroupPrefix: "analytics__chip--",
    chipWarning: "analytics__chip--warning",
    chipRemove: "studioUi__chipRemove",
    aliasCol: "tagAliases__aliasCol",
    aliasButton: "tagAliases__aliasBtn",
    tagsCol: "tagAliases__tagsCol",
    tagList: "tagAliases__tagList",
    formMeta: "analyticsForm__meta",
    formFields: "analyticsForm__fields",
    formField: "analyticsForm__field",
    formLabel: "analyticsForm__label",
    formWarning: "analyticsForm__warning",
    formStatus: "analyticsForm__status",
    formSearchWrap: "analyticsForm__searchWrap",
    formKey: "analyticsForm__key",
    formSelected: "analyticsForm__selected",
    popup: "studioUi__popup",
    popupInner: "studioUi__popupInner",
    popupPill: "studioUi__popupPill",
    popupMore: "studioUi__popupMore",
    editDescription: "tagAliasesEdit__description",
    editDialog: "tagAliasesEdit__dialog"
  },
  state: {
    active: "active",
    success: "success",
    warn: "warn",
    error: "error"
  }
});

export const tagGroupsUi = createUiContract({
  role: {
    pageRoot: "tag-groups",
    content: "content"
  },
  className: {
    error: "studioForm__status",
    empty: "studioUi__empty",
    chip: "studioUi__keyPill",
    chipGroupPrefix: "analytics__chip--",
    section: "analytics__groupInfoSection tagGroups__section",
    head: "analytics__groupInfoHead",
    text: "analytics__groupInfoText"
  }
});
