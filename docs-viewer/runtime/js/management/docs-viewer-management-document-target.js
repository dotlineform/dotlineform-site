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
  var parentKeys = ["doc_id"];
  var collectionKeys = ["collection", "doc_id"];
  if (!sameKeys(keys, parentKeys) && !sameKeys(keys, collectionKeys)) {
    throw new Error(
      "Managed document target must contain doc_id, "
      + "with collection only for a collection document."
    );
  }

  var docId = cleanString(value.doc_id);
  if (!docId) throw new Error("Managed document target doc_id is required.");

  var target = {
    doc_id: docId
  };
  if (Object.prototype.hasOwnProperty.call(value, "collection")) {
    var collection = cleanString(value.collection).toLowerCase();
    if (!collection) throw new Error("Managed document target collection is required.");
    target.collection = collection;
  }
  return Object.freeze(target);
}

export function normalizeManagedDocumentCollectionTarget(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Managed document collection target must be an object.");
  }
  var keys = targetKeys(value);
  var parentKeys = [];
  var collectionKeys = ["collection"];
  if (!sameKeys(keys, parentKeys) && !sameKeys(keys, collectionKeys)) {
    throw new Error(
      "Managed document collection target must contain only an optional collection, "
      + "with collection only for a configured child collection."
    );
  }

  var target = {  };
  if (Object.prototype.hasOwnProperty.call(value, "collection")) {
    var collection = cleanString(value.collection).toLowerCase();
    if (!collection) {
      throw new Error("Managed document collection target collection is required.");
    }
    target.collection = collection;
  }
  return Object.freeze(target);
}

export function managedDocumentTargetsEqual(left, right) {
  var normalizedLeft = normalizeManagedDocumentTarget(left);
  var normalizedRight = normalizeManagedDocumentTarget(right);
  return (
    normalizedLeft.doc_id === normalizedRight.doc_id
    && cleanString(normalizedLeft.collection) === cleanString(normalizedRight.collection)
  );
}
