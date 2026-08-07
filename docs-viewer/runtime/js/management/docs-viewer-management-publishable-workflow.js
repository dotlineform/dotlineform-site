import {
  setManagedDocsPublishable
} from "./docs-viewer-management-client.js";
import {
  normalizeManagedDocumentCollectionTarget
} from "./docs-viewer-management-document-target.js";
import {
  openDocsViewerChoiceModal
} from "./docs-viewer-management-modal-shell.js";

function exactDocIds(values) {
  if (!Array.isArray(values) || !values.length) {
    throw new Error("Select one or more documents.");
  }
  var seen = new Set();
  return values.map(function (value) {
    if (typeof value !== "string" || !value || value !== value.trim()) {
      throw new Error("Every checked document id must be exact and non-blank.");
    }
    if (seen.has(value)) {
      throw new Error("Checked document ids must not contain duplicates.");
    }
    var docId = value;
    seen.add(docId);
    return docId;
  });
}

function sameCollection(left, right) {
  return (
    left.scope === right.scope
    && String(left.sub_scope || "") === String(right.sub_scope || "")
  );
}

function setBusy(callbacks, busy) {
  if (typeof callbacks.setBusy === "function") callbacks.setBusy(busy);
  if (typeof callbacks.render === "function") callbacks.render();
}

function setMessage(callbacks, message, isError) {
  if (typeof callbacks.setMessage === "function") {
    callbacks.setMessage(message, isError);
  }
}

export function setPublishableChoiceOptions(options = {}) {
  var count = exactDocIds(options.checkedDocIds).length;
  return {
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Set Publishable…",
    body: count + " checked document" + (count === 1 ? "." : "s."),
    name: "docsViewerSetPublishableChoice",
    value: "",
    choices: [
      { value: "include", label: "Include in next Publish" },
      { value: "exclude", label: "Exclude from next Publish" }
    ],
    primaryLabel: "OK",
    cancelLabel: "Cancel",
    requiredMessage: "Choose whether to include or exclude the checked documents."
  };
}

export function validateSetPublishableResponse(response, options = {}) {
  var payload = response && typeof response === "object" ? response : {};
  var source = normalizeManagedDocumentCollectionTarget(options.source);
  var requestedDocIds = exactDocIds(options.checkedDocIds);
  var responseTarget = normalizeManagedDocumentCollectionTarget(payload.target);
  var responseDocIds;
  try {
    responseDocIds = exactDocIds(payload.requested_doc_ids);
  } catch (error) {
    throw new Error(
      "Set Publishable response did not match the exact checked selection.",
      { cause: error }
    );
  }
  if (
    payload.ok !== true
    || payload.operation !== "set_publishable"
    || payload.publishable !== options.publishable
    || !sameCollection(responseTarget, source)
    || responseDocIds.length !== requestedDocIds.length
    || responseDocIds.some(function (docId, index) {
      return docId !== requestedDocIds[index];
    })
  ) {
    throw new Error("Set Publishable response did not match the exact checked selection.");
  }
  return payload;
}

export async function openDocsViewerSetPublishableWorkflow(options = {}) {
  var source = normalizeManagedDocumentCollectionTarget(options.source);
  var checkedDocIds = exactDocIds(options.checkedDocIds);
  var callbacks = options.callbacks || {};
  var choose = options.choose || openDocsViewerChoiceModal;
  var apply = options.apply || setManagedDocsPublishable;
  var choice = await choose(setPublishableChoiceOptions({
    root: options.root,
    restoreFocus: options.restoreFocus,
    checkedDocIds: checkedDocIds
  }));
  if (!choice || choice.confirmed !== true) return null;
  if (!["include", "exclude"].includes(choice.value)) {
    throw new Error("Set Publishable choice is invalid.");
  }

  var publishable = choice.value === "include";
  var applied;
  setBusy(callbacks, true);
  setMessage(callbacks, "Updating checked documents…", false);
  try {
    applied = await apply(
      source,
      checkedDocIds,
      publishable,
      options.clientOptions || {}
    );
    applied = validateSetPublishableResponse(applied, {
      source: source,
      checkedDocIds: checkedDocIds,
      publishable: publishable
    });
    if (typeof callbacks.onApplied === "function") {
      await callbacks.onApplied(applied);
    }
    setMessage(callbacks, applied.summary_text || "Publishability updated.", false);
    return applied;
  } catch (error) {
    setMessage(
      callbacks,
      error && error.message ? error.message : "Set Publishable failed.",
      true
    );
    return null;
  } finally {
    setBusy(callbacks, false);
  }
}
