---
draft: false
doc_id: d-20260423-165116-c83a81
title: Broken Links Script
added_date: "2026-04-23 16:51:16"
last_updated: "2026-11-18"
parent_id: d-20260424-000000-50b63f

---

# Broken Links

## Saved Local Report

Opening Broken Links in Manage reads the last saved scan. **Refresh** explicitly audits the configured Working workspace and saves the completed result. The private output is selected by workspace `broken_links_report`, currently `working/generated/reports/broken-links/report.json`. Correct a finding's exact source, Save/rebuild it, then Refresh to update the diagnosis. [Source correction](Source_Editing.md) · [Workspace owner](../../docs-viewer/config/workspace/docs-workspace.json)

The report shows Last scanned and keeps previous results while refreshing or after a failed Refresh. Missing saved output gives an empty report. Invalid saved output reports an error. A failed audit preserves the prior snapshot. Ordinary builds and publication leave this explicit diagnostic snapshot with its report owner.

## Command Line

Run the existing read-only scan from the repository root with the configured process environment and project interpreter.

```bash
python3 docs-viewer/services/docs_broken_links.py --json
```

Omit `--json` for human output. `--repo-root PATH` overrides root detection. The CLI prints current findings independently of the saved report and writes no source, media or report snapshot. [Audit implementation](../../docs-viewer/services/docs_broken_links.py)

## Inputs And Destination Checks

The audit covers ordinary Index members and every configured collection, including Draft and publication-excluded sources. It reads exact source identity and tokens plus each source's last generated `content_html`. Missing generated output is recorded as unscanned for rendered links, while source token/media diagnosis continues.

Document destinations are checked at their exact collection/by-ID output. Local destinations use Working, and public destinations use configured repository projections. A label can differ from the current target title. Rendered code links, same-document fragments and fragment-only links are ignored. External websites and fragment existence are outside this scan. Retired stage/scope/subdocument routes are diagnosed as broken. [Rendered-link parser](../../docs-viewer/services/docs_rendered_links.py)

Work-token diagnosis reads the adopted Catalogue document's by-ID Work data. A Work pending Regenerate can therefore affect this diagnosis. Gallery-token diagnosis uses the generated Gallery record and media policy. Missing or invalid Work and Gallery inputs produce `missing_media` or `missing_gallery`. The saved report records these findings with issue type `semantic_token`. Distinct targets are checked once per scan, with a finding retained for each occurrence. [Catalogue adoption](Generated_Data_Contracts.md#catalogue-reference-and-presentation)

Docs-owned media references and assigned thumbnails are checked against their exact configured ready-media owner. The audit checks local file presence, with one result reused for each distinct identity. It reads no media bytes, contacts no R2 endpoint and scans no whole media inventory. Paths and correction links retain confinement and safety at their actual boundaries. [Media ownership](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

## Request And Result

`GET /docs/broken-links` accepts no parameters and reads the saved artifact, returning `report: null` if absent. `POST /docs/broken-links` takes an empty JSON object and awaits audit and persistence. The saved `docs_broken_links_report_v1` contains UTC `scanned_at`, finding summary, `entries` and `unavailable_sources`. Saved reads check their representation and safe correction links. The browser owns display sorting.

Each finding identifies its source collection and document ID. Token findings include raw token/range/target/reason. Missing Docs media includes type/identity and displays the logical reference as text. Unscanned sources remain visible as partial coverage. [Report service](../../docs-viewer/services/docs_management_broken_links_service.py) · [Earlier evidence](../deliveries/Document_Grammar_And_Review_Delivery.md#broken-links-evidence)
