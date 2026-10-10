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

  return {
    docs: [],
    docsById: new Map(),
    childrenByParent: new Map(),
    payloadCache: new Map(),
    selectedDocId: "",
    indexSelectedDocId: "",
    documentTarget: null,
    displayedRecord: null,
    displayedDocId: "",
    displayedPayload: null,
    expandedDocIds: new Set(),
    requestId: 0,
    searchIndex: null,
    searchLoaded: false,
    searchRequestPromise: null,
    recentEntries: [],
    recentLoaded: false,
    recentRequestPromise: null,
    searchQuery: "",
    searchVisibleCount: options.searchBatchSize || 50,
    searchDebounceId: null,
    recentLimit: options.defaultRecentLimit || 20,
    docsViewerConfigLoaded: false,
    docsViewerConfigRequestPromise: null,
    workspaceLoaded: false,
    workspaceRequestPromise: null,
    activeConfig: null,
    publicViewerBaseUrl: "",
    viewerConfigLoaded: false,
    viewerConfigRequestPromise: null,
    uiStatuses: [],
    uiStatusByValue: new Map(),
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
    generatedDataCapabilities: null,
    reloadNonce: "",
    reloadExpectedDocId: "",
    pendingBusyCount: 0,
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
    workspaceConfig: stateDomain("workspaceConfig", "generated static config", state, [
      "docsViewerConfig",
      "docsViewerConfigLoaded",
      "docsViewerConfigRequestPromise",
      "workspaceLoaded",
      "workspaceRequestPromise",
      "activeConfig",
      "publicViewerBaseUrl",
      "viewerConfig",
      "viewerConfigLoaded",
      "viewerConfigRequestPromise",
      "uiStatuses",
      "uiStatusByValue",
      "recentLimit",
    ]),
    documentIndex: stateDomain("documentIndex", "generated static data or local generated-read service", state, [
      "docs",
      "docsById",
      "childrenByParent",
      "indexSelectedDocId",
      "expandedDocIds"
    ]),
    selectedDocument: stateDomain("selectedDocument", "generated static data or local generated-read service", state, [
      "selectedDocId",
      "displayedDocId",
      "documentTarget",
      "displayedRecord",
      "displayedPayload",
      "payloadCache",
      "requestId",
      "reloadNonce",
      "reloadExpectedDocId"
    ]),
    searchRecent: stateDomain("searchRecent", "generated static data or local generated-read service plus browser-only query state", state, [
      "searchIndex",
      "searchLoaded",
      "searchRequestPromise",
      "recentEntries",
      "recentLoaded",
      "recentRequestPromise",
      "searchQuery",
      "searchVisibleCount",
      "searchDebounceId",
      "recentLimit"
    ]),
    panelView: stateDomain("panelView", "browser-only UI state", state, [
      "viewState"
    ]),
    management: stateDomain("management", "management backend capability and write flow", state, [
      "managementChecked",
      "managementAvailable",
      "managementBusy",
      "managementCapabilities",
      "managementCapabilityCheckId",
      "managementCapabilityError",
      "managementMessage",
      "managementMessageIsError",
      "managementStatusOwnsViewerStatus"
    ]),
    generatedData: stateDomain("generatedData", "local generated-read service capability", state, [
      "generatedDataReadChecked",
      "generatedDataReadAvailable",
      "generatedDataReadRequestPromise",
      "generatedDataCapabilities"
    ]),
    busyStatus: stateDomain("busyStatus", "browser-only UI state", state, [
      "pendingBusyCount"
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
