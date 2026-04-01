---
layout: default
title: recently added
permalink: /recent/
section: works
---

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

<div
  class="index recentIndex"
  id="recentIndexRoot"
  data-baseurl="{{ site.baseurl | default: '' }}"
  data-thumb-works-base="{{ thumb_works_base_out | escape }}"
  data-thumb-sizes="{{ thumb_sizes | jsonify | escape }}"
  data-thumb-suffix="{{ thumb_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  hidden
>
  <h1 class="index__heading">recently added</h1>
  <ul class="recentIndex__list" id="recentIndexList"></ul>
  <nav class="page__nav">
    <a class="page__back" href="{{ '/series/' | relative_url }}">← works</a>
  </nav>
</div>
<p id="recentIndexEmpty" hidden>nothing recently added yet</p>

<script>
  (function () {
    var root = document.getElementById('recentIndexRoot');
    var list = document.getElementById('recentIndexList');
    var empty = document.getElementById('recentIndexEmpty');
    if (!root || !list || !empty) return;

    var baseurl = String(root.getAttribute('data-baseurl') || '').replace(/\/$/, '');
    var thumbWorksBase = String(root.getAttribute('data-thumb-works-base') || '').trim();
    var thumbSizes = [];
    try {
      thumbSizes = JSON.parse(root.getAttribute('data-thumb-sizes') || '[]');
    } catch (err) {
      thumbSizes = [];
    }
    thumbSizes = Array.isArray(thumbSizes) ? thumbSizes.map(function (value) {
      var n = Number(value);
      return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
    }).filter(function (value) { return value > 0; }) : [];
    if (!thumbSizes.length) thumbSizes = [96, 192];
    var primaryThumbSize = thumbSizes[0];
    var thumbSuffix = String(root.getAttribute('data-thumb-suffix') || 'thumb').trim() || 'thumb';
    var assetFormat = String(root.getAttribute('data-asset-format') || 'webp').trim() || 'webp';
    var recentIndexUrl = baseurl + '/assets/data/recent_index.json';
    var seriesIndexUrl = baseurl + '/assets/data/series_index.json';
    var monthNames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];

    function fetchJson(url) {
      return fetch(url, { cache: 'default' })
        .then(function (response) {
          if (!response.ok) throw new Error('HTTP ' + response.status);
          return response.json();
        });
    }

    function text(value) {
      return String(value == null ? '' : value).trim();
    }

    function thumbUrl(thumbId) {
      var id = text(thumbId);
      if (!id) return '';
      return thumbWorksBase + id + '-' + thumbSuffix + '-' + String(primaryThumbSize) + '.' + assetFormat;
    }

    function formatDate(value) {
      var raw = text(value);
      var match = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
      if (!match) return raw;
      var year = Number(match[1]);
      var month = Number(match[2]);
      var day = Number(match[3]);
      if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day) || month < 1 || month > 12) {
        return raw;
      }
      return String(day) + ' ' + monthNames[month - 1] + ' ' + String(year);
    }

    function entryHref(entry, seriesMap) {
      var kind = text(entry && entry.kind).toLowerCase();
      var targetId = text(entry && entry.target_id);
      if (!targetId) return '';
      if (kind === 'series') {
        var seriesItem = seriesMap && typeof seriesMap === 'object' ? seriesMap[targetId] : null;
        var works = Array.isArray(seriesItem && seriesItem.works) ? seriesItem.works : [];
        if (works.length === 1) {
          return baseurl + '/works/' + encodeURIComponent(String(works[0])) + '/?from=recent';
        }
        return baseurl + '/series/' + encodeURIComponent(targetId) + '/?from=recent';
      }
      return baseurl + '/works/' + encodeURIComponent(targetId) + '/?from=recent';
    }

    function compareEntries(a, b) {
      var dateCmp = text(b && b.published_date).localeCompare(text(a && a.published_date));
      if (dateCmp !== 0) return dateCmp;
      var recordedCmp = text(b && b.recorded_at_utc).localeCompare(text(a && a.recorded_at_utc));
      if (recordedCmp !== 0) return recordedCmp;
      return text(a && a.title).localeCompare(text(b && b.title), undefined, { numeric: true, sensitivity: 'base' });
    }

    function renderEntry(entry, seriesMap) {
      var href = entryHref(entry, seriesMap);
      if (!href) return null;

      var title = text(entry && entry.title) || text(entry && entry.target_id);
      var caption = text(entry && entry.caption);
      var dateText = formatDate(entry && entry.published_date);
      var thumb = thumbUrl(entry && entry.thumb_id);

      var item = document.createElement('li');
      var link = document.createElement('a');
      link.className = 'recentIndexItem';
      link.href = href;
      link.title = title;

      var dateEl = document.createElement('div');
      dateEl.className = 'recentIndexItem__date';
      dateEl.textContent = dateText;
      link.appendChild(dateEl);

      if (thumb) {
        var img = document.createElement('img');
        img.className = 'recentIndexItem__img';
        img.src = thumb;
        img.width = primaryThumbSize;
        img.height = primaryThumbSize;
        img.alt = title;
        img.loading = 'lazy';
        img.decoding = 'async';
        link.appendChild(img);
      } else {
        var placeholder = document.createElement('span');
        placeholder.className = 'recentIndexItem__img';
        placeholder.setAttribute('aria-hidden', 'true');
        link.appendChild(placeholder);
      }

      var meta = document.createElement('div');
      meta.className = 'recentIndexItem__meta';

      var titleEl = document.createElement('div');
      titleEl.className = 'recentIndexItem__title';
      titleEl.textContent = title;
      meta.appendChild(titleEl);

      var captionEl = document.createElement('div');
      captionEl.className = 'recentIndexItem__caption';
      captionEl.textContent = caption;
      meta.appendChild(captionEl);

      link.appendChild(meta);
      item.appendChild(link);
      return item;
    }

    Promise.all([
      fetchJson(recentIndexUrl),
      fetchJson(seriesIndexUrl).catch(function () { return {}; })
    ])
      .then(function (responses) {
        var payload = responses[0] || {};
        var seriesPayload = responses[1] || {};
        var seriesMap = seriesPayload && typeof seriesPayload.series === 'object' ? seriesPayload.series : {};
        var entries = payload && Array.isArray(payload.entries) ? payload.entries.slice() : [];
        entries.sort(compareEntries);
        entries = entries.slice(0, 50);

        list.innerHTML = '';
        entries.forEach(function (entry) {
          var item = renderEntry(entry, seriesMap);
          if (item) list.appendChild(item);
        });

        root.hidden = !list.children.length;
        empty.hidden = list.children.length > 0;
      })
      .catch(function () {
        root.hidden = true;
        empty.hidden = false;
      });
  })();
</script>
