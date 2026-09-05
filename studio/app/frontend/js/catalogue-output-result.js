/** Describe output completion separately from the already persisted canonical edit. */
export function catalogueOutputError(response) {
  const output = response?.output;
  if (output?.status !== "failed") return "";
  return `${output.message || "Data saved, but output generation did not complete."} ${output.error || ""}`.trim();
}

/** Keep a confirmed mutation distinct from a later editor refresh failure. */
export function catalogueSavedActionError(response, error) {
  if (!response?.saved) return "";
  const message = catalogueOutputError(response) || "Changes saved, but the editor could not refresh.";
  return `${message} ${error?.message || ""}`.trim();
}
