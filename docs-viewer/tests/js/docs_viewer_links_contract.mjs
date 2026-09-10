import assert from "node:assert/strict";
import { docsViewerLinksPresentation } from "../../runtime/js/shared/docs-viewer-links-presentation.js";
import { createDocsViewerLinksDetailAdapter } from "../../runtime/js/shared/docs-viewer-links-detail.js";
import { createDocsViewerConfiguredScopeProvider } from "../../runtime/js/shared/docs-viewer-configured-scope-provider.js";
import { createDocsViewerGeneratedDataRuntime } from "../../runtime/js/shared/docs-viewer-generated-data-runtime.js";
import { withDocsViewerContentDetailDefinitions } from "../../runtime/js/shared/docs-viewer-content-detail-view.js";

const id = number => `d-20260910-120000-${String(number).padStart(6, "0")}`;
const target = { scope: "analysis", stage: "working", sub_scope: "", doc_id: id(1) };
function summary(number, title, subScope = "", subject = null) {
  return { target: { scope: "analysis", sub_scope: subScope, doc_id: id(number) }, title, subject,
    href: `/docs/?scope=analysis&doc=${id(subScope ? 99 : number)}${subScope ? "&subdoc=" + id(number) : ""}` };
}
const entry = (document, count = 1) => ({ document, occurrences: Array(count).fill({ label: "authored label", href: document.href }) });
const work = { state: "valid", kind: "work", key: "00523" };
const payload = { schema_version: 1, self: summary(1, "A"), outgoing: [
  entry(summary(2, "Zebra", "works", work), 2),
  entry(summary(3, "Concept", "concepts", work)),
  entry(summary(4, "Reference")),
  entry(summary(5, "Other child", "moments")),
  entry(summary(6, "alpha", "works", work))
], incoming: [entry(summary(2, "Zebra", "works", work)), entry(summary(4, "Reference")), entry(summary(7, "Reference"))] };
const originalPayload = structuredClone(payload);
const view = docsViewerLinksPresentation(payload, target);
assert.deepEqual(payload, originalPayload); // Direction and occurrences remain in the data.
assert.deepEqual(view.sections.map(s => s.label), ["Concepts", "Works", "References"]);
assert.equal(view.sections[0].entries.length, 1); // Concept classification wins subject overlap.
assert.deepEqual(view.sections[1].entries.map(e => e.document.title), ["alpha", "Zebra"]);
assert.deepEqual(view.sections[2].entries.map(e => e.document.target.doc_id), [id(4), id(7)]); // Include incoming-only documents; keep same-title identities distinct.
assert.equal(view.sections.flatMap(s => s.entries).some(e => "direction" in e), false);
const exactIdentities = docsViewerLinksPresentation({ ...payload,
  outgoing: [entry(summary(2, "Same", "works", work))],
  incoming: [entry(summary(2, "Same", "concepts")), entry(summary(2, "Same"))]
}, target);
assert.equal(exactIdentities.sections.length, 3); // Collection identity is part of deduplication.
assert.equal(new URL(view.sections[1].entries[0].document.href, "https://example.test").searchParams.get("stage"), "working");
assert.equal(payload.outgoing[0].document.href.includes("stage="), false);
assert.deepEqual(docsViewerLinksPresentation({ ...payload, outgoing: [], incoming: [] }, target).sections, []);
for (const change of [
  p => { p.self.target.sub_scope = "works"; },
  p => { p.schema_version = 2; },
  p => { p.outgoing[0].document.href = "javascript:alert(1)"; },
  p => { p.outgoing[0].document.href = "//other.test/docs/"; },
  p => { p.outgoing[0].document.href = `/docs/?doc=${id(2)}`; },
  p => { p.outgoing.push(p.outgoing[0]); }
]) {
  const bad = structuredClone(payload);
  change(bad);
  assert.throws(() => docsViewerLinksPresentation(bad, target));
}

