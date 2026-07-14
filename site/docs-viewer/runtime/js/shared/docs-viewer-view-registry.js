import {
  normalizeHostedViewCapabilities
} from "./docs-viewer-hosted-view-capabilities.js";
import {
  docsViewerRouteFeatureEnabled
} from "./docs-viewer-route-features.js";

var PANELS = ["index", "main", "info"];
var APP_KINDS = ["public", "manage", "review"];

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
  return Object.assign(normalizeCommon(source, "control"), {
    actionId: cleanString(source.actionId),
    ownerViewId: cleanId(source.ownerViewId, "control owner view"),
    modeIds: cleanStringList(source.modeIds),
    renderer: cleanString(source.renderer)
  });
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
        capabilities: { layoutStates: ["normal", "collapsed"], toolbar: false }
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
        id: "bookmark",
        actionId: "bookmark",
        label: "Bookmark",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document"],
        features: ["bookmarks"],
        renderer: "bookmark-toggle"
      },
      {
        id: "info",
        actionId: "info",
        label: "Document info",
        ownerViewId: "rendered-document",
        renderer: "info-toggle"
      }
    ]
  };
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
    if (!views.has(control.ownerViewId)) {
      throw new Error("Docs Viewer control " + control.id + " has unknown owner view: " + control.ownerViewId);
    }
    control.modeIds.forEach(function (modeId) {
      var mode = modes.get(modeId);
      if (!mode || mode.ownerViewId !== control.ownerViewId) {
        throw new Error("Docs Viewer control " + control.id + " has unknown owner mode: " + modeId);
      }
    });
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
    if (type === "mode" || type === "control") {
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
    if (!control || control.ownerViewId !== cleanString(activeViewId)) return false;
    return !control.modeIds.length || control.modeIds.indexOf(cleanString(activeModeId)) !== -1;
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
      return Array.from(controls.values()).filter(function (control) {
        return !ownerId || control.ownerViewId === ownerId;
      }).map(function (control) {
        return Object.assign(projection(control, "control"), {
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
      return Array.from(controls.values()).filter(function (control) {
        return statusFor(control, "control").available
          && controlActive(control, state.activeViewId, state.activeModeId);
      }).map(function (control) { return projection(control, "control"); });
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
