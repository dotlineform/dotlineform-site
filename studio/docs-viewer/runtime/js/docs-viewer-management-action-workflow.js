import {
  isDocViewable
} from "./docs-viewer-tree.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function docTitleList(docs) {
  return docs.map(function (item) {
    return item.title || item.doc_id;
  }).join(", ");
}

function docLabel(doc) {
  return doc && doc.title ? doc.title : (doc && doc.doc_id ? doc.doc_id : "");
}

function parentLabel(parentId, options) {
  var normalized = normalizeText(parentId);
  var text = options.text || {};
  if (!normalized) return text.normalizeOrderRootLabel;
  var docsById = options.docsById instanceof Map ? options.docsById : new Map();
  return docLabel(docsById.get(normalized)) || normalized;
}

function formatText(options, template, tokens) {
  if (typeof options.formatText === "function") {
    return options.formatText(template, tokens);
  }
  var text = String(template || "");
  Object.keys(tokens || {}).forEach(function (key) {
    text = text.replace(new RegExp("\\{" + key + "\\}", "g"), tokens[key]);
  });
  return text;
}

export function collectDescendantDocIds(docs, docId, bucket) {
  var records = Array.isArray(docs) ? docs : [];
  var targetDocId = normalizeText(docId);
  var targetBucket = bucket instanceof Set ? bucket : new Set();
  if (!targetDocId) return targetBucket;
  records.forEach(function (candidate) {
    if (!candidate || (candidate.parent_id || "") !== targetDocId || targetBucket.has(candidate.doc_id)) return;
    targetBucket.add(candidate.doc_id);
    collectDescendantDocIds(records, candidate.doc_id, targetBucket);
  });
  return targetBucket;
}

export function buildNormalizeOrderChoices(options = {}) {
  var doc = options.doc || null;
  var text = options.text || {};
  var choices = [];
  var seen = new Set();

  function push(value, label) {
    if (!value || seen.has(value)) return;
    seen.add(value);
    choices.push({ value: value, label: label });
  }

  if (doc) {
    var currentParentId = normalizeText(doc.parent_id);
    push(
      "parent:" + currentParentId,
      formatText(options, text.normalizeOrderCurrentSiblingsLabel, {
        parent: parentLabel(currentParentId, options)
      })
    );
    push(
      "parent:" + doc.doc_id,
      formatText(options, text.normalizeOrderSelectedChildrenLabel, {
        title: docLabel(doc)
      })
    );
  }
  push("parent:", text.normalizeOrderRootChoiceLabel);
  push("whole", text.normalizeOrderWholeScopeLabel);
  return choices;
}

export function normalizeOrderPayload(choiceValue) {
  var value = normalizeText(choiceValue);
  if (value === "whole") return { whole_scope: true };
  if (value.indexOf("parent:") === 0) {
    return { parent_id: value.slice("parent:".length) };
  }
  return null;
}

export function nonViewableAncestorDocs(doc, findDocById) {
  var ancestors = [];
  var current = doc && doc.parent_id && typeof findDocById === "function" ? findDocById(doc.parent_id) : null;
  while (current) {
    if (!isDocViewable(current)) {
      ancestors.unshift(current);
    }
    current = current.parent_id && typeof findDocById === "function" ? findDocById(current.parent_id) : null;
  }
  return ancestors;
}

export async function resolveViewabilityTargetDocIds(options = {}) {
  var doc = options.doc || null;
  if (!doc || !doc.doc_id) return null;

  var ancestors = nonViewableAncestorDocs(doc, options.findDocById);
  if (ancestors.length && typeof options.confirmAncestors === "function") {
    var confirmedAncestors = await options.confirmAncestors({
      ancestors: ancestors,
      titles: docTitleList(ancestors)
    });
    if (!confirmedAncestors) {
      return null;
    }
  }

  var includeDescendants = false;
  var descendantIds = Array.from(collectDescendantDocIds(options.allDocs, doc.doc_id, new Set()));
  if (descendantIds.length && typeof options.chooseDescendants === "function") {
    var descendantChoice = await options.chooseDescendants({
      descendantIds: descendantIds
    });
    if (!descendantChoice || !descendantChoice.confirmed) {
      return null;
    }
    var normalizedChoice = normalizeText(descendantChoice.value).toLowerCase();
    if (normalizedChoice === "all") {
      includeDescendants = true;
    } else if (normalizedChoice !== "selected") {
      if (typeof options.onInvalidChoice === "function") {
        options.onInvalidChoice(normalizedChoice);
      }
      return null;
    }
  }

  var targetIds = new Set();
  ancestors.forEach(function (ancestor) {
    targetIds.add(ancestor.doc_id);
  });
  targetIds.add(doc.doc_id);
  if (includeDescendants) {
    descendantIds.forEach(function (docId) {
      targetIds.add(docId);
    });
  }
  return Array.from(targetIds);
}
