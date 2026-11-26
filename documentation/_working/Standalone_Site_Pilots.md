---
draft: false
doc_id: d-20261122-160647-241260
title: Standalone Site Pilots
added_date: "2026-11-22 16:06:47"
last_updated: "2026-11-26"
summary: Test an unlinked static pilot in site-preview and on GitHub Pages, starting with a cross-origin read from R2.
ui_status: done
parent_id: d-20261118-235100-64ad2e
---
# Standalone Site Pilots

Use one tracked static page to test a feature locally and on the deployed site. Give each pilot a named folder under `site/pilot/` and share its direct URL. Keep the page outside the site's navigation and Docs Viewer routes. The first pilot proves that a browser can read an object from the existing R2 media host before the HLS pilot adds playlists, segments and a player. [Site preview and deploy](../guide/Publish_And_Deploy.md#3-review-and-deploy-the-site) · [Catalogue HLS Video Pilot](Catalogue_HLS_Video_Pilot.md)

## First Pilot With An R2 Image

| Item | Path or address |
| --- | --- |
| Static page in the repository | `site/pilot/r2-image/index.html` |
| Default local preview | `http://127.0.0.1:4000/pilot/r2-image/` |
| GitHub Pages on the site domain | `https://www.dotlineform.com/pilot/r2-image/` |
| Test object on the existing R2 bucket | `works/video/pilot/r2-image/test.webp` |
| Public object URL | `https://media.dotlineform.com/works/video/pilot/r2-image/test.webp` |

The test object is a copy of the already public Catalogue image `works/img/04813-primary-800.webp`. The page fetches the pilot URL once with JavaScript using a plain `GET`, then displays the decoded image or shows a failure message. The page and its script are served as one static file.

## Why The Browser Requires CORS

A regular `<img>` and an image fetched by JavaScript can both use `GET`. With a regular `<img>`, the browser reads and decodes the public image from R2 so it can display it. The browser's **same-origin policy** keeps the page's JavaScript from reading the bytes of that cross-origin response or extracting its pixels through a canvas. A JavaScript `fetch()` can read the response when the media server gives the page's origin permission through CORS. [Same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Same-origin_policy) · [Image embedding](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/img#crossorigin)

Imagine opening an unrelated website while signed into webmail. If the browser let that page read every response it could load, the page could request your inbox and copy its contents whenever the webmail service recognised your session. The browser enforces the boundary between those origins and lets each server choose which other origins may read its responses.

For this pilot, fetching the image in JavaScript exercises the permission that `hls.js` will need to read the HLS playlists and video segments. [hls.js CORS requirements](https://github.com/video-dev/hls.js#cors)

## Configure Cross-Origin Reads In R2

The page and the media are served from different origins. An **origin** is the scheme, hostname and port of the page. The browser sends it in the `Origin` request header. R2's cross-origin resource sharing policy, or **CORS**, tells the browser which origins may read the response. For the live pilot the page origin is `https://www.dotlineform.com` and the media request goes to `https://media.dotlineform.com`. The `/pilot/r2-image/` path is part of the page URL. The origin used in the policy ends at the hostname or port. [Cloudflare R2 CORS](https://developers.cloudflare.com/r2/buckets/cors/)

On 22 November 2026, read-only requests for the existing `works/img/04813-primary-800.webp` object returned HTTP 200 for both the default local and live page origins. Neither response included `Access-Control-Allow-Origin`. Check the current bucket policy and the new test object before deciding what to change.

1. Open the Cloudflare dashboard and go to **Storage & databases → R2 → Overview**. Select the existing bucket whose **Settings → Custom Domains** lists `media.dotlineform.com`. [R2 custom domains](https://developers.cloudflare.com/r2/buckets/public-buckets/#custom-domains)
2. In that bucket's **Settings**, find **CORS Policy** and review the current rules. If the rules already allow `GET` from the exact pilot origins, use them. Otherwise, choose **Add** or edit the existing policy and enter the JSON. Add the missing origin to a suitable read rule or add a new rule. Preserve the existing rules when saving. The example is a complete policy for a bucket with no existing rules, or a rule to merge into the current policy array. [Dashboard CORS procedure](https://developers.cloudflare.com/r2/buckets/cors/#add-cors-policies-from-the-dashboard)

```json
[
  {
    "AllowedOrigins": ["http://127.0.0.1:4000", "https://www.dotlineform.com"],
    "AllowedMethods": ["GET"]
  }
]
```

3. Save the policy, then check the test object's response for each origin. If you use a different preview address, use that exact origin in the rule and the check. For example, `http://localhost:4000` or a Mac's LAN address used by an iPhone would be its own origin. The policy applies to the bucket and controls whether JavaScript on those page origins may read its public responses. [Origin matching](https://developers.cloudflare.com/r2/buckets/cors/#common-issues)

```bash
curl -fsS -D - -o /dev/null \
  -H 'Origin: http://127.0.0.1:4000' \
  'https://media.dotlineform.com/works/video/pilot/r2-image/test.webp'
```

Repeat with `Origin: https://www.dotlineform.com`. Expect HTTP 200 and an `Access-Control-Allow-Origin` response header matching the supplied origin. Use the fresh pilot object for this check. If the response still carries old headers after a policy change, use **Caching → Configuration → Custom Purge → Prefix** with the pilot image's hostname and full path to clear its cached variants, then retest the original URL. Confirm the read in the browser. The HLS pilot will separately check requests for its actual playlists and segments. [R2 CORS on custom domains](https://developers.cloudflare.com/r2/buckets/cors/#use-cors-with-a-custom-domain) · [Cloudflare purge by prefix](https://developers.cloudflare.com/cache/how-to/purge-cache/purge_by_prefix/)

## Verify, Deploy And Retire

- [x] Created the page and copied the public Work 04813 WebP to the pilot key. `bin/site-validate` passed on 26 November 2026. The exact preview route showed the fetch failure while the R2 response lacked the CORS header. The page makes one request, checks the HTTP status and decodes the image before displaying it. [Verification](../development/Verification.md)
- [x] Added one `GET` rule for the two pilot origins to `dotlineform-media`. The bucket had no prior CORS policy. The original URL initially served cached responses without the new headers, so the exact pilot image prefix was purged. The original URL then returned HTTP 200 with the matching `Access-Control-Allow-Origin` for each origin, and the browser displayed the image from `site-preview`.
- [x] Released the pilot on 26 November 2026 through the manual **Public site** workflow. The deployed `site/` delta contained only the pilot page. At `https://www.dotlineform.com/pilot/r2-image/`, the browser fetched and displayed the same R2 WebP and reported success. [GitHub Pages deployment](https://github.com/dotlineform/dotlineform-site/actions/runs/45812962314) · [Deploy procedure](../guide/Publish_And_Deploy.md#3-review-and-deploy-the-site)
- [ ] Agree which pilot assets to retain for follow-on work. Retire a finished pilot by removing its `site/pilot/<name>/` folder in a later Pages release and removing its temporary R2 objects once they are no longer used. Keep CORS origins used by the HLS pilot or other consumers.
