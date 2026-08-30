# Docs Viewer Development

Docs Viewer code and configuration live in this repository. Scope-owned documents, media, generated output, and accepted published output do not.

## Scope storage

`config/scopes/docs_scopes.json` is the storage authority. Every configured scope resolves to:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/<scope-id>/
├── source/
│   ├── documents/
│   └── media/
│       ├── img/
│       ├── svg/
│       ├── files/
│       ├── html/
│       └── build-source/mermaid/
├── generated/
└── published/
```

Keep the standard directories even when they are empty. There is no repository fallback and no shared top-level media workspace. If the configured root is unavailable, leave it unavailable and fix or reconnect that root.

## Set up or migrate a scope

1. Add or confirm the scope configuration.
2. Create the standard external folder structure manually.
3. Copy the canonical documents and retained media into `source/`.
4. Run Build from Manage and review Generated.
5. Run Publish and review Published.

For Analysis, run Deploy Repo only when the accepted Published snapshot should replace its configured tracked-site and public-media projection. Review the exact preview and resulting repository delta before committing it.

Do not copy `generated/` or `published/` forward as source. They are replaceable lifecycle outputs.

## Normal lifecycle

- Source mutations use the Docs Viewer source/mutation service. The development watcher may refresh document projections, but it does not Publish.
- Build replaces the scope's generated documents and search output, then writes the completed generated-snapshot manifest.
- Publish removes the previous managed files in `published/`, copies the accepted generated snapshot, then writes the completed published-snapshot manifest. Empty directories may remain.
- Publish owns document eligibility. Every consumer sees the same accepted Published document set.
- Deploy Repo is available only for Analysis. Its write-free preview validates one complete Published revision and reports the exact configured repository, media, Catalogue, and lineage changes. Confirmed apply deploys that complete accepted set without reading source or generated output or applying another eligibility rule.
- The local Publish workflow may run Publish and Deploy Repo together, but they remain independently selectable operations. A successful Publish remains valid if Deploy Repo is incomplete and Deploy Repo can normally be retried on its own.
- Review the resulting tracked `site/` delta through the local site preview. Git commit and push remain explicit ordinary repository actions.
- Deploy Public remains the separate manually triggered GitHub Pages workflow over the committed and pushed `site/` snapshot. It does not Build, Publish, Deploy Repo, or read external scopes.

The app reports paths and capabilities from the configured external root. It must not infer storage from scope type, public visibility, repository contents, or an old manifest record.

## Recovery

For a failed Build, Publish, or Deploy Repo, fix the source, configuration, producer, or destination and rerun the owning action. Generated and deployed output does not require transactional swaps, automatic retries, or backup directories. If an external publication-lineage update succeeds but its `dotlineform/projects` follow-through Build fails, fix the cause and run that ordinary Projects Build; Deploy Repo reports the two outcomes separately.

The clean Git commit immediately before the Stage 2.3 removal is the recovery point for the retired repository scope copies. Retained media is recoverable from each active scope's `source/media/`. Restore manually only when necessary, verify the restored source, then Build and Publish again.
