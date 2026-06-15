---
doc_id: local-setup
title: Local Setup
added_date: 2026-04-13
last_updated: 2026-06-13
parent_id: ""
viewable: true
---
# Local Setup

This guide centralizes the current local toolchain needed to run the Python scripts in this repo and to verify the static public site locally.

For cloud-hosted development guidance, see [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments).
For dependency-role guidance across local and cloud environments, see [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies).

All commands assume you are in `dotlineform-site/` unless stated otherwise.

## Local App Boundaries

The local development stack is split into sibling services:

- `bin/site-preview` for the public static-site preview
- `bin/local-studio` for Local Studio catalogue workflows and the docs live rebuild watcher
- `bin/local-admin` for Admin operations
- `bin/local-analytics` for Analytics tag and Data Sharing routes/APIs
- `docs-viewer/bin/docs-viewer` for Docs Viewer `/docs/` manage mode and docs management APIs
- `bin/local-all` when one terminal should supervise the sibling services together

These services should stay separate.
Do not make public preview part of Studio startup semantics, and do not reintroduce Analytics or Data Sharing routes under `/studio/`.

## Child References

- [Toolchain](/docs/?scope=studio&doc=local-setup-toolchain) covers current versions, fresh macOS install, version checks, and switching Python versions.
- [Environment](/docs/?scope=studio&doc=local-setup-environment) covers `var/local/site.env`, process environment fallback, repo-specific operating notes, and common commands.
- [Public Site Preview](/docs/?scope=studio&doc=local-setup-public-site-preview) covers the public static preview and validation commands and wrapper defaults.
- [Local Admin App](/docs/?scope=studio&doc=local-admin-app) covers Admin route/API ownership and output paths.
- [Recovery](/docs/?scope=studio&doc=local-setup-recovery) covers recovery after macOS, Xcode, or Command Line Tools updates.
- [GitHub And Codex Notes](/docs/?scope=studio&doc=local-setup-github-codex) covers local-vs-GitHub setup boundaries and Codex guidance.
