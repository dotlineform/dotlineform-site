import {
  appendAssetVersion
} from "./docs-viewer-data.js";
import {
  createDocsViewerAccessProjection
} from "./docs-viewer-access.js";
import {
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
  var routeConfig = resolveDocsViewerRouteConfig({
    root: root,
    routeConfig: settings.routeConfig
  });
  var routeViewerBaseUrl = routeConfig.viewerBaseUrl;
  var viewerBaseUrl = routeViewerBaseUrl || locationPathname(windowRef);
  var access = createDocsViewerAccessProjection({
    routeConfig: routeConfig,
    managementModeValue: settings.managementModeValue,
    search: locationSearch(windowRef)
  });
  var allowManagement = access.allowManagement;
  var managementBaseUrl = allowManagement ? cleanBaseUrl(routeConfig.access.managementBaseUrl) : "";
  var generatedBaseUrl = cleanBaseUrl(routeConfig.generatedBaseUrl) || managementBaseUrl;
  var context = {
    root: root,
    routeConfig: routeConfig,
    access: access,
    allowManagement: allowManagement,
    allowScopeQuery: access.allowScopeQuery,
    docsViewerConfigUrl: routeConfig.docsViewerConfigUrl,
    routeViewerBaseUrl: routeViewerBaseUrl,
    indexUrl: appendAssetVersion(routeConfig.indexUrl, assetVersion),
    viewerBaseUrl: viewerBaseUrl,
    viewerScope: routeConfig.defaultScopeId,
    includeScopeParam: Boolean(routeConfig.includeScopeParam),
    defaultRouteDocId: routeConfig.defaultDocId,
    viewerPathname: viewerPathname(viewerBaseUrl, windowRef),
    searchIndexUrl: appendAssetVersion(routeConfig.searchIndexUrl, assetVersion),
    uiTextUrl: routeConfig.uiTextUrl,
    reportRegistryUrl: routeConfig.reportRegistryUrl,
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
  nextContext.routeConfig = Object.assign({}, current.routeConfig || {}, {
    defaultDocId: nextContext.defaultRouteDocId,
    defaultScopeId: nextContext.viewerScope,
    indexUrl: nextContext.indexUrl,
    searchIndexUrl: nextContext.searchIndexUrl,
    viewerBaseUrl: nextContext.viewerBaseUrl
  });
  nextContext.bookmarkScope = nextContext.viewerScope || nextContext.viewerPathname || "docs";
  return nextContext;
}
