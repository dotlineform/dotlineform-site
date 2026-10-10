/**
 * Resolve the server-validated central policy for one exact document/collection
 * target. The first match owns restrictions; unmatched targets keep their actions.
 * Missing capabilities disable invocation until the policy has been received.
 */
export function managedDocumentActionState(capabilities, actionId, target) {
  var policy = capabilities && capabilities.document_actions;
  if (!policy || policy.schema !== "docs_management_document_actions_v1" || !Array.isArray(policy.rules)) {
    return { hidden: false, disabled: true, reason: "Document action policy is unavailable." };
  }
  if (!target) return { hidden: false, disabled: true, reason: "No document target." };
  var rule = policy.rules.find(function (entry) {
    var match = entry.match;
    return match.collections ? match.collections.includes(target.collection)
      : !target.collection && match.doc_ids.includes(target.doc_id);
  });
  var allowed = !rule || (rule.allow ? rule.allow.includes(actionId) : !rule.deny.includes(actionId));
  return { hidden: !allowed, disabled: !allowed, reason: allowed ? "" : rule.reason };
}
