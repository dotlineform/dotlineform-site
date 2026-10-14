import { mountWorkResourcesReport } from "./work-resources-report.js";

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

/** Consume saved labels literally; retain URL safety at the navigation boundary. */
export function buildWorkLinkRows(report) {
  return report.rows.map(row => {
    if (!safeLinkUrl(row.link.url)) throw new Error("Work link URL is unsafe.");
    return { work: row.work, label: row.link.label, href: row.link.url, identity: row.link.url, external: true };
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
    readRows: async () => buildWorkLinkRows((await service.runWorkLinks()).report)
  });
}
