function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function locationSearch(windowRef) {
  return windowRef && windowRef.location ? windowRef.location.search : "";
}

function normalizeRouteType(value, allowManagement) {
  var routeType = cleanString(value).toLowerCase();
  if (routeType === "manage" || routeType === "public") return routeType;
  return allowManagement ? "manage" : "public";
}

export function createDocsViewerAccessProjection(options) {
  var settings = options || {};
  var routeConfig = settings.routeConfig || {};
  var routeAccess = routeConfig.access || {};
  var allowManagement = Boolean(
    settings.allowManagement != null ? settings.allowManagement : routeAccess.allowManagement
  );
  var allowScopeQuery = Boolean(
    settings.allowScopeQuery != null ? settings.allowScopeQuery : routeAccess.allowScopeQuery
  );
  var searchParams = new URLSearchParams(settings.search || locationSearch(settings.window));
  var managementModeValue = cleanString(settings.managementModeValue || routeAccess.managementModeValue) || "manage";
  var requestedMode = allowManagement ? cleanString(searchParams.get("mode")) : "";
  var routeType = normalizeRouteType(settings.routeType || routeConfig.routeType, allowManagement);
  var managementRequested = allowManagement && routeType === "manage";
  return {
    routeType: routeType,
    allowManagement: allowManagement,
    allowScopeQuery: allowScopeQuery,
    publicReadOnly: !allowManagement,
    requestedMode: requestedMode,
    managementModeValue: managementModeValue,
    managementRequested: managementRequested,
    importRequested: managementRequested && searchParams.get("import") === "1",
    canLoadManagementUi: allowManagement && routeType === "manage",
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
