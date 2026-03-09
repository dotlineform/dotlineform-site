import {
  fetchJson
} from "./studio-data.js";
import {
  studioWorksUi
} from "./studio-ui.js";

const UI = studioWorksUi;
const { selector: UI_SELECTOR, state: UI_STATE } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initStudioWorksPage);
} else {
  initStudioWorksPage();
}

function initStudioWorksPage() {
  const worksListRoot = document.getElementById("worksCuratorRoot");
  const emptyEl = document.getElementById("worksCuratorEmpty");
  const list = document.getElementById("worksList");
  const countEl = document.getElementById("worksListCount");
  const backNav = document.getElementById("worksIndexBackNav");
  const backLink = document.getElementById("worksIndexBackLink");
  const buttons = Array.prototype.slice.call(document.querySelectorAll(UI_SELECTOR.sortButton));
  if (!worksListRoot || !emptyEl || !list || !countEl || !buttons.length) return;

  const baseurl = String(worksListRoot.dataset.baseurl || "");
  const worksIndexUrl = String(worksListRoot.dataset.worksIndexUrl || "");
  const seriesIndexUrl = String(worksListRoot.dataset.seriesIndexUrl || "");
  const seriesBaseHref = String(worksListRoot.dataset.seriesBaseHref || `${baseurl}/series/`);
  const validKeys = { cat: true, year: true, title: true, series: true, storage: true, seriessort: true };
  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const params = new URLSearchParams(window.location.search);
  const sortParam = params.get("sort");
  const hasExplicitSort = !(sortParam == null || String(sortParam).trim() === "");
  let sortKey = String(sortParam || "").toLowerCase();
  let sortDir = String(params.get("dir") || "asc").toLowerCase();
  const seriesFilter = String(params.get("series") || "").trim().toLowerCase();
  const hasSeriesFilter = seriesFilter.length > 0;
  let visualSortKey = sortKey;
  let totalWorksAll = 0;
  let totalSeriesAll = 0;

  if (!hasExplicitSort) sortKey = hasSeriesFilter ? "seriessort" : "cat";
  if (!validKeys[sortKey]) sortKey = hasSeriesFilter ? "seriessort" : "cat";
  if (!validKeys[sortKey]) sortKey = "cat";
  if (sortDir !== "asc" && sortDir !== "desc") sortDir = "asc";
  if (hasSeriesFilter) {
    worksListRoot.classList.add("worksList--singleSeries");
  }

  function normalizeText(value) {
    return String(value == null ? "" : value).trim();
  }

  function slugSortKey(value) {
    return normalizeText(value).toLowerCase();
  }

  function numericAwareSortKey(value) {
    return normalizeText(value).replace(/\d+/g, (match) => match.padStart(3, "0"));
  }

  function seriesPrimarySortFromSortFields(sortFieldsRaw) {
    let token = normalizeText(sortFieldsRaw).split(",")[0] || "";
    token = slugSortKey(token);
    if (token.charAt(0) === "-") token = token.slice(1);
    if (token === "work_id") return "cat";
    if (token === "year") return "year";
    if (token === "title" || token === "title_sort") return "title";
    if (token === "series" || token === "series_title") return "series";
    if (token === "storage" || token === "storage_location") return "storage";
    return "";
  }

  function isCustomSeriesSort(sortFieldsRaw) {
    const raw = normalizeText(sortFieldsRaw);
    if (!raw) return false;
    const parts = raw.split(",");
    let nonWork = 0;
    for (let idx = 0; idx < parts.length; idx += 1) {
      let token = slugSortKey(parts[idx]);
      if (token.charAt(0) === "-") token = token.slice(1);
      if (!token || token === "work_id") continue;
      nonWork += 1;
    }
    return nonWork > 0;
  }

  function buildSeriesMeta(seriesMap) {
    const out = {};
    if (!seriesMap || typeof seriesMap !== "object") return out;
    Object.keys(seriesMap).forEach((sidRaw) => {
      const sid = slugSortKey(sidRaw);
      if (!sid) return;
      const row = seriesMap[sidRaw];
      if (!row || typeof row !== "object") return;
      const works = Array.isArray(row.works) ? row.works.map(normalizeText).filter(Boolean) : [];
      const rankMap = {};
      const rankWidth = Math.max(3, String(works.length).length);
      for (let idx = 0; idx < works.length; idx += 1) {
        const wid = works[idx];
        const rank = String(idx + 1).padStart(rankWidth, "0");
        rankMap[wid] = `${rank}-${wid}`;
      }
      out[sid] = {
        label: normalizeText(row.title) || sid,
        sort_fields: normalizeText(row.sort_fields),
        primary_sort: seriesPrimarySortFromSortFields(row.sort_fields),
        custom_sort: isCustomSeriesSort(row.sort_fields),
        rank_map: rankMap
      };
    });
    return out;
  }

  function rowMatchesSeries(row) {
    if (!hasSeriesFilter) return true;
    const rowSeriesId = slugSortKey(row.getAttribute("data-series-id"));
    return rowSeriesId === seriesFilter;
  }

  function updateCount(visibleRows) {
    if (hasSeriesFilter) {
      const workCount = visibleRows.length;
      const workWord = workCount === 1 ? "work" : "works";
      let seriesLabel = "";
      if (visibleRows.length) {
        seriesLabel = normalizeText(visibleRows[0].getAttribute("data-series-label"));
      }
      countEl.textContent = "";
      countEl.appendChild(document.createTextNode(`${workCount} ${workWord}`));
      if (seriesLabel) {
        countEl.appendChild(document.createTextNode(" in "));
        const seriesLink = document.createElement("a");
        seriesLink.className = "worksList__countSeriesLink";
        seriesLink.href = `${seriesBaseHref}${encodeURIComponent(seriesFilter)}/`;
        seriesLink.textContent = seriesLabel;
        countEl.appendChild(seriesLink);
      }
      if (backNav && backLink) {
        backNav.hidden = false;
        backLink.setAttribute("href", `${seriesBaseHref}${encodeURIComponent(seriesFilter)}/`);
        backLink.textContent = seriesLabel ? `← ${seriesLabel}` : "← series";
      }
      return;
    }

    const workWordAll = totalWorksAll === 1 ? "work" : "works";
    countEl.textContent = `${totalWorksAll} ${workWordAll} in ${totalSeriesAll} series`;
    if (backNav) backNav.hidden = true;
  }

  function compareValues(a, b, key) {
    if (key === "year") {
      const av = Number(a.getAttribute("data-year") || "0");
      const bv = Number(b.getAttribute("data-year") || "0");
      return av - bv;
    }
    if (key === "seriessort") {
      const aSeriesSort = normalizeText(a.getAttribute("data-series-sort"));
      const bSeriesSort = normalizeText(b.getAttribute("data-series-sort"));
      return collator.compare(aSeriesSort, bSeriesSort);
    }
    const as = normalizeText(a.getAttribute(`data-${key}`));
    const bs = normalizeText(b.getAttribute(`data-${key}`));
    return collator.compare(as, bs);
  }

  function updateRowLinks(key, dir) {
    const rows = Array.prototype.slice.call(list.querySelectorAll(".worksList__item"));
    rows.forEach((row) => {
      const titleLink = row.querySelector(".worksList__title");
      if (!titleLink) return;
      let href = String(titleLink.getAttribute("href") || "");
      const hashIndex = href.indexOf("#");
      let hash = "";
      if (hashIndex >= 0) {
        hash = href.slice(hashIndex);
        href = href.slice(0, hashIndex);
      }
      const qIndex = href.indexOf("?");
      const base = qIndex >= 0 ? href.slice(0, qIndex) : href;
      const query = new URLSearchParams(qIndex >= 0 ? href.slice(qIndex + 1) : "");
      query.set("from", "works_curator_index");
      query.set("return_sort", key);
      query.set("return_dir", dir);
      if (hasSeriesFilter) {
        query.set("return_series", seriesFilter);
      } else {
        query.delete("return_series");
      }
      titleLink.setAttribute("href", `${base}?${query.toString()}${hash}`);
    });
  }

  function applySort(key, dir) {
    const rows = Array.prototype.slice.call(list.querySelectorAll(".worksList__item"));
    const visibleRows = rows.filter(rowMatchesSeries);
    if (hasSeriesFilter) list.innerHTML = "";
    visibleRows.sort((a, b) => {
      const primary = compareValues(a, b, key);
      if (primary !== 0) return dir === "asc" ? primary : -primary;

      const tieTitle = compareValues(a, b, "title");
      if (tieTitle !== 0) return tieTitle;
      const tieCat = compareValues(a, b, "cat");
      if (tieCat !== 0) return tieCat;
      const tieSeries = compareValues(a, b, "series");
      if (tieSeries !== 0) return tieSeries;
      return compareValues(a, b, "storage");
    });
    visibleRows.forEach((row) => {
      list.appendChild(row);
    });
    updateCount(visibleRows);
    updateRowLinks(key, dir);
  }

  function updateHeaderState(key, dir) {
    buttons.forEach((btn) => {
      const btnKey = btn.getAttribute("data-sort-key");
      const icon = btn.querySelector(".worksList__sortIcon");
      const active = btnKey === key;
      if (active) {
        btn.dataset.state = UI_STATE.active;
      } else {
        delete btn.dataset.state;
      }
      if (!icon) return;
      icon.textContent = active ? (dir === "asc" ? "▲" : "▼") : "";
    });
  }

  function visualSortKeyFor(rows, key) {
    if (key !== "seriessort") return key;
    if (!hasSeriesFilter) return "cat";

    const sameAsCat = rows.length > 0 && rows.every((row) => {
      const a = normalizeText(row.getAttribute("data-series-sort"));
      const b = normalizeText(row.getAttribute("data-cat"));
      return a === b;
    });
    if (sameAsCat) return "cat";

    for (let idx = 0; idx < rows.length; idx += 1) {
      const hint = slugSortKey(rows[idx].getAttribute("data-series-primary-sort"));
      if (validKeys[hint] && hint !== "seriessort") return hint;
    }
    return "cat";
  }

  function persist(key, dir) {
    const next = new URLSearchParams(window.location.search);
    next.set("sort", key);
    next.set("dir", dir);
    const query = next.toString();
    let path = String(window.location.pathname || "/");
    path = `/${path.replace(/^\/+/, "").replace(/\/{2,}/g, "/")}`;
    const nextUrl = path + (query ? `?${query}` : "") + window.location.hash;
    window.history.replaceState({}, "", nextUrl);
  }

  function makeWorkRow(work, seriesMetaById) {
    const wid = normalizeText(work && work.work_id);
    if (!wid) return null;
    const sid = slugSortKey(work && work.series_id);
    const sm = sid ? seriesMetaById[sid] || null : null;
    const seriesLabel = sm && sm.label ? sm.label : sid || "";
    const seriesPrimarySort = sm && sm.primary_sort ? sm.primary_sort : "";
    let yearVal = Number(work && work.year);
    if (!Number.isFinite(yearVal)) yearVal = 0;
    const yearDisplay = normalizeText(work && work.year_display) || normalizeText(work && work.year);
    const titleRaw = normalizeText(work && work.title) || wid;
    const titleSortRaw = normalizeText(work && work.title_sort);
    const titleSort = (titleSortRaw || numericAwareSortKey(titleRaw)).toLowerCase();
    let storageRaw = normalizeText(work && work.storage);
    if (!storageRaw) storageRaw = normalizeText(work && work.storage_location);
    let seriesSort = wid;
    if (sm && sm.custom_sort && sm.rank_map && sm.rank_map[wid]) {
      seriesSort = sm.rank_map[wid];
    }

    const li = document.createElement("li");
    li.className = "worksList__item";
    li.setAttribute("data-cat", wid.toLowerCase());
    li.setAttribute("data-series-sort", seriesSort.toLowerCase());
    li.setAttribute("data-series-primary-sort", seriesPrimarySort.toLowerCase());
    li.setAttribute("data-year", String(yearVal));
    li.setAttribute("data-title", titleSort);
    li.setAttribute("data-series", seriesLabel.toLowerCase());
    li.setAttribute("data-storage", storageRaw.toLowerCase());
    li.setAttribute("data-series-id", sid);
    li.setAttribute("data-series-label", seriesLabel);

    const workHref = `${baseurl}/works/${encodeURIComponent(wid)}/?from=works_curator_index`;

    const catA = document.createElement("a");
    catA.className = "worksList__cat";
    catA.href = workHref;
    catA.textContent = wid;
    li.appendChild(catA);

    const yearSpan = document.createElement("span");
    yearSpan.className = "worksList__year";
    yearSpan.textContent = yearDisplay;
    li.appendChild(yearSpan);

    const titleA = document.createElement("a");
    titleA.className = "worksList__title";
    titleA.href = workHref;
    titleA.textContent = titleRaw;
    li.appendChild(titleA);

    const seriesA = document.createElement("a");
    seriesA.className = "worksList__series";
    seriesA.href = sid ? `${seriesBaseHref}${encodeURIComponent(sid)}/` : seriesBaseHref;
    seriesA.textContent = seriesLabel;
    li.appendChild(seriesA);

    const storageSpan = document.createElement("span");
    storageSpan.className = "worksList__storage";
    storageSpan.textContent = storageRaw || "—";
    li.appendChild(storageSpan);

    return li;
  }

  function renderFromJson(worksPayload, seriesPayload) {
    const worksMap = worksPayload && worksPayload.works && typeof worksPayload.works === "object" ? worksPayload.works : {};
    const seriesMap = seriesPayload && seriesPayload.series && typeof seriesPayload.series === "object" ? seriesPayload.series : {};
    const seriesMetaById = buildSeriesMeta(seriesMap);
    const rows = [];
    const seriesIdSet = {};

    Object.keys(worksMap).forEach((wid) => {
      const row = makeWorkRow(worksMap[wid], seriesMetaById);
      if (!row) return;
      rows.push(row);
      const sid = slugSortKey(row.getAttribute("data-series-id"));
      if (sid) seriesIdSet[sid] = true;
    });

    totalWorksAll = rows.length;
    totalSeriesAll = Object.keys(seriesIdSet).length;
    list.innerHTML = "";
    if (!rows.length) return false;

    const frag = document.createDocumentFragment();
    rows.forEach((row) => {
      frag.appendChild(row);
    });
    list.appendChild(frag);
    return true;
  }

  function initSortUi() {
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = slugSortKey(btn.getAttribute("data-sort-key"));
        if (!validKeys[key]) return;
        if (key === visualSortKey) {
          sortDir = sortDir === "asc" ? "desc" : "asc";
        } else {
          sortKey = key;
          sortDir = "asc";
        }
        sortKey = key;
        applySort(sortKey, sortDir);
        const rows = Array.prototype.slice.call(list.querySelectorAll(".worksList__item")).filter(rowMatchesSeries);
        visualSortKey = visualSortKeyFor(rows, sortKey);
        updateHeaderState(visualSortKey, sortDir);
        persist(sortKey, sortDir);
      });
    });

    applySort(sortKey, sortDir);
    const initialRows = Array.prototype.slice.call(list.querySelectorAll(".worksList__item")).filter(rowMatchesSeries);
    visualSortKey = visualSortKeyFor(initialRows, sortKey);
    updateHeaderState(visualSortKey, sortDir);
    persist(sortKey, sortDir);
  }

  Promise.all([
    fetchJson(worksIndexUrl),
    fetchJson(seriesIndexUrl).catch(() => null)
  ])
    .then((parts) => {
      const hasRows = renderFromJson(parts[0], parts[1]);
      if (!hasRows) {
        worksListRoot.hidden = true;
        emptyEl.hidden = false;
        return;
      }
      worksListRoot.hidden = false;
      emptyEl.hidden = true;
      try {
        initSortUi();
      } catch (err) {
        console.error("works_curator: initSortUi failed", err);
      }
    })
    .catch((err) => {
      console.error("works_curator: render failed", err);
      worksListRoot.hidden = true;
      emptyEl.hidden = false;
    });
}
