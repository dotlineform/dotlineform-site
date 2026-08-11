import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";

const PUBLIC_REPORT_LOADERS = {
  docs_subscope: {
    load: function () {
      return import("../shared/docs-subscope-report.js").then(function (module) {
        return module.mountDocsSubscopeReport;
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
    if (report.defaultAccess === "public") reportsById.set(report.reportId, report);
  });
  return {
    schema: cleanString(payload && payload.schema),
    reports,
    reportsById
  };
}

function loadReportRegistry(context) {
  const registryUrl = cleanString(context && context.reportRegistryUrl);
  if (!registryUrl) {
    return Promise.reject(new Error("Public report registry is not configured."));
  }
  return fetch(appendAssetVersion(registryUrl), {
    headers: { Accept: "application/json" },
    cache: "default"
  })
    .then(function (response) {
      if (!response.ok) throw new Error("Failed to load public report registry.");
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

function registerExpandedPresentation(context, root, reportMeta, mountResult) {
  const adapter = context && context.reportPresentationAdapter;
  if (!adapter || typeof adapter.registerMountedReport !== "function") return;
  try {
    adapter.registerMountedReport({
      content: context.content,
      doc: context.doc,
      document: root.ownerDocument,
      documentMountGeneration: context.documentMountGeneration,
      mountResult,
      reportMeta,
      reportRoot: root,
      requestContentDetail: context.requestContentDetail,
      viewerScope: context.viewerScope
    });
  } catch (error) {
    console.warn("docs_viewer: expanded report registration unavailable", error);
  }
}

function unavailable(root, message) {
  root.innerHTML = "";
  const note = document.createElement("p");
  note.className = "docsViewer__panelStatus muted small";
  note.textContent = message;
  root.appendChild(note);
}

function canMountPublicReport(meta, reportMeta) {
  const access = meta.access || reportMeta.defaultAccess || "public";
  if (access !== "public") {
    return { ok: false, message: "This report is local-only." };
  }
  if (reportMeta.defaultAccess !== "public") {
    return { ok: false, message: "This report has not been promoted for public routes." };
  }
  if (!PUBLIC_REPORT_LOADERS[reportMeta.loaderId]) {
    return { ok: false, message: "This report type is not available on public routes yet." };
  }
  return { ok: true };
}

export function mountDocsViewerPublicReport(context) {
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
    if (!reportMeta) {
      unavailable(root, "This report has not been promoted for public routes.");
      return true;
    }

    const availability = canMountPublicReport(meta, reportMeta);
    if (!availability.ok) {
      unavailable(root, availability.message);
      return true;
    }

    root.innerHTML = '<p class="docsViewer__panelStatus muted small">Loading report...</p>';
    return PUBLIC_REPORT_LOADERS[reportMeta.loaderId].load().then(function (mount) {
      if (!hostIsCurrent(root, context.content)) return false;
      const resolvedReportMeta = Object.assign({}, meta, { registryEntry: reportMeta });
      return Promise.resolve(mount(Object.assign({}, context, {
        reportRoot: root,
        reportMeta: resolvedReportMeta,
        reportRegistry: registry
      }))).then(function (mountResult) {
        if (!hostIsCurrent(root, context.content)) return false;
        registerExpandedPresentation(context, root, resolvedReportMeta, mountResult);
        return true;
      });
    });
  }).catch((error) => {
    if (hostIsCurrent(root, context.content)) {
      unavailable(root, error && error.message ? error.message : "Failed to render report.");
    }
    return true;
  });
}
