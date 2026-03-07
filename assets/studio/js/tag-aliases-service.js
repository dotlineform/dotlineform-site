import {
  getStudioText
} from "./studio-config.js";
import {
  postJson,
  STUDIO_WRITE_ENDPOINTS
} from "./studio-transport.js";
import {
  buildImportSummary,
  buildManualPatchForAliasCreate,
  buildManualPatchForAliasDelete,
  buildManualPatchForAliasEdit,
  buildManualPatchForAliasPromote,
  buildManualPatchForDemote,
  buildManualPatchForNewAliases,
  utcTimestamp
} from "./tag-aliases-save.js";

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
}

export async function submitAliasesImport(options) {
  const { saveMode, importMode, importAliases, filename, config, state } = options || {};
  if (saveMode === "post") {
    try {
      const response = await postJson(STUDIO_WRITE_ENDPOINTS.importTagAliases, {
        mode: importMode,
        import_aliases: importAliases,
        import_filename: filename || "",
        client_time_utc: utcTimestamp()
      });
      return {
        ok: true,
        mode: "post",
        response,
        summary: buildImportSummary(response)
      };
    } catch (error) {
      return {
        ok: false,
        mode: "patch",
        switchToPatch: true,
        message: aliasesText(
          config,
          "server_import_failed",
          "Server import failed; switched to patch mode. {message}",
          { message: String(error && error.message ? error.message : "").trim() }
        ).trim(),
        patchResult: buildManualPatchForNewAliases(state, importAliases)
      };
    }
  }

  return {
    ok: true,
    mode: "patch",
    patchResult: buildManualPatchForNewAliases(state, importAliases)
  };
}

export async function submitAliasDelete(options) {
  const { saveMode, aliasKey, config } = options || {};
  if (saveMode === "post") {
    try {
      const response = await postJson(STUDIO_WRITE_ENDPOINTS.deleteTagAlias, {
        alias: aliasKey,
        client_time_utc: utcTimestamp()
      });
      const summary = String(response.summary_text || "").trim() || aliasesText(
        config,
        "delete_success_summary",
        "deleted alias {alias_key}",
        { alias_key: aliasKey }
      );
      return {
        ok: true,
        mode: "post",
        response,
        summary
      };
    } catch (error) {
      return {
        ok: false,
        mode: "patch",
        switchToPatch: true,
        message: aliasesText(
          config,
          "server_delete_failed",
          "Server delete failed; switched to patch mode. {message}",
          { message: String(error && error.message ? error.message : "").trim() }
        ).trim(),
        patchResult: buildManualPatchForAliasDelete(aliasKey)
      };
    }
  }

  return {
    ok: true,
    mode: "patch",
    patchResult: buildManualPatchForAliasDelete(aliasKey)
  };
}

export async function submitAliasEdit(options) {
  const {
    saveMode,
    isCreate,
    originalAlias,
    validation,
    config
  } = options || {};

  if (isCreate) {
    if (saveMode === "post") {
      try {
        const response = await postJson(STUDIO_WRITE_ENDPOINTS.importTagAliases, {
          mode: "add",
          import_aliases: {
            aliases: {
              [validation.alias]: {
                description: validation.description,
                tags: validation.tags
              }
            }
          },
          import_filename: "",
          client_time_utc: utcTimestamp()
        });
        return {
          ok: true,
          mode: "post",
          response,
          summary: buildImportSummary(response)
        };
      } catch (error) {
        return {
          ok: false,
          mode: "patch",
          switchToPatch: true,
          message: aliasesText(
            config,
            "server_create_failed",
            "Server create failed; switched to patch mode. {message}",
            { message: String(error && error.message ? error.message : "").trim() }
          ).trim(),
          patchResult: buildManualPatchForAliasCreate(
            validation.alias,
            validation.description,
            validation.tags
          )
        };
      }
    }

    return {
      ok: true,
      mode: "patch",
      patchResult: buildManualPatchForAliasCreate(
        validation.alias,
        validation.description,
        validation.tags
      )
    };
  }

  if (saveMode === "post") {
    try {
      const response = await postJson(STUDIO_WRITE_ENDPOINTS.mutateTagAlias, {
        alias: originalAlias,
        new_alias: validation.alias,
        description: validation.description,
        tags: validation.tags,
        client_time_utc: utcTimestamp()
      });
      return {
        ok: true,
        mode: "post",
        response
      };
    } catch (error) {
      return {
        ok: false,
        mode: "patch",
        switchToPatch: true,
        message: aliasesText(
          config,
          "server_save_failed",
          "Server save failed; switched to patch mode. {message}",
          { message: String(error && error.message ? error.message : "").trim() }
        ).trim(),
        patchResult: buildManualPatchForAliasEdit(
          originalAlias,
          validation.alias,
          validation.description,
          validation.tags
        )
      };
    }
  }

  return {
    ok: true,
    mode: "patch",
    patchResult: buildManualPatchForAliasEdit(
      originalAlias,
      validation.alias,
      validation.description,
      validation.tags
    )
  };
}

