import { applyManagedDocsDeployRepo, previewManagedDocsDeployRepo } from "./docs-viewer-management-client.js";
import { stageDeployRepoCapability } from "./docs-viewer-management-capabilities.js";
import { openDocsViewerConfirmModal } from "./docs-viewer-management-modal-shell.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function docsViewerDeployRepoConfirmBody(preview) {
  var repository = preview && preview.repository || {};
  var media = preview && preview.media || {};
  var lineage = preview && preview.publication_lineage || {};
  var lines = [
    "Deploy this Preview snapshot to its configured repository and public-media destinations?",
    "Documents: " + Number(preview && preview.document_count || 0),
    "Repository files added: " + Number(repository.added_count || 0),
    "Repository files changed: " + Number(repository.changed_count || 0),
    "Repository files removed: " + Number(repository.removed_count || 0),
    "Media copies: " + Number(media.copy_count || 0),
    "Media removals: " + Number(media.remove_count || 0),
    "Media errors: " + Number(media.error_count || 0),
    "Publication lineage: " + (lineage.changed === true ? "change" : "unchanged"),
    "Preview revision: " + cleanString(preview && preview.preview_revision),
    "Deploy Repo plan: " + cleanString(preview && preview.plan_revision)
  ];
  var repositoryChanges = Array.isArray(repository.changes) ? repository.changes : [];
  if (repositoryChanges.length) {
    lines.push("Repository paths:");
    repositoryChanges.forEach(function (change) {
      lines.push("- " + cleanString(change && change.action) + " " + cleanString(change && change.path));
    });
  }
  var mediaTypes = Array.isArray(media.types) ? media.types : [];
  var mediaChanges = mediaTypes.flatMap(function (type) {
    return (Array.isArray(type && type.items) ? type.items : []).filter(function (item) {
      return item && (item.action === "copy" || item.action === "remove");
    });
  });
  if (mediaChanges.length) {
    lines.push("Media transfers:");
    mediaChanges.forEach(function (change) {
      lines.push(
        "- " + cleanString(change.action) + " " +
        cleanString(change.provider) + ":" + cleanString(change.identity)
      );
    });
  }
  return lines.join("\n");
}

export function docsViewerDeployRepoHasChanges(preview) {
  return Number(preview && preview.change_count || 0) > 0;
}

/** Review and deploy one exact prepared Preview revision. */
export async function runManagedDocsDeployRepoWorkflow(options = {}) {
  var clientOptions = options.clientOptions || {};
  if (!stageDeployRepoCapability(options.capabilities, clientOptions.stage).available) {
    throw new Error("Deploy Repo is unavailable for this stage.");
  }
  var result = { cancelled: false, deploy_repo: { status: "pending", payload: null, error: "" } };
  function phase(name, busy, message) {
    if (typeof options.onPhase === "function") options.onPhase({ phase: name, busy: busy, message: message });
  }
  try {
    phase("deploy_repo_preview", true, "Checking repository deployment changes...");
    var preview = await previewManagedDocsDeployRepo(clientOptions);
    result.deploy_repo.payload = preview;
    if (Number(preview.error_count || 0) > 0) throw new Error("Deploy Repo preview reported destination errors; fix them and preview again.");
    if (!docsViewerDeployRepoHasChanges(preview)) {
      result.deploy_repo.status = "unchanged";
      return result;
    }
    phase("deploy_repo_confirm", false, "");
    var confirmed = await openDocsViewerConfirmModal({
      root: options.root, title: "Deploy Repo", body: docsViewerDeployRepoConfirmBody(preview),
      size: "wide", primaryLabel: "Deploy Repo", cancelLabel: "Cancel"
    });
    if (!confirmed) {
      result.cancelled = true;
      result.deploy_repo.status = "cancelled";
      return result;
    }
    phase("deploy_repo_apply", true, "Updating the repository deployment...");
    var payload = await applyManagedDocsDeployRepo(preview, clientOptions);
    result.deploy_repo.payload = payload;
    result.deploy_repo.status = payload.complete === false ? "partial" : "applied";
    if (payload.complete === false) result.deploy_repo.error = cleanString(payload.summary_text) || "Deploy Repo completed only partially.";
  } catch (error) {
    result.deploy_repo.status = "failed";
    result.deploy_repo.error = cleanString(error && error.message) || "Deploy Repo failed.";
  } finally {
    phase("complete", false, "");
  }
  return result;
}

function operationMessage(label, outcome) {
  var status = cleanString(outcome && outcome.status);
  if (status === "unselected" || status === "pending" || status === "cancelled") return "";
  if (status === "applied") return label + ": complete.";
  if (status === "unchanged") return label + ": already current.";
  if (status === "not_run") return label + ": not run.";
  if (status === "partial") {
    return label + ": incomplete. " + cleanString(outcome.error);
  }
  return label + ": failed. " + cleanString(outcome && outcome.error);
}

export function docsViewerDeployRepoWorkflowMessage(result) {
  return [
    operationMessage("Deploy Repo", result && result.deploy_repo)
  ].filter(Boolean).join(" ");
}

export function docsViewerDeployRepoWorkflowHasFailure(result) {
  return [result && result.deploy_repo].some(function (outcome) {
    return outcome && (outcome.status === "failed" || outcome.status === "partial");
  });
}
