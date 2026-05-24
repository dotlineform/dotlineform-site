function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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

export function formatCatalogueFieldPlanList(value, options = {}) {
  const emptyText = Object.prototype.hasOwnProperty.call(options, "emptyText")
    ? normalizeText(options.emptyText)
    : "none";
  return Array.isArray(value) && value.length
    ? value.map((item) => normalizeText(item)).filter(Boolean).join(", ") || emptyText
    : emptyText;
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

export function formatCatalogueBuildPreviewModalHtml(response, changedFields, options = {}) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  const fieldPlan = response && response.field_plan && typeof response.field_plan === "object"
    ? response.field_plan
    : build && build.field_plan && typeof build.field_plan === "object"
      ? build.field_plan
      : null;
  const summary = formatCatalogueBuildPreview(build, options)
    || lookupText(options, "build_preview_no_result", "No public update work selected.");
  const rules = fieldPlan ? formatCatalogueFieldPlanList(fieldPlan.rule_ids) : "none";
  const artifacts = fieldPlan ? formatCatalogueFieldPlanList(fieldPlan.artifacts) : "none";
  const explanations = fieldPlan && Array.isArray(fieldPlan.explanations) ? fieldPlan.explanations : [];
  const explanationGroups = new Map();
  explanations.forEach((row) => {
    const artifact = normalizeText(row && row.artifact);
    const reason = normalizeText(row && row.reason);
    if (!artifact && !reason) return;
    const key = reason || "selected by registry rule";
    const current = explanationGroups.get(key) || [];
    if (artifact) current.push(artifact);
    explanationGroups.set(key, current);
  });
  const explanationLines = Array.from(explanationGroups.entries()).map(([reason, groupedArtifacts]) => {
    const artifactText = groupedArtifacts.length ? formatCatalogueFieldPlanList(groupedArtifacts) : "artifact";
    return `${artifactText}: ${reason}`;
  });
  const details = [
    lookupText(options, "build_preview_modal_changed_fields", "Changed fields: {fields}.", {
      fields: formatCatalogueFieldPlanList(changedFields)
    }),
    lookupText(options, "build_preview_modal_rules", "Rules: {rules}.", { rules }),
    lookupText(options, "build_preview_modal_artifacts", "Artifacts: {artifacts}.", { artifacts })
  ];
  const reasonsText = explanationLines.length
    ? `${lookupText(options, "build_preview_modal_reasons_heading", "Reasons:")}\n${explanationLines.map((line) => `- ${line}`).join("\n")}`
    : "";
  const reasonsClass = normalizeText(options.reasonsClass);

  return `
    <p class="tagStudioForm__impact">${escapeHtml(summary)}</p>
    ${details.map((line) => `<p class="tagStudioModal__label">${escapeHtml(line)}</p>`).join("")}
    ${reasonsText ? `<pre class="tagStudioModal__pre${reasonsClass ? ` ${escapeHtml(reasonsClass)}` : ""}">${escapeHtml(reasonsText)}</pre>` : ""}
  `;
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
