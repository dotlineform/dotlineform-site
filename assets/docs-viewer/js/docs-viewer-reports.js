import {
  appendAssetVersion
} from "./docs-viewer-data.js";

const REPORT_REGISTRY_URL = "/assets/data/docs/reports.json";

const REPORT_LOADERS = {
  docs_index_table: {
    load: function () {
      return import("./reports/docs-index-table-report.js").then(function (module) {
        return module.mountDocsIndexTableReport;
      });
    }
  },
  reports_list: {
    load: function () {
      return import("./reports/reports-list-report.js").then(function (module) {
        return module.mountReportsListReport;
      });
    }
  },
  source_config: {
    load: function () {
      return import("./reports/source-config-report.js").then(function (module) {
        return module.mountSourceConfigReport;
      });
    }
  },
  semantic_references: {
    load: function () {
      return import("./reports/semantic-references-report.js").then(function (module) {
        return module.mountSemanticReferencesReport;
      });
    }
  }
};

const FALLBACK_REPORT_REGISTRY = {
  schema: "docs_viewer_reports_v1",
  reports: [
    {
      reportId: "docs_index_table",
      title: "Docs Index Table",
      description: "Displays a sortable Docs Viewer index table for a selected docs scope.",
      defaultAccess: "public",
      loaderId: "docs_index_table",
      presets: []
    },
    {
      reportId: "reports_list",
      title: "Reports List",
      description: "Displays the configured Docs Viewer report metadata from the report registry.",
      defaultAccess: "public",
      loaderId: "reports_list",
      presets: []
    },
    {
      reportId: "source_config",
      title: "Source Config",
      description: "Displays Docs Viewer source config for all scopes in manage mode.",
      defaultAccess: "manage",
      loaderId: "source_config",
      presets: []
    },
    {
      reportId: "semantic_references",
      title: "Semantic References",
      description: "Displays generated semantic-reference targets and source docs.",
      defaultAccess: "manage",
      loaderId: "semantic_references",
      presets: []
    }
  ],
  reportsById: new Map()
};
FALLBACK_REPORT_REGISTRY.reportsById = new Map(
  FALLBACK_REPORT_REGISTRY.reports.map(function (report) {
    return [report.reportId, report];
  })
);

function cleanString(value) {
  return String(value || "").trim();
}

function normalizeList(value) {
  if (!Array.isArray(value)) return [];
  return value.map(cleanString).filter(Boolean);
}

function normalizePreset(raw) {
  return {
    presetId: cleanString(raw && raw.preset_id),
    title: cleanString(raw && raw.title),
    description: cleanString(raw && raw.description),
    defaultScope: cleanString(raw && raw.default_scope),
    columns: normalizeList(raw && raw.columns),
    filters: normalizeList(raw && raw.filters),
    sortable: normalizeList(raw && raw.sortable)
  };
}

function normalizeReport(raw) {
  const reportId = cleanString(raw && raw.report_id);
  if (!reportId) return null;
  return {
    reportId,
    title: cleanString(raw && raw.title) || reportId,
    description: cleanString(raw && raw.description),
    defaultAccess: cleanString(raw && raw.default_access) || "public",
    loaderId: cleanString(raw && raw.loader_id) || reportId,
    presets: Array.isArray(raw && raw.presets)
      ? raw.presets.map(normalizePreset).filter(function (preset) { return preset.presetId; })
      : []
  };
}

function normalizeReportRegistry(payload) {
  const reports = Array.isArray(payload && payload.reports)
    ? payload.reports.map(normalizeReport).filter(Boolean)
    : [];
  const reportsById = new Map();
  reports.forEach(function (report) {
    reportsById.set(report.reportId, report);
  });
  return {
    schema: cleanString(payload && payload.schema),
    reports,
    reportsById
  };
}

function reportRegistryUrl(context) {
  return cleanString(context && context.reportRegistryUrl) || REPORT_REGISTRY_URL;
}

function loadReportRegistry(context) {
  return fetch(appendAssetVersion(reportRegistryUrl(context)), {
    headers: { Accept: "application/json" },
    cache: "default"
  })
    .then(function (response) {
      if (!response.ok) throw new Error("Failed to load report registry.");
      return response.json();
    })
    .then(normalizeReportRegistry)
    .catch(function () {
      return FALLBACK_REPORT_REGISTRY;
    });
}

function normalizeReportMetadata(payload) {
  const reportId = cleanString(payload && payload.viewer_report);
  if (!reportId) return null;
  return {
    reportId,
    scope: cleanString(payload.viewer_report_scope),
    access: cleanString(payload.viewer_report_access),
    preset: cleanString(payload.viewer_report_preset)
  };
}

function unavailable(root, message) {
  root.innerHTML = "";
  const note = document.createElement("p");
  note.className = "docsViewerReport__status";
  note.textContent = message;
  root.appendChild(note);
}

function accessMessage(access) {
  if (access === "manage") {
    return "This report is available in manage mode.";
  }
  if (access === "local") {
    return "This report needs local generated-data access.";
  }
  return "This report is unavailable in the current viewer context.";
}

function canMountReport(meta, reportMeta, context) {
  const access = meta.access || reportMeta.defaultAccess || "public";
  if (access === "public") {
    return Promise.resolve({ ok: true, access });
  }
  if (access === "manage") {
    return Promise.resolve({ ok: Boolean(context.managementMode), access });
  }
  if (access === "local") {
    if (typeof context.checkGeneratedDataReadCapability !== "function") {
      return Promise.resolve({ ok: false, access });
    }
    return context.checkGeneratedDataReadCapability(meta.scope || context.viewerScope)
      .then((available) => ({ ok: Boolean(available), access }))
      .catch(() => ({ ok: false, access }));
  }
  return Promise.resolve({ ok: false, access });
}

export function mountDocsViewerReport(context) {
  const meta = normalizeReportMetadata(context && context.payload);
  if (!meta) return Promise.resolve(false);

  const root = document.createElement("section");
  root.className = "docsViewerReport";
  root.dataset.reportId = meta.reportId;
  root.setAttribute("aria-label", "Document report");
  context.content.appendChild(root);

  return loadReportRegistry(context).then(function (registry) {
    const reportMeta = registry.reportsById.get(meta.reportId);
    const loader = reportMeta ? REPORT_LOADERS[reportMeta.loaderId] : null;

    if (!reportMeta || !loader) {
      unavailable(root, "This report type is not available.");
      return true;
    }

    return canMountReport(meta, reportMeta, context).then((result) => {
      if (!result.ok) {
        unavailable(root, accessMessage(result.access));
        return true;
      }
      root.innerHTML = '<p class="docsViewerReport__status">Loading report...</p>';
      return loader.load().then(function (mount) {
        return Promise.resolve(mount(Object.assign({}, context, {
          reportRoot: root,
          reportMeta: Object.assign({}, meta, { registryEntry: reportMeta }),
          reportRegistry: registry
        }))).then(function () {
          return true;
        });
      });
    });
  }).catch((error) => {
    unavailable(root, error && error.message ? error.message : "Failed to render report.");
    return true;
  });
}
