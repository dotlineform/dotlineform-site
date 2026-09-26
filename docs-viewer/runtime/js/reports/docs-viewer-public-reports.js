import {
  appendAssetVersion
} from "../shared/docs-viewer-asset-url.js";
import { mountDocsViewerMediaLinks } from "../shared/docs-viewer-media-detail.js";

const PUBLIC_REPORT_LOADERS = {
  selected_documents: {
    load: function () {
      return import("./selected-documents-report.js").then(function (module) {
        return module.mountSelectedDocumentsReport;
      });
    }
  },
  docs_collection: {
    load: function () {
      return import("../shared/docs-collection-report.js").then(function (module) {
        return module.mountDocsCollectionReport;
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
    if (PUBLIC_REPORT_LOADERS[report.loaderId]) reportsById.set(report.reportId, report);
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
    preset: cleanString(report.preset),
    collection: cleanString(report.collection)
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
  note.className = "docsViewer__panelStatus muted small";
  note.textContent = message;
  root.appendChild(note);
}

function canMountPublicReport(reportMeta) {
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

  function isCurrent() {
    return hostIsCurrent(root, context.content)
      && (typeof context.isCurrentDocument !== "function" || context.isCurrentDocument());
  }

  return loadReportRegistry(context).then(function (registry) {
    if (!isCurrent()) return false;
    const reportMeta = registry.reportsById.get(meta.reportId);
    if (!reportMeta) {
      unavailable(root, "This report has not been promoted for public routes.");
      return true;
    }

    const availability = canMountPublicReport(reportMeta);
    if (!availability.ok) {
      unavailable(root, availability.message);
      return true;
    }

    root.innerHTML = '<p class="docsViewer__panelStatus muted small">Loading report...</p>';
    return PUBLIC_REPORT_LOADERS[reportMeta.loaderId].load().then(function (mount) {
      if (!isCurrent()) return false;
      const resolvedReportMeta = Object.assign({}, meta, { registryEntry: reportMeta });
      return Promise.resolve(mount(Object.assign({}, context, {
        reportRoot: root,
        reportMeta: resolvedReportMeta,
        reportRegistry: registry,
        mountCollectionDocumentContent: function (child) {
          var target = child.documentTarget;
          mountDocsViewerMediaLinks({
            content: child.content,
            documentTarget: { ...(target.stage ? { stage: target.stage } : {}),
              collection: target.collection, docId: target.doc_id },
            isCurrentDocument: child.isCurrentDocument,
            openMediaTarget: context.openMediaTarget,
            loadMediaTarget: context.loadMediaTarget,
            openMediaPresentation: context.openMediaPresentation
          });
          if (typeof context.mountThemedDiagrams === "function") context.mountThemedDiagrams();
          if (!child.payload.report) return Promise.resolve();
          return mountDocsViewerPublicReport(Object.assign({}, context, child, {
            onCollectionDocumentState: null
          }));
        }
      }))).then(function () {
        if (!isCurrent()) return false;
        return true;
      });
    });
  }).catch((error) => {
    if (isCurrent()) {
      unavailable(root, error && error.message ? error.message : "Failed to render report.");
    }
    return true;
  });
}
