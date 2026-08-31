import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const workflow = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-export-scopes-workflow.js"
)));
const client = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-management-client.js"
)));
const actions = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-action-definitions.js"
)));
const eventRouterModule = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/management/docs-viewer-management-event-router.js"
)));

assert.deepEqual(
  actions.getDocsViewerActionDefinition(actions.DOCS_VIEWER_ACTION_IDS.EXPORT_SCOPES),
  { id: "export-scopes", target: "scope" }
);
let routedExportScopes = false;
const eventRouter = eventRouterModule.createDocsViewerManagementEventRouter({
  commands: {
    exportScopes() {
      routedExportScopes = true;
    }
  }
});
assert.equal(eventRouter.handleAppManagementControl({
  actionId: "export-scopes",
  eventType: "click"
}), true);
assert.equal(routedExportScopes, true);

const capabilities = {
  static_html_export: { preview: true, apply: true, error: "" },
  scopes: {
    analysis: {
      static_html_export: { preview: true, apply: true, error: "" }
    },
    notes: {
      static_html_export: {
        preview: false,
        apply: false,
        error: "The Notes generated snapshot is unavailable."
      }
    },
    studio: {
      static_html_export: { preview: true, apply: true, error: "" }
    }
  }
};
const scopeConfigs = [
  { scopeId: "analysis", meta: "Public", emoji: "🌐" },
  { scopeId: "notes", meta: "External local", emoji: "💻" },
  { scopeId: "studio", meta: "Local", emoji: "䷑" }
];

assert.deepEqual(
  workflow.docsViewerExportScopeRecords({
    capabilities,
    currentScope: "studio",
    scopeConfigs
  }),
  [
    {
      scope: "analysis",
      label: "analysis",
      emoji: "🌐",
      available: true,
      reason: "",
      selected: false
    },
    {
      scope: "notes",
      label: "notes",
      emoji: "💻",
      available: false,
      reason: "The Notes generated snapshot is unavailable.",
      selected: false
    },
    {
      scope: "studio",
      label: "studio",
      emoji: "䷑",
      available: true,
      reason: "",
      selected: true
    }
  ]
);
assert.equal(
  workflow.docsViewerExportScopesAvailable({ capabilities, scopeConfigs }),
  true
);
assert.deepEqual(
  workflow.docsViewerExportScopeDocIds({
    docs: [{ doc_id: "parent" }, { doc_id: "child" }]
  }, "studio"),
  ["parent", "child"]
);
assert.throws(
  () => workflow.docsViewerExportScopeDocIds({ docs: [] }, "studio"),
  /No generated documents/
);

let indexRequest = null;
await client.readManagedDocsIndex("Analysis", {
  baseUrl: "http://127.0.0.1:8789",
  async fetch(url, options) {
    indexRequest = { url, options };
    return {
      ok: true,
      status: 200,
      async json() {
        return { schema: "docs_index_tree_v1", docs: [] };
      }
    };
  }
});
assert.equal(
  indexRequest.url,
  "http://127.0.0.1:8789/docs/index-tree?scope=analysis"
);
assert.equal(indexRequest.options.method, "GET");

function snapshotPreview(scope, docIds, targetState) {
  const replacing = targetState === "recognized" || targetState === "unrecognized";
  return {
    ok: true,
    schema_version: "docs_static_html_snapshot_preview_v2",
    operation: "preview",
    dry_run: true,
    scope,
    doc_ids: docIds,
    document_count: docIds.length,
    media_count: 0,
    media_bytes: 0,
    external_dependency_count: 0,
    selection_kind: "complete",
    target_state: targetState,
    destination_label: `/docs-export/${scope} - 2026-08-31/`,
    plan_revision: "a".repeat(64),
    target_revision: "b".repeat(64),
    export_date: "2026-08-31",
    replacement_required: replacing,
    replace_allowed: true,
    ...(targetState === "recognized" ? { existing_snapshot: { scope } } : {})
  };
}

const indexes = {
  analysis: { docs: [{ doc_id: "analysis-a" }] },
  studio: { docs: [{ doc_id: "studio-a" }, { doc_id: "studio-b" }] }
};
const calls = [];
let confirmation = null;
const result = await workflow.runManagedDocsExportScopesWorkflow({
  capabilities,
  clientOptions: { baseUrl: "http://127.0.0.1:8789", scope: "studio" },
  currentScope: "studio",
  scopeConfigs,
  selection: { confirmed: true, scopes: ["analysis", "studio"] },
  operations: {
    async readIndex(scope) {
      calls.push(`read:${scope}`);
      return indexes[scope];
    },
    async previewSnapshot(scope, docIds) {
      calls.push(`preview:${scope}:${docIds.join(",")}`);
      return snapshotPreview(scope, docIds, scope === "studio" ? "recognized" : "absent");
    },
    async confirmBatch(options) {
      calls.push("confirm");
      confirmation = options;
      return true;
    },
    async applySnapshot(scope, preview) {
      calls.push(`apply:${scope}:${preview.destination_label}`);
      return { ok: true, scope };
    }
  }
});

assert.deepEqual(calls, [
  "read:analysis",
  "preview:analysis:analysis-a",
  "read:studio",
  "preview:studio:studio-a,studio-b",
  "confirm",
  "apply:analysis:/docs-export/analysis - 2026-08-31/",
  "apply:studio:/docs-export/studio - 2026-08-31/"
]);
assert.equal(confirmation.primaryTone, "danger");
assert.match(confirmation.body[0], /Create snapshot/);
assert.match(confirmation.body[1], /Replace existing snapshot/);
assert.deepEqual(result.scopes, ["analysis", "studio"]);
assert.equal(result.documentCount, 3);
assert.equal(
  workflow.docsViewerExportScopesWorkflowMessage(result),
  "Exported 2 scopes (3 documents) to docs-export."
);

let cancelledOperationRan = false;
const cancelled = await workflow.runManagedDocsExportScopesWorkflow({
  capabilities,
  currentScope: "studio",
  scopeConfigs,
  selection: { confirmed: false, scopes: [] },
  operations: {
    async readIndex() {
      cancelledOperationRan = true;
      return {};
    }
  }
});
assert.equal(cancelled.cancelled, true);
assert.equal(cancelledOperationRan, false);

await assert.rejects(
  workflow.runManagedDocsExportScopesWorkflow({
    capabilities,
    currentScope: "studio",
    scopeConfigs,
    selection: { confirmed: true, scopes: ["notes"] },
    operations: {
      async readIndex() {
        return {};
      }
    }
  }),
  /Notes generated snapshot is unavailable/
);

await assert.rejects(
  workflow.runManagedDocsExportScopesWorkflow({
    capabilities,
    currentScope: "studio",
    scopeConfigs,
    selection: { confirmed: true, scopes: ["studio"] },
    operations: {
      async readIndex() {
        return indexes.studio;
      },
      async previewSnapshot(scope, docIds) {
        return {
          ...snapshotPreview(scope, docIds, "absent"),
          selection_kind: "partial"
        };
      }
    }
  }),
  /generated Index changed before the full-scope preview/
);

console.log("Docs Viewer Export Scopes workflow JavaScript contract OK");
