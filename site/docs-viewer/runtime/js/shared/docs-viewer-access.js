function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function createDocsViewerAccessProjection(options) {
  var settings = options || {};
  var routeConfig = settings.routeConfig || {};
  var routeAccess = routeConfig.access || {};
  var isDocsManagementRoute = Boolean(
    settings.isDocsManagementRoute != null
      ? settings.isDocsManagementRoute
      : routeAccess.isDocsManagementRoute
  );
  var allowManagement = isDocsManagementRoute;
  var allowScopeQuery = Boolean(
    settings.allowScopeQuery != null ? settings.allowScopeQuery : routeAccess.allowScopeQuery
  );
  return {
    isDocsManagementRoute: isDocsManagementRoute,
    allowManagement: allowManagement,
    allowScopeQuery: allowScopeQuery,
    publicReadOnly: !allowManagement,
    managementRequested: allowManagement,
    canLoadManagementUi: allowManagement,
    backendReachability: allowManagement ? "unknown" : "unavailable",
    writeAvailability: allowManagement ? "backend-gated" : "unavailable",
    hostedViewDefaults: {
      public: true,
      manage: allowManagement,
      manageLocal: allowManagement
    }
  };
}

export function hostedViewAccessAllowed(accessProjection, requirement) {
  var access = accessProjection || {};
  var required = cleanString(requirement || "public").toLowerCase();
  if (!required || required === "public") return true;
  if (required === "manage") return Boolean(access.allowManagement);
  if (required === "manage-local") return Boolean(access.allowManagement);
  return false;
}
