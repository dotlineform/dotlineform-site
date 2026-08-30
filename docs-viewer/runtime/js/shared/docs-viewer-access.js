function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export const DOCS_VIEWER_APP_KINDS = Object.freeze({
  PUBLIC: "public",
  MANAGE: "manage",
  REVIEW: "review"
});

export function normalizeDocsViewerAppKind(value) {
  var kind = cleanString(value).toLowerCase();
  if (
    kind === DOCS_VIEWER_APP_KINDS.PUBLIC
    || kind === DOCS_VIEWER_APP_KINDS.MANAGE
    || kind === DOCS_VIEWER_APP_KINDS.REVIEW
  ) {
    return kind;
  }
  throw new Error("Docs Viewer app kind must be public, manage, or review.");
}

export function createDocsViewerAccessProjection(options) {
  var settings = options || {};
  var appKind = normalizeDocsViewerAppKind(settings.appKind);
  var routeAccess = settings.routeAccess || {};
  return {
    appKind: appKind,
    allowScopeQuery: Boolean(routeAccess.allowScopeQuery),
    managementUi: appKind === DOCS_VIEWER_APP_KINDS.MANAGE && Boolean(routeAccess.managementUi)
  };
}
