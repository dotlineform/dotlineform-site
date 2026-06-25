import {
  importText
} from "./docs-html-import-text.js";

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

function resultCountsText(preview) {
  const stats = preview.source_stats && typeof preview.source_stats === "object" ? preview.source_stats : {};
  if (preview.source_format === "markdown" || preview.source_format === "markdown_package") {
    return importText(
      preview.source_format === "markdown_package"
        ? "resultMarkdownPackageCounts"
        : "resultMarkdownCounts",
      {
        chars: Number(stats.chars || 0),
        links: Number(stats.links || 0),
        images: Number(stats.images || 0),
        attachments: Number(stats.attachments || 0)
      }
    );
  }
  return importText(
    "resultSummaryCounts",
    {
      links: Number(stats.links || 0),
      images: Number(stats.images || 0),
      svg: Number(stats.svg || 0),
      details: Number(stats.details || 0)
    }
  );
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
  const sourceLabel = sourceDocLinkHtml(payload.scope, payload.doc_id);
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
      escapeHtml(importText("scriptFileResultType"))
    ];
  })).concat(mediaPlans.map((item) => {
    const sourcePath = normalizeText(item && item.source_path);
    const title = normalizeText(item && item.title) || sourcePath;
    const kind = normalizeText(item && item.kind) || (normalizeText(item && item.media_path).includes("/files/") ? "attachment" : "image");
    const conversion = item && item.conversion && typeof item.conversion === "object" ? item.conversion : {};
    const typeText = kind === "image" && normalizeText(conversion.format)
      ? importText(
        "imageMediaResultType",
        {
          format: normalizeText(conversion.format).toUpperCase(),
          max_width: Number(conversion.max_width || 800)
        }
      )
      : importText("attachmentMediaResultType");
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
    importText("warningsHeading")
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
      ? importText("resultTitleAll", { count: payloads.length })
      : importText("resultTitle")
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
    importText("collisionHeading")
  );
  setText(
    state.collisionBodyNode,
    isInteractiveAssetOverwrite
      ? importText(
        "interactiveAssetCollisionBody"
      )
      : importText(
        "collisionBody"
      )
  );
  setText(
    state.collisionMetaNode,
    isInteractiveAssetOverwrite
      ? importText(
        "interactiveAssetOverwriteRequired",
        {
          path: interactiveTargetText
        }
      )
      : importText(
        "overwriteRequired",
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
