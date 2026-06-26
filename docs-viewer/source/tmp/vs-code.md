---
doc_id: vs-code
title: "vs code"
added_date: 2026-05-26
last_updated: 2026-06-26
---

## VS Code menu ##

- **Commit**: saves the selected/staged changes into your local Git history only. Nothing goes to GitHub. No GitHub Actions run. No live site update.
- **Commit & Push**: commits locally, then sends the commit to GitHub. That can trigger GitHub Actions and, on `main`, the current legacy Pages publish path.
- **Commit & Sync**: commits, pushes your changes, and also pulls remote changes. Treat it as “commit plus network operations”.
- **Commit (Amend)**: rewrites the previous local commit. Useful only when you deliberately want to fold changes into the last commit.