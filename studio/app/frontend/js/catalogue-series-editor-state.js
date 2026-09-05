import {
  collectRequiredElements,
  createCatalogueEditorRouteStateOptions
} from "./catalogue-editor-route-boot.js";
import {
  createCatalogueEditorMessageRoleNode
} from "./catalogue-editor-message-controller.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";


export const SERIES_ROUTE_STATE = createCatalogueEditorRouteStateOptions({
  route: "catalogue-series"
});

export function collectSeriesEditorElements() {
  return collectRequiredElements({
    root: "catalogueSeriesRoot",
    loadingNode: "catalogueSeriesLoading",
    emptyNode: "catalogueSeriesEmpty",
    fieldsNode: "catalogueSeriesFields",
    searchNode: "catalogueSeriesSearch",
    popupNode: "catalogueSeriesPopup",
    popupListNode: "catalogueSeriesPopupList",
    openButton: "catalogueSeriesOpen",
    newButton: "catalogueSeriesNew",
    saveButton: "catalogueSeriesSave",
    deleteButton: "catalogueSeriesDelete",
    statusNode: "catalogueSeriesStatus",
    membersHeadingNode: "catalogueSeriesMembersHeading",
    membersActionsNode: "catalogueSeriesMembersActions",
    membersMetaNode: "catalogueSeriesMembersMeta",
    membersResultsNode: "catalogueSeriesMembersResults"
  });
}

export function createSeriesEditorState(elements, options = {}) {
  const mediaConfigLoader = options.mediaConfigLoader || loadCatalogueMediaConfig;
  return {
    config: null,
    mode: "single",
    seriesById: new Map(),
    workSearchById: new Map(),
    nextSuggestedSeriesId: "",
    currentLookup: null,
    currentSeriesId: "",
    currentRecord: null,
    currentRecordHash: "",
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    mediaConfig: mediaConfigLoader(elements.root),
    rebuildPending: false,
    pendingBuildExtraWorkIds: [],
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    root: elements.root,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    messageController: null,
    memberSeriesByWorkId: new Map(),
    baselineMemberSeriesByWorkId: new Map(),
    membersListController: null,
    membersActionsController: null,
    selectedMemberWorkId: "",
    searchNode: elements.searchNode,
    popupNode: elements.popupNode,
    popupListNode: elements.popupListNode,
    openButton: elements.openButton,
    newButton: elements.newButton,
    saveButton: elements.saveButton,
    deleteButton: elements.deleteButton,
    contextNode: createCatalogueEditorMessageRoleNode("catalogueSeriesContext", "context"),
    statusNode: elements.statusNode,
    warningNode: createCatalogueEditorMessageRoleNode("catalogueSeriesWarning", "warning"),
    resultNode: createCatalogueEditorMessageRoleNode("catalogueSeriesResult", "result"),
    buildImpactNode: null,
    membersActionsNode: elements.membersActionsNode,
    membersMetaNode: elements.membersMetaNode,
    membersResultsNode: elements.membersResultsNode
  };
}
