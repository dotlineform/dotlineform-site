import {
  getStudioDataPath,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import {
  THUMBNAIL_QUALITY_ENDPOINTS,
  postJson,
  probeThumbnailQualityCatalogueHealth
} from "./studio-transport.js";
import {
  initializeStudioRouteState
} from "./studio-route-state.js";
import {
  applyOperationalRunButtonState,
  collectOperationalRouteElements,
  markOperationalRouteReady,
  syncOperationalRouteBusyState
} from "./studio-operational-route.js";

const UI_TEXT_GROUP = "thumbnail_quality";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setText(node, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
}

function setStatus(node, state, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
  if (state) {
    node.setAttribute("data-state", state);
  } else {
    node.removeAttribute("data-state");
  }
}

function pageText(config, key, fallback, tokens = null) {
  return getStudioText(config, `${UI_TEXT_GROUP}.${key}`, fallback, tokens);
}

function routeDetail(state, mode = "preview") {
  return {
    route: "thumbnail-quality",
    mode: () => mode,
    serviceAvailable: (state) => state.catalogueServerAvailable,
    isBusy: (state) => state.isBusy,
    recordLoaded: (state) => Boolean(state.payload && Array.isArray(state.payload.rows) && state.payload.rows.length)
  };
}

function markBusy(state, busy, mode) {
  state.isBusy = Boolean(busy);
  syncOperationalRouteBusyState(state, routeDetail(state, mode));
}

function markReady(state, ready, mode) {
  markOperationalRouteReady(state, ready, routeDetail(state, mode));
}

function syncRefreshButtonState(state) {
  applyOperationalRunButtonState(state.refreshButton, state, {
    serviceAvailable: (routeState) => routeState.catalogueServerAvailable,
    isBusy: (routeState) => routeState.isBusy
  });
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function dataUrl(config) {
  return getStudioDataPath(config, "thumbnail_quality_preview") || "/studio/data/generated/thumbnail-quality/thumbnail-quality-preview.json";
}

function renderSettingCard(label, settings) {
  const args = Array.isArray(settings?.ffmpeg_args) ? settings.ffmpeg_args.join(" ") : "";
  const scale = normalizeText(settings?.scale_filter);
  return `
    <article class="thumbnailQualitySettings__item">
      <h3>${escapeHtml(label)}</h3>
      <p>${escapeHtml(scale)}</p>
      <code>${escapeHtml(args)}</code>
    </article>
  `;
}

function renderSettings(state) {
  const payload = state.payload || {};
  const baseline = payload.baseline || {};
  const variants = Array.isArray(payload.variants) ? payload.variants : [];
  const cards = [
    renderSettingCard(normalizeText(baseline.label) || pageText(state.config, "current_label", "current pipeline"), baseline.settings || {})
  ];
  variants.forEach((variant) => {
    cards.push(renderSettingCard(normalizeText(variant.label), variant.settings || {}));
  });
  state.settingsList.innerHTML = cards.join("");
}

function renderImageTile(item, roleLabel) {
  const url = normalizeText(item?.url);
  const label = normalizeText(item?.label) || roleLabel;
  const sizeLabel = normalizeText(item?.size_label);
  const byteCount = Number(item?.size_bytes);
  const title = Number.isFinite(byteCount) ? `${label}: ${sizeLabel}` : label;
  return `
    <figure class="thumbnailQualityTile">
      <div class="thumbnailQualityTile__imageWrap">
        ${url ? `<img src="${escapeHtml(url)}?v=${encodeURIComponent(normalizeText(item?.size_bytes))}" alt="${escapeHtml(title)}" loading="lazy" decoding="async">` : ""}
      </div>
      <figcaption>
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(sizeLabel || "--")}</strong>
      </figcaption>
    </figure>
  `;
}

function variantById(row, variantId) {
  const variants = Array.isArray(row?.variants) ? row.variants : [];
  return variants.find((variant) => normalizeText(variant?.variant_id) === variantId) || null;
}

function renderSeriesPreview(state) {
  const rows = Array.isArray(state.payload?.rows) ? state.payload.rows : [];
  const items = rows.map((row) => {
    const variant = variantById(row, "q62-96");
    const url = normalizeText(variant?.url);
    if (!url) return "";
    const sourceName = normalizeText(row?.source_name) || pageText(state.config, "source_label", "source");
    const sizeLabel = normalizeText(variant?.size_label);
    const label = sizeLabel ? `${sourceName}, q62 96, ${sizeLabel}` : `${sourceName}, q62 96`;
    return `
      <span class="seriesGrid__item thumbnailQualitySeriesPreview__item">
        <img class="seriesGrid__img" src="${escapeHtml(url)}?v=${encodeURIComponent(normalizeText(variant?.size_bytes))}" alt="${escapeHtml(label)}" loading="lazy" decoding="async">
      </span>
    `;
  }).filter(Boolean);
  state.seriesGrid.innerHTML = items.join("");
}

function renderRows(state) {
  const payload = state.payload || {};
  const rows = Array.isArray(payload.rows) ? payload.rows : [];
  if (!rows.length) {
    state.rowsNode.innerHTML = "";
    setText(state.emptyNode, pageText(state.config, "empty_state", "No source images found."));
    state.emptyNode.hidden = false;
    return;
  }

  state.emptyNode.hidden = true;
  state.rowsNode.innerHTML = rows.map((row) => {
    const variants = Array.isArray(row.variants) ? row.variants : [];
    const tiles = [
      renderImageTile(row.baseline, pageText(state.config, "current_label", "current")),
      ...variants.map((variant) => renderImageTile(variant, normalizeText(variant.label)))
    ];
    return `
      <article class="tagStudio__panel thumbnailQualityRow">
        <header class="thumbnailQualityRow__header">
          <h3>${escapeHtml(normalizeText(row.source_name) || pageText(state.config, "source_label", "source"))}</h3>
          <p>${escapeHtml(normalizeText(row.source_display))}</p>
        </header>
        <div class="thumbnailQualityRow__tiles">${tiles.join("")}</div>
      </article>
    `;
  }).join("");
}

function renderPayload(state) {
  const payload = state.payload || {};
  renderSettings(state);
  renderSeriesPreview(state);
  renderRows(state);
  const count = Number(payload.source_count || 0);
  setStatus(
    state.statusNode,
    "",
    pageText(state.config, "loaded_status", "{count} source images. Generated {generated_at}.", {
      count: String(count),
      generated_at: normalizeText(payload.generated_at_utc) || "--"
    })
  );
}

async function loadPayload(state) {
  state.payload = await fetchJson(dataUrl(state.config));
  renderPayload(state);
}

async function refreshPreview(state) {
  if (!state.catalogueServerAvailable) {
    setStatus(state.resultNode, "error", pageText(state.config, "server_unavailable", "Start the catalogue service to refresh."));
    return;
  }
  markBusy(state, true, "refreshing");
  syncRefreshButtonState(state);
  setStatus(state.resultNode, "", pageText(state.config, "refreshing", "Refreshing thumbnail previews..."));
  try {
    state.payload = await postJson(THUMBNAIL_QUALITY_ENDPOINTS.refresh, {});
    renderPayload(state);
    setStatus(state.resultNode, "success", pageText(state.config, "refresh_success", "Thumbnail previews refreshed."));
  } catch (error) {
    console.warn("thumbnail_quality: refresh failed", error);
    setStatus(state.resultNode, "error", pageText(state.config, "refresh_error", "Refresh failed: {error}", {
      error: normalizeText(error && error.message) || "unknown error"
    }));
  } finally {
    markBusy(state, false, "preview");
    syncRefreshButtonState(state);
  }
}

async function initThumbnailQualityPage() {
  const root = document.getElementById("thumbnailQualityRoot");
  const loadingNode = document.getElementById("thumbnailQualityLoading");
  const emptyNode = document.getElementById("thumbnailQualityEmpty");
  const refreshButton = document.getElementById("thumbnailQualityRefreshButton");
  const rowsNode = document.getElementById("thumbnailQualityRows");
  const seriesGrid = document.getElementById("thumbnailQualitySeriesGrid");
  const settingsList = document.getElementById("thumbnailQualitySettingsList");
  const statusNode = document.getElementById("thumbnailQualityStatus");
  const resultNode = document.getElementById("thumbnailQualityResult");
  const required = collectOperationalRouteElements({
    root,
    loadingNode,
    emptyNode,
    refreshButton,
    rowsNode,
    seriesGrid,
    settingsList,
    statusNode,
    resultNode
  });
  if (!required.ok) return;

  const state = {
    root,
    loadingNode,
    emptyNode,
    refreshButton,
    rowsNode,
    seriesGrid,
    settingsList,
    statusNode,
    resultNode,
    config: null,
    payload: null,
    catalogueServerAvailable: false,
    isBusy: false
  };

  initializeStudioRouteState(root, { route: "thumbnail-quality", mode: "loading" });
  markBusy(state, true, "loading");

  try {
    const [config, catalogueServerAvailable] = await Promise.all([
      loadStudioConfigWithText(UI_TEXT_GROUP),
      probeThumbnailQualityCatalogueHealth().catch(() => false)
    ]);
    state.config = config;
    state.catalogueServerAvailable = catalogueServerAvailable;
    syncRefreshButtonState(state);

    setText(document.getElementById("thumbnailQualityPageHeading"), pageText(config, "heading", "thumbnail quality"));
    setText(document.getElementById("thumbnailQualitySettingsHeading"), pageText(config, "settings_heading", "settings"));
    setText(document.getElementById("thumbnailQualitySeriesHeading"), pageText(config, "series_heading", "series gallery comparison"));
    setText(document.getElementById("thumbnailQualitySeriesContext"), pageText(config, "series_context", "q62 96 thumbnails shown with the live series gallery layout."));
    setText(document.getElementById("thumbnailQualityContext"), pageText(config, "context", "Compare current and lower-quality thumbnail encodes from source images."));
    setText(refreshButton, pageText(config, "refresh_button", "Refresh"));
    setText(loadingNode, pageText(config, "loading", "loading thumbnail quality preview..."));

    refreshButton.addEventListener("click", () => {
      refreshPreview(state).catch((error) => console.warn("thumbnail_quality: unexpected refresh failure", error));
    });

    await loadPayload(state);
    loadingNode.hidden = true;
    root.hidden = false;
    markBusy(state, false, "preview");
    syncRefreshButtonState(state);
    markReady(state, true, "preview");
  } catch (error) {
    console.warn("thumbnail_quality: init failed", error);
    loadingNode.hidden = true;
    setText(emptyNode, pageText(state.config, "load_error", "Thumbnail quality preview data is not available."));
    emptyNode.hidden = false;
    root.hidden = false;
    markBusy(state, false, "error");
    markReady(state, true, "error");
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initThumbnailQualityPage);
} else {
  initThumbnailQualityPage();
}
