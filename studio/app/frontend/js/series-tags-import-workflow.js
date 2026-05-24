import {
  getStudioText
} from "./studio-config.js";
import {
  getStudioAssignmentsSeries,
  loadStudioAssignmentsJson
} from "./studio-data.js";
import {
  getStudioWriteEndpoint,
  postJson,
} from "./studio-transport.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";

export async function previewSeriesTagsImport(options = {}) {
  const { file, config } = options;
  if (!file) {
    return {
      ok: false,
      resultKind: "error",
      resultText: seriesTagsText(config, "session_import_no_file", "No import file selected.")
    };
  }

  let importPayload = null;
  try {
    importPayload = JSON.parse(await file.text());
  } catch (error) {
    return {
      ok: false,
      resultKind: "error",
      resultText: seriesTagsText(config, "session_import_invalid_json", "Import file is not valid JSON.")
    };
  }

  try {
    const importPreview = await postJson(getStudioWriteEndpoint("importTagAssignmentsPreview", config), {
      import_assignments: importPayload,
      import_filename: file.name || "",
      client_time_utc: new Date().toISOString()
    });
    return {
      ok: true,
      importPayload,
      importPreview,
      importResolutions: defaultImportResolutions(importPreview),
      resultKind: "success",
      resultText: String(importPreview.summary_text || seriesTagsText(config, "session_import_preview_success", "Import preview ready."))
    };
  } catch (error) {
    return {
      ok: false,
      importPayload,
      resultKind: "error",
      resultText: String(error && error.message ? error.message : seriesTagsText(config, "session_import_preview_failed", "Import preview failed."))
    };
  }
}

export async function applySeriesTagsImport(options = {}) {
  const {
    config,
    file,
    importPayload,
    importPreview,
    importResolutions
  } = options;

  if (!importPayload || !importPreview) {
    return {
      ok: false,
      resultKind: "error",
      resultText: seriesTagsText(config, "session_import_apply_without_preview", "Preview the import before applying it.")
    };
  }

  try {
    const filename = file && file.name ? file.name : "";
    const response = await postJson(getStudioWriteEndpoint("importTagAssignments", config), {
      import_assignments: importPayload,
      import_filename: filename,
      resolutions: importResolutions || {},
      client_time_utc: new Date().toISOString(),
      activity_context: buildStudioActivityContext({
        pageId: "series-tags",
        actionId: "import-series-tag-assignments",
        route: "/studio/analytics/series-tags/",
        controlId: "apply-import",
        controlSelector: "[data-import-action=\"apply-import\"]",
        recordIdField: "import_filename",
        recordId: filename || "series-tags-import"
      })
    });
    return {
      ok: true,
      response,
      assignmentsSeries: getStudioAssignmentsSeries(await loadStudioAssignmentsJson(config, { cache: "no-store" })),
      resultKind: "success",
      resultText: String(response.summary_text || seriesTagsText(config, "session_import_apply_success", "Import applied."))
    };
  } catch (error) {
    return {
      ok: false,
      resultKind: "error",
      resultText: String(error && error.message ? error.message : seriesTagsText(config, "session_import_apply_failed", "Import failed."))
    };
  }
}

function defaultImportResolutions(importPreview) {
  const resolutions = {};
  for (const row of importPreview && importPreview.series || []) {
    if (String(row && row.status || "") === "conflict") {
      resolutions[String(row.series_id || "").trim().toLowerCase()] = "skip";
    }
  }
  return resolutions;
}

function seriesTagsText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tags.${key}`, fallback, tokens);
}
