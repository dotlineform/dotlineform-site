import { text } from './text.js';

export var GRID_THUMBNAIL_SIZES = '(min-width: 1200px) 10vw, (min-width: 700px) 14vw, 22vw';

export function thumbUrl(base, id, suffix, size, format) {
  var thumbId = text(id);
  if (!thumbId) return '';
  return text(base) + thumbId + '-' + text(suffix) + '-' + text(size) + '.' + text(format);
}

export function thumbSrcset(base, id, sizes, suffix, format) {
  var thumbId = text(id);
  if (!thumbId) return '';
  return (Array.isArray(sizes) ? sizes : [])
    .map(function (size) {
      return thumbUrl(base, thumbId, suffix, size, format) + ' ' + String(size) + 'w';
    })
    .join(', ');
}

export function thumbnailImageData(options) {
  var opts = options || {};
  var thumbId = text(opts.id);
  var size = Number(opts.size);
  var srcsetSizes = Array.isArray(opts.srcsetSizes) ? opts.srcsetSizes : [];
  var src = thumbUrl(opts.base, thumbId, opts.suffix, size, opts.format);
  return {
    src: src,
    srcset: src ? thumbSrcset(opts.base, thumbId, srcsetSizes, opts.suffix, opts.format) : '',
    sizes: text(opts.sizes) || GRID_THUMBNAIL_SIZES,
    width: size,
    height: size,
    alt: text(opts.alt),
    loading: text(opts.loading) || 'lazy',
    decoding: text(opts.decoding) || 'async'
  };
}
