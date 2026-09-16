import { savedStateOwner } from "./docs-viewer-saved-state.js";

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
    publicPreviewBase: routeConfig.publicPreviewBase,
    studioBaseUrl: routeConfig.studioBaseUrl,
    routeViewerBaseUrl: routeViewerBaseUrl,
    indexTreeUrl: appendAssetVersion(routeConfig.indexTreeUrl, assetVersion),
    recentUrl: appendAssetVersion(routeConfig.recentUrl, assetVersion),
    recentBasis: routeConfig.recentBasis,
    viewerBaseUrl: viewerBaseUrl,
    viewerStage: routeConfig.appKind === "manage" ? (new URLSearchParams(locationSearch(windowRef)).get("stage") || routeConfig.defaultStage) : "",
    preserveQueryParams: routeConfig.preserveQueryParams || [],
    defaultRouteDocId: "",
    viewerPathname: resolvedViewerPathname,
    searchIndexUrl: appendAssetVersion(routeConfig.searchIndexUrl, assetVersion),
    collections: [],
    collectionsById: new Map(),
    reportRegistryUrl: routeConfig.reportRegistryUrl
  };
  context.bookmarkOwner = savedStateOwner(routeConfig.appKind, context.viewerStage);
  var routeParams = new URLSearchParams(locationSearch(windowRef));
  context.openImportOnLoad = context.isDocsManagementRoute && routeParams.get("import") === "1";
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
    viewerStage: cleanString(values && values.viewerStage),
    indexTreeUrl: values && values.indexTreeUrl ? values.indexTreeUrl : "",
    recentUrl: values && values.recentUrl ? values.recentUrl : "",
    searchIndexUrl: values && values.searchIndexUrl ? values.searchIndexUrl : "",
    collections: Array.isArray(values && values.collections) ? values.collections : [],
    collectionsById: values && values.collectionsById instanceof Map ? values.collectionsById : new Map(),
    defaultRouteDocId: cleanString(values && values.defaultRouteDocId),
    viewerBaseUrl: nextViewerBaseUrl,
    viewerPathname: values && values.viewerPathname ? values.viewerPathname : viewerPathname(nextViewerBaseUrl, windowRef)
  });
  nextContext.routeConfig = Object.assign({}, current.routeConfig || {}, {
    indexTreeUrl: nextContext.indexTreeUrl,
    recentUrl: nextContext.recentUrl,
    searchIndexUrl: nextContext.searchIndexUrl,
    collections: nextContext.collections,
    viewerBaseUrl: nextContext.viewerBaseUrl
  });
  nextContext.bookmarkOwner = savedStateOwner(nextContext.routeConfig.appKind, nextContext.viewerStage);
  if (nextContext.viewerStage) {
    nextContext.preserveQueryParams = Array.from(new Set([].concat(current.preserveQueryParams || [], ["stage"])));
  }
  return nextContext;
}
