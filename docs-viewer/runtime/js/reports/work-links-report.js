import { mountWorkResourcesReport } from "./work-resources-report.js";

const REPORT_SCHEMA = "docs_work_links_report_v1";
const WORK_ID_PATTERN = /^[0-9]{5}$/;

function exactKeys(value, keys) {
  return value && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).sort().join(",") === keys;
}

function safeLinkUrl(value) {
  if (typeof value !== "string" || !value || value !== value.trim()
    || Array.from(value).some(character => character === "\\"
      || character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127)) return false;
  try {
    const target = new URL(value, "https://docs.invalid/");
    return ["http:", "https:", "mailto:", "tel:"].includes(target.protocol)
      && !target.username && !target.password;
  } catch (_error) {
    return false;
  }
}

/** Keep authored labels/URLs intact while validating safe browser navigation. */
export function normalizeWorkLinksResponse(payload) {
  const report = payload && payload.report;
  if (!payload || payload.ok !== true || !exactKeys(report, "rows,schema_version")
    || report.schema_version !== REPORT_SCHEMA || !Array.isArray(report.rows)) {
    throw new Error("Work Links report is invalid.");
  }
  return report.rows.map(row => {
    if (!exactKeys(row, "link,work") || !exactKeys(row.work, "title,work_id")
      || typeof row.work.work_id !== "string" || !WORK_ID_PATTERN.test(row.work.work_id)
      || typeof row.work.title !== "string" || !row.work.title.trim()
      || !exactKeys(row.link, "label,url") || typeof row.link.label !== "string" || !row.link.label.trim()
      || !safeLinkUrl(row.link.url)) {
      throw new Error("Work Links row is invalid.");
    }
    return row;
  });
}

export function mountWorkLinksReport(context) {
  const service = context.reportService;
  if (!service || typeof service.runWorkLinks !== "function") {
    throw new Error("Local docs-management server is not configured.");
  }
  return mountWorkResourcesReport(context, {
    reportId: "work_links",
    title: "Work Links",
    resourceHeading: "Links",
    emptyText: "No Work links were found.",
    readRows: async () => normalizeWorkLinksResponse(await service.runWorkLinks()).map(row => ({
      work: row.work, label: row.link.label, href: row.link.url, identity: row.link.url, external: true
    }))
  });
}
