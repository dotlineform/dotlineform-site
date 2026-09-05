/** Describe output completion separately from the already persisted canonical edit. */
export function catalogueOutputError(response) {
  const output = response?.output;
  if (output?.status !== "failed") return "";
  return `${output.message || "Data saved, but output generation did not complete."} ${output.error || ""}`.trim();
}
