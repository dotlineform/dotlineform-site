import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";

const REPORT_LOADERS = {
  docs_index_table: {
    load: function () {
      return import("./docs-index-table-report.js").then(function (module) {
        return module.mountDocsIndexTableReport;
      });
    }
  },
  reports_list: {
    load: function () {
      return import("./reports-list-report.js").then(function (module) {
        return module.mountReportsListReport;
      });
    }
  },
  source_config: {
    load: function () {
      return import("./source-config-report.js").then(function (module) {
        return module.mountSourceConfigReport;
      });
    }
  },
  docs_subscope: {
    load: function () {
      return import("../shared/docs-subscope-report.js").then(function (module) {
        return module.mountDocsSubscopeReport;
      });
    }
  },
  docs_broken_links: {
    load: function () {
      return import("./docs-broken-links-report.js").then(function (module) {
        return module.mountDocsBrokenLinksReport;
      });
    }
  },
  semantic_tokens: {
    load: function () {
      return import("./semantic-tokens-report.js").then(function (module) {
        return module.mountSemanticTokensReport;
      });
    }
  },
  project_state: {
    load: function () {
      return import("./project-state-report.js").then(function (module) {
        return module.mountProjectStateReport;
      });
    }
  },
  works: {
    load: function () {
      return import("./works-report.js").then(function (module) {
        return module.mountWorksReport;
      });
    }
  },
  catalogue_works: {
    load: function () {
      return import("./catalogue-works-report.js").then(function (module) {
        return module.mountCatalogueWorksReport;
      });
    }
  },
  uncataloged_files: {
    load: function () {
      return import("./uncataloged-files-report.js").then(function (module) {
        return module.mountUncatalogedFilesReport;
      });
    }
  },
  missing_source_files: {
    load: function () {
      return import("./missing-source-files-report.js").then(function (module) {
        return module.mountMissingSourceFilesReport;
      });
    }
  }
};

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
  return cleanString(context && context.reportRegistryUrl);
}

function loadReportRegistry(context) {
  const registryUrl = reportRegistryUrl(context);
  if (!registryUrl) {
    return Promise.reject(new Error("Report registry is not configured."));
  }
  return fetch(appendAssetVersion(registryUrl), {
    headers: { Accept: "application/json" },
    cache: "default"
  })
    .then(function (response) {
      if (!response.ok) throw new Error("Failed to load report registry.");
      return response.json();
    })
    .then(normalizeReportRegistry);
}

function normalizeReportMetadata(payload) {
  const report = payload && payload.report;
  const reportId = cleanString(report && report.id);
  if (!reportId) return null;
  return {
    reportId,
    scope: cleanString(report.scope),
    access: cleanString(report.access),
    preset: cleanString(report.preset),
    subScope: cleanString(report.sub_scope)
  };
}

function generatedReportHost(context) {
  const content = context && context.content;
  const hosts = content && typeof content.querySelectorAll === "function"
    ? content.querySelectorAll("[data-docs-viewer-report-host]")
    : [];
  if (hosts.length !== 1) {
    throw new Error("Report document must contain exactly one generated host.");
  }
  return hosts[0];
}

function hostIsCurrent(root, content) {
  return !content || typeof content.contains !== "function" || content.contains(root);
}

function unavailable(root, message) {
  root.innerHTML = "";
  const note = document.createElement("p");
  note.className = "docsViewerReport__status";
  note.textContent = message;
  root.appendChild(note);
}

function accessMessage(access) {
  if (access === "local") {
    return "This report is available in local Docs Viewer mode.";
  }
  return "This report is unavailable in the current viewer context.";
}

function canMountReport(meta, reportMeta, context) {
  const access = meta.access || reportMeta.defaultAccess || "public";
  if (access === "public") {
    return Promise.resolve({ ok: true, access });
  }
  if (access === "local") {
    return Promise.resolve({
      ok: Boolean(
        context.managementContext
        && context.managementService
        && context.appContext
        && context.appContext.kind === "manage"
      ),
      access
    });
  }
  return Promise.resolve({ ok: false, access });
}

export function mountDocsViewerReport(context) {
  const meta = normalizeReportMetadata(context && context.payload);
  if (!meta) return Promise.resolve(false);

  let root;
  try {
    root = generatedReportHost(context);
  } catch (error) {
    return Promise.reject(error);
  }
  root.dataset.reportId = meta.reportId;

  return loadReportRegistry(context).then(function (registry) {
    if (!hostIsCurrent(root, context.content)) return false;
    const reportMeta = registry.reportsById.get(meta.reportId);
    const loader = reportMeta ? REPORT_LOADERS[reportMeta.loaderId] : null;

    if (!reportMeta || !loader) {
      unavailable(root, "This report type is not available.");
      return true;
    }

    return canMountReport(meta, reportMeta, context).then((result) => {
      if (!hostIsCurrent(root, context.content)) return false;
      if (!result.ok) {
        unavailable(root, accessMessage(result.access));
        return true;
      }
      root.innerHTML = '<p class="docsViewerReport__status">Loading report...</p>';
      return loader.load().then(function (mount) {
        if (!hostIsCurrent(root, context.content)) return false;
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
    if (hostIsCurrent(root, context.content)) {
      unavailable(root, error && error.message ? error.message : "Failed to render report.");
    }
    return true;
  });
}
