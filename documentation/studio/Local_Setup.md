---
draft: false
doc_id: d-20260413-000000-d314b7
title: Local Setup
added_date: 2026-04-13 00:00:00
last_updated: "2026-08-14 21:18:02"
parent_id: ""

---
# Local Setup

This guide centralizes the current local toolchain needed to run the Python scripts in this repo and to verify the static public site locally.

For cloud-hosted development guidance, see [Cloud Environments](Cloud_Environments.md).
For dependency-role guidance across local and cloud environments, see [Runtime Dependencies](Runtime_Dependencies.md).

All commands assume you are in `dotlineform-site/` unless stated otherwise.

## Local App Boundaries

The local development stack is split into sibling services:

- `bin/site-preview` for the public static-site preview
- `bin/local-studio` for Local Studio catalogue/tag workflows and the docs live rebuild watcher
- `docs-viewer/bin/docs-viewer` for Docs Viewer `/docs/` manage mode, document-package routes, and docs management APIs
- `bin/local-all` when one terminal should supervise the sibling services together

These services should stay separate.
Do not make public preview part of Studio startup semantics, and do not
reintroduce retired Analytics or Data Sharing routes.

## Child References

- [Toolchain](Local_Setup_Toolchain.md) covers current versions, fresh macOS install, version checks, and switching Python versions.
- [Environment](Local_Setup_Environment.md) covers `.env.local`, process environment fallback, repo-specific operating notes, and common commands.
- [Public Site Preview](Local_Setup_Public_Site_Preview.md) covers the public static preview and validation commands and wrapper defaults.
- [Recovery](Local_Setup_Recovery.md) covers recovery after macOS, Xcode, or Command Line Tools updates.
- [GitHub And Codex Notes](Local_Setup_GitHub_And_Codex_Notes.md) covers local-vs-GitHub setup boundaries and Codex guidance.
