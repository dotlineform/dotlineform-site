function stateDomain(name, authority, state, fieldNames) {
  var fields = fieldNames.slice();
  var domain = {
    name: name,
    authority: authority,
    fields: fields,
    has: function (fieldName) {
      return fields.indexOf(fieldName) !== -1;
    },
    get: function (fieldName) {
      if (!this.has(fieldName)) return undefined;
      return state[fieldName];
    },
    set: function (fieldName, value) {
      if (!this.has(fieldName)) return false;
      state[fieldName] = value;
      return true;
    },
    snapshot: function () {
      var output = {};
      fields.forEach(function (fieldName) {
        output[fieldName] = state[fieldName];
      });
      return output;
    }
  };

  fields.forEach(function (fieldName) {
    Object.defineProperty(domain, fieldName, {
      enumerable: true,
      get: function () {
        return state[fieldName];
      },
      set: function (value) {
        state[fieldName] = value;
      }
    });
  });

  return domain;
}

function createManagementTextDefaults() {
  return {
    checkingNote: "Checking manage mode...",
    clearSearchNote: "Clear search to manage the current doc.",
    serverNotConfiguredError: "Local docs-management server is not configured.",
    unavailableNote: "Manage mode unavailable: local docs server unavailable for this scope.",
    cancelButton: "Cancel",
    confirmContinueButton: "Continue",
    viewableAncestorPrompt: "Showing this doc also requires showing these parent docs:\n\n{titles}\n\nContinue?",
    viewableAncestorTitle: "Show parent docs",
    viewableDescendantPrompt: "Choose whether to show only this doc or include its descendant docs.",
    viewableDescendantTitle: "Show descendants",
    viewableDescendantSelectedLabel: "Selected doc only",
    viewableDescendantAllLabel: "Selected doc and descendants",
    viewableInvalidChoice: "Show update cancelled: expected `all` or `selected`.",
    createDocTitle: "New doc title",
    createChildDocTitle: "New child title",
    createSiblingDocTitle: "New sibling title",
    createDocLabel: "title",
    createDocDefaultTitle: "New Doc",
    createDocButton: "Create",
    deleteConfirmTitle: "Confirm delete",
    deleteConfirmButton: "Delete",
    metadataStatusLabel: "status",
    metadataStatusNoneOption: "<none>",
    metadataStatusSelectedSuffix: " (selected)",
    metadataNonViewableLabel: "non-viewable",
    metadataParentRootOption: "Root",
    metadataParentInvalid: "Select a parent from the search field suggestions or enter Root.",
    metadataParentNoMatches: "No matching parent docs.",
    docNonViewableEmoji: "\uD83D\uDEAB",
    statusMenuLabel: "Document status",
    statusPillSetLabel: "Set status: {label}",
    statusPillClearLabel: "Clear status: {label}",
    statusPillReadonlyLabel: "Status: {label}",
    statusPillSaving: "Saving status for {title}...",
    statusPillSaved: "Status saved.",
    statusPillFailed: "Status update failed.",
    settingsLoading: "Loading settings...",
    settingsEmpty: "No editable settings are available for this scope.",
    settingsSaving: "Saving settings...",
    settingsSaved: "Settings saved.",
    settingsLoadFailed: "Settings unavailable.",
    settingsSaveFailed: "Settings save failed.",
    scopeNewButton: "New scope",
    scopeDeleteMenuButton: "Delete scope",
    scopeCreateTitle: "New scope",
    scopeCreateIntro: "Create a Docs Viewer scope through the local management server.",
    scopeIdLabel: "scope id",
    scopeTitleLabel: "title",
    scopePublishingModeLabel: "publishing mode",
    scopePublicReadonlyMode: "public read-only scope",
    scopeLocalCommittedMode: "committed manage-mode scope",
    scopeLocalUncommittedMode: "local-only uncommitted scope",
    scopePublicReadonlyModeNote: "Creates a source root, scope config, read-only route, manifest record, and generated outputs when requested.",
    scopeLocalCommittedModeNote: "Creates tracked source, config, manifest, and non-public generated outputs under docs-viewer/generated/ when requested. No public route is created.",
    scopeLocalUncommittedModeNote: "Creates local-only scope files and records the result as uncommitted local drift. No public route is created.",
    scopeSourceRootLabel: "source root",
    scopeDefaultDocIdLabel: "default doc id",
    scopePublicRoutePathLabel: "public route path",
    scopeWriteGeneratedLabel: "write generated outputs immediately",
    scopeBuildSearchLabel: "build inline search",
    scopePreviewButton: "Preview",
    scopeSaveButton: "Save",
    scopeDeleteButton: "Delete",
    scopeResultOkButton: "OK",
    scopeCreateRequiredMessage: "Enter the required scope fields.",
    scopeCreateRouteRequiredMessage: "Enter a public route path for public read-only scopes.",
    scopeCreatePreviewing: "Previewing new scope...",
    scopeCreatePreviewTitle: "Preview new scope",
    scopeCreateSaving: "Saving new scope...",
    scopeCreateFailed: "New scope failed.",
    scopeCreateResultTitle: "Scope created",
    scopeDeleteTitle: "Delete scope",
    scopeDeleteIntro: "Select the user-created scope to delete.",
    scopeDeleteTargetLabel: "scope",
    scopeDeleteRequiredMessage: "Select a scope to delete.",
    scopeDeleteNoTargets: "No user-created scopes are eligible for deletion.",
    scopeDeletePreviewing: "Previewing scope deletion...",
    scopeDeletePreviewTitle: "Preview delete scope",
    scopeDeleteDeleting: "Deleting scope...",
    scopeDeleteFailed: "Delete scope failed.",
    scopeDeleteBlocked: "Delete scope is blocked.",
    scopeDeleteBlockedTitle: "Delete blocked",
    scopeDeleteResultTitle: "Scope deleted",
    importCancelButton: "Cancel",
    copyLinkLabel: "Copy Link",
    copyLinkStatus: "Copied link for {title}.",
    copyLinkFailed: "Copy link failed."
  };
}

