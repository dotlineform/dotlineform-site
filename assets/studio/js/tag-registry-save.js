import {
  getStudioText
} from "./studio-config.js";
import {
  labelFromSlug,
  labelFromTagId,
  normalize,
  normalizeTimestamp
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

export function normalizeImportTag(raw, idx, groups) {
  if (!raw || typeof raw !== "object") {
    throw new Error(registryText(null, "import_tag_object_invalid", "Import tag at index {index} must be an object.", { index: idx }));
  }

  const tagId = normalize(raw.tag_id);
  const group = normalize(raw.group);
  const status = normalize(raw.status || "active");
  const description = String(raw.description || "").trim();

  if (!tagId || tagId.indexOf(":") <= 0) {
    throw new Error(registryText(null, "import_tag_invalid_tag_id", "Import tag {index} has invalid tag_id.", { index: idx }));
  }
  if (!Array.isArray(groups) || !groups.includes(group)) {
    throw new Error(registryText(null, "import_tag_invalid_group", "Import tag {index} has invalid group.", { index: idx }));
  }
  if (!["active", "deprecated", "candidate"].includes(status)) {
    throw new Error(registryText(null, "import_tag_invalid_status", "Import tag {index} has invalid status.", { index: idx }));
  }

  const tagGroup = tagId.split(":", 1)[0];
  if (tagGroup !== group) {
    throw new Error(registryText(null, "import_tag_group_prefix_mismatch", "Import tag {index} group must match tag_id prefix.", { index: idx }));
  }

  const [, slug = ""] = tagId.split(":", 2);

  return {
    tag_id: tagId,
    group,
    label: labelFromSlug(slug),
    status,
    description
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
        status: normalize((tagRow && tagRow.status) || "active"),
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
      "Patch mode: new tag row prepared for assets/studio/data/tag_registry.json tags[]."
    ),
    snippet
  };
}

export function buildManualPatchForNewTags(state, importRegistry) {
  const importTags = Array.isArray(importRegistry && importRegistry.tags) ? importRegistry.tags : [];
  const existingIds = new Set(state.tags.map((tag) => tag.tagId));
  const nowUtc = utcTimestamp();

  const newTags = importTags
    .filter((tag) => tag && typeof tag === "object" && !existingIds.has(normalize(tag.tag_id)))
    .map((tag) => ({
      tag_id: normalize(tag.tag_id),
      group: normalize(tag.group),
      label: labelFromTagId(normalize(tag.tag_id)),
      status: normalize(tag.status || "active"),
      description: String(tag.description || "").trim(),
      updated_at_utc: nowUtc
    }));

  if (!newTags.length) {
    return {
      kind: "warn",
      message: registryText(
        state.config,
        "patch_import_none_message",
        "Patch mode ({import_mode}): {imported_count} imported; 0 new tags to add.",
        {
          import_mode: state.importMode,
          imported_count: importTags.length
        }
      ),
      snippet: ""
    };
  }

  const snippet = JSON.stringify(
    newTags,
    null,
    2
  );

  return {
    kind: "warn",
    message: registryText(
      state.config,
      "patch_import_message",
      "Patch mode ({import_mode}): {imported_count} imported; {new_count} new tag rows prepared for assets/studio/data/tag_registry.json tags[].",
      {
        import_mode: state.importMode,
        imported_count: importTags.length,
        new_count: newTags.length
      }
    ),
    snippet
  };
}

export function buildImportSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  const mode = normalize(response.mode || "");
  return [
    `mode ${mode || "unknown"}`,
    `Imported ${Number(response.imported_total || 0)} tags`,
    `added ${Number(response.added || 0)}`,
    `overwritten ${Number(response.overwritten || 0)}`,
    `unchanged ${Number(response.unchanged || 0)}`,
    `removed ${Number(response.removed || 0)}`,
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

export function buildRegistryImportModeText(state, mode) {
  const label = mode === "post"
    ? registryText(state.config, "import_mode_local_server", "Local server")
    : registryText(state.config, "import_mode_patch", "Patch");
  return registryText(state.config, "import_mode_template", "Import mode: {mode}", { mode: label });
}

export function readImportRegistryPayload(payload, groups) {
  if (!payload || typeof payload !== "object") {
    throw new Error(registryText(null, "import_invalid_object", "Import file must be a JSON object."));
  }

  const rawTags = Array.isArray(payload.tags) ? payload.tags : null;
  if (!rawTags) {
    throw new Error(registryText(null, "import_missing_tags_array", "Import file must include a tags array."));
  }

  const normalizedTags = [];
  const seen = new Set();
  for (let idx = 0; idx < rawTags.length; idx += 1) {
    const normalizedTag = normalizeImportTag(rawTags[idx], idx, groups);
    if (!normalizedTag) continue;
    if (seen.has(normalizedTag.tag_id)) {
      const replaceIndex = normalizedTags.findIndex((item) => item.tag_id === normalizedTag.tag_id);
      if (replaceIndex >= 0) normalizedTags[replaceIndex] = normalizedTag;
      continue;
    }
    seen.add(normalizedTag.tag_id);
    normalizedTags.push(normalizedTag);
  }

  return {
    tag_registry_version: String(payload.tag_registry_version || "tag_registry_v1"),
    updated_at_utc: normalizeTimestamp(payload.updated_at_utc) || "",
    policy: payload.policy && typeof payload.policy === "object" ? payload.policy : undefined,
    tags: normalizedTags
  };
}

export function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}
