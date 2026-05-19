function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function uniqueSorted(values) {
  return Array.from(new Set(values.map(cleanString).filter(Boolean))).sort((a, b) => a.localeCompare(b));
}

function entryId(entry) {
  return cleanString(entry && entry.id);
}

function entryTitle(entry) {
  return cleanString(entry && entry.title) || entryId(entry);
}

function entryDate(entry) {
  return cleanString(entry && entry.date);
}

function entrySummary(entry) {
  return cleanString(entry && entry.summary);
}

function entryDomains(entry) {
  return Array.isArray(entry && entry.domains) ? entry.domains.map(cleanString).filter(Boolean) : [];
}

function selectedDomainFromRoute(domains) {
  const params = new URLSearchParams(window.location.search);
  const selected = cleanString(params.get("report_domain")).toLowerCase();
  if (!selected) return "";
  return domains.includes(selected) ? selected : "";
}

function persistSelectedDomain(domain) {
  const url = new URL(window.location.href);
  if (domain) {
    url.searchParams.set("report_domain", domain);
  } else {
    url.searchParams.delete("report_domain");
  }
  try {
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  } catch (_error) {
    // Route persistence is useful in the viewer but should not block report rendering.
  }
}

function fetchChangeHistory(context) {
  const baseUrl = cleanString(context.managementBaseUrl).replace(/\/+$/, "");
  if (!baseUrl) {
    return Promise.reject(new Error("Local docs-management server is not configured."));
  }
  return window.fetch(baseUrl + "/docs/generated/docs-log?projection=search-index", {
    headers: { Accept: "application/json" },
    cache: "no-store"
  }).then((response) => {
    return response.json().catch(() => {
      throw new Error("HTTP " + response.status);
    }).then((payload) => {
      if (!response.ok) {
        throw new Error(payload && payload.error ? payload.error : "HTTP " + response.status);
      }
      return payload;
    });
  });
}

function renderToolbar(root, state) {
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";

  const label = document.createElement("label");
  label.className = "docsViewerReport__selectLabel";
  label.setAttribute("for", "docsViewerChangeHistoryDomain");
  label.textContent = "Domain";

  const select = document.createElement("select");
  select.id = "docsViewerChangeHistoryDomain";
  select.className = "docsViewerReport__select";

  const all = document.createElement("option");
  all.value = "";
  all.textContent = "All domains";
  select.appendChild(all);

  state.domains.forEach((domain) => {
    const option = document.createElement("option");
    option.value = domain;
    option.textContent = domain;
    select.appendChild(option);
  });
  select.value = state.selectedDomain;

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";

  toolbar.appendChild(label);
  toolbar.appendChild(select);
  toolbar.appendChild(status);

  select.addEventListener("change", () => {
    state.selectedDomain = cleanString(select.value);
    persistSelectedDomain(state.selectedDomain);
    renderEntries(state);
  });

  state.statusNode = status;
  root.appendChild(toolbar);
}

function appendEntry(parent, entry) {
  const row = document.createElement("li");
  row.className = "docsViewerReport__changeEntry";
  row.dataset.changeEntryId = entryId(entry);

  const heading = document.createElement("h2");
  heading.className = "docsViewerReport__changeTitle";
  heading.textContent = entryTitle(entry);

  const meta = document.createElement("p");
  meta.className = "docsViewerReport__subtext";
  const domains = entryDomains(entry);
  meta.textContent = [entryDate(entry), domains.join(", ")].filter(Boolean).join(" - ");

  const summary = document.createElement("p");
  summary.className = "docsViewerReport__changeSummary";
  summary.textContent = entrySummary(entry);

  row.appendChild(heading);
  row.appendChild(meta);
  row.appendChild(summary);
  parent.appendChild(row);
}

function renderEntries(state) {
  clearNode(state.entriesNode);
  const visible = state.selectedDomain
    ? state.entries.filter((entry) => entryDomains(entry).includes(state.selectedDomain))
    : state.entries;
  state.statusNode.textContent = visible.length === 1 ? "1 entry" : `${visible.length} entries`;
  visible.forEach((entry) => appendEntry(state.entriesNode, entry));
}

export function mountChangeHistoryReport(context) {
  const root = context.reportRoot;
  clearNode(root);

  return fetchChangeHistory(context).then((payload) => {
    const entries = Array.isArray(payload && payload.entries)
      ? payload.entries.filter((entry) => entryId(entry))
      : [];
    const domains = uniqueSorted(entries.flatMap(entryDomains));
    const state = {
      context,
      entries,
      domains,
      selectedDomain: selectedDomainFromRoute(domains),
      statusNode: null,
      entriesNode: document.createElement("ul")
    };
    state.entriesNode.className = "docsViewerReport__changeEntries";
    renderToolbar(root, state);
    root.appendChild(state.entriesNode);
    renderEntries(state);
  }).catch((error) => {
    clearNode(root);
    const status = document.createElement("p");
    status.className = "docsViewerReport__status";
    status.textContent = error && error.message ? error.message : "Failed to load change history.";
    root.appendChild(status);
  });
}
