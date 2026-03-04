---
layout: default
title: works
section: series
permalink: /series/
---

<h1 class="index__heading visually-hidden">works</h1>
<div class="index" id="seriesIndexGrid" aria-live="polite"></div>
<p id="seriesIndexEmpty" hidden>no series yet</p>

<script>
  (function () {
    var grid = document.getElementById('seriesIndexGrid');
    var empty = document.getElementById('seriesIndexEmpty');
    if (!grid || !empty) return;

    var baseurl = {{ site.baseurl | default: '' | jsonify }};
    var dataUrl = baseurl + '/assets/data/series_index.json';

    function withBase(path) {
      var s = String(path || '').trim();
      if (!s) return '';
      if (/^https?:\/\//i.test(s)) return s;
      if (s.charAt(0) === '/') return baseurl + s;
      return baseurl + '/' + s.replace(/^\/+/, '');
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

    function cardHref(s) {
      var sid = String((s && s.series_id) || '').trim();
      var works = Array.isArray(s && s.works) ? s.works : [];
      if (works.length === 1) {
        return baseurl + '/works/' + encodeURIComponent(String(works[0])) + '/';
      }
      return baseurl + '/series/' + encodeURIComponent(sid) + '/';
    }

    function cardThumb(s) {
      var thumb = (s && s.thumb && typeof s.thumb === 'object') ? s.thumb : null;
      if (thumb && thumb.thumb_96) return withBase(thumb.thumb_96);
      var thumbId = String((thumb && thumb.work_id) || '').trim();
      if (!thumbId) {
        var works = Array.isArray(s && s.works) ? s.works : [];
        if (works.length) thumbId = String(works[works.length - 1] || '').trim();
      }
      if (!thumbId) return '';
      return withBase('/assets/works/img/' + thumbId + '-thumb-96.webp');
    }

    function renderSeriesCard(s) {
      var href = cardHref(s);
      var thumb = cardThumb(s);
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

    fetch(dataUrl, { cache: 'default' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (payload) {
        var seriesMap = (payload && payload.series && typeof payload.series === 'object') ? payload.series : {};
        var items = Object.keys(seriesMap).map(function (sid) { return seriesMap[sid]; }).filter(Boolean);
        items.sort(compareSeries);

        grid.innerHTML = '';
        if (!items.length) {
          empty.hidden = false;
          return;
        }
        empty.hidden = true;

        var frag = document.createDocumentFragment();
        for (var i = 0; i < items.length; i += 1) {
          frag.appendChild(renderSeriesCard(items[i]));
        }
        grid.appendChild(frag);
      })
      .catch(function () {
        grid.innerHTML = '';
        empty.hidden = false;
      });
  })();
</script>
