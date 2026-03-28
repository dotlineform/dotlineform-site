(function () {
  var root = document.getElementById('momentPageRoot');
  if (!root) return;

  var baseurl = String(root.getAttribute('data-baseurl') || '').replace(/\/$/, '');
  var momentId = String(root.getAttribute('data-moment-id') || '').trim();
  if (!momentId) return;

  var imgBase = String(root.getAttribute('data-img-base') || '');
  var primarySuffix = String(root.getAttribute('data-primary-suffix') || 'primary').trim() || 'primary';
  var assetFormat = String(root.getAttribute('data-asset-format') || 'webp').trim() || 'webp';
  var displayWidth = Number(root.getAttribute('data-primary-display-width') || '0');
  if (!Number.isFinite(displayWidth) || displayWidth <= 0) displayWidth = 1600;

  var renderWidths = [];
  try {
    renderWidths = JSON.parse(root.getAttribute('data-primary-render-widths') || '[]');
  } catch (e) {
    renderWidths = [];
  }
  renderWidths = Array.isArray(renderWidths) ? renderWidths.map(function (value) {
    var n = Number(value);
    return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
  }).filter(function (value) { return value > 0; }) : [];
  if (!renderWidths.length) renderWidths = [800, 1200, 1600];

  var fallbackRaw = root.getAttribute('data-fallback-json') || '{}';
  var fallback = {};
  try {
    fallback = JSON.parse(fallbackRaw);
  } catch (e) {
    fallback = {};
  }

  function text(value) {
    return String(value == null ? '' : value).trim();
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
    } catch (e) {
      return text(meta && meta.date);
    }
  }

  function normalizeImages(raw) {
    if (!Array.isArray(raw)) return [];
    return raw
      .map(function (item) {
        if (!item || typeof item !== 'object') return null;
        var file = text(item.file);
        if (!file) return null;
        return {
          file: file,
          alt: text(item.alt),
          caption: text(item.caption)
        };
      })
      .filter(Boolean);
  }

  function normalizeMoment(raw) {
    var source = raw && typeof raw === 'object' ? raw : {};
    var normalized = {};
    normalized.moment_id = text(source.moment_id) || momentId;
    normalized.title = text(source.title) || normalized.moment_id || 'Untitled';
    normalized.date = text(source.date);
    normalized.date_display = text(source.date_display);
    normalized.images = normalizeImages(source.images);
    normalized.width_px = Number(source.width_px);
    normalized.height_px = Number(source.height_px);
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
      src: imgBase + stem + '-' + primarySuffix + '-' + String(displayWidth) + '.' + assetFormat,
      srcset: renderWidths.map(function (width) {
        return imgBase + stem + '-' + primarySuffix + '-' + String(width) + '.' + assetFormat + ' ' + String(width) + 'w';
      }).join(', '),
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
    applyContentHtml('<p>problem loading content</p>');
  }

  function fetchJson(url) {
    return fetch(url, { cache: 'default' })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      });
  }

  applyMetadata(fallback);

  var url = baseurl + '/assets/moments/index/' + encodeURIComponent(momentId) + '.json';
  fetchJson(url)
    .then(function (payload) {
      var moment = (payload && payload.moment && typeof payload.moment === 'object') ? payload.moment : null;
      var contentHtml = payload && typeof payload.content_html === 'string' ? payload.content_html : null;
      if (!moment || contentHtml == null) throw new Error('Invalid moment payload');

      var merged = {};
      var key;
      for (key in fallback) merged[key] = fallback[key];
      for (key in moment) merged[key] = moment[key];
      applyMetadata(merged);
      applyContentHtml(contentHtml);
    })
    .catch(function () {
      applyMetadata(fallback);
      showLoadError();
    });
})();
