import { createThumbnailGridList } from '../components/thumbnail-grid-list.js';
import {
  catalogueIndexUrl,
  momentUrl,
  momentsIndexUrl,
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
var MODE_STORAGE_KEY = 'dlf.catalogIndex.mode';

var DEFAULT_SORT = {
  key: 'year',
  directions: {
    year: 'desc',
    title: 'asc'
  }
};

var STORAGE_KEYS = {
  works: {
    view: 'dlf.catalogIndex.works.view',
    sort: 'dlf.catalogIndex.works.sort',
    page: 'dlf.catalogIndex.works.page',
    legacyView: 'dlf.seriesIndex.view',
    legacySort: 'dlf.seriesIndex.sort',
    legacyPage: 'dlf.seriesIndex.page'
  },
  moments: {
    view: 'dlf.catalogIndex.moments.view',
    sort: 'dlf.catalogIndex.moments.sort',
    page: 'dlf.catalogIndex.moments.page',
    legacyView: 'dlf.momentsIndex.view',
    legacySort: 'dlf.momentsIndex.sort',
    legacyPage: ''
  }
};

var UI_TEXT_DEFAULTS = {
  sort_year_label: 'year',
  sort_title_label: 'title',
  sort_direction_asc: '↑',
  sort_direction_desc: '↓',
  pager_prev_label: 'Previous page',
  pager_next_label: 'Next page',
  mode_works_label: 'works',
  mode_moments_label: 'moments',
  empty_works: 'no works yet',
  empty_moments: 'no moments yet'
};

function normalizeMode(value) {
  return lowerText(value) === 'moments' ? 'moments' : 'works';
}

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

function readStoredMode() {
  return normalizeMode(readStoredItem(MODE_STORAGE_KEY, ''));
}

function persistMode(mode) {
  writeStoredItem(MODE_STORAGE_KEY, normalizeMode(mode));
}

function readStoredView(mode) {
  var keys = STORAGE_KEYS[normalizeMode(mode)];
  return normalizeView(readStoredItem(keys.view, keys.legacyView));
}

function persistView(mode, view) {
  var keys = STORAGE_KEYS[normalizeMode(mode)];
  writeStoredItem(keys.view, normalizeView(view));
}

function readStoredSort(mode) {
  var keys = STORAGE_KEYS[normalizeMode(mode)];
  var raw = readStoredItem(keys.sort, keys.legacySort);
  if (raw == null) return sanitizeSortState(DEFAULT_SORT);
  try {
    return sanitizeSortState(JSON.parse(raw));
  } catch (err) {
    return sanitizeSortState(DEFAULT_SORT);
  }
}

function persistSort(mode, sortState) {
  var keys = STORAGE_KEYS[normalizeMode(mode)];
  writeStoredItem(keys.sort, JSON.stringify(sanitizeSortState(sortState)));
}

function readStoredPage(mode) {
  var keys = STORAGE_KEYS[normalizeMode(mode)];
  return normalizePage(readStoredItem(keys.page, keys.legacyPage));
}

function persistPage(mode, page) {
  var keys = STORAGE_KEYS[normalizeMode(mode)];
  writeStoredItem(keys.page, String(normalizePage(page)));
}

function copyUiText(source) {
  return {
    sort_year_label: text((source && source.sort_year_label) || UI_TEXT_DEFAULTS.sort_year_label),
    sort_title_label: text((source && source.sort_title_label) || UI_TEXT_DEFAULTS.sort_title_label),
    sort_direction_asc: text((source && source.sort_direction_asc) || UI_TEXT_DEFAULTS.sort_direction_asc),
    sort_direction_desc: text((source && source.sort_direction_desc) || UI_TEXT_DEFAULTS.sort_direction_desc),
    pager_prev_label: text((source && source.pager_prev_label) || UI_TEXT_DEFAULTS.pager_prev_label),
    pager_next_label: text((source && source.pager_next_label) || UI_TEXT_DEFAULTS.pager_next_label),
    mode_works_label: text((source && source.mode_works_label) || UI_TEXT_DEFAULTS.mode_works_label),
    mode_moments_label: text((source && source.mode_moments_label) || UI_TEXT_DEFAULTS.mode_moments_label),
    empty_works: text((source && source.empty_works) || UI_TEXT_DEFAULTS.empty_works),
    empty_moments: text((source && source.empty_moments) || UI_TEXT_DEFAULTS.empty_moments)
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
  var thumbMomentsBase = text(root.getAttribute('data-thumb-moments-base'));
  var thumbSizes = loadThumbSizes(root);
  var primaryThumbSize = thumbSizes[0];
  var thumbSrcsetSizes = thumbSizes.slice(0, 2);
  var thumbSuffix = text(root.getAttribute('data-thumb-suffix')) || 'thumb';
  var assetFormat = text(root.getAttribute('data-asset-format')) || 'webp';

  function thumbBaseFor(item) {
    return item && item.kind === 'moments' ? thumbMomentsBase : thumbWorksBase;
  }

  return function itemThumbnail(item) {
    return thumbnailImageData({
      base: thumbBaseFor(item),
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
  var recentBtn = document.getElementById('seriesIndexRecentBtn');
  var empty = document.getElementById('seriesIndexEmpty');
  if (!root || !list || !thumbGrid || !pager || !pagerStatus || !prevBtn || !nextBtn || !recentBtn || !empty) return;

  var viewButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="catalog-index-view-btn"]'));
  var sortButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="catalog-index-sort-btn"]'));
  var modeButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="catalog-index-mode-btn"]'));
  if (!viewButtons.length || !sortButtons.length || !modeButtons.length) return;

  var baseurl = trimBaseurl(root.getAttribute('data-baseurl'));
  var routeState = parseRouteState(window.location);
  var selectedSeriesId = lowerText(routeState.series);
  var currentMode = selectedSeriesId ? 'works' : (routeState.mode === 'moments' ? 'moments' : readStoredMode());
  var modeState = {
    works: {
      view: readStoredView('works'),
      sort: readStoredSort('works'),
      page: readStoredPage('works')
    },
    moments: {
      view: readStoredView('moments'),
      sort: readStoredSort('moments'),
      page: readStoredPage('moments')
    }
  };
  var uiText = copyUiText(UI_TEXT_DEFAULTS);
  var catalogueItems = {
    works: [],
    moments: []
  };
  var getSortedItems = createCatalogueSorter();
  var itemThumbnail = createThumbProjector(root);

  function currentItems() {
    return Array.isArray(catalogueItems[currentMode]) ? catalogueItems[currentMode] : [];
  }

  function currentState() {
    return modeState[currentMode];
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
      currentState().page = normalizePage(page);
      persistPage(currentMode, currentState().page);
    }
  });

  function updateModeUi() {
    modeButtons.forEach(function (button) {
      var mode = normalizeMode(button.getAttribute('data-mode'));
      var label = mode === 'moments' ? uiText.mode_moments_label : uiText.mode_works_label;
      var active = mode === currentMode;
      var hasItems = Array.isArray(catalogueItems[mode]) && catalogueItems[mode].length > 0;
      var labelEl = button.querySelector('.seriesIndex__modeText');

      button.setAttribute('aria-pressed', active ? 'true' : 'false');
      button.setAttribute('aria-label', 'Show ' + label);
      button.disabled = !hasItems;
      if (labelEl) labelEl.textContent = label;
    });
    syncRecentButtonState();
  }

  function syncRecentButtonState() {
    var enabledHref = text(recentBtn.getAttribute('data-enabled-href'));
    var disabled = currentMode === 'moments' || !!selectedSeriesId;
    recentBtn.setAttribute('aria-disabled', disabled ? 'true' : 'false');
    if (disabled) {
      recentBtn.removeAttribute('href');
      recentBtn.setAttribute('tabindex', '-1');
    } else {
      if (enabledHref) recentBtn.setAttribute('href', enabledHref);
      recentBtn.removeAttribute('tabindex');
    }
  }

  function updateSortUi() {
    var sortState = currentState().sort;
    sortButtons.forEach(function (button) {
      var key = normalizeSortKey(button.getAttribute('data-sort-key'));
      var direction = sortState.directions[key];
      var isActive = key === sortState.key;
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
    var state = currentState();
    var hasItems = currentItems().length > 0;
    empty.textContent = currentMode === 'moments' ? uiText.empty_moments : uiText.empty_works;
    empty.hidden = hasItems;
    viewButtons.forEach(function (button) {
      var buttonView = normalizeView(button.getAttribute('data-view'));
      var active = buttonView === state.view;
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function renderCurrentView() {
    var items = currentItems();
    var state = currentState();
    var sortedItems = getSortedItems(items, state.sort);
    var projectedItems = sortedItems.map(projectThumbnailItem);
    var result = thumbnailGridList.render({
      items: projectedItems,
      mode: state.view,
      page: state.page
    });
    state.page = normalizePage(result.page);
    persistPage(currentMode, state.page);
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

  function mergeMomentIndexItem(item, indexMap) {
    var momentId = text((item && item.moment_id) || (item && item.id));
    var row = indexMap && momentId ? indexMap[momentId] : null;
    return {
      moment_id: momentId,
      title: text((row && row.title) || (item && item.title) || momentId),
      date: text(row && row.date),
      date_display: text(row && row.date_display),
      thumb_id: text(row && row.thumb_id)
    };
  }

  function buildMomentItem(momentItem) {
    var momentId = text(momentItem && momentItem.moment_id);
    if (!momentId) return null;
    var yearDisplay = text(momentItem && momentItem.date_display);
    if (!yearDisplay) {
      var fallbackYear = parseYearNumber(momentItem && momentItem.date, momentItem && momentItem.date_display);
      yearDisplay = Number.isFinite(fallbackYear) ? String(fallbackYear) : '';
    }
    return {
      kind: 'moments',
      id: momentId,
      title: text((momentItem && momentItem.title) || momentId),
      href: momentUrl(momentId, baseurl),
      year_display: yearDisplay,
      year_sort: parseYearNumber(momentItem && momentItem.date, momentItem && momentItem.date_display),
      thumb_id: text(momentItem && momentItem.thumb_id)
    };
  }

  function loadMomentsIndexMap() {
    return fetchJson(momentsIndexUrl(baseurl))
      .then(function (payload) {
        var moments = payload && payload.moments && typeof payload.moments === 'object' ? payload.moments : null;
        return moments || {};
      });
  }

  viewButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var nextView = normalizeView(button.getAttribute('data-view'));
      if (nextView === currentState().view) return;
      currentState().view = nextView;
      persistView(currentMode, nextView);
      renderCurrentView();
    });
  });

  sortButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var nextKey = normalizeSortKey(button.getAttribute('data-sort-key'));
      if (currentState().sort.key === nextKey) {
        currentState().sort.directions[nextKey] = currentState().sort.directions[nextKey] === 'desc' ? 'asc' : 'desc';
      } else {
        currentState().sort.key = nextKey;
      }
      currentState().sort = sanitizeSortState(currentState().sort);
      persistSort(currentMode, currentState().sort);
      updateSortUi();
      renderCurrentView();
    });
  });

  modeButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var nextMode = normalizeMode(button.getAttribute('data-mode'));
      if (selectedSeriesId) {
        window.location.href = catalogueIndexUrl(baseurl, nextMode === 'moments' ? { mode: 'moments' } : {});
        return;
      }
      if (nextMode === currentMode || !catalogueItems[nextMode].length) return;
      currentMode = nextMode;
      persistMode(currentMode);
      if (window.history && window.history.replaceState) {
        window.history.replaceState({}, '', catalogueIndexUrl(baseurl, { mode: currentMode }));
      }
      updateModeUi();
      updateSortUi();
      renderCurrentView();
    });
  });

  Promise.all([
    fetchJson(seriesIndexUrl(baseurl)),
    loadMomentsIndexMap(),
    selectedSeriesId ? fetchJson(worksIndexUrl(baseurl)).catch(function () { return {}; }) : Promise.resolve({})
  ])
    .then(function (results) {
      var seriesPayload = results[0];
      var momentsIndexMap = results[1];
      var worksPayload = results[2];
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
        catalogueItems.works = selectedWorkIds.map(function (workId) {
          return buildWorkItem(workId, worksMap, selectedSeries);
        }).filter(Boolean);
      } else {
        catalogueItems.works = Object.keys(seriesMap).map(function (sid) {
          return buildSeriesItem(seriesMap[sid]);
        }).filter(Boolean);
      }
      catalogueItems.moments = Object.keys(momentsIndexMap).map(function (momentId) {
        return buildMomentItem(mergeMomentIndexItem({ moment_id: momentId }, momentsIndexMap));
      }).filter(Boolean);

      if (!catalogueItems.works.length && !catalogueItems.moments.length) {
        empty.textContent = uiText.empty_works;
        empty.hidden = false;
        root.hidden = true;
        return;
      }

      if (!catalogueItems[currentMode].length) {
        currentMode = catalogueItems.works.length ? 'works' : 'moments';
        persistMode(currentMode);
      }

      root.hidden = false;
      updateModeUi();
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
