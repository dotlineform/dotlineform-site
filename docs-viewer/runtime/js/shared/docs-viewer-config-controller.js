import {
  routeConfigWorkspaceProjection
} from "./docs-viewer-route-config.js";
import {
  DOCS_VIEWER_CODE_CONFIG
} from "./docs-viewer-code-config.js";

export function positiveInteger(value, fallback) {
  var parsed = parseInt(value, 10);
  return parsed > 0 ? parsed : fallback;
}

export function getConfigValue(config, path) {
  var current = config;
  String(path || "").split(".").filter(Boolean).forEach(function (key) {
    if (current && Object.prototype.hasOwnProperty.call(current, key)) {
      current = current[key];
    } else {
      current = undefined;
    }
  });
  return current;
}

export function getConfigText(config, path, fallback) {
  var value = getConfigValue(config, "ui_text." + path);
  return String(value == null ? fallback == null ? "" : fallback : value);
}

export function formatText(template, tokens) {
  var text = String(template || "");
  Object.keys(tokens || {}).forEach(function (key) {
    text = text.replace(new RegExp("\\{" + key + "\\}", "g"), tokens[key]);
  });
  return text;
}

export function normalizeDocsViewerCollectionCustomisation(rawCustomisation) {
  if (!rawCustomisation || typeof rawCustomisation !== "object" || Array.isArray(rawCustomisation)) {
    throw new Error("Docs Viewer collection_customisation must be an object.");
  }
  var customisationKeys = Object.keys(rawCustomisation).sort();
  if (
    customisationKeys.length < 1
    || customisationKeys.length > 2
    || !customisationKeys.includes("id")
    || customisationKeys.some(function (key) {
      return key !== "id" && key !== "capabilities";
    })
  ) {
    throw new Error(
      "Docs Viewer collection_customisation must contain id and optional capabilities."
    );
  }
  var customisationId = String(rawCustomisation.id || "").trim();
  if (!/^[a-z][a-z0-9_]*$/.test(customisationId)) {
    throw new Error("Docs Viewer collection_customisation id is invalid.");
  }
  if (!Object.prototype.hasOwnProperty.call(rawCustomisation, "capabilities")) {
    return Object.freeze({ id: customisationId });
  }

  var rawCapabilities = rawCustomisation.capabilities;
  if (!rawCapabilities || typeof rawCapabilities !== "object" || Array.isArray(rawCapabilities)) {
    throw new Error("Docs Viewer collection_customisation capabilities must be an object.");
  }
  var capabilityKeys = Object.keys(rawCapabilities).sort();
  if (
    !capabilityKeys.length
    || capabilityKeys.some(function (key) {
      return key !== "assignable_field_groups";
    })
  ) {
    throw new Error(
      "Docs Viewer collection_customisation capabilities contains an invalid field."
    );
  }
  var capabilities = {};
  if (Object.prototype.hasOwnProperty.call(rawCapabilities, "assignable_field_groups")) {
    var rawGroups = rawCapabilities.assignable_field_groups;
    if (!Array.isArray(rawGroups) || !rawGroups.length) {
      throw new Error(
        "Docs Viewer collection_customisation assignable_field_groups must be a non-empty array."
      );
    }
    var seen = new Set();
    capabilities.assignableFieldGroups = Object.freeze(rawGroups.map(function (rawGroup) {
      var groupId = String(rawGroup || "").trim();
      if (!/^[a-z][a-z0-9_]*$/.test(groupId) || seen.has(groupId)) {
        throw new Error(
          "Docs Viewer collection_customisation assignable_field_groups contains an invalid or duplicate id."
        );
      }
      seen.add(groupId);
      return groupId;
    }));
  }

  return Object.freeze({
    id: customisationId,
    capabilities: Object.freeze(capabilities)
  });
}

export function hasDocsViewerAssignableFieldGroup(descriptor, groupId) {
  var value = String(groupId || "").trim();
  var groups = descriptor
    && descriptor.capabilities
    && descriptor.capabilities.assignableFieldGroups;
  return Boolean(value && Array.isArray(groups) && groups.includes(value));
}

