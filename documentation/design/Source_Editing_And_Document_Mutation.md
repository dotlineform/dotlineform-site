---
draft: false
doc_id: d-20261118-211800-26fde1
title: Source Editing And Document Mutation
added_date: "2026-11-18 21:18:00"
last_updated: "2026-11-18"
summary: Rationale for the complete buffer, exact mutation ownership and phase-specific completion.
parent_id: d-20261118-151521-a0f9c3
---
# Source editing and document mutation

## One mounted document, one complete draft

Title, Summary, directives and body edits stay together until Save. The editor captures the target and the buffer range while it owns them, so an asynchronous picker can apply a choice to the intended occurrence. The same dirty decision covers text and pending Files. This replaced separate editing panels and delayed token-draft serialization. [Accepted Source delivery](../deliveries/Source_Editor_And_Token_Modals_Delivery.md) · [Current session](../reference/Source_Editing.md#target-and-session)

## Write each effect at its owner

The browser already knows the edited draft and selected files. The service resolves their configured destination, validates the complete candidate once and carries the result through media writes, source persistence and exact generation. This keeps ordinary edits independent of full builds and discovery refresh. The committed record tells retained views which metadata changed, while a fresh by-ID read supplies what the editor must display. [Current Save handoff](../reference/Source_Editing.md#follow-a-save) · [Save and Build optimisations](../deliveries/Save_Build_Optimisations.md)

Readiness, Star, Position and Delete remain separate intentions. A change to Index order can preserve Markdown and relationships. Star owns its saved list, and a confirmed Delete already knows which identities were removed. Passing each completed effect to generation keeps its source of truth visible. [Mutation owners](../reference/Source_Mutation_Endpoints.md)

## Local dispatch and saved reads

The HTTP boundary frames bounded requests, process capability and permitted origins. The browser supplies an exact target and intention; a focused operation owns required filesystem work and carries resolved inputs/effects through generation. Moving a control or changing a route map does not transfer that operation's authority.

Saved generated reads have no authoring or freshness decision to make. Direct by-ID lookup keeps content identity independent of tree membership; a named collection supplies its own configured artifact boundary. Explicit document generation, discovery Refresh and queue-only Publish can therefore advance independently. HTTP caching reuses a representation without becoming another generation or publication ledger. [Current service map](../reference/Endpoint_Overview.md)

## Keep partial completion visible

Source persistence, generation, publication handoff and browser display can each fail after earlier effects have completed. The return contract reports the phase and lets the editor take saved source as its baseline. The author can correct the failed owner and rebuild or reload as appropriate. General disk-conflict handling and richer editing remain separate product decisions. [Save recovery](../reference/Source_Editing.md#if-save-stops) · [Source follow-ons](../deliveries/Source_Editor_And_Token_Modals_Delivery.md#follow-on)
