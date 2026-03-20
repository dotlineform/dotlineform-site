---
layout: default
title: Moments
section: moments
permalink: /moments/
---

{% assign thumb_base = site.thumb_base | default: "" %}
{% assign thumb_moments = site.thumb_moments | default: "/assets/moments/img" %}
{% assign moments_thumb_base = thumb_base | append: thumb_moments | append: "/" %}
{%- assign moments_thumb_base_out = moments_thumb_base -%}
{%- unless moments_thumb_base contains '://' -%}
  {%- assign moments_thumb_base_out = moments_thumb_base | relative_url -%}
{%- endunless -%}

{%- capture moments_index_items -%}
[
{%- assign first_moment = true -%}
{%- for moment in site.moments -%}
  {%- if moment.published == false -%}{%- continue -%}{%- endif -%}
  {%- unless first_moment -%},{%- endunless -%}
  {%- assign moment_id = moment.moment_id | default: moment.slug -%}
  {%- assign year_number = nil -%}
  {%- assign year_text = nil -%}
  {%- if moment.date -%}
    {%- assign year_number = moment.date | date: "%Y" | plus: 0 -%}
    {%- assign year_text = moment.date | date: "%Y" -%}
  {%- endif -%}
  {
    "moment_id": {{ moment_id | jsonify }},
    "title": {{ moment.title | default: moment.slug | jsonify }},
    "year": {{ year_number | jsonify }},
    "year_display": {{ moment.date_display | default: year_text | jsonify }},
    "url": {{ moment.url | relative_url | jsonify }},
    "thumb_id": {% if moment.images and moment.images.size > 0 %}{{ moment_id | jsonify }}{% else %}null{% endif %}
  }
  {%- assign first_moment = false -%}
{%- endfor -%}
]
{%- endcapture -%}

<h1 class="index__heading visually-hidden">moments</h1>
<div id="momentsIndexRoot" data-moments-thumb-base="{{ moments_thumb_base_out | escape }}" hidden>
  <div class="seriesIndex__toolbar" aria-label="Moments view and sorting">
    <div class="seriesIndex__viewControls" role="group" aria-label="Moments view">
      <button
        class="theme-toggle seriesIndex__viewBtn"
        type="button"
        data-role="moments-index-view-btn"
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
        data-role="moments-index-view-btn"
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
    <div class="seriesIndex__sortControls" role="group" aria-label="Sort moments">
      <button
        class="theme-toggle seriesIndex__sortBtn"
        type="button"
        data-role="moments-index-sort-btn"
        data-sort-key="year"
        aria-pressed="true"
      >
        <span class="seriesIndex__sortText">year</span>
        <span class="seriesIndex__sortArrow" aria-hidden="true">↓</span>
      </button>
      <button
        class="theme-toggle seriesIndex__sortBtn"
        type="button"
        data-role="moments-index-sort-btn"
        data-sort-key="title"
        aria-pressed="false"
      >
        <span class="seriesIndex__sortText">title</span>
        <span class="seriesIndex__sortArrow" aria-hidden="true">↑</span>
      </button>
    </div>
  </div>
  <div class="index seriesIndex__list" id="momentsIndexList" aria-live="polite"></div>
  <div class="seriesGrid seriesIndex__grid" id="momentsIndexThumbGrid" aria-live="polite" hidden></div>
</div>
<p id="momentsIndexEmpty" hidden>no moments yet</p>

