import {
  getStudioTagWriteEndpoint,
  postJson
} from "./studio-transport.js";

export async function postTags(seriesId, workId, tags, keepWork, utcTimestampFn = utcTimestamp, signal, activityContext = null, config = null) {
  const payload = {
    series_id: seriesId,
    tags,
    client_time_utc: utcTimestampFn()
  };
  if (workId != null && workId !== "") {
    payload.work_id = workId;
    payload.keep_work = Boolean(keepWork);
  }
  if (activityContext) {
    payload.activity_context = activityContext;
  }
  return postJson(getStudioTagWriteEndpoint("saveTags", config), payload, { signal });
}

export function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

export function buildTagSaveSuccessMessage(config, summary, analyticsTagEditorText) {
  const seriesSaved = Boolean(summary && summary.seriesSaved);
  const savedCount = Number(summary && summary.savedCount) || 0;
  const removedCount = Number(summary && summary.removedCount) || 0;
  const savedAt = String(summary && summary.savedAt || "");
  const seriesPart = seriesSaved
    ? analyticsTagEditorText(config, "save_status_success_series", "Saved series tags")
    : "";
  const base = analyticsTagEditorText(
    config,
    "save_status_success_base",
    "Saved {saved_count} work row{saved_plural}",
    {
      saved_count: savedCount,
      saved_plural: savedCount === 1 ? "" : "s"
    }
  );
  const removed = removedCount > 0
    ? analyticsTagEditorText(
        config,
        "save_status_success_removed_suffix",
        "; removed {removed_count} row{removed_plural}",
        {
          removed_count: removedCount,
          removed_plural: removedCount === 1 ? "" : "s"
        }
      )
    : "";
  const at = analyticsTagEditorText(
    config,
    "save_status_success_at_suffix",
    " at {saved_at}.",
    { saved_at: savedAt }
  );
  if (seriesPart && savedCount > 0) {
    return `${seriesPart}; ${base.toLowerCase()}${removed}${at}`;
  }
  if (seriesPart) {
    return `${seriesPart}${at}`;
  }
  return `${base}${removed}${at}`;
}
