export function text(value) {
  return String(value == null ? '' : value).trim();
}

export function lowerText(value) {
  return text(value).toLowerCase();
}

export function toPositiveInteger(value) {
  var number = Number(value);
  return Number.isFinite(number) && number > 0 ? Math.floor(number) : 0;
}

export function normalizePositiveSizes(raw, fallback) {
  var values = Array.isArray(raw) ? raw : [];
  var sizes = values.map(toPositiveInteger).filter(function (value) {
    return value > 0;
  });
  return sizes.length ? sizes : (Array.isArray(fallback) ? fallback.slice() : []);
}
