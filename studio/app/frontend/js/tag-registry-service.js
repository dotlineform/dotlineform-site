import {
  getStudioText
} from "./studio-config.js";
import {
  getStudioTagWriteEndpoint,
  postJson
} from "./studio-transport.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import {
  buildCreateSummary,
  buildDeletePreviewPayload,
  buildMutationSummary,
  utcTimestamp
} from "./tag-registry-save.js";

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
}

function registryActivityContext(actionId, controlId, controlSelector, recordIdField, recordId) {
  return buildStudioActivityContext({
    pageId: "tag-registry",
    actionId,
    route: "/studio/tag-registry/",
    controlId,
    controlSelector,
    recordIdField,
    recordId
  });
}

export async function previewDeleteImpact(options) {
  const { saveMode, tagId, config } = options || {};
  if (saveMode !== "post") {
    return {
      ok: false,
      localRequired: true,
      message: registryText(config, "delete_impact_unavailable_local", "Delete impact: unavailable (local server required).")
    };
  }

  const payload = buildDeletePreviewPayload(tagId);
  if (!payload) {
    return {
      ok: false,
      message: registryText(config, "delete_impact_unavailable", "Delete impact: unavailable.")
    };
  }

  try {
    const response = await postJson(getStudioTagWriteEndpoint("mutateTagPreview", config), payload);
    const summary = buildMutationSummary(response);
    return {
      ok: true,
      response,
      summary,
      message: registryText(config, "delete_impact_template", "Delete impact: {summary}", { summary })
    };
  } catch (error) {
    const message = String(error && error.message ? error.message : "preview failed");
    return {
      ok: false,
      message: registryText(config, "delete_impact_error_template", "Delete impact: {message}", { message })
    };
  }
}

export async function submitTagEdit(options) {
  const { saveMode, tag, description, config } = options || {};
  if (saveMode !== "post") {
    return {
      ok: false,
      code: "local_required",
      message: registryText(config, "local_edit_required", "Local server is required for edit.")
    };
  }
  if (!tag) {
    return {
      ok: false,
      code: "missing_tag",
      message: registryText(config, "selected_tag_missing", "Selected tag is no longer available.")
    };
  }
  if (description === String(tag.description || "").trim()) {
    return {
      ok: false,
      code: "no_changes",
      message: registryText(config, "edit_no_changes", "No changes to save.")
    };
  }

  try {
    const response = await postJson(getStudioTagWriteEndpoint("mutateTag", config), {
      action: "edit",
      tag_id: tag.tagId,
      description,
      allow_canonical_rename: false,
      client_time_utc: utcTimestamp(),
      activity_context: registryActivityContext("edit-tag", "save-edit", "[data-role=\"save-edit\"]", "tag_id", tag.tagId)
    });
    return {
      ok: true,
      response,
      summary: buildMutationSummary(response),
      message: registryText(config, "edit_saved", "Saved.")
    };
  } catch (error) {
    return {
      ok: false,
      code: "request_failed",
      message: String(error && error.message ? error.message : registryText(config, "edit_save_failed", "Save failed."))
    };
  }
}

export async function submitCreateTag(options) {
  const { saveMode, newTagRow, config, state } = options || {};
  if (saveMode === "post") {
    try {
      const response = await postJson(getStudioTagWriteEndpoint("createTag", config), {
        group: newTagRow && newTagRow.group,
        slug: newTagRow && newTagRow.label,
        description: newTagRow && newTagRow.description,
        client_time_utc: utcTimestamp(),
        activity_context: registryActivityContext("create-tag", "create-tag", "[data-role=\"create-tag\"]", "tag_id", newTagRow && newTagRow.tag_id)
      });
      return {
        ok: true,
        mode: "post",
        response,
        summary: buildCreateSummary(response)
      };
    } catch (error) {
      if (Number.isFinite(Number(error && error.status))) {
        return {
          ok: false,
          mode: "post",
          switchToPatch: false,
          message: String(error && error.message ? error.message : registryText(config, "create_failed", "Create failed."))
        };
      }
      return {
        ok: false,
        mode: "patch",
        switchToPatch: true,
        message: registryText(
          config,
          "server_create_failed",
          "Server create failed; switched to patch mode. {message}",
          { message: String(error && error.message ? error.message : "").trim() }
        ).trim()
      };
    }
  }

  return {
    ok: true,
    mode: "patch",
    state
  };
}

export async function submitDeleteTag(options) {
  const { saveMode, tag, config } = options || {};
  if (saveMode !== "post") {
    return {
      ok: false,
      code: "local_required",
      message: registryText(config, "local_delete_required", "Local server is required for delete.")
    };
  }
  if (!tag) {
    return {
      ok: false,
      code: "missing_tag",
      message: registryText(config, "selected_tag_missing", "Selected tag is no longer available.")
    };
  }

  try {
    const response = await postJson(getStudioTagWriteEndpoint("mutateTag", config), {
      action: "delete",
      tag_id: tag.tagId,
      client_time_utc: utcTimestamp(),
      activity_context: registryActivityContext("delete-tag", "confirm-delete-tag", "[data-role=\"confirm-delete-tag\"]", "tag_id", tag.tagId)
    });
    return {
      ok: true,
      response,
      summary: buildMutationSummary(response)
    };
  } catch (error) {
    return {
      ok: false,
      code: "request_failed",
      message: String(error && error.message ? error.message : registryText(config, "delete_failed", "Delete failed."))
    };
  }
}

export async function previewTagDemote(options) {
  const { tagId, aliasTargets, config } = options || {};
  try {
    const response = await postJson(getStudioTagWriteEndpoint("demoteTagPreview", config), {
      tag_id: tagId,
      alias_targets: aliasTargets,
      client_time_utc: utcTimestamp()
    });
    return {
      ok: true,
      response,
      summary: String(response.summary_text || "").trim() || `demote ${tagId}`
    };
  } catch (error) {
    return {
      ok: false,
      message: String(error && error.message ? error.message : registryText(config, "demote_preview_failed", "Demotion preview failed."))
    };
  }
}

export async function submitTagDemote(options) {
  const { saveMode, tagId, aliasTargets, config } = options || {};
  if (saveMode === "post") {
    try {
      const response = await postJson(getStudioTagWriteEndpoint("demoteTag", config), {
        tag_id: tagId,
        alias_targets: aliasTargets,
        client_time_utc: utcTimestamp(),
        activity_context: registryActivityContext("demote-registry-tag", "confirm-demote", "[data-role=\"confirm-demote\"]", "tag_id", tagId)
      });
      return {
        ok: true,
        mode: "post",
        response,
        summary: String(response.summary_text || registryText(config, "demoted_success", "Demoted."))
      };
    } catch (error) {
      return {
        ok: false,
        mode: "post",
        message: String(error && error.message ? error.message : registryText(config, "demotion_failed", "Demotion failed."))
      };
    }
  }

  return {
    ok: true,
    mode: "patch"
  };
}
