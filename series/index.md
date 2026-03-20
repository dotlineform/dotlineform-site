---
layout: default
title: works
section: series
permalink: /series/
---

<h1 class="index__heading visually-hidden">works</h1>
{% assign thumb_base = site.thumb_base | default: "" %}
{% assign thumb_works = site.thumb_works | default: "/assets/works/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign thumb_variants = pipeline.variants.thumb %}
{% assign thumb_sizes = thumb_variants.sizes | default: "96,192" %}
{% assign thumb_suffix = thumb_variants.suffix | default: "thumb" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign thumb_works_base = thumb_base | append: thumb_works | append: "/" %}
{%- assign thumb_works_base_out = thumb_works_base -%}
{%- unless thumb_works_base contains '://' -%}
  {%- assign thumb_works_base_out = thumb_works_base | relative_url -%}
{%- endunless -%}

<div id="seriesIndexRoot" data-thumb-works-base="{{ thumb_works_base_out | escape }}" data-thumb-sizes="{{ thumb_sizes | jsonify | escape }}" data-thumb-suffix="{{ thumb_suffix | escape }}" data-asset-format="{{ asset_format | escape }}" hidden>
  <div class="seriesIndex__toolbar" aria-label="Series view and sorting">
    <div class="seriesIndex__viewControls" role="group" aria-label="Series view">
      <button
        class="theme-toggle seriesIndex__viewBtn"
        type="button"
        data-role="series-index-view-btn"
        data-view="list"
        aria-label="Show list view"
        aria-pressed="true"
      >
        <svg class="seriesIndex__viewIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <rect x="4" y="5" width="2.5" height="2.5" rx="1"></rect>
          <rect x="4" y="10.75" width="2.5" height="2.5" rx="1"></rect>
          <rect x="4" y="16.5" width="2.5" height="2.5" rx="1"></rect>
          <path d="M10 6.25H20"></path>
          <path d="M10 12H20"></path>
          <path d="M10 17.75H20"></path>
        </svg>
        <span class="sr-only">list</span>
      </button>
      <button
        class="theme-toggle seriesIndex__viewBtn"
        type="button"
        data-role="series-index-view-btn"
        data-view="grid"
        aria-label="Show grid view"
        aria-pressed="false"
      >
        <svg class="seriesIndex__viewIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <rect x="4" y="4" width="6.25" height="6.25" rx="1.5"></rect>
          <rect x="13.75" y="4" width="6.25" height="6.25" rx="1.5"></rect>
          <rect x="4" y="13.75" width="6.25" height="6.25" rx="1.5"></rect>
          <rect x="13.75" y="13.75" width="6.25" height="6.25" rx="1.5"></rect>
        </svg>
        <span class="sr-only">grid</span>
      </button>
    </div>
    <span class="seriesIndex__toolbarSpacer" aria-hidden="true"></span>
    <div class="seriesIndex__sortControls" role="group" aria-label="Sort series">
      <button
        class="theme-toggle seriesIndex__sortBtn"
        type="button"
        data-role="series-index-sort-btn"
        data-sort-key="year"
        aria-pressed="true"
      >
        <span class="seriesIndex__sortText">year</span>
        <span class="seriesIndex__sortArrow" aria-hidden="true">↓</span>
      </button>
      <button
        class="theme-toggle seriesIndex__sortBtn"
        type="button"
        data-role="series-index-sort-btn"
        data-sort-key="title"
        aria-pressed="false"
      >
        <span class="seriesIndex__sortText">title</span>
        <span class="seriesIndex__sortArrow" aria-hidden="true">↑</span>
      </button>
    </div>
  </div>
  <div class="index seriesIndex__list" id="seriesIndexList" aria-live="polite"></div>
  <div class="seriesGrid seriesIndex__grid" id="seriesIndexThumbGrid" aria-live="polite" hidden></div>
</div>
<p id="seriesIndexEmpty" hidden>no series yet</p>

<script>
  (function () {
    var root = document.getElementById('seriesIndexRoot');
    var list = document.getElementById('seriesIndexList');
    var thumbGrid = document.getElementById('seriesIndexThumbGrid');
    var empty = document.getElementById('seriesIndexEmpty');
    if (!root || !list || !thumbGrid || !empty) return;

    var viewButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="series-index-view-btn"]'));
    var sortButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="series-index-sort-btn"]'));
    if (!viewButtons.length || !sortButtons.length) return;

    var baseurl = {{ site.baseurl | default: '' | jsonify }};
    var thumbWorksBase = String(root.getAttribute('data-thumb-works-base') || '');
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
    if (thumbSrcsetSizes.length < 2) thumbSrcsetSizes = [primaryThumbSize, primaryThumbSize];
    var thumbSuffix = String(root.getAttribute('data-thumb-suffix') || 'thumb').trim() || 'thumb';
    var assetFormat = String(root.getAttribute('data-asset-format') || 'webp').trim() || 'webp';
    var dataUrl = baseurl + '/assets/data/series_index.json';
    var configUrl = baseurl + '/assets/studio/data/studio_config.json';
    var viewStorageKey = 'dlf.seriesIndex.view';
    var sortStorageKey = 'dlf.seriesIndex.sort';
    var defaultSort = {
      key: 'year',
      directions: {
        year: 'desc',
        title: 'asc'
      }
    };
    var uiTextDefaults = {
      sort_year_label: 'year',
      sort_title_label: 'title',
      sort_direction_asc: '↑',
      sort_direction_desc: '↓'
    };
    var currentView = readStoredView();
    var currentSort = readStoredSort();
    var uiText = copyUiText(uiTextDefaults);
    var seriesItems = [];
    var titleCollator = (window.Intl && typeof window.Intl.Collator === 'function')
      ? new window.Intl.Collator(undefined, { numeric: true, sensitivity: 'base' })
      : null;

    function thumbUrl(workId, size) {
      var wid = String(workId || '').trim();
      if (!wid) return '';
      return String(thumbWorksBase || '') + wid + '-' + thumbSuffix + '-' + size + '.' + assetFormat;
    }

    function normalizeView(value) {
      return String(value || '').trim().toLowerCase() === 'list' ? 'list' : 'grid';
    }

    function readStoredView() {
      try {
        return normalizeView(window.localStorage.getItem(viewStorageKey));
      } catch (err) {
        return 'grid';
      }
    }

    function persistView(view) {
      try {
        window.localStorage.setItem(viewStorageKey, normalizeView(view));
      } catch (err) {
        // Ignore storage failures; the page still works with in-memory state.
      }
    }

    function fetchJson(url) {
      return fetch(url, { cache: 'default' })
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        });
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

    function readStoredSort() {
      try {
        return sanitizeSortState(JSON.parse(window.localStorage.getItem(sortStorageKey) || 'null'));
      } catch (err) {
        return sanitizeSortState(defaultSort);
      }
    }

    function persistSort(sortState) {
      try {
        window.localStorage.setItem(sortStorageKey, JSON.stringify(sanitizeSortState(sortState)));
      } catch (err) {
        // Ignore storage failures; the page still works with in-memory state.
      }
    }

    function copyUiText(source) {
      return {
        sort_year_label: String((source && source.sort_year_label) || uiTextDefaults.sort_year_label),
        sort_title_label: String((source && source.sort_title_label) || uiTextDefaults.sort_title_label),
        sort_direction_asc: String((source && source.sort_direction_asc) || uiTextDefaults.sort_direction_asc),
        sort_direction_desc: String((source && source.sort_direction_desc) || uiTextDefaults.sort_direction_desc)
      };
    }

    function readUiText(configPayload) {
      var text = configPayload && configPayload.ui_text && configPayload.ui_text.site_series_index;
      return copyUiText(text);
    }

    function compareText(a, b) {
      var aa = String(a || '');
      var bb = String(b || '');
      if (titleCollator) return titleCollator.compare(aa, bb);
      if (aa < bb) return -1;
      if (aa > bb) return 1;
      return 0;
    }

    function compareSeriesId(a, b) {
      return compareText(a && a.series_id, b && b.series_id);
    }

    function numericAwareSortKey(value) {
      return String(value == null ? '' : value).trim().replace(/\d+/g, function (m) {
        return m.padStart(3, '0');
      });
    }

    function titleValue(item) {
      return numericAwareSortKey(item && (item.title || item.series_id));
    }

    function titleCompare(a, b) {
      var cmp = compareText(titleValue(a), titleValue(b));
      if (cmp !== 0) return cmp;
      return compareSeriesId(a, b);
    }

    function yearDisplayText(item) {
      return String((item && (item.year_display != null ? item.year_display : item.year)) || '').trim();
    }

    function yearSortNumber(item) {
      var numericYear = Number(item && item.year);
      if (Number.isFinite(numericYear)) return numericYear;
      var match = yearDisplayText(item).match(/(\d{4})/);
      if (match) return Number(match[1]);
      return null;
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

    function compareSeries(a, b, sortState) {
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
      return compareSeriesId(a, b);
    }

    function getSortedItems(items, sortState) {
      return items.slice().sort(function (a, b) {
        return compareSeries(a, b, sortState);
      });
    }

    function cardHref(s) {
      var sid = String((s && s.series_id) || '').trim();
      var works = Array.isArray(s && s.works) ? s.works : [];
      if (works.length === 1) {
        return baseurl + '/works/' + encodeURIComponent(String(works[0])) + '/';
      }
      return baseurl + '/series/' + encodeURIComponent(sid) + '/';
    }

    function cardThumbData(s) {
      var thumbId = String((s && s.primary_work_id) || '').trim();
      return {
        thumb_primary: thumbUrl(thumbId, String(primaryThumbSize)),
        thumb_srcset: thumbSrcsetSizes.map(function (size) {
          return thumbUrl(thumbId, String(size)) + ' ' + size + 'w';
        }).join(', '),
        thumb_id: thumbId
      };
    }

    function renderSeriesCard(s) {
      var href = cardHref(s);
      var thumbData = cardThumbData(s);
      var thumb = thumbData.thumb_primary;
      var title = String((s && s.title) || (s && s.series_id) || '');
      var yearTxt = String((s && (s.year_display != null ? s.year_display : s.year)) || '');

      var a = document.createElement('a');
      a.className = 'seriesIndexItem';
      a.href = href;

      if (thumb) {
        var img = document.createElement('img');
        img.className = 'seriesIndexItem__img';
        img.src = thumb;
        img.alt = title;
        img.loading = 'lazy';
        img.decoding = 'async';
        a.appendChild(img);
      }

      var meta = document.createElement('div');
      meta.className = 'seriesIndexItem__meta';

      var t = document.createElement('div');
      t.className = 'seriesIndexItem__title';
      t.textContent = title;
      meta.appendChild(t);

      var y = document.createElement('div');
      y.className = 'seriesIndexItem__year';
      y.textContent = yearTxt;
      meta.appendChild(y);

      a.appendChild(meta);
      return a;
    }

    function renderSeriesGridItem(s) {
      var href = cardHref(s);
      var thumbData = cardThumbData(s);
      var thumbPrimary = String(thumbData.thumb_primary || '');
      var thumbSrcset = String(thumbData.thumb_srcset || '');
      var title = String((s && s.title) || (s && s.series_id) || '');

      var a = document.createElement('a');
      a.className = 'seriesGrid__item';
      a.href = href;
      a.setAttribute('aria-label', title);
      a.title = title;

      if (thumbPrimary) {
        var img = document.createElement('img');
        img.className = 'seriesGrid__img';
        img.src = thumbPrimary;
        img.srcset = thumbSrcset;
        img.sizes = '(min-width: 1200px) 10vw, (min-width: 700px) 14vw, 22vw';
        img.width = primaryThumbSize;
        img.height = primaryThumbSize;
        img.loading = 'lazy';
        img.decoding = 'async';
        img.alt = title;
        a.appendChild(img);
      }

      return a;
    }

    function updateSortUi() {
      sortButtons.forEach(function (button) {
        var key = normalizeSortKey(button.getAttribute('data-sort-key'));
        var direction = currentSort.directions[key];
        var isActive = key === currentSort.key;
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
      var showingGrid = currentView === 'grid';
      list.hidden = showingGrid;
      thumbGrid.hidden = !showingGrid;
      viewButtons.forEach(function (button) {
        var buttonView = String(button.getAttribute('data-view') || '').trim().toLowerCase();
        var active = buttonView === currentView;
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
    }

    function renderCurrentView() {
      var sortedItems = getSortedItems(seriesItems, currentSort);
      list.innerHTML = '';
      thumbGrid.innerHTML = '';
      if (!sortedItems.length) return;

      var frag = document.createDocumentFragment();
      var i;

      if (currentView === 'grid') {
        for (i = 0; i < sortedItems.length; i += 1) {
          frag.appendChild(renderSeriesGridItem(sortedItems[i]));
        }
        thumbGrid.appendChild(frag);
      } else {
        for (i = 0; i < sortedItems.length; i += 1) {
          frag.appendChild(renderSeriesCard(sortedItems[i]));
        }
        list.appendChild(frag);
      }
    }

    viewButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var nextView = normalizeView(button.getAttribute('data-view'));
        if (nextView === currentView) return;
        currentView = nextView;
        renderCurrentView();
        updateViewUi();
        persistView(currentView);
      });
    });

    sortButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var nextKey = normalizeSortKey(button.getAttribute('data-sort-key'));
        if (currentSort.key === nextKey) {
          currentSort.directions[nextKey] = currentSort.directions[nextKey] === 'desc' ? 'asc' : 'desc';
        } else {
          currentSort.key = nextKey;
        }
        currentSort = sanitizeSortState(currentSort);
        renderCurrentView();
        updateSortUi();
        persistSort(currentSort);
      })
    });

    Promise.all([
      fetchJson(dataUrl),
      fetchJson(configUrl).catch(function () { return null; })
    ])
      .then(function (results) {
        var payload = results[0];
        var configPayload = results[1];
        var seriesMap = (payload && payload.series && typeof payload.series === 'object') ? payload.series : {};
        uiText = readUiText(configPayload);
        seriesItems = Object.keys(seriesMap).map(function (sid) { return seriesMap[sid]; }).filter(Boolean);

        if (!seriesItems.length) {
          root.hidden = true;
          empty.hidden = false;
          return;
        }

        empty.hidden = true;
        root.hidden = false;
        renderCurrentView();
        updateSortUi();
        updateViewUi();
      })
      .catch(function () {
        list.innerHTML = '';
        thumbGrid.innerHTML = '';
        root.hidden = true;
        empty.hidden = false;
      });
  })();
</script>
