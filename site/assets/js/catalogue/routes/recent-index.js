import {
  catalogueIndexUrl,
  recentIndexUrl,
  seriesIndexUrl,
  trimBaseurl,
  workUrl
} from '../shared/catalogue-urls.js';
import { fetchJson } from '../shared/fetch-json.js';
import { normalizePositiveSizes, text } from '../shared/text.js';
import { thumbUrl } from '../shared/thumbnails.js';

var root = document.getElementById('recentIndexRoot');
var list = document.getElementById('recentIndexList');
var empty = document.getElementById('recentIndexEmpty');
if (root && list && empty) bootRecentIndexRoute(root, list, empty);

function bootRecentIndexRoute(rootNode, listNode, emptyNode) {
  var baseurl = trimBaseurl(rootNode.getAttribute('data-baseurl'));
  var thumbWorksBase = text(rootNode.getAttribute('data-thumb-works-base'));
  var thumbSizes = normalizePositiveSizes(jsonAttribute(rootNode, 'data-thumb-sizes', []), [96, 192]);
  var primaryThumbSize = thumbSizes[0];
  var thumbSuffix = text(rootNode.getAttribute('data-thumb-suffix')) || 'thumb';
  var assetFormat = text(rootNode.getAttribute('data-asset-format')) || 'webp';
  var monthNames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];

  function jsonAttribute(node, name, fallback) {
    try {
      return JSON.parse(node.getAttribute(name) || '[]');
    } catch (err) {
      return fallback;
    }
  }

  function recentThumbUrl(thumbId) {
    return thumbUrl(thumbWorksBase, thumbId, thumbSuffix, primaryThumbSize, assetFormat);
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
        return workUrl(String(works[0]), baseurl, { from: 'recent' });
      }
      return catalogueIndexUrl(baseurl, { series: targetId, from: 'recent' });
    }
    return workUrl(targetId, baseurl, { from: 'recent' });
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
    var thumb = recentThumbUrl(entry && entry.thumb_id);

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
    fetchJson(recentIndexUrl(baseurl)),
    fetchJson(seriesIndexUrl(baseurl)).catch(function () { return {}; })
  ])
    .then(function (responses) {
      var payload = responses[0] || {};
      var seriesPayload = responses[1] || {};
      var seriesMap = seriesPayload && typeof seriesPayload.series === 'object' ? seriesPayload.series : {};
      var entries = payload && Array.isArray(payload.entries) ? payload.entries.slice() : [];
      entries.sort(compareEntries);
      entries = entries.slice(0, 50);

      listNode.innerHTML = '';
      entries.forEach(function (entry) {
        var item = renderEntry(entry, seriesMap);
        if (item) listNode.appendChild(item);
      });

      rootNode.hidden = !listNode.children.length;
      emptyNode.hidden = listNode.children.length > 0;
    })
    .catch(function () {
      rootNode.hidden = true;
      emptyNode.hidden = false;
    });
}
