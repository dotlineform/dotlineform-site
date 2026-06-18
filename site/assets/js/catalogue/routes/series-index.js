import { createThumbnailGridList } from '../components/thumbnail-grid-list.js';
import {
  catalogueIndexUrl,
  parseRouteState,
  seriesIndexUrl,
  trimBaseurl,
  worksIndexUrl,
  workUrl
} from '../shared/catalogue-urls.js';
import { fetchJson } from '../shared/fetch-json.js';
import { readStoredItem, writeStoredItem } from '../shared/local-storage.js';
import { lowerText, normalizePositiveSizes, text } from '../shared/text.js';
import { thumbnailImageData } from '../shared/thumbnails.js';

var PAGE_SIZE = 80;

var DEFAULT_SORT = {
  key: 'year',
  directions: {
    year: 'desc',
    title: 'asc'
  }
};

var STORAGE_KEYS = {
  view: 'dlf.catalogIndex.works.view',
  sort: 'dlf.catalogIndex.works.sort',
  page: 'dlf.catalogIndex.works.page',
  legacyView: 'dlf.seriesIndex.view',
  legacySort: 'dlf.seriesIndex.sort',
  legacyPage: 'dlf.seriesIndex.page'
};

var UI_TEXT_DEFAULTS = {
  sort_year_label: 'year',
  sort_title_label: 'title',
  sort_direction_asc: '↑',
  sort_direction_desc: '↓',
  pager_prev_label: 'Previous page',
  pager_next_label: 'Next page',
  empty_works: 'no works yet'
};

function normalizeView(value) {
  return lowerText(value) === 'list' ? 'list' : 'grid';
}

function normalizeDirection(value, fallback) {
  var normalized = lowerText(value);
  if (normalized === 'asc' || normalized === 'desc') return normalized;
  return fallback === 'desc' ? 'desc' : 'asc';
}

function normalizeSortKey(value) {
  return lowerText(value) === 'title' ? 'title' : 'year';
}

function normalizePage(value) {
  var page = Number(value);
  if (!Number.isFinite(page) || page < 1) return 1;
  return Math.floor(page);
}

function sanitizeSortState(raw) {
  var directions = raw && raw.directions && typeof raw.directions === 'object' ? raw.directions : {};
  return {
    key: normalizeSortKey(raw && raw.key),
    directions: {
      year: normalizeDirection(directions.year, DEFAULT_SORT.directions.year),
      title: normalizeDirection(directions.title, DEFAULT_SORT.directions.title)
    }
  };
}

function readStoredView() {
  return normalizeView(readStoredItem(STORAGE_KEYS.view, STORAGE_KEYS.legacyView));
}

function persistView(view) {
  writeStoredItem(STORAGE_KEYS.view, normalizeView(view));
}

function readStoredSort() {
  var raw = readStoredItem(STORAGE_KEYS.sort, STORAGE_KEYS.legacySort);
  if (raw == null) return sanitizeSortState(DEFAULT_SORT);
  try {
    return sanitizeSortState(JSON.parse(raw));
  } catch (err) {
    return sanitizeSortState(DEFAULT_SORT);
  }
}

function persistSort(sortState) {
  writeStoredItem(STORAGE_KEYS.sort, JSON.stringify(sanitizeSortState(sortState)));
}

function readStoredPage() {
  return normalizePage(readStoredItem(STORAGE_KEYS.page, STORAGE_KEYS.legacyPage));
}

function persistPage(page) {
  writeStoredItem(STORAGE_KEYS.page, String(normalizePage(page)));
}

function copyUiText(source) {
  return {
    sort_year_label: text((source && source.sort_year_label) || UI_TEXT_DEFAULTS.sort_year_label),
    sort_title_label: text((source && source.sort_title_label) || UI_TEXT_DEFAULTS.sort_title_label),
    sort_direction_asc: text((source && source.sort_direction_asc) || UI_TEXT_DEFAULTS.sort_direction_asc),
    sort_direction_desc: text((source && source.sort_direction_desc) || UI_TEXT_DEFAULTS.sort_direction_desc),
    pager_prev_label: text((source && source.pager_prev_label) || UI_TEXT_DEFAULTS.pager_prev_label),
    pager_next_label: text((source && source.pager_next_label) || UI_TEXT_DEFAULTS.pager_next_label),
    empty_works: text((source && source.empty_works) || UI_TEXT_DEFAULTS.empty_works)
  };
}

