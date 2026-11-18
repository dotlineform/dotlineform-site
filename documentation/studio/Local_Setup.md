---
draft: false
doc_id: d-20260413-000000-d314b7
title: Local Setup
added_date: 2026-04-13 00:00:00
last_updated: "2026-11-18"
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
- `bin/local-studio` for Studio Catalogue authoring and Refresh
- `docs-viewer/bin/docs-viewer` for the local Docs reader, with Manage enabled by `DOCS_VIEWER_MANAGEMENT_ENABLED=1`
- `bin/local-all` when one terminal should supervise the sibling services together

Each service has its own startup command and data authority. [Local runners and default addresses](Local_Runners.md) · [Start a local surface](../guide/How_The_Site_Fits_Together.md#start-a-local-surface)

## Child References

- [Toolchain](Local_Setup_Toolchain.md) covers current versions, fresh macOS install, version checks, and switching Python versions.
- [Environment](Local_Setup_Environment.md) covers `.env.local`, process environment fallback, repo-specific operating notes, and common commands.
- [Public Site Preview](Local_Setup_Public_Site_Preview.md) covers the public static preview and validation commands and wrapper defaults.
- [Recovery](Local_Setup_Recovery.md) covers recovery after macOS, Xcode, or Command Line Tools updates.

Local authoring and media preparation use the configured Python and media tools. Pages deploys the tracked site tree. [Runtime dependencies](Runtime_Dependencies.md) · [Publish and deploy](../guide/Publish_And_Deploy.md)
