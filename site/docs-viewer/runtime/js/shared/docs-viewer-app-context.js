import {
  appendAssetVersion
} from "./docs-viewer-asset-url.js";
import {
  createDocsViewerAccessProjection,
  normalizeDocsViewerAppKind
} from "./docs-viewer-access.js";
import {
  isDocsManagementRoutePath,
  resolveDocsViewerRouteConfig
} from "./docs-viewer-route-config.js";
import {
  createDocsViewerServiceAvailability
} from "./docs-viewer-service-context.js";

function cleanString(value) {
  return String(value || "").trim();
}

function safeReviewPackageId(value) {
  var packageId = cleanString(value);
  return /^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(packageId) ? packageId : "";
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
    appKind: settings.appKind,
    routeConfig: settings.routeConfig,
    routeConfigSource: settings.routeConfigSource
  });
  var routeViewerBaseUrl = routeConfig.viewerBaseUrl;
  var viewerBaseUrl = routeViewerBaseUrl || locationPathname(windowRef);
  var resolvedViewerPathname = viewerPathname(viewerBaseUrl, windowRef);
  var docsManagementRoute = isDocsManagementRoutePath(resolvedViewerPathname);
  var appContext = createDocsViewerAppContext({
    appKind: settings.appKind || routeConfig.appKind,
    routeConfig: routeConfig
  });
  var context = {
    root: root,
    routeConfig: routeConfig,
    appContext: appContext,
    isDocsManagementRoute: docsManagementRoute,
    docsViewerConfigUrl: routeConfig.docsViewerConfigUrl,
    routeViewerBaseUrl: routeViewerBaseUrl,
    indexTreeUrl: appendAssetVersion(routeConfig.indexTreeUrl, assetVersion),
    recentlyAddedUrl: appendAssetVersion(routeConfig.recentlyAddedUrl, assetVersion),
    viewerBaseUrl: viewerBaseUrl,
    viewerScope: routeConfig.defaultScopeId,
    includeScopeParam: Boolean(routeConfig.includeScopeParam),
    preserveQueryParams: routeConfig.preserveQueryParams || [],
    defaultRouteDocId: "",
    viewerPathname: resolvedViewerPathname,
    searchIndexUrl: appendAssetVersion(routeConfig.searchIndexUrl, assetVersion),
    subScopes: [],
    subScopesById: new Map(),
    reportRegistryUrl: routeConfig.reportRegistryUrl
  };
  context.bookmarkScope = context.viewerScope || context.viewerPathname || "docs";
  var routeParams = new URLSearchParams(locationSearch(windowRef));
  context.openImportOnLoad = context.isDocsManagementRoute && routeParams.get("import") === "1";
  context.importReviewPackageId = context.openImportOnLoad
    ? safeReviewPackageId(routeParams.get("review_package"))
    : "";
  return context;
}

export function createDocsViewerAppContext(options) {
  var settings = options || {};
  var routeConfig = settings.routeConfig || {};
  var kind = normalizeDocsViewerAppKind(settings.appKind || routeConfig.appKind);
  var routeAccess = createDocsViewerAccessProjection({
    appKind: kind,
    routeAccess: routeConfig.access
  });
  return {
    kind: kind,
    routeAccess: routeAccess,
    featurePolicy: routeConfig.features || {},
    serviceAvailability: createDocsViewerServiceAvailability(routeConfig.services),
    backendCapabilities: null
  };
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
