/**
 * Match responsive selection to the rendered image slot, including aspect-ratio limits.
 * Dimensions establish layout before loading. Release when the owning view is removed;
 * detached report fragments also disconnect after their first connected observation.
 */
export function mountDocsViewerResponsiveImage(image, data) {
  image.width = data.widthPx;
  image.height = data.heightPx;
  if (!data.srcset) {
    image.src = data.src;
    return function () {};
  }
  var view = image.ownerDocument.defaultView;
  var connected = false;
  var released = false;
  var observer = new view.ResizeObserver(update);
  function release() {
    if (released) return;
    released = true;
    observer.disconnect();
  }
  function update() {
    if (released) return;
    if (!image.isConnected) {
      if (connected) release();
      return;
    }
    connected = true;
    var box = image.getBoundingClientRect();
    var width = Math.min(box.width, box.height * data.widthPx / data.heightPx);
    if (width <= 0) return;
    image.sizes = Math.ceil(width) + "px";
    if (image.srcset !== data.srcset) image.srcset = data.srcset;
    if (image.getAttribute("src") !== data.src) image.src = data.src;
  }
  observer.observe(image);
  update();
  return release;
}
