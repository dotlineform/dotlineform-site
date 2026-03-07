import {
  getStudioText
} from "./studio-config.js";
import {
  normalize,
  normalizeImportAliasRows,
  normalizeTimestamp
} from "./tag-aliases-domain.js";

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
}

export function buildManualPatchForNewAliases(state, importAliases) {
  const importRows = normalizeImportAliasRows(importAliases.aliases || {}, aliasText);
  const existing = new Set(state.aliases.map((entry) => entry.alias));
  const aliasesToAdd = {};
  let newCount = 0;

  for (const row of importRows) {
    if (existing.has(row.alias)) continue;
    aliasesToAdd[row.alias] = row.value;
    newCount += 1;
  }

  if (newCount === 0) {
    return {
      kind: "warn",
      message: aliasesText(
        state.config,
        "patch_import_none_message",
        "Patch mode ({import_mode}): {imported_count} imported; 0 new aliases to add.",
        {
          import_mode: state.importMode,
          imported_count: importRows.length
        }
      ),
      snippet: ""
    };
  }

  return {
    kind: "warn",
    message: aliasesText(
      state.config,
      "patch_import_message",
      "Patch mode ({import_mode}): {imported_count} imported; {new_count} alias rows prepared for assets/studio/data/tag_aliases.json aliases object.",
      {
        import_mode: state.importMode,
        imported_count: importRows.length,
        new_count: newCount
      }
    ),
    snippet: JSON.stringify(aliasesToAdd, null, 2)
  };
}

export function buildImportSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  const mode = normalize(response.mode || "");
  return [
    `mode ${mode || "unknown"}`,
    `Imported ${Number(response.imported_total || 0)} aliases`,
    `added ${Number(response.added || 0)}`,
    `overwritten ${Number(response.overwritten || 0)}`,
    `unchanged ${Number(response.unchanged || 0)}`,
    `removed ${Number(response.removed || 0)}`,
    `final ${Number(response.final_total || 0)}`
  ].join("; ");
}

export function buildManualPatchForAliasPromote(state, aliasKey, group) {
  const newTagId = `${group}:${aliasKey}`;
  const canonicalExists = state.registryById.has(newTagId);
  const sectionSnippet = {
    tag_registry: {},
    tag_aliases: {
      remove_alias_keys: [aliasKey]
    }
  };

  if (!canonicalExists) {
    sectionSnippet.tag_registry = {
      tags_append: [
        {
          tag_id: newTagId,
          group,
          label: aliasKey,
          status: "active",
          description: "",
          updated_at_utc: utcTimestamp()
        }
      ]
    };
  }

  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_promote_message",
      "Patch mode: section snippets prepared for promoting \"{alias_key}\".",
      { alias_key: aliasKey }
    ),
    snippet: JSON.stringify(sectionSnippet, null, 2)
  };
}

export function buildManualPatchForAliasDelete(aliasKey) {
  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_delete_message",
      "Patch mode: remove this alias key from assets/studio/data/tag_aliases.json aliases object."
    ),
    snippet: JSON.stringify({ remove_alias_keys: [aliasKey] }, null, 2)
  };
}

export function buildManualPatchForAliasCreate(aliasKey, description, tags) {
  const normalizedAlias = normalize(aliasKey);
  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_create_message",
      "Patch mode: alias fragment prepared for new alias \"{alias_key}\". Paste inside aliases object.",
      { alias_key: normalizedAlias }
    ),
    snippet: JSON.stringify({
      [normalizedAlias]: {
        description: String(description || "").trim(),
        tags: Array.isArray(tags) ? tags.slice() : []
      }
    }, null, 2)
  };
}

export function buildManualPatchForAliasEdit(aliasKey, newAliasKey, description, tags) {
  const normalizedOld = normalize(aliasKey);
  const normalizedNew = normalize(newAliasKey);
  const renameNote = normalizedOld !== normalizedNew
    ? aliasesText(
        null,
        "patch_edit_rename_note",
        " Also remove old alias key \"{alias_key}\" from assets/studio/data/tag_aliases.json.",
        { alias_key: normalizedOld }
      )
    : "";

  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_edit_message",
      "Patch mode: alias fragment prepared for \"{alias_key}\". Paste inside aliases object.{rename_note}",
      {
        alias_key: normalizedOld,
        rename_note: renameNote
      }
    ),
    snippet: JSON.stringify({
      [normalizedNew]: {
        description: String(description || "").trim(),
        tags: Array.isArray(tags) ? tags.slice() : []
      }
    }, null, 2)
  };
}

export function buildManualPatchForDemote(tagId, aliasTargets) {
  const parts = String(tagId || "").split(":", 2);
  const aliasKey = parts.length === 2 ? parts[1] : "";
  return {
    kind: "warn",
    message: aliasesText(
      null,
      "patch_demote_message",
      "Patch mode: section snippets prepared for demoting \"{tag_id}\".",
      { tag_id: tagId }
    ),
    snippet: JSON.stringify({
      tag_registry: {
        remove_tag_ids: [tagId]
      },
      tag_aliases: {
        set_aliases: {
          [aliasKey]: {
            description: "",
            tags: aliasTargets.slice()
          }
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
    }, null, 2)
  };
}

export async function readImportAliasesFromFile(file) {
  const rawText = await file.text();
  let payload = null;
  try {
    payload = JSON.parse(rawText);
  } catch (error) {
    throw new Error(aliasesText(null, "import_invalid_json", "Import file is not valid JSON."));
  }

  if (!payload || typeof payload !== "object") {
    throw new Error(aliasesText(null, "import_invalid_object", "Import file must be a JSON object."));
  }

  const rows = normalizeImportAliasRows(payload.aliases, aliasText);
  if (!rows.length) {
    throw new Error(aliasesText(null, "import_missing_aliases_object", "Import file must include aliases object with at least one alias."));
  }

  const aliasesObj = {};
  for (const row of rows) {
    aliasesObj[row.alias] = row.value;
  }
  return {
    tag_aliases_version: String(payload.tag_aliases_version || "tag_aliases_v1"),
    updated_at_utc: normalizeTimestamp(payload.updated_at_utc) || "",
    aliases: aliasesObj
  };
}

export function buildAliasesImportModeText(state, mode) {
  const label = mode === "post"
    ? aliasesText(state.config, "import_mode_local_server", "Local server")
    : aliasesText(state.config, "import_mode_patch", "Patch");
  return aliasesText(state.config, "import_mode_template", "Import mode: {mode}", { mode: label });
}

export function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function aliasText(key, fallback, tokens) {
  return aliasesText(null, key, fallback, tokens);
}
