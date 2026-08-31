import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const workflow = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-management-publish-workflow.js"
)));
const client = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-management-client.js"
)));

const capabilities = {
  publishing: { confirm: true, apply: true },
  deploy_repo: { preview: true, apply: true },
  scopes: {
    analysis: {
      available: true,
      publishing: { confirm: true, apply: true },
      deploy_repo: { available: true, preview: true, apply: true, reason: "" }
    },
    studio: {
      available: true,
      publishing: { confirm: true, apply: true },
      deploy_repo: {
        available: false,
        preview: false,
        apply: false,
        reason: "Deploy Repo is available only for Analysis."
      }
    }
  }
};

assert.deepEqual(
  workflow.docsViewerPublishWorkflowAvailability(capabilities, "analysis"),
  {
    publish: { available: true, reason: "" },
    deploy_repo: { available: true, reason: "" }
  }
);
assert.equal(
  workflow.docsViewerPublishWorkflowAvailability(capabilities, "studio").deploy_repo.available,
  false
);
assert.equal(
  workflow.docsViewerPublishWorkflowLabel({ publish: true, deploy_repo: true }),
  "Publish And Deploy"
);
assert.equal(
  workflow.docsViewerPublishWorkflowLabel({ publish: true, deploy_repo: false }),
  "Publish"
);
assert.equal(
  workflow.docsViewerPublishWorkflowLabel({ publish: false, deploy_repo: true }),
  "Copy to local repo"
);

const revision = "sha256:" + "a".repeat(64);
const clientRequests = [];
const clientOptions = {
  baseUrl: "http://127.0.0.1:8789",
  scope: "analysis",
  async fetch(url, options) {
    clientRequests.push({ url, options });
    return {
      ok: true,
      status: 200,
      async json() {
        return { ok: true };
      }
    };
  }
};
await client.previewManagedDocsDeployRepo(clientOptions);
await client.applyManagedDocsDeployRepo(
  {
    published_revision: revision,
    deployment_timestamp: "2026-08-31T00:00:00Z",
    plan_revision: "sha256:" + "c".repeat(64)
  },
  clientOptions
);
assert.deepEqual(
  clientRequests.map((request) => request.url),
  [
    "http://127.0.0.1:8789/docs/deploy-repo/preview",
    "http://127.0.0.1:8789/docs/deploy-repo/apply"
  ]
);
assert.deepEqual(JSON.parse(clientRequests[1].options.body), {
  scope: "analysis",
  confirm: true,
  published_revision: revision,
  deployment_timestamp: "2026-08-31T00:00:00Z",
  plan_revision: "sha256:" + "c".repeat(64)
});

const calls = [];
const partial = await workflow.runManagedDocsPublishWorkflow({
  scope: "analysis",
  capabilities,
  selection: { confirmed: true, publish: true, deploy_repo: true },
  operations: {
    async previewPublish() {
      calls.push("publish-preview");
      return {
        added_count: 1,
        changed_count: 0,
        removed_count: 0,
        target_published_revision: revision
      };
    },
    async confirmPublish() {
      calls.push("publish-confirm");
      return true;
    },
    async applyPublish() {
      calls.push("publish-apply");
      return {
        applied: true,
        publish_manifest: { published_revision: revision }
      };
    },
    async previewDeployRepo() {
      calls.push("deploy-preview");
      return {
        published_revision: revision,
        change_count: 1,
        error_count: 0
      };
    },
    async confirmDeployRepo() {
      calls.push("deploy-confirm");
      return true;
    },
    async applyDeployRepo(preview) {
      calls.push("deploy-apply:" + preview.published_revision);
      return {
        applied: true,
        complete: false,
        summary_text: "Repository current; media destination stale."
      };
    }
  }
});

assert.deepEqual(calls, [
  "publish-preview",
  "publish-confirm",
  "publish-apply",
  "deploy-preview",
  "deploy-confirm",
  "deploy-apply:" + revision
]);
assert.equal(partial.publish.status, "applied");
assert.equal(partial.deploy_repo.status, "partial");
assert.equal(workflow.docsViewerPublishWorkflowHasFailure(partial), true);
assert.match(
  workflow.docsViewerPublishWorkflowMessage(partial),
  /^Publish: complete\. Deploy Repo: incomplete\./
);

const retryCalls = [];
const retry = await workflow.runManagedDocsPublishWorkflow({
  scope: "analysis",
  capabilities,
  selection: { confirmed: true, publish: false, deploy_repo: true },
  operations: {
    async previewDeployRepo() {
      retryCalls.push("deploy-preview");
      return {
        published_revision: revision,
        change_count: 1,
        error_count: 0
      };
    },
    async confirmDeployRepo() {
      retryCalls.push("deploy-confirm");
      return true;
    },
    async applyDeployRepo() {
      retryCalls.push("deploy-apply");
      return { applied: true, complete: true };
    }
  }
});
assert.deepEqual(retryCalls, ["deploy-preview", "deploy-confirm", "deploy-apply"]);
assert.equal(retry.publish.status, "unselected");
assert.equal(retry.deploy_repo.status, "applied");

let deployAttempted = false;
const publishFailure = await workflow.runManagedDocsPublishWorkflow({
  scope: "analysis",
  capabilities,
  selection: { confirmed: true, publish: true, deploy_repo: true },
  operations: {
    async previewPublish() {
      return {
        added_count: 1,
        changed_count: 0,
        removed_count: 0,
        target_published_revision: revision
      };
    },
    async confirmPublish() {
      return true;
    },
    async applyPublish() {
      throw new Error("simulated Publish failure");
    },
    async previewDeployRepo() {
      deployAttempted = true;
      return {};
    }
  }
});
assert.equal(publishFailure.publish.status, "failed");
assert.equal(publishFailure.deploy_repo.status, "not_run");
assert.equal(deployAttempted, false);

const wrongRevision = await workflow.runManagedDocsPublishWorkflow({
  scope: "analysis",
  capabilities,
  selection: { confirmed: true, publish: true, deploy_repo: true },
  operations: {
    async previewPublish() {
      return {
        added_count: 0,
        changed_count: 0,
        removed_count: 0,
        target_published_revision: revision
      };
    },
    async previewDeployRepo() {
      return {
        published_revision: "sha256:" + "b".repeat(64),
        change_count: 1,
        error_count: 0
      };
    }
  }
});
assert.equal(wrongRevision.publish.status, "unchanged");
assert.equal(wrongRevision.deploy_repo.status, "failed");
assert.match(wrongRevision.deploy_repo.error, /exact accepted Publish revision/);

console.log("Docs Viewer Publish workflow JavaScript contract OK");