// Configured provider preserves explicit stage and delegates one document read.
const calls = [];
const generatedData = createDocsViewerGeneratedDataRuntime({
  viewerScope: "analysis", viewerStage: "working", generatedBaseUrl: "http://127.0.0.1:8765",
  generatedData: { generatedDataReadChecked: true, generatedDataCapabilities: { generated_data_reads: true,
    scopes: { analysis: { stages: { working: { available: true, generated_data_reads: true } } } } } },
  window: { fetch: async (url, options) => { calls.push({ url, options }); return { ok: true, json: async () => payload }; } }
});
const provider = createDocsViewerConfiguredScopeProvider({ generatedData,
  scopeConfig: { scopeConfigsById: new Map([["analysis", { stage: "working", linksEnabled: true }]]) }
});
assert.equal(provider.canReadLinks(target), true);
assert.equal(provider.canReadLinks({ ...target, scope: "studio" }), false);
assert.equal(provider.canReadLinks({ ...target, stage: "pre-publish" }), false);
await assert.rejects(() => provider.readLinks({ ...target, stage: "" }), /not enabled/);
assert.equal(await provider.readLinks(target), payload);
assert.equal(calls.length, 1);
assert.equal(calls[0].url, `http://127.0.0.1:8765/docs/links?scope=analysis&stage=working&doc_id=${id(1)}`);
assert.equal(calls[0].options.cache, "no-store");

// Public reads only the configured static file, without capability/service requests.
let publicStatus = 200;
const publicCalls = [];
const publicData = createDocsViewerGeneratedDataRuntime({ window: { fetch: async url => {
  publicCalls.push(url);
  return { ok: publicStatus === 200, status: publicStatus, json: async () => payload };
} } });
const publicProvider = createDocsViewerConfiguredScopeProvider({ generatedData: publicData,
  scopeConfig: { scopeConfigsById: new Map([["analysis", { linksEnabled: true, linksByIdUrlBase: "/prepared/links-by-id" }]]) }
});
assert.equal(await publicProvider.readLinks({ ...target, stage: "" }), payload);
assert.deepEqual(publicCalls, [`/prepared/links-by-id/${id(1)}.json`]);
publicStatus = 404;
assert.equal(await publicProvider.readLinks({ ...target, stage: "" }), null);
publicStatus = 500;
await assert.rejects(() => publicProvider.readLinks({ ...target, stage: "" }), /Failed to load Links/);

// Real adapter request ownership: late child/navigation or mode-change responses cannot open a view.
const adapter = createDocsViewerLinksDetailAdapter();
const content = {};
const requests = [];
const opened = [];
const warnings = [];
const states = [];
const context = { content, target, title: "A", collectionProvider: {
  canReadLinks: () => true,
  readLinks: requested => new Promise(resolve => requests.push({ requested, resolve }))
}, projectControlState: state => states.push(state), showWarning: warning => warnings.push(warning),
requestContentDetail: presentation => { opened.push(presentation); return true; } };
adapter.mountDocument(context);
const first = adapter.openTarget({ content });
const child = { ...target, sub_scope: "works", doc_id: id(2) };
adapter.setDocument({ content, target: child, title: "Zebra" });
requests[0].resolve(payload);
assert.equal(await first, false);
const second = adapter.openTarget({ content });
assert.deepEqual(requests[1].requested, child);
requests[1].resolve({ ...payload, self: summary(2, "Zebra", "works", work) });
assert.equal(await second, true);
assert.equal(opened.length, 1);
assert.deepEqual(Object.keys(opened[0]).sort(), ["generation", "kind", "version"]); // Hosted contexts contain no DOM handles.
const control = { isConnected: true };
const third = adapter.openTarget({ content, invocationControl: control });
control.isConnected = false;
requests[2].resolve(payload);
assert.equal(await third, false);
assert.equal(states.at(-1).busy, false);
const fourth = adapter.openTarget({ content });
adapter.releaseDocument({ content });
requests[3].resolve(payload);
assert.equal(await fourth, false);
assert.equal(opened.length, 1);
assert.deepEqual(warnings, []);
assert.throws(() => adapter.mountPresentation({ content, targetContext: opened[0] }), /stale/);
const definitions = withDocsViewerContentDetailDefinitions(null, { linksDetailAdapter: adapter });
assert.equal(definitions.controls.find(c => c.id === "document-links").ownerViewId, "rendered-document");
assert.ok(definitions.views.find(v => v.id === "content-detail").load());
console.log("Links model, provider, static isolation and request ownership contracts passed.");