<script>
  (function () {
    var root = document.getElementById('momentsIndexRoot');
    var list = document.getElementById('momentsIndexList');
    var thumbGrid = document.getElementById('momentsIndexThumbGrid');
    var empty = document.getElementById('momentsIndexEmpty');
    if (!root || !list || !thumbGrid || !empty) return;

    var viewButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="moments-index-view-btn"]'));
    var sortButtons = Array.prototype.slice.call(root.querySelectorAll('[data-role="moments-index-sort-btn"]'));
    if (!viewButtons.length || !sortButtons.length) return;

    var momentsThumbBase = String(root.getAttribute('data-moments-thumb-base') || '');
    var momentsItems = {{ moments_index_items | strip_newlines }};
    var viewStorageKey = 'dlf.momentsIndex.view';
    var sortStorageKey = 'dlf.momentsIndex.sort';
    var defaultSort = {
      key: 'year',
      directions: {
        year: 'desc',
        title: 'asc'
      }
    };
    var currentView = readStoredView();
    var currentSort = readStoredSort();
    var titleCollator = (window.Intl && typeof window.Intl.Collator === 'function')
      ? new window.Intl.Collator(undefined, { numeric: true, sensitivity: 'base' })
      : null;

    function thumbUrl(momentId, size) {
      var mid = String(momentId || '').trim();
      if (!mid) return '';
      return String(momentsThumbBase || '') + mid + '-thumb-' + size + '.webp';
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
      }
    }

    function compareText(a, b) {
      var aa = String(a || '');
      var bb = String(b || '');
      if (titleCollator) return titleCollator.compare(aa, bb);
      if (aa < bb) return -1;
      if (aa > bb) return 1;
      return 0;
    }

    function compareMomentId(a, b) {
      return compareText(a && a.moment_id, b && b.moment_id);
    }

    function numericAwareSortKey(value) {
      return String(value == null ? '' : value).trim().replace(/\d+/g, function (m) {
        return m.padStart(3, '0');
      });
    }

    function titleValue(item) {
      return numericAwareSortKey(item && (item.title || item.moment_id));
    }

    function titleCompare(a, b) {
      var cmp = compareText(titleValue(a), titleValue(b));
      if (cmp !== 0) return cmp;
      return compareMomentId(a, b);
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

    function compareMoments(a, b, sortState) {
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
      return compareMomentId(a, b);
    }

    function getSortedItems(items, sortState) {
      return items.slice().sort(function (a, b) {
        return compareMoments(a, b, sortState);
      });
    }

    function cardThumbData(item) {
      var thumbId = String((item && item.thumb_id) || '').trim();
      return {
        thumb_96: thumbUrl(thumbId, '96'),
        thumb_192: thumbUrl(thumbId, '192')
      };
    }

    function renderMomentCard(item) {
      var href = String((item && item.url) || '').trim();
      var thumbData = cardThumbData(item);
      var thumb = thumbData.thumb_96;
      var title = String((item && item.title) || (item && item.moment_id) || '');
      var yearTxt = yearDisplayText(item);

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
      } else {
        var placeholder = document.createElement('span');
        placeholder.className = 'seriesIndexItem__img';
        placeholder.setAttribute('aria-hidden', 'true');
        a.appendChild(placeholder);
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

    function renderMomentGridItem(item) {
      var href = String((item && item.url) || '').trim();
      var thumbData = cardThumbData(item);
      var thumb96 = String(thumbData.thumb_96 || '');
      var thumb192 = String(thumbData.thumb_192 || thumb96);
      var title = String((item && item.title) || (item && item.moment_id) || '');

      var a = document.createElement('a');
      a.className = 'seriesGrid__item';
      a.href = href;
      a.setAttribute('aria-label', title);
      a.title = title;

      if (thumb96) {
        var img = document.createElement('img');
        img.className = 'seriesGrid__img';
        img.src = thumb96;
        img.srcset = thumb96 + ' 96w, ' + thumb192 + ' 192w';
        img.sizes = '(min-width: 1200px) 10vw, (min-width: 700px) 14vw, 22vw';
        img.width = 96;
        img.height = 96;
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
        var label = key === 'title' ? 'title' : 'year';
        var arrow = direction === 'desc' ? '↓' : '↑';

        button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        button.setAttribute('aria-label', 'Sort by ' + label + ' ' + (direction === 'desc' ? 'descending' : 'ascending'));
        if (labelEl) labelEl.textContent = label;
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
      var sortedItems = getSortedItems(momentsItems, currentSort);
      list.innerHTML = '';
      thumbGrid.innerHTML = '';
      if (!sortedItems.length) return;

      var frag = document.createDocumentFragment();
      var i;

      if (currentView === 'grid') {
        for (i = 0; i < sortedItems.length; i += 1) {
          frag.appendChild(renderMomentGridItem(sortedItems[i]));
        }
        thumbGrid.appendChild(frag);
      } else {
        for (i = 0; i < sortedItems.length; i += 1) {
          frag.appendChild(renderMomentCard(sortedItems[i]));
        }
        list.appendChild(frag);
      }
    }

    viewButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var nextView = normalizeView(button.getAttribute('data-view'));
        if (nextView === currentView) return;
        currentView = nextView;
        persistView(currentView);
        updateViewUi();
        renderCurrentView();
      });
    });

    sortButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var key = normalizeSortKey(button.getAttribute('data-sort-key'));
        if (key === currentSort.key) {
          currentSort.directions[key] = currentSort.directions[key] === 'desc' ? 'asc' : 'desc';
        } else {
          currentSort.key = key;
        }
        currentSort = sanitizeSortState(currentSort);
        persistSort(currentSort);
        updateSortUi();
        renderCurrentView();
      });
    });

    if (!Array.isArray(momentsItems) || !momentsItems.length) {
      root.hidden = true;
      empty.hidden = false;
      return;
    }

    root.hidden = false;
    empty.hidden = true;
    updateSortUi();
    updateViewUi();
    renderCurrentView();
  })();
</script>
