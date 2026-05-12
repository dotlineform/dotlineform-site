const REPORTS = {
  docs_index_table: {
    defaultAccess: "public",
    load: function () {
      return import("./reports/docs-index-table-report.js").then(function (module) {
        return module.mountDocsIndexTableReport;
      });
    }
  }
};

function cleanString(value) {
  return String(value || "").trim();
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

function canMountReport(meta, report, context) {
  const access = meta.access || report.defaultAccess || "public";
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

  const report = REPORTS[meta.reportId];
  const root = document.createElement("section");
  root.className = "docsViewerReport";
  root.dataset.reportId = meta.reportId;
  root.setAttribute("aria-label", "Document report");
  context.content.appendChild(root);

  if (!report) {
    unavailable(root, "This report type is not available.");
    return Promise.resolve(true);
  }

  return canMountReport(meta, report, context).then((result) => {
    if (!result.ok) {
      unavailable(root, accessMessage(result.access));
      return true;
    }
    root.innerHTML = '<p class="docsViewerReport__status">Loading report...</p>';
    return report.load().then(function (mount) {
      return Promise.resolve(mount(Object.assign({}, context, {
        reportRoot: root,
        reportMeta: meta
      }))).then(function () {
        return true;
      });
    });
  }).catch((error) => {
    unavailable(root, error && error.message ? error.message : "Failed to render report.");
    return true;
  });
}