export async function previewAliasPromote(options) {
  const { aliasKey, group, config } = options || {};
  try {
    const response = await postJson(STUDIO_WRITE_ENDPOINTS.promoteTagAliasPreview, {
      alias: aliasKey,
      group,
      client_time_utc: utcTimestamp()
    });
    return {
      ok: true,
      response,
      summary: String(response.summary_text || "").trim() || `alias ${aliasKey} -> ${group}:${aliasKey}`
    };
  } catch (error) {
    return {
      ok: false,
      message: String(error && error.message ? error.message : aliasesText(config, "promotion_preview_failed", "Promotion preview failed."))
    };
  }
}

export async function submitAliasPromote(options) {
  const { saveMode, state, aliasKey, group } = options || {};
  if (saveMode === "post") {
    try {
      const response = await postJson(STUDIO_WRITE_ENDPOINTS.promoteTagAlias, {
        alias: aliasKey,
        group,
        client_time_utc: utcTimestamp()
      });
      return {
        ok: true,
        mode: "post",
        response,
        summary: String(response.summary_text || aliasesText(state.config, "promoted_success", "Promoted."))
      };
    } catch (error) {
      return {
        ok: false,
        mode: "post",
        message: String(error && error.message ? error.message : aliasesText(state.config, "promotion_failed", "Promotion failed."))
      };
    }
  }

  return {
    ok: true,
    mode: "patch",
    patchResult: buildManualPatchForAliasPromote(state, aliasKey, group)
  };
}

export async function previewTagDemoteFromAliases(options) {
  const { canonicalTagId, aliasTargets, config } = options || {};
  try {
    const response = await postJson(STUDIO_WRITE_ENDPOINTS.demoteTagPreview, {
      tag_id: canonicalTagId,
      alias_targets: aliasTargets,
      client_time_utc: utcTimestamp()
    });
    return {
      ok: true,
      response,
      summary: String(response.summary_text || "").trim() || `demote ${canonicalTagId}`
    };
  } catch (error) {
    return {
      ok: false,
      message: String(error && error.message ? error.message : aliasesText(config, "demotion_preview_failed", "Demotion preview failed."))
    };
  }
}

export async function submitTagDemoteFromAliases(options) {
  const { saveMode, canonicalTagId, aliasTargets } = options || {};
  if (saveMode === "post") {
    try {
      const response = await postJson(STUDIO_WRITE_ENDPOINTS.demoteTag, {
        tag_id: canonicalTagId,
        alias_targets: aliasTargets,
        client_time_utc: utcTimestamp()
      });
      return {
        ok: true,
        mode: "post",
        response
      };
    } catch (error) {
      return {
        ok: false,
        mode: "post",
        message: String(error && error.message ? error.message : "")
      };
    }
  }

  return {
    ok: true,
    mode: "patch",
    patchResult: buildManualPatchForDemote(canonicalTagId, aliasTargets)
  };
}
