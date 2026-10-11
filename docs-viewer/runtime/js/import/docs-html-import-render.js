import {
  docsImportResultDestination
} from "../management/docs-viewer-management-import-result.js";

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

function setText(node, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
}

function setHtml(node, value) {
  if (!node) return;
  node.innerHTML = String(value == null ? "" : value);
}

function resultDocLinksHtml(payload) {
  const returnedTarget = payload
    && payload.target
    && typeof payload.target === "object"
    ? payload.target
    : {};
  const normalizedCollection = normalizeText(
    returnedTarget.collection || (payload && payload.collection)
  );
  const normalizedDocId = normalizeText(returnedTarget.doc_id || (payload && payload.doc_id));
  if (!normalizedDocId) return "";
  const sourceLink = [
    `<a href="#" data-doc-source-link="true"`,
    normalizedCollection
      ? ` data-collection="${escapeHtml(normalizedCollection)}"`
      : "",
    ` data-doc-id="${escapeHtml(normalizedDocId)}">`,
    `Source</a>`
  ].join("");
  try {
    const destination = docsImportResultDestination(payload);
    return [
      `<a href="${escapeHtml(destination.href)}" data-doc-destination-link="true">`,
      `${escapeHtml(normalizedDocId)}</a>`,
      ` <span aria-hidden="true">·</span> ${sourceLink}`
    ].join("");
  } catch (_error) {
    return `${escapeHtml(normalizedDocId)} <span aria-hidden="true">·</span> ${sourceLink}`;
  }
}

function resultCountsText(preview) {
  const stats = preview.source_stats && typeof preview.source_stats === "object" ? preview.source_stats : {};
  if (preview.source_format === "markdown" || preview.source_format === "markdown_package") {
    const counts = `${Number(stats.chars || 0)} chars, ${Number(stats.links || 0)} links, ${Number(stats.images || 0)} images`;
    return preview.source_format === "markdown_package"
      ? `${counts}, ${Number(stats.attachments || 0)} attachments`
      : counts;
  }
  return `${Number(stats.links || 0)} links, ${Number(stats.images || 0)} images, ${Number(stats.svg || 0)} SVG, ${Number(stats.details || 0)} details blocks`;
}

function resultRowsForPayload(payload, includeFilename) {
  const preview = payload && payload.import_preview && typeof payload.import_preview === "object"
    ? payload.import_preview
    : {};
  const scriptRows = Array.isArray(payload && payload.interactive_html_written)
    ? payload.interactive_html_written
    : [];
  const mediaPlans = []
    .concat(Array.isArray(preview.media_plans) ? preview.media_plans : [])
    .concat(preview.media_plan && typeof preview.media_plan === "object" ? [preview.media_plan] : []);
  const sourceLabel = resultDocLinksHtml(payload);
  const sourceName = normalizeText(payload && payload.staged_filename);
  const rows = [
    [
      includeFilename && sourceName
        ? `${escapeHtml(sourceName)}: ${sourceLabel}`
        : sourceLabel,
      escapeHtml(resultCountsText(preview))
    ]
  ].concat(scriptRows.map((item) => {
    const displayName = normalizeText(item && item.display_name)
      || normalizeText(item && item.filename).replace(/\.html$/i, "")
      || normalizeText(item && item.target_path).split("/").pop().replace(/\.html$/i, "");
    return [
      escapeHtml(displayName),
      "script file"
    ];
  })).concat(mediaPlans.map((item) => {
    const sourcePath = normalizeText(item && item.source_path);
    const title = normalizeText(item && item.title) || sourcePath;
    const kind = normalizeText(item && item.kind) || (normalizeText(item && item.media_path).includes("/files/") ? "attachment" : "image");
    const conversion = item && item.conversion && typeof item.conversion === "object" ? item.conversion : {};
    const typeText = kind === "image" && normalizeText(conversion.format)
      ? `image, ${normalizeText(conversion.format).toUpperCase()} <= ${Number(conversion.max_width || 800)}px`
      : "attachment";
    const mediaPath = normalizeText(item && (item.media_path || item.media_link || item.media_token));
    return [
      escapeHtml(`${title}${sourcePath && sourcePath !== title ? ` (${sourcePath})` : ""}`),
      escapeHtml(mediaPath ? `${typeText}: ${mediaPath}` : typeText)
    ];
  }));
  return rows;
}

