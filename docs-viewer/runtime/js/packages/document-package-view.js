export function packageText(value) {
  return String(value == null ? "" : value).trim();
}

export function profileForId(profiles, profileId) {
  const normalized = packageText(profileId);
  return (profiles || []).find((profile) => packageText(profile && profile.profile_id) === normalized) || null;
}

export function packageIssueMessage(issue) {
  if (typeof issue === "string") return packageText(issue);
  if (!issue || typeof issue !== "object") return "";
  return packageText(issue.message || issue.error || issue.code);
}
