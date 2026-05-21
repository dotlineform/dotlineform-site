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

function formatText(template, tokens = {}) {
  let text = String(template || "");
  Object.keys(tokens).forEach((key) => {
    text = text.replace(new RegExp(`\\{${key}\\}`, "g"), tokens[key]);
  });
  return text;
}

function importText(config, path, fallback, tokens = {}) {
  let current = config;
  String(path || "").split(".").filter(Boolean).forEach((key) => {
    if (current && Object.prototype.hasOwnProperty.call(current, key)) {
      current = current[key];
    } else {
      current = undefined;
    }
  });
  return formatText(String(current == null ? fallback == null ? "" : fallback : current), tokens);
}

function sourceDocLinkHtml(scope, docId) {
  const normalizedScope = normalizeText(scope);
  const normalizedDocId = normalizeText(docId);
  if (!normalizedScope || !normalizedDocId) return "";
  return [
    `<a href="#" data-doc-source-link="true"`,
    ` data-scope="${escapeHtml(normalizedScope)}"`,
    ` data-doc-id="${escapeHtml(normalizedDocId)}">`,
    `${escapeHtml(normalizedDocId)}</a>`
  ].join("");
}

function resultCountsText(config, preview) {
  const stats = preview.source_stats && typeof preview.source_stats === "object" ? preview.source_stats : {};
  if (preview.source_format === "markdown" || preview.source_format === "markdown_package") {
    return importText(
      config,
      preview.source_format === "markdown_package"
        ? "docs_html_import.result_markdown_package_counts"
        : "docs_html_import.result_markdown_counts",
      preview.source_format === "markdown_package"
        ? "{chars} chars, {links} links, {images} images, {attachments} attachments"
        : "{chars} chars, {links} links, {images} images",
      {
        chars: Number(stats.chars || 0),
        links: Number(stats.links || 0),
        images: Number(stats.images || 0),
        attachments: Number(stats.attachments || 0)
      }
    );
  }
  return importText(
    config,
    "docs_html_import.result_summary_counts",
    "{links} links, {images} images, {svg} SVG, {details} details blocks",
    {
      links: Number(stats.links || 0),
      images: Number(stats.images || 0),
      svg: Number(stats.svg || 0),
      details: Number(stats.details || 0)
    }
  );
}

function resultRowsForPayload(config, payload, includeFilename) {
  const preview = payload && payload.import_preview && typeof payload.import_preview === "object"
    ? payload.import_preview
    : {};
  const scriptRows = Array.isArray(payload && payload.interactive_html_written)
    ? payload.interactive_html_written
    : [];
  const mediaPlans = []
    .concat(Array.isArray(preview.media_plans) ? preview.media_plans : [])
    .concat(preview.media_plan && typeof preview.media_plan === "object" ? [preview.media_plan] : []);
  const sourceLabel = sourceDocLinkHtml(payload.scope, payload.doc_id);
  const sourceName = normalizeText(payload && payload.staged_filename);
  const rows = [
    [
      includeFilename && sourceName
        ? `${escapeHtml(sourceName)}: ${sourceLabel}`
        : sourceLabel,
      escapeHtml(resultCountsText(config, preview))
    ]
  ].concat(scriptRows.map((item) => {
    const displayName = normalizeText(item && item.display_name)
      || normalizeText(item && item.filename).replace(/\.html$/i, "")
      || normalizeText(item && item.target_path).split("/").pop().replace(/\.html$/i, "");
    return [
      escapeHtml(displayName),
      escapeHtml(importText(config, "docs_html_import.script_file_result_type", "script file"))
    ];
  })).concat(mediaPlans.map((item) => {
    const sourcePath = normalizeText(item && item.source_path);
    const title = normalizeText(item && item.title) || sourcePath;
    const kind = normalizeText(item && item.kind) || (normalizeText(item && item.media_path).includes("/files/") ? "attachment" : "image");
    const conversion = item && item.conversion && typeof item.conversion === "object" ? item.conversion : {};
    const typeText = kind === "image" && normalizeText(conversion.format)
      ? importText(
        config,
        "docs_html_import.image_media_result_type",
        "image, {format} <= {max_width}px",
        {
          format: normalizeText(conversion.format).toUpperCase(),
          max_width: Number(conversion.max_width || 800)
        }
      )
      : importText(config, "docs_html_import.attachment_media_result_type", "attachment");
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
  state.pendingOverwriteDocId = "";
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
    importText(state.config, "docs_html_import.warnings_heading", "Warnings")
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
      ? importText(state.config, "docs_html_import.result_title_all", "Imported {count} files", { count: payloads.length })
      : importText(state.config, "docs_html_import.result_title", "Imported")
  );
  const rows = payloads.flatMap((payload) => resultRowsForPayload(state.config, payload, includeFilename));
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

export function renderDocsHtmlImportOverwriteWarning(state, payload) {
  const collision = payload && payload.collision && typeof payload.collision === "object" ? payload.collision : {};
  const preview = payload && payload.import_preview && typeof payload.import_preview === "object"
    ? payload.import_preview
    : {};
  const interactivePlans = Array.isArray(preview.interactive_html_plans)
    ? preview.interactive_html_plans
    : [];
  const interactiveTargetText = interactivePlans.length === 1
    ? normalizeText(interactivePlans[0] && (interactivePlans[0].target_path || interactivePlans[0].filename))
    : `${interactivePlans.length} script files`;
  const isInteractiveAssetOverwrite = Boolean(payload && payload.requires_interactive_html_confirmation);
  state.pendingOverwriteDocId = normalizeText(collision.doc_id);
  setText(
    state.collisionHeadingNode,
    importText(state.config, "docs_html_import.collision_heading", "Overwrite warning")
  );
  setText(
    state.collisionBodyNode,
    isInteractiveAssetOverwrite
      ? importText(
        state.config,
        "docs_html_import.interactive_asset_collision_body",
        "This import includes an interactive HTML companion that matches an existing asset. Confirm overwrite to replace that asset."
      )
      : importText(
        state.config,
        "docs_html_import.collision_body",
        "This import matches an existing doc target. Confirm overwrite to replace the current source while keeping the same doc identity and filename."
      )
  );
  setText(
    state.collisionMetaNode,
    isInteractiveAssetOverwrite
      ? importText(
        state.config,
        "docs_html_import.interactive_asset_overwrite_required",
        "Interactive asset overwrite required: {path}. Review the warning and confirm if you want to replace it.",
        {
          path: interactiveTargetText
        }
      )
      : importText(
        state.config,
        "docs_html_import.overwrite_required",
        "Overwrite required: {doc_id} ({title}). Review the warning and confirm if you want to replace it.",
        {
          doc_id: collision.doc_id || preview.proposed_doc_id || "",
          title: collision.title || preview.title || ""
        }
      )
  );
  state.warningNode.hidden = false;
  state.confirmButton.hidden = false;
  state.cancelButton.hidden = false;
}
