import { text, toPositiveInteger } from '../shared/text.js';

var GRID_IMAGE_SIZES = '(min-width: 1200px) 10vw, (min-width: 700px) 14vw, 22vw';

function normalizeMode(value) {
  return text(value).toLowerCase() === 'list' ? 'list' : 'grid';
}

function normalizePage(value) {
  var page = Number(value);
  if (!Number.isFinite(page) || page < 1) return 1;
  return Math.floor(page);
}

function replaceWithPlaceholder(img, mode, title) {
  if (!img.parentNode) return;
  img.parentNode.replaceChild(renderPlaceholder(mode, title), img);
}

function renderPlaceholder(mode, title) {
  var placeholder = document.createElement('span');
  placeholder.className = [
    'catalogueGridList__image',
    'catalogueGridList__image--' + normalizeMode(mode),
    'catalogueGridList__image--placeholder'
  ].join(' ');
  placeholder.setAttribute('aria-hidden', 'true');
  if (title) placeholder.title = title;
  return placeholder;
}

function renderImage(item, mode) {
  var thumb = item && item.thumbnail && typeof item.thumbnail === 'object' ? item.thumbnail : {};
  var title = text((item && item.title) || (thumb && thumb.alt));
  var src = text(thumb.src);
  if (!src) return renderPlaceholder(mode, title);

  var img = document.createElement('img');
  img.className = [
    'catalogueGridList__image',
    'catalogueGridList__image--' + normalizeMode(mode)
  ].join(' ');
  img.addEventListener('error', function () {
    replaceWithPlaceholder(img, mode, title);
  }, { once: true });
  img.src = src;
  if (thumb.srcset) img.srcset = text(thumb.srcset);
  img.sizes = text(thumb.sizes) || GRID_IMAGE_SIZES;
  var width = toPositiveInteger(thumb.width);
  var height = toPositiveInteger(thumb.height);
  if (width) img.width = width;
  if (height) img.height = height;
  img.alt = text(thumb.alt) || title;
  img.loading = 'lazy';
  img.decoding = 'async';
  return img;
}

function renderItem(item, mode) {
  var normalizedMode = normalizeMode(mode);
  var title = text(item && item.title) || text(item && item.id);
  var href = text(item && item.href);
  var link = document.createElement('a');
  link.className = [
    'catalogueGridList__item',
    'catalogueGridList__item--' + normalizedMode
  ].join(' ');
  link.href = href;
  if (title) link.title = title;
  if (item && item.current) link.setAttribute('aria-current', 'true');
  if (item && item.selected) link.setAttribute('data-selected', 'true');

  if (normalizedMode === 'grid') {
    if (title) link.setAttribute('aria-label', title);
    link.appendChild(renderImage(item, normalizedMode));
    return link;
  }

  link.appendChild(renderImage(item, normalizedMode));

  var meta = document.createElement('div');
  meta.className = 'catalogueGridList__meta';

  var titleEl = document.createElement('div');
  titleEl.className = 'catalogueGridList__title';
  titleEl.textContent = title;
  meta.appendChild(titleEl);

  var caption = text(item && item.caption);
  if (caption) {
    var captionEl = document.createElement('div');
    captionEl.className = 'catalogueGridList__caption';
    captionEl.textContent = caption;
    meta.appendChild(captionEl);
  }

  link.appendChild(meta);
  return link;
}

export function createThumbnailGridList(options) {
  return new ThumbnailGridList(options || {});
}

export class ThumbnailGridList {
  constructor(options) {
    this.listElement = options.listElement || null;
    this.gridElement = options.gridElement || null;
    this.pagerElement = options.pagerElement || null;
    this.pagerStatusElement = options.pagerStatusElement || null;
    this.previousButton = options.previousButton || null;
    this.nextButton = options.nextButton || null;
    this.pageSize = toPositiveInteger(options.pageSize) || 80;
    this.labels = Object.assign({
      previous: 'Previous page',
      next: 'Next page'
    }, options.labels || {});
    this.onPageChange = typeof options.onPageChange === 'function' ? options.onPageChange : null;
    this.items = [];
    this.mode = 'grid';
    this.page = 1;
    this.pageCount = 1;

    this.handlePrevious = this.handlePrevious.bind(this);
    this.handleNext = this.handleNext.bind(this);
    if (this.previousButton) this.previousButton.addEventListener('click', this.handlePrevious);
    if (this.nextButton) this.nextButton.addEventListener('click', this.handleNext);
  }

  render(state) {
    var nextState = state || {};
    this.items = Array.isArray(nextState.items) ? nextState.items.slice() : [];
    this.mode = normalizeMode(nextState.mode);
    this.page = normalizePage(nextState.page);
    this.pageCount = Math.max(1, Math.ceil(this.items.length / this.pageSize));
    this.page = Math.min(this.page, this.pageCount);

    if (this.listElement) this.listElement.innerHTML = '';
    if (this.gridElement) this.gridElement.innerHTML = '';

    var target = this.mode === 'grid' ? this.gridElement : this.listElement;
    if (target && this.items.length) {
      var start = (this.page - 1) * this.pageSize;
      var end = Math.min(start + this.pageSize, this.items.length);
      var pageItems = this.items.slice(start, end);
      var fragment = document.createDocumentFragment();
      pageItems.forEach(function (item) {
        fragment.appendChild(renderItem(item, this.mode));
      }, this);
      target.appendChild(fragment);
    }

    this.updateVisibility();
    this.updatePager();

    return {
      page: this.page,
      pageCount: this.pageCount,
      hasItems: this.items.length > 0
    };
  }

  setPage(page) {
    this.page = normalizePage(page);
    if (this.onPageChange) this.onPageChange(this.page);
    return this.render({
      items: this.items,
      mode: this.mode,
      page: this.page
    });
  }

  handlePrevious() {
    if (this.pageCount < 2) return;
    this.setPage((this.page - 1 + this.pageCount - 1) % this.pageCount + 1);
  }

  handleNext() {
    if (this.pageCount < 2) return;
    this.setPage((this.page % this.pageCount) + 1);
  }

  updateVisibility() {
    var hasItems = this.items.length > 0;
    if (this.listElement) this.listElement.hidden = !hasItems || this.mode !== 'list';
    if (this.gridElement) this.gridElement.hidden = !hasItems || this.mode !== 'grid';
  }

  updatePager() {
    var hasPages = this.pageCount >= 2 && this.items.length > 0;
    if (this.pagerStatusElement) {
      this.pagerStatusElement.textContent = String(this.page) + '/' + String(this.pageCount);
    }
    if (this.pagerElement) {
      this.pagerElement.hidden = !hasPages;
      this.pagerElement.classList.toggle('catalogueGridList__pager--list', this.mode === 'list');
    }
    if (this.previousButton) {
      this.previousButton.disabled = !hasPages;
      this.previousButton.setAttribute('aria-label', this.labels.previous);
    }
    if (this.nextButton) {
      this.nextButton.disabled = !hasPages;
      this.nextButton.setAttribute('aria-label', this.labels.next);
    }
  }
}
