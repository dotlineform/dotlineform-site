import {
  fetchJson
} from "./studio-data.js";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSeriesTagEditorPage);
} else {
  initSeriesTagEditorPage();
}

function initSeriesTagEditorPage() {
  const root = document.getElementById("seriesTagEditorRoot");
  const emptyEl = document.getElementById("seriesTagEditorEmpty");
  const mount = document.getElementById("tag-studio");
  if (!root || !emptyEl || !mount) return;

  const titleEl = document.getElementById("seriesTagEditorTitle");
  const catEl = document.getElementById("seriesTagEditorCat");
  const yearEl = document.getElementById("seriesTagEditorYear");
  const yearDisplayEl = document.getElementById("seriesTagEditorYearDisplay");
  const sortFieldsEl = document.getElementById("seriesTagEditorSortFields");
  const primaryWorkEl = document.getElementById("seriesTagEditorPrimaryWork");
  const foldersEl = document.getElementById("seriesTagEditorFolders");
  const notesEl = document.getElementById("seriesTagEditorNotes");
  const mediaFigureEl = document.getElementById("seriesTagEditorMedia");
  const mediaLinkEl = document.getElementById("seriesTagEditorMediaLink");
  const mediaImgEl = document.getElementById("seriesTagEditorMediaImg");
  const baseurl = String(root.dataset.baseurl || "");
  const mediaBase = String(root.dataset.mediaBase || "");
  const mediaPrefix = root.dataset.mediaPrefix === undefined
    ? "/assets"
    : String(root.dataset.mediaPrefix);
  const seriesIndexUrl = String(root.dataset.seriesIndexUrl || "");
  const tagStudioModuleUrl = String(root.dataset.tagStudioModuleUrl || "");
  const params = new URLSearchParams(window.location.search);
  const seriesIdQuery = String(params.get("series") || "").trim().toLowerCase();
  let defaultMediaWorkId = "";
  let defaultMediaTitle = "";
  let currentMediaWorkId = "";

  function showError(message) {
    root.hidden = true;
    emptyEl.hidden = false;
    emptyEl.textContent = message;
  }

  function textOrDash(value) {
    const text = String(value == null ? "" : value).trim();
    return text || "—";
  }

  function setLinkOrDash(el, href, label) {
    if (!el) return;
    const text = String(label == null ? "" : label).trim();
    if (!text) {
      el.textContent = "—";
      return;
    }
    el.textContent = "";
    const link = document.createElement("a");
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = text;
    el.appendChild(link);
  }

  function normalizeSeriesMap(seriesMap) {
    const map = {};
    if (!seriesMap || typeof seriesMap !== "object") return map;
    Object.keys(seriesMap).forEach((key) => {
      const id = String(key || "").trim().toLowerCase();
      if (!id) return;
      map[id] = seriesMap[key];
    });
    return map;
  }

  function applyBaseurl(url) {
    if (/^[a-z]+:\/\//i.test(url)) return url;
    if (url.charAt(0) === "/") return baseurl + url;
    return url;
  }

  function worksImgBasePath() {
    const base = String(mediaBase || "").replace(/\/+$/, "");
    const prefix = String(mediaPrefix || "").replace(/\/+$/, "");
    if (base) return `${base}${prefix}/works/img/`;
    return applyBaseurl(`${prefix || ""}/works/img/`).replace(/\/{2,}/g, "/");
  }

  async function fetchWorkRecord(primaryWorkId) {
    const url = `${baseurl}/assets/works/index/${encodeURIComponent(primaryWorkId)}.json`;
    try {
      const payload = await fetchJson(url);
      return payload && payload.work && typeof payload.work === "object" ? payload.work : null;
    } catch (error) {
      return null;
    }
  }

  async function renderPrimaryMedia(primaryWorkId, displayTitle) {
    if (!mediaFigureEl || !mediaLinkEl || !mediaImgEl) return;
    if (!primaryWorkId) {
      mediaFigureEl.hidden = true;
      return;
    }

    const imgBase = worksImgBasePath();
    const src800 = `${imgBase}${primaryWorkId}-primary-800.webp`;
    const src1200 = `${imgBase}${primaryWorkId}-primary-1200.webp`;
    const src1600 = `${imgBase}${primaryWorkId}-primary-1600.webp`;
    const src2400 = `${imgBase}${primaryWorkId}-primary-2400.webp`;
    const work = await fetchWorkRecord(primaryWorkId);
    let widthCm = Number(work && work.width_cm);
    let heightCm = Number(work && work.height_cm);
    if (!Number.isFinite(widthCm) || widthCm <= 0) widthCm = 4;
    if (!Number.isFinite(heightCm) || heightCm <= 0) heightCm = 3;
    const has2400 = Boolean(work && work.has_primary_2400 === true);
    const fullSrc = has2400 ? src2400 : src1600;
    let srcset = `${src800} 800w, ${src1200} 1200w, ${src1600} 1600w`;
    if (has2400) srcset += `, ${src2400} 2400w`;

    mediaLinkEl.href = fullSrc;
    mediaLinkEl.style.setProperty("--work-ar", `${widthCm} / ${heightCm}`);
    mediaImgEl.src = src1600;
    mediaImgEl.setAttribute("srcset", srcset);
    mediaImgEl.alt = displayTitle;
    mediaFigureEl.hidden = false;
  }

  function syncHeaderMediaForWork(workId) {
    const nextWorkId = String(workId || "").trim();
    const targetWorkId = nextWorkId || defaultMediaWorkId;
    const targetTitle = defaultMediaTitle || titleEl.textContent || "Series Tag Editor";
    if (!targetWorkId || currentMediaWorkId === targetWorkId) return;
    currentMediaWorkId = targetWorkId;
    renderPrimaryMedia(targetWorkId, targetTitle).catch((err) => {
      console.error("series_tag_editor: failed to render selected media", err);
      if (mediaFigureEl) mediaFigureEl.hidden = true;
    });
  }

  if (!seriesIdQuery) {
    showError("Missing series id. Open this page with ?series=<series_id>.");
    return;
  }

  fetchJson(seriesIndexUrl)
    .then((payload) => {
      const rawSeriesMap = payload && payload.series && typeof payload.series === "object" ? payload.series : {};
      const seriesMap = normalizeSeriesMap(rawSeriesMap);
      const row = seriesMap[seriesIdQuery];
      if (!row || typeof row !== "object") {
        showError(`Unknown series id: ${seriesIdQuery}`);
        return;
      }

      const seriesTitle = textOrDash(row.title);
      titleEl.textContent = seriesTitle;
      setLinkOrDash(catEl, `${baseurl}/series/${encodeURIComponent(seriesIdQuery)}/`, seriesIdQuery);
      yearEl.textContent = textOrDash(row.year);
      yearDisplayEl.textContent = textOrDash(row.year_display);
      sortFieldsEl.textContent = textOrDash(row.sort_fields);

      const primaryWorkId = String(row.primary_work_id || "").trim();
      if (primaryWorkId) {
        setLinkOrDash(primaryWorkEl, `${baseurl}/works/${encodeURIComponent(primaryWorkId)}/`, primaryWorkId);
      } else {
        primaryWorkEl.textContent = "—";
      }

      const folders = Array.isArray(row.project_folders) ? row.project_folders.filter(Boolean) : [];
      foldersEl.textContent = folders.length ? folders.join(", ") : textOrDash(row.project_folders);
      notesEl.textContent = textOrDash(row.notes);
      defaultMediaWorkId = primaryWorkId;
      defaultMediaTitle = seriesTitle;
      currentMediaWorkId = "";
      renderPrimaryMedia(primaryWorkId, seriesTitle)
        .then(() => {
          currentMediaWorkId = primaryWorkId;
        })
        .catch((err) => {
          console.error("series_tag_editor: failed to render primary media", err);
          if (mediaFigureEl) mediaFigureEl.hidden = true;
        });

      window.addEventListener("series-tag-editor:selected-work-change", (event) => {
        const detail = event && event.detail && typeof event.detail === "object" ? event.detail : {};
        const detailSeriesId = String(detail.seriesId || "").trim().toLowerCase();
        if (detailSeriesId !== seriesIdQuery) return;
        syncHeaderMediaForWork(detail.workId);
      });

      mount.setAttribute("data-series-id", seriesIdQuery);
      root.hidden = false;
      emptyEl.hidden = true;
      import(tagStudioModuleUrl).catch((err) => {
        console.error("series_tag_editor: failed to load tag-studio.js", err);
        showError("Failed to load tag editor module.");
      });
    })
    .catch((err) => {
      console.error("series_tag_editor: failed to load series index", err);
      showError("Failed to load series metadata.");
    });
}