function payloadWarnings(payload, includeFilename) {
  const preview = payload && payload.import_preview && typeof payload.import_preview === "object"
    ? payload.import_preview
    : {};
  const warnings = Array.isArray(preview.warnings) ? preview.warnings : [];
  const sourceName = normalizeText(payload && payload.staged_filename);
  return warnings
    .filter((item) => normalizeText(item))
    .map((item) => includeFilename && sourceName ? `${sourceName}: ${item}` : item);
}

export function resetDocsHtmlImportWarning(state) {
  state.warningNode.hidden = true;
  setText(state.collisionMetaNode, "");
  state.confirmButton.hidden = true;
  state.cancelButton.hidden = true;
}

export function clearDocsHtmlImportResult(state) {
  state.resultNode.hidden = true;
  state.warningsWrap.hidden = true;
  state.warningsList.innerHTML = "";
}

export function renderDocsHtmlImportWarnings(state, warnings) {
  const items = Array.isArray(warnings) ? warnings.filter((item) => normalizeText(item)) : [];
  if (!items.length) {
    state.warningsWrap.hidden = true;
    state.warningsList.innerHTML = "";
    return;
  }
  setText(
    state.warningsHeading,
    "Warnings"
  );
  state.warningsList.innerHTML = items.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");
  state.warningsWrap.hidden = false;
}

export function renderDocsHtmlImportResult(state, payloadOrPayloads) {
  const payloads = Array.isArray(payloadOrPayloads) ? payloadOrPayloads : [payloadOrPayloads].filter(Boolean);
  const includeFilename = payloads.length > 1;
  setText(
    state.resultTitleNode,
    includeFilename
      ? `Imported ${payloads.length} files`
      : "Imported"
  );
  const rows = payloads.flatMap((payload) => resultRowsForPayload(payload, includeFilename));
  setHtml(
    state.resultGridNode,
    rows.map((row, index) => (
      `<div>` +
        `<dd${index === 0 ? ' id="docsHtmlImportResultDocId"' : ""}>${row[0]}</dd>` +
        `<dd${index === 0 ? ' id="docsHtmlImportResultCounts"' : ""}>${row[1]}</dd>` +
      `</div>`
    )).join("")
  );
  renderDocsHtmlImportWarnings(state, payloads.flatMap((payload) => payloadWarnings(payload, includeFilename)));
  state.resultNode.hidden = false;
}

export function renderDocsHtmlImportInteractiveOverwriteWarning(state, payload) {
  const preview = payload && payload.import_preview && typeof payload.import_preview === "object"
    ? payload.import_preview
    : {};
  const interactivePlans = Array.isArray(preview.interactive_html_plans)
    ? preview.interactive_html_plans
    : [];
  const interactiveTargetText = interactivePlans.length === 1
    ? normalizeText(interactivePlans[0] && (interactivePlans[0].target_path || interactivePlans[0].filename))
    : `${interactivePlans.length} script files`;
  setText(
    state.collisionHeadingNode,
    "Replace interactive HTML asset"
  );
  setText(
    state.collisionBodyNode,
    "This import includes an interactive HTML companion that matches an existing asset. Confirm overwrite to replace that asset."
  );
  setText(
    state.collisionMetaNode,
    `Interactive asset overwrite required: ${interactiveTargetText}. Review the warning and confirm if you want to replace it.`
  );
  state.warningNode.hidden = false;
  state.confirmButton.hidden = false;
  state.cancelButton.hidden = false;
}
