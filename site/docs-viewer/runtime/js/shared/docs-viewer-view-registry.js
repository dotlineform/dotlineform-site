import {
  normalizeHostedViewCapabilities
} from "./docs-viewer-hosted-view-capabilities.js";
import {
  docsViewerRouteFeatureEnabled
} from "./docs-viewer-route-features.js";

var PANELS = ["index", "main", "info"];
var APP_KINDS = ["public", "manage", "review"];
var CONTROL_OWNER_TYPES = ["app", "view"];
var CONTROL_SURFACES = ["app-viewer", "app-management", "index-view", "main-view"];

export const DOCS_VIEWER_CONTROL_OWNER_TYPES = Object.freeze({
  APP: "app",
  VIEW: "view"
});

export const DOCS_VIEWER_CONTROL_SURFACES = Object.freeze({
  APP_VIEWER: "app-viewer",
  APP_MANAGEMENT: "app-management",
  INDEX_VIEW: "index-view",
  MAIN_VIEW: "main-view"
});

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function cleanId(value, type) {
  var id = cleanString(value);
  if (!id) throw new Error("Docs Viewer " + type + " definition requires an id.");
  return id;
}

function cleanStringList(value) {
  if (!Array.isArray(value)) return [];
  var seen = new Set();
  return value.map(cleanString).filter(function (item) {
    if (!item || seen.has(item)) return false;
    seen.add(item);
    return true;
  });
}

function lifecycle(record) {
  var source = record || {};
  return {
    load: typeof source.load === "function" ? source.load : null,
    mount: typeof source.mount === "function" ? source.mount : null,
    update: typeof source.update === "function" ? source.update : null,
    unmount: typeof source.unmount === "function" ? source.unmount : null,
    dispose: typeof source.dispose === "function" ? source.dispose : null
  };
}

function normalizeCommon(record, type) {
  var source = record && typeof record === "object" ? record : {};
  var appKinds = cleanStringList(source.appKinds);
  appKinds.forEach(function (kind) {
    if (APP_KINDS.indexOf(kind) === -1) {
      throw new Error("Docs Viewer " + type + " " + cleanString(source.id) + " has unknown app kind: " + kind);
    }
  });
  return Object.assign({
    id: cleanId(source.id, type),
    label: cleanString(source.label) || cleanString(source.id),
    appKinds: appKinds.length ? appKinds : APP_KINDS.slice(),
    features: cleanStringList(source.features),
    requiredCapabilities: cleanStringList(source.requiredCapabilities),
    availability: cleanString(source.availability) || "available"
  }, lifecycle(source));
}

function normalizeView(record) {
  var source = record || {};
  var view = normalizeCommon(source, "view");
  var panel = cleanString(source.panel);
  if (PANELS.indexOf(panel) === -1) {
    throw new Error("Docs Viewer view " + view.id + " requires panel index, main, or info.");
  }
  return Object.assign(view, {
    panel: panel,
    renderer: cleanString(source.renderer),
    placeholderText: cleanString(source.placeholderText),
    capabilities: normalizeHostedViewCapabilities(source.capabilities)
  });
}

function normalizeMode(record) {
  var source = record || {};
  return Object.assign(normalizeCommon(source, "mode"), {
    ownerViewId: cleanId(source.ownerViewId, "mode owner view")
  });
}

