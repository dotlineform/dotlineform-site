import { text, toPositiveInteger } from '../shared/text.js';

function setOptionalAttribute(node, name, value) {
  var valueText = text(value);
  if (valueText) {
    node.setAttribute(name, valueText);
  } else {
    node.removeAttribute(name);
  }
}

function setOptionalNumberAttribute(node, name, value) {
  var number = toPositiveInteger(value);
  if (number > 0) {
    node.setAttribute(name, String(number));
  } else {
    node.removeAttribute(name);
  }
}

function applyAttributes(node, attrs) {
  Object.keys(attrs || {}).forEach(function (name) {
    setOptionalAttribute(node, name, attrs[name]);
  });
}

function renderImage(image) {
  var imgData = image || {};
  var img = document.createElement('img');
  img.className = text(imgData.className) || 'page__mediaImg';
  setOptionalAttribute(img, 'id', imgData.id);
  setOptionalAttribute(img, 'src', imgData.src);
  setOptionalAttribute(img, 'srcset', imgData.srcset);
  setOptionalAttribute(img, 'sizes', imgData.sizes);
  setOptionalNumberAttribute(img, 'width', imgData.width);
  setOptionalNumberAttribute(img, 'height', imgData.height);
  img.alt = text(imgData.alt);
  img.loading = text(imgData.loading) || 'eager';
  img.decoding = text(imgData.decoding) || 'async';
  setOptionalAttribute(img, 'fetchpriority', imgData.fetchPriority || imgData.fetchpriority);
  applyAttributes(img, imgData.attributes);
  return img;
}

function renderLink(link, image, aspectRatio) {
  var linkData = link || {};
  var anchor = document.createElement('a');
  anchor.className = text(linkData.className) || 'page__mediaLink';
  setOptionalAttribute(anchor, 'id', linkData.id);
  setOptionalAttribute(anchor, 'href', linkData.href);
  setOptionalAttribute(anchor, 'target', linkData.target);
  setOptionalAttribute(anchor, 'rel', linkData.rel);
  if (aspectRatio) anchor.style.setProperty('--work-ar', aspectRatio);
  applyAttributes(anchor, linkData.attributes);
  anchor.appendChild(image);
  return anchor;
}

function renderCaption(caption) {
  var captionData = caption || {};
  var label = text(typeof captionData === 'string' ? captionData : captionData.text);
  var captionEl = document.createElement('figcaption');
  if (captionData && typeof captionData === 'object') {
    setOptionalAttribute(captionEl, 'id', captionData.id);
    setOptionalAttribute(captionEl, 'class', captionData.className);
    applyAttributes(captionEl, captionData.attributes);
  }
  captionEl.textContent = label;
  captionEl.hidden = !label;
  return captionEl;
}

export function renderPrimaryMedia(options) {
  var opts = options || {};
  var root = opts.rootElement || null;
  if (!root) return null;

  var imageData = opts.image && typeof opts.image === 'object' ? opts.image : {};
  var src = text(imageData.src);
  root.innerHTML = '';
  root.style.removeProperty('--work-ar');

  if (opts.hidden || !src) {
    root.hidden = true;
    return {
      rootElement: root,
      imageElement: null,
      linkElement: null,
      captionElement: null
    };
  }

  root.hidden = false;
  var aspectRatio = text(opts.aspectRatio);
  var shouldRenderLink = opts.link && text(opts.link.href);
  if (aspectRatio && !shouldRenderLink) root.style.setProperty('--work-ar', aspectRatio);

  var image = renderImage(imageData);
  var link = shouldRenderLink ? renderLink(opts.link, image, aspectRatio) : null;
  root.appendChild(link || image);

  var caption = null;
  if (opts.caption != null) {
    caption = renderCaption(opts.caption);
    root.appendChild(caption);
  }

  return {
    rootElement: root,
    imageElement: image,
    linkElement: link,
    captionElement: caption
  };
}