function numericAwareSortKey(value) {
  return text(value).replace(/\d+/g, function (match) {
    return match.padStart(3, '0');
  });
}

function parseYearNumber(rawDate, displayText) {
  var dateText = text(rawDate);
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateText)) return Number(dateText.slice(0, 4));
  var display = text(displayText);
  var match = display.match(/(\d{4})/);
  return match ? Number(match[1]) : null;
}

function yearDisplayText(item) {
  return text(item && item.year_display);
}

function createCatalogueSorter() {
  var titleCollator = (window.Intl && typeof window.Intl.Collator === 'function')
    ? new window.Intl.Collator(undefined, { numeric: true, sensitivity: 'base' })
    : null;

  function compareText(a, b) {
    var aa = String(a || '');
    var bb = String(b || '');
    if (titleCollator) return titleCollator.compare(aa, bb);
    if (aa < bb) return -1;
    if (aa > bb) return 1;
    return 0;
  }

  function titleValue(item) {
    return numericAwareSortKey(item && (item.title || item.id));
  }

  function titleCompare(a, b) {
    var cmp = compareText(titleValue(a), titleValue(b));
    if (cmp !== 0) return cmp;
    return compareText(a && a.id, b && b.id);
  }

  function yearSortNumber(item) {
    return Number.isFinite(item && item.year_sort) ? item.year_sort : null;
  }

  function yearCompare(a, b) {
    var ay = yearSortNumber(a);
    var by = yearSortNumber(b);
    if (ay !== by) {
      if (ay == null) return 1;
      if (by == null) return -1;
      return ay - by;
    }
    var displayCmp = compareText(yearDisplayText(a), yearDisplayText(b));
    if (displayCmp !== 0) return displayCmp;
    return titleCompare(a, b);
  }

  function compareCatalogueItems(a, b, sortState) {
    var activeKey = normalizeSortKey(sortState && sortState.key);
    var direction = sanitizeSortState(sortState).directions[activeKey];
    var primary = activeKey === 'title' ? titleCompare(a, b) : yearCompare(a, b);
    if (primary !== 0) return direction === 'desc' ? -primary : primary;

    if (activeKey === 'title') {
      var yearFallback = yearCompare(a, b);
      if (yearFallback !== 0) return yearFallback;
    } else {
      var titleFallback = titleCompare(a, b);
      if (titleFallback !== 0) return titleFallback;
    }
    return compareText(a && a.id, b && b.id);
  }

  return function getSortedItems(items, sortState) {
    return items.slice().sort(function (a, b) {
      return compareCatalogueItems(a, b, sortState);
    });
  };
}

function loadThumbSizes(root) {
  var raw = [];
  try {
    raw = JSON.parse(root.getAttribute('data-thumb-sizes') || '[]');
  } catch (err) {
    raw = [];
  }
  return normalizePositiveSizes(raw, [96, 192]);
}

function createThumbProjector(root) {
  var thumbWorksBase = text(root.getAttribute('data-thumb-works-base'));
  var thumbSizes = loadThumbSizes(root);
  var primaryThumbSize = thumbSizes[0];
  var thumbSrcsetSizes = thumbSizes.slice(0, 2);
  var thumbSuffix = text(root.getAttribute('data-thumb-suffix')) || 'thumb';
  var assetFormat = text(root.getAttribute('data-asset-format')) || 'webp';

  return function itemThumbnail(item) {
    return thumbnailImageData({
      base: thumbWorksBase,
      id: item && item.thumb_id,
      suffix: thumbSuffix,
      size: primaryThumbSize,
      srcsetSizes: thumbSrcsetSizes,
      format: assetFormat,
      alt: text((item && item.title) || (item && item.id))
    });
  };
}

