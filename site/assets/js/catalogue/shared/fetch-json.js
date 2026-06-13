export function fetchJson(url) {
  return fetch(url, { cache: 'default' })
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    });
}
