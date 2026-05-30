---
doc_id: local-setup
title: Local Setup
added_date: 2026-04-13
last_updated: 2026-05-30
parent_id: ""
viewable: true
---
# Local Setup

This guide centralizes the current local toolchain needed to run the Python scripts in this repo and to verify the Jekyll site locally.

For cloud-hosted development guidance, see [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments).
For dependency-role guidance across local and cloud environments, see [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies).

All commands assume you are in `dotlineform-site/` unless stated otherwise.

## Local App Boundaries

The local development stack is split into sibling services:

- `bin/public-site-preview` for the public Jekyll preview
- `bin/local-studio` for Local Studio catalogue, audit, activity, admin, and docs-watcher workflows
- `bin/local-analytics` for Analytics tag and Data Sharing routes/APIs
- `bin/local-ui-catalogue` for isolated UI Catalogue demos
- `docs-viewer/bin/docs-viewer` for Docs Viewer `/docs/` manage mode and docs management APIs
- `bin/local-all` when one terminal should supervise the sibling services together

These services should stay separate.
Do not make public preview part of Studio startup semantics, do not reintroduce Analytics or Data Sharing routes under `/studio/`, and do not serve UI Catalogue demos through Local Studio.

## Child References

- [Toolchain](/docs/?scope=studio&doc=local-setup-toolchain) covers current versions, fresh macOS install, version checks, and switching Python/Ruby versions.
- [Environment](/docs/?scope=studio&doc=local-setup-environment) covers `var/local/site.env`, process environment fallback, repo-specific operating notes, and common commands.
- [Public Site Preview](/docs/?scope=studio&doc=local-setup-public-site-preview) covers the public Jekyll preview/build commands, CSS rebuild behavior, LiveReload, and the difference between wrapper scripts and raw Jekyll commands.
- [Recovery](/docs/?scope=studio&doc=local-setup-recovery) covers recovery after macOS, Xcode, or Command Line Tools updates.
- [GitHub And Codex Notes](/docs/?scope=studio&doc=local-setup-github-codex) covers local-vs-GitHub setup boundaries and Codex guidance.
