import {
  appendAssetVersion
} from "./docs-viewer-data.js";

function cleanString(value) {
  return String(value || "").trim();
}

function cleanBaseUrl(value) {
  return cleanString(value).replace(/\/+$/, "");
}

function datasetFlag(root, name) {
  return Boolean(root && root.dataset && root.dataset[name] === "true");
}

function locationSearch(windowRef) {
  return windowRef && windowRef.location ? windowRef.location.search : "";
}

function locationPathname(windowRef) {
  return windowRef && windowRef.location ? windowRef.location.pathname : "";
}

function locationOrigin(windowRef) {
  return windowRef && windowRef.location ? windowRef.location.origin : "";
}

function viewerPathname(viewerBaseUrl, windowRef) {
  try {
    return new URL(viewerBaseUrl, locationOrigin(windowRef)).pathname;
  } catch (error) {
    return locationPathname(windowRef);
  }
}

function defaultWindowRef() {
  return typeof window !== "undefined" ? window : null;
}

function routeAccessFlags(options) {
  var settings = options || {};
  var allowManagement = Boolean(settings.allowManagement);
  var allowScopeQuery = Boolean(settings.allowScopeQuery);
  var searchParams = new URLSearchParams(settings.search || "");
  var requestedMode = allowManagement ? cleanString(searchParams.get("mode")) : "";
  var managementModeValue = cleanString(settings.managementModeValue) || "manage";
  return {
    allowManagement: allowManagement,
    allowScopeQuery: allowScopeQuery,
    publicReadOnly: !allowManagement,
    requestedMode: requestedMode,
    managementModeValue: managementModeValue,
    managementRequested: allowManagement && requestedMode === managementModeValue,
    importRequested: allowManagement && searchParams.get("import") === "1"
  };
}

export function createDocsViewerRouteContext(options) {
  var settings = options || {};
  var root = settings.root || null;
  var windowRef = settings.window || defaultWindowRef();
  var assetVersion = cleanString(settings.assetVersion);
  var routeViewerBaseUrl = cleanString(root && root.dataset ? root.dataset.viewerBaseUrl : "");
  var viewerBaseUrl = routeViewerBaseUrl || locationPathname(windowRef);
  var allowManagement = datasetFlag(root, "allowManagement");
  var managementBaseUrl = allowManagement ? cleanBaseUrl(root && root.dataset ? root.dataset.managementBaseUrl : "") : "";
  var generatedBaseUrl = cleanBaseUrl(root && root.dataset ? root.dataset.generatedBaseUrl : "") || managementBaseUrl;
  var context = {
    root: root,
    access: routeAccessFlags({
      allowManagement: allowManagement,
      allowScopeQuery: datasetFlag(root, "allowScopeQuery"),
      managementModeValue: settings.managementModeValue,
      search: locationSearch(windowRef)
    }),
    allowManagement: allowManagement,
    allowScopeQuery: datasetFlag(root, "allowScopeQuery"),
    docsViewerConfigUrl: cleanString(root && root.dataset ? root.dataset.docsViewerConfigUrl : ""),
    routeViewerBaseUrl: routeViewerBaseUrl,
    indexUrl: appendAssetVersion(root && root.dataset ? root.dataset.indexUrl : "", assetVersion),
    viewerBaseUrl: viewerBaseUrl,
    viewerScope: cleanString(root && root.dataset ? root.dataset.viewerScope : ""),
    includeScopeParam: datasetFlag(root, "includeScopeParam"),
    defaultRouteDocId: cleanString(root && root.dataset ? root.dataset.defaultDocId : ""),
    viewerPathname: viewerPathname(viewerBaseUrl, windowRef),
    searchIndexUrl: appendAssetVersion(root && root.dataset ? root.dataset.searchIndexUrl : "", assetVersion),
    uiTextUrl: cleanString(root && root.dataset ? root.dataset.uiTextUrl : ""),
    reportRegistryUrl: cleanString(root && root.dataset ? root.dataset.reportRegistryUrl : ""),
    managementBaseUrl: managementBaseUrl,
    generatedBaseUrl: generatedBaseUrl
  };
  context.bookmarkScope = context.viewerScope || context.viewerPathname || "docs";
  context.openImportOnLoad = context.access.importRequested;
  return context;
}

export function updateDocsViewerRouteContext(context, values, options) {
  var current = context || {};
  var settings = options || {};
  var windowRef = settings.window || defaultWindowRef();
  var nextViewerBaseUrl = cleanString(values && values.viewerBaseUrl) || current.viewerBaseUrl || locationPathname(windowRef);
  var nextContext = Object.assign({}, current, {
    viewerScope: cleanString(values && values.viewerScope),
    indexUrl: values && values.indexUrl ? values.indexUrl : "",
    searchIndexUrl: values && values.searchIndexUrl ? values.searchIndexUrl : "",
    defaultRouteDocId: cleanString(values && values.defaultRouteDocId),
    viewerBaseUrl: nextViewerBaseUrl,
    includeScopeParam: Boolean(values && values.includeScopeParam),
    viewerPathname: values && values.viewerPathname ? values.viewerPathname : viewerPathname(nextViewerBaseUrl, windowRef)
  });
  nextContext.bookmarkScope = nextContext.viewerScope || nextContext.viewerPathname || "docs";
  return nextContext;
}
