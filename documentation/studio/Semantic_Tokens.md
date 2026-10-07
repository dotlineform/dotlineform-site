---
draft: false
doc_id: d-20260725-153656-516b61
title: Semantic Tokens
added_date: "2026-07-25 15:36:56"
last_updated: "2026-10-07 16:05:28"
summary: Explain current Catalogue media and image tokens, authoring, generated usage, ownership, and the public boundary.
parent_id: d-20260424-000000-50b63f
---
# Semantic Tokens

The supported semantic source forms identify Catalogue media independently of documents. **Add Media View link** inserts a text opener for one exact Work or Gallery. **Add Catalogue Image** inserts a Work image with authored alt text and optional caption presentation. Detail and Series token forms are retired; Series remains an independent document Subject.

Ordinary document references use **Insert doc link**, which selects an exact document and inserts a Markdown link. **Add Catalogue Token** and **Insert Subject Link** are retired, together with their old three-part text-token syntax. Concept/Moment IDs and Concept tokens are also retired; documents in those collections use ordinary document identity. There are no compatibility aliases for the retired forms.

## Authoring

1. Select source text or place the cursor, then choose the appropriate document-link, Media View-link or Catalogue-image action.
2. Select a concrete target and complete the action's required fields. Catalogue media selection is Catalogue-owned and does not require a related document.
3. The action inserts through the captured, revision-guarded Source range. Save owns writing and the document rebuild.
4. A caret inside a supported Catalogue token opens its Info view. Update edits only occurrence fields; removal deletes the exact token range. Identity changes require removing the occurrence and inserting a new one.

See [Source Editor UI](Semantic_Tokens_Source_Editor_UI.md) and [Source Editor Scripts](Source_Editor_Scripts.md) for the current actions and mutation boundaries.

## Build And Runtime

Work/Gallery media links and Work image tokens become HTML markers carrying exact Catalogue identity and authored presentation. The browser resolves these through generated Catalogue data and opens [Media View](Catalogue_Media_View.md). Their document Build does not require a private target-lookup row or a corresponding document.

Malformed or retired token forms remain literal and produce no usage row. Existing authored Series media tokens were left in Working source at the user's request; they do not open Media View after rebuild. The read-only [Docs Broken Links](Broken_Links.md) audit diagnoses supported media targets through their current owners.

## Ownership And Data

- Catalogue owns Work, Series and Gallery identities; Media View presents Work images and Gallery memberships.
- Docs Viewer owns source ranges, token parsing, rendering markers, generated occurrence data and Source Info contributions.
- Subject metadata owns what a document is about. A body token is an authored occurrence and never creates or changes a Subject association.
- The checked registry at `docs-viewer/config/semantic-tokens/registry.json` declares Catalogue Work/Gallery definitions and the Info contribution. It is not a target store or a per-scope toolbar policy.
- Working collection Subject labels and assignment choices use the existing stage-bound Catalogue provider and its generated Work/Series targets. Work Save completes those indexes; reloading the collection page or reopening its Subject picker reads the saved titles. Subject identity and document navigation remain separate from those display labels.
- Catalogue target discovery reads current generated indexes through `/docs/catalogue-media-targets`. The former private discovery file, builder and browser file loader are retired; no separate lookup refresh is required. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns this boundary.
- Each configured scope or stage owns `generated/documents/semantic-tokens/index.json`. Work media occurrences carry identity with an empty `href`; runtime resolution supplies their media presentation. The [Semantic Tokens Report](Semantic_Tokens_Report.md) consumes this generated inventory.

Public readers use rendered HTML and public generated Catalogue data. They do not load the private token registry, management lookup or local usage index. Publish and deployment remain separate operations.

Further detail: [Architecture](Semantic_Tokens_Architecture.md), [Usage Index](Usage_Index.md), and [Doc Relationships](Doc_Relationships.md).
