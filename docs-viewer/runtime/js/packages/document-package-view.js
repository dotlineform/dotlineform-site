export function packageText(value) {
  return String(value == null ? "" : value).trim();
}

export function escapePackageHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function setPackageStatus(node, state, message) {
  if (!node) return;
  node.textContent = packageText(message);
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

export function setPackageBusy(root, busy) {
  if (!root) return;
  root.dataset.documentPackageBusy = busy ? "true" : "false";
}

export function setPackageReady(root, ready) {
  if (!root) return;
  root.dataset.documentPackageReady = ready ? "true" : "false";
}

export function selectedScopeFromUrl(scopes) {
  const requested = packageText(new URL(window.location.href).searchParams.get("scope")).toLowerCase();
  return (scopes || []).some((item) => packageText(item.scope) === requested) ? requested : "";
}

export function packageScopeLabel(scopes, scope) {
  const normalized = packageText(scope);
  const record = (scopes || []).find((item) => packageText(item && item.scope) === normalized);
  return packageText(record && record.label) || normalized;
}

export function syncPackageScopeLinks(scope) {
  const normalized = packageText(scope);
  document.querySelectorAll("[data-package-scope-link]").forEach((link) => {
    const baseHref = packageText(link.dataset.packageScopeLink);
    if (!baseHref) return;
    const url = new URL(baseHref, window.location.origin);
    if (normalized) url.searchParams.set("scope", normalized);
    link.href = `${url.pathname}${url.search}${url.hash}`;
  });
}

export function profileForId(profiles, profileId) {
  const normalized = packageText(profileId);
  return (profiles || []).find((profile) => packageText(profile && profile.profile_id) === normalized) || null;
}

export function formatPackageBytes(value) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function packageIssueMessage(issue) {
  if (typeof issue === "string") return packageText(issue);
  if (!issue || typeof issue !== "object") return "";
  return packageText(issue.message || issue.error || issue.code);
}

export function renderReturnedPackageRows(container, rows) {
  if (!container) return;
  const records = Array.isArray(rows) ? rows : [];
  if (!records.length) {
    container.innerHTML = '<p class="docsPackageEmpty">The inspected package contains no displayable document rows.</p>';
    return;
  }
  container.innerHTML = records.map((row) => {
    const issues = (Array.isArray(row.issues) ? row.issues : []).map(packageIssueMessage).filter(Boolean);
    const depth = Math.max(0, Number(row.depth || 0));
    return `
      <div class="docsPackageDocumentRow" style="--package-row-depth: ${depth}">
        <span class="docsPackageDocumentRow__text">
          <span class="docsPackageDocumentRow__title">${escapePackageHtml(packageText(row.title) || "missing title")}</span>
          <span class="docsPackageDocumentRow__meta">${escapePackageHtml(packageText(row.meta))}</span>
          ${issues.length ? `<span class="docsPackageDocumentRow__issues" data-state="error">${escapePackageHtml(issues.join(" · "))}</span>` : ""}
        </span>
      </div>
    `;
  }).join("");
}

export function packageCountsHtml(counts) {
  if (!counts || typeof counts !== "object") return "";
  const rows = Object.entries(counts).filter(([, value]) => Number.isFinite(Number(value)));
  if (!rows.length) return "";
  return `<dl class="docsPackageModal__counts">${rows.map(([key, value]) => `
    <div><dt>${escapePackageHtml(key.replace(/_/g, " "))}</dt><dd>${escapePackageHtml(String(value))}</dd></div>
  `).join("")}</dl>`;
}

export function packageIssuesHtml(payload) {
  const issues = [
    ...(Array.isArray(payload && payload.errors) ? payload.errors : []),
    ...(Array.isArray(payload && payload.warnings) ? payload.warnings : []),
    ...(Array.isArray(payload && payload.issues) ? payload.issues : [])
  ].map(packageIssueMessage).filter(Boolean);
  if (!issues.length) return "";
  return `<section class="docsPackageModal__issues"><strong>Issues</strong><ul>${issues.map((item) => `<li>${escapePackageHtml(item)}</li>`).join("")}</ul></section>`;
}

export function packagePathsHtml(payload) {
  const paths = [
    payload && payload.output_file,
    payload && payload.metadata_file,
    payload && payload.context_file,
    ...(Array.isArray(payload && payload.output_files) ? payload.output_files : [])
  ].map(packageText).filter((value, index, all) => value && all.indexOf(value) === index);
  if (!paths.length) return "";
  return `<section class="docsPackageModal__paths"><strong>Files</strong>${paths.map((path) => `<code>${escapePackageHtml(path)}</code>`).join("")}</section>`;
}
