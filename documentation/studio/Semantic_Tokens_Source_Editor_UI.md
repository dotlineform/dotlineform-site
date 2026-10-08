---
draft: false
doc_id: d-20260623-180405-631ef4
title: Semantic Tokens Source Editor UI
added_date: "2026-06-23 18:04:05"
last_updated: "2026-10-08 18:18:38"
summary: Create and edit supported Catalogue occurrences through their modals in one complete Markdown Source buffer.
parent_id: d-20260725-153656-516b61
---
# Semantic Tokens Source Editor UI

The manage-only Source editor provides actions for document references and Catalogue media. All use the complete Markdown textarea, exact mounted Working document target and shared dirty session. **Edit document** opens front matter and body in the same buffer. Source has no metadata/token panel or **i** toggle; selection alone opens nothing.

| action | selection and output |
| --- | --- |
| **Insert doc link** | Select an exact document from the workspace's eligible collections; insert its title and ordinary Markdown document location. |
| **Add Media View link** | Select an exact Catalogue Work or Gallery and link text; create or edit its Media View opener. |
| **Add Catalogue Image** | Select an exact Catalogue Work; create or edit its image identity, title-caption choice, optional static summary, placement and width. |
| **Add image** | Insert Docs-owned staged media through its existing media publication workflow. |

**Add Catalogue Token**, **Insert Subject Link** and Concept-token authoring are retired. Subject assignment and ordinary local-folder paste/open remain independent supported workflows. Scope-specific button policy is proposed separately in [Scope-configured Authoring Controls](Scope_Configured_Authoring_Controls.md).

## Creation And Guarded Insertion

Opening a document or Catalogue selection modal captures the source selection, mounted adapter and buffer revision before focus moves. Confirmation validates the chosen target and required occurrence fields, then replaces that captured selection or inserts at the captured cursor. A stale buffer or changed editor leaves source unchanged with a contained error.

The Catalogue actions use Catalogue identity and generated media independently of whether a related document exists. They do not filter candidates by document collections or Subject associations.

Selecting a Catalogue target, including through **Use document subject**, validates its media without a transient loading message. Confirmation remains disabled until validation completes; failures appear in the status area.

The modal starts with search status and results hidden. Results appear only when the query has matches; an empty result container contributes no padding or grid gap. Initial Catalogue loading and subject selection add no transient status row.

The modal changes the ordinary dirty buffer. The session's Save owns the complete source write; watcher generation and displayed-output refresh run independently. Cancellation leaves source unchanged. The generic editor owns focus, selection and dirty-state projection. **Use document subject** reads a safe projection of the captured unsaved buffer through the source service. Invalid front matter leaves that optional choice unavailable with a visible error; it does not reset existing token fields or prevent choosing a Catalogue target.

## Media View Link

The modal searches generated Work/Gallery targets by title or identity, lets the author choose a target and supply link text, and validates its current media presentation before insertion or Apply. The resulting token stores the exact canonical target ID and escaped occurrence text. Work IDs contain five digits; Gallery IDs retain the registry's canonical identity.

Activation opens that exact Work or Gallery in Media View. Series is not a token target.

## Catalogue Image

The image modal uses the same generated Work target source and validates the selected primary image. **Use document subject** and the search field share one row. Search retains its accessible name without a visible Search Catalogue label. The image fields are **Title caption**, **Summary** and **Layout**; Summary remains optional authored text. The search input, summary box and layout controls share a fixed label column and left edge; the search input and summary box have equal widths. The search icon sits immediately before that shared field edge. The image modal uses a narrower 48rem card, bounded by the available window width. **Full**, **Left** and **Right** form the layout radio group, followed by **Fill available width** on the same row. The modal displays no derived-alt value or caption preview. Build still derives alt text from the current Work title and includes the title caption only when selected. The visible caption can be absent while the authored summary remains. Add and Edit expose the same fields; illustrative images have no Work-metadata option.

The stored `catalogue:image:work` token contains exact Work identity, explicit choices and presentation settings, plus any authored summary. It stores no literal Work title, alt text, caption, metadata or resolved media URL, and it does not acquire document identity. The modal validates the selected current media presentation before insertion; document Build derives the selected text from the generated Work record.

Supported token forms and identity rules remain owned by [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md). Creation and editing use the same grammar and target families; images support Works only.

## Existing Occurrences

Use the corresponding Catalogue action with the caret strictly inside a supported occurrence or its exact range selected. The modal opens in edit mode with the stored target and every authored field populated, and confirmation is labelled **Apply**. With no matching occurrence, the action keeps normal creation behavior. Selecting or moving the caret alone does not open a modal.

Recognition reads the current unsaved body, excluding front matter, fenced/inline/indented code, comments, `<pre>` blocks and escaped literal examples. Valid token fields are treated atomically, so plain authored link text containing backticks or comment markers does not change the surrounding context. Captured occurrence offsets include the current header length. Malformed or unsupported token-like text remains literal.

A Media View-link occurrence retains its authored link text. An image retains its title-caption choice, optional static summary, placement and fill-width. Build derives Work title/alt from generated data without changing stored choices. The same picker allows selecting another supported target. Unavailable identities and failed media reads remain visible while the source and entered presentation values remain available.

Ordinary Markdown links have no editing modal in this workflow. Title/Summary and other valid metadata are edited directly in the complete Source buffer. The rendered reader panel retains its independent related-links pinning owner.

## Apply, Save And Lifecycle

Apply validates modal values and current media, serializes the token and replaces only the captured occurrence. It checks exact text/range, buffer revision and the mounted adapter before mutation. A changed buffer or replaced editor produces a contained error and leaves source unchanged. Cancel leaves the buffer unchanged; failed validation retains the modal values for correction.

After Apply, token text in the buffer is authoritative. There is no pending token-field draft or later token serialization during Save. The single Save validates the complete Markdown and mounted identity before one atomic source write. Failed validation or persistence retains the full draft. Range/revision checks protect in-session mutations; they are not disk-concurrency checks.

Token removal is an ordinary text edit. Leaving Source offers one discard decision covering front matter, body and applied token changes.

Modal work belongs to its captured Source adapter. Teardown invalidates that adapter, so late work cannot mutate a replacement session. Entering Source closes any reader capture, and returning to rendered content leaves the reader panel closed until a pin is used.

## Ownership And Review

The generic Source adapter owns the complete buffer, snapshots, captures and guarded mutations. The service/source model owns front-matter validation and persistence. Focused Catalogue contributions own modals, initialization and token serialization. The shared content-detail host owns Media View presentation; the [Architecture](Semantic_Tokens_Architecture.md) records Build, generated data and public ownership.

Current Source tests retain superseded contracts and are unreviewed for this workflow. [Source Editor Scripts](Source_Editor_Scripts.md) records the evidence limit. Toolbar fit, modal values/feel, selection and ordinary navigation remain user manual review concerns; automated test work requires a separately agreed specification.
