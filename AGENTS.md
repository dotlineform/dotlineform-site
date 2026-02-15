## Runtime and Paths

- Use `/Users/dlf/miniconda3/bin/python3` for all Python commands.
- Run project commands from `dotlineform-site/` unless explicitly told otherwise.

## Safety Defaults

- Prefer dry-run behavior for generators unless explicitly asked to write.
- Do not overwrite prose includes in `_includes/work_prose`, `_includes/series_prose`, or `_includes/moments_prose` unless explicitly requested.
- Do not delete generated or source files unless explicitly requested.

## Pipeline Conventions

- Treat `data/works.xlsx` as canonical source for generated collections.
- Treat worksheets `Works`, `Series`, `WorkDetails`, and `Moments` as canonical.
- Keep generated output deterministic (stable ordering, stable checksums, stable formatting).

## Moments-Specific Rules

- Generate `_moments/*.md` from worksheet `Moments`.
- Moment prose content lives in `_includes/moments_prose/<slug>.md`.
- Moment layout should use srcset variants `800`, `1200`, `1600` only.
- Do not add a `2400` variant for moments unless explicitly requested.

## Validation Checklist

- After changing Python scripts, run a syntax check with the configured interpreter.
- After generator changes, run a dry-run and summarize what would be written.
- After layout/template changes, verify behavior on desktop and mobile.
- Include changed file paths (and line references when useful) in summaries.

## Git and Change Hygiene

- Do not commit unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Never use destructive git commands (`reset --hard`, checkout/revert of unrelated changes) without explicit approval.
- Ignore unrelated dirty files and do not revert user changes.

## Implementation Style

- Preserve existing Jekyll/Liquid conventions in this repo.
- Prefer shared JS/CSS logic over duplicated inline logic.
- Keep comments concise and implementation-focused.
