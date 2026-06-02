import {
  collectRequiredElements,
  createCatalogueEditorRouteStateOptions
} from "./catalogue-editor-route-boot.js";
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
    readonlyNode: "catalogueSeriesReadonly",
    summaryNode: "catalogueSeriesSummary",
    readinessNode: "catalogueSeriesReadiness",
    runtimeStateNode: "catalogueSeriesRuntimeState",
    buildImpactNode: "catalogueSeriesBuildImpact",
    searchNode: "catalogueSeriesSearch",
    popupNode: "catalogueSeriesPopup",
    popupListNode: "catalogueSeriesPopupList",
    openButton: "catalogueSeriesOpen",
    newButton: "catalogueSeriesNew",
    saveButton: "catalogueSeriesSave",
    publicationButton: "catalogueSeriesPublication",
    deleteButton: "catalogueSeriesDelete",
    saveModeNode: "catalogueSeriesSaveMode",
    contextNode: "catalogueSeriesContext",
    statusNode: "catalogueSeriesStatus",
    warningNode: "catalogueSeriesWarning",
    resultNode: "catalogueSeriesResult",
    metaNode: "catalogueSeriesMeta",
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
    readonlyNodes: new Map(),
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
    saveModeNode: elements.saveModeNode,
    contextNode: elements.contextNode,
    statusNode: elements.statusNode,
    warningNode: elements.warningNode,
    resultNode: elements.resultNode,
    summaryNode: elements.summaryNode,
    readinessNode: elements.readinessNode,
    runtimeStateNode: elements.runtimeStateNode,
    buildImpactNode: elements.buildImpactNode,
    metaNode: elements.metaNode,
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
