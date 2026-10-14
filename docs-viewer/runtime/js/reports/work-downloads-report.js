import { mountWorkResourcesReport } from "./work-resources-report.js";

/** Match supplied references once, retaining missing, shared and unassigned files. */
export function buildWorkDownloadRows(report) {
  const files = new Set(report.files);
  const referenced = new Set();
  const rows = [];
  report.works.forEach(record => {
    const work = { work_id: record.work_id, title: record.title };
    record.download_filenames.forEach(filename => {
      referenced.add(filename);
      const file = files.has(filename) ? filename : "";
      rows.push({ work, label: file, href: "#", filename: file, identity: filename });
    });
  });
  files.forEach(filename => {
    if (!referenced.has(filename)) {
      rows.push({ work: null, label: filename, href: "#", filename, identity: filename });
    }
  });
  return rows;
}

/** Keep Downloads composition and Finder activation in this report's adapter. */
export function mountWorkDownloadsReport(context) {
  const service = context.reportService;
  if (!service || typeof service.runWorkDownloads !== "function" || typeof service.openWorkDownload !== "function") {
    throw new Error("Local docs-management server is not configured.");
  }
  return mountWorkResourcesReport(context, {
    reportId: "work_downloads",
    title: "Work Downloads",
    resourceHeading: "File",
    emptyText: "No Work downloads or saved files were found.",
    readRows: async () => buildWorkDownloadRows((await service.runWorkDownloads()).report),
    openFile: filename => service.openWorkDownload(filename)
  });
}
