---
draft: false
doc_id: d-20260423-204839-111501
title: Runtime Dependencies
added_date: "2026-04-23 20:48:39"
last_updated: "2026-11-18"
parent_id: d-20260419-000000-d2e47b
---
# Runtime Dependencies

## Authorities

[requirements.txt](../../requirements.txt) pins the shared Python baseline, including its explicitly included App-service development requirements. Feature/tool-local `package.json` and adjacent lockfiles own direct/resolved Node dependencies. [setup.sh](../../.codex/setup.sh) and [devcontainer](../../.devcontainer/devcontainer.json) own bootstrap; invoking code owns external command requirements. Native App and Processing keep their own lifecycle owners.

Read those files for current versions and exhaustive package lists. A package's feature-specific use does not make installation optional once it belongs to the pinned baseline. Copying Python services/builders into a portable installation also needs that pinned dependency boundary.

## Python And Media Roles

| Dependency | Responsibility |
| --- | --- |
| Beautiful Soup and lxml | Parse imported HTML; project code owns conversion decisions |
| Bleach | Explicit HTML sanitization |
| Mammoth | Word-to-semantic-HTML conversion through the repository's fixed style/image adapter |
| Pillow | Required image decoding/validation, import WebP work and document thumbnail encoding |
| markdown-it-py | Shared CommonMark rendering |
| pytest | Pinned by the App-service development requirements and available for agreed focused Python test work |

[Import](../reference/Docs_Import.md) and [format mappings](../reference/HTML_Import_Mapping.md) own conversion. [Document grammar](../reference/Document_Identity.md#parsing-and-rendering) owns renderer rules and their sanitization boundary. Do not introduce a generic third-party converter as the product-rule owner.

Native raster Add/Edit validates static content with Pillow and uses FFmpeg for resizing/WebP even without a thumbnail. Import and thumbnail owners retain their separate paths; they do not inherit Studio pipeline policy. `heif-convert` and macOS `sips` remain workflow-specific tools. Code-only static checks and public preview do not require media tools. [Media workflow](../reference/Media_And_Asset_Handling.md)

## Tool Environments

Repository lint tools have an isolated owner:

```bash
python3 -m venv tooling/lint/.venv
tooling/lint/.venv/bin/python -m pip install -r tooling/lint/python-requirements.txt
npm ci --prefix tooling/lint
```

Use the configured project interpreter for the creation command. Each package root owns reproducible installation and ignored `node_modules/`; do not rely on globally installed executables. External diagram authoring needs no Docs Viewer Node runtime.

Local work follows the project Miniconda convention. Earlier cloud/Codespaces bootstrap creates/reuses `.venv` and installs Python/lint dependencies; the [new Codex Cloud setup](../_working/Cloud_Environments.md) remains unresolved. Dependency setup does not supply private workspaces or publishing credentials. Public preview, Studio and Docs Viewer remain separate services; `local-all` supervises siblings.

## Change Method

Establish the concrete consumer before adding a package/tool. Prefer existing dependencies or the standard library when sufficient. Pin Python packages in the shared requirements; pin direct Node packages exactly with their adjacent lockfile. Add system/bootstrap support only for environments that must execute that workflow.

Use focused installation, import or `pip check` diagnostics and the relevant static or manual consumer evidence. Agree any focused test work separately. [Verification](Verification.md) · [Test Contract Discipline](Test_Contract_Discipline.md)

Confirm the parsing stack in a new environment with the configured interpreter when that capability is needed:

```bash
python3 -c "import bs4, lxml, bleach, mammoth, PIL; from markdown_it import MarkdownIt; MarkdownIt('commonmark')"
```

Keep versions/flags with their executable authorities. Known limits include shared-baseline growth, local/cloud Python or system-library differences, feature-local Node setup and command-specific external tools. A successful bootstrap establishes neither workspace access nor publication readiness.
