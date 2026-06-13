  (function () {
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

    var runtime = window.__dlfPublicCatalogueRuntime;
    if (!runtime) return;

    var baseurl = runtime.trimBaseurl(root.getAttribute('data-baseurl'));
    var routeState = runtime.parseRouteState(window.location);
    var selectedSeriesId = String(routeState.series || '').trim().toLowerCase();
    var thumbWorksBase = String(root.getAttribute('data-thumb-works-base') || '').trim();
    var thumbMomentsBase = String(root.getAttribute('data-thumb-moments-base') || '').trim();
    var thumbSizes = [];
    try {
      thumbSizes = JSON.parse(root.getAttribute('data-thumb-sizes') || '[]');
    } catch (e) {
      thumbSizes = [];
    }
    thumbSizes = Array.isArray(thumbSizes) ? thumbSizes.map(function (value) {
      var n = Number(value);
      return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
    }).filter(function (value) { return value > 0; }) : [];
    if (!thumbSizes.length) thumbSizes = [96, 192];
    var primaryThumbSize = thumbSizes[0];
    var thumbSrcsetSizes = thumbSizes.slice(0, 2);
    var thumbSuffix = String(root.getAttribute('data-thumb-suffix') || 'thumb').trim() || 'thumb';
    var assetFormat = String(root.getAttribute('data-asset-format') || 'webp').trim() || 'webp';
    var seriesIndexUrl = baseurl + '/assets/data/series_index.json';
    var momentsIndexUrl = baseurl + '/assets/data/moments_index.json';
    var pageSize = 80;
    var modeStorageKey = 'dlf.catalogIndex.mode';
    var defaultSort = {
      key: 'year',
      directions: {
        year: 'desc',
        title: 'asc'
      }
    };
    var storageKeys = {
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
    var uiTextDefaults = {
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
    var uiText = copyUiText(uiTextDefaults);
    var catalogueItems = {
      works: [],
      moments: []
    };
    var titleCollator = (window.Intl && typeof window.Intl.Collator === 'function')
      ? new window.Intl.Collator(undefined, { numeric: true, sensitivity: 'base' })
      : null;

    function normalizeMode(value) {
      return String(value || '').trim().toLowerCase() === 'moments' ? 'moments' : 'works';
    }

    function readStoredMode() {
      try {
        return normalizeMode(window.localStorage.getItem(modeStorageKey));
      } catch (err) {
        return 'works';
      }
    }

    function persistMode(mode) {
      try {
        window.localStorage.setItem(modeStorageKey, normalizeMode(mode));
      } catch (err) {
      }
    }

    function readStoredItem(primaryKey, legacyKey) {
      try {
        var primaryValue = window.localStorage.getItem(primaryKey);
        if (primaryValue != null && String(primaryValue).trim() !== '') return primaryValue;
        if (!legacyKey) return null;
        var legacyValue = window.localStorage.getItem(legacyKey);
        return legacyValue != null && String(legacyValue).trim() !== '' ? legacyValue : null;
      } catch (err) {
        return null;
      }
    }

    function normalizeView(value) {
      return String(value || '').trim().toLowerCase() === 'list' ? 'list' : 'grid';
    }

    function readStoredView(mode) {
      var keys = storageKeys[normalizeMode(mode)];
      return normalizeView(readStoredItem(keys.view, keys.legacyView));
    }

    function persistView(mode, view) {
      var keys = storageKeys[normalizeMode(mode)];
      try {
        window.localStorage.setItem(keys.view, normalizeView(view));
      } catch (err) {
      }
    }

    function normalizeDirection(value, fallback) {
      var normalized = String(value || '').trim().toLowerCase();
      if (normalized === 'asc' || normalized === 'desc') return normalized;
      return fallback === 'desc' ? 'desc' : 'asc';
    }

    function normalizeSortKey(value) {
      return String(value || '').trim().toLowerCase() === 'title' ? 'title' : 'year';
    }

    function sanitizeSortState(raw) {
      var directions = raw && raw.directions && typeof raw.directions === 'object' ? raw.directions : {};
      return {
        key: normalizeSortKey(raw && raw.key),
        directions: {
          year: normalizeDirection(directions.year, defaultSort.directions.year),
          title: normalizeDirection(directions.title, defaultSort.directions.title)
        }
      };
    }

    function readStoredSort(mode) {
      var keys = storageKeys[normalizeMode(mode)];
      var raw = readStoredItem(keys.sort, keys.legacySort);
      if (raw == null) return sanitizeSortState(defaultSort);
      try {
        return sanitizeSortState(JSON.parse(raw));
      } catch (err) {
        return sanitizeSortState(defaultSort);
      }
    }

    function persistSort(mode, sortState) {
      var keys = storageKeys[normalizeMode(mode)];
      try {
        window.localStorage.setItem(keys.sort, JSON.stringify(sanitizeSortState(sortState)));
      } catch (err) {
      }
    }

    function normalizePage(value) {
      var page = Number(value);
      if (!Number.isFinite(page) || page < 1) return 1;
      return Math.floor(page);
    }

    function readStoredPage(mode) {
      var keys = storageKeys[normalizeMode(mode)];
      return normalizePage(readStoredItem(keys.page, keys.legacyPage));
    }

    function persistPage(mode, page) {
      var keys = storageKeys[normalizeMode(mode)];
      try {
        window.localStorage.setItem(keys.page, String(normalizePage(page)));
      } catch (err) {
      }
    }

    function copyUiText(source) {
      return {
        sort_year_label: String((source && source.sort_year_label) || uiTextDefaults.sort_year_label),
        sort_title_label: String((source && source.sort_title_label) || uiTextDefaults.sort_title_label),
        sort_direction_asc: String((source && source.sort_direction_asc) || uiTextDefaults.sort_direction_asc),
        sort_direction_desc: String((source && source.sort_direction_desc) || uiTextDefaults.sort_direction_desc),
        pager_prev_label: String((source && source.pager_prev_label) || uiTextDefaults.pager_prev_label),
        pager_next_label: String((source && source.pager_next_label) || uiTextDefaults.pager_next_label),
        mode_works_label: String((source && source.mode_works_label) || uiTextDefaults.mode_works_label),
        mode_moments_label: String((source && source.mode_moments_label) || uiTextDefaults.mode_moments_label),
        empty_works: String((source && source.empty_works) || uiTextDefaults.empty_works),
        empty_moments: String((source && source.empty_moments) || uiTextDefaults.empty_moments)
      };
    }

    function fetchJson(url) {
      return fetch(url, { cache: 'default' })
        .then(function (response) {
          if (!response.ok) throw new Error('HTTP ' + response.status);
          return response.json();
        });
    }

    function compareText(a, b) {
      var aa = String(a || '');
      var bb = String(b || '');
      if (titleCollator) return titleCollator.compare(aa, bb);
      if (aa < bb) return -1;
      if (aa > bb) return 1;
      return 0;
    }

    function numericAwareSortKey(value) {
      return String(value == null ? '' : value).trim().replace(/\d+/g, function (m) {
        return m.padStart(3, '0');
      });
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

    function yearDisplayText(item) {
      return String((item && item.year_display) || '').trim();
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

    function getSortedItems(items, sortState) {
      return items.slice().sort(function (a, b) {
        return compareCatalogueItems(a, b, sortState);
      });
    }

    function thumbBaseFor(item) {
      return item && item.kind === 'moments' ? thumbMomentsBase : thumbWorksBase;
    }

    function thumbUrl(item, size) {
      var thumbId = String(item && item.thumb_id || '').trim();
      if (!thumbId) return '';
      return thumbBaseFor(item) + thumbId + '-' + thumbSuffix + '-' + size + '.' + assetFormat;
    }

    function itemThumbData(item) {
      var thumbPrimary = thumbUrl(item, String(primaryThumbSize));
      return {
        thumb_primary: thumbPrimary,
        thumb_srcset: thumbPrimary ? thumbSrcsetSizes.map(function (size) {
          return thumbUrl(item, String(size)) + ' ' + size + 'w';
        }).join(', ') : ''
      };
    }

    function buildListThumbPlaceholder() {
      var placeholder = document.createElement('span');
      placeholder.className = 'seriesIndexItem__img';
      placeholder.setAttribute('aria-hidden', 'true');
      return placeholder;
    }

    function buildGridThumbPlaceholder(title) {
      var placeholder = document.createElement('span');
      placeholder.className = 'seriesGrid__img seriesGrid__img--placeholder';
      placeholder.setAttribute('aria-hidden', 'true');
      if (title) placeholder.title = title;
      return placeholder;
    }

    function renderCatalogueCard(item) {
      var href = String((item && item.href) || '').trim();
      var thumbData = itemThumbData(item);
      var thumb = thumbData.thumb_primary;
      var title = String((item && item.title) || (item && item.id) || '');
      var yearTxt = yearDisplayText(item);

      var link = document.createElement('a');
      link.className = 'seriesIndexItem';
      link.href = href;

      if (thumb) {
        var img = document.createElement('img');
        img.className = 'seriesIndexItem__img';
        img.addEventListener('error', function () {
          if (!img.parentNode) return;
          img.parentNode.replaceChild(buildListThumbPlaceholder(), img);
        }, { once: true });
        img.src = thumb;
        img.alt = title;
        img.loading = 'lazy';
        img.decoding = 'async';
        link.appendChild(img);
      } else {
        var placeholder = document.createElement('span');
        placeholder.className = 'seriesIndexItem__img';
        placeholder.setAttribute('aria-hidden', 'true');
        link.appendChild(placeholder);
      }

      var meta = document.createElement('div');
      meta.className = 'seriesIndexItem__meta';

      var titleEl = document.createElement('div');
      titleEl.className = 'seriesIndexItem__title';
      titleEl.textContent = title;
      meta.appendChild(titleEl);

      var yearEl = document.createElement('div');
      yearEl.className = 'seriesIndexItem__year';
      yearEl.textContent = yearTxt;
      meta.appendChild(yearEl);

      link.appendChild(meta);
      return link;
    }

    function renderCatalogueGridItem(item) {
      var href = String((item && item.href) || '').trim();
      var thumbData = itemThumbData(item);
      var thumbPrimary = String(thumbData.thumb_primary || '');
      var thumbSrcset = String(thumbData.thumb_srcset || '');
      var title = String((item && item.title) || (item && item.id) || '');

      var link = document.createElement('a');
      link.className = 'seriesGrid__item';
      link.href = href;
      link.setAttribute('aria-label', title);
      link.title = title;

      if (thumbPrimary) {
        var img = document.createElement('img');
        img.className = 'seriesGrid__img';
        img.addEventListener('error', function () {
          if (!img.parentNode) return;
          img.parentNode.replaceChild(buildGridThumbPlaceholder(title), img);
        }, { once: true });
        img.src = thumbPrimary;
        img.srcset = thumbSrcset;
        img.sizes = '(min-width: 1200px) 10vw, (min-width: 700px) 14vw, 22vw';
        img.width = primaryThumbSize;
        img.height = primaryThumbSize;
        img.loading = 'lazy';
        img.decoding = 'async';
        img.alt = title;
        link.appendChild(img);
      } else {
        link.appendChild(buildGridThumbPlaceholder(title));
      }

      return link;
    }

    function parseYearNumber(rawDate, displayText) {
      var dateText = String(rawDate || '').trim();
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateText)) return Number(dateText.slice(0, 4));
      var display = String(displayText || '').trim();
      var match = display.match(/(\d{4})/);
      return match ? Number(match[1]) : null;
    }

    function cardHref(seriesItem) {
      var sid = String((seriesItem && seriesItem.series_id) || '').trim();
      var works = Array.isArray(seriesItem && seriesItem.works) ? seriesItem.works : [];
      if (works.length === 1) {
        return runtime.workUrl(String(works[0]), baseurl);
      }
      return runtime.catalogueIndexUrl(baseurl, { series: sid });
    }

    function buildSeriesItem(seriesItem) {
      var sid = String((seriesItem && seriesItem.series_id) || '').trim();
      if (!sid) return null;
      var yearDisplay = String((seriesItem && (seriesItem.year_display != null ? seriesItem.year_display : seriesItem.year)) || '').trim();
      var numericYear = Number(seriesItem && seriesItem.year);
      return {
        kind: 'works',
        id: sid,
        title: String((seriesItem && seriesItem.title) || sid),
        href: cardHref(seriesItem),
        year_display: yearDisplay,
        year_sort: Number.isFinite(numericYear) ? numericYear : parseYearNumber('', yearDisplay),
        thumb_id: String((seriesItem && seriesItem.primary_work_id) || '').trim()
      };
    }

    function buildWorkItem(workId, worksMap, seriesRow) {
      var wid = String(workId || '').trim();
      if (!wid) return null;
      var work = worksMap && worksMap[wid] && typeof worksMap[wid] === 'object' ? worksMap[wid] : {};
      var title = String((work && work.title) || wid);
      var yearDisplay = String((work && (work.year_display != null ? work.year_display : work.year)) || '').trim();
      var numericYear = Number(work && work.year);
      return {
        kind: 'works',
        id: wid,
        title: title,
        href: runtime.workUrl(wid, baseurl, { series: selectedSeriesId }),
        year_display: yearDisplay,
        year_sort: Number.isFinite(numericYear) ? numericYear : parseYearNumber('', yearDisplay),
        thumb_id: wid,
        series_title: String((seriesRow && seriesRow.title) || selectedSeriesId)
      };
    }

    function mergeMomentIndexItem(item, indexMap) {
      var momentId = String((item && item.moment_id) || (item && item.id) || '').trim();
      var row = indexMap && momentId ? indexMap[momentId] : null;
      return {
        moment_id: momentId,
        title: String((row && row.title) || (item && item.title) || momentId),
        date: String((row && row.date) || ''),
        date_display: String((row && row.date_display) || ''),
        thumb_id: String((row && row.thumb_id) || '').trim()
      };
    }

    function buildMomentItem(momentItem) {
      var momentId = String((momentItem && momentItem.moment_id) || '').trim();
      if (!momentId) return null;
      var yearDisplay = String((momentItem && momentItem.date_display) || '').trim();
      if (!yearDisplay) {
        var fallbackYear = parseYearNumber(momentItem && momentItem.date, momentItem && momentItem.date_display);
        yearDisplay = Number.isFinite(fallbackYear) ? String(fallbackYear) : '';
      }
      return {
        kind: 'moments',
        id: momentId,
        title: String((momentItem && momentItem.title) || momentId),
        href: runtime.momentUrl(momentId, baseurl),
        year_display: yearDisplay,
        year_sort: parseYearNumber(momentItem && momentItem.date, momentItem && momentItem.date_display),
        thumb_id: String((momentItem && momentItem.thumb_id) || '').trim()
      };
    }

    function loadMomentsIndexMap() {
      return fetchJson(momentsIndexUrl)
        .then(function (payload) {
          var moments = payload && payload.moments && typeof payload.moments === 'object' ? payload.moments : null;
          return moments || {};
        });
    }

    function currentItems() {
      return Array.isArray(catalogueItems[currentMode]) ? catalogueItems[currentMode] : [];
    }

    function currentState() {
      return modeState[currentMode];
    }

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
      var enabledHref = String(recentBtn.getAttribute('data-enabled-href') || '').trim();
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
      var showingGrid = currentState().view === 'grid';
      var hasItems = currentItems().length > 0;
      list.hidden = !hasItems || showingGrid;
      thumbGrid.hidden = !hasItems || !showingGrid;
      pager.classList.toggle('seriesIndex__pager--list', !showingGrid);
      empty.textContent = currentMode === 'moments' ? uiText.empty_moments : uiText.empty_works;
      empty.hidden = hasItems;
      viewButtons.forEach(function (button) {
        var buttonView = String(button.getAttribute('data-view') || '').trim().toLowerCase();
        var active = buttonView === currentState().view;
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
    }

    function updatePagerUi(pageCount) {
      var state = currentState();
      var safePageCount = Math.max(1, Number(pageCount) || 1);
      state.page = Math.min(normalizePage(state.page), safePageCount);
      pagerStatus.textContent = String(state.page) + '/' + String(safePageCount);
      pager.hidden = safePageCount < 2 || currentItems().length < 1;
      prevBtn.disabled = safePageCount < 2;
      nextBtn.disabled = safePageCount < 2;
      prevBtn.setAttribute('aria-label', uiText.pager_prev_label);
      nextBtn.setAttribute('aria-label', uiText.pager_next_label);
      persistPage(currentMode, state.page);
    }

    function renderCurrentView() {
      var items = currentItems();
      var state = currentState();
      var sortedItems = getSortedItems(items, state.sort);
      var pageCount = Math.max(1, Math.ceil(sortedItems.length / pageSize));
      state.page = Math.min(normalizePage(state.page), pageCount);
      var start = (state.page - 1) * pageSize;
      var end = Math.min(start + pageSize, sortedItems.length);
      var pageItems = sortedItems.slice(start, end);
      list.innerHTML = '';
      thumbGrid.innerHTML = '';
      pager.hidden = true;

      if (!sortedItems.length) {
        updatePagerUi(1);
        updateViewUi();
        return;
      }

      var frag = document.createDocumentFragment();
      var i;

      if (state.view === 'grid') {
        for (i = 0; i < pageItems.length; i += 1) {
          frag.appendChild(renderCatalogueGridItem(pageItems[i]));
        }
        thumbGrid.appendChild(frag);
      } else {
        for (i = 0; i < pageItems.length; i += 1) {
          frag.appendChild(renderCatalogueCard(pageItems[i]));
        }
        list.appendChild(frag);
      }

      updatePagerUi(pageCount);
      updateViewUi();
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
          window.location.href = runtime.catalogueIndexUrl(baseurl, nextMode === 'moments' ? { mode: 'moments' } : {});
          return;
        }
        if (nextMode === currentMode || !catalogueItems[nextMode].length) return;
        currentMode = nextMode;
        persistMode(currentMode);
        if (window.history && window.history.replaceState) {
          window.history.replaceState({}, '', runtime.catalogueIndexUrl(baseurl, { mode: currentMode }));
        }
        updateModeUi();
        updateSortUi();
        renderCurrentView();
      });
    });

    prevBtn.addEventListener('click', function () {
      var pageCount = Math.max(1, Math.ceil(currentItems().length / pageSize));
      if (pageCount < 2) return;
      currentState().page = (currentState().page - 1 + pageCount - 1) % pageCount + 1;
      renderCurrentView();
    });

    nextBtn.addEventListener('click', function () {
      var pageCount = Math.max(1, Math.ceil(currentItems().length / pageSize));
      if (pageCount < 2) return;
      currentState().page = (currentState().page % pageCount) + 1;
      renderCurrentView();
    });

    Promise.all([
      fetchJson(seriesIndexUrl),
      loadMomentsIndexMap(),
      selectedSeriesId ? fetchJson(baseurl + '/assets/data/works_index.json').catch(function () { return {}; }) : Promise.resolve({})
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

        uiText = copyUiText(uiTextDefaults);
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
  })();
