import { renderPrimaryMedia } from '../components/primary-media.js';
import { createThumbnailGridList } from '../components/thumbnail-grid-list.js';
import {
  buildPath,
  catalogueIndexUrl,
  parseRouteState,
  trimBaseurl,
  workDetailUrl,
  workPayloadUrl
} from '../shared/catalogue-urls.js';
import { fetchJson } from '../shared/fetch-json.js';
import { normalizePositiveSizes, slug, text, toNumber, toPositiveInteger } from '../shared/text.js';
import { thumbnailImageData } from '../shared/thumbnails.js';

var root = document.getElementById('selectedWorkRoot');
if (root) {
  var routeState = parseRouteState(window.location);
  var workId = text(routeState.work);
  if (workId) bootSelectedWorkRoute(root, routeState, workId);
}

function jsonAttribute(node, name, fallback) {
  try {
    return JSON.parse(node.getAttribute(name) || '[]');
  } catch (err) {
    return fallback;
  }
}

function setText(id, value) {
  var node = document.getElementById(id);
  if (node) node.textContent = value;
}

function setRow(rowId, textId, value) {
  var row = document.getElementById(rowId);
  if (!row) return;
  var valueText = text(value);
  setText(textId, valueText);
  row.hidden = !valueText;
}

function isAbsoluteUrl(value) {
  return /^(https?:)?\/\//i.test(value);
}

function safeHref(value) {
  var href = text(value);
  if (!href) return '';
  if (/^(https?:|mailto:)/i.test(href)) return href;
  if (href.charAt(0) === '/' || href.charAt(0) === '#') return href;
  return '';
}

function encodedPath(value) {
  return text(value).split('/').map(function (part) {
    return encodeURIComponent(part);
  }).join('/');
}

function arrayFromPayload(payload, work, key) {
  if (work && Array.isArray(work[key])) return work[key];
  if (payload && Array.isArray(payload[key])) return payload[key];
  return [];
}

function dimensionsText(meta) {
  var mediumType = text(meta && meta.medium_type).toLowerCase();
  if (mediumType === 'music') return '';
  var h = toNumber(meta && meta.height_cm);
  var w = toNumber(meta && meta.width_cm);
  var d = toNumber(meta && meta.depth_cm);
  if (h != null && w != null) {
    var base = String(h) + ' \u00d7 ' + String(w);
    if (d != null && d > 0) base += ' \u00d7 ' + String(d);
    return base + ' cm';
  }
  if (h != null) return String(h) + ' cm';
  if (w != null) return String(w) + ' cm';
  return '';
}

function appendSeparatedLink(parent, link, isFirst) {
  if (!isFirst) parent.appendChild(document.createTextNode(', '));
  parent.appendChild(link);
}

function renderMetaLinks(rowId, labelId, linksId, singular, plural, entries, hrefForEntry) {
  var row = document.getElementById(rowId);
  var label = document.getElementById(labelId);
  var links = document.getElementById(linksId);
  if (!row || !label || !links) return;

  var validEntries = (Array.isArray(entries) ? entries : []).map(function (entry) {
    var href = hrefForEntry(entry);
    var labelText = text(entry && entry.label) || text(entry && entry.filename) || text(entry && entry.url);
    return href && labelText ? { href: href, label: labelText } : null;
  }).filter(Boolean);

  label.textContent = validEntries.length === 1 ? singular : plural;
  links.innerHTML = '';
  validEntries.forEach(function (entry, index) {
    var link = document.createElement('a');
    link.href = entry.href;
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = entry.label;
    appendSeparatedLink(links, link, index === 0);
  });
  row.hidden = !validEntries.length;
}

