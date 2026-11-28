---
draft: false
doc_id: d-20261126-204215-5f1e47
title: Catalogue Search And Ranking
added_date: "2026-11-26 20:42:15"
last_updated: "2026-11-27"
summary: How Catalogue search differs from Index Search and how it prioritises Work titles.
ui_status: done
parent_id: d-20260602-160839-6d3cbb
---
# Catalogue Search And Ranking

## How The Two Searches Work

**Index Search** loads a prepared search file for the selected scope. Portfolio search covers eligible page, collection and Gallery titles. Collection scopes can search additional fields such as summaries, headings or body text, depending on the scope. [Index search scopes](../reference/Reader_Discovery_And_Return.md#scope-and-eligibility)

The Catalogue’s **work or gallery** field matches Work titles and IDs live in the browser using the Catalogue manifest. It loads a separate lookup for Gallery titles and direct memberships. The browser puts matching Gallery titles first, then Galleries containing matching Works, then individual Works. [Catalogue collection browsing](../reference/Reader_Discovery_And_Return.md#catalogue-collection-browsing)

## Why A–Z Prioritises Work Titles

Before title priority, searching for `nerve` under A–Z put the Work *nerve* (`00008`) at result 22 in the snapshots checked on 26 November 2026. Seven Galleries came first, followed by fourteen Works whose titles sort before *nerve*.

Under **A–Z**, the browser now puts exact Work titles first, followed by titles starting with the query and then other matches. It walks the already ordered Work matches once, so each set stays alphabetical. In the same snapshots, that puts *nerve* first among Works and eighth overall. [Catalogue search code](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js)

Three priority groups give the same order as three numeric scores. Scores become useful when several signals should add up, such as title word order, a Medium match or a small recency boost. Ranking existing matches uses the data already in memory. Searching additional fields requires loading those fields, and typo tolerance can grow more expensive if it compares every query against every title.

## Verification And Release

Focused JavaScript lint, the public projection check and site validation passed. The user confirmed deployment of the ranking change on 26 November 2026.