function createStateDefaults(settings) {
  var options = settings || {};
  var panelLayout = options.panelLayout || null;
  var windowRef = options.window || {};

  return {
    allDocs: [],
    allDocsById: new Map(),
    docs: [],
    docsById: new Map(),
    childrenByParent: new Map(),
    payloadCache: new Map(),
    selectedDocId: "",
    expandedDocIds: new Set(),
    requestId: 0,
    searchEntries: [],
    searchLoaded: false,
    searchRequestPromise: null,
    recentEntries: [],
    recentLoaded: false,
    recentRequestPromise: null,
    searchQuery: "",
    searchVisibleCount: options.searchBatchSize || 50,
    searchDebounceId: null,
    searchRouteActive: false,
    recentModeActive: false,
    recentLimit: options.defaultRecentLimit || 10,
    docsViewerConfigLoaded: false,
    docsViewerConfigRequestPromise: null,
    scopeConfigs: [],
    scopeConfigsById: new Map(),
    defaultScopeId: "",
    viewerConfigLoaded: false,
    viewerConfigRequestPromise: null,
    uiStatuses: [],
    uiStatusByValue: new Map(),
    statusMenuOpen: false,
    bookmarks: [],
    bookmarksLoaded: false,
    bookmarkSupport: Boolean(windowRef.indexedDB),
    editingBookmarkKey: "",
    pendingBookmarkFocusKey: "",
    managementMode: false,
    managementChecked: false,
    managementAvailable: false,
    managementBusy: false,
    managementCapabilities: null,
    managementCapabilityCheckId: 0,
    managementMessage: "",
    managementMessageIsError: false,
    managementStatusOwnsViewerStatus: false,
    generatedDataReadChecked: false,
    generatedDataReadAvailable: false,
    generatedDataReadRequestPromise: null,
    managementText: createManagementTextDefaults(),
    showNonViewable: true,
    reloadNonce: "",
    reloadExpectedDocId: "",
    pendingBusyCount: 0,
    metadataEditingDocId: "",
    metadataRestoreFocusId: "",
    nonLoadableDocIds: new Set(),
    manageOnlyTreeRootIds: new Set(),
    showUpdatedDate: true,
    hostedViews: options.hostedViewRegistry || null,
    indexPanelState: panelLayout && typeof panelLayout.indexPanelState === "function"
      ? panelLayout.indexPanelState()
      : null,
    viewState: panelLayout && typeof panelLayout.projectViewState === "function"
      ? panelLayout.projectViewState()
      : null
  };
}

