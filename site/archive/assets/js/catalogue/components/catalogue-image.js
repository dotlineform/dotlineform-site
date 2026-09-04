import { text, toPositiveInteger } from '../shared/text.js';

function classList(values) {
  return values.filter(Boolean).join(' ');
}

function normalizeVariant(value) {
  var variant = text(value).toLowerCase();
  return variant === 'list' ? 'list' : 'grid';
}

export function renderCatalogueImagePlaceholder(options) {
  var opts = options || {};
  var title = text(opts.title || opts.alt);
  var variant = normalizeVariant(opts.variant);
  var placeholder = document.createElement('span');
  placeholder.className = classList([
    'catalogueImage',
    'catalogueImage--' + variant,
    'catalogueImage--placeholder',
    text(opts.className)
  ]);
  placeholder.setAttribute('aria-hidden', 'true');
  if (title) placeholder.title = title;
  return placeholder;
}

export function renderCatalogueImage(media, options) {
  var image = media && typeof media === 'object' ? media : {};
  var opts = options || {};
  var title = text(opts.title || image.alt);
  var src = text(image.src);
  var variant = normalizeVariant(opts.variant);
  if (!src) {
    return renderCatalogueImagePlaceholder({
      alt: image.alt,
      title: title,
      variant: variant,
      className: opts.className
    });
  }

  var img = document.createElement('img');
  img.className = classList([
    'catalogueImage',
    'catalogueImage--' + variant,
    text(opts.className)
  ]);
  img.addEventListener('error', function () {
    if (!img.parentNode) return;
    img.parentNode.replaceChild(renderCatalogueImagePlaceholder({
      alt: image.alt,
      title: title,
      variant: variant,
      className: opts.className
    }), img);
  }, { once: true });
  img.src = src;
  if (image.srcset) img.srcset = text(image.srcset);
  if (image.sizes) img.sizes = text(image.sizes);
  var width = toPositiveInteger(image.width);
  var height = toPositiveInteger(image.height);
  if (width) img.width = width;
  if (height) img.height = height;
  img.alt = text(image.alt) || title;
  img.loading = text(image.loading) || 'lazy';
  img.decoding = text(image.decoding) || 'async';
  return img;
}
