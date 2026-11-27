---
draft: false
doc_id: d-20261126-221122-5cdb8e
title: Authored Page Breaks For Texts
added_date: "2026-11-26 22:11:22"
last_updated: "2026-11-27"
summary: Accepted authored page turns and continuous reading in Texts, piloted with the 12-page Nerve edition.
ui_status: done
parent_id: d-20260602-160839-6d3cbb
---
# Authored Page Breaks For Texts

Closed on 27 November 2026 after the user verified the reading behaviour and approved closeout. *Nerve* is one Texts edition with 11 authored breaks, 12 pages and one reading link from Catalogue Work `00008`. [Reader behaviour](../reference/Reader_Discovery_And_Return.md#authored-pages-in-texts) · [Source authoring](../reference/Source_Editing.md#directives)

## Code Review

- Generation recognises standalone, top-level breaks in Texts and produces one full document payload. The existing Markdown parser protects code and nested content. Read-only diagnostics confirmed that fenced, indented, inline and quotation examples stay literal. The static HTML renderer retained the complete text and linked Catalogue image.
- The browser groups the mounted content once when it finds break markers. The toolbar follows the active rendered document, and the pager reuses the Library pagination control and the reader's Back handling. Returning to paged mode checks the viewport once at the switch. The URL parser handles the page number, and the mounted pager resolves it against the actual page count. Page controls reuse the loaded body without additional reads or writes.
- A Manage check reproduced the 15 px shift on switching modes. The page-start offset now includes the same top padding as the main document. The cover stayed at the same height on page 1, and switching modes on page 2 retained both its alignment and URL. The final review left no open implementation findings.

## Verification And Release

- The exact Working build rendered one Texts document with zero warnings using `build_docs.py --stage working --write --collection texts --only-doc-ids d-20261127-100053-b77c4f --skip-media-builds`. The dry run for the ordinary Texts host passed. Focused lint, `bin/site-code-update --check`, `bin/site-validate` and whitespace checks passed.
- Manage browser checks covered both **Go to page 1** controls, keyboard page turns, bookmark reload, Back, both reading modes and the toolbar's removal and restoration across document navigation. The user verified the behaviours and approved closure. The recorded browser checks were scoped to Manage.
- Closeout confirmed that Working and the tracked public snapshot contain identical Nerve HTML and Catalogue references and that Nerve has cleared the publication queue. The public runtime was projected locally. The runtime changes remained uncommitted at closeout, and live GitHub Pages deployment was outside this verification. [Release workflow](../guide/Publish_And_Deploy.md)

## Follow-ons

**Go to page** makes the page count actionable by touch, click and keyboard. Activating it opens a field with the valid page range. Submitting a valid page number opens that page at its start and replaces the current page number in the URL.

A full-text **Search Texts** scope remains a separate option if readers need to find an edition by a phrase. Portfolio Search covers eligible Texts titles. [Search scope](../reference/Reader_Discovery_And_Return.md#scope-and-eligibility)
