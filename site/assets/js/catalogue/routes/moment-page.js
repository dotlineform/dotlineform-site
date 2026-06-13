import { renderPrimaryMedia } from '../components/primary-media.js';
import { renderProseContent } from '../components/prose-content.js';
import {
  catalogueIndexUrl,
  momentPayloadUrl,
  momentUrl,
  momentsIndexUrl,
  parseRouteState,
  trimBaseurl
} from '../shared/catalogue-urls.js';
import { fetchJson } from '../shared/fetch-json.js';
import { normalizePositiveSizes, text, toNumber, toPositiveInteger } from '../shared/text.js';
import { thumbSrcset, thumbUrl } from '../shared/thumbnails.js';

var root = document.getElementById('momentPageRoot');
if (root) bootMomentRoute(root);

function jsonAttribute(node, name, fallback) {
  try {
    return JSON.parse(node.getAttribute(name) || '[]');
  } catch (err) {
    return fallback;
  }
}

function parseDateValue(raw) {
  var dateText = text(raw);
  if (!dateText) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateText)) {
    return new Date(dateText + 'T00:00:00Z');
  }
  var parsed = new Date(dateText);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatDate(meta) {
  var display = text(meta && meta.date_display);
  if (display) return display;
  var parsed = parseDateValue(meta && meta.date);
  if (!parsed) return '';
  try {
    return new Intl.DateTimeFormat('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      timeZone: 'UTC'
    }).format(parsed);
  } catch (err) {
    return text(meta && meta.date);
  }
}

function normalizeImages(raw) {
  if (!Array.isArray(raw)) return [];
  return raw.map(function (item) {
    if (!item || typeof item !== 'object') return null;
    var file = text(item.file);
    if (!file) return null;
    return {
      file: file,
      alt: text(item.alt),
      caption: text(item.caption)
    };
  }).filter(Boolean);
}

function renderTextError(container, message) {
  if (!container) return;
  container.innerHTML = '';
  var paragraph = document.createElement('p');
  paragraph.textContent = message;
  container.appendChild(paragraph);
}

