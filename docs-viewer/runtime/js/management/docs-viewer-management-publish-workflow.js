import {
  applyManagedDocsDeployRepo,
  applyManagedDocsPublish,
  confirmManagedDocsPublish,
  previewManagedDocsDeployRepo
} from "./docs-viewer-management-client.js";
import {
  scopeDeployRepoCapability,
  scopePublishSupported
} from "./docs-viewer-management-capabilities.js";
import {
  escapeHtml,
  openDocsViewerConfirmModal,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";

var WORKFLOW_TEXT = {
  cancelButton: "Cancel",
  selectionTitle: "Publish",
  publishChecking: "Checking accepted-snapshot changes...",
  publishApplying: "Updating the accepted scope snapshot...",
  deployChecking: "Checking repository deployment changes...",
  deployApplying: "Updating the repository deployment..."
};

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function docsViewerPublishWorkflowAvailability(capabilities, scope) {
  var publishAvailable = scopePublishSupported(capabilities, scope);
  var deployRepo = scopeDeployRepoCapability(capabilities, scope);
  return {
    publish: {
      available: publishAvailable,
      reason: publishAvailable ? "" : "Publish is unavailable for this scope."
    },
    deploy_repo: deployRepo
  };
}

export function docsViewerPublishWorkflowLabel(selection) {
  var publish = selection && selection.publish === true;
  var deployRepo = selection && selection.deploy_repo === true;
  if (publish && deployRepo) return "Publish And Deploy";
  if (publish) return "Publish";
  if (deployRepo) return "Copy to local repo";
  return "Select an operation";
}

function operationChoiceMarkup(role, label, capability) {
  var available = capability && capability.available === true;
  var checked = available ? " checked" : "";
  var disabled = available ? "" : " disabled";
  return "" +
    '<label class="docsViewer__field docsViewer__field--checkbox docsViewer__publishOperationChoice">' +
      '<input class="docsViewer__checkboxInput" type="checkbox" data-role="' + escapeHtml(role) + '"' + checked + disabled + '>' +
      '<span class="docsViewer__fieldLabel">' + escapeHtml(label) + '</span>' +
    '</label>';
}

export function openDocsViewerPublishWorkflowSelection(options = {}) {
  var availability = options.availability || {};
  var publish = availability.publish || { available: false, reason: "Publish is unavailable." };
  var deployRepo = availability.deploy_repo || { available: false, reason: "Deploy Repo is unavailable." };
  if (publish.available !== true && deployRepo.available !== true) {
    return Promise.reject(new Error("No Publish or Deploy Repo operation is available."));
  }
  var initialSelection = {
    publish: publish.available === true,
    deploy_repo: deployRepo.available === true
  };
  var bodyHtml =
    operationChoiceMarkup("publish-operation", "Publish", publish) +
    operationChoiceMarkup("deploy-repo-operation", "Copy to local repo", deployRepo);

  return openDocsViewerManagementModal({
    root: options.root,
    title: WORKFLOW_TEXT.selectionTitle,
    size: "compact",
    bodyHtml: bodyHtml,
    focusSelector: "input:not([disabled])",
    actions: [
      {
        role: "modal-primary",
        label: docsViewerPublishWorkflowLabel(initialSelection)
      },
      { role: "modal-cancel", label: WORKFLOW_TEXT.cancelButton }
    ],
    onOpen: function (api) {
      var primary = api.host.querySelector('[data-role="modal-primary"]');
      var publishInput = api.host.querySelector('[data-role="publish-operation"]');
      var deployInput = api.host.querySelector('[data-role="deploy-repo-operation"]');
      function renderSelection() {
        var selection = {
          publish: Boolean(publishInput && publishInput.checked && !publishInput.disabled),
          deploy_repo: Boolean(deployInput && deployInput.checked && !deployInput.disabled)
        };
        if (primary) {
          primary.textContent = docsViewerPublishWorkflowLabel(selection);
          primary.disabled = !selection.publish && !selection.deploy_repo;
        }
      }
      [publishInput, deployInput].filter(Boolean).forEach(function (input) {
        input.addEventListener("change", renderSelection);
      });
      renderSelection();
    },
    onSubmit: function (api) {
      var publishInput = api.host.querySelector('[data-role="publish-operation"]');
      var deployInput = api.host.querySelector('[data-role="deploy-repo-operation"]');
      var selection = {
        publish: Boolean(publishInput && publishInput.checked && !publishInput.disabled),
        deploy_repo: Boolean(deployInput && deployInput.checked && !deployInput.disabled)
      };
      if (!selection.publish && !selection.deploy_repo) {
        api.setStatus("Select Publish, Copy to local repo, or both.");
        return false;
      }
      return { confirmed: true, selection: selection };
    }
  }).then(function (result) {
    return result && result.confirmed
      ? { confirmed: true, ...result.selection }
      : { confirmed: false, publish: false, deploy_repo: false };
  });
}

export function docsViewerPublishHasChanges(preview) {
  return Number(preview && preview.added_count || 0)
    + Number(preview && preview.changed_count || 0)
    + Number(preview && preview.removed_count || 0) > 0;
}

export function docsViewerDeployRepoConfirmBody(preview) {
  var repository = preview && preview.repository || {};
  var media = preview && preview.media || {};
  var catalogue = preview && preview.catalogue_document_urls || {};
  var lineage = preview && preview.publication_lineage || {};
  var lines = [
    "Deploy this accepted Analysis snapshot to its configured repository and public-media destinations?",
    "Documents: " + Number(preview && preview.document_count || 0),
    "Repository files added: " + Number(repository.added_count || 0),
    "Repository files changed: " + Number(repository.changed_count || 0),
    "Repository files removed: " + Number(repository.removed_count || 0),
    "Media copies: " + Number(media.copy_count || 0),
    "Media removals: " + Number(media.remove_count || 0),
    "Media errors: " + Number(media.error_count || 0),
    catalogue.status === "paused"
      ? cleanString(catalogue.reason)
      : "Catalogue paths changed: " + Number(catalogue.changed_count || 0),
    "Publication lineage: " + (lineage.changed === true ? "change" : "unchanged"),
    "Accepted Published revision: " + cleanString(preview && preview.published_revision),
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

function workflowResult(selection) {
  return {
    cancelled: false,
    selection: {
      publish: selection.publish === true,
      deploy_repo: selection.deploy_repo === true
    },
    publish: {
      status: selection.publish === true ? "pending" : "unselected",
      payload: null,
      error: ""
    },
    deploy_repo: {
      status: selection.deploy_repo === true ? "pending" : "unselected",
      payload: null,
      error: ""
    }
  };
}

function notifyPhase(options, phase, busy, message) {
  if (typeof options.onPhase === "function") {
    options.onPhase({ phase: phase, busy: busy, message: message || "" });
  }
}

function errorMessage(error, fallback) {
  return cleanString(error && error.message) || fallback;
}

function markDeployRepoNotRun(result) {
  if (result.deploy_repo.status === "pending") {
    result.deploy_repo.status = "not_run";
  }
}

function acceptedPublishRevision(preview, payload) {
  var expected = cleanString(preview && preview.target_published_revision);
  var manifest = payload && payload.publish_manifest;
  var actual = cleanString(manifest && manifest.published_revision);
  if (!expected || actual !== expected) {
    throw new Error("Publish did not return the exact accepted revision reviewed for deployment.");
  }
  return actual;
}

function defaultConfirmDeployRepo(root, preview) {
  return openDocsViewerConfirmModal({
    root: root,
    title: "Deploy accepted scope snapshot to repository",
    body: docsViewerDeployRepoConfirmBody(preview),
    size: "wide",
    primaryLabel: "Deploy Repo",
    cancelLabel: WORKFLOW_TEXT.cancelButton,
    primaryDisabled: Number(preview && preview.error_count || 0) > 0
  });
}

export async function runManagedDocsPublishWorkflow(options = {}) {
  var availability = options.availability || docsViewerPublishWorkflowAvailability(
    options.capabilities,
    options.scope
  );
  var operations = options.operations || {};
  var selection = options.selection || await (
    operations.select || openDocsViewerPublishWorkflowSelection
  )({
    root: options.root,
    availability: availability
  });
  if (!selection || selection.confirmed !== true) {
    return { ...workflowResult({}), cancelled: true };
  }
  if (
    (selection.publish === true && availability.publish.available !== true)
    || (selection.deploy_repo === true && availability.deploy_repo.available !== true)
    || (selection.publish !== true && selection.deploy_repo !== true)
  ) {
    throw new Error("Selected Publish workflow operations are unavailable.");
  }

  var result = workflowResult(selection);
  var clientOptions = options.clientOptions || {};
  var previewPublish = operations.previewPublish || confirmManagedDocsPublish;
  var applyPublish = operations.applyPublish || applyManagedDocsPublish;
  var previewDeployRepo = operations.previewDeployRepo || previewManagedDocsDeployRepo;
  var applyDeployRepo = operations.applyDeployRepo || applyManagedDocsDeployRepo;
  var confirmDeployRepo = operations.confirmDeployRepo || function (preview) {
    return defaultConfirmDeployRepo(options.root, preview);
  };
  var acceptedRevision = "";

  if (selection.publish === true) {
    var publishPreview;
    notifyPhase(options, "publish_preview", true, WORKFLOW_TEXT.publishChecking);
    try {
      publishPreview = await previewPublish(clientOptions);
      result.publish.payload = publishPreview;
      acceptedRevision = cleanString(publishPreview.target_published_revision);
      if (!docsViewerPublishHasChanges(publishPreview)) {
        result.publish.status = "unchanged";
      } else {
        notifyPhase(options, "publish_apply", true, WORKFLOW_TEXT.publishApplying);
        var publishPayload = await applyPublish(publishPreview, clientOptions);
        result.publish.payload = publishPayload;
        acceptedRevision = acceptedPublishRevision(publishPreview, publishPayload);
        result.publish.status = "applied";
      }
    } catch (error) {
      result.publish.status = result.publish.payload && result.publish.payload.applied === true
        ? "partial"
        : "failed";
      result.publish.error = errorMessage(error, "Publish failed.");
      markDeployRepoNotRun(result);
      return result;
    }
  }

  if (selection.deploy_repo === true) {
    notifyPhase(options, "deploy_repo_preview", true, WORKFLOW_TEXT.deployChecking);
    try {
      var deployPreview = await previewDeployRepo(clientOptions);
      result.deploy_repo.payload = deployPreview;
      if (
        acceptedRevision
        && cleanString(deployPreview.published_revision) !== acceptedRevision
      ) {
        throw new Error("Deploy Repo did not preview the exact accepted Publish revision.");
      }
      if (Number(deployPreview.error_count || 0) > 0) {
        throw new Error("Deploy Repo preview reported destination errors; fix them and preview again.");
      }
      if (!docsViewerDeployRepoHasChanges(deployPreview)) {
        result.deploy_repo.status = "unchanged";
      } else {
        notifyPhase(options, "deploy_repo_confirm", false, "");
        if (!await confirmDeployRepo(deployPreview)) {
          result.deploy_repo.status = "cancelled";
          result.cancelled = true;
          return result;
        }
        notifyPhase(options, "deploy_repo_apply", true, WORKFLOW_TEXT.deployApplying);
        var deployPayload = await applyDeployRepo(deployPreview, clientOptions);
        result.deploy_repo.payload = deployPayload;
        result.deploy_repo.status = deployPayload && deployPayload.complete === false
          ? "partial"
          : "applied";
        if (result.deploy_repo.status === "partial") {
          result.deploy_repo.error = cleanString(deployPayload.summary_text)
            || "Deploy Repo completed only partially.";
        }
      }
    } catch (error) {
      result.deploy_repo.status = "failed";
      result.deploy_repo.error = errorMessage(error, "Deploy Repo failed.");
      return result;
    }
  }

  notifyPhase(options, "complete", false, "");
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

export function docsViewerPublishWorkflowMessage(result) {
  return [
    operationMessage("Publish", result && result.publish),
    operationMessage("Deploy Repo", result && result.deploy_repo)
  ].filter(Boolean).join(" ");
}

export function docsViewerPublishWorkflowHasFailure(result) {
  return [result && result.publish, result && result.deploy_repo].some(function (outcome) {
    return outcome && (outcome.status === "failed" || outcome.status === "partial");
  });
}
