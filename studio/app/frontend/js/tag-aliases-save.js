import {
  getStudioText
} from "./studio-config.js";
import {
  normalize
} from "./tag-aliases-domain.js";

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
}

export function buildManualPatchForAliasPromote(state, aliasKey, group) {
  const newTagId = normalize(aliasKey);
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
      "Patch mode: remove this alias key from studio/data/canonical/tags/tag-aliases.json aliases object."
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
        " Also remove old alias key \"{alias_key}\" from studio/data/canonical/tags/tag-aliases.json.",
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
  const aliasKey = normalize(tagId);
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

export function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}
