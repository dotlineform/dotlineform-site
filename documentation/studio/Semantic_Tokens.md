---
draft: false
doc_id: d-20260725-153656-516b61
title: Semantic Tokens
added_date: "2026-07-25 15:36:56"
last_updated: "2026-11-18"
summary: Explain current Catalogue media and image tokens, authoring, document relationships, and the public boundary.
parent_id: d-20260424-000000-50b63f
---
# Semantic Tokens

The supported semantic source forms identify Catalogue media independently of documents. **Add Media View link** inserts a text opener for one exact Work or Gallery. **Add Catalogue image** inserts a Work image with authored presentation options. Detail and Series token forms and document Subjects are retired.

Ordinary document references use **Insert doc link**, which selects an exact document and inserts a Markdown link. **Add Catalogue Token** and **Insert Subject Link** are retired, together with their old three-part text-token syntax. Concept/Moment IDs and Concept tokens are also retired; documents in those collections use ordinary document identity. There are no compatibility aliases for the retired forms.

## Authoring

1. Select source text or place the cursor, then choose the appropriate document-link, Media View-link or Catalogue-image action.
2. Select a concrete target and complete the action's required fields. Catalogue media selection is Catalogue-owned and does not require a related document.
3. The action inserts through the captured, revision-guarded Source range. Save owns writing and the document rebuild.
4. A caret inside a supported Catalogue token opens its Info view. Update edits only occurrence fields; removal deletes the exact token range. Identity changes require removing the occurrence and inserting a new one.

See [Source Editor UI](Semantic_Tokens_Source_Editor_UI.md) and [Source Editor Scripts](Source_Editor_Scripts.md) for the current actions and mutation boundaries.

## Build And Runtime

Work/Gallery media links and Work image tokens become HTML markers carrying exact Catalogue identity and authored presentation. The browser resolves these through generated Catalogue data and opens [Media View](Catalogue_Media_View.md). Their document Build does not require a private target-lookup row or a corresponding document.

Malformed or retired token forms remain literal. Existing authored Series media tokens were left in Working source at the user's request. The read-only [Docs Broken Links](Broken_Links_Script.md) audit diagnoses supported media targets through their current owners.

## Ownership And Data

- Catalogue owns Work, Series and Gallery identities; Media View presents Work images and Gallery memberships.
- Docs Viewer owns source ranges, token parsing, rendering markers and Source Info contributions.
- The checked registry at `docs-viewer/config/semantic-tokens/registry.json` declares Catalogue Work/Gallery definitions and the Info contribution. It is not a target store or a per-scope toolbar policy.
- Catalogue target discovery reads current generated indexes through `/docs/catalogue-media-targets`. The former private discovery file, builder and browser file loader are retired; no separate lookup refresh is required. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns this boundary.
- Document Build records relationships from supported Work tokens to their Catalogue documents for [Related Links](Related_Links.md). Gallery tokens identify Media View targets. The former usage index and its report are retired. [Document relationships and audit](Semantic_Tokens_Architecture.md#document-relationships-and-audit)

Public readers use the prepared document presentation and configured Catalogue data. Publish and deployment remain separate operations. [Catalogue reference and presentation](Generated_Data_Contracts.md#catalogue-reference-and-presentation)
