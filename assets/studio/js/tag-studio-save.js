import {
  STUDIO_WRITE_ENDPOINTS,
  postJson
} from "./studio-transport.js";

export async function postTags(seriesId, workId, tags, keepWork, utcTimestampFn = utcTimestamp, signal) {
  return postJson(
    STUDIO_WRITE_ENDPOINTS.saveTags,
    {
      series_id: seriesId,
      work_id: workId,
      tags,
      keep_work: Boolean(keepWork),
      client_time_utc: utcTimestampFn()
    },
    { signal }
  );
}

export function buildPatchSnippet(seriesId, diff, timestamp) {
  if (!diff || !diff.changedWorkIds.length) return "";
  const setBlocks = diff.changedWorkIds
    .filter((workId) => diff.nextWorkStateById.has(workId))
    .map((workId) => {
      const tagsText = JSON.stringify(diff.nextWorkStateById.get(workId) || [], null, 2).replace(/\n/g, "\n      ");
      return [
        `${JSON.stringify(workId)}: {`,
        `  "tags": ${tagsText},`,
        `  "updated_at_utc": ${JSON.stringify(timestamp)}`,
        "}"
      ].join("\n");
    });
  const deleteWorkIds = diff.changedWorkIds.filter((workId) => !diff.nextWorkStateById.has(workId));
  return [
    setBlocks.length ? `Under series[${JSON.stringify(seriesId)}].works, set:\n${setBlocks.join("\n")}` : "",
    deleteWorkIds.length ? `Under series[${JSON.stringify(seriesId)}].works, delete: ${deleteWorkIds.map((workId) => JSON.stringify(workId)).join(", ")}` : "",
    "If the works object becomes empty, delete the works object too.",
    `Update series[${JSON.stringify(seriesId)}].updated_at_utc to ${JSON.stringify(timestamp)}.`,
    `Update the top-level updated_at_utc to ${JSON.stringify(timestamp)}.`
  ].filter(Boolean).join("\n\n");
}

export function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

export function buildSaveModeText(config, mode, studioText) {
  const label = mode === "post"
    ? studioText(config, "save_mode_local_server", "Local server")
    : studioText(config, "save_mode_patch", "Patch");
  return studioText(config, "save_mode_template", "Save mode: {mode}", { mode: label });
}

export function buildSaveSuccessMessage(config, savedCount, removedCount, savedAt, studioText) {
  const base = studioText(
    config,
    "save_status_success_base",
    "Saved {saved_count} work row{saved_plural}",
    {
      saved_count: savedCount,
      saved_plural: savedCount === 1 ? "" : "s"
    }
  );
  const removed = removedCount > 0
    ? studioText(
        config,
        "save_status_success_removed_suffix",
        "; removed {removed_count} row{removed_plural}",
        {
          removed_count: removedCount,
          removed_plural: removedCount === 1 ? "" : "s"
        }
      )
    : "";
  const at = studioText(
    config,
    "save_status_success_at_suffix",
    " at {saved_at}.",
    { saved_at: savedAt }
  );
  return `${base}${removed}${at}`;
}
