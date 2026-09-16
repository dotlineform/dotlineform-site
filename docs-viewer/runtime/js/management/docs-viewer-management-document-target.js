function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function targetKeys(target) {
  return Object.keys(target || {}).sort();
}

function sameKeys(actual, expected) {
  return actual.length === expected.length && actual.every(function (key, index) {
    return key === expected[index];
  });
}

export function normalizeManagedDocumentTarget(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Managed document target must be an object.");
  }
  var keys = targetKeys(value);
  var parentKeys = ["doc_id", "stage"];
  var subScopeKeys = ["doc_id", "stage", "sub_scope"];
  if (!sameKeys(keys, parentKeys) && !sameKeys(keys, subScopeKeys)) {
    throw new Error(
      "Managed document target must contain exactly stage and doc_id, "
      + "with sub_scope only for a sub-scope document."
    );
  }

  var docId = cleanString(value.doc_id);
  if (!["working", "pre-publish", "published"].includes(value.stage)) throw new Error("Managed target stage is required.");
  if (!docId) throw new Error("Managed document target doc_id is required.");

  var target = {
    stage: value.stage,
    doc_id: docId
  };
  if (Object.prototype.hasOwnProperty.call(value, "sub_scope")) {
    var subScope = cleanString(value.sub_scope).toLowerCase();
    if (!subScope) throw new Error("Managed document target sub_scope is required.");
    target.sub_scope = subScope;
  }
  return Object.freeze(target);
}

export function normalizeManagedDocumentCollectionTarget(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Managed document collection target must be an object.");
  }
  var keys = targetKeys(value);
  var parentKeys = ["stage"];
  var subScopeKeys = ["stage", "sub_scope"];
  if (!sameKeys(keys, parentKeys) && !sameKeys(keys, subScopeKeys)) {
    throw new Error(
      "Managed document collection target must contain exactly stage, "
      + "with sub_scope only for a configured child collection."
    );
  }

  if (!["working", "pre-publish", "published"].includes(value.stage)) throw new Error("Managed collection stage is required.");

  var target = { stage: value.stage };
  if (Object.prototype.hasOwnProperty.call(value, "sub_scope")) {
    var subScope = cleanString(value.sub_scope).toLowerCase();
    if (!subScope) {
      throw new Error("Managed document collection target sub_scope is required.");
    }
    target.sub_scope = subScope;
  }
  return Object.freeze(target);
}

export function managedDocumentTargetsEqual(left, right) {
  var normalizedLeft = normalizeManagedDocumentTarget(left);
  var normalizedRight = normalizeManagedDocumentTarget(right);
  return (
    cleanString(normalizedLeft.stage) === cleanString(normalizedRight.stage)
    && normalizedLeft.doc_id === normalizedRight.doc_id
    && cleanString(normalizedLeft.sub_scope) === cleanString(normalizedRight.sub_scope)
  );
}
