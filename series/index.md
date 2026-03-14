---
layout: default
title: works
section: series
permalink: /series/
---

<h1 class="index__heading visually-hidden">works</h1>
<div id="seriesIndexRoot" hidden>
  <div class="seriesIndex__toolbar" role="group" aria-label="Series view">
    <button
      class="theme-toggle seriesIndex__viewBtn"
      type="button"
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
  <div class="index seriesIndex__list" id="seriesIndexList" aria-live="polite"></div>
  <div class="seriesGrid seriesIndex__grid" id="seriesIndexThumbGrid" aria-live="polite" hidden></div>
</div>
<p id="seriesIndexEmpty" hidden>no series yet</p>

<script>
  (function () {
    var root = document.getElementById('seriesIndexRoot');
    var list = document.getElementById('seriesIndexList');
    var thumbGrid = document.getElementById('seriesIndexThumbGrid');
    var viewButtons = Array.prototype.slice.call(document.querySelectorAll('.seriesIndex__viewBtn'));
    var empty = document.getElementById('seriesIndexEmpty');
    if (!root || !list || !thumbGrid || !viewButtons.length || !empty) return;

    var baseurl = {{ site.baseurl | default: '' | jsonify }};
    var dataUrl = baseurl + '/assets/data/series_index.json';
    var params = new URLSearchParams(window.location.search);
    var currentView = normalizeView(params.get('view'));
    var seriesItems = [];

    function withBase(path) {
      var s = String(path || '').trim();
      if (!s) return '';
      if (/^https?:\/\//i.test(s)) return s;
      if (s.charAt(0) === '/') return baseurl + s;
      return baseurl + '/' + s.replace(/^\/+/, '');
    }

    function normalizeView(value) {
      return String(value || '').trim().toLowerCase() === 'grid' ? 'grid' : 'list';
    }

    function persistView(view) {
      var next = new URLSearchParams(window.location.search);
      if (view === 'grid') {
        next.set('view', 'grid');
      } else {
        next.delete('view');
      }
      var query = next.toString();
      var nextUrl = window.location.pathname + (query ? ('?' + query) : '') + window.location.hash;
      window.history.replaceState({}, '', nextUrl);
    }

    function yearValue(v) {
      var n = Number(v);
      if (Number.isFinite(n)) return n;
      return Number.NEGATIVE_INFINITY;
    }

    function compareSeries(a, b) {
      var ay = yearValue(a && a.year);
      var by = yearValue(b && b.year);
      if (ay !== by) return by - ay;
      var at = String((a && (a.title_sort || a.title || a.series_id)) || '');
      var bt = String((b && (b.title_sort || b.title || b.series_id)) || '');
      if (at < bt) return -1;
      if (at > bt) return 1;
      var as = String((a && a.series_id) || '');
      var bs = String((b && b.series_id) || '');
      if (as < bs) return -1;
      if (as > bs) return 1;
      return 0;
    }

    function withReturnView(url) {
      var q = new URLSearchParams();
      q.set('from', 'series_index');
      q.set('return_view', currentView);
      return url + '?' + q.toString();
    }

    function cardHref(s) {
      var sid = String((s && s.series_id) || '').trim();
      var works = Array.isArray(s && s.works) ? s.works : [];
      if (works.length === 1) {
        return withReturnView(baseurl + '/works/' + encodeURIComponent(String(works[0])) + '/');
      }
      return withReturnView(baseurl + '/series/' + encodeURIComponent(sid) + '/');
    }

    function cardThumbData(s) {
      var thumb = (s && s.thumb && typeof s.thumb === 'object') ? s.thumb : null;
      var thumb96 = thumb && thumb.thumb_96 ? withBase(thumb.thumb_96) : '';
      var thumb192 = thumb && thumb.thumb_192 ? withBase(thumb.thumb_192) : '';
      var thumbId = String((thumb && thumb.work_id) || '').trim();
      if (!thumbId) {
        var works = Array.isArray(s && s.works) ? s.works : [];
        if (works.length) thumbId = String(works[works.length - 1] || '').trim();
      }
      if (!thumb96 && thumbId) thumb96 = withBase('/assets/works/img/' + thumbId + '-thumb-96.webp');
      if (!thumb192 && thumbId) thumb192 = withBase('/assets/works/img/' + thumbId + '-thumb-192.webp');
      return {
        thumb_96: thumb96,
        thumb_192: thumb192,
        thumb_id: thumbId
      };
    }

    function renderSeriesCard(s) {
      var href = cardHref(s);
      var thumbData = cardThumbData(s);
      var thumb = thumbData.thumb_96;
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
      var thumb96 = String(thumbData.thumb_96 || '');
      var thumb192 = String(thumbData.thumb_192 || thumb96);
      var title = String((s && s.title) || (s && s.series_id) || '');

      var a = document.createElement('a');
      a.className = 'seriesGrid__item';
      a.href = href;
      a.setAttribute('aria-label', title);

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

    function updateViewUi() {
      var showingGrid = currentView === 'grid';
      list.hidden = showingGrid;
      thumbGrid.hidden = !showingGrid;
      viewButtons.forEach(function (button) {
        var buttonView = String(button.getAttribute('data-view') || '').trim().toLowerCase();
        var active = buttonView === currentView;
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
        button.classList.toggle('is-active', active);
      });
    }

    function renderCurrentView() {
      list.innerHTML = '';
      thumbGrid.innerHTML = '';
      if (!seriesItems.length) return;

      var frag = document.createDocumentFragment();
      var i;

      if (currentView === 'grid') {
        for (i = 0; i < seriesItems.length; i += 1) {
          frag.appendChild(renderSeriesGridItem(seriesItems[i]));
        }
        thumbGrid.appendChild(frag);
      } else {
        for (i = 0; i < seriesItems.length; i += 1) {
          frag.appendChild(renderSeriesCard(seriesItems[i]));
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

    fetch(dataUrl, { cache: 'default' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (payload) {
        var seriesMap = (payload && payload.series && typeof payload.series === 'object') ? payload.series : {};
        seriesItems = Object.keys(seriesMap).map(function (sid) { return seriesMap[sid]; }).filter(Boolean);
        seriesItems.sort(compareSeries);

        if (!seriesItems.length) {
          root.hidden = true;
          empty.hidden = false;
          return;
        }

        empty.hidden = true;
        root.hidden = false;
        renderCurrentView();
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