function bootSelectedWorkRoute(rootNode, routeState, workId) {
  var baseurl = trimBaseurl(rootNode.getAttribute('data-baseurl'));
  var worksImgBase = text(rootNode.getAttribute('data-works-img-base'));
  var worksFilesBase = text(rootNode.getAttribute('data-works-files-base'));
  var detailsThumbBase = text(rootNode.getAttribute('data-details-thumb-base'));
  var primaryDisplayWidth = toPositiveInteger(rootNode.getAttribute('data-primary-display-width')) || 1200;
  var primaryFullWidth = toPositiveInteger(rootNode.getAttribute('data-primary-full-width')) || primaryDisplayWidth;
  var primarySuffix = text(rootNode.getAttribute('data-primary-suffix')) || 'primary';
  var detailThumbSuffix = text(rootNode.getAttribute('data-detail-thumb-suffix')) || 'thumb';
  var assetFormat = text(rootNode.getAttribute('data-asset-format')) || 'webp';
  var unavailableText = text(rootNode.getAttribute('data-unavailable-text')) || 'info not available';
  var renderWidths = normalizePositiveSizes(jsonAttribute(rootNode, 'data-primary-render-widths', []), [primaryDisplayWidth]);
  var detailThumbSizes = normalizePositiveSizes(jsonAttribute(rootNode, 'data-detail-thumb-sizes', []), [96, 192]);

  function workImageUrl(id, width) {
    return worksImgBase + encodeURIComponent(id) + '-' + primarySuffix + '-' + String(width) + '.' + assetFormat;
  }

  function workFileUrl(filename) {
    var name = text(filename);
    if (!name) return '';
    if (isAbsoluteUrl(name)) return name;
    if (name.charAt(0) === '/') return name;
    return worksFilesBase.replace(/\/$/, '') + '/' + encodedPath(name);
  }

  function renderDownloadsAndLinks(payload, work) {
    renderMetaLinks(
      'selectedWorkDownloadsRow',
      'selectedWorkDownloadsLabel',
      'selectedWorkDownloadsLinks',
      'download',
      'downloads',
      arrayFromPayload(payload, work, 'downloads'),
      function (entry) { return workFileUrl(entry && entry.filename); }
    );
    renderMetaLinks(
      'selectedWorkLinksRow',
      'selectedWorkLinksLabel',
      'selectedWorkLinksLinks',
      'link',
      'links',
      arrayFromPayload(payload, work, 'links'),
      function (entry) { return safeHref(entry && entry.url); }
    );
  }

  function updateBackLink() {
    var link = document.getElementById('pageBackLink');
    if (!link) return;
    if (routeState.series) {
      link.textContent = '\u2190 series';
      link.href = catalogueIndexUrl(baseurl, { series: routeState.series, seriesPage: routeState.seriesPage });
      return;
    }
    if (routeState.from === 'recent') {
      link.textContent = '\u2190 recently added';
      link.href = buildPath(baseurl, '/recent/');
      return;
    }
    link.textContent = '\u2190 works';
    link.href = catalogueIndexUrl(baseurl);
  }

  function renderMedia(work) {
    var media = document.getElementById('selectedWorkMedia');
    if (!media) return;
    var displaySrc = workImageUrl(workId, primaryDisplayWidth);
    var fullSrc = workImageUrl(workId, primaryFullWidth);
    var srcset = renderWidths.map(function (width) {
      return workImageUrl(workId, width) + ' ' + String(width) + 'w';
    }).join(', ');
    var widthPx = toNumber(work && work.width_px);
    var heightPx = toNumber(work && work.height_px);
    renderPrimaryMedia({
      rootElement: media,
      aspectRatio: widthPx && heightPx ? String(widthPx) + ' / ' + String(heightPx) : '',
      link: {
        id: 'selectedWorkMediaLink',
        href: fullSrc,
        target: '_blank',
        rel: 'noopener'
      },
      image: {
        id: 'selectedWorkImg',
        src: displaySrc,
        srcset: srcset,
        sizes: '(max-width: 800px) 100vw, 72ch',
        alt: text(work && work.title) || workId,
        loading: 'eager',
        decoding: 'async',
        fetchPriority: 'high'
      }
    });
  }

  function detailHref(uid, workTitle, sectionId) {
    return workDetailUrl(uid, baseurl, {
      from_work: workId,
      from_work_title: workTitle,
      section: sectionId,
      details_section: sectionId,
      details_page: routeState.detailsPage > 0 ? routeState.detailsPage : '',
      series: routeState.series,
      series_page: routeState.seriesPage
    });
  }

  function detailItem(detail, workTitle, sectionId) {
    var uid = text(detail && detail.detail_uid);
    if (!uid) return null;
    var title = text(detail && detail.title) || uid;
    return {
      id: uid,
      title: title,
      href: detailHref(uid, workTitle, sectionId),
      thumbnail: thumbnailImageData({
        base: detailsThumbBase,
        id: uid,
        suffix: detailThumbSuffix,
        size: detailThumbSizes[0],
        srcsetSizes: detailThumbSizes.slice(0, 2),
        format: assetFormat,
        alt: title
      })
    };
  }

  function renderDetails(payload, workTitle) {
    var section = document.getElementById('selectedWorkDetailsSection');
    var content = document.getElementById('selectedWorkDetailsContent');
    if (!section || !content) return;
    var sections = payload && Array.isArray(payload.sections) ? payload.sections : [];
    var hasDetails = false;
    content.innerHTML = '';

    sections.forEach(function (sec) {
      var label = text(sec && (sec.section_title || sec.project_subfolder)) || 'Details';
      var sectionId = slug(sec && (sec.section_id || label)) || 'details';
      var details = sec && Array.isArray(sec.details) ? sec.details : [];
      var items = details.map(function (detail) {
        return detailItem(detail, workTitle, sectionId);
      }).filter(Boolean);
      if (!items.length) return;

      var group = document.createElement('section');
      group.className = 'workDetails__group';
      group.id = 'details-' + sectionId;

      var title = document.createElement('h3');
      title.className = 'workDetails__title';
      title.textContent = label;
      group.appendChild(title);

      var grid = document.createElement('div');
      grid.className = 'catalogueGridList catalogueGridList--grid';
      grid.setAttribute('aria-label', 'details for ' + label);
      createThumbnailGridList({
        gridElement: grid,
        pageSize: Math.max(items.length, 1)
      }).render({
        items: items,
        mode: 'grid',
        page: 1
      });
      group.appendChild(grid);
      content.appendChild(group);
      hasDetails = true;
    });

    section.hidden = !hasDetails;
  }

  function dispatchMetadata(work) {
    var nav = document.getElementById('seriesNav');
    var seriesIds = Array.isArray(work && work.series_ids) ? work.series_ids.map(text).filter(Boolean) : [];
    var primarySeries = seriesIds.length ? seriesIds[0] : '';
    if (nav) {
      nav.setAttribute('data-work-id', workId);
      nav.setAttribute('data-series', primarySeries);
      nav.setAttribute('data-series-ids', seriesIds.join(','));
    }
    document.dispatchEvent(new CustomEvent('dlf:work-metadata-applied', {
      detail: { work_id: workId, series_id: primarySeries, series_ids: seriesIds }
    }));
  }

  function renderProse(payload) {
    var proseSection = document.getElementById('selectedWorkProseSection');
    var prose = document.getElementById('selectedWorkProseContent');
    if (!prose || typeof payload.content_html !== 'string' || !payload.content_html.trim()) return;
    prose.innerHTML = payload.content_html;
    if (proseSection) proseSection.hidden = false;
  }

  fetchJson(workPayloadUrl(workId, baseurl))
    .then(function (payload) {
      var work = payload && payload.work && typeof payload.work === 'object' ? payload.work : { work_id: workId, title: unavailableText };
      var title = text(work.title) || workId;
      rootNode.hidden = false;
      setText('selectedWorkTitleHidden', title);
      setText('selectedWorkTitleText', title);
      setText('selectedWorkCatText', text(work.work_id) || workId);
      setRow('selectedWorkYearRow', 'selectedWorkYearText', text(work.year_display) || text(work.year));
      setRow('selectedWorkMediumRow', 'selectedWorkMediumText', text(work.medium_caption));
      setRow('selectedWorkDimensionsRow', 'selectedWorkDimensionsText', dimensionsText(work));
      renderDownloadsAndLinks(payload, work);
      document.title = title + ' | dotlineform';
      renderMedia(work);
      updateBackLink();
      dispatchMetadata(work);
      renderProse(payload);
      renderDetails(payload, title);
    })
    .catch(function () {
      rootNode.hidden = false;
      setText('selectedWorkTitleHidden', unavailableText);
      setText('selectedWorkTitleText', unavailableText);
      setText('selectedWorkCatText', workId);
      updateBackLink();
    });
}
