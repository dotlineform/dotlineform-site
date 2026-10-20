export function packageText(value) {
  return String(value == null ? "" : value).trim();
}

export function packageIssueMessage(issue) {
  if (typeof issue === "string") return packageText(issue);
  if (!issue || typeof issue !== "object") return "";
  return packageText(issue.message || issue.error || issue.code);
}
