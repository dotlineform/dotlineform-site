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
    configuredScopesLoaded: false,
    configuredScopesRequestPromise: null,
    scopeConfigs: [],
    scopeConfigsById: new Map(),
    defaultScopeId: "",
    viewerConfigLoaded: false,
    viewerConfigRequestPromise: null,
    uiStatuses: [],
    uiStatusByValue: new Map(),
    bookmarks: [],
    bookmarksLoaded: false,
    bookmarkSupport: Boolean(windowRef.indexedDB),
    editingBookmarkKey: "",
    pendingBookmarkFocusKey: "",
    managementContext: false,
    managementChecked: false,
    managementAvailable: false,
    managementBusy: false,
    managementCapabilities: null,
    managementCapabilityCheckId: 0,
    managementCapabilityError: "",
    managementMessage: "",
    managementMessageIsError: false,
    managementStatusOwnsViewerStatus: false,
    generatedDataReadChecked: false,
    generatedDataReadAvailable: false,
    generatedDataReadRequestPromise: null,
    showNonViewable: true,
    docNonViewableEmoji: "\uD83D\uDEAB",
    reloadNonce: "",
    reloadExpectedDocId: "",
    pendingBusyCount: 0,
    metadataEditingDocId: "",
    metadataRestoreFocusId: "",
    nonLoadableDocIds: new Set(),
    manageOnlyTreeRootIds: new Set(),
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
  var appContext = routeContext.appContext || {};
  var routeAccess = appContext.routeAccess || {};

  return {
    routeSession: {
      name: "routeSession",
      authority: "route config and current browser URL",
      routeContext: routeContext,
      appContext: appContext,
      get managementContext() {
        return Boolean(state.managementContext);
      },
      set managementContext(value) {
        state.managementContext = Boolean(value);
      },
      appKind: appContext.kind || "",
      managementUi: Boolean(routeAccess.managementUi),
      updateRouteContext: function (nextRouteContext) {
        this.routeContext = nextRouteContext || {};
        this.appContext = this.routeContext.appContext || {};
        this.appKind = this.appContext.kind || "";
        this.managementUi = Boolean(this.appContext.routeAccess && this.appContext.routeAccess.managementUi);
      }
    },
    scopeConfig: stateDomain("scopeConfig", "generated static config", state, [
      "docsViewerConfig",
      "docsViewerConfigLoaded",
      "docsViewerConfigRequestPromise",
      "configuredScopesLoaded",
      "configuredScopesRequestPromise",
      "scopeConfigs",
      "scopeConfigsById",
      "defaultScopeId",
      "viewerConfig",
      "viewerConfigLoaded",
      "viewerConfigRequestPromise",
      "uiStatuses",
      "uiStatusByValue",
      "recentLimit",
      "docNonViewableEmoji"
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
      "managementContext",
      "managementChecked",
      "managementAvailable",
      "managementBusy",
      "managementCapabilities",
      "managementCapabilityCheckId",
      "managementCapabilityError",
      "managementMessage",
      "managementMessageIsError",
      "managementStatusOwnsViewerStatus",
      "metadataEditingDocId",
      "metadataRestoreFocusId",
      "docNonViewableEmoji"
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