function normalizeControl(record) {
  var source = record || {};
  var ownerType = cleanString(source.ownerType);
  if (CONTROL_OWNER_TYPES.indexOf(ownerType) === -1) {
    throw new Error("Docs Viewer control " + cleanString(source.id) + " requires ownerType app or view.");
  }
  var surfaceId = cleanString(source.surfaceId);
  if (CONTROL_SURFACES.indexOf(surfaceId) === -1) {
    throw new Error("Docs Viewer control " + cleanString(source.id) + " has unknown surface: " + surfaceId);
  }
  var ownerViewId = cleanString(source.ownerViewId);
  var modeIds = cleanStringList(source.modeIds);
  if (ownerType === DOCS_VIEWER_CONTROL_OWNER_TYPES.APP) {
    if (ownerViewId) {
      throw new Error("Docs Viewer app control " + cleanString(source.id) + " cannot declare an owner view.");
    }
    if (modeIds.length) {
      throw new Error("Docs Viewer app control " + cleanString(source.id) + " cannot declare owner modes.");
    }
    if (
      surfaceId !== DOCS_VIEWER_CONTROL_SURFACES.APP_VIEWER
      && surfaceId !== DOCS_VIEWER_CONTROL_SURFACES.APP_MANAGEMENT
    ) {
      throw new Error("Docs Viewer app control " + cleanString(source.id) + " requires an app control surface.");
    }
  } else {
    ownerViewId = cleanId(ownerViewId, "control owner view");
    if (
      surfaceId !== DOCS_VIEWER_CONTROL_SURFACES.INDEX_VIEW
      && surfaceId !== DOCS_VIEWER_CONTROL_SURFACES.MAIN_VIEW
    ) {
      throw new Error("Docs Viewer view control " + cleanString(source.id) + " requires a view control surface.");
    }
  }
  return Object.assign(normalizeCommon(source, "control"), {
    actionId: cleanString(source.actionId),
    ownerType: ownerType,
    ownerViewId: ownerViewId,
    modeIds: modeIds,
    surfaceId: surfaceId,
    renderer: cleanString(source.renderer)
  });
}

export function normalizeDocsViewerControlState(record) {
  var source = record && typeof record === "object" && !Array.isArray(record) ? record : {};
  var state = {};
  ["hidden", "disabled", "pressed", "busy", "expanded"].forEach(function (key) {
    if (Object.prototype.hasOwnProperty.call(source, key)) state[key] = Boolean(source[key]);
  });
  if (Object.prototype.hasOwnProperty.call(source, "label")) state.label = cleanString(source.label);
  if (Object.prototype.hasOwnProperty.call(source, "count")) {
    var count = Number(source.count);
    state.count = Number.isFinite(count) ? count : 0;
  }
  return state;
}

function insertDefinition(map, record, type) {
  if (map.has(record.id)) {
    throw new Error("Duplicate Docs Viewer " + type + " definition: " + record.id);
  }
  map.set(record.id, record);
}

function capabilityValue(capabilities, path) {
  var current = capabilities;
  var parts = cleanString(path).split(".").filter(Boolean);
  for (var index = 0; index < parts.length; index += 1) {
    if (!current || typeof current !== "object" || !Object.prototype.hasOwnProperty.call(current, parts[index])) {
      return undefined;
    }
    current = current[parts[index]];
  }
  return current;
}

function normalizePolicy(rawPolicy) {
  var policy = rawPolicy && typeof rawPolicy === "object" && !Array.isArray(rawPolicy) ? rawPolicy : {};
  return {
    hiddenViews: cleanStringList(policy.hiddenViews),
    hiddenModes: cleanStringList(policy.hiddenModes),
    hiddenControls: cleanStringList(policy.hiddenControls)
  };
}

export function createDocsViewerSharedViewDefinitions() {
  return {
    views: [
      {
        id: "index-tree",
        label: "Index tree",
        panel: "index",
        renderer: "index-tree",
        capabilities: { layoutStates: ["normal", "collapsed"] }
      },
      { id: "rendered-document", label: "Document", panel: "main" },
      { id: "search-results", label: "Search results", panel: "main", features: ["search"] },
      { id: "recent-results", label: "Recently added", panel: "main", features: ["recently-added"] },
      {
        id: "metadata-info",
        label: "Metadata info",
        panel: "info",
        load: function () {
          return import("./docs-viewer-metadata-info-view.js")
            .then(function (module) { return module.createDocsViewerMetadataInfoView(); });
        }
      }
    ],
    modes: [
      { id: "rendered-document", label: "Rendered document", ownerViewId: "rendered-document" }
    ],
    controls: [
      {
        id: "recently-added",
        label: "recently added",
        ownerType: "app",
        surfaceId: "app-viewer",
        features: ["recently-added"],
        renderer: "recent-button"
      },
      {
        id: "search",
        label: "Search docs",
        ownerType: "app",
        surfaceId: "app-viewer",
        features: ["search"],
        renderer: "search-input"
      },
      {
        id: "index-view-switch",
        label: "Tree index view",
        ownerType: "app",
        surfaceId: "app-viewer",
        renderer: "index-view-toggle"
      },
      {
        id: "bookmark",
        actionId: "bookmark",
        label: "Bookmark",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document"],
        surfaceId: "main-view",
        features: ["bookmarks"],
        renderer: "bookmark-toggle"
      },
      {
        id: "info",
        actionId: "info",
        label: "Document info",
        ownerType: "view",
        ownerViewId: "rendered-document",
        surfaceId: "main-view",
        renderer: "info-toggle"
      }
    ]
  };
}

