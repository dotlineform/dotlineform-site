export function buildStudioActivityContext({
  pageId,
  actionId,
  route,
  controlId,
  controlSelector,
  recordIdField,
  recordId
}) {
  const normalizedActionId = String(actionId || "").trim();
  const normalizedRecordId = String(recordId || "").trim();
  const fallback = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const randomId = window.crypto && typeof window.crypto.randomUUID === "function"
    ? window.crypto.randomUUID()
    : fallback;
  return {
    page_id: pageId,
    action_id: normalizedActionId,
    route,
    control_id: controlId,
    control_selector: controlSelector,
    correlation_id: `${normalizedActionId}:${normalizedRecordId}:${randomId}`,
    [recordIdField]: normalizedRecordId
  };
}
