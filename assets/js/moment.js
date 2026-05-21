(function () {
  var root = document.getElementById('momentPageRoot');
  if (!root) return;
  var runtime = window.__dlfPublicCatalogueRuntime;
  if (!runtime) return;

  var baseurl = runtime.trimBaseurl(root.getAttribute('data-baseurl'));
  var momentId = runtime.text(root.getAttribute('data-moment-id'));
  if (!momentId) return;

  var imgBase = String(root.getAttribute('data-img-base') || '');
  var primarySuffix = runtime.text(root.getAttribute('data-primary-suffix')) || 'primary';
  var assetFormat = runtime.text(root.getAttribute('data-asset-format')) || 'webp';
  var displayWidth = runtime.toPositiveInteger(root.getAttribute('data-primary-display-width'));
  if (!Number.isFinite(displayWidth) || displayWidth <= 0) displayWidth = 1600;
  var loadingText = String(root.getAttribute('data-loading-text') || 'loading...');
  var unavailableText = String(root.getAttribute('data-unavailable-text') || 'info not available');

  var renderWidths = [];
  try {
    renderWidths = JSON.parse(root.getAttribute('data-primary-render-widths') || '[]');
  } catch (e) {
    renderWidths = [];
  }
  renderWidths = runtime.normalizePositiveSizes(renderWidths, [800, 1200, 1600]);

  function parseDateValue(raw) {
    var dateText = runtime.text(raw);
    if (!dateText) return null;
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateText)) {
      return new Date(dateText + 'T00:00:00Z');
    }
    var parsed = new Date(dateText);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function formatDate(meta) {
    var display = runtime.text(meta && meta.date_display);
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
    } catch (e) {
      return runtime.text(meta && meta.date);
    }
  }

  function normalizeImages(raw) {
    if (!Array.isArray(raw)) return [];
    return raw
      .map(function (item) {
        if (!item || typeof item !== 'object') return null;
        var file = runtime.text(item.file);
        if (!file) return null;
        return {
          file: file,
          alt: runtime.text(item.alt),
          caption: runtime.text(item.caption)
        };
      })
      .filter(Boolean);
  }

  function normalizeMoment(raw) {
    var source = raw && typeof raw === 'object' ? raw : {};
    var normalized = {};
    normalized.moment_id = runtime.text(source.moment_id) || momentId;
    normalized.title = runtime.text(source.title) || normalized.moment_id || 'Untitled';
    normalized.date = runtime.text(source.date);
    normalized.date_display = runtime.text(source.date_display);
    normalized.images = normalizeImages(source.images);
    normalized.width_px = runtime.toNumber(source.width_px);
    normalized.height_px = runtime.toNumber(source.height_px);
    if (!Number.isFinite(normalized.width_px) || normalized.width_px <= 0) normalized.width_px = null;
    if (!Number.isFinite(normalized.height_px) || normalized.height_px <= 0) normalized.height_px = null;
    return normalized;
  }

  function deriveStem(meta, hero) {
    var fallbackStem = runtime.text(hero && hero.file).replace(/^\/+/, '').split('/').pop().split('.')[0];
    return runtime.text(meta && meta.moment_id) || fallbackStem;
  }

  function buildImageSources(meta, hero) {
    var file = runtime.text(hero && hero.file);
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
      src: runtime.thumbUrl(imgBase, stem, primarySuffix, displayWidth, assetFormat),
      srcset: runtime.thumbSrcset(imgBase, stem, renderWidths, primarySuffix, assetFormat),
      external: false
    };
  }

  function applyMetadata(meta) {
    var normalized = normalizeMoment(meta);
    var titleEl = document.getElementById('momentTitleText');
    var dateEl = document.getElementById('momentDateText');
    var heroEl = document.getElementById('momentHero');
    var heroImg = document.getElementById('momentHeroImg');
    var heroCaption = document.getElementById('momentHeroCaption');

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

    if (!heroEl || !heroImg || !heroCaption) return;

    var hero = normalized.images.length ? normalized.images[0] : null;
    if (!hero) {
      heroEl.hidden = true;
      heroImg.removeAttribute('src');
      heroImg.removeAttribute('srcset');
      heroImg.setAttribute('alt', normalized.title || 'Moment');
      heroCaption.textContent = '';
      heroCaption.hidden = true;
      return;
    }

    var sources = buildImageSources(normalized, hero);
    if (!sources) {
      heroEl.hidden = true;
      return;
    }

    heroEl.hidden = false;
    heroImg.setAttribute('src', sources.src);
    if (sources.external || !sources.srcset) {
      heroImg.removeAttribute('srcset');
      heroImg.removeAttribute('sizes');
    } else {
      heroImg.setAttribute('srcset', sources.srcset);
      heroImg.setAttribute('sizes', '(max-width: 800px) 100vw, 72ch');
    }
    if (normalized.width_px && normalized.height_px) {
      heroImg.setAttribute('width', String(normalized.width_px));
      heroImg.setAttribute('height', String(normalized.height_px));
    }
    heroImg.setAttribute('alt', hero.alt || normalized.title || 'Moment');

    if (hero.caption) {
      heroCaption.textContent = hero.caption;
      heroCaption.hidden = false;
    } else {
      heroCaption.textContent = '';
      heroCaption.hidden = true;
    }
  }

  function applyContentHtml(html) {
    var body = document.getElementById('momentBody');
    if (!body) return;
    body.innerHTML = String(html == null ? '' : html);
  }

  function showLoadError() {
    applyContentHtml('<p>' + unavailableText + '</p>');
  }

  applyMetadata({ moment_id: momentId, title: loadingText });

  runtime.fetchJson(runtime.momentPayloadUrl(momentId, baseurl))
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
})();
