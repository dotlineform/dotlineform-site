import {
  applyCatalogueMediaPublish,
  previewCatalogueMediaPublish
} from "./catalogue-editor-service-client.js";
import { computeRecordHash } from "./catalogue-editor-records.js";
import { formatCatalogueMediaPublishPreview } from "./catalogue-editor-modal-formatters.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import {
  extractCatalogueActionPreview,
  getCataloguePreviewBlocker
} from "./catalogue-editor-action-workflow.js";
import { setLoadedWorkRecord } from "./catalogue-work-route-state.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import { normalizeText } from "./catalogue-work-fields.js";
import { applyWorkRecordMutation } from "./catalogue-work-action-records.js";
import { catalogueReadinessItem } from "./catalogue-editor-readiness.js";
import {
  refreshBuildPreview,
  saveCurrentWork
} from "./catalogue-work-actions.js";

function text(state, context, key, fallback, tokens = null) {
  return context.text(key, fallback, tokens);
}

function setTextWithState(context, node, value, tone = "") {
  context.setTextWithState(node, value, tone);
}

function buildMediaPublishActivityContext(workId) {
  return buildStudioActivityContext({
    pageId: "catalogue-work",
    actionId: "publish-work-media",
    route: "/studio/catalogue-work/",
    controlId: "catalogueWorkSave",
    controlSelector: "#catalogueWorkSave",
    recordIdField: "work_id",
    recordId: workId
  });
}

export function workMediaPublishEnabled(state, context) {
  const mediaItem = catalogueReadinessItem(state.buildPreview, "work_media");
  const version = Math.floor(Number(state.currentRecord && state.currentRecord.media_version));
  return Boolean(
    state.mode === "single" &&
    state.currentRecord &&
    state.currentWorkId &&
    state.serverAvailable &&
    normalizeText(state.currentRecord.status).toLowerCase() === "published" &&
    Number.isFinite(version) &&
    version > 0 &&
    mediaItem &&
    normalizeText(mediaItem.status) === "ready" &&
    !state.isSaving &&
    !state.isBuilding &&
    !state.isDeleting &&
    !context.draftHasChanges()
  );
}

export function workSaveActionRequired(state, sourceDirty = false) {
  return Boolean(
    sourceDirty ||
    (state && state.mode === "single" && state.mediaPublishPending)
  );
}

export async function publishWorkMedia(state, context) {
  if (!workMediaPublishEnabled(state, context)) return false;
  const currentVersion = Math.floor(Number(state.currentRecord.media_version));

  const request = {
    work_id: state.currentWorkId,
    expected_media_version: currentVersion
  };
  state.isBuilding = true;
  context.updateEditorState();
  setTextWithState(context, state.statusNode, text(state, context, "media_publish_preview_running", "Checking R2 media…"));
  setTextWithState(context, state.resultNode, "");
  try {
    const previewResponse = await previewCatalogueMediaPublish(request);
    const preview = extractCatalogueActionPreview(previewResponse);
    const blocker = getCataloguePreviewBlocker(preview, {
      fallback: text(state, context, "media_publish_status_blocked", "Media publishing is blocked.")
    });
    if (blocker) {
      setTextWithState(context, state.statusNode, blocker, "error");
      setTextWithState(context, state.resultNode, normalizeText(preview && preview.summary), "error");
      return false;
    }
    const previewFingerprint = normalizeText(preview && preview.preview_fingerprint);
    if (!previewFingerprint) throw new Error("media publish preview missing fingerprint");

    const summary = formatCatalogueMediaPublishPreview(preview, {
      text: (key, fallback, tokens) => text(state, context, key, fallback, tokens),
      currentVersion
    });
    state.isBuilding = false;
    context.updateEditorState();
    const confirmed = await confirmCatalogueActionModal(state, {
      title: preview.requires_force
        ? text(state, context, "media_publish_overwrite_confirm_title", "Confirm media replacement")
        : text(state, context, "media_publish_confirm_title", "Confirm media publish"),
      message: summary,
      primaryLabel: preview.requires_force
        ? text(state, context, "media_publish_overwrite_confirm_button", "Replace media")
        : text(state, context, "media_publish_confirm_button", "Publish media"),
      cancelLabel: text(state, context, "confirm_cancel_button", "Cancel"),
      defaultAction: "cancel",
      restoreFocus: state.saveButton
    });
    if (!confirmed) {
      setTextWithState(context, state.statusNode, text(state, context, "media_publish_status_cancelled", "Media publishing cancelled."));
      return false;
    }

    state.isBuilding = true;
    context.updateEditorState();
    setTextWithState(context, state.statusNode, text(state, context, "media_publish_status_running", "Publishing media to R2…"));
    const response = await applyCatalogueMediaPublish({
      ...request,
      preview_fingerprint: previewFingerprint,
      force: Boolean(preview.requires_force),
      confirm_overwrite: Boolean(preview.requires_force),
      activity_context: buildMediaPublishActivityContext(state.currentWorkId)
    });
    const record = response && response.record && typeof response.record === "object" ? response.record : null;
    if (!record) throw new Error("media publish response missing work record");

    const workId = state.currentWorkId;
    const recordHash = await computeRecordHash(record);
    applyWorkRecordMutation(state, { workId, record, recordHash });
    const lookup = await context.loadWorkLookupRecord(workId).catch(() => null);
    setLoadedWorkRecord(state, workId, record, context.workRouteStateOptions({
      recordHash,
      keepResult: true,
      lookup
    }));
    await refreshBuildPreview(state, context);

    const resultSummary = normalizeText(response && response.result && response.result.summary);
    const confirmedVersion = Math.floor(Number(response.media_version));
    setTextWithState(
      context,
      state.resultNode,
      resultSummary || text(state, context, "media_publish_result_complete", "R2 media publishing completed."),
      "success"
    );
    setTextWithState(
      context,
      state.statusNode,
      Number.isFinite(confirmedVersion)
        ? text(state, context, "media_publish_status_success_version", "Media published. Confirmed URL version: v={media_version}.", { media_version: String(confirmedVersion) })
        : text(state, context, "media_publish_status_success", "Media published."),
      "success"
    );
    return true;
  } catch (error) {
    const message = Number(error && error.status) === 409
      ? text(state, context, "media_publish_status_conflict", "The confirmed media version changed. Reload before publishing media.")
      : `${text(state, context, "media_publish_status_failed", "Media publishing failed.")} ${normalizeText(error && error.message)}`.trim();
    setTextWithState(context, state.statusNode, message, "error");
    return false;
  } finally {
    state.isBuilding = false;
    context.updateEditorState();
  }
}

export async function runWorkSaveThenMediaPublish(options) {
  await options.save();
  if (!options.mediaPublishEnabled()) return false;
  options.setMediaPublishPending(true);
  const completed = await options.publishMedia();
  if (completed) options.setMediaPublishPending(false);
  return true;
}

export async function saveWorkThenPublishMedia(state, context) {
  return runWorkSaveThenMediaPublish({
    save: () => saveCurrentWork(state, context),
    mediaPublishEnabled: () => workMediaPublishEnabled(state, context),
    publishMedia: () => publishWorkMedia(state, context),
    setMediaPublishPending: (pending) => {
      state.mediaPublishPending = Boolean(pending);
    }
  });
}