function initSeriesIndexRoute() {
  var root = document.getElementById('seriesIndexRoot');
  var list = document.getElementById('seriesIndexList');
  var thumbGrid = document.getElementById('seriesIndexThumbGrid');
  var pager = document.getElementById('seriesIndexPager');
  var pagerStatus = document.getElementById('seriesIndexPagerStatus');
  var prevBtn = document.getElementById('seriesIndexPrev');
  var nextBtn = document.getElementById('seriesIndexNext');
  var empty = document.getElementById('seriesIndexEmpty');
  if (!root || !list || !thumbGrid || !pager || !pagerStatus || !prevBtn || !nextBtn || !empty) return;

  var viewButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="catalog-index-view-btn"]'));
  var sortButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="catalog-index-sort-btn"]'));
  if (!viewButtons.length || !sortButtons.length) return;

  var baseurl = trimBaseurl(root.getAttribute('data-baseurl'));
  var routeState = parseRouteState(window.location);
  var selectedSeriesId = lowerText(routeState.series);
  var state = {
    view: readStoredView(),
    sort: readStoredSort(),
    page: readStoredPage()
  };
  var uiText = copyUiText(UI_TEXT_DEFAULTS);
  var catalogueItems = [];
  var getSortedItems = createCatalogueSorter();
  var itemThumbnail = createThumbProjector(root);

  var thumbnailGridList = createThumbnailGridList({
    listElement: list,
    gridElement: thumbGrid,
    pagerElement: pager,
    pagerStatusElement: pagerStatus,
    previousButton: prevBtn,
    nextButton: nextBtn,
    pageSize: PAGE_SIZE,
    labels: {
      previous: uiText.pager_prev_label,
      next: uiText.pager_next_label
    },
    onPageChange: function (page) {
      state.page = normalizePage(page);
      persistPage(state.page);
    }
  });

  function updateSortUi() {
    sortButtons.forEach(function (button) {
      var key = normalizeSortKey(button.getAttribute('data-sort-key'));
      var direction = state.sort.directions[key];
      var isActive = key === state.sort.key;
      var labelEl = button.querySelector('.seriesIndex__sortText');
      var arrowEl = button.querySelector('.seriesIndex__sortArrow');
      var buttonLabel = key === 'title' ? uiText.sort_title_label : uiText.sort_year_label;
      var arrow = direction === 'desc' ? uiText.sort_direction_desc : uiText.sort_direction_asc;

      button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
      button.setAttribute(
        'aria-label',
        'Sort by ' + buttonLabel + ' ' + (direction === 'desc' ? 'descending' : 'ascending')
      );
      if (labelEl) labelEl.textContent = buttonLabel;
      if (arrowEl) arrowEl.textContent = arrow;
    });
  }

  function updateViewUi() {
    empty.textContent = uiText.empty_works;
    empty.hidden = catalogueItems.length > 0;
    viewButtons.forEach(function (button) {
      var buttonView = normalizeView(button.getAttribute('data-view'));
      var active = buttonView === state.view;
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function projectThumbnailItem(item) {
    return {
      id: text(item && item.id),
      title: text((item && item.title) || (item && item.id)),
      caption: yearDisplayText(item),
      href: text(item && item.href),
      thumbnail: itemThumbnail(item)
    };
  }

  function renderCurrentView() {
    var sortedItems = getSortedItems(catalogueItems, state.sort);
    var projectedItems = sortedItems.map(projectThumbnailItem);
    var result = thumbnailGridList.render({
      items: projectedItems,
      mode: state.view,
      page: state.page
    });
    state.page = normalizePage(result.page);
    persistPage(state.page);
    updateViewUi();
  }

  function cardHref(seriesItem) {
    var sid = text(seriesItem && seriesItem.series_id);
    var works = Array.isArray(seriesItem && seriesItem.works) ? seriesItem.works : [];
    if (works.length === 1) {
      return workUrl(String(works[0]), baseurl);
    }
    return catalogueIndexUrl(baseurl, { series: sid });
  }

  function buildSeriesItem(seriesItem) {
    var sid = text(seriesItem && seriesItem.series_id);
    if (!sid) return null;
    var yearDisplay = text(seriesItem && (seriesItem.year_display != null ? seriesItem.year_display : seriesItem.year));
    var numericYear = Number(seriesItem && seriesItem.year);
    return {
      kind: 'works',
      id: sid,
      title: text((seriesItem && seriesItem.title) || sid),
      href: cardHref(seriesItem),
      year_display: yearDisplay,
      year_sort: Number.isFinite(numericYear) ? numericYear : parseYearNumber('', yearDisplay),
      thumb_id: text(seriesItem && seriesItem.primary_work_id)
    };
  }

  function buildWorkItem(workId, worksMap, seriesRow) {
    var wid = text(workId);
    if (!wid) return null;
    var work = worksMap && worksMap[wid] && typeof worksMap[wid] === 'object' ? worksMap[wid] : {};
    var title = text((work && work.title) || wid);
    var yearDisplay = text(work && (work.year_display != null ? work.year_display : work.year));
    var numericYear = Number(work && work.year);
    return {
      kind: 'works',
      id: wid,
      title: title,
      href: workUrl(wid, baseurl, { series: selectedSeriesId }),
      year_display: yearDisplay,
      year_sort: Number.isFinite(numericYear) ? numericYear : parseYearNumber('', yearDisplay),
      thumb_id: wid,
      series_title: text((seriesRow && seriesRow.title) || selectedSeriesId)
    };
  }

  viewButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var nextView = normalizeView(button.getAttribute('data-view'));
      if (nextView === state.view) return;
      state.view = nextView;
      persistView(nextView);
      renderCurrentView();
    });
  });

  sortButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var nextKey = normalizeSortKey(button.getAttribute('data-sort-key'));
      if (state.sort.key === nextKey) {
        state.sort.directions[nextKey] = state.sort.directions[nextKey] === 'desc' ? 'asc' : 'desc';
      } else {
        state.sort.key = nextKey;
      }
      state.sort = sanitizeSortState(state.sort);
      persistSort(state.sort);
      updateSortUi();
      renderCurrentView();
    });
  });

  Promise.all([
    fetchJson(seriesIndexUrl(baseurl)),
    selectedSeriesId ? fetchJson(worksIndexUrl(baseurl)).catch(function () { return {}; }) : Promise.resolve({})
  ])
    .then(function (results) {
      var seriesPayload = results[0];
      var worksPayload = results[1];
      var seriesMap = seriesPayload && seriesPayload.series && typeof seriesPayload.series === 'object'
        ? seriesPayload.series
        : {};
      var worksMap = worksPayload && worksPayload.works && typeof worksPayload.works === 'object'
        ? worksPayload.works
        : {};

      uiText = copyUiText(UI_TEXT_DEFAULTS);
      if (selectedSeriesId) {
        var selectedSeries = seriesMap[selectedSeriesId] && typeof seriesMap[selectedSeriesId] === 'object'
          ? seriesMap[selectedSeriesId]
          : null;
        var selectedWorkIds = Array.isArray(selectedSeries && selectedSeries.works) ? selectedSeries.works : [];
        catalogueItems = selectedWorkIds.map(function (workId) {
          return buildWorkItem(workId, worksMap, selectedSeries);
        }).filter(Boolean);
      } else {
        catalogueItems = Object.keys(seriesMap).map(function (sid) {
          return buildSeriesItem(seriesMap[sid]);
        }).filter(Boolean);
      }

      if (!catalogueItems.length) {
        empty.textContent = uiText.empty_works;
        empty.hidden = false;
        root.hidden = true;
        return;
      }

      root.hidden = false;
      updateSortUi();
      renderCurrentView();
    })
    .catch(function () {
      list.innerHTML = '';
      thumbGrid.innerHTML = '';
      empty.textContent = 'problem loading content';
      empty.hidden = false;
      root.hidden = true;
    });
}

initSeriesIndexRoute();
