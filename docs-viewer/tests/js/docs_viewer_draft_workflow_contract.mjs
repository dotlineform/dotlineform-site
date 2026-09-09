import assert from "node:assert/strict";
import { toggleManagedDocDraft } from "../../runtime/js/management/docs-viewer-management-draft-workflow.js";
import { normalizeDocsIndexTreePayload } from "../../runtime/js/shared/docs-viewer-tree-payload-adapter.js";

for (const subScope of [null, "works"]) {
  const target = { scope: "analysis", stage: "working", doc_id: "document", ...(subScope ? { sub_scope: subScope } : {}) };
  const revision = "sha256:" + "a".repeat(64);
  const events = [];
  let finishRefresh;
  const refresh = new Promise(resolve => { finishRefresh = resolve; });
  const fetch = async (url, options) => {
    if (options.method === "GET") {
      assert.equal(new URL(url).searchParams.get("stage"), "working");
      return { ok: true, json: async () => ({ ok: true, ...target, source_revision: revision, record: { draft: false } }) };
    }
    assert.equal(new URL(url).pathname, "/docs/set-draft");
    assert.deepEqual(JSON.parse(options.body), { ...target, draft: true, source_revision: revision });
    events.push("write");
    return { ok: true, json: async () => ({ ok: true, target, record: { draft: true } }) };
  };
  const run = toggleManagedDocDraft(target, {
    clientOptions: { baseUrl: "http://fixture.test", fetch },
    reloadTarget: async selected => {
      assert.deepEqual(selected, target);
      events.push("refresh");
      await refresh;
    }
  }).then(() => events.push("complete"));
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(events, ["write", "refresh"]);
  finishRefresh();
  await run;
  assert.deepEqual(events, ["write", "refresh", "complete"]);
}
await assert.rejects(toggleManagedDocDraft({ scope: "analysis", stage: "pre-publish", doc_id: "document" }, {}), /only in Analysis Working/);
const tree = normalizeDocsIndexTreePayload({ schema: "docs_index_tree_v1", docs: [
  { doc_id: "draft", title: "Draft", content_url: "/draft", draft: true },
  { doc_id: "ready", title: "Ready", content_url: "/ready", draft: false }
] });
assert.deepEqual(tree.docs.map(doc => doc.draft), [true, false]);
console.log("Draft contract passed: exact targets, awaited refresh and boolean tree state.");
