---
draft: false
doc_id: d-20260930-195002-b3417e
title: Related Links
added_date: "2026-09-30 19:50:02"
last_updated: "2026-11-20"
summary: Author-inserted related-links directive, a sorted list with collection icons, and build-time relationship snapshots in document JSON.
parent_id: d-20260419-000000-d2e47b
---
# Related Links

Related Links is a generated section inside a document. It lists incoming document relationships, explicit outgoing document links and authored Gallery openers. Work Media View uses its own Gallery and Context links. [Media View link sources](Catalogue_Media_View.md#what-links-appear)

## Authoring Decision

Put `[[links|]]` on its own line. **Directives → Insert related links** inserts it with the caret after the pipe. An optional literal heading, as in `[[links|Further reading]]`, renders as H2 in Catalogue documents and H3 elsewhere. Empty or whitespace-only headings render without a heading. Code examples stay literal. A document without the directive, or with no qualifying links, has no generated section or pin.

Each exact destination appears once. Entries sort by case-folded title or label, then destination identity. The first occurrence naming a Gallery supplies its row label, including a paired image or hidden link. A Work association gives the Work’s Catalogue document an incoming backlink. The referring page also lists that Catalogue document if it explicitly links there or receives a link from it. A Catalogue search URL keeps its query in the original authored link. A direct link to the Catalogue report is a document relationship. [Source forms](Document_And_Catalogue_References.md#supported-source-forms) · [Section renderer](../../docs-viewer/build/docs_builder/related_links.py)

The reader adds **Pin related links** to non-empty sections, including heading-free sections. It captures the already loaded title, optional summary and same list. Gallery buttons open Media View from the document displayed at activation. HTML Export retains the list and displays Gallery labels as text. [Info Panel](Info_Panel.md)

## Selected Icons And Collection Configuration

The list uses decorative destination icons and omits bullet markers. Collection icons come from workspace configuration, ordinary documents use the document icon and Gallery rows use `images`. The Catalogue report host uses the configured Catalogue icon. [Collection icons](Source_Organisation.md#collection-icons) · [Icon renderer](Icon_Tokens.md)

## Generated Data And Freshness

Ordinary authored document links and supported Work image, Entry and Media View tokens contribute exact document edges. Work tokens point to that Work's Catalogue subdocument. A Work's own Entry is a self-reference and is omitted. There is no Gallery document endpoint. Gallery rows are added at section rendering from parsed Gallery references, outside the document graph. Generated rows create no authored edges. [Relationship builder](../../docs-viewer/build/docs_builder/links_builder.py)

Source Save and **Edit doc → Rebuild** update the selected saved relationships before rendering. They carry exact affected direct neighbours through generation where needed. A complete Build finishes relationship maintenance before rendering, including Catalogue's `[[links|context]]` sections. The section uses refreshed or saved per-document version-5 `links-by-id` records. Each outgoing row carries `explicit_doc_link`. Build filters outgoing rows on that evidence before combining them with incoming rows. The local Links diagnostic report uses those records too. The reader uses the section already embedded in by-ID JSON. [Builder](Builder.md) · [Generation owner](../../docs-viewer/services/docs_generation.py)

Publication eligibility determines which bodies reach Public. The prepared list can retain an authored destination whose body was excluded, giving the normal unavailable-document response when followed. Publish transfers completed queued bytes. Broken Links is the separate audit for unresolved targets. [Publish and deploy](../guide/Publish_And_Deploy.md) · [Broken Links](Broken_Links.md)

The standalone per-document Links view and Documents Linking Here report were retired. [Design](../design/Media_View_And_Document_Relationships.md) · [Delivery and outstanding review](../deliveries/Media_View_And_Document_Relationships_Review.md)
