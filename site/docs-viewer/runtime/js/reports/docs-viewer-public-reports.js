import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";

const PUBLIC_REPORT_LOADERS = {};

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
  const reportId = cleanString(payload && payload.viewer_report);
  if (!reportId) return null;
  return {
    reportId,
    scope: cleanString(payload.viewer_report_scope),
    access: cleanString(payload.viewer_report_access),
    preset: cleanString(payload.viewer_report_preset),
    subScope: cleanString(payload.viewer_report_subscope)
  };
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

  const root = document.createElement("section");
  root.className = "docsViewerReport";
  root.dataset.reportId = meta.reportId;
  root.setAttribute("aria-label", "Document report");
  context.content.appendChild(root);

  return loadReportRegistry(context).then(function (registry) {
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
      return Promise.resolve(mount(Object.assign({}, context, {
        reportRoot: root,
        reportMeta: Object.assign({}, meta, { registryEntry: reportMeta }),
        reportRegistry: registry
      }))).then(function () {
        return true;
      });
    });
  }).catch((error) => {
    unavailable(root, error && error.message ? error.message : "Failed to render report.");
    return true;
  });
}
