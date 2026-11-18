---
draft: false
doc_id: d-20260904-173415-b28651
title: Catalogue Archive
added_date: "2026-09-04 17:34:15"
last_updated: "2026-11-18"
summary: How the legacy Catalogue site and R2 media were frozen on 4 September 2026.
parent_id: d-20260720-161656-1357d0
---
# Catalogue Archive

The legacy Catalogue was frozen on 4 September 2026 in [UAC 1](archive/UAC_1_Freeze_Legacy_Catalogue.md). The active Catalogue is part of the public Docs Viewer at `/`. [Browse the Catalogue](../guide/Find_And_Read_Things.md#browse-the-catalogue)

## Site Snapshot

The pre-archive Git revision is `519c49bbaa43ddfcdddc2521ef95bf2c4eccf95f`. Catalogue pages, payloads, Search/Recent indexes, browser code and thumbnails moved into `site/archive/`. Shared styles, scripts and icons were copied so later active-site edits do not change the archive.

`/archive/` opens the frozen Series index, with routes beneath it for Series, Works, Work Details, Recent and Search. Search and Recent retain their existing data; they are not rebuilt from changing canonical data. The active homepage directly hosts the public Docs Viewer at `/`. The archive remains in the published site, with no direct links to `/archive/`. Former Catalogue routes have no redirects.

On 8 October 2026, `/about/` and every site footer were removed, including the archived page footers and the public Docs route template. Archive header labels no longer link directly to `/archive/`; the archive's internal Series, Works, Work Details, Recent and Search navigation remains available. The About page has no redirect or replacement route.

## Historical Reader References

The frozen Search route is `/archive/search/`. Its [policy](../../site/archive/assets/data/search/policy.json) and [Work and Series index](../../site/archive/assets/data/search/catalogue/index.json) were retained with the snapshot. [Catalogue Search](archive/Catalogue_Search.md) records the former builder and ranking design. [Catalogue Search Policy](archive/Catalogue_Search_Policy.md) records the browser controls.

The [design](archive/Public_Catalogue_Design.md), [route model](archive/Public_Route_Model.md) and [data flow](archive/Public_Catalogue_Data_Flow.md) describe the site before relocation. Their original route and code paths identify the pre-archive revision above.

## R2 Copy

Portable rclone v1.75.0 was installed under ignored `var/tools/rclone/`. The `uac` remote used the Cloudflare S3 provider and existing `.env.local` credentials supplied through environment variables. After successful dry runs against an empty destination, these server-side copies ran within the same bucket:

```bash
rclone copy "uac:${R2_BUCKET}/works/" "uac:${R2_BUCKET}/archive/catalogue/works/" --metadata --transfers 8
rclone copy "uac:${R2_BUCKET}/work_details/" "uac:${R2_BUCKET}/archive/catalogue/work_details/" --metadata --transfers 8
```

All 13,891 objects (1.75 GB), including unlinked objects, copied in about 17 minutes without errors. HTTP metadata was preserved; original objects remained intact. Docs and home media were outside the copy. One-off wrappers and ordinary progress logs remain under ignored `var/uac-1/`.

Archive image and download URLs now use `https://media.dotlineform.com/archive/catalogue/`. Local preview was accepted, including opening copied Work images, Work Detail images and PDFs in new tabs. This delivery did not deploy the public site.

## Freeze-Time Pause

The freeze left Studio canonical data in place. Catalogue authoring, builds and media commands paused until the new projection was ready. During that pause, Docs Deploy Repo and document-URL Refresh and Delete reported Catalogue as paused while independent Docs operations continued. The active authoring and publishing workflow resumes through Studio and Working and leaves the archive frozen. [Maintain the Catalogue](../guide/Maintain_The_Catalogue.md)