function bootMomentRoute(rootNode) {
  var baseurl = trimBaseurl(rootNode.getAttribute('data-baseurl'));
  var routeState = parseRouteState(window.location);
  var momentId = text(rootNode.getAttribute('data-moment-id')) || text(routeState.moment);
  var imgBase = String(rootNode.getAttribute('data-img-base') || '');
  var primarySuffix = text(rootNode.getAttribute('data-primary-suffix')) || 'primary';
  var assetFormat = text(rootNode.getAttribute('data-asset-format')) || 'webp';
  var displayWidth = toPositiveInteger(rootNode.getAttribute('data-primary-display-width')) || 1600;
  var loadingText = String(rootNode.getAttribute('data-loading-text') || 'loading...');
  var unavailableText = String(rootNode.getAttribute('data-unavailable-text') || 'info not available');
  var renderWidths = normalizePositiveSizes(jsonAttribute(rootNode, 'data-primary-render-widths', []), [800, 1200, 1600]);
  var backNav = document.getElementById('momentBackNav');
  var backLink = document.getElementById('momentBackLink');

  function normalizeMoment(raw) {
    var source = raw && typeof raw === 'object' ? raw : {};
    var normalized = {};
    normalized.moment_id = text(source.moment_id) || momentId;
    normalized.title = text(source.title) || normalized.moment_id || 'Untitled';
    normalized.date = text(source.date);
    normalized.date_display = text(source.date_display);
    normalized.images = normalizeImages(source.images);
    normalized.width_px = toNumber(source.width_px);
    normalized.height_px = toNumber(source.height_px);
    if (!Number.isFinite(normalized.width_px) || normalized.width_px <= 0) normalized.width_px = null;
    if (!Number.isFinite(normalized.height_px) || normalized.height_px <= 0) normalized.height_px = null;
    return normalized;
  }

  function deriveStem(meta, hero) {
    var fallbackStem = text(hero && hero.file).replace(/^\/+/, '').split('/').pop().split('.')[0];
    return text(meta && meta.moment_id) || fallbackStem;
  }

  function buildImageSources(meta, hero) {
    var file = text(hero && hero.file);
    if (!file) return null;
    if (file.indexOf('://') !== -1) {
      return {
        src: file,
        srcset: '',
        external: true
      };
    }

    var stem = deriveStem(meta, hero);
    if (!stem) return null;
    return {
      src: thumbUrl(imgBase, stem, primarySuffix, displayWidth, assetFormat),
      srcset: thumbSrcset(imgBase, stem, renderWidths, primarySuffix, assetFormat),
      external: false
    };
  }

  function applyMetadata(meta) {
    var normalized = normalizeMoment(meta);
    var titleEl = document.getElementById('momentTitleText');
    var dateEl = document.getElementById('momentDateText');
    var heroEl = document.getElementById('momentHero');

    if (titleEl) titleEl.textContent = normalized.title;
    if (normalized.title) document.title = normalized.title + ' | dotlineform';

    if (dateEl) {
      var formattedDate = formatDate(normalized);
      if (formattedDate) {
        dateEl.textContent = formattedDate;
        dateEl.hidden = false;
      } else {
        dateEl.textContent = '';
        dateEl.hidden = true;
      }
    }

    if (!heroEl) return;

    var hero = normalized.images.length ? normalized.images[0] : null;
    if (!hero) {
      renderPrimaryMedia({
        rootElement: heroEl,
        hidden: true
      });
      return;
    }

    var sources = buildImageSources(normalized, hero);
    if (!sources) {
      renderPrimaryMedia({
        rootElement: heroEl,
        hidden: true
      });
      return;
    }

    renderPrimaryMedia({
      rootElement: heroEl,
      image: {
        id: 'momentHeroImg',
        src: sources.src,
        srcset: sources.external ? '' : sources.srcset,
        sizes: sources.external ? '' : '(max-width: 800px) 100vw, 72ch',
        width: normalized.width_px,
        height: normalized.height_px,
        alt: hero.alt || normalized.title || 'Moment',
        loading: 'eager',
        decoding: 'async',
        fetchPriority: 'high'
      },
      caption: {
        id: 'momentHeroCaption',
        text: hero.caption
      }
    });
  }

  function applyContentHtml(html) {
    renderProseContent({
      rootElement: document.getElementById('momentBody'),
      html: typeof html === 'string' ? html : ''
    });
  }

  function showLoadError() {
    renderTextError(document.getElementById('momentBody'), unavailableText);
  }

  function setBackLinkVisible(visible) {
    if (backLink) {
      backLink.setAttribute('href', catalogueIndexUrl(baseurl, { mode: 'moments' }));
    }
    if (backNav) backNav.hidden = !visible;
  }

  function formatBrowseDate(row) {
    return formatDate({
      date: row && row.date,
      date_display: row && row.date_display
    });
  }

  function renderBrowse(payload) {
    var titleEl = document.getElementById('momentTitleText');
    var dateEl = document.getElementById('momentDateText');
    var heroEl = document.getElementById('momentHero');
    var body = document.getElementById('momentBody');
    setBackLinkVisible(false);
    if (titleEl) titleEl.textContent = 'moments';
    document.title = 'moments | dotlineform';
    if (dateEl) dateEl.hidden = true;
    if (heroEl) {
      renderPrimaryMedia({
        rootElement: heroEl,
        hidden: true
      });
    }
    if (!body) return;

    var moments = payload && payload.moments && typeof payload.moments === 'object' ? payload.moments : {};
    var rows = Object.keys(moments).map(function (id) {
      var row = moments[id] && typeof moments[id] === 'object' ? moments[id] : {};
      return {
        id: text(row.moment_id) || id,
        title: text(row.title) || id,
        date: text(row.date),
        date_display: text(row.date_display)
      };
    }).sort(function (a, b) {
      var ad = text(a.date);
      var bd = text(b.date);
      if (ad !== bd) return ad < bd ? 1 : -1;
      return a.title.localeCompare(b.title);
    });

    if (!rows.length) {
      renderTextError(body, unavailableText);
      return;
    }

    var list = document.createElement('div');
    list.className = 'index';
    rows.forEach(function (row) {
      var link = document.createElement('a');
      link.className = 'index__item';
      link.href = momentUrl(row.id, baseurl);

      var title = document.createElement('span');
      title.className = 'index__title';
      title.textContent = row.title;
      link.appendChild(title);

      var dateText = formatBrowseDate(row);
      if (dateText) {
        var meta = document.createElement('span');
        meta.className = 'index__meta';
        meta.textContent = dateText;
        link.appendChild(meta);
      }

      list.appendChild(link);
    });

    body.innerHTML = '';
    body.appendChild(list);
  }

  if (!momentId) {
    applyMetadata({ title: loadingText });
    fetchJson(momentsIndexUrl(baseurl))
      .then(renderBrowse)
      .catch(function () {
        applyMetadata({ title: unavailableText });
        showLoadError();
      });
    return;
  }

  applyMetadata({ moment_id: momentId, title: loadingText });
  setBackLinkVisible(true);

  fetchJson(momentPayloadUrl(momentId, baseurl))
    .then(function (payload) {
      var moment = (payload && payload.moment && typeof payload.moment === 'object') ? payload.moment : null;
      var contentHtml = payload && typeof payload.content_html === 'string' ? payload.content_html : null;
      if (!moment || contentHtml == null) throw new Error('Invalid moment payload');

      applyMetadata(moment);
      applyContentHtml(contentHtml);
    })
    .catch(function () {
      applyMetadata({ moment_id: momentId, title: unavailableText });
      showLoadError();
    });
}
