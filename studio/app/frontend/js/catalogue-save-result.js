/** Report an incomplete local Save without implying generated data was refreshed. */
export function catalogueSaveCompletionError(response) {
  const completion = response?.save_completion;
  if (completion?.status !== "failed") return "";
  return `${completion.message || "Data saved, but local Save completion did not finish."} ${completion.error || ""}`.trim();
}

/** Keep a confirmed mutation distinct from a later editor refresh failure. */
export function catalogueSavedActionError(response, error) {
  if (!response?.saved) return "";
  const message = catalogueSaveCompletionError(response) || (response.created_ids?.length
    ? `Works created (${response.created_ids.join(", ")}), but the editor could not refresh.`
    : "Changes saved, but the editor could not refresh.");
  return `${message} ${error?.message || ""}`.trim();
}
