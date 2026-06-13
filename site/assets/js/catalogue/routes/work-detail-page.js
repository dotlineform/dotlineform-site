import { renderMetadataPanel } from '../components/metadata-panel.js';
import { renderPrimaryMedia } from '../components/primary-media.js';
import { bindArrowNavigation } from '../navigation/keyboard-navigation.js';
import { bindLinkSwipeZone } from '../navigation/swipe-navigation.js';
import {
  catalogueIndexUrl,
  parseRouteState,
  trimBaseurl,
  workDetailUrl,
  workPayloadUrl,
  workUrl
} from '../shared/catalogue-urls.js';
import { fetchJson } from '../shared/fetch-json.js';
import { normalizePositiveSizes, slug, text, toNumber, toPositiveInteger } from '../shared/text.js';

var root = document.getElementById('detailPageRoot');
if (root) bootWorkDetailRoute(root);

function jsonAttribute(node, name, fallback) {
  try {
    return JSON.parse(node.getAttribute(name) || '[]');
  } catch (err) {
    return fallback;
  }
}

function detailWorkId(detailUid) {
  var uid = text(detailUid);
  return uid.indexOf('-') !== -1 ? uid.split('-', 1)[0] : '';
}

function bootWorkDetailRoute(rootNode) {
  var empty = document.getElementById('detailPageEmpty');
  var routeState = parseRouteState(window.location);
  var detailUid = text(routeState.detail);
  var unavailableText = text(rootNode.getAttribute('data-unavailable-text')) || 'info not available';

  if (!detailUid) {
    if (empty) {
      empty.hidden = false;
      empty.textContent = unavailableText;
    }
    return;
  }

  var params = new URLSearchParams(window.location.search);
  var baseurl = trimBaseurl(rootNode.getAttribute('data-baseurl'));
  var imgBase = text(rootNode.getAttribute('data-img-base'));
  var primaryDisplayWidth = toPositiveInteger(rootNode.getAttribute('data-primary-display-width')) || 1200;
  var primaryFullWidth = toPositiveInteger(rootNode.getAttribute('data-primary-full-width')) || primaryDisplayWidth;
  var primarySuffix = text(rootNode.getAttribute('data-primary-suffix')) || 'primary';
  var assetFormat = text(rootNode.getAttribute('data-asset-format')) || 'webp';
  var renderWidths = normalizePositiveSizes(jsonAttribute(rootNode, 'data-primary-render-widths', []), [primaryDisplayWidth]);
  bindArrowNavigation({
    prevIds: ['detailNavPrev'],
    nextIds: ['detailNavNext']
  });

  var ctx = {
    detailUid: detailUid,
    fromWork: text(params.get('from_work')) || detailWorkId(detailUid),
    fromWorkTitle: text(params.get('from_work_title')),
    section: text(params.get('section')).toLowerCase(),
    detailsSection: routeState.detailsSection,
    detailsPage: routeState.detailsPage || 1,
    series: text(routeState.series),
    seriesPage: routeState.seriesPage,
    title: detailUid,
    widthPx: 0,
    heightPx: 0
  };
  if (!ctx.detailsSection) ctx.detailsSection = ctx.section;
  if (!ctx.fromWorkTitle) ctx.fromWorkTitle = ctx.fromWork;

  function imageUrl(uid, width) {
    return imgBase + encodeURIComponent(uid) + '-' + primarySuffix + '-' + String(width) + '.' + assetFormat;
  }

  function renderMetadata() {
    var metadata = document.getElementById('detailMetadata');
    var rows = document.getElementById('detailMetadataRows');
    if (!metadata || !rows) return;
    renderMetadataPanel({
      rootElement: metadata,
      rowsElement: rows,
      rows: [
        {
          modifier: 'title',
          segments: [
            { text: ctx.title || 'Untitled', id: 'detailTitleText', className: 'catalogueMetadata__titleMain' },
            { node: document.getElementById('detailNav') }
          ]
        },
        {
          segments: [
            'cat. ',
            { text: ctx.detailUid, id: 'detailCatText' }
          ]
        }
      ]
    });
  }

  function updateTitle() {
    var hiddenTitle = document.getElementById('detailHiddenTitle');
    if (hiddenTitle) hiddenTitle.textContent = ctx.title || 'Untitled';
    renderMetadata();
    if (ctx.title) document.title = ctx.title + ' | dotlineform';
  }

  function updateMedia() {
    var media = document.getElementById('detailPrimaryMedia');
    if (!media) return;
    var srcset = renderWidths.map(function (width) {
      return imageUrl(ctx.detailUid, width) + ' ' + String(width) + 'w';
    }).join(', ');
    renderPrimaryMedia({
      rootElement: media,
      aspectRatio: ctx.widthPx > 0 && ctx.heightPx > 0 ? String(ctx.widthPx) + ' / ' + String(ctx.heightPx) : '',
      link: {
        id: 'detailMediaLink',
        href: imageUrl(ctx.detailUid, primaryFullWidth),
        target: '_blank',
        rel: 'noopener',
        attributes: {
          'data-swipe-nav-zone': 'detail-media'
        }
      },
      image: {
        id: 'detailPrimaryImg',
        src: imageUrl(ctx.detailUid, primaryDisplayWidth),
        srcset: srcset,
        sizes: '(max-width: 800px) 100vw, 72ch',
        alt: ctx.title || ctx.detailUid,
        loading: 'eager',
        decoding: 'async',
        fetchPriority: 'high'
      }
    });
  }

  function updateBackLink() {
    var link = document.getElementById('detailBackLink');
    if (!link) return;
    if (!ctx.fromWork) {
      link.textContent = '\u2190 works';
      link.href = catalogueIndexUrl(baseurl);
      return;
    }
    var href = workUrl(ctx.fromWork, baseurl, {
      series: ctx.series,
      series_page: ctx.seriesPage,
      details_section: ctx.detailsSection,
      details_page: ctx.detailsPage
    });
    if (ctx.section) href += '#details-' + encodeURIComponent(ctx.section);
    link.textContent = '\u2190 ' + (ctx.fromWorkTitle || ctx.fromWork);
    link.href = href;
  }

  function detailHref(uid) {
    return workDetailUrl(uid, baseurl, {
      from_work: ctx.fromWork,
      from_work_title: ctx.fromWorkTitle,
      section: ctx.section,
      series: ctx.series,
      series_page: ctx.seriesPage,
      details_section: ctx.detailsSection,
      details_page: ctx.detailsPage
    });
  }

  function findDetailRecord(workPayload) {
    var sections = workPayload && Array.isArray(workPayload.sections) ? workPayload.sections : [];
    for (var i = 0; i < sections.length; i += 1) {
      var sec = sections[i] || {};
      var details = Array.isArray(sec.details) ? sec.details : [];
      for (var j = 0; j < details.length; j += 1) {
        var detail = details[j] || {};
        if (text(detail.detail_uid) === ctx.detailUid) {
          return {
            detail: detail,
            sectionId: slug(sec.section_id || sec.section_title || sec.project_subfolder || 'details')
          };
        }
      }
    }
    return { detail: null, sectionId: '' };
  }

  function setNavigation(workPayload) {
    var nav = document.getElementById('detailNav');
    var prevA = document.getElementById('detailNavPrev');
    var nextA = document.getElementById('detailNavNext');
    var counter = document.getElementById('detailTitleCounter');
    if (!nav || !prevA || !nextA) return;

    var sections = workPayload && Array.isArray(workPayload.sections) ? workPayload.sections : [];
    var details = [];
    sections.forEach(function (sec) {
      var sectionId = slug(sec && (sec.section_id || sec.section_title || sec.project_subfolder || 'details'));
      if (ctx.section && sectionId !== ctx.section) return;
      var list = sec && Array.isArray(sec.details) ? sec.details : [];
      list.forEach(function (detail) { details.push(detail); });
    });
    if (!details.length && ctx.section) {
      sections.forEach(function (sec) {
        var list = sec && Array.isArray(sec.details) ? sec.details : [];
        list.forEach(function (detail) { details.push(detail); });
      });
    }

    var ids = details.map(function (detail) {
      return text(detail && detail.detail_uid);
    }).filter(Boolean);
    var index = ids.indexOf(ctx.detailUid);
    if (ids.length < 2 || index < 0) {
      nav.hidden = true;
      if (counter) counter.hidden = true;
      return;
    }

    prevA.href = detailHref(ids[(index - 1 + ids.length) % ids.length]);
    nextA.href = detailHref(ids[(index + 1) % ids.length]);
    if (counter) {
      counter.textContent = String(index + 1) + '/' + String(ids.length);
      counter.hidden = false;
    }
    nav.hidden = false;
  }

  function bindSwipeNavigation() {
    var zone = document.querySelector('[data-swipe-nav-zone="detail-media"]');
    if (!zone) return;
    bindLinkSwipeZone(zone, {
      getPrev: function () { return document.getElementById('detailNavPrev'); },
      getNext: function () { return document.getElementById('detailNavNext'); }
    });
  }

  updateTitle();
  updateMedia();
  updateBackLink();
  rootNode.hidden = false;
  bindSwipeNavigation();

  fetchJson(workPayloadUrl(ctx.fromWork, baseurl))
    .then(function (workPayload) {
      var work = workPayload && workPayload.work && typeof workPayload.work === 'object' ? workPayload.work : null;
      var workTitle = text(work && work.title);
      if (workTitle && (!params.get('from_work_title') || !ctx.fromWorkTitle)) ctx.fromWorkTitle = workTitle;
      var found = findDetailRecord(workPayload);
      if (found.detail) {
        ctx.title = text(found.detail.title) || ctx.detailUid;
        ctx.widthPx = toNumber(found.detail.width_px) || 0;
        ctx.heightPx = toNumber(found.detail.height_px) || 0;
        if (!ctx.section && found.sectionId) ctx.section = found.sectionId;
        if (!ctx.detailsSection && found.sectionId) ctx.detailsSection = found.sectionId;
      }
      updateTitle();
      updateMedia();
      bindSwipeNavigation();
      updateBackLink();
      setNavigation(workPayload);
    })
    .catch(function () {
      ctx.title = unavailableText;
      updateTitle();
      updateBackLink();
    });
}
