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
  var parentKeys = ["doc_id", "scope"];
  var subScopeKeys = ["doc_id", "scope", "sub_scope"];
  if (!sameKeys(keys, parentKeys) && !sameKeys(keys, subScopeKeys)) {
    throw new Error(
      "Managed document target must contain exactly scope and doc_id, "
      + "with sub_scope only for a sub-scope document."
    );
  }

  var scope = cleanString(value.scope).toLowerCase();
  var docId = cleanString(value.doc_id);
  if (!scope) throw new Error("Managed document target scope is required.");
  if (!docId) throw new Error("Managed document target doc_id is required.");

  var target = {
    scope: scope,
    doc_id: docId
  };
  if (Object.prototype.hasOwnProperty.call(value, "sub_scope")) {
    var subScope = cleanString(value.sub_scope).toLowerCase();
    if (!subScope) throw new Error("Managed document target sub_scope is required.");
    target.sub_scope = subScope;
  }
  return Object.freeze(target);
}

export function managedDocumentTargetsEqual(left, right) {
  var normalizedLeft = normalizeManagedDocumentTarget(left);
  var normalizedRight = normalizeManagedDocumentTarget(right);
  return (
    normalizedLeft.scope === normalizedRight.scope
    && normalizedLeft.doc_id === normalizedRight.doc_id
    && cleanString(normalizedLeft.sub_scope) === cleanString(normalizedRight.sub_scope)
  );
}
