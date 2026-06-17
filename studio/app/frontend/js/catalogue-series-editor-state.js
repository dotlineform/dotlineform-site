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
import {
  getSeriesTypeOptions
} from "./catalogue-series-fields.js";

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
    publicationButton: "catalogueSeriesPublication",
    deleteButton: "catalogueSeriesDelete",
    statusNode: "catalogueSeriesStatus",
    metaNode: "catalogueSeriesMeta",
    previewNode: "catalogueSeriesSidePanel",
    membersHeadingNode: "catalogueSeriesMembersHeading",
    memberSearchRowNode: "catalogueSeriesMemberSearchRow",
    memberSearchNode: "catalogueSeriesMemberSearch",
    memberSearchMetaNode: "catalogueSeriesMemberSearchMeta",
    memberAddNode: "catalogueSeriesMemberAdd",
    memberAddButton: "catalogueSeriesMemberAddButton",
    membersMetaNode: "catalogueSeriesMembersMeta",
    membersStatusNode: "catalogueSeriesMembersStatus",
    membersResultsNode: "catalogueSeriesMembersResults"
  });
}

export function createSeriesEditorState(elements, options = {}) {
  const seriesTypeOptions = options.seriesTypeOptions || getSeriesTypeOptions();
  const mediaConfigLoader = options.mediaConfigLoader || loadCatalogueMediaConfig;
  return {
    config: null,
    mode: "single",
    seriesById: new Map(),
    workSearchById: new Map(),
    seriesTypeOptions,
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
    memberSeriesIdsByWorkId: new Map(),
    baselineMemberSeriesIdsByWorkId: new Map(),
    searchNode: elements.searchNode,
    popupNode: elements.popupNode,
    popupListNode: elements.popupListNode,
    openButton: elements.openButton,
    newButton: elements.newButton,
    saveButton: elements.saveButton,
    publicationButton: elements.publicationButton,
    deleteButton: elements.deleteButton,
    contextNode: createCatalogueEditorMessageRoleNode("catalogueSeriesContext", "context"),
    statusNode: elements.statusNode,
    warningNode: createCatalogueEditorMessageRoleNode("catalogueSeriesWarning", "warning"),
    resultNode: createCatalogueEditorMessageRoleNode("catalogueSeriesResult", "result"),
    buildImpactNode: null,
    metaNode: elements.metaNode,
    previewNode: elements.previewNode,
    memberSearchRowNode: elements.memberSearchRowNode,
    memberSearchNode: elements.memberSearchNode,
    memberSearchMetaNode: elements.memberSearchMetaNode,
    memberAddNode: elements.memberAddNode,
    memberAddButton: elements.memberAddButton,
    membersMetaNode: elements.membersMetaNode,
    membersStatusNode: elements.membersStatusNode,
    membersResultsNode: elements.membersResultsNode
  };
}
