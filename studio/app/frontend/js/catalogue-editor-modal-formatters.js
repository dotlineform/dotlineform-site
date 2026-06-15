function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function interpolateText(template, tokens = null) {
  let text = normalizeText(template);
  if (!tokens || typeof tokens !== "object") return text;
  Object.entries(tokens).forEach(([key, value]) => {
    text = text.replaceAll(`{${key}}`, String(value == null ? "" : value));
  });
  return text;
}

function lookupText(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  return interpolateText(fallback, tokens);
}

function formatLocalMediaCounts(counts) {
  if (!counts || typeof counts !== "object") return "";
  const pending = Number(counts.pending) || 0;
  const blocked = Number(counts.blocked) || 0;
  const unavailable = Number(counts.unavailable) || 0;
  const current = Number(counts.current) || 0;
  const mediaParts = [];
  if (pending) mediaParts.push(`local media pending ${pending}`);
  if (blocked) mediaParts.push(`local media blocked ${blocked}`);
  if (unavailable) mediaParts.push(`local media unavailable ${unavailable}`);
  if (!pending && !blocked && !unavailable && current) mediaParts.push(`local media current ${current}`);
  return mediaParts.length ? `${mediaParts.join("; ")}.` : "";
}

export function formatCatalogueBuildPreview(build, options = {}) {
  if (!build || typeof build !== "object") return "";
  const searchText = build.rebuild_search
    ? lookupText(options, "build_preview_search_yes", "yes")
    : lookupText(options, "build_preview_search_no", "no");
  let baseText = "";
  if (options.target === "moment") {
    const momentIds = Array.isArray(build.moment_ids) ? build.moment_ids : [];
    const momentText = momentIds.length ? momentIds.join(", ") : normalizeText(options.fallbackMomentId) || "none";
    baseText = lookupText(
      options,
      "build_preview_template",
      options.defaultTemplate || "Public update preview: moment {moment_ids}; catalogue search {search_rebuild}.",
      {
        moment_ids: momentText,
        search_rebuild: searchText
      }
    );
  } else {
    const workIds = Array.isArray(build.work_ids) ? build.work_ids : [];
    const seriesIds = Array.isArray(build.series_ids) ? build.series_ids : [];
    baseText = lookupText(
      options,
      "build_preview_template",
      options.defaultTemplate || "Build preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.",
      {
        work_ids: workIds.length ? workIds.join(", ") : "none",
        series_ids: seriesIds.length ? seriesIds.join(", ") : "none",
        search_rebuild: searchText
      }
    );
  }

  const localMedia = build.local_media && typeof build.local_media === "object" ? build.local_media : null;
  const localCounts = localMedia && typeof localMedia.counts === "object" ? localMedia.counts : null;
  const mediaText = formatLocalMediaCounts(localCounts);
  return mediaText ? `${baseText} ${mediaText}` : baseText;
}

export function formatCataloguePublicationPreview(preview, options = {}) {
  const summary = normalizeText(preview && preview.summary)
    || lookupText(options, "unpublish_confirm_default", options.defaultText || "Unpublish this source record?");
  const dirtyNote = options.includeDirtyNote
    ? lookupText(options, "unpublish_confirm_dirty_note", "Unsaved form changes will be discarded.")
    : "";
  return dirtyNote ? `${summary}\n\n${dirtyNote}` : summary;
}

export function formatCatalogueDeletePreview(preview, options = {}) {
  return normalizeText(preview && preview.summary)
    || lookupText(options, "delete_confirm_default", options.defaultText || "Delete this source record?");
}
