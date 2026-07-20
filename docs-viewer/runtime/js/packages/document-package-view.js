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

export function renderPackageOptions(node, items, options = {}) {
  if (!node) return;
  const valueKey = options.valueKey || "id";
  const labelKey = options.labelKey || "label";
  const placeholder = packageText(options.placeholder);
  const selectedValue = packageText(options.selectedValue);
  const rows = [];
  if (placeholder) rows.push(`<option value="">${escapePackageHtml(placeholder)}</option>`);
  (items || []).forEach((item) => {
    const value = packageText(item && item[valueKey]);
    if (!value) return;
    const label = packageText(item && item[labelKey]) || value;
    const selected = value === selectedValue ? " selected" : "";
    rows.push(`<option value="${escapePackageHtml(value)}"${selected}>${escapePackageHtml(label)}</option>`);
  });
  node.innerHTML = rows.join("");
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

function documentDepth(record, byId, active = new Set()) {
  const id = packageText(record && (record.doc_id || record.id));
  const parentId = packageText(record && record.parent_id);
  if (!id || !parentId || active.has(id)) return 0;
  const parent = byId.get(parentId);
  if (!parent) return 0;
  active.add(id);
  return 1 + documentDepth(parent, byId, active);
}

function prepareRowMeta(record) {
  const parts = [packageText(record.doc_id || record.id)];
  if (record.viewable === false) parts.push("not viewable");
  if (record.published === false) parts.push("not published");
  if (!packageText(record.summary)) parts.push("no summary");
  return parts.filter(Boolean).join(" · ");
}

export function renderSelectablePackageDocuments(container, documents, options = {}) {
  if (!container) return [];
  const filter = packageText(options.filter).toLowerCase();
  const selectedIds = options.selectedIds instanceof Set ? options.selectedIds : new Set();
  const byId = new Map(
    (documents || []).map((record) => [packageText(record && (record.doc_id || record.id)), record])
  );
  const visible = (documents || []).filter((record) => {
    const haystack = `${packageText(record && record.title)} ${packageText(record && record.doc_id)}`.toLowerCase();
    return !filter || haystack.includes(filter);
  });
  if (!visible.length) {
    container.innerHTML = `<p class="docsPackageEmpty">${filter ? "No documents match the filter." : "No documents are available."}</p>`;
    return [];
  }
  container.innerHTML = "";
  visible.forEach((record) => {
    const docId = packageText(record && (record.doc_id || record.id));
    const selectable = Boolean(docId && record.selectable !== false);
    const row = document.createElement("div");
    row.className = "docsPackageDocumentRow";
    row.style.setProperty("--package-row-depth", String(documentDepth(record, byId)));

    const label = document.createElement("label");
    label.className = "docsPackageDocumentRow__label";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = docId;
    checkbox.checked = selectedIds.has(docId);
    checkbox.disabled = !selectable;
    checkbox.addEventListener("change", () => {
      if (typeof options.onToggle === "function") options.onToggle(docId, checkbox.checked);
    });
    const text = document.createElement("span");
    text.className = "docsPackageDocumentRow__text";
    text.innerHTML = `
      <span class="docsPackageDocumentRow__title">${escapePackageHtml(packageText(record.title) || docId)}</span>
      <span class="docsPackageDocumentRow__meta">${escapePackageHtml(prepareRowMeta(record))}</span>
    `;
    label.append(checkbox, text);

    const size = document.createElement("span");
    size.className = "docsPackageDocumentRow__size";
    const length = Number(record.content_text_length || 0);
    size.textContent = length > 0 ? `${length.toLocaleString()} chars` : "";
    row.append(label, size);
    container.appendChild(row);
  });
  return visible;
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
