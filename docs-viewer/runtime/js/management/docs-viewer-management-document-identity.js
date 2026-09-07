import { managedDocumentTargetsEqual } from "./docs-viewer-management-document-target.js";

/** Document-owned identities are exact three-digit strings in separate sequences. */
export function isDocsViewerDocumentIdentity(value) {
  return typeof value === "string" && value.length === 3 && /^[0-9]{3}$/.test(value);
}

/** Read a revision only after checking the full stage-owned metadata target. */
export function documentIdentityMetadataRevision(response, target) {
  var candidate = response && {
    scope: response.scope,
    ...(response.stage ? { stage: response.stage } : {}),
    sub_scope: response.sub_scope,
    doc_id: response.doc_id
  };
  if (!managedDocumentTargetsEqual(candidate, target)
    || !response.record || response.record.doc_id !== target.doc_id
    || !/^sha256:[0-9a-f]{64}$/.test(response.source_revision || "")) {
    throw new Error("Document metadata did not match its exact target and revision.");
  }
  return response.source_revision;
}

/** Validate allocation responses before refreshing a document or presenting its ID. */
export function allocatedDocumentIdentity(response, target, kind) {
  if (!response || !managedDocumentTargetsEqual(response.target, target)
    || response.ok !== true || response.operation !== "allocate_identity"
    || response.kind !== kind || response.field !== kind + "_id"
    || typeof response.changed !== "boolean"
    || !isDocsViewerDocumentIdentity(response.value)
    || !/^sha256:[0-9a-f]{64}$/.test(response.source_revision || "")) {
    throw new Error("Document identity allocation returned an invalid response.");
  }
  return response;
}

/** Project identity independently of title, heading and authoring Subject. */
export function documentIdentityInfoField(record, kind) {
  var value = record && record.customisation && record.customisation[kind + "_id"];
  var absent = value == null || value === "";
  var valid = isDocsViewerDocumentIdentity(value);
  return Object.freeze({
    id: kind + "_id", label: kind === "concept" ? "Concept ID" : "Moment ID",
    state: absent ? "unassigned" : valid ? "assigned" : "unavailable",
    value: absent ? "Unassigned" : valid ? value : "Malformed",
    detail: absent || valid ? "" : String(value)
  });
}

/** Always offer the configured Working control; repeat clicks preserve an existing ID. */
export function renderDocumentIdentityControl(context, options, kind) {
  var settings = context || {};
  var host = settings.host;
  if (!host || typeof settings.registerAction !== "function") return;
  var label = kind === "concept" ? "Concept" : "Moment";
  var info = documentIdentityInfoField(settings.document, kind);
  var button = host.ownerDocument.createElement("button");
  var registration = settings.registerAction({
    id: "allocate-" + kind, placement: "detail-toolbar", targetKind: "validated-detail",
    capability: typeof options.readMetadata === "function" && typeof options.allocateIdentity === "function",
    emptyState: "omitted", refreshEffect: "none",
    handler: async function (target, actionContext) {
      var metadata = await options.readMetadata(target);
      var response = allocatedDocumentIdentity(await options.allocateIdentity(target, {
        source_revision: documentIdentityMetadataRevision(metadata, target), confirm: true
      }), target, kind);
      if (actionContext && typeof actionContext.refreshDocument === "function") {
        await actionContext.refreshDocument(target);
      }
      return response;
    }
  });
  if (registration.hidden) return;
  button.className = "docsViewerReport__button docsReportDetail__iconButton";
  button.type = "button";
  button.textContent = label + (info.state === "assigned" ? " " + info.value : "");
  button.disabled = !registration.enabled;
  button.addEventListener("click", function () {
    if (button.disabled) return;
    button.disabled = true;
    registration.invoke().catch(function (error) {
      if (typeof options.setStatus === "function") options.setStatus(error.message || "Identity allocation failed.", true);
    }).finally(function () {
      if (button.isConnected) button.disabled = !registration.enabled;
    });
  });
  host.appendChild(button);
}