export function composeDocsViewerViewDefinitionSets(contributions) {
  var shared = createDocsViewerSharedViewDefinitions();
  var appControls = shared.controls.filter(function (control) { return control.ownerType === "app"; });
  var viewControls = shared.controls.filter(function (control) { return control.ownerType === "view"; });
  return [
    { views: shared.views, modes: shared.modes, controls: appControls },
    contributions || {},
    { controls: viewControls }
  ];
}

export function createDocsViewerViewRegistry(options) {
  var settings = options || {};
  var views = new Map();
  var modes = new Map();
  var controls = new Map();
  var projectionInputs = settings.projectionInputs || {};
  var policy = normalizePolicy(settings.routePolicy);
  var definitionSets = Array.isArray(settings.definitionSets) ? settings.definitionSets : [];

  definitionSets.forEach(function (definitionSet) {
    var definitions = definitionSet || {};
    (definitions.views || []).forEach(function (record) {
      insertDefinition(views, normalizeView(record), "view");
    });
    (definitions.modes || []).forEach(function (record) {
      insertDefinition(modes, normalizeMode(record), "mode");
    });
    (definitions.controls || []).forEach(function (record) {
      insertDefinition(controls, normalizeControl(record), "control");
    });
  });

  modes.forEach(function (mode) {
    if (!views.has(mode.ownerViewId)) {
      throw new Error("Docs Viewer mode " + mode.id + " has unknown owner view: " + mode.ownerViewId);
    }
  });
  controls.forEach(function (control) {
    if (control.ownerType === DOCS_VIEWER_CONTROL_OWNER_TYPES.VIEW) {
      var ownerView = views.get(control.ownerViewId) || null;
      if (!ownerView) {
        throw new Error("Docs Viewer control " + control.id + " has unknown owner view: " + control.ownerViewId);
      }
      var expectedSurface = ownerView.panel === "index"
        ? DOCS_VIEWER_CONTROL_SURFACES.INDEX_VIEW
        : ownerView.panel === "main"
          ? DOCS_VIEWER_CONTROL_SURFACES.MAIN_VIEW
          : "";
      if (!expectedSurface || control.surfaceId !== expectedSurface) {
        throw new Error("Docs Viewer control " + control.id + " has a surface that does not match its owner view.");
      }
      control.modeIds.forEach(function (modeId) {
        var mode = modes.get(modeId);
        if (!mode || mode.ownerViewId !== control.ownerViewId) {
          throw new Error("Docs Viewer control " + control.id + " has unknown owner mode: " + modeId);
        }
      });
    }
  });

  policy.hiddenViews.forEach(function (id) {
    if (!views.has(id)) throw new Error("Unknown Docs Viewer route-policy view: " + id);
  });
  policy.hiddenModes.forEach(function (id) {
    if (!modes.has(id)) throw new Error("Unknown Docs Viewer route-policy mode: " + id);
  });
  policy.hiddenControls.forEach(function (id) {
    if (!controls.has(id)) throw new Error("Unknown Docs Viewer route-policy control: " + id);
  });

  function currentInputs() {
    return typeof projectionInputs === "function" ? projectionInputs() || {} : projectionInputs || {};
  }

  function statusFor(record, type) {
    if (!record) return { available: false, reason: "missing" };
    if (record.availability !== "available") return { available: false, reason: record.availability };
    var inputs = currentInputs();
    var appContext = inputs.appContext || {};
    if (record.appKinds.indexOf(cleanString(appContext.kind)) === -1) {
      return { available: false, reason: "access" };
    }
    var featurePolicy = appContext.featurePolicy || {};
    for (var featureIndex = 0; featureIndex < record.features.length; featureIndex += 1) {
      if (!docsViewerRouteFeatureEnabled(featurePolicy, record.features[featureIndex])) {
        return { available: false, reason: "feature" };
      }
    }
    var backendCapabilities = inputs.backendCapabilities || appContext.backendCapabilities || null;
    for (var capabilityIndex = 0; capabilityIndex < record.requiredCapabilities.length; capabilityIndex += 1) {
      if (capabilityValue(backendCapabilities, record.requiredCapabilities[capabilityIndex]) !== true) {
        return { available: false, reason: "capability" };
      }
    }
    var hidden = type === "view"
      ? policy.hiddenViews
      : type === "mode"
        ? policy.hiddenModes
        : policy.hiddenControls;
    if (hidden.indexOf(record.id) !== -1) return { available: false, reason: "policy" };
    if (type === "mode" || (type === "control" && record.ownerType === DOCS_VIEWER_CONTROL_OWNER_TYPES.VIEW)) {
      var ownerStatus = statusFor(views.get(record.ownerViewId) || null, "view");
      if (!ownerStatus.available) return { available: false, reason: "owner-view" };
    }
    return { available: true, reason: "" };
  }

  function projection(record, type) {
    var status = statusFor(record, type);
    return Object.assign({}, record, {
      available: status.available,
      unavailableReason: status.reason
    });
  }

  function resolved(record, type) {
    var status = statusFor(record, type);
    var key = type;
    return {
      id: record ? record.id : "",
      registered: Boolean(record),
      available: status.available,
      reason: status.reason,
      [key]: status.available ? record : null
    };
  }

  function controlActive(control, activeViewId, activeModeId) {
    if (!control) return false;
    if (control.ownerType === DOCS_VIEWER_CONTROL_OWNER_TYPES.APP) return true;
    if (control.ownerViewId !== cleanString(activeViewId)) return false;
    return !control.modeIds.length || control.modeIds.indexOf(cleanString(activeModeId)) !== -1;
  }

  function controlState(control, stateById) {
    var states = stateById && typeof stateById === "object" ? stateById : {};
    return normalizeDocsViewerControlState(states[control.id]);
  }

  function controlProjection(control, activeState) {
    var state = activeState || {};
    return Object.assign(projection(control, "control"), {
      state: controlState(control, state.controlStateById)
    });
  }

  return {
    listViews: function (panel) {
      var targetPanel = cleanString(panel);
      return Array.from(views.values()).filter(function (view) {
        return !targetPanel || view.panel === targetPanel;
      }).map(function (view) { return projection(view, "view"); });
    },
    listModes: function (ownerViewId) {
      var ownerId = cleanString(ownerViewId);
      return Array.from(modes.values()).filter(function (mode) {
        return !ownerId || mode.ownerViewId === ownerId;
      }).map(function (mode) { return projection(mode, "mode"); });
    },
    listControls: function (optionsForList) {
      var listSettings = optionsForList || {};
      var ownerId = cleanString(listSettings.ownerViewId);
      var ownerType = cleanString(listSettings.ownerType);
      var surfaceId = cleanString(listSettings.surfaceId);
      return Array.from(controls.values()).filter(function (control) {
        return (!ownerId || control.ownerViewId === ownerId)
          && (!ownerType || control.ownerType === ownerType)
          && (!surfaceId || control.surfaceId === surfaceId);
      }).map(function (control) {
        return Object.assign(controlProjection(control, listSettings), {
          active: statusFor(control, "control").available && controlActive(
            control,
            listSettings.activeViewId,
            listSettings.activeModeId
          )
        });
      });
    },
    projectControls: function (activeState) {
      var state = activeState || {};
      var surfaceId = cleanString(state.surfaceId);
      return Array.from(controls.values()).filter(function (control) {
        return (!surfaceId || control.surfaceId === surfaceId)
          && statusFor(control, "control").available
          && controlActive(control, state.activeViewId, state.activeModeId);
      }).map(function (control) { return controlProjection(control, state); });
    },
    resolveView: function (id) { return resolved(views.get(cleanString(id)) || null, "view"); },
    resolveMode: function (id) { return resolved(modes.get(cleanString(id)) || null, "mode"); },
    resolveControl: function (id, activeState) {
      var control = controls.get(cleanString(id)) || null;
      var result = resolved(control, "control");
      result.active = Boolean(
        result.available
        && controlActive(control, activeState && activeState.activeViewId, activeState && activeState.activeModeId)
      );
      return result;
    },
    setProjectionInputs: function (nextInputs) {
      projectionInputs = nextInputs || {};
    }
  };
}
