import {
  getStudioText
} from "./studio-config.js";
import {
  labelFromTagId,
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
  const parts = String(tagId || "").split(":", 2);
  const aliasKey = parts.length === 2 ? parts[1] : "";
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

export function buildManualPatchForCreateTag(tagRow) {
  const normalizedTagId = normalize(tagRow && tagRow.tag_id);
  const snippet = JSON.stringify(
    [
      {
        tag_id: normalizedTagId,
        group: normalize(tagRow && tagRow.group),
        label: labelFromTagId(normalizedTagId),
        description: String((tagRow && tagRow.description) || "").trim(),
        updated_at_utc: utcTimestamp()
      }
    ],
    null,
    2
  );
  return {
    kind: "warn",
    message: registryText(
      null,
      "patch_create_message",
      "Patch mode: new tag row prepared for studio/data/canonical/tags/tag-registry.json tags[]."
    ),
    snippet
  };
}

export function buildCreateSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  return `created tag ${normalize(response.tag_id || "")}; final ${Number(response.final_total || 0)}`;
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
