import { renderMetadataPanel } from '../components/metadata-panel.js';
import { renderPrimaryMedia } from '../components/primary-media.js';
import { renderProseContent } from '../components/prose-content.js';
import { createThumbnailGridList } from '../components/thumbnail-grid-list.js';
import { bindArrowNavigation } from '../navigation/keyboard-navigation.js';
import { createSelectedWorkSeriesNavigation } from '../navigation/work-series-navigation.js';
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

var DETAILS_PAGE_SIZE = 80;
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

function metadataLinkEntries(entries, hrefForEntry) {
  return (Array.isArray(entries) ? entries : []).map(function (entry) {
    var href = hrefForEntry(entry);
    var labelText = text(entry && entry.label) || text(entry && entry.filename) || text(entry && entry.url);
    return href && labelText ? { href: href, label: labelText, target: '_blank', rel: 'noopener' } : null;
  }).filter(Boolean);
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
  var seriesNavigation = createSelectedWorkSeriesNavigation({
    baseurl: baseurl,
    routeState: routeState,
    navElement: document.getElementById('seriesNav'),
    prevLinkElement: document.getElementById('seriesNavPrev'),
    nextLinkElement: document.getElementById('seriesNavNext'),
    counterElement: document.getElementById('seriesNavCounter'),
    seriesLinkWrapElement: document.getElementById('workSeriesLinkWrap'),
    seriesLinkElement: document.getElementById('workSeriesLink'),
    backLinkElement: document.getElementById('pageBackLink')
  });
  bindArrowNavigation({
    prevIds: ['seriesNavPrev'],
    nextIds: ['seriesNavNext']
  });

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

  function renderMetadata(payload, work, title) {
    var metadata = document.getElementById('selectedWorkMetadata');
    var rows = document.getElementById('selectedWorkMetadataRows');
    if (!metadata || !rows) return;

    var nav = document.getElementById('seriesNav');
    var seriesLinkWrap = document.getElementById('workSeriesLinkWrap');
    var yearText = text(work && work.year_display) || text(work && work.year);
    var mediumText = text(work && work.medium_caption);
    var dimensions = dimensionsText(work);
    var downloads = metadataLinkEntries(
      arrayFromPayload(payload, work, 'downloads'),
      function (entry) { return workFileUrl(entry && entry.filename); }
    );
    var links = metadataLinkEntries(
      arrayFromPayload(payload, work, 'links'),
      function (entry) { return safeHref(entry && entry.url); }
    );

    renderMetadataPanel({
      rootElement: metadata,
      rowsElement: rows,
      rows: [
        {
          modifier: 'title',
          segments: [
            { text: title, id: 'selectedWorkTitleText', className: 'catalogueMetadata__titleMain' },
            { node: nav }
          ]
        },
        {
          hidden: !yearText,
          segments: [{ text: yearText, id: 'selectedWorkYearText' }]
        },
        {
          hidden: !mediumText,
          segments: [{ text: mediumText, id: 'selectedWorkMediumText' }]
        },
        {
          hidden: !dimensions,
          segments: [{ text: dimensions, id: 'selectedWorkDimensionsText' }]
        },
        {
          segments: [
            'cat. ',
            { text: text(work && work.work_id) || workId, id: 'selectedWorkCatText' },
            ' ',
            { node: seriesLinkWrap }
          ]
        },
        {
          hidden: !downloads.length,
          segments: [
            { text: downloads.length === 1 ? 'download' : 'downloads', id: 'selectedWorkDownloadsLabel' },
            ' ',
            { links: downloads, id: 'selectedWorkDownloadsLinks' }
          ]
        },
        {
          hidden: !links.length,
          segments: [
            { text: links.length === 1 ? 'link' : 'links', id: 'selectedWorkLinksLabel' },
            ' ',
            { links: links, id: 'selectedWorkLinksLinks' }
          ]
        }
      ]
    });
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

  function persistDetailsPage(sectionId, page) {
    var path = String(window.location.pathname || '/');
    var params = new URLSearchParams(window.location.search);
    var normalizedPage = toPositiveInteger(page) || 1;
    params.set('details_section', sectionId);
    if (normalizedPage > 1) {
      params.set('details_page', String(normalizedPage));
    } else {
      params.delete('details_page');
    }
    var query = params.toString();
    window.history.replaceState({}, '', path + (query ? ('?' + query) : '') + '#details-' + encodeURIComponent(sectionId));
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

  function detailHref(uid, sectionId, detailsPage) {
    var normalizedPage = toPositiveInteger(detailsPage) || 1;
    return workDetailUrl(uid, baseurl, {
      from_work: workId,
      section: sectionId,
      details_page: normalizedPage > 1 ? normalizedPage : '',
      series: routeState.series,
      series_page: routeState.seriesPage > 0 ? routeState.seriesPage : ''
    });
  }

  function detailItem(detail, sectionId, detailsPage) {
    var uid = text(detail && detail.detail_uid);
    if (!uid) return null;
    var title = text(detail && detail.title) || uid;
    return {
      id: uid,
      title: title,
      href: detailHref(uid, sectionId, detailsPage),
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

  function createDetailsPager(label) {
    var pager = document.createElement('nav');
    pager.className = 'catalogueGridList__pager';
    pager.setAttribute('aria-label', 'details pagination for ' + label);
    pager.hidden = true;

    var status = document.createElement('span');
    status.className = 'catalogueGridList__pagerStatus';
    pager.appendChild(status);

    var previous = document.createElement('button');
    previous.className = 'catalogueGridList__pagerButton';
    previous.type = 'button';
    previous.setAttribute('aria-label', 'Previous details page');
    previous.textContent = '\u2190';
    pager.appendChild(previous);

    var next = document.createElement('button');
    next.className = 'catalogueGridList__pagerButton';
    next.type = 'button';
    next.setAttribute('aria-label', 'Next details page');
    next.textContent = '\u2192';
    pager.appendChild(next);

    return {
      root: pager,
      status: status,
      previous: previous,
      next: next
    };
  }

  function renderDetails(payload) {
    var section = document.getElementById('selectedWorkDetailsSection');
    var content = document.getElementById('selectedWorkDetailsContent');
    if (!section || !content) return;
    var sections = payload && Array.isArray(payload.sections) ? payload.sections : [];
    var hasDetails = false;
    content.innerHTML = '';

    sections.forEach(function (sec) {
      var label = text(sec && sec.section_title) || 'Details';
      var sectionId = slug(sec && (sec.section_id || label)) || 'details';
      var details = sec && Array.isArray(sec.details) ? sec.details : [];
      var items = details.map(function (detail) {
        return detailItem(detail, sectionId, 1);
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
      var pager = createDetailsPager(label);
      var pageCount = Math.max(1, Math.ceil(items.length / DETAILS_PAGE_SIZE));
      var initialPage = routeState.detailsSection === sectionId && routeState.detailsPage > 0 ? routeState.detailsPage : 1;
      initialPage = Math.min(initialPage, pageCount);
      var thumbnailGridList = null;
      var renderDetailsPage = function (page) {
        var normalizedPage = Math.min(toPositiveInteger(page) || 1, pageCount);
        var pageItems = details.map(function (detail) {
          return detailItem(detail, sectionId, normalizedPage);
        }).filter(Boolean);
        return thumbnailGridList.render({
          items: pageItems,
          mode: 'grid',
          page: normalizedPage
        });
      };
      thumbnailGridList = createThumbnailGridList({
        gridElement: grid,
        pagerElement: pager.root,
        pagerStatusElement: pager.status,
        previousButton: pager.previous,
        nextButton: pager.next,
        pageSize: DETAILS_PAGE_SIZE,
        labels: {
          previous: 'Previous details page',
          next: 'Next details page'
        },
        onPageChange: function (page) {
          persistDetailsPage(sectionId, page);
          renderDetailsPage(page);
        }
      });
      renderDetailsPage(initialPage);
      group.appendChild(grid);
      group.appendChild(pager.root);
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
    seriesNavigation.update({ workId: workId, seriesId: primarySeries });
    document.dispatchEvent(new CustomEvent('dlf:work-metadata-applied', {
      detail: { work_id: workId, series_id: primarySeries, series_ids: seriesIds }
    }));
  }

  function renderProse(payload) {
    var proseSection = document.getElementById('selectedWorkProseSection');
    var prose = document.getElementById('selectedWorkProseContent');
    renderProseContent({
      rootElement: proseSection,
      contentElement: prose,
      html: payload && typeof payload.content_html === 'string' ? payload.content_html : '',
      hideRootWhenEmpty: true
    });
  }

  fetchJson(workPayloadUrl(workId, baseurl))
    .then(function (payload) {
      var work = payload && payload.work && typeof payload.work === 'object' ? payload.work : { work_id: workId, title: unavailableText };
      var title = text(work.title) || workId;
      rootNode.hidden = false;
      setText('selectedWorkTitleHidden', title);
      renderMetadata(payload, work, title);
      document.title = title + ' | dotlineform';
      renderMedia(work);
      updateBackLink();
      dispatchMetadata(work);
      renderProse(payload);
      renderDetails(payload);
    })
    .catch(function () {
      rootNode.hidden = false;
      setText('selectedWorkTitleHidden', unavailableText);
      renderMetadata(null, { work_id: workId }, unavailableText);
      updateBackLink();
    });
}
