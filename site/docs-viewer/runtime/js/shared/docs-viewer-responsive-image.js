/**
 * Match responsive selection to the slot width established by CSS before loading.
 * Release when the owning view is removed. Detached report fragments also disconnect
 * after their first connected observation.
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
    var width = image.getBoundingClientRect().width;
    if (width <= 0) return;
    var sizes = Math.ceil(width) + "px";
    if (image.sizes !== sizes) image.sizes = sizes;
    if (image.srcset !== data.srcset) image.srcset = data.srcset;
    if (image.getAttribute("src") !== data.src) image.src = data.src;
  }
  observer.observe(image);
  update();
  return release;
}
