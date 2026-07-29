import {
  getStudioText
} from "./studio-config.js";
import {
  normalize
} from "./tag-registry-domain.js";

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
}

export function buildDeletePreviewPayload(tagId, utcTimestampFn = utcTimestamp) {
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId) return null;
  return {
    action: "delete",
    tag_id: normalizedTagId,
    client_time_utc: utcTimestampFn()
  };
}

export function buildManualPatchForDemote(tagId, aliasTargets) {
  const aliasKey = normalize(tagId);
  const aliasValue = {
    description: "",
    tags: aliasTargets.slice()
  };

  const snippet = JSON.stringify(
    {
      tag_registry: {
        remove_tag_ids: [tagId]
      },
      tag_aliases: {
        set_aliases: {
          [aliasKey]: aliasValue
        },
        replace_target_refs: {
          from: tagId,
          to: aliasTargets
        }
      },
      tag_assignments: {
        replace_tag_refs: {
          from: tagId,
          to: aliasTargets
        }
      }
    },
    null,
    2
  );

  return {
    kind: "warn",
    message: registryText(
      null,
      "patch_demote_message",
      "Patch mode: section snippets prepared for demoting \"{tag_id}\".",
      { tag_id: tagId }
    ),
    snippet
  };
}

function localDocumentTimestamp(date = new Date()) {
  const part = (value) => String(value).padStart(2, "0");
  return [
    `${date.getFullYear()}-${part(date.getMonth() + 1)}-${part(date.getDate())}`,
    `${part(date.getHours())}:${part(date.getMinutes())}:${part(date.getSeconds())}`
  ].join(" ");
}

function randomDocumentSuffix() {
  const bytes = new Uint8Array(3);
  globalThis.crypto.getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

export function buildManualPatchForCreateTag(tagRow, options = {}) {
  const normalizedTagId = normalize(tagRow && tagRow.tag_id);
  const group = normalize(tagRow && tagRow.group);
  const addedDate = String(options.addedDate || localDocumentTimestamp()).trim();
  const suffix = String(options.suffix || randomDocumentSuffix()).trim();
  const updatedAtUtc = String(options.updatedAtUtc || utcTimestamp()).trim();
  const dateParts = addedDate.match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/);
  if (!dateParts || !/^[0-9a-f]{6}$/.test(suffix)) {
    throw new Error("Could not allocate manual patch document identity.");
  }
  const docId = [
    "d",
    dateParts.slice(1, 4).join(""),
    dateParts.slice(4, 7).join(""),
    suffix
  ].join("-");
  const documentPath = `docs-viewer/scopes/analysis/source/sub-scopes/tags/documents/${docId}.md`;
  const documentBody = `# ${normalizedTagId}\n`;
  const runtime = options.config && options.config.app && options.config.app.runtime;
  const tagService = runtime && runtime.services && runtime.services.tags;
  const documentUrlTemplate = String(
    options.documentUrlTemplate
    || (tagService && tagService.analysis_tags_document_url_template)
    || ""
  ).trim();
  if (!documentUrlTemplate.includes("{doc_id}")) {
    throw new Error("Missing canonical Analysis tag document URL template.");
  }
  const documentUrl = documentUrlTemplate.replace("{doc_id}", docId);
  const documentSource = [
    "---",
    `doc_id: ${docId}`,
    `title: ${JSON.stringify(normalizedTagId)}`,
    `added_date: ${JSON.stringify(addedDate)}`,
    `last_updated: ${dateParts.slice(1, 4).join("-")}`,
    `group: ${group}`,
    'parent_id: ""',
    "viewable: true",
    "---",
    documentBody
  ].join("\n");
  const snippet = JSON.stringify(
    {
      notice: "Nothing has been written. Apply the Registry and Markdown changes together.",
      guards: [
        `Refuse if tag_id already exists: ${normalizedTagId}`,
        `Refuse if doc_id or destination already exists: ${docId}`
      ],
      registry: {
        path: "studio/data/canonical/tags/tag-registry.json",
        root_updated_at_utc: updatedAtUtc,
        append_row: {
          tag_id: normalizedTagId,
          group,
          doc_url: [documentUrl],
          updated_at_utc: updatedAtUtc
        }
      },
      document: {
        path: documentPath,
        source: documentSource
      },
      rebuild: [
        "docs-viewer/build/build_docs.py --scope analysis --sub-scope tags",
        "--write --skip-browser-config"
      ].join(" ")
    },
    null,
    2
  );
  return {
    kind: "warn",
    message: registryText(
      null,
      "patch_create_message",
      "Patch mode: linked Registry row and Analysis tag document prepared; nothing has been written."
    ),
    snippet
  };
}

export function buildCreateSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  return [
    `created tag ${normalize(response.tag_id || "")}`,
    `linked Analysis document ${normalize(response.doc_id || "")}`,
    `final ${Number(response.final_total || 0)}`
  ].join("; ");
}

export function buildMutationSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  const action = normalize(response.action || "");
  const oldTagId = String(response.old_tag_id || "");
  const newTagId = String(response.new_tag_id || "");
  const seriesRows = Number(response.series_rows_touched || 0);
  const refs = Number(response.series_tag_refs_rewritten || 0);
  const aliasesRewritten = Number(response.aliases_rewritten || 0);
  const aliasesRemovedEmpty = Number(response.aliases_removed_empty || 0);
  const aliasesRemovedRedundant = Number(response.aliases_removed_redundant || 0);
  const idPart = newTagId ? `${oldTagId} -> ${newTagId}` : oldTagId;
  return [
    `mode ${action || "unknown"}`,
    `tag ${idPart}`,
    `series rows ${seriesRows}`,
    `refs ${refs}`,
    `aliases rewritten ${aliasesRewritten}`,
    `aliases removed-empty ${aliasesRemovedEmpty}`,
    `aliases removed-redundant ${aliasesRemovedRedundant}`
  ].join("; ");
}

export function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}