function createStateDomains(state, settings) {
  var routeContext = settings.routeContext || {};
  var accessProjection = routeContext.access || {};

  return {
    routeSession: {
      name: "routeSession",
      authority: "route config and current browser URL",
      routeContext: routeContext,
      accessProjection: accessProjection,
      get managementMode() {
        return Boolean(state.managementMode);
      },
      set managementMode(value) {
        state.managementMode = Boolean(value);
      },
      publicReadOnly: Boolean(accessProjection.publicReadOnly),
      canLoadManagementUi: Boolean(accessProjection.canLoadManagementUi),
      updateRouteContext: function (nextRouteContext) {
        this.routeContext = nextRouteContext || {};
        this.accessProjection = this.routeContext.access || {};
        this.publicReadOnly = Boolean(this.accessProjection.publicReadOnly);
        this.canLoadManagementUi = Boolean(this.accessProjection.canLoadManagementUi);
      }
    },
    scopeConfig: stateDomain("scopeConfig", "generated static config", state, [
      "docsViewerConfig",
      "docsViewerConfigLoaded",
      "docsViewerConfigRequestPromise",
      "scopeConfigs",
      "scopeConfigsById",
      "defaultScopeId",
      "viewerConfig",
      "viewerConfigLoaded",
      "viewerConfigRequestPromise",
      "uiStatuses",
      "uiStatusByValue",
      "recentLimit",
      "showUpdatedDate",
      "managementText"
    ]),
    documentIndex: stateDomain("documentIndex", "generated static data or local generated-read service", state, [
      "allDocs",
      "allDocsById",
      "docs",
      "docsById",
      "childrenByParent",
      "expandedDocIds",
      "nonLoadableDocIds",
      "manageOnlyTreeRootIds",
      "showNonViewable",
      "showUpdatedDate",
      "uiStatusByValue"
    ]),
    selectedDocument: stateDomain("selectedDocument", "generated static data or local generated-read service", state, [
      "selectedDocId",
      "payloadCache",
      "requestId",
      "reloadNonce",
      "reloadExpectedDocId"
    ]),
    searchRecent: stateDomain("searchRecent", "generated static data or local generated-read service plus browser-only query state", state, [
      "searchEntries",
      "searchLoaded",
      "searchRequestPromise",
      "recentEntries",
      "recentLoaded",
      "recentRequestPromise",
      "searchQuery",
      "searchVisibleCount",
      "searchDebounceId",
      "searchRouteActive",
      "recentModeActive",
      "recentLimit"
    ]),
    bookmarks: stateDomain("bookmarks", "browser storage", state, [
      "bookmarks",
      "bookmarksLoaded",
      "bookmarkSupport",
      "editingBookmarkKey",
      "pendingBookmarkFocusKey"
    ]),
    panelView: stateDomain("panelView", "browser-only UI state", state, [
      "indexPanelState",
      "viewState",
      "hostedViews",
      "expandedDocIds"
    ]),
    management: stateDomain("management", "management backend capability and write flow", state, [
      "managementMode",
      "managementChecked",
      "managementAvailable",
      "managementBusy",
      "managementCapabilities",
      "managementCapabilityCheckId",
      "managementMessage",
      "managementMessageIsError",
      "managementStatusOwnsViewerStatus",
      "metadataEditingDocId",
      "metadataRestoreFocusId",
      "statusMenuOpen",
      "managementText"
    ]),
    generatedData: stateDomain("generatedData", "local generated-read service capability", state, [
      "generatedDataReadChecked",
      "generatedDataReadAvailable",
      "generatedDataReadRequestPromise",
      "managementCapabilities",
      "reloadNonce",
      "reloadExpectedDocId"
    ]),
    busyStatus: stateDomain("busyStatus", "browser-only UI state", state, [
      "pendingBusyCount",
      "managementStatusOwnsViewerStatus",
      "managementMessage",
      "managementMessageIsError"
    ])
  };
}

export function createDocsViewerAppSession(options) {
  var settings = options || {};
  var state = createStateDefaults(settings);
  var domains = createStateDomains(state, settings);

  return {
    state: state,
    domains: domains
  };
}
