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

Do not copy `generated/` or `published/` forward as source. They are replaceable lifecycle outputs.

## Normal lifecycle

- Source mutations use the Docs Viewer source/mutation service. The development watcher may refresh document projections, but it does not Publish.
- Build replaces the scope's generated documents and search output, then writes the completed generated-snapshot manifest.
- Publish removes the previous managed files in `published/`, copies the accepted generated snapshot, then writes the completed published-snapshot manifest. Empty directories may remain.
- Public `site/` projection and remote deployment are separate from Publish.

The app reports paths and capabilities from the configured external root. It must not infer storage from scope type, public visibility, repository contents, or an old manifest record.

## Recovery

For a failed Build or Publish, fix the source, configuration, or producer and rerun the action. Generated output does not require transactional swaps, retries, or automatic backup directories.

The clean Git commit immediately before the Stage 2.3 removal is the recovery point for the retired repository scope copies. Retained media is recoverable from each active scope's `source/media/`. Restore manually only when necessary, verify the restored source, then Build and Publish again.
