const PAGE_SIZE = 20;

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

function selectedPageFromRoute() {
  const params = new URLSearchParams(window.location.search);
  const page = Number.parseInt(cleanString(params.get("report_page")), 10);
  return Number.isFinite(page) && page > 0 ? page : 1;
}

function selectedQueryFromRoute() {
  const params = new URLSearchParams(window.location.search);
  return cleanString(params.get("report_query"));
}

function persistReportRoute(state) {
  const url = new URL(window.location.href);
  if (state.selectedDomain) {
    url.searchParams.set("report_domain", state.selectedDomain);
  } else {
    url.searchParams.delete("report_domain");
  }
  if (state.query) {
    url.searchParams.set("report_query", state.query);
  } else {
    url.searchParams.delete("report_query");
  }
  if (state.currentPage > 1) {
    url.searchParams.set("report_page", String(state.currentPage));
  } else {
    url.searchParams.delete("report_page");
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

function entrySearchText(entry) {
  const weighted = entry && entry.search_text && typeof entry.search_text === "object" ? entry.search_text : {};
  return [
    weighted.title,
    weighted.trace,
    weighted.summary,
    weighted.body,
    entryTitle(entry),
    entryDate(entry),
    entrySummary(entry),
    entryDomains(entry).join(" ")
  ].map(cleanString).filter(Boolean).join(" ").toLowerCase();
}

function queryTokens(query) {
  return cleanString(query).toLowerCase().split(/\s+/).filter(Boolean);
}

function matchesQuery(entry, query) {
  const tokens = queryTokens(query);
  if (!tokens.length) return true;
  const haystack = entrySearchText(entry);
  return tokens.every((token) => haystack.includes(token));
}

function renderSearchControl(state) {
  const wrap = document.createElement("div");
  wrap.className = "docsViewerReport__search";

  const input = document.createElement("input");
  input.type = "search";
  input.className = "docsViewerReport__searchInput";
  input.placeholder = "search...";
  input.value = state.query;
  input.setAttribute("aria-label", "Search change history");

  const clear = document.createElement("button");
  clear.type = "button";
  clear.className = "docsViewerReport__searchClear";
  clear.textContent = "x";
  clear.title = "Clear search";
  clear.setAttribute("aria-label", "Clear search");

  input.addEventListener("input", () => {
    state.query = cleanString(input.value);
    state.currentPage = 1;
    persistReportRoute(state);
    renderEntries(state);
  });

  clear.addEventListener("click", () => {
    state.query = "";
    input.value = "";
    input.focus();
    state.currentPage = 1;
    persistReportRoute(state);
    renderEntries(state);
  });

  state.searchInputNode = input;
  state.searchClearNode = clear;
  wrap.appendChild(input);
  wrap.appendChild(clear);
  return wrap;
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

  toolbar.appendChild(label);
  toolbar.appendChild(select);
  toolbar.appendChild(renderSearchControl(state));
  toolbar.appendChild(state.topPagerNode);

  select.addEventListener("change", () => {
    state.selectedDomain = cleanString(select.value);
    state.currentPage = 1;
    persistReportRoute(state);
    renderEntries(state);
  });

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

function filteredEntries(state) {
  return state.entries
    .filter((entry) => matchesQuery(entry, state.query))
    .filter((entry) => !state.selectedDomain || entryDomains(entry).includes(state.selectedDomain));
}

function appendPagerButton(parent, label, ariaLabel, disabled, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "docsViewerReport__pagerButton";
  button.textContent = label;
  button.setAttribute("aria-label", ariaLabel);
  button.title = ariaLabel;
  button.disabled = disabled;
  button.addEventListener("click", onClick);
  parent.appendChild(button);
}

function appendPagerControls(parent, state, pageCount) {
  if (pageCount <= 1) return;

  const previousDisabled = state.currentPage <= 1;
  const nextDisabled = state.currentPage >= pageCount;

  appendPagerButton(parent, "◀︎", "Previous page", previousDisabled, () => {
    if (previousDisabled) return;
    state.currentPage -= 1;
    persistReportRoute(state);
    renderEntries(state);
  });

  const status = document.createElement("span");
  status.className = "docsViewerReport__pagerStatus";
  status.textContent = `${state.currentPage} of ${pageCount}`;
  parent.appendChild(status);

  appendPagerButton(parent, "▶︎", "Next page", nextDisabled, () => {
    if (nextDisabled) return;
    state.currentPage += 1;
    persistReportRoute(state);
    renderEntries(state);
  });
}

function renderPager(state, pageCount) {
  clearNode(state.topPagerNode);
  clearNode(state.bottomPagerNode);
  appendPagerControls(state.topPagerNode, state, pageCount);
  appendPagerControls(state.bottomPagerNode, state, pageCount);
}

function renderEntries(state) {
  clearNode(state.entriesNode);
  const visible = filteredEntries(state);
  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  state.currentPage = Math.min(Math.max(1, state.currentPage), pageCount);
  const start = (state.currentPage - 1) * PAGE_SIZE;
  const pageEntries = visible.slice(start, start + PAGE_SIZE);
  if (state.searchClearNode) {
    state.searchClearNode.hidden = !state.query;
  }
  if (pageEntries.length) {
    pageEntries.forEach((entry) => appendEntry(state.entriesNode, entry));
  } else {
    const empty = document.createElement("li");
    empty.className = "docsViewerReport__empty";
    empty.textContent = "No matching entries.";
    state.entriesNode.appendChild(empty);
  }
  renderPager(state, pageCount);
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
      query: selectedQueryFromRoute(),
      currentPage: selectedPageFromRoute(),
      searchInputNode: null,
      searchClearNode: null,
      entriesNode: document.createElement("ul"),
      topPagerNode: document.createElement("nav"),
      bottomPagerNode: document.createElement("nav")
    };
    state.entriesNode.className = "docsViewerReport__changeEntries";
    state.topPagerNode.className = "docsViewerReport__pager docsViewerReport__pager--top";
    state.topPagerNode.setAttribute("aria-label", "Change history pages");
    state.bottomPagerNode.className = "docsViewerReport__pager docsViewerReport__pager--bottom";
    state.bottomPagerNode.setAttribute("aria-label", "Change history pages");
    renderToolbar(root, state);
    root.appendChild(state.entriesNode);
    root.appendChild(state.bottomPagerNode);
    renderEntries(state);
  }).catch((error) => {
    clearNode(root);
    const status = document.createElement("p");
    status.className = "docsViewerReport__status";
    status.textContent = error && error.message ? error.message : "Failed to load change history.";
    root.appendChild(status);
  });
}
