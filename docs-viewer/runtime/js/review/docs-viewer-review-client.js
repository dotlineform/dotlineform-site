function cleanBaseUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function queryString(values) {
  var params = new URLSearchParams();
  Object.entries(values || {}).forEach(function (entry) {
    var value = String(entry[1] == null ? "" : entry[1]).trim();
    if (value) params.set(entry[0], value);
  });
  var text = params.toString();
  return text ? "?" + text : "";
}

export function requestDocsReviewJson(path, options) {
  var settings = options || {};
  var fetchImpl = settings.fetch || window.fetch.bind(window);
  var requestOptions = {
    headers: { Accept: "application/json" },
    cache: "no-store"
  };
  if (settings.body) {
    requestOptions.method = "POST";
    requestOptions.headers["Content-Type"] = "application/json";
    requestOptions.body = JSON.stringify(settings.body);
  }
  return fetchImpl(cleanBaseUrl(settings.baseUrl) + path + queryString(settings.query), requestOptions)
    .then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (payload) {
        if (response.ok) return payload;
        var error = new Error(payload.error || "Docs Review request failed (" + response.status + ")");
        error.status = response.status;
        throw error;
      });
    });
}
