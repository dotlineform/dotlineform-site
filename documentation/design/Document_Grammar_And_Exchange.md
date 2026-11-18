---
draft: false
doc_id: d-20261118-192400-5c92b1
title: Document Grammar And Exchange
added_date: "2026-11-18 19:24:00"
last_updated: "2026-11-18"
summary: Rationale for stable document targets, bounded source syntax and package-local Review authority.
parent_id: d-20261118-151521-a0f9c3
---
# Document grammar and exchange

## Stable targets and authored meaning

Titles and placement help people find a document. The immutable code carries its identity through edits, movement and exchange, with the configured collection identifying its owner. Date and randomness in a new ID provide allocation inputs. They do not define the document's current subject. Catalogue deliberately uses its existing Work ID for adopted Work documents. [Current identity and source grammar](../reference/Document_Identity.md)

Authored links and typed Catalogue references have different presentation roles. The relationship model records exact directed document endpoints, while Gallery media references preserve their separate context. Keeping link diagnosis explicit lets ordinary editing and rendering proceed with their own completed inputs. [References](../reference/Document_And_Catalogue_References.md) · [Audit](../reference/Broken_Links.md)

## Choose a representation for its consumer

Word Title becomes the document H1, and Word section headings start at H2. HTML conversion preserves readable structure and warns when a structure has to be simplified. That gives canonical Markdown a defined result from another format. Structured packages use rendered-derived text for external editing. A summary-only return can preserve the canonical body by omitting content. [Import mapping](../reference/HTML_Import_Mapping.md) · [Package fidelity](../reference/Document_Packages.md#package-output)

## Inspect before accepting canonical changes

Review retains package-local source and generated output so a person can inspect the edited return independently. Its Build refreshes that projection, and VS Code opens the exact package member. Canonical Import separately establishes destination, prepared membership, source versions and overwrite fields. This keeps visual acceptance and mutation authority with their respective owners. [Review authority](../reference/Docs_Review.md#review-authority)

Metadata separation and authored link strength have their own pending design choices. Their records remain in Working until an implementation scope is settled. [Metadata proposal](../_working/Document_Content_And_Metadata.md) · [Link strength](../_working/Document_Link_Strength.md)