export function initDocsViewerConfigController(context) {
  var workspaceConfig = context.workspaceConfig || {};
  var documentIndex = context.documentIndex || {};
  var searchRecent = context.searchRecent || {};
  var configService = context.configService || {};
  var routeCommands = context.routeCommands || {};
  var root = context.root;
  if (!Array.isArray(documentIndex.docs)) documentIndex.docs = [];

  function normalizeCollectionConfig(rawCollection) {
    if (!rawCollection || typeof rawCollection !== "object") return null;
    var collection = String(rawCollection.collection || "").trim().toLowerCase();
    if (!collection) return null;
    var manifestUrl = String(rawCollection.manifest_url || "").trim();
    var byIdUrlBase = String(rawCollection.by_id_url_base || "").trim().replace(/\/+$/, "");
    if (!manifestUrl || !byIdUrlBase) return null;
    var icon = rawCollection.icon;
    if (typeof icon !== "string" || icon !== icon.trim() || !/^[a-z0-9][a-z0-9_-]*$/.test(icon)) {
      throw new Error("Collection icon requires an extensionless SVG filename stem.");
    }
    var reportHostDocId = rawCollection.report_host_doc_id;
    if (typeof reportHostDocId !== "string" || !/^d-[0-9]{8}-[0-9]{6}-[0-9a-f]{6}$/.test(reportHostDocId)) {
      throw new Error("Collection requires a configured immutable report host ID.");
    }
    var collectionCustomisation = null;
    if (Object.prototype.hasOwnProperty.call(rawCollection, "collection_customisation")) {
      collectionCustomisation = normalizeDocsViewerCollectionCustomisation(
        rawCollection.collection_customisation
      );
    }
    var record = {
      collection: collection,
      title: String(rawCollection.title || "").trim(),
      icon: icon,
      iconUrl: new URL("../../../static/icons/" + icon + ".svg", import.meta.url).href,
      reportHostDocId: reportHostDocId,
      manifestUrl: manifestUrl,
      byIdUrlBase: byIdUrlBase,
      collectionCustomisation: collectionCustomisation
    };
    return record;
  }

  function normalizeBrowserConfig(raw) {
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error("Docs Viewer configuration must be an object.");
    var children = (raw.collections || []).map(normalizeCollectionConfig);
    if (children.some(function (child) { return !child; }) || new Set(children.map(function (child) { return child.collection; })).size !== children.length) {
      throw new Error("Docs Viewer collections require unique configured identities and payload URLs.");
    }
    if (new Set(children.map(function (child) { return child.reportHostDocId; })).size !== children.length) {
      throw new Error("Docs Viewer collections require unique report host IDs.");
    }
    var config = {
      viewerBaseUrl: String(raw.viewer_base_url || ""),
      mediaRoot: String(raw.media_root || ""),
      defaultDocId: String(raw.default_doc_id || ""),
      indexTreeUrl: String(raw.index_tree_url || ""),
      recentUrl: String(raw.recent_url || ""),
      selectedUrl: String(raw.selected_url || ""),
      backlinksUrl: String(raw.backlinks_url || ""),
      linksEnabled: raw.links_enabled === true,
      searchIndexUrl: String(raw.search_index_url || ""),
      collections: children,
      collectionsById: new Map(children.map(function (child) { return [child.collection, child]; })),
      collectionsByReportHostId: new Map(children.map(function (child) { return [child.reportHostDocId, child]; }))
    };
    if (!config.viewerBaseUrl || !config.mediaRoot || !config.indexTreeUrl
        || context.featurePolicy.recent && !config.recentUrl
        || context.featurePolicy.search && !config.searchIndexUrl) {
      throw new Error("Docs Viewer configuration is missing a required reader URL.");
    }
    return config;
  }

  function normalizeConfigEnvelope(payload) {
    if (!payload || payload.schema_version !== "docs_viewer_config_v4") {
      throw new Error("Docs Viewer config has an unsupported schema.");
    }
    return {
      publicViewerBaseUrl: String(payload.public_viewer_base_url || ""),
      rawWorkspace: payload.workspace,
      docsViewerSettings: payload.docs_viewer || {}
    };
  }

  function applyWorkspaceConfig(config) {
    workspaceConfig.activeConfig = config;
    var projection = routeConfigWorkspaceProjection(config, {
      routeViewerBaseUrl: context.routeViewerBaseUrl, window: window
    });
    routeCommands.applyRouteGlobals(projection);
    root.dataset.indexTreeUrl = config.indexTreeUrl;
    root.dataset.recentUrl = config.recentUrl;
    root.dataset.searchIndexUrl = config.searchIndexUrl;
    root.dataset.defaultDocId = config.defaultDocId;
    root.dataset.viewerBaseUrl = projection.viewerBaseUrl;
  }

  function loadConfigEnvelope(options) {
    var settings = options || {};
    if (settings.force) {
      workspaceConfig.docsViewerConfigLoaded = false;
      workspaceConfig.docsViewerConfigRequestPromise = null;
    }
    if (workspaceConfig.docsViewerConfigLoaded) return Promise.resolve(workspaceConfig.docsViewerConfig);
    if (workspaceConfig.docsViewerConfigRequestPromise) return workspaceConfig.docsViewerConfigRequestPromise;
    if (typeof configService.fetchDocsViewerConfig !== "function") {
      return Promise.reject(new Error("Docs Viewer config service is not configured."));
    }

    workspaceConfig.docsViewerConfigRequestPromise = configService.fetchDocsViewerConfig(settings)
      .then(function (payload) {
        var config = normalizeConfigEnvelope(payload);
        workspaceConfig.docsViewerConfig = config;
        workspaceConfig.docsViewerConfigLoaded = true;
        return config;
      })
      .finally(function () {
        workspaceConfig.docsViewerConfigRequestPromise = null;
      });

    return workspaceConfig.docsViewerConfigRequestPromise;
  }

  function loadWorkspaceConfiguration(options) {
    var settings = options || {};
    if (settings.force) {
      workspaceConfig.workspaceLoaded = false;
      workspaceConfig.workspaceRequestPromise = null;
    }
    if (workspaceConfig.workspaceLoaded) return Promise.resolve(workspaceConfig.activeConfig);
    if (workspaceConfig.workspaceRequestPromise) return workspaceConfig.workspaceRequestPromise;

    workspaceConfig.workspaceRequestPromise = loadConfigEnvelope(settings)
      .then(function (envelope) {
        workspaceConfig.publicViewerBaseUrl = envelope.publicViewerBaseUrl;
        var params = new URLSearchParams(window.location.search);
        if (params.has("scope") || params.has("stage")) throw new Error("This Docs URL uses retired context; use a current document link.");
        if (!envelope.rawWorkspace) throw new Error("Docs requires one workspace configuration.");
        var config = normalizeBrowserConfig(envelope.rawWorkspace);
        applyWorkspaceConfig(config);
        workspaceConfig.workspaceLoaded = true;
        return config;
      })
      .finally(function () {
        workspaceConfig.workspaceRequestPromise = null;
      });
    return workspaceConfig.workspaceRequestPromise;
  }

  function normalizeUiStatuses() {
    var rawStatuses = DOCS_VIEWER_CODE_CONFIG.uiStatuses;
    if (!Array.isArray(rawStatuses)) return [];

    var seen = new Set();
    return rawStatuses.reduce(function (statuses, rawStatus) {
      if (!rawStatus || typeof rawStatus !== "object") return statuses;
      var value = typeof rawStatus.ui_status === "string" ? rawStatus.ui_status.trim() : "";
      var label = typeof rawStatus.label === "string" ? rawStatus.label.trim() : "";
      var artwork = typeof rawStatus.artwork === "string" ? rawStatus.artwork.trim() : "";
      if (!value || !label || !artwork || seen.has(value)) {
        return statuses;
      }
      seen.add(value);
      statuses.push({
        ui_status: value,
        label: label,
        artwork: artwork
      });
      return statuses;
    }, []);
  }

  function applyViewerConfig(config) {
    workspaceConfig.viewerConfig = config || {};
    workspaceConfig.viewerConfigLoaded = true;
    workspaceConfig.recentLimit = positiveInteger(getConfigValue(config, "docs_viewer.recent_limit"), context.defaultRecentLimit);
    searchRecent.recentLimit = workspaceConfig.recentLimit;
    workspaceConfig.uiStatuses = normalizeUiStatuses();
    workspaceConfig.uiStatusByValue = new Map(workspaceConfig.uiStatuses.map(function (status) {
      return [status.ui_status, status];
    }));
    if (typeof context.setRecentControlLabel === "function") context.setRecentControlLabel("Recent");
    if (context.managementController()) {
      context.managementController().applyConfig(config);
    }
    if (documentIndex.docs.length) {
      context.renderSidebar();
    }
    if (searchRecent.recentModeActive) {
      context.renderRecentMode();
    }
  }

  function loadViewerSettings(options) {
    var settings = options || {};
    if (settings.force) {
      workspaceConfig.viewerConfigLoaded = false;
      workspaceConfig.viewerConfigRequestPromise = null;
    }
    if (workspaceConfig.viewerConfigLoaded) return Promise.resolve(null);
    if (workspaceConfig.viewerConfigRequestPromise) return workspaceConfig.viewerConfigRequestPromise;
    if (typeof configService.fetchDocsViewerConfig !== "function") {
      applyViewerConfig({});
      return Promise.resolve(null);
    }

    workspaceConfig.viewerConfigRequestPromise = loadConfigEnvelope(settings)
      .then(function (configEnvelope) {
        configEnvelope = configEnvelope || {};
        var config = {
          docs_viewer: configEnvelope.docsViewerSettings || {}
        };
        applyViewerConfig(config);
        return config;
      })
      .catch(function () {
        applyViewerConfig({});
        return null;
      })
      .finally(function () {
        workspaceConfig.viewerConfigRequestPromise = null;
      });
    return workspaceConfig.viewerConfigRequestPromise;
  }

  function reloadViewerConfiguration() {
    var reloadOptions = {
      force: true,
      reloadNonce: String(Date.now())
    };
    workspaceConfig.viewerConfigLoaded = false;
    workspaceConfig.viewerConfigRequestPromise = null;
    var reloadDiscovery = context.featurePolicy && context.featurePolicy.workspaceConfiguration
      ? loadWorkspaceConfiguration(reloadOptions)
      : loadConfigEnvelope(reloadOptions);
    return reloadDiscovery.then(function () {
      return loadViewerSettings();
    });
  }

  return {
    loadWorkspaceConfiguration: loadWorkspaceConfiguration,
    loadViewerSettings: loadViewerSettings,
    reloadViewerConfiguration: reloadViewerConfiguration
  };
}
