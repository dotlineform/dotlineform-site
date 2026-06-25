import {
  appendAssetVersion
} from "./docs-viewer-asset-url.js";
import {
  createDocsViewerAccessProjection
} from "./docs-viewer-access.js";
import {
  isDocsManagementRoutePath,
  resolveDocsViewerRouteConfig
} from "./docs-viewer-route-config.js";

function cleanString(value) {
  return String(value || "").trim();
}

function cleanBaseUrl(value) {
  return cleanString(value).replace(/\/+$/, "");
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

export function createDocsViewerRouteContext(options) {
  var settings = options || {};
  var root = settings.root || null;
  var windowRef = settings.window || defaultWindowRef();
  var assetVersion = cleanString(settings.assetVersion);
  var routeConfig = settings.resolvedRouteConfig || resolveDocsViewerRouteConfig({
    root: root,
    document: settings.document,
    routeConfig: settings.routeConfig,
    routeConfigSource: settings.routeConfigSource
  });
  var routeViewerBaseUrl = routeConfig.viewerBaseUrl;
  var viewerBaseUrl = routeViewerBaseUrl || locationPathname(windowRef);
  var resolvedViewerPathname = viewerPathname(viewerBaseUrl, windowRef);
  var docsManagementRoute = isDocsManagementRoutePath(resolvedViewerPathname);
  var access = createDocsViewerAccessProjection({
    routeConfig: routeConfig,
    isDocsManagementRoute: docsManagementRoute
  });
  var allowManagement = access.allowManagement;
  var managementBaseUrl = allowManagement ? cleanBaseUrl(routeConfig.access.managementBaseUrl) : "";
  var generatedBaseUrl = allowManagement ? (cleanBaseUrl(routeConfig.generatedBaseUrl) || managementBaseUrl) : "";
  var context = {
    root: root,
    routeConfig: routeConfig,
    access: access,
    isDocsManagementRoute: docsManagementRoute,
    allowManagement: allowManagement,
    allowScopeQuery: access.allowScopeQuery,
    docsViewerConfigUrl: routeConfig.docsViewerConfigUrl,
    routeViewerBaseUrl: routeViewerBaseUrl,
    indexTreeUrl: appendAssetVersion(routeConfig.indexTreeUrl, assetVersion),
    recentlyAddedUrl: appendAssetVersion(routeConfig.recentlyAddedUrl, assetVersion),
    viewerBaseUrl: viewerBaseUrl,
    viewerScope: routeConfig.defaultScopeId,
    includeScopeParam: Boolean(routeConfig.includeScopeParam),
    defaultRouteDocId: "",
    viewerPathname: resolvedViewerPathname,
    searchIndexUrl: appendAssetVersion(routeConfig.searchIndexUrl, assetVersion),
    subScopes: [],
    subScopesById: new Map(),
    reportRegistryUrl: routeConfig.reportRegistryUrl,
    managementBaseUrl: managementBaseUrl,
    generatedBaseUrl: generatedBaseUrl
  };
  context.bookmarkScope = context.viewerScope || context.viewerPathname || "docs";
  context.openImportOnLoad = context.isDocsManagementRoute && new URLSearchParams(locationSearch(windowRef)).get("import") === "1";
  return context;
}

export function updateDocsViewerRouteContext(context, values, options) {
  var current = context || {};
  var settings = options || {};
  var windowRef = settings.window || defaultWindowRef();
  var nextViewerBaseUrl = cleanString(values && values.viewerBaseUrl) || current.viewerBaseUrl || locationPathname(windowRef);
  var nextContext = Object.assign({}, current, {
    viewerScope: cleanString(values && values.viewerScope),
    indexTreeUrl: values && values.indexTreeUrl ? values.indexTreeUrl : "",
    recentlyAddedUrl: values && values.recentlyAddedUrl ? values.recentlyAddedUrl : "",
    searchIndexUrl: values && values.searchIndexUrl ? values.searchIndexUrl : "",
    subScopes: Array.isArray(values && values.subScopes) ? values.subScopes : [],
    subScopesById: values && values.subScopesById instanceof Map ? values.subScopesById : new Map(),
    defaultRouteDocId: cleanString(values && values.defaultRouteDocId),
    viewerBaseUrl: nextViewerBaseUrl,
    includeScopeParam: Boolean(values && values.includeScopeParam),
    viewerPathname: values && values.viewerPathname ? values.viewerPathname : viewerPathname(nextViewerBaseUrl, windowRef)
  });
  nextContext.routeConfig = Object.assign({}, current.routeConfig || {}, {
    defaultScopeId: nextContext.viewerScope,
    indexTreeUrl: nextContext.indexTreeUrl,
    recentlyAddedUrl: nextContext.recentlyAddedUrl,
    searchIndexUrl: nextContext.searchIndexUrl,
    subScopes: nextContext.subScopes,
    viewerBaseUrl: nextContext.viewerBaseUrl
  });
  nextContext.bookmarkScope = nextContext.viewerScope || nextContext.viewerPathname || "docs";
  return nextContext;
}
