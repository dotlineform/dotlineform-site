import { mountWorkResourcesReport } from "./work-resources-report.js";

const REPORT_SCHEMA = "docs_work_downloads_report_v1";
const WORK_ID_PATTERN = /^[0-9]{5}$/;

function exactKeys(value, keys) {
  return value && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).sort().join(",") === keys;
}

function isFilename(value) {
  return typeof value === "string" && value.length > 0 && value === value.trim()
    && ![".", ".."].includes(value) && !value.includes("/") && !value.includes("\\")
    && !Array.from(value).some(character => character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127);
}

/** Validate exact Work/file matches; shared presentation owns ordering. */
export function normalizeWorkDownloadsResponse(payload) {
  const report = payload && payload.report;
  if (!payload || payload.ok !== true || !exactKeys(report, "rows,schema_version")
    || report.schema_version !== REPORT_SCHEMA || !Array.isArray(report.rows)) {
    throw new Error("Work Downloads report is invalid.");
  }
  return report.rows.map(row => {
    if (!exactKeys(row, "file,work") || (row.file !== null && !isFilename(row.file))) {
      throw new Error("Work Downloads row is invalid.");
    }
    if (row.work !== null && (!exactKeys(row.work, "filename,title,work_id")
      || typeof row.work.work_id !== "string" || !WORK_ID_PATTERN.test(row.work.work_id)
      || typeof row.work.title !== "string" || !row.work.title.trim() || !isFilename(row.work.filename)
      || (row.file !== null && row.file !== row.work.filename))) {
      throw new Error("Work Downloads Work reference is invalid.");
    }
    if (row.work === null && row.file === null) throw new Error("Work Downloads row is empty.");
    return row;
  });
}

/** Keep Downloads validation and Finder activation in this report's adapter. */
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
    readRows: async () => normalizeWorkDownloadsResponse(await service.runWorkDownloads()).map(row => ({
      work: row.work, label: row.file || "", href: "#", filename: row.file || "",
      identity: row.work?.filename || row.file
    })),
    openFile: filename => service.openWorkDownload(filename)
  });
}
