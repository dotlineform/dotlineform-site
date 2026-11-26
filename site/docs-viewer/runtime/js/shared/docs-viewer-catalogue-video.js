/** Load the player library only for a film on a browser without native HLS. */
var hlsLibrary;

function loadHlsLibrary(document) {
  if (!hlsLibrary) {
    hlsLibrary = new Promise(function (resolve, reject) {
      var script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/npm/hls.js@1.7.4/dist/hls.min.js";
      script.integrity = "sha384-p9vgU/7IYJWd3I4STrtqxqR/2cAQlhIX7D/HrTnIMEjjcUox165b7se7sxmm3zDg";
      script.crossOrigin = "anonymous";
      script.addEventListener("load", function () { resolve(document.defaultView.Hls); }, { once: true });
      script.addEventListener("error", function () {
        script.remove();
        reject(new Error("The video player could not be loaded."));
      }, { once: true });
      document.head.append(script);
    }).catch(function (error) {
      hlsLibrary = null;
      throw error;
    });
  }
  return hlsLibrary;
}

/** Attach playback for one Catalogue player and return its release action. */
export function mountCatalogueVideo(video, status, url) {
  var active = true;
  var player = null;

  function showError(message) {
    if (!active) return;
    status.textContent = message;
    status.hidden = false;
  }

  function onMediaError() {
    showError("The video could not be played.");
  }

  video.addEventListener("error", onMediaError);
  if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = url;
  } else {
    loadHlsLibrary(video.ownerDocument).then(function (Hls) {
      if (!active) return;
      if (!Hls?.isSupported()) {
        showError("HLS playback is unavailable in this browser.");
        return;
      }
      player = new Hls();
      player.on(Hls.Events.ERROR, function (_event, data) {
        if (data.fatal) onMediaError();
      });
      player.loadSource(url);
      player.attachMedia(video);
    }).catch(function (error) { showError(error.message); });
  }

  return function release() {
    active = false;
    video.removeEventListener("error", onMediaError);
    video.pause();
    if (player) player.destroy();
    if (video.hasAttribute("src")) {
      video.removeAttribute("src");
      video.load();
    }
  };
}
